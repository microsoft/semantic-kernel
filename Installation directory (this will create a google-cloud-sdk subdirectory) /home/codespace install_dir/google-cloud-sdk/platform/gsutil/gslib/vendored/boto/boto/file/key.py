# Copyright 2010 Google Inc.
# Copyright (c) 2011, Nexenta Systems Inc.
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

# File representation of key, for use with "file://" URIs.

import os, shutil
import sys

from boto.compat import StringIO

class Key(object):

    KEY_STREAM_READABLE = 0x01
    KEY_STREAM_WRITABLE = 0x02
    KEY_STREAM          = (KEY_STREAM_READABLE | KEY_STREAM_WRITABLE)
    KEY_REGULAR_FILE    = 0x00

    def __init__(self, bucket, name, fp=None, key_type=KEY_REGULAR_FILE):
        self.bucket = bucket
        self.full_path = name
        if name == '-':
            self.name = None
            self.size = None
        else:
            self.name = name
            self.size = os.stat(name).st_size
        self.key_type = key_type
        if key_type == self.KEY_STREAM_READABLE:
            self.fp = sys.stdin
            self.full_path = '<STDIN>'
        elif key_type == self.KEY_STREAM_WRITABLE:
            self.fp = sys.stdout
            self.full_path = '<STDOUT>'
        else:
            self.fp = fp

    def __str__(self):
        return 'file://' + self.full_path

    def get_file(self, fp, headers=None, cb=None, num_cb=10, torrent=False):
        """
        Retrieves a file from a Key

        :type fp: file
        :param fp: File pointer to put the data into

        :type headers: string
        :param: ignored in this subclass.

        :type cb: function
        :param cb: ignored in this subclass.

        :type cb: int
        :param num_cb: ignored in this subclass.
        """
        if self.key_type & self.KEY_STREAM_WRITABLE:
            raise BotoClientError('Stream is not readable')
        elif self.key_type & self.KEY_STREAM_READABLE:
            key_file = self.fp
        else:
            key_file = open(self.full_path, 'rb')
        try:
            shutil.copyfileobj(key_file, fp)
        finally:
            key_file.close()

    def set_contents_from_file(self, fp, headers=None, replace=True, cb=None,
                               num_cb=10, policy=None, md5=None):
        """
        Store an object in a file using the name of the Key object as the
        key in file URI and the contents of the file pointed to by 'fp' as the
        contents.

        :type fp: file
        :param fp: the file whose contents to upload

        :type headers: dict
        :param headers: ignored in this subclass.

        :type replace: bool
        :param replace: If this parameter is False, the method
                        will first check to see if an object exists in the
                        bucket with the same key.  If it does, it won't
                        overwrite it.  The default value is True which will
                        overwrite the object.

        :type cb: function
        :param cb: ignored in this subclass.

        :type cb: int
        :param num_cb: ignored in this subclass.

        :type policy: :class:`boto.s3.acl.CannedACLStrings`
        :param policy: ignored in this subclass.

        :type md5: A tuple containing the hexdigest version of the MD5 checksum
                   of the file as the first element and the Base64-encoded
                   version of the plain checksum as the second element.
                   This is the same format returned by the compute_md5 method.
        :param md5: ignored in this subclass.
        """
        if self.key_type & self.KEY_STREAM_READABLE:
            raise BotoClientError('Stream is not writable')
        elif self.key_type & self.KEY_STREAM_WRITABLE:
            key_file = self.fp
        else:
            if not replace and os.path.exists(self.full_path):
                return
            key_file = open(self.full_path, 'wb')
        try:
            shutil.copyfileobj(fp, key_file)
        finally:
            key_file.close()

    def get_contents_to_file(self, fp, headers=None, cb=None, num_cb=None,
                             torrent=False, version_id=None,
                             res_download_handler=None, response_headers=None):
        """
        Copy contents from the current file to the file pointed to by 'fp'.

        :type fp: File-like object
        :param fp:

        :type headers: dict
        :param headers: Unused in this subclass.

        :type cb: function
        :param cb: Unused in this subclass.

        :type cb: int
        :param num_cb: Unused in this subclass.

        :type torrent: bool
        :param torrent: Unused in this subclass.

        :type res_upload_handler: ResumableDownloadHandler
        :param res_download_handler: Unused in this subclass.

        :type response_headers: dict
        :param response_headers: Unused in this subclass.
        """
        shutil.copyfileobj(self.fp, fp)

    def get_contents_as_string(self, headers=None, cb=None, num_cb=10,
                               torrent=False):
        """
        Retrieve file data from the Key, and return contents as a string.

        :type headers: dict
        :param headers: ignored in this subclass.

        :type cb: function
        :param cb: ignored in this subclass.

        :type cb: int
        :param num_cb: ignored in this subclass.

        :type cb: int
        :param num_cb: ignored in this subclass.

        :type torrent: bool
        :param torrent: ignored in this subclass.

        :rtype: string
        :returns: The contents of the file as a string
        """

        fp = StringIO()
        self.get_contents_to_file(fp)
        return fp.getvalue()

    def is_stream(self):
        return (self.key_type & self.KEY_STREAM)

    def close(self):
        """
        Closes fp associated with underlying file.
        Caller should call this method when done with this class, to avoid
        using up OS resources (e.g., when iterating over a large number
        of files).
        """
        self.fp.close()
