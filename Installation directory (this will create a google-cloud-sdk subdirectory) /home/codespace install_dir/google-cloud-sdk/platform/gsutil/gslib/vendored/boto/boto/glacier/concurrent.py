# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
import os
import math
import threading
import hashlib
import time
import logging
from boto.compat import Queue
import binascii

from boto.glacier.utils import DEFAULT_PART_SIZE, minimum_part_size, \
                               chunk_hashes, tree_hash, bytes_to_hex
from boto.glacier.exceptions import UploadArchiveError, \
                                    DownloadArchiveError, \
                                    TreeHashDoesNotMatchError


_END_SENTINEL = object()
log = logging.getLogger('boto.glacier.concurrent')


class ConcurrentTransferer(object):
    def __init__(self, part_size=DEFAULT_PART_SIZE, num_threads=10):
        self._part_size = part_size
        self._num_threads = num_threads
        self._threads = []

    def _calculate_required_part_size(self, total_size):
        min_part_size_required = minimum_part_size(total_size)
        if self._part_size >= min_part_size_required:
            part_size = self._part_size
        else:
            part_size = min_part_size_required
            log.debug("The part size specified (%s) is smaller than "
                      "the minimum required part size.  Using a part "
                      "size of: %s", self._part_size, part_size)
        total_parts = int(math.ceil(total_size / float(part_size)))
        return total_parts, part_size

    def _shutdown_threads(self):
        log.debug("Shutting down threads.")
        for thread in self._threads:
            thread.should_continue = False
        for thread in self._threads:
            thread.join()
        log.debug("Threads have exited.")

    def _add_work_items_to_queue(self, total_parts, worker_queue, part_size):
        log.debug("Adding work items to queue.")
        for i in range(total_parts):
            worker_queue.put((i, part_size))
        for i in range(self._num_threads):
            worker_queue.put(_END_SENTINEL)


class ConcurrentUploader(ConcurrentTransferer):
    """Concurrently upload an archive to glacier.

    This class uses a thread pool to concurrently upload an archive
    to glacier using the multipart upload API.

    The threadpool is completely managed by this class and is
    transparent to the users of this class.

    """
    def __init__(self, api, vault_name, part_size=DEFAULT_PART_SIZE,
                 num_threads=10):
        """
        :type api: :class:`boto.glacier.layer1.Layer1`
        :param api: A layer1 glacier object.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type part_size: int
        :param part_size: The size, in bytes, of the chunks to use when uploading
            the archive parts.  The part size must be a megabyte multiplied by
            a power of two.

        :type num_threads: int
        :param num_threads: The number of threads to spawn for the thread pool.
            The number of threads will control how much parts are being
            concurrently uploaded.

        """
        super(ConcurrentUploader, self).__init__(part_size, num_threads)
        self._api = api
        self._vault_name = vault_name

    def upload(self, filename, description=None):
        """Concurrently create an archive.

        The part_size value specified when the class was constructed
        will be used *unless* it is smaller than the minimum required
        part size needed for the size of the given file.  In that case,
        the part size used will be the minimum part size required
        to properly upload the given file.

        :type file: str
        :param file: The filename to upload

        :type description: str
        :param description: The description of the archive.

        :rtype: str
        :return: The archive id of the newly created archive.

        """
        total_size = os.stat(filename).st_size
        total_parts, part_size = self._calculate_required_part_size(total_size)
        hash_chunks = [None] * total_parts
        worker_queue = Queue()
        result_queue = Queue()
        response = self._api.initiate_multipart_upload(self._vault_name,
                                                       part_size,
                                                       description)
        upload_id = response['UploadId']
        # The basic idea is to add the chunks (the offsets not the actual
        # contents) to a work queue, start up a thread pool, let the crank
        # through the items in the work queue, and then place their results
        # in a result queue which we use to complete the multipart upload.
        self._add_work_items_to_queue(total_parts, worker_queue, part_size)
        self._start_upload_threads(result_queue, upload_id,
                                   worker_queue, filename)
        try:
            self._wait_for_upload_threads(hash_chunks, result_queue,
                                          total_parts)
        except UploadArchiveError as e:
            log.debug("An error occurred while uploading an archive, "
                      "aborting multipart upload.")
            self._api.abort_multipart_upload(self._vault_name, upload_id)
            raise e
        log.debug("Completing upload.")
        response = self._api.complete_multipart_upload(
            self._vault_name, upload_id, bytes_to_hex(tree_hash(hash_chunks)),
            total_size)
        log.debug("Upload finished.")
        return response['ArchiveId']

    def _wait_for_upload_threads(self, hash_chunks, result_queue, total_parts):
        for _ in range(total_parts):
            result = result_queue.get()
            if isinstance(result, Exception):
                log.debug("An error was found in the result queue, terminating "
                          "threads: %s", result)
                self._shutdown_threads()
                raise UploadArchiveError("An error occurred while uploading "
                                         "an archive: %s" % result)
            # Each unit of work returns the tree hash for the given part
            # number, which we use at the end to compute the tree hash of
            # the entire archive.
            part_number, tree_sha256 = result
            hash_chunks[part_number] = tree_sha256
        self._shutdown_threads()

    def _start_upload_threads(self, result_queue, upload_id, worker_queue,
                              filename):
        log.debug("Starting threads.")
        for _ in range(self._num_threads):
            thread = UploadWorkerThread(self._api, self._vault_name, filename,
                                        upload_id, worker_queue, result_queue)
            time.sleep(0.2)
            thread.start()
            self._threads.append(thread)


class TransferThread(threading.Thread):
    def __init__(self, worker_queue, result_queue):
        super(TransferThread, self).__init__()
        self._worker_queue = worker_queue
        self._result_queue = result_queue
        # This value can be set externally by other objects
        # to indicate that the thread should be shut down.
        self.should_continue = True

    def run(self):
        while self.should_continue:
            try:
                work = self._worker_queue.get(timeout=1)
            except Empty:
                continue
            if work is _END_SENTINEL:
                self._cleanup()
                return
            result = self._process_chunk(work)
            self._result_queue.put(result)
        self._cleanup()

    def _process_chunk(self, work):
        pass

    def _cleanup(self):
        pass


class UploadWorkerThread(TransferThread):
    def __init__(self, api, vault_name, filename, upload_id,
                 worker_queue, result_queue, num_retries=5,
                 time_between_retries=5,
                 retry_exceptions=Exception):
        super(UploadWorkerThread, self).__init__(worker_queue, result_queue)
        self._api = api
        self._vault_name = vault_name
        self._filename = filename
        self._fileobj = open(filename, 'rb')
        self._upload_id = upload_id
        self._num_retries = num_retries
        self._time_between_retries = time_between_retries
        self._retry_exceptions = retry_exceptions

    def _process_chunk(self, work):
        result = None
        for i in range(self._num_retries + 1):
            try:
                result = self._upload_chunk(work)
                break
            except self._retry_exceptions as e:
                log.error("Exception caught uploading part number %s for "
                          "vault %s, attempt: (%s / %s), filename: %s, "
                          "exception: %s, msg: %s",
                          work[0], self._vault_name, i + 1, self._num_retries + 1,
                          self._filename, e.__class__, e)
                time.sleep(self._time_between_retries)
                result = e
        return result

    def _upload_chunk(self, work):
        part_number, part_size = work
        start_byte = part_number * part_size
        self._fileobj.seek(start_byte)
        contents = self._fileobj.read(part_size)
        linear_hash = hashlib.sha256(contents).hexdigest()
        tree_hash_bytes = tree_hash(chunk_hashes(contents))
        byte_range = (start_byte, start_byte + len(contents) - 1)
        log.debug("Uploading chunk %s of size %s", part_number, part_size)
        response = self._api.upload_part(self._vault_name, self._upload_id,
                                         linear_hash,
                                         bytes_to_hex(tree_hash_bytes),
                                         byte_range, contents)
        # Reading the response allows the connection to be reused.
        response.read()
        return (part_number, tree_hash_bytes)

    def _cleanup(self):
        self._fileobj.close()


class ConcurrentDownloader(ConcurrentTransferer):
    """
    Concurrently download an archive from glacier.

    This class uses a thread pool to concurrently download an archive
    from glacier.

    The threadpool is completely managed by this class and is
    transparent to the users of this class.

    """
    def __init__(self, job, part_size=DEFAULT_PART_SIZE,
                 num_threads=10):
        """
        :param job: A layer2 job object for archive retrieval object.

        :param part_size: The size, in bytes, of the chunks to use when uploading
            the archive parts.  The part size must be a megabyte multiplied by
            a power of two.

        """
        super(ConcurrentDownloader, self).__init__(part_size, num_threads)
        self._job = job

    def download(self, filename):
        """
        Concurrently download an archive.

        :param filename: The filename to download the archive to
        :type filename: str

        """
        total_size = self._job.archive_size
        total_parts, part_size = self._calculate_required_part_size(total_size)
        worker_queue = Queue()
        result_queue = Queue()
        self._add_work_items_to_queue(total_parts, worker_queue, part_size)
        self._start_download_threads(result_queue, worker_queue)
        try:
            self._wait_for_download_threads(filename, result_queue, total_parts)
        except DownloadArchiveError as e:
            log.debug("An error occurred while downloading an archive: %s", e)
            raise e
        log.debug("Download completed.")

    def _wait_for_download_threads(self, filename, result_queue, total_parts):
        """
        Waits until the result_queue is filled with all the downloaded parts
        This indicates that all part downloads have completed

        Saves downloaded parts into filename

        :param filename:
        :param result_queue:
        :param total_parts:
        """
        hash_chunks = [None] * total_parts
        with open(filename, "wb") as f:
            for _ in range(total_parts):
                result = result_queue.get()
                if isinstance(result, Exception):
                    log.debug("An error was found in the result queue, "
                              "terminating threads: %s", result)
                    self._shutdown_threads()
                    raise DownloadArchiveError(
                        "An error occurred while uploading "
                        "an archive: %s" % result)
                part_number, part_size, actual_hash, data = result
                hash_chunks[part_number] = actual_hash
                start_byte = part_number * part_size
                f.seek(start_byte)
                f.write(data)
                f.flush()
        final_hash = bytes_to_hex(tree_hash(hash_chunks))
        log.debug("Verifying final tree hash of archive, expecting: %s, "
                  "actual: %s", self._job.sha256_treehash, final_hash)
        if self._job.sha256_treehash != final_hash:
            self._shutdown_threads()
            raise TreeHashDoesNotMatchError(
                "Tree hash for entire archive does not match, "
                "expected: %s, got: %s" % (self._job.sha256_treehash,
                                           final_hash))
        self._shutdown_threads()

    def _start_download_threads(self, result_queue, worker_queue):
        log.debug("Starting threads.")
        for _ in range(self._num_threads):
            thread = DownloadWorkerThread(self._job, worker_queue, result_queue)
            time.sleep(0.2)
            thread.start()
            self._threads.append(thread)


class DownloadWorkerThread(TransferThread):
    def __init__(self, job,
                 worker_queue, result_queue,
                 num_retries=5,
                 time_between_retries=5,
                 retry_exceptions=Exception):
        """
        Individual download thread that will download parts of the file from Glacier. Parts
        to download stored in work queue.

        Parts download to a temp dir with each part a separate file

        :param job: Glacier job object
        :param work_queue: A queue of tuples which include the part_number and
            part_size
        :param result_queue: A priority queue of tuples which include the
            part_number and the path to the temp file that holds that
            part's data.

        """
        super(DownloadWorkerThread, self).__init__(worker_queue, result_queue)
        self._job = job
        self._num_retries = num_retries
        self._time_between_retries = time_between_retries
        self._retry_exceptions = retry_exceptions

    def _process_chunk(self, work):
        """
        Attempt to download a part of the archive from Glacier
        Store the result in the result_queue

        :param work:
        """
        result = None
        for _ in range(self._num_retries):
            try:
                result = self._download_chunk(work)
                break
            except self._retry_exceptions as e:
                log.error("Exception caught downloading part number %s for "
                          "job %s", work[0], self._job,)
                time.sleep(self._time_between_retries)
                result = e
        return result

    def _download_chunk(self, work):
        """
        Downloads a chunk of archive from Glacier. Saves the data to a temp file
        Returns the part number and temp file location

        :param work:
        """
        part_number, part_size = work
        start_byte = part_number * part_size
        byte_range = (start_byte, start_byte + part_size - 1)
        log.debug("Downloading chunk %s of size %s", part_number, part_size)
        response = self._job.get_output(byte_range)
        data = response.read()
        actual_hash = bytes_to_hex(tree_hash(chunk_hashes(data)))
        if response['TreeHash'] != actual_hash:
            raise TreeHashDoesNotMatchError(
                "Tree hash for part number %s does not match, "
                "expected: %s, got: %s" % (part_number, response['TreeHash'],
                                           actual_hash))
        return (part_number, part_size, binascii.unhexlify(actual_hash), data)
