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

"""
Provides basic mocks of core storage service classes, for unit testing:
ACL, Key, Bucket, Connection, and StorageUri. We implement a subset of
the interfaces defined in the real boto classes, but don't handle most
of the optional params (which we indicate with the constant "NOT_IMPL").
"""

import copy
import boto
import base64
import re
import six
from hashlib import md5

from boto.utils import compute_md5
from boto.utils import find_matching_headers
from boto.utils import merge_headers_by_name
from boto.utils import write_to_fd
from boto.s3.prefix import Prefix
from boto.compat import six

NOT_IMPL = None


class MockAcl(object):

    def __init__(self, parent=NOT_IMPL):
        pass

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        pass

    def to_xml(self):
        return '<mock_ACL_XML/>'


class MockKey(object):

    def __init__(self, bucket=None, name=None):
        self.bucket = bucket
        self.name = name
        self.data = None
        self.etag = None
        self.size = None
        self.closed = True
        self.content_encoding = None
        self.content_language = None
        self.content_type = None
        self.last_modified = 'Wed, 06 Oct 2010 05:11:54 GMT'
        self.BufferSize = 8192

    def __repr__(self):
        if self.bucket:
            return '<MockKey: %s,%s>' % (self.bucket.name, self.name)
        else:
            return '<MockKey: %s>' % self.name

    def get_contents_as_string(self, headers=NOT_IMPL,
                               cb=NOT_IMPL, num_cb=NOT_IMPL,
                               torrent=NOT_IMPL,
                               version_id=NOT_IMPL):
        return self.data

    def get_contents_to_file(self, fp, headers=NOT_IMPL,
                             cb=NOT_IMPL, num_cb=NOT_IMPL,
                             torrent=NOT_IMPL,
                             version_id=NOT_IMPL,
                             res_download_handler=NOT_IMPL):
        data = six.ensure_binary(self.data)
        write_to_fd(fp, data)

    def get_file(self, fp, headers=NOT_IMPL, cb=NOT_IMPL, num_cb=NOT_IMPL,
                 torrent=NOT_IMPL, version_id=NOT_IMPL,
                 override_num_retries=NOT_IMPL):
        data = six.ensure_binary(self.data)
        write_to_fd(fp, data)

    def _handle_headers(self, headers):
        if not headers:
            return
        if find_matching_headers('Content-Encoding', headers):
            self.content_encoding = merge_headers_by_name('Content-Encoding',
                                                          headers)
        if find_matching_headers('Content-Type', headers):
            self.content_type = merge_headers_by_name('Content-Type', headers)
        if find_matching_headers('Content-Language', headers):
            self.content_language = merge_headers_by_name('Content-Language',
                                                          headers)

    # Simplistic partial implementation for headers: Just supports range GETs
    # of flavor 'Range: bytes=xyz-'.
    def open_read(self, headers=None, query_args=NOT_IMPL,
                  override_num_retries=NOT_IMPL):
        if self.closed:
            self.read_pos = 0
        self.closed = False
        if headers and 'Range' in headers:
            match = re.match('bytes=([0-9]+)-$', headers['Range'])
            if match:
                self.read_pos = int(match.group(1))

    def close(self, fast=NOT_IMPL):
      self.closed = True

    def read(self, size=0):
        self.open_read()
        if size == 0:
            data = self.data[self.read_pos:]
            self.read_pos = self.size
        else:
            data = self.data[self.read_pos:self.read_pos+size]
            self.read_pos += size
        if not data:
            self.close()
        return data

    def set_contents_from_file(self, fp, headers=None, replace=NOT_IMPL,
                               cb=NOT_IMPL, num_cb=NOT_IMPL,
                               policy=NOT_IMPL, md5=NOT_IMPL,
                               res_upload_handler=NOT_IMPL):
        self.data = fp.read()
        self.set_etag()
        self.size = len(self.data)
        self._handle_headers(headers)

    def set_contents_from_stream(self, fp, headers=None, replace=NOT_IMPL,
                               cb=NOT_IMPL, num_cb=NOT_IMPL, policy=NOT_IMPL,
                               reduced_redundancy=NOT_IMPL, query_args=NOT_IMPL,
                               size=NOT_IMPL):
        self.data = ''
        chunk = fp.read(self.BufferSize)
        while chunk:
          self.data += chunk
          chunk = fp.read(self.BufferSize)
        self.set_etag()
        self.size = len(self.data)
        self._handle_headers(headers)

    def set_contents_from_string(self, s, headers=NOT_IMPL, replace=NOT_IMPL,
                                 cb=NOT_IMPL, num_cb=NOT_IMPL, policy=NOT_IMPL,
                                 md5=NOT_IMPL, reduced_redundancy=NOT_IMPL):
        self.data = copy.copy(s)
        self.set_etag()
        self.size = len(s)
        self._handle_headers(headers)

    def set_contents_from_filename(self, filename, headers=None,
                                   replace=NOT_IMPL, cb=NOT_IMPL,
                                   num_cb=NOT_IMPL, policy=NOT_IMPL,
                                   md5=NOT_IMPL, res_upload_handler=NOT_IMPL):
        fp = open(filename, 'rb')
        self.set_contents_from_file(fp, headers, replace, cb, num_cb,
                                    policy, md5, res_upload_handler)
        fp.close()

    def copy(self, dst_bucket_name, dst_key, metadata=NOT_IMPL,
             reduced_redundancy=NOT_IMPL, preserve_acl=NOT_IMPL):
        dst_bucket = self.bucket.connection.get_bucket(dst_bucket_name)
        return dst_bucket.copy_key(dst_key, self.bucket.name,
                                   self.name, metadata)

    @property
    def provider(self):
        provider = None
        if self.bucket and self.bucket.connection:
            provider = self.bucket.connection.provider
        return provider

    def set_etag(self):
        """
        Set etag attribute by generating hex MD5 checksum on current
        contents of mock key.
        """
        m = md5()
        if not isinstance(self.data, bytes):
            m.update(self.data.encode('utf-8'))
        else:
            m.update(self.data)
        hex_md5 = m.hexdigest()
        self.etag = hex_md5

    def compute_md5(self, fp):
        """
        :type fp: file
        :param fp: File pointer to the file to MD5 hash.  The file pointer
                   will be reset to the beginning of the file before the
                   method returns.

        :rtype: tuple
        :return: A tuple containing the hex digest version of the MD5 hash
                 as the first element and the base64 encoded version of the
                 plain digest as the second element.
        """
        tup = compute_md5(fp)
        # Returned values are MD5 hash, base64 encoded MD5 hash, and file size.
        # The internal implementation of compute_md5() needs to return the
        # file size but we don't want to return that value to the external
        # caller because it changes the class interface (i.e. it might
        # break some code) so we consume the third tuple value here and
        # return the remainder of the tuple to the caller, thereby preserving
        # the existing interface.
        self.size = tup[2]
        return tup[0:2]

class MockBucket(object):

    def __init__(self, connection=None, name=None, key_class=NOT_IMPL):
        self.name = name
        self.keys = {}
        self.acls = {name: MockAcl()}
        # default object ACLs are one per bucket and not supported for keys
        self.def_acl = MockAcl()
        self.subresources = {}
        self.connection = connection
        self.logging = False

    def __repr__(self):
        return 'MockBucket: %s' % self.name

    def copy_key(self, new_key_name, src_bucket_name,
                 src_key_name, metadata=NOT_IMPL, src_version_id=NOT_IMPL,
                 storage_class=NOT_IMPL, preserve_acl=NOT_IMPL,
                 encrypt_key=NOT_IMPL, headers=NOT_IMPL, query_args=NOT_IMPL):
        new_key = self.new_key(key_name=new_key_name)
        src_key = self.connection.get_bucket(
            src_bucket_name).get_key(src_key_name)
        new_key.data = copy.copy(src_key.data)
        new_key.size = len(new_key.data)
        return new_key

    def disable_logging(self):
        self.logging = False

    def enable_logging(self, target_bucket_prefix):
        self.logging = True

    def get_logging_config(self):
        return {"Logging": {}}

    def get_versioning_status(self, headers=NOT_IMPL):
        return False

    def get_acl(self, key_name='', headers=NOT_IMPL, version_id=NOT_IMPL):
        if key_name:
            # Return ACL for the key.
            return self.acls[key_name]
        else:
            # Return ACL for the bucket.
            return self.acls[self.name]

    def get_def_acl(self, key_name=NOT_IMPL, headers=NOT_IMPL,
                    version_id=NOT_IMPL):
        # Return default ACL for the bucket.
        return self.def_acl

    def get_subresource(self, subresource, key_name=NOT_IMPL, headers=NOT_IMPL,
                        version_id=NOT_IMPL):
        if subresource in self.subresources:
            return self.subresources[subresource]
        else:
            return '<Subresource/>'

    def get_tags(self):
      return []

    def new_key(self, key_name=None):
        mock_key = MockKey(self, key_name)
        self.keys[key_name] = mock_key
        self.acls[key_name] = MockAcl()
        return mock_key

    def delete_key(self, key_name, headers=NOT_IMPL,
                   version_id=NOT_IMPL, mfa_token=NOT_IMPL):
        if key_name not in self.keys:
            raise boto.exception.StorageResponseError(404, 'Not Found')
        del self.keys[key_name]

    def get_all_keys(self, headers=NOT_IMPL):
        return six.itervalues(self.keys)

    def get_key(self, key_name, headers=NOT_IMPL, version_id=NOT_IMPL):
        # Emulate behavior of boto when get_key called with non-existent key.
        if key_name not in self.keys:
            return None
        return self.keys[key_name]

    def list(self, prefix='', delimiter='', marker=NOT_IMPL,
             headers=NOT_IMPL):
        prefix = prefix or '' # Turn None into '' for prefix match.
        # Return list instead of using a generator so we don't get
        # 'dictionary changed size during iteration' error when performing
        # deletions while iterating (e.g., during test cleanup).
        result = []
        key_name_set = set()
        for k in six.itervalues(self.keys):
            if k.name.startswith(prefix):
                k_name_past_prefix = k.name[len(prefix):]
                if delimiter:
                  pos = k_name_past_prefix.find(delimiter)
                else:
                  pos = -1
                if (pos != -1):
                    key_or_prefix = Prefix(
                        bucket=self, name=k.name[:len(prefix)+pos+1])
                else:
                    key_or_prefix = MockKey(bucket=self, name=k.name)
                if key_or_prefix.name not in key_name_set:
                    key_name_set.add(key_or_prefix.name)
                    result.append(key_or_prefix)
        return result

    def set_acl(self, acl_or_str, key_name='', headers=NOT_IMPL,
                version_id=NOT_IMPL):
        # We only handle setting ACL XML here; if you pass a canned ACL
        # the get_acl call will just return that string name.
        if key_name:
            # Set ACL for the key.
            self.acls[key_name] = MockAcl(acl_or_str)
        else:
            # Set ACL for the bucket.
            self.acls[self.name] = MockAcl(acl_or_str)

    def set_def_acl(self, acl_or_str, key_name=NOT_IMPL, headers=NOT_IMPL,
                    version_id=NOT_IMPL):
        # We only handle setting ACL XML here; if you pass a canned ACL
        # the get_acl call will just return that string name.
        # Set default ACL for the bucket.
        self.def_acl = acl_or_str

    def set_subresource(self, subresource, value, key_name=NOT_IMPL,
                        headers=NOT_IMPL, version_id=NOT_IMPL):
        self.subresources[subresource] = value


class MockProvider(object):

    def __init__(self, provider):
        self.provider = provider

    def get_provider_name(self):
        return self.provider


class MockConnection(object):

    def __init__(self, aws_access_key_id=NOT_IMPL,
                 aws_secret_access_key=NOT_IMPL, is_secure=NOT_IMPL,
                 port=NOT_IMPL, proxy=NOT_IMPL, proxy_port=NOT_IMPL,
                 proxy_user=NOT_IMPL, proxy_pass=NOT_IMPL,
                 host=NOT_IMPL, debug=NOT_IMPL,
                 https_connection_factory=NOT_IMPL,
                 calling_format=NOT_IMPL,
                 path=NOT_IMPL, provider='s3',
                 bucket_class=NOT_IMPL):
        self.buckets = {}
        self.provider = MockProvider(provider)

    def create_bucket(self, bucket_name, headers=NOT_IMPL, location=NOT_IMPL,
                      policy=NOT_IMPL, storage_class=NOT_IMPL):
        if bucket_name in self.buckets:
            raise boto.exception.StorageCreateError(
                409, 'BucketAlreadyOwnedByYou',
                "<Message>Your previous request to create the named bucket "
                "succeeded and you already own it.</Message>")
        mock_bucket = MockBucket(name=bucket_name, connection=self)
        self.buckets[bucket_name] = mock_bucket
        return mock_bucket

    def delete_bucket(self, bucket, headers=NOT_IMPL):
        if bucket not in self.buckets:
            raise boto.exception.StorageResponseError(
                404, 'NoSuchBucket', '<Message>no such bucket</Message>')
        del self.buckets[bucket]

    def get_bucket(self, bucket_name, validate=NOT_IMPL, headers=NOT_IMPL):
        if bucket_name not in self.buckets:
            raise boto.exception.StorageResponseError(404, 'NoSuchBucket',
                                                 'Not Found')
        return self.buckets[bucket_name]

    def get_all_buckets(self, headers=NOT_IMPL):
        return six.itervalues(self.buckets)


# We only mock a single provider/connection.
mock_connection = MockConnection()


class MockBucketStorageUri(object):

    delim = '/'

    def __init__(self, scheme, bucket_name=None, object_name=None,
                 debug=NOT_IMPL, suppress_consec_slashes=NOT_IMPL,
                 version_id=None, generation=None, is_latest=False):
        self.scheme = scheme
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.suppress_consec_slashes = suppress_consec_slashes
        if self.bucket_name and self.object_name:
            self.uri = ('%s://%s/%s' % (self.scheme, self.bucket_name,
                                        self.object_name))
        elif self.bucket_name:
            self.uri = ('%s://%s/' % (self.scheme, self.bucket_name))
        else:
            self.uri = ('%s://' % self.scheme)

        self.version_id = version_id
        self.generation = generation and int(generation)
        self.is_version_specific = (bool(self.generation)
                                    or bool(self.version_id))
        self.is_latest = is_latest
        if bucket_name and object_name:
            self.versionless_uri = '%s://%s/%s' % (scheme, bucket_name,
                                                   object_name)

    def __repr__(self):
        """Returns string representation of URI."""
        return self.uri

    def acl_class(self):
        return MockAcl

    def canned_acls(self):
        return boto.provider.Provider('aws').canned_acls

    def clone_replace_name(self, new_name):
        return self.__class__(self.scheme, self.bucket_name, new_name)

    def clone_replace_key(self, key):
        return self.__class__(
                key.provider.get_provider_name(),
                bucket_name=key.bucket.name,
                object_name=key.name,
                suppress_consec_slashes=self.suppress_consec_slashes,
                version_id=getattr(key, 'version_id', None),
                generation=getattr(key, 'generation', None),
                is_latest=getattr(key, 'is_latest', None))

    def connect(self, access_key_id=NOT_IMPL, secret_access_key=NOT_IMPL):
        return mock_connection

    def create_bucket(self, headers=NOT_IMPL, location=NOT_IMPL,
                      policy=NOT_IMPL, storage_class=NOT_IMPL):
        return self.connect().create_bucket(self.bucket_name)

    def delete_bucket(self, headers=NOT_IMPL):
        return self.connect().delete_bucket(self.bucket_name)

    def get_versioning_config(self, headers=NOT_IMPL):
        self.get_bucket().get_versioning_status(headers)

    def has_version(self):
        return (issubclass(type(self), MockBucketStorageUri)
                and ((self.version_id is not None)
                     or (self.generation is not None)))

    def delete_key(self, validate=NOT_IMPL, headers=NOT_IMPL,
                   version_id=NOT_IMPL, mfa_token=NOT_IMPL):
        self.get_bucket().delete_key(self.object_name)

    def disable_logging(self, validate=NOT_IMPL, headers=NOT_IMPL,
                        version_id=NOT_IMPL):
        self.get_bucket().disable_logging()

    def enable_logging(self, target_bucket, target_prefix, validate=NOT_IMPL,
                       headers=NOT_IMPL, version_id=NOT_IMPL):
        self.get_bucket().enable_logging(target_bucket)

    def get_logging_config(self, validate=NOT_IMPL, headers=NOT_IMPL,
                           version_id=NOT_IMPL):
        return self.get_bucket().get_logging_config()

    def equals(self, uri):
        return self.uri == uri.uri

    def get_acl(self, validate=NOT_IMPL, headers=NOT_IMPL, version_id=NOT_IMPL):
        return self.get_bucket().get_acl(self.object_name)

    def get_def_acl(self, validate=NOT_IMPL, headers=NOT_IMPL,
                    version_id=NOT_IMPL):
        return self.get_bucket().get_def_acl(self.object_name)

    def get_subresource(self, subresource, validate=NOT_IMPL, headers=NOT_IMPL,
                        version_id=NOT_IMPL):
        return self.get_bucket().get_subresource(subresource, self.object_name)

    def get_all_buckets(self, headers=NOT_IMPL):
        return self.connect().get_all_buckets()

    def get_all_keys(self, validate=NOT_IMPL, headers=NOT_IMPL):
        return self.get_bucket().get_all_keys(self)

    def list_bucket(self, prefix='', delimiter='', headers=NOT_IMPL,
                    all_versions=NOT_IMPL):
        return self.get_bucket().list(prefix=prefix, delimiter=delimiter)

    def get_bucket(self, validate=NOT_IMPL, headers=NOT_IMPL):
        return self.connect().get_bucket(self.bucket_name)

    def get_key(self, validate=NOT_IMPL, headers=NOT_IMPL,
                version_id=NOT_IMPL):
        return self.get_bucket().get_key(self.object_name)

    def is_file_uri(self):
        return False

    def is_cloud_uri(self):
        return True

    def names_container(self):
        return bool(not self.object_name)

    def names_singleton(self):
        return bool(self.object_name)

    def names_directory(self):
        return False

    def names_provider(self):
        return bool(not self.bucket_name)

    def names_bucket(self):
        return self.names_container()

    def names_file(self):
        return False

    def names_object(self):
        return not self.names_container()

    def is_stream(self):
        return False

    def new_key(self, validate=NOT_IMPL, headers=NOT_IMPL):
        bucket = self.get_bucket()
        return bucket.new_key(self.object_name)

    def set_acl(self, acl_or_str, key_name='', validate=NOT_IMPL,
                headers=NOT_IMPL, version_id=NOT_IMPL):
        self.get_bucket().set_acl(acl_or_str, key_name)

    def set_def_acl(self, acl_or_str, key_name=NOT_IMPL, validate=NOT_IMPL,
                    headers=NOT_IMPL, version_id=NOT_IMPL):
        self.get_bucket().set_def_acl(acl_or_str)

    def set_subresource(self, subresource, value, validate=NOT_IMPL,
                        headers=NOT_IMPL, version_id=NOT_IMPL):
        self.get_bucket().set_subresource(subresource, value, self.object_name)

    def copy_key(self, src_bucket_name, src_key_name, metadata=NOT_IMPL,
                 src_version_id=NOT_IMPL, storage_class=NOT_IMPL,
                 preserve_acl=NOT_IMPL, encrypt_key=NOT_IMPL, headers=NOT_IMPL,
                 query_args=NOT_IMPL, src_generation=NOT_IMPL):
        dst_bucket = self.get_bucket()
        return dst_bucket.copy_key(new_key_name=self.object_name,
                                   src_bucket_name=src_bucket_name,
                                   src_key_name=src_key_name)

    def set_contents_from_string(self, s, headers=NOT_IMPL, replace=NOT_IMPL,
                                 cb=NOT_IMPL, num_cb=NOT_IMPL, policy=NOT_IMPL,
                                 md5=NOT_IMPL, reduced_redundancy=NOT_IMPL):
        key = self.new_key()
        key.set_contents_from_string(s)

    def set_contents_from_file(self, fp, headers=None, replace=NOT_IMPL,
                               cb=NOT_IMPL, num_cb=NOT_IMPL, policy=NOT_IMPL,
                               md5=NOT_IMPL, size=NOT_IMPL, rewind=NOT_IMPL,
                               res_upload_handler=NOT_IMPL):
        key = self.new_key()
        return key.set_contents_from_file(fp, headers=headers)

    def set_contents_from_stream(self, fp, headers=NOT_IMPL, replace=NOT_IMPL,
                                 cb=NOT_IMPL, num_cb=NOT_IMPL, policy=NOT_IMPL,
                                 reduced_redundancy=NOT_IMPL,
                                 query_args=NOT_IMPL, size=NOT_IMPL):
        dst_key.set_contents_from_stream(fp)

    def get_contents_to_file(self, fp, headers=NOT_IMPL, cb=NOT_IMPL,
                             num_cb=NOT_IMPL, torrent=NOT_IMPL,
                             version_id=NOT_IMPL, res_download_handler=NOT_IMPL,
                             response_headers=NOT_IMPL):
        key = self.get_key()
        key.get_contents_to_file(fp)

    def get_contents_to_stream(self, fp, headers=NOT_IMPL, cb=NOT_IMPL,
                               num_cb=NOT_IMPL, version_id=NOT_IMPL):
        key = self.get_key()
        return key.get_contents_to_file(fp)
