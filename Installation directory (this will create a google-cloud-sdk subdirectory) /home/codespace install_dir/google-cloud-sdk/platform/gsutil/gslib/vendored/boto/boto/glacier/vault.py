# -*- coding: utf-8 -*-
# Copyright (c) 2012 Thomas Parslow http://almostobsolete.net/
# Copyright (c) 2012 Robie Basak <robie@justgohome.co.uk>
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
import codecs
from boto.glacier.exceptions import UploadArchiveError
from boto.glacier.job import Job
from boto.glacier.writer import compute_hashes_from_fileobj, \
                                resume_file_upload, Writer
from boto.glacier.concurrent import ConcurrentUploader
from boto.glacier.utils import minimum_part_size, DEFAULT_PART_SIZE
import os.path


_MEGABYTE = 1024 * 1024
_GIGABYTE = 1024 * _MEGABYTE

MAXIMUM_ARCHIVE_SIZE = 10000 * 4 * _GIGABYTE
MAXIMUM_NUMBER_OF_PARTS = 10000


class Vault(object):

    DefaultPartSize = DEFAULT_PART_SIZE
    SingleOperationThreshold = 100 * _MEGABYTE

    ResponseDataElements = (('VaultName', 'name', None),
                            ('VaultARN', 'arn', None),
                            ('CreationDate', 'creation_date', None),
                            ('LastInventoryDate', 'last_inventory_date', None),
                            ('SizeInBytes', 'size', 0),
                            ('NumberOfArchives', 'number_of_archives', 0))

    def __init__(self, layer1, response_data=None):
        self.layer1 = layer1
        if response_data:
            for response_name, attr_name, default in self.ResponseDataElements:
                value = response_data[response_name]
                setattr(self, attr_name, value)
        else:
            for response_name, attr_name, default in self.ResponseDataElements:
                setattr(self, attr_name, default)

    def __repr__(self):
        return 'Vault("%s")' % self.arn

    def delete(self):
        """
        Delete's this vault. WARNING!
        """
        self.layer1.delete_vault(self.name)

    def upload_archive(self, filename, description=None):
        """
        Adds an archive to a vault. For archives greater than 100MB the
        multipart upload will be used.

        :type file: str
        :param file: A filename to upload

        :type description: str
        :param description: An optional description for the archive.

        :rtype: str
        :return: The archive id of the newly created archive
        """
        if os.path.getsize(filename) > self.SingleOperationThreshold:
            return self.create_archive_from_file(filename, description=description)
        return self._upload_archive_single_operation(filename, description)

    def _upload_archive_single_operation(self, filename, description):
        """
        Adds an archive to a vault in a single operation. It's recommended for
        archives less than 100MB

        :type file: str
        :param file: A filename to upload

        :type description: str
        :param description: A description for the archive.

        :rtype: str
        :return: The archive id of the newly created archive
        """
        with open(filename, 'rb') as fileobj:
            linear_hash, tree_hash = compute_hashes_from_fileobj(fileobj)
            fileobj.seek(0)
            response = self.layer1.upload_archive(self.name, fileobj,
                                                  linear_hash, tree_hash,
                                                  description)
        return response['ArchiveId']

    def create_archive_writer(self, part_size=DefaultPartSize,
                              description=None):
        """
        Create a new archive and begin a multi-part upload to it.
        Returns a file-like object to which the data for the archive
        can be written. Once all the data is written the file-like
        object should be closed, you can then call the get_archive_id
        method on it to get the ID of the created archive.

        :type part_size: int
        :param part_size: The part size for the multipart upload.

        :type description: str
        :param description: An optional description for the archive.

        :rtype: :class:`boto.glacier.writer.Writer`
        :return: A Writer object that to which the archive data
            should be written.
        """
        response = self.layer1.initiate_multipart_upload(self.name,
                                                         part_size,
                                                         description)
        return Writer(self, response['UploadId'], part_size=part_size)

    def create_archive_from_file(self, filename=None, file_obj=None,
                                 description=None, upload_id_callback=None):
        """
        Create a new archive and upload the data from the given file
        or file-like object.

        :type filename: str
        :param filename: A filename to upload

        :type file_obj: file
        :param file_obj: A file-like object to upload

        :type description: str
        :param description: An optional description for the archive.

        :type upload_id_callback: function
        :param upload_id_callback: if set, call with the upload_id as the
            only parameter when it becomes known, to enable future calls
            to resume_archive_from_file in case resume is needed.

        :rtype: str
        :return: The archive id of the newly created archive
        """
        part_size = self.DefaultPartSize
        if not file_obj:
            file_size = os.path.getsize(filename)
            try:
                part_size = minimum_part_size(file_size, part_size)
            except ValueError:
                raise UploadArchiveError("File size of %s bytes exceeds "
                                         "40,000 GB archive limit of Glacier.")
            file_obj = open(filename, "rb")
        writer = self.create_archive_writer(
            description=description,
            part_size=part_size)
        if upload_id_callback:
            upload_id_callback(writer.upload_id)
        while True:
            data = file_obj.read(part_size)
            if not data:
                break
            writer.write(data)
        writer.close()
        return writer.get_archive_id()

    @staticmethod
    def _range_string_to_part_index(range_string, part_size):
        start, inside_end = [int(value) for value in range_string.split('-')]
        end = inside_end + 1
        length = end - start
        if length == part_size + 1:
            # Off-by-one bug in Amazon's Glacier implementation,
            # see: https://forums.aws.amazon.com/thread.jspa?threadID=106866
            # Workaround: since part_size is too big by one byte, adjust it
            end -= 1
            inside_end -= 1
            length -= 1
        assert not (start % part_size), (
            "upload part start byte is not on a part boundary")
        assert (length <= part_size), "upload part is bigger than part size"
        return start // part_size

    def resume_archive_from_file(self, upload_id, filename=None,
                                 file_obj=None):
        """Resume upload of a file already part-uploaded to Glacier.

        The resumption of an upload where the part-uploaded section is empty
        is a valid degenerate case that this function can handle.

        One and only one of filename or file_obj must be specified.

        :type upload_id: str
        :param upload_id: existing Glacier upload id of upload being resumed.

        :type filename: str
        :param filename: file to open for resume

        :type fobj: file
        :param fobj: file-like object containing local data to resume. This
            must read from the start of the entire upload, not just from the
            point being resumed. Use fobj.seek(0) to achieve this if necessary.

        :rtype: str
        :return: The archive id of the newly created archive

        """
        part_list_response = self.list_all_parts(upload_id)
        part_size = part_list_response['PartSizeInBytes']

        part_hash_map = {}
        for part_desc in part_list_response['Parts']:
            part_index = self._range_string_to_part_index(
                part_desc['RangeInBytes'], part_size)
            part_tree_hash = codecs.decode(part_desc['SHA256TreeHash'], 'hex_codec')
            part_hash_map[part_index] = part_tree_hash

        if not file_obj:
            file_obj = open(filename, "rb")

        return resume_file_upload(
            self, upload_id, part_size, file_obj, part_hash_map)

    def concurrent_create_archive_from_file(self, filename, description,
                                            **kwargs):
        """
        Create a new archive from a file and upload the given
        file.

        This is a convenience method around the
        :class:`boto.glacier.concurrent.ConcurrentUploader`
        class.  This method will perform a multipart upload
        and upload the parts of the file concurrently.

        :type filename: str
        :param filename: A filename to upload

        :param kwargs: Additional kwargs to pass through to
            :py:class:`boto.glacier.concurrent.ConcurrentUploader`.
            You can pass any argument besides the ``api`` and
            ``vault_name`` param (these arguments are already
            passed to the ``ConcurrentUploader`` for you).

        :raises: `boto.glacier.exception.UploadArchiveError` is an error
            occurs during the upload process.

        :rtype: str
        :return: The archive id of the newly created archive

        """
        uploader = ConcurrentUploader(self.layer1, self.name, **kwargs)
        archive_id = uploader.upload(filename, description)
        return archive_id

    def retrieve_archive(self, archive_id, sns_topic=None,
                         description=None):
        """
        Initiate a archive retrieval job to download the data from an
        archive. You will need to wait for the notification from
        Amazon (via SNS) before you can actually download the data,
        this takes around 4 hours.

        :type archive_id: str
        :param archive_id: The id of the archive

        :type description: str
        :param description: An optional description for the job.

        :type sns_topic: str
        :param sns_topic: The Amazon SNS topic ARN where Amazon Glacier
            sends notification when the job is completed and the output
            is ready for you to download.

        :rtype: :class:`boto.glacier.job.Job`
        :return: A Job object representing the retrieval job.
        """
        job_data = {'Type': 'archive-retrieval',
                    'ArchiveId': archive_id}
        if sns_topic is not None:
            job_data['SNSTopic'] = sns_topic
        if description is not None:
            job_data['Description'] = description

        response = self.layer1.initiate_job(self.name, job_data)
        return self.get_job(response['JobId'])

    def retrieve_inventory(self, sns_topic=None,
                           description=None, byte_range=None,
                           start_date=None, end_date=None,
                           limit=None):
        """
        Initiate a inventory retrieval job to list the items in the
        vault. You will need to wait for the notification from
        Amazon (via SNS) before you can actually download the data,
        this takes around 4 hours.

        :type description: str
        :param description: An optional description for the job.

        :type sns_topic: str
        :param sns_topic: The Amazon SNS topic ARN where Amazon Glacier
            sends notification when the job is completed and the output
            is ready for you to download.

        :type byte_range: str
        :param byte_range: Range of bytes to retrieve.

        :type start_date: DateTime
        :param start_date: Beginning of the date range to query.

        :type end_date: DateTime
        :param end_date: End of the date range to query.

        :type limit: int
        :param limit: Limits the number of results returned.

        :rtype: str
        :return: The ID of the job
        """
        job_data = {'Type': 'inventory-retrieval'}
        if sns_topic is not None:
            job_data['SNSTopic'] = sns_topic
        if description is not None:
            job_data['Description'] = description
        if byte_range is not None:
            job_data['RetrievalByteRange'] = byte_range
        if start_date is not None or end_date is not None or limit is not None:
            rparams = {}

            if start_date is not None:
                rparams['StartDate'] = start_date.strftime('%Y-%m-%dT%H:%M:%S%Z')
            if end_date is not None:
                rparams['EndDate'] = end_date.strftime('%Y-%m-%dT%H:%M:%S%Z')
            if limit is not None:
                rparams['Limit'] = limit

            job_data['InventoryRetrievalParameters'] = rparams

        response = self.layer1.initiate_job(self.name, job_data)
        return response['JobId']

    def retrieve_inventory_job(self, **kwargs):
        """
        Identical to ``retrieve_inventory``, but returns a ``Job`` instance
        instead of just the job ID.

        :type description: str
        :param description: An optional description for the job.

        :type sns_topic: str
        :param sns_topic: The Amazon SNS topic ARN where Amazon Glacier
            sends notification when the job is completed and the output
            is ready for you to download.

        :type byte_range: str
        :param byte_range: Range of bytes to retrieve.

        :type start_date: DateTime
        :param start_date: Beginning of the date range to query.

        :type end_date: DateTime
        :param end_date: End of the date range to query.

        :type limit: int
        :param limit: Limits the number of results returned.

        :rtype: :class:`boto.glacier.job.Job`
        :return: A Job object representing the retrieval job.
        """
        job_id = self.retrieve_inventory(**kwargs)
        return self.get_job(job_id)

    def delete_archive(self, archive_id):
        """
        This operation deletes an archive from the vault.

        :type archive_id: str
        :param archive_id: The ID for the archive to be deleted.
        """
        return self.layer1.delete_archive(self.name, archive_id)

    def get_job(self, job_id):
        """
        Get an object representing a job in progress.

        :type job_id: str
        :param job_id: The ID of the job

        :rtype: :class:`boto.glacier.job.Job`
        :return: A Job object representing the job.
        """
        response_data = self.layer1.describe_job(self.name, job_id)
        return Job(self, response_data)

    def list_jobs(self, completed=None, status_code=None):
        """
        Return a list of Job objects related to this vault.

        :type completed: boolean
        :param completed: Specifies the state of the jobs to return.
            If a value of True is passed, only completed jobs will
            be returned.  If a value of False is passed, only
            uncompleted jobs will be returned.  If no value is
            passed, all jobs will be returned.

        :type status_code: string
        :param status_code: Specifies the type of job status to return.
            Valid values are: InProgress|Succeeded|Failed.  If not
            specified, jobs with all status codes are returned.

        :rtype: list of :class:`boto.glacier.job.Job`
        :return: A list of Job objects related to this vault.
        """
        response_data = self.layer1.list_jobs(self.name, completed,
                                              status_code)
        return [Job(self, jd) for jd in response_data['JobList']]

    def list_all_parts(self, upload_id):
        """Automatically make and combine multiple calls to list_parts.

        Call list_parts as necessary, combining the results in case multiple
        calls were required to get data on all available parts.

        """
        result = self.layer1.list_parts(self.name, upload_id)
        marker = result['Marker']
        while marker:
            additional_result = self.layer1.list_parts(
                self.name, upload_id, marker=marker)
            result['Parts'].extend(additional_result['Parts'])
            marker = additional_result['Marker']
        # The marker makes no sense in an unpaginated result, and clearing it
        # makes testing easier. This also has the nice property that the result
        # is a normal (but expanded) response.
        result['Marker'] = None
        return result
