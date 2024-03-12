# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
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

from boto.compat import unquote_str

def bucket_lister(bucket, prefix='', delimiter='', marker='', headers=None,
                  encoding_type=None):
    """
    A generator function for listing keys in a bucket.
    """
    more_results = True
    k = None
    while more_results:
        rs = bucket.get_all_keys(prefix=prefix, marker=marker,
                                 delimiter=delimiter, headers=headers,
                                 encoding_type=encoding_type)
        for k in rs:
            yield k
        if k:
            marker = rs.next_marker or k.name
        if marker and encoding_type == "url":
            marker = unquote_str(marker)
        more_results= rs.is_truncated

class BucketListResultSet(object):
    """
    A resultset for listing keys within a bucket.  Uses the bucket_lister
    generator function and implements the iterator interface.  This
    transparently handles the results paging from S3 so even if you have
    many thousands of keys within the bucket you can iterate over all
    keys in a reasonably efficient manner.
    """

    def __init__(self, bucket=None, prefix='', delimiter='', marker='',
                 headers=None, encoding_type=None):
        self.bucket = bucket
        self.prefix = prefix
        self.delimiter = delimiter
        self.marker = marker
        self.headers = headers
        self.encoding_type = encoding_type

    def __iter__(self):
        return bucket_lister(self.bucket, prefix=self.prefix,
                             delimiter=self.delimiter, marker=self.marker,
                             headers=self.headers,
                             encoding_type=self.encoding_type)

def versioned_bucket_lister(bucket, prefix='', delimiter='',
                            key_marker='', version_id_marker='', headers=None,
                            encoding_type=None):
    """
    A generator function for listing versions in a bucket.
    """
    more_results = True
    k = None
    while more_results:
        rs = bucket.get_all_versions(prefix=prefix, key_marker=key_marker,
                                     version_id_marker=version_id_marker,
                                     delimiter=delimiter, headers=headers,
                                     max_keys=999, encoding_type=encoding_type)
        for k in rs:
            yield k
        key_marker = rs.next_key_marker
        if key_marker and encoding_type == "url":
            key_marker = unquote_str(key_marker)
        version_id_marker = rs.next_version_id_marker
        more_results= rs.is_truncated

class VersionedBucketListResultSet(object):
    """
    A resultset for listing versions within a bucket.  Uses the bucket_lister
    generator function and implements the iterator interface.  This
    transparently handles the results paging from S3 so even if you have
    many thousands of keys within the bucket you can iterate over all
    keys in a reasonably efficient manner.
    """

    def __init__(self, bucket=None, prefix='', delimiter='', key_marker='',
                 version_id_marker='', headers=None, encoding_type=None):
        self.bucket = bucket
        self.prefix = prefix
        self.delimiter = delimiter
        self.key_marker = key_marker
        self.version_id_marker = version_id_marker
        self.headers = headers
        self.encoding_type = encoding_type

    def __iter__(self):
        return versioned_bucket_lister(self.bucket, prefix=self.prefix,
                                       delimiter=self.delimiter,
                                       key_marker=self.key_marker,
                                       version_id_marker=self.version_id_marker,
                                       headers=self.headers,
                                       encoding_type=self.encoding_type)

def multipart_upload_lister(bucket, key_marker='',
                            upload_id_marker='',
                            headers=None, encoding_type=None):
    """
    A generator function for listing multipart uploads in a bucket.
    """
    more_results = True
    k = None
    while more_results:
        rs = bucket.get_all_multipart_uploads(key_marker=key_marker,
                                              upload_id_marker=upload_id_marker,
                                              headers=headers,
                                              encoding_type=encoding_type)
        for k in rs:
            yield k
        key_marker = rs.next_key_marker
        if key_marker and encoding_type == "url":
            key_marker = unquote_str(key_marker)
        upload_id_marker = rs.next_upload_id_marker
        more_results= rs.is_truncated

class MultiPartUploadListResultSet(object):
    """
    A resultset for listing multipart uploads within a bucket.
    Uses the multipart_upload_lister generator function and
    implements the iterator interface.  This
    transparently handles the results paging from S3 so even if you have
    many thousands of uploads within the bucket you can iterate over all
    keys in a reasonably efficient manner.
    """
    def __init__(self, bucket=None, key_marker='',
                 upload_id_marker='', headers=None, encoding_type=None):
        self.bucket = bucket
        self.key_marker = key_marker
        self.upload_id_marker = upload_id_marker
        self.headers = headers
        self.encoding_type = encoding_type

    def __iter__(self):
        return multipart_upload_lister(self.bucket,
                                       key_marker=self.key_marker,
                                       upload_id_marker=self.upload_id_marker,
                                       headers=self.headers,
                                       encoding_type=self.encoding_type)
