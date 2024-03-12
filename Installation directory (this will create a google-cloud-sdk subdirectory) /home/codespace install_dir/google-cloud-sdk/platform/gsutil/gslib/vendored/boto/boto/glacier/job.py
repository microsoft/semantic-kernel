# -*- coding: utf-8 -*-
# Copyright (c) 2012 Thomas Parslow http://almostobsolete.net/
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
import math
import socket

from boto.glacier.exceptions import TreeHashDoesNotMatchError, \
                                    DownloadArchiveError
from boto.glacier.utils import tree_hash_from_str


class Job(object):

    DefaultPartSize = 4 * 1024 * 1024

    ResponseDataElements = (('Action', 'action', None),
                            ('ArchiveId', 'archive_id', None),
                            ('ArchiveSizeInBytes', 'archive_size', 0),
                            ('Completed', 'completed', False),
                            ('CompletionDate', 'completion_date', None),
                            ('CreationDate', 'creation_date', None),
                            ('InventorySizeInBytes', 'inventory_size', 0),
                            ('JobDescription', 'description', None),
                            ('JobId', 'id', None),
                            ('SHA256TreeHash', 'sha256_treehash', None),
                            ('SNSTopic', 'sns_topic', None),
                            ('StatusCode', 'status_code', None),
                            ('StatusMessage', 'status_message', None),
                            ('VaultARN', 'arn', None))

    def __init__(self, vault, response_data=None):
        self.vault = vault
        if response_data:
            for response_name, attr_name, default in self.ResponseDataElements:
                setattr(self, attr_name, response_data[response_name])
        else:
            for response_name, attr_name, default in self.ResponseDataElements:
                setattr(self, attr_name, default)

    def __repr__(self):
        return 'Job(%s)' % self.arn

    def get_output(self, byte_range=None, validate_checksum=False):
        """
        This operation downloads the output of the job.  Depending on
        the job type you specified when you initiated the job, the
        output will be either the content of an archive or a vault
        inventory.

        You can download all the job output or download a portion of
        the output by specifying a byte range. In the case of an
        archive retrieval job, depending on the byte range you
        specify, Amazon Glacier returns the checksum for the portion
        of the data. You can compute the checksum on the client and
        verify that the values match to ensure the portion you
        downloaded is the correct data.

        :type byte_range: tuple
        :param range: A tuple of integer specifying the slice (in bytes)
            of the archive you want to receive

        :type validate_checksum: bool
        :param validate_checksum: Specify whether or not to validate
            the associate tree hash.  If the response does not contain
            a TreeHash, then no checksum will be verified.

        """
        response = self.vault.layer1.get_job_output(self.vault.name,
                                                    self.id,
                                                    byte_range)
        if validate_checksum and 'TreeHash' in response:
            data = response.read()
            actual_tree_hash = tree_hash_from_str(data)
            if response['TreeHash'] != actual_tree_hash:
                raise TreeHashDoesNotMatchError(
                    "The calculated tree hash %s does not match the "
                    "expected tree hash %s for the byte range %s" % (
                        actual_tree_hash, response['TreeHash'], byte_range))
        return response

    def _calc_num_chunks(self, chunk_size):
        return int(math.ceil(self.archive_size / float(chunk_size)))

    def download_to_file(self, filename, chunk_size=DefaultPartSize,
                         verify_hashes=True, retry_exceptions=(socket.error,)):
        """Download an archive to a file by name.

        :type filename: str
        :param filename: The name of the file where the archive
            contents will be saved.

        :type chunk_size: int
        :param chunk_size: The chunk size to use when downloading
            the archive.

        :type verify_hashes: bool
        :param verify_hashes: Indicates whether or not to verify
            the tree hashes for each downloaded chunk.

        """
        num_chunks = self._calc_num_chunks(chunk_size)
        with open(filename, 'wb') as output_file:
            self._download_to_fileob(output_file, num_chunks, chunk_size,
                                     verify_hashes, retry_exceptions)

    def download_to_fileobj(self, output_file, chunk_size=DefaultPartSize,
                            verify_hashes=True,
                            retry_exceptions=(socket.error,)):
        """Download an archive to a file object.

        :type output_file: file
        :param output_file: The file object where the archive
            contents will be saved.

        :type chunk_size: int
        :param chunk_size: The chunk size to use when downloading
            the archive.

        :type verify_hashes: bool
        :param verify_hashes: Indicates whether or not to verify
            the tree hashes for each downloaded chunk.

        """
        num_chunks = self._calc_num_chunks(chunk_size)
        self._download_to_fileob(output_file, num_chunks, chunk_size,
                                 verify_hashes, retry_exceptions)

    def _download_to_fileob(self, fileobj, num_chunks, chunk_size, verify_hashes,
                            retry_exceptions):
        for i in range(num_chunks):
            byte_range = ((i * chunk_size), ((i + 1) * chunk_size) - 1)
            data, expected_tree_hash = self._download_byte_range(
                byte_range, retry_exceptions)
            if verify_hashes:
                actual_tree_hash = tree_hash_from_str(data)
                if expected_tree_hash != actual_tree_hash:
                    raise TreeHashDoesNotMatchError(
                        "The calculated tree hash %s does not match the "
                        "expected tree hash %s for the byte range %s" % (
                            actual_tree_hash, expected_tree_hash, byte_range))
            fileobj.write(data)

    def _download_byte_range(self, byte_range, retry_exceptions):
        # You can occasionally get socket.errors when downloading
        # chunks from Glacier, so each chunk can be retried up
        # to 5 times.
        for _ in range(5):
            try:
                response = self.get_output(byte_range)
                data = response.read()
                expected_tree_hash = response['TreeHash']
                return data, expected_tree_hash
            except retry_exceptions as e:
                continue
        else:
            raise DownloadArchiveError("There was an error downloading"
                                       "byte range %s: %s" % (byte_range,
                                                              e))
