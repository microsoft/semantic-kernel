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

import base64
import binascii
import os
import re

from boto.compat import StringIO, six
from boto.exception import BotoClientError
from boto.s3.key import Key as S3Key
from boto.s3.keyfile import KeyFile
from boto.utils import compute_hash, get_utf8able_str

class Key(S3Key):
    """
    Represents a key (object) in a GS bucket.

    :ivar bucket: The parent :class:`boto.gs.bucket.Bucket`.
    :ivar name: The name of this Key object.
    :ivar metadata: A dictionary containing user metadata that you
        wish to store with the object or that has been retrieved from
        an existing object.
    :ivar cache_control: The value of the `Cache-Control` HTTP header.
    :ivar content_type: The value of the `Content-Type` HTTP header.
    :ivar content_encoding: The value of the `Content-Encoding` HTTP header.
    :ivar content_disposition: The value of the `Content-Disposition` HTTP
        header.
    :ivar content_language: The value of the `Content-Language` HTTP header.
    :ivar etag: The `etag` associated with this object.
    :ivar last_modified: The string timestamp representing the last
        time this object was modified in GS.
    :ivar owner: The ID of the owner of this object.
    :ivar storage_class: The storage class of the object. Currently, one of:
        STANDARD | DURABLE_REDUCED_AVAILABILITY.
    :ivar md5: The MD5 hash of the contents of the object.
    :ivar size: The size, in bytes, of the object.
    :ivar generation: The generation number of the object.
    :ivar metageneration: The generation number of the object metadata.
    :ivar encrypted: Whether the object is encrypted while at rest on
        the server.
    :ivar cloud_hashes: Dictionary of checksums as supplied by the storage
        provider.
    """

    def __init__(self, bucket=None, name=None, generation=None):
        super(Key, self).__init__(bucket=bucket, name=name)
        self.generation = generation
        self.meta_generation = None
        self.cloud_hashes = {}
        self.component_count = None

    def __repr__(self):
        if self.generation and self.metageneration:
            ver_str = '#%s.%s' % (self.generation, self.metageneration)
        else:
            ver_str = ''
        if self.bucket:
            return '<Key: %s,%s%s>' % (self.bucket.name, self.name, ver_str)
        else:
            return '<Key: None,%s%s>' % (self.name, ver_str)

    def endElement(self, name, value, connection):
        if name == 'Key':
            self.name = value
        elif name == 'ETag':
            self.etag = value
        elif name == 'IsLatest':
            if value == 'true':
                self.is_latest = True
            else:
                self.is_latest = False
        elif name == 'LastModified':
            self.last_modified = value
        elif name == 'Size':
            self.size = int(value)
        elif name == 'StorageClass':
            self.storage_class = value
        elif name == 'Owner':
            pass
        elif name == 'VersionId':
            self.version_id = value
        elif name == 'Generation':
            self.generation = value
        elif name == 'MetaGeneration':
            self.metageneration = value
        else:
            setattr(self, name, value)

    def handle_version_headers(self, resp, force=False):
        self.metageneration = resp.getheader('x-goog-metageneration', None)
        self.generation = resp.getheader('x-goog-generation', None)

    def handle_restore_headers(self, response):
        return

    def handle_addl_headers(self, headers):
        for key, value in headers:
            if key == 'x-goog-hash':
                for hash_pair in value.split(','):
                    alg, b64_digest = hash_pair.strip().split('=', 1)
                    self.cloud_hashes[alg] = binascii.a2b_base64(b64_digest)
            elif key == 'x-goog-component-count':
                self.component_count = int(value)
            elif key == 'x-goog-generation':
                self.generation = value
            # Use x-goog-stored-content-encoding and
            # x-goog-stored-content-length to indicate original content length
            # and encoding, which are transcoding-invariant (so are preferable
            # over using content-encoding and size headers).
            elif key == 'x-goog-stored-content-encoding':
                self.content_encoding = value
            elif key == 'x-goog-stored-content-length':
                self.size = int(value)
            elif key == 'x-goog-storage-class':
                self.storage_class = value

    def open_read(self, headers=None, query_args='',
                  override_num_retries=None, response_headers=None):
        """
        Open this key for reading

        :type headers: dict
        :param headers: Headers to pass in the web request

        :type query_args: string
        :param query_args: Arguments to pass in the query string
            (ie, 'torrent')

        :type override_num_retries: int
        :param override_num_retries: If not None will override configured
            num_retries parameter for underlying GET.

        :type response_headers: dict
        :param response_headers: A dictionary containing HTTP
            headers/values that will override any headers associated
            with the stored object in the response.  See
            http://goo.gl/EWOPb for details.
        """
        # For GCS we need to include the object generation in the query args.
        # The rest of the processing is handled in the parent class.
        if self.generation:
            if query_args:
                query_args += '&'
            query_args += 'generation=%s' % self.generation
        super(Key, self).open_read(headers=headers, query_args=query_args,
                                   override_num_retries=override_num_retries,
                                   response_headers=response_headers)

    def get_file(self, fp, headers=None, cb=None, num_cb=10,
                 torrent=False, version_id=None, override_num_retries=None,
                 response_headers=None, hash_algs=None):
        query_args = None
        if self.generation:
            query_args = ['generation=%s' % self.generation]
        self._get_file_internal(fp, headers=headers, cb=cb, num_cb=num_cb,
                                override_num_retries=override_num_retries,
                                response_headers=response_headers,
                                hash_algs=hash_algs,
                                query_args=query_args)

    def get_contents_to_file(self, fp, headers=None,
                             cb=None, num_cb=10,
                             torrent=False,
                             version_id=None,
                             res_download_handler=None,
                             response_headers=None,
                             hash_algs=None):
        """
        Retrieve an object from GCS using the name of the Key object as the
        key in GCS. Write the contents of the object to the file pointed
        to by 'fp'.

        :type fp: File -like object
        :param fp:

        :type headers: dict
        :param headers: additional HTTP headers that will be sent with
            the GET request.

        :type cb: function
        :param cb: a callback function that will be called to report
            progress on the upload. The callback should accept two
            integer parameters, the first representing the number of
            bytes that have been successfully transmitted to GCS and
            the second representing the size of the to be transmitted
            object.

        :type cb: int
        :param num_cb: (optional) If a callback is specified with the
            cb parameter this parameter determines the granularity of
            the callback by defining the maximum number of times the
            callback will be called during the file transfer.

        :type torrent: bool
        :param torrent: If True, returns the contents of a torrent
            file as a string.

        :type res_upload_handler: ResumableDownloadHandler
        :param res_download_handler: If provided, this handler will
            perform the download.

        :type response_headers: dict
        :param response_headers: A dictionary containing HTTP
            headers/values that will override any headers associated
            with the stored object in the response. See
            http://goo.gl/sMkcC for details.
        """
        if self.bucket is not None:
            if res_download_handler:
                res_download_handler.get_file(self, fp, headers, cb, num_cb,
                                              torrent=torrent,
                                              version_id=version_id,
                                              hash_algs=hash_algs)
            else:
                self.get_file(fp, headers, cb, num_cb, torrent=torrent,
                              version_id=version_id,
                              response_headers=response_headers,
                              hash_algs=hash_algs)

    def compute_hash(self, fp, algorithm, size=None):
        """
        :type fp: file
        :param fp: File pointer to the file to hash. The file
            pointer will be reset to the same position before the
            method returns.

        :type algorithm: zero-argument constructor for hash objects that
            implements update() and digest() (e.g. hashlib.md5)

        :type size: int
        :param size: (optional) The Maximum number of bytes to read
            from the file pointer (fp). This is useful when uploading
            a file in multiple parts where the file is being split
            in place into different parts. Less bytes may be available.
        """
        hex_digest, b64_digest, data_size = compute_hash(
            fp, size=size, hash_algorithm=algorithm)
        # The internal implementation of compute_hash() needs to return the
        # data size, but we don't want to return that value to the external
        # caller because it changes the class interface (i.e. it might
        # break some code), so we consume the third tuple value here and
        # return the remainder of the tuple to the caller, thereby preserving
        # the existing interface.
        self.size = data_size
        return (hex_digest, b64_digest)

    def send_file(self, fp, headers=None, cb=None, num_cb=10,
                  query_args=None, chunked_transfer=False, size=None,
                  hash_algs=None):
        """
        Upload a file to GCS.

        :type fp: file
        :param fp: The file pointer to upload. The file pointer must
            point at the offset from which you wish to upload.
            ie. if uploading the full file, it should point at the
            start of the file. Normally when a file is opened for
            reading, the fp will point at the first byte. See the
            bytes parameter below for more info.

        :type headers: dict
        :param headers: The headers to pass along with the PUT request

        :type num_cb: int
        :param num_cb: (optional) If a callback is specified with the
            cb parameter this parameter determines the granularity of
            the callback by defining the maximum number of times the
            callback will be called during the file
            transfer. Providing a negative integer will cause your
            callback to be called with each buffer read.

        :type query_args: string
        :param query_args: Arguments to pass in the query string.

        :type chunked_transfer: boolean
        :param chunked_transfer: (optional) If true, we use chunked
            Transfer-Encoding.

        :type size: int
        :param size: (optional) The Maximum number of bytes to read
            from the file pointer (fp). This is useful when uploading
            a file in multiple parts where you are splitting the file
            up into different ranges to be uploaded. If not specified,
            the default behaviour is to read all bytes from the file
            pointer. Less bytes may be available.

        :type hash_algs: dictionary
        :param hash_algs: (optional) Dictionary of hash algorithms and
            corresponding hashing class that implements update() and digest().
            Defaults to {'md5': hashlib.md5}.
        """
        self._send_file_internal(fp, headers=headers, cb=cb, num_cb=num_cb,
                                 query_args=query_args,
                                 chunked_transfer=chunked_transfer, size=size,
                                 hash_algs=hash_algs)

    def delete(self, headers=None):
        return self.bucket.delete_key(self.name, version_id=self.version_id,
                                      generation=self.generation,
                                      headers=headers)

    def add_email_grant(self, permission, email_address):
        """
        Convenience method that provides a quick way to add an email grant to a
        key. This method retrieves the current ACL, creates a new grant based on
        the parameters passed in, adds that grant to the ACL and then PUT's the
        new ACL back to GS.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
            READ|FULL_CONTROL
            See http://code.google.com/apis/storage/docs/developer-guide.html#authorization
            for more details on permissions.

        :type email_address: string
        :param email_address: The email address associated with the Google
                              account to which you are granting the permission.
        """
        acl = self.get_acl()
        acl.add_email_grant(permission, email_address)
        self.set_acl(acl)

    def add_user_grant(self, permission, user_id):
        """
        Convenience method that provides a quick way to add a canonical user
        grant to a key. This method retrieves the current ACL, creates a new
        grant based on the parameters passed in, adds that grant to the ACL and
        then PUT's the new ACL back to GS.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
            READ|FULL_CONTROL
            See http://code.google.com/apis/storage/docs/developer-guide.html#authorization
            for more details on permissions.

        :type user_id: string
        :param user_id: The canonical user id associated with the GS account to
             which you are granting the permission.
        """
        acl = self.get_acl()
        acl.add_user_grant(permission, user_id)
        self.set_acl(acl)

    def add_group_email_grant(self, permission, email_address, headers=None):
        """
        Convenience method that provides a quick way to add an email group
        grant to a key. This method retrieves the current ACL, creates a new
        grant based on the parameters passed in, adds that grant to the ACL and
        then PUT's the new ACL back to GS.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
            READ|FULL_CONTROL
            See http://code.google.com/apis/storage/docs/developer-guide.html#authorization
            for more details on permissions.

        :type email_address: string
        :param email_address: The email address associated with the Google
            Group to which you are granting the permission.
        """
        acl = self.get_acl(headers=headers)
        acl.add_group_email_grant(permission, email_address)
        self.set_acl(acl, headers=headers)

    def add_group_grant(self, permission, group_id):
        """
        Convenience method that provides a quick way to add a canonical group
        grant to a key. This method retrieves the current ACL, creates a new
        grant based on the parameters passed in, adds that grant to the ACL and
        then PUT's the new ACL back to GS.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
            READ|FULL_CONTROL
            See http://code.google.com/apis/storage/docs/developer-guide.html#authorization
            for more details on permissions.

        :type group_id: string
        :param group_id: The canonical group id associated with the Google
            Groups account you are granting the permission to.
        """
        acl = self.get_acl()
        acl.add_group_grant(permission, group_id)
        self.set_acl(acl)

    def set_contents_from_file(self, fp, headers=None, replace=True,
                               cb=None, num_cb=10, policy=None, md5=None,
                               res_upload_handler=None, size=None, rewind=False,
                               if_generation=None):
        """
        Store an object in GS using the name of the Key object as the
        key in GS and the contents of the file pointed to by 'fp' as the
        contents.

        :type fp: file
        :param fp: The file whose contents are to be uploaded.

        :type headers: dict
        :param headers: (optional) Additional HTTP headers to be sent with the
            PUT request.

        :type replace: bool
        :param replace: (optional) If this parameter is False, the method will
            first check to see if an object exists in the bucket with the same
            key. If it does, it won't overwrite it. The default value is True
            which will overwrite the object.

        :type cb: function
        :param cb: (optional) Callback function that will be called to report
            progress on the upload. The callback should accept two integer
            parameters, the first representing the number of bytes that have
            been successfully transmitted to GS and the second representing the
            total number of bytes that need to be transmitted.

        :type num_cb: int
        :param num_cb: (optional) If a callback is specified with the cb
            parameter, this parameter determines the granularity of the callback
            by defining the maximum number of times the callback will be called
            during the file transfer.

        :type policy: :class:`boto.gs.acl.CannedACLStrings`
        :param policy: (optional) A canned ACL policy that will be applied to
            the new key in GS.

        :type md5: tuple
        :param md5: (optional) A tuple containing the hexdigest version of the
            MD5 checksum of the file as the first element and the
            Base64-encoded version of the plain checksum as the second element.
            This is the same format returned by the compute_md5 method.

            If you need to compute the MD5 for any reason prior to upload, it's
            silly to have to do it twice so this param, if present, will be
            used as the MD5 values of the file. Otherwise, the checksum will be
            computed.

        :type res_upload_handler: :py:class:`boto.gs.resumable_upload_handler.ResumableUploadHandler`
        :param res_upload_handler: (optional) If provided, this handler will
            perform the upload.

        :type size: int
        :param size: (optional) The Maximum number of bytes to read from the
            file pointer (fp). This is useful when uploading a file in multiple
            parts where you are splitting the file up into different ranges to
            be uploaded. If not specified, the default behaviour is to read all
            bytes from the file pointer. Less bytes may be available.

            Notes:

                1. The "size" parameter currently cannot be used when a
                   resumable upload handler is given but is still useful for
                   uploading part of a file as implemented by the parent class.
                2. At present Google Cloud Storage does not support multipart
                   uploads.

        :type rewind: bool
        :param rewind: (optional) If True, the file pointer (fp) will be
            rewound to the start before any bytes are read from it. The default
            behaviour is False which reads from the current position of the
            file pointer (fp).

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the
            object will only be written to if its current generation number is
            this value. If set to the value 0, the object will only be written
            if it doesn't already exist.

        :rtype: int
        :return: The number of bytes written to the key.

        TODO: At some point we should refactor the Bucket and Key classes,
        to move functionality common to all providers into a parent class,
        and provider-specific functionality into subclasses (rather than
        just overriding/sharing code the way it currently works).
        """
        provider = self.bucket.connection.provider
        if res_upload_handler and size:
            # could use size instead of file_length if provided but...
            raise BotoClientError(
                '"size" param not supported for resumable uploads.')
        headers = headers or {}
        if policy:
            headers[provider.acl_header] = policy

        if rewind:
            # caller requests reading from beginning of fp.
            fp.seek(0, os.SEEK_SET)
        else:
            # The following seek/tell/seek logic is intended
            # to detect applications using the older interface to
            # set_contents_from_file(), which automatically rewound the
            # file each time the Key was reused. This changed with commit
            # 14ee2d03f4665fe20d19a85286f78d39d924237e, to support uploads
            # split into multiple parts and uploaded in parallel, and at
            # the time of that commit this check was added because otherwise
            # older programs would get a success status and upload an empty
            # object. Unfortuantely, it's very inefficient for fp's implemented
            # by KeyFile (used, for example, by gsutil when copying between
            # providers). So, we skip the check for the KeyFile case.
            # TODO: At some point consider removing this seek/tell/seek
            # logic, after enough time has passed that it's unlikely any
            # programs remain that assume the older auto-rewind interface.
            if not isinstance(fp, KeyFile):
                spos = fp.tell()
                fp.seek(0, os.SEEK_END)
                if fp.tell() == spos:
                    fp.seek(0, os.SEEK_SET)
                    if fp.tell() != spos:
                        # Raise an exception as this is likely a programming
                        # error whereby there is data before the fp but nothing
                        # after it.
                        fp.seek(spos)
                        raise AttributeError('fp is at EOF. Use rewind option '
                                             'or seek() to data start.')
                # seek back to the correct position.
                fp.seek(spos)

        if hasattr(fp, 'name'):
            self.path = fp.name
        if self.bucket is not None:
            if isinstance(fp, KeyFile):
                # Avoid EOF seek for KeyFile case as it's very inefficient.
                key = fp.getkey()
                size = key.size - fp.tell()
                self.size = size
                # At present both GCS and S3 use MD5 for the etag for
                # non-multipart-uploaded objects. If the etag is 32 hex
                # chars use it as an MD5, to avoid having to read the file
                # twice while transferring.
                if (re.match('^"[a-fA-F0-9]{32}"$', key.etag)):
                    etag = key.etag.strip('"')
                    md5 = (etag, base64.b64encode(binascii.unhexlify(etag)))
            if size:
                self.size = size
            else:
                # If md5 is provided, still need to size so
                # calculate based on bytes to end of content
                spos = fp.tell()
                fp.seek(0, os.SEEK_END)
                self.size = fp.tell() - spos
                fp.seek(spos)
                size = self.size

            if md5 is None:
                md5 = self.compute_md5(fp, size)
            self.md5 = md5[0]
            self.base64md5 = md5[1]

            if self.name is None:
                self.name = self.md5

            if not replace:
                if self.bucket.lookup(self.name):
                    return

            if if_generation is not None:
                headers['x-goog-if-generation-match'] = str(if_generation)

            if res_upload_handler:
                res_upload_handler.send_file(self, fp, headers, cb, num_cb)
            else:
                # Not a resumable transfer so use basic send_file mechanism.
                self.send_file(fp, headers, cb, num_cb, size=size)

    def set_contents_from_filename(self, filename, headers=None, replace=True,
                                   cb=None, num_cb=10, policy=None, md5=None,
                                   reduced_redundancy=None,
                                   res_upload_handler=None,
                                   if_generation=None):
        """
        Store an object in GS using the name of the Key object as the
        key in GS and the contents of the file named by 'filename'.
        See set_contents_from_file method for details about the
        parameters.

        :type filename: string
        :param filename: The name of the file that you want to put onto GS.

        :type headers: dict
        :param headers: (optional) Additional headers to pass along with the
            request to GS.

        :type replace: bool
        :param replace: (optional) If True, replaces the contents of the file
            if it already exists.

        :type cb: function
        :param cb: (optional) Callback function that will be called to report
            progress on the upload. The callback should accept two integer
            parameters, the first representing the number of bytes that have
            been successfully transmitted to GS and the second representing the
            total number of bytes that need to be transmitted.

        :type num_cb: int
        :param num_cb: (optional) If a callback is specified with the cb
            parameter this parameter determines the granularity of the callback
            by defining the maximum number of times the callback will be called
            during the file transfer.

        :type policy: :py:attribute:`boto.gs.acl.CannedACLStrings`
        :param policy: (optional) A canned ACL policy that will be applied to
            the new key in GS.

        :type md5: tuple
        :param md5: (optional) A tuple containing the hexdigest version of the
            MD5 checksum of the file as the first element and the
            Base64-encoded version of the plain checksum as the second element.
            This is the same format returned by the compute_md5 method.

            If you need to compute the MD5 for any reason prior to upload, it's
            silly to have to do it twice so this param, if present, will be
            used as the MD5 values of the file. Otherwise, the checksum will be
            computed.

        :type res_upload_handler: :py:class:`boto.gs.resumable_upload_handler.ResumableUploadHandler`
        :param res_upload_handler: (optional) If provided, this handler will
            perform the upload.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the
            object will only be written to if its current generation number is
            this value. If set to the value 0, the object will only be written
            if it doesn't already exist.
        """
        # Clear out any previously computed hashes, since we are setting the
        # content.
        self.local_hashes = {}

        with open(filename, 'rb') as fp:
            self.set_contents_from_file(fp, headers, replace, cb, num_cb,
                                        policy, md5, res_upload_handler,
                                        if_generation=if_generation)

    def set_contents_from_string(self, s, headers=None, replace=True,
                                 cb=None, num_cb=10, policy=None, md5=None,
                                 if_generation=None):
        """
        Store an object in GCS using the name of the Key object as the
        key in GCS and the string 's' as the contents.
        See set_contents_from_file method for details about the
        parameters.

        :type headers: dict
        :param headers: Additional headers to pass along with the
                        request to AWS.

        :type replace: bool
        :param replace: If True, replaces the contents of the file if
                        it already exists.

        :type cb: function
        :param cb: a callback function that will be called to report
                   progress on the upload. The callback should accept
                   two integer parameters, the first representing the
                   number of bytes that have been successfully
                   transmitted to GCS and the second representing the
                   size of the to be transmitted object.

        :type cb: int
        :param num_cb: (optional) If a callback is specified with
                       the cb parameter this parameter determines the
                       granularity of the callback by defining
                       the maximum number of times the callback will
                       be called during the file transfer.

        :type policy: :class:`boto.gs.acl.CannedACLStrings`
        :param policy: A canned ACL policy that will be applied to the
                       new key in GCS.

        :type md5: A tuple containing the hexdigest version of the MD5
                   checksum of the file as the first element and the
                   Base64-encoded version of the plain checksum as the
                   second element. This is the same format returned by
                   the compute_md5 method.
        :param md5: If you need to compute the MD5 for any reason prior
                    to upload, it's silly to have to do it twice so this
                    param, if present, will be used as the MD5 values
                    of the file. Otherwise, the checksum will be computed.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the
            object will only be written to if its current generation number is
            this value. If set to the value 0, the object will only be written
            if it doesn't already exist.
        """

        # Clear out any previously computed md5 hashes, since we are setting the content.
        self.md5 = None
        self.base64md5 = None

        fp = StringIO(get_utf8able_str(s))
        r = self.set_contents_from_file(fp, headers, replace, cb, num_cb,
                                        policy, md5,
                                        if_generation=if_generation)
        fp.close()
        return r

    def set_contents_from_stream(self, *args, **kwargs):
        """
        Store an object using the name of the Key object as the key in
        cloud and the contents of the data stream pointed to by 'fp' as
        the contents.

        The stream object is not seekable and total size is not known.
        This has the implication that we can't specify the
        Content-Size and Content-MD5 in the header. So for huge
        uploads, the delay in calculating MD5 is avoided but with a
        penalty of inability to verify the integrity of the uploaded
        data.

        :type fp: file
        :param fp: the file whose contents are to be uploaded

        :type headers: dict
        :param headers: additional HTTP headers to be sent with the
            PUT request.

        :type replace: bool
        :param replace: If this parameter is False, the method will first check
            to see if an object exists in the bucket with the same key. If it
            does, it won't overwrite it. The default value is True which will
            overwrite the object.

        :type cb: function
        :param cb: a callback function that will be called to report
            progress on the upload. The callback should accept two integer
            parameters, the first representing the number of bytes that have
            been successfully transmitted to GS and the second representing the
            total number of bytes that need to be transmitted.

        :type num_cb: int
        :param num_cb: (optional) If a callback is specified with the
            cb parameter, this parameter determines the granularity of
            the callback by defining the maximum number of times the
            callback will be called during the file transfer.

        :type policy: :class:`boto.gs.acl.CannedACLStrings`
        :param policy: A canned ACL policy that will be applied to the new key
            in GS.

        :type size: int
        :param size: (optional) The Maximum number of bytes to read from
            the file pointer (fp). This is useful when uploading a
            file in multiple parts where you are splitting the file up
            into different ranges to be uploaded. If not specified,
            the default behaviour is to read all bytes from the file
            pointer. Less bytes may be available.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the
            object will only be written to if its current generation number is
            this value. If set to the value 0, the object will only be written
            if it doesn't already exist.
        """
        if_generation = kwargs.pop('if_generation', None)
        if if_generation is not None:
            headers = kwargs.get('headers', {})
            headers['x-goog-if-generation-match'] = str(if_generation)
            kwargs['headers'] = headers
        super(Key, self).set_contents_from_stream(*args, **kwargs)

    def set_acl(self, acl_or_str, headers=None, generation=None,
                 if_generation=None, if_metageneration=None):
        """Sets the ACL for this object.

        :type acl_or_str: string or :class:`boto.gs.acl.ACL`
        :param acl_or_str: A canned ACL string (see
            :data:`~.gs.acl.CannedACLStrings`) or an ACL object.

        :type headers: dict
        :param headers: Additional headers to set during the request.

        :type generation: int
        :param generation: If specified, sets the ACL for a specific generation
            of a versioned object. If not specified, the current version is
            modified.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the acl
            will only be updated if its current generation number is this value.

        :type if_metageneration: int
        :param if_metageneration: (optional) If set to a metageneration number,
            the acl will only be updated if its current metageneration number is
            this value.
        """
        if self.bucket is not None:
            self.bucket.set_acl(acl_or_str, self.name, headers=headers,
                                generation=generation,
                                if_generation=if_generation,
                                if_metageneration=if_metageneration)

    def get_acl(self, headers=None, generation=None):
        """Returns the ACL of this object.

        :param dict headers: Additional headers to set during the request.

        :param int generation: If specified, gets the ACL for a specific
            generation of a versioned object. If not specified, the current
            version is returned.

        :rtype: :class:`.gs.acl.ACL`
        """
        if self.bucket is not None:
            return self.bucket.get_acl(self.name, headers=headers,
                                       generation=generation)

    def get_xml_acl(self, headers=None, generation=None):
        """Returns the ACL string of this object.

        :param dict headers: Additional headers to set during the request.

        :param int generation: If specified, gets the ACL for a specific
            generation of a versioned object. If not specified, the current
            version is returned.

        :rtype: str
        """
        if self.bucket is not None:
            return self.bucket.get_xml_acl(self.name, headers=headers,
                                           generation=generation)

    def set_xml_acl(self, acl_str, headers=None, generation=None,
                     if_generation=None, if_metageneration=None):
        """Sets this objects's ACL to an XML string.

        :type acl_str: string
        :param acl_str: A string containing the ACL XML.

        :type headers: dict
        :param headers: Additional headers to set during the request.

        :type generation: int
        :param generation: If specified, sets the ACL for a specific generation
            of a versioned object. If not specified, the current version is
            modified.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the acl
            will only be updated if its current generation number is this value.

        :type if_metageneration: int
        :param if_metageneration: (optional) If set to a metageneration number,
            the acl will only be updated if its current metageneration number is
            this value.
        """
        if self.bucket is not None:
            return self.bucket.set_xml_acl(acl_str, self.name, headers=headers,
                                           generation=generation,
                                           if_generation=if_generation,
                                           if_metageneration=if_metageneration)

    def set_canned_acl(self, acl_str, headers=None, generation=None,
                       if_generation=None, if_metageneration=None):
        """Sets this objects's ACL using a predefined (canned) value.

        :type acl_str: string
        :param acl_str: A canned ACL string. See
            :data:`~.gs.acl.CannedACLStrings`.

        :type headers: dict
        :param headers: Additional headers to set during the request.

        :type generation: int
        :param generation: If specified, sets the ACL for a specific generation
            of a versioned object. If not specified, the current version is
            modified.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the acl
            will only be updated if its current generation number is this value.

        :type if_metageneration: int
        :param if_metageneration: (optional) If set to a metageneration number,
            the acl will only be updated if its current metageneration number is
            this value.
        """
        if self.bucket is not None:
            return self.bucket.set_canned_acl(
                acl_str,
                self.name,
                headers=headers,
                generation=generation,
                if_generation=if_generation,
                if_metageneration=if_metageneration
            )

    def compose(self, components, content_type=None, headers=None):
        """Create a new object from a sequence of existing objects.

        The content of the object representing this Key will be the
        concatenation of the given object sequence. For more detail, visit

            https://developers.google.com/storage/docs/composite-objects

        :type components list of Keys
        :param components List of gs.Keys representing the component objects

        :type content_type (optional) string
        :param content_type Content type for the new composite object.
        """
        compose_req = []
        for key in components:
            if key.bucket.name != self.bucket.name:
                raise BotoClientError(
                    'GCS does not support inter-bucket composing')

            generation_tag = ''
            if key.generation:
                generation_tag = ('<Generation>%s</Generation>'
                                  % str(key.generation))
            compose_req.append('<Component><Name>%s</Name>%s</Component>' %
                               (key.name, generation_tag))
        compose_req_xml = ('<ComposeRequest>%s</ComposeRequest>' %
                         ''.join(compose_req))
        headers = headers or {}
        if content_type:
            headers['Content-Type'] = content_type
        resp = self.bucket.connection.make_request(
            'PUT', self.bucket.name, self.name,
            headers=headers, query_args='compose',
            data=compose_req_xml)
        if resp.status < 200 or resp.status > 299:
            raise self.bucket.connection.provider.storage_response_error(
                resp.status, resp.reason, resp.read())

        # Return the generation so that the result URI can be built with this
        # for automatic parallel uploads.
        return resp.getheader('x-goog-generation')
