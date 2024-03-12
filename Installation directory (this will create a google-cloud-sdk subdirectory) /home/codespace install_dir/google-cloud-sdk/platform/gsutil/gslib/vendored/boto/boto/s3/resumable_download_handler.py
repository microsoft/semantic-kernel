# Copyright 2010 Google Inc.
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
import errno
import os
import re
import socket
import time

import six.moves.http_client as httplib

import boto
from boto import config, storage_uri_for_key
from boto.connection import AWSAuthConnection
from boto.exception import ResumableDownloadException
from boto.exception import ResumableTransferDisposition
from boto.s3.keyfile import KeyFile
from boto.gs.key import Key as GSKey

"""
Resumable download handler.

Resumable downloads will retry failed downloads, resuming at the byte count
completed by the last download attempt. If too many retries happen with no
progress (per configurable num_retries param), the download will be aborted.

The caller can optionally specify a tracker_file_name param in the
ResumableDownloadHandler constructor. If you do this, that file will
save the state needed to allow retrying later, in a separate process
(e.g., in a later run of gsutil).

Note that resumable downloads work across providers (they depend only
on support Range GETs), but this code is in the boto.s3 package
because it is the wrong abstraction level to go in the top-level boto
package.

TODO: At some point we should refactor the code to have a storage_service
package where all these provider-independent files go.
"""


class ByteTranslatingCallbackHandler(object):
    """
    Proxy class that translates progress callbacks made by
    boto.s3.Key.get_file(), taking into account that we're resuming
    a download.
    """
    def __init__(self, proxied_cb, download_start_point):
        self.proxied_cb = proxied_cb
        self.download_start_point = download_start_point

    def call(self, total_bytes_uploaded, total_size):
        self.proxied_cb(self.download_start_point + total_bytes_uploaded,
                        total_size)


def get_cur_file_size(fp, position_to_eof=False):
    """
    Returns size of file, optionally leaving fp positioned at EOF.
    """
    if isinstance(fp, KeyFile) and not position_to_eof:
        # Avoid EOF seek for KeyFile case as it's very inefficient.
        return fp.getkey().size
    if not position_to_eof:
        cur_pos = fp.tell()
    fp.seek(0, os.SEEK_END)
    cur_file_size = fp.tell()
    if not position_to_eof:
        fp.seek(cur_pos, os.SEEK_SET)
    return cur_file_size


class ResumableDownloadHandler(object):
    """
    Handler for resumable downloads.
    """

    MIN_ETAG_LEN = 5

    RETRYABLE_EXCEPTIONS = (httplib.HTTPException, IOError, socket.error,
                            socket.gaierror)

    def __init__(self, tracker_file_name=None, num_retries=None):
        """
        Constructor. Instantiate once for each downloaded file.

        :type tracker_file_name: string
        :param tracker_file_name: optional file name to save tracking info
            about this download. If supplied and the current process fails
            the download, it can be retried in a new process. If called
            with an existing file containing an unexpired timestamp,
            we'll resume the transfer for this file; else we'll start a
            new resumable download.

        :type num_retries: int
        :param num_retries: the number of times we'll re-try a resumable
            download making no progress. (Count resets every time we get
            progress, so download can span many more than this number of
            retries.)
        """
        self.tracker_file_name = tracker_file_name
        self.num_retries = num_retries
        self.etag_value_for_current_download = None
        if tracker_file_name:
            self._load_tracker_file_etag()
        # Save download_start_point in instance state so caller can
        # find how much was transferred by this ResumableDownloadHandler
        # (across retries).
        self.download_start_point = None

    def _load_tracker_file_etag(self):
        f = None
        try:
            f = open(self.tracker_file_name, 'r')
            self.etag_value_for_current_download = f.readline().rstrip('\n')
            # We used to match an MD5-based regex to ensure that the etag was
            # read correctly. Since ETags need not be MD5s, we now do a simple
            # length sanity check instead.
            if len(self.etag_value_for_current_download) < self.MIN_ETAG_LEN:
                print('Couldn\'t read etag in tracker file (%s). Restarting '
                      'download from scratch.' % self.tracker_file_name)
        except IOError as e:
            # Ignore non-existent file (happens first time a download
            # is attempted on an object), but warn user for other errors.
            if e.errno != errno.ENOENT:
                # Will restart because
                # self.etag_value_for_current_download is None.
                print('Couldn\'t read URI tracker file (%s): %s. Restarting '
                      'download from scratch.' %
                      (self.tracker_file_name, e.strerror))
        finally:
            if f:
                f.close()

    def _save_tracker_info(self, key):
        self.etag_value_for_current_download = key.etag.strip('"\'')
        if not self.tracker_file_name:
            return
        f = None
        try:
            f = open(self.tracker_file_name, 'w')
            f.write('%s\n' % self.etag_value_for_current_download)
        except IOError as e:
            raise ResumableDownloadException(
                'Couldn\'t write tracker file (%s): %s.\nThis can happen'
                'if you\'re using an incorrectly configured download tool\n'
                '(e.g., gsutil configured to save tracker files to an '
                'unwritable directory)' %
                (self.tracker_file_name, e.strerror),
                ResumableTransferDisposition.ABORT)
        finally:
            if f:
                f.close()

    def _remove_tracker_file(self):
        if (self.tracker_file_name and
            os.path.exists(self.tracker_file_name)):
                os.unlink(self.tracker_file_name)

    def _attempt_resumable_download(self, key, fp, headers, cb, num_cb,
                                    torrent, version_id, hash_algs):
        """
        Attempts a resumable download.

        Raises ResumableDownloadException if any problems occur.
        """
        cur_file_size = get_cur_file_size(fp, position_to_eof=True)

        if (cur_file_size and 
            self.etag_value_for_current_download and
            self.etag_value_for_current_download == key.etag.strip('"\'')):
            # Try to resume existing transfer.
            if cur_file_size > key.size:
              raise ResumableDownloadException(
                  '%s is larger (%d) than %s (%d).\nDeleting tracker file, so '
                  'if you re-try this download it will start from scratch' %
                  (fp.name, cur_file_size, str(storage_uri_for_key(key)),
                   key.size), ResumableTransferDisposition.ABORT)
            elif cur_file_size == key.size:
                if key.bucket.connection.debug >= 1:
                    print('Download complete.')
                return
            if key.bucket.connection.debug >= 1:
                print('Resuming download.')
            headers = headers.copy()
            headers['Range'] = 'bytes=%d-%d' % (cur_file_size, key.size - 1)
            cb = ByteTranslatingCallbackHandler(cb, cur_file_size).call
            self.download_start_point = cur_file_size
        else:
            if key.bucket.connection.debug >= 1:
                print('Starting new resumable download.')
            self._save_tracker_info(key)
            self.download_start_point = 0
            # Truncate the file, in case a new resumable download is being
            # started atop an existing file.
            fp.truncate(0)

        # Disable AWSAuthConnection-level retry behavior, since that would
        # cause downloads to restart from scratch.
        if isinstance(key, GSKey):
          key.get_file(fp, headers, cb, num_cb, torrent, version_id,
                       override_num_retries=0, hash_algs=hash_algs)
        else:
          key.get_file(fp, headers, cb, num_cb, torrent, version_id,
                       override_num_retries=0)
        fp.flush()

    def get_file(self, key, fp, headers, cb=None, num_cb=10, torrent=False,
                 version_id=None, hash_algs=None):
        """
        Retrieves a file from a Key
        :type key: :class:`boto.s3.key.Key` or subclass
        :param key: The Key object from which upload is to be downloaded
        
        :type fp: file
        :param fp: File pointer into which data should be downloaded
        
        :type headers: string
        :param: headers to send when retrieving the files
        
        :type cb: function
        :param cb: (optional) a callback function that will be called to report
             progress on the download.  The callback should accept two integer
             parameters, the first representing the number of bytes that have
             been successfully transmitted from the storage service and
             the second representing the total number of bytes that need
             to be transmitted.
        
        :type num_cb: int
        :param num_cb: (optional) If a callback is specified with the cb
             parameter this parameter determines the granularity of the callback
             by defining the maximum number of times the callback will be
             called during the file transfer.
             
        :type torrent: bool
        :param torrent: Flag for whether to get a torrent for the file

        :type version_id: string
        :param version_id: The version ID (optional)

        :type hash_algs: dictionary
        :param hash_algs: (optional) Dictionary of hash algorithms and
            corresponding hashing class that implements update() and digest().
            Defaults to {'md5': hashlib/md5.md5}.

        Raises ResumableDownloadException if a problem occurs during
            the transfer.
        """

        debug = key.bucket.connection.debug
        if not headers:
            headers = {}

        # Use num-retries from constructor if one was provided; else check
        # for a value specified in the boto config file; else default to 6.
        if self.num_retries is None:
            self.num_retries = config.getint('Boto', 'num_retries', 6)
        progress_less_iterations = 0

        while True:  # Retry as long as we're making progress.
            had_file_bytes_before_attempt = get_cur_file_size(fp)
            try:
                self._attempt_resumable_download(key, fp, headers, cb, num_cb,
                                                 torrent, version_id, hash_algs)
                # Download succceded, so remove the tracker file (if have one).
                self._remove_tracker_file()
                # Previously, check_final_md5() was called here to validate 
                # downloaded file's checksum, however, to be consistent with
                # non-resumable downloads, this call was removed. Checksum
                # validation of file contents should be done by the caller.
                if debug >= 1:
                    print('Resumable download complete.')
                return
            except self.RETRYABLE_EXCEPTIONS as e:
                if debug >= 1:
                    print('Caught exception (%s)' % e.__repr__())
                if isinstance(e, IOError) and e.errno == errno.EPIPE:
                    # Broken pipe error causes httplib to immediately
                    # close the socket (http://bugs.python.org/issue5542),
                    # so we need to close and reopen the key before resuming
                    # the download.
                    if isinstance(key, GSKey):
                      key.get_file(fp, headers, cb, num_cb, torrent, version_id,
                                   override_num_retries=0, hash_algs=hash_algs)
                    else:
                      key.get_file(fp, headers, cb, num_cb, torrent, version_id,
                                   override_num_retries=0)
            except ResumableDownloadException as e:
                if (e.disposition ==
                    ResumableTransferDisposition.ABORT_CUR_PROCESS):
                    if debug >= 1:
                        print('Caught non-retryable ResumableDownloadException '
                              '(%s)' % e.message)
                    raise
                elif (e.disposition ==
                    ResumableTransferDisposition.ABORT):
                    if debug >= 1:
                        print('Caught non-retryable ResumableDownloadException '
                              '(%s); aborting and removing tracker file' %
                              e.message)
                    self._remove_tracker_file()
                    raise
                else:
                    if debug >= 1:
                        print('Caught ResumableDownloadException (%s) - will '
                              'retry' % e.message)

            # At this point we had a re-tryable failure; see if made progress.
            if get_cur_file_size(fp) > had_file_bytes_before_attempt:
                progress_less_iterations = 0
            else:
                progress_less_iterations += 1

            if progress_less_iterations > self.num_retries:
                # Don't retry any longer in the current process.
                raise ResumableDownloadException(
                    'Too many resumable download attempts failed without '
                    'progress. You might try this download again later',
                    ResumableTransferDisposition.ABORT_CUR_PROCESS)

            # Close the key, in case a previous download died partway
            # through and left data in the underlying key HTTP buffer.
            # Do this within a try/except block in case the connection is
            # closed (since key.close() attempts to do a final read, in which
            # case this read attempt would get an IncompleteRead exception,
            # which we can safely ignore.
            try:
                key.close()
            except httplib.IncompleteRead:
                pass

            sleep_time_secs = 2**progress_less_iterations
            if debug >= 1:
                print('Got retryable failure (%d progress-less in a row).\n'
                      'Sleeping %d seconds before re-trying' %
                      (progress_less_iterations, sleep_time_secs))
            time.sleep(sleep_time_secs)
