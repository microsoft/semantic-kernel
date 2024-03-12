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

import boto
import os
import sys
import textwrap
from boto.s3.deletemarker import DeleteMarker
from boto.exception import BotoClientError
from boto.exception import InvalidUriError


class StorageUri(object):
    """
    Base class for representing storage provider-independent bucket and
    object name with a shorthand URI-like syntax.

    This is an abstract class: the constructor cannot be called (throws an
    exception if you try).
    """

    connection = None
    # Optional args that can be set from one of the concrete subclass
    # constructors, to change connection behavior (e.g., to override
    # https_connection_factory).
    connection_args = None

    # Map of provider scheme ('s3' or 'gs') to AWSAuthConnection object. We
    # maintain a pool here in addition to the connection pool implemented
    # in AWSAuthConnection because the latter re-creates its connection pool
    # every time that class is instantiated (so the current pool is used to
    # avoid re-instantiating AWSAuthConnection).
    provider_pool = {}

    def __init__(self):
        """Uncallable constructor on abstract base StorageUri class.
        """
        raise BotoClientError('Attempt to instantiate abstract StorageUri '
                              'class')

    def __repr__(self):
        """Returns string representation of URI."""
        return self.uri

    def equals(self, uri):
        """Returns true if two URIs are equal."""
        return self.uri == uri.uri

    def check_response(self, resp, level, uri):
        if resp is None:
            raise InvalidUriError('\n'.join(textwrap.wrap(
                'Attempt to get %s for "%s" failed. This can happen if '
                'the URI refers to a non-existent object or if you meant to '
                'operate on a directory (e.g., leaving off -R option on gsutil '
                'cp, mv, or ls of a bucket)' % (level, uri), 80)))

    def _check_bucket_uri(self, function_name):
        if issubclass(type(self), BucketStorageUri) and not self.bucket_name:
            raise InvalidUriError(
                '%s on bucket-less URI (%s)' % (function_name, self.uri))

    def _check_object_uri(self, function_name):
        if issubclass(type(self), BucketStorageUri) and not self.object_name:
            raise InvalidUriError('%s on object-less URI (%s)' %
                                  (function_name, self.uri))

    def _warn_about_args(self, function_name, **args):
        for arg in args:
            if args[arg]:
                sys.stderr.write(
                    'Warning: %s ignores argument: %s=%s\n' %
                    (function_name, arg, str(args[arg])))

    def connect(self, access_key_id=None, secret_access_key=None, **kwargs):
        """
        Opens a connection to appropriate provider, depending on provider
        portion of URI. Requires Credentials defined in boto config file (see
        boto/pyami/config.py).
        @type storage_uri: StorageUri
        @param storage_uri: StorageUri specifying a bucket or a bucket+object
        @rtype: L{AWSAuthConnection<boto.gs.connection.AWSAuthConnection>}
        @return: A connection to storage service provider of the given URI.
        """
        connection_args = dict(self.connection_args or ())

        if (hasattr(self, 'suppress_consec_slashes') and
                'suppress_consec_slashes' not in connection_args):
            connection_args['suppress_consec_slashes'] = (
                self.suppress_consec_slashes)
        connection_args.update(kwargs)
        if not self.connection:
            if self.scheme in self.provider_pool:
                self.connection = self.provider_pool[self.scheme]
            elif self.scheme == 's3':
                from boto.s3.connection import S3Connection
                self.connection = S3Connection(access_key_id,
                                               secret_access_key,
                                               **connection_args)
                self.provider_pool[self.scheme] = self.connection
            elif self.scheme == 'gs':
                from boto.gs.connection import GSConnection
                self.connection = GSConnection(access_key_id,
                                               secret_access_key,
                                               **connection_args)
                self.provider_pool[self.scheme] = self.connection
            elif self.scheme == 'file':
                from boto.file.connection import FileConnection
                self.connection = FileConnection(self)
            else:
                raise InvalidUriError('Unrecognized scheme "%s"' %
                                      self.scheme)
        self.connection.debug = self.debug
        return self.connection

    def has_version(self):
        return (issubclass(type(self), BucketStorageUri)
                and ((self.version_id is not None)
                     or (self.generation is not None)))

    def delete_key(self, validate=False, headers=None, version_id=None,
                   mfa_token=None):
        self._check_object_uri('delete_key')
        bucket = self.get_bucket(validate, headers)
        return bucket.delete_key(self.object_name, headers, version_id,
                                 mfa_token)

    def list_bucket(self, prefix='', delimiter='', headers=None,
                    all_versions=False):
        self._check_bucket_uri('list_bucket')
        bucket = self.get_bucket(headers=headers)
        if all_versions:
            return (v for v in bucket.list_versions(
                prefix=prefix, delimiter=delimiter, headers=headers)
                if not isinstance(v, DeleteMarker))
        else:
            return bucket.list(prefix=prefix, delimiter=delimiter,
                               headers=headers)

    def get_all_keys(self, validate=False, headers=None, prefix=None):
        bucket = self.get_bucket(validate, headers)
        return bucket.get_all_keys(headers)

    def get_bucket(self, validate=False, headers=None):
        self._check_bucket_uri('get_bucket')
        conn = self.connect()
        bucket = conn.get_bucket(self.bucket_name, validate, headers)
        self.check_response(bucket, 'bucket', self.uri)
        return bucket

    def get_key(self, validate=False, headers=None, version_id=None):
        self._check_object_uri('get_key')
        bucket = self.get_bucket(validate, headers)
        key = bucket.get_key(self.object_name, headers, version_id)
        self.check_response(key, 'key', self.uri)
        return key

    def new_key(self, validate=False, headers=None):
        self._check_object_uri('new_key')
        bucket = self.get_bucket(validate, headers)
        return bucket.new_key(self.object_name)

    def get_contents_to_stream(self, fp, headers=None, version_id=None):
        self._check_object_uri('get_key')
        self._warn_about_args('get_key', validate=False)
        key = self.get_key(None, headers)
        self.check_response(key, 'key', self.uri)
        return key.get_contents_to_file(fp, headers, version_id=version_id)

    def get_contents_to_file(self, fp, headers=None, cb=None, num_cb=10,
                             torrent=False, version_id=None,
                             res_download_handler=None, response_headers=None,
                             hash_algs=None):
        self._check_object_uri('get_contents_to_file')
        key = self.get_key(None, headers)
        self.check_response(key, 'key', self.uri)
        if hash_algs:
            key.get_contents_to_file(fp, headers, cb, num_cb, torrent,
                                     version_id, res_download_handler,
                                     response_headers,
                                     hash_algs=hash_algs)
        else:
            key.get_contents_to_file(fp, headers, cb, num_cb, torrent,
                                     version_id, res_download_handler,
                                     response_headers)

    def get_contents_as_string(self, validate=False, headers=None, cb=None,
                               num_cb=10, torrent=False, version_id=None):
        self._check_object_uri('get_contents_as_string')
        key = self.get_key(validate, headers)
        self.check_response(key, 'key', self.uri)
        return key.get_contents_as_string(headers, cb, num_cb, torrent,
                                          version_id)

    def acl_class(self):
        conn = self.connect()
        acl_class = conn.provider.acl_class
        self.check_response(acl_class, 'acl_class', self.uri)
        return acl_class

    def canned_acls(self):
        conn = self.connect()
        canned_acls = conn.provider.canned_acls
        self.check_response(canned_acls, 'canned_acls', self.uri)
        return canned_acls


class BucketStorageUri(StorageUri):
    """
    StorageUri subclass that handles bucket storage providers.
    Callers should instantiate this class by calling boto.storage_uri().
    """

    delim = '/'
    capabilities = set([])  # A set of additional capabilities.

    def __init__(self, scheme, bucket_name=None, object_name=None,
                 debug=0, connection_args=None, suppress_consec_slashes=True,
                 version_id=None, generation=None, is_latest=False):
        """Instantiate a BucketStorageUri from scheme,bucket,object tuple.

        @type scheme: string
        @param scheme: URI scheme naming the storage provider (gs, s3, etc.)
        @type bucket_name: string
        @param bucket_name: bucket name
        @type object_name: string
        @param object_name: object name, excluding generation/version.
        @type debug: int
        @param debug: debug level to pass in to connection (range 0..2)
        @type connection_args: map
        @param connection_args: optional map containing args to be
            passed to {S3,GS}Connection constructor (e.g., to override
            https_connection_factory).
        @param suppress_consec_slashes: If provided, controls whether
            consecutive slashes will be suppressed in key paths.
        @param version_id: Object version id (S3-specific).
        @param generation: Object generation number (GCS-specific).
        @param is_latest: boolean indicating that a versioned object is the
            current version

        After instantiation the components are available in the following
        fields: scheme, bucket_name, object_name, version_id, generation,
        is_latest, versionless_uri, version_specific_uri, uri.
        Note: If instantiated without version info, the string representation
        for a URI stays versionless; similarly, if instantiated with version
        info, the string representation for a URI stays version-specific. If you
        call one of the uri.set_contents_from_xyz() methods, a specific object
        version will be created, and its version-specific URI string can be
        retrieved from version_specific_uri even if the URI was instantiated
        without version info.
        """

        self.scheme = scheme
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.debug = debug
        if connection_args:
            self.connection_args = connection_args
        self.suppress_consec_slashes = suppress_consec_slashes
        self.version_id = version_id
        self.generation = generation and int(generation)
        self.is_latest = is_latest
        self.is_version_specific = bool(self.generation) or bool(version_id)
        self._build_uri_strings()

    def _build_uri_strings(self):
        if self.bucket_name and self.object_name:
            self.versionless_uri = '%s://%s/%s' % (self.scheme, self.bucket_name,
                                                   self.object_name)
            if self.generation:
                self.version_specific_uri = '%s#%s' % (self.versionless_uri,
                                                       self.generation)
            elif self.version_id:
                self.version_specific_uri = '%s#%s' % (
                    self.versionless_uri, self.version_id)
            if self.is_version_specific:
                self.uri = self.version_specific_uri
            else:
                self.uri = self.versionless_uri
        elif self.bucket_name:
            self.uri = ('%s://%s/' % (self.scheme, self.bucket_name))
        else:
            self.uri = ('%s://' % self.scheme)

    def _update_from_key(self, key):
        self._update_from_values(
            getattr(key, 'version_id', None),
            getattr(key, 'generation', None),
            getattr(key, 'is_latest', None),
            getattr(key, 'md5', None))

    def _update_from_values(self, version_id, generation, is_latest, md5):
        self.version_id = version_id
        self.generation = generation
        self.is_latest = is_latest
        self._build_uri_strings()
        self.md5 = md5

    def get_key(self, validate=False, headers=None, version_id=None):
        self._check_object_uri('get_key')
        bucket = self.get_bucket(validate, headers)
        if self.get_provider().name == 'aws':
            key = bucket.get_key(self.object_name, headers,
                                 version_id=(version_id or self.version_id))
        elif self.get_provider().name == 'google':
            key = bucket.get_key(self.object_name, headers,
                                 generation=self.generation)
        self.check_response(key, 'key', self.uri)
        return key

    def delete_key(self, validate=False, headers=None, version_id=None,
                   mfa_token=None):
        self._check_object_uri('delete_key')
        bucket = self.get_bucket(validate, headers)
        if self.get_provider().name == 'aws':
            version_id = version_id or self.version_id
            return bucket.delete_key(self.object_name, headers, version_id,
                                     mfa_token)
        elif self.get_provider().name == 'google':
            return bucket.delete_key(self.object_name, headers,
                                     generation=self.generation)

    def clone_replace_name(self, new_name):
        """Instantiate a BucketStorageUri from the current BucketStorageUri,
        but replacing the object_name.

        @type new_name: string
        @param new_name: new object name
        """
        self._check_bucket_uri('clone_replace_name')
        return BucketStorageUri(
            self.scheme, bucket_name=self.bucket_name, object_name=new_name,
            debug=self.debug,
            suppress_consec_slashes=self.suppress_consec_slashes)

    def clone_replace_key(self, key):
        """Instantiate a BucketStorageUri from the current BucketStorageUri, by
        replacing the object name with the object name and other metadata found
        in the given Key object (including generation).

        @type key: Key
        @param key: key for the new StorageUri to represent
        """
        self._check_bucket_uri('clone_replace_key')
        version_id = None
        generation = None
        is_latest = False
        if hasattr(key, 'version_id'):
            version_id = key.version_id
        if hasattr(key, 'generation'):
            generation = key.generation
        if hasattr(key, 'is_latest'):
            is_latest = key.is_latest

        return BucketStorageUri(
            key.provider.get_provider_name(),
            bucket_name=key.bucket.name,
            object_name=key.name,
            debug=self.debug,
            suppress_consec_slashes=self.suppress_consec_slashes,
            version_id=version_id,
            generation=generation,
            is_latest=is_latest)

    def get_acl(self, validate=False, headers=None, version_id=None):
        """returns a bucket's acl"""
        self._check_bucket_uri('get_acl')
        bucket = self.get_bucket(validate, headers)
        # This works for both bucket- and object- level ACLs (former passes
        # key_name=None):
        key_name = self.object_name or ''
        if self.get_provider().name == 'aws':
            version_id = version_id or self.version_id
            acl = bucket.get_acl(key_name, headers, version_id)
        else:
            acl = bucket.get_acl(key_name, headers, generation=self.generation)
        self.check_response(acl, 'acl', self.uri)
        return acl

    def get_def_acl(self, validate=False, headers=None):
        """returns a bucket's default object acl"""
        self._check_bucket_uri('get_def_acl')
        bucket = self.get_bucket(validate, headers)
        acl = bucket.get_def_acl(headers)
        self.check_response(acl, 'acl', self.uri)
        return acl

    def get_cors(self, validate=False, headers=None):
        """returns a bucket's CORS XML"""
        self._check_bucket_uri('get_cors')
        bucket = self.get_bucket(validate, headers)
        cors = bucket.get_cors(headers)
        self.check_response(cors, 'cors', self.uri)
        return cors

    def set_cors(self, cors, validate=False, headers=None):
        """sets or updates a bucket's CORS XML"""
        self._check_bucket_uri('set_cors ')
        bucket = self.get_bucket(validate, headers)
        if self.scheme == 's3':
          bucket.set_cors(cors, headers)
        else:
          bucket.set_cors(cors.to_xml(), headers)

    def get_location(self, validate=False, headers=None):
        self._check_bucket_uri('get_location')
        bucket = self.get_bucket(validate, headers)
        return bucket.get_location(headers)

    def get_storage_class(self, validate=False, headers=None):
        self._check_bucket_uri('get_storage_class')
        # StorageClass is defined as a bucket and object param for GCS, but
        # only as a key param for S3.
        if self.scheme != 'gs':
            raise ValueError('get_storage_class() not supported for %s '
                             'URIs.' % self.scheme)
        bucket = self.get_bucket(validate, headers)
        return bucket.get_storage_class(headers)

    def set_storage_class(self, storage_class, validate=False, headers=None):
        """Updates a bucket's storage class."""
        self._check_bucket_uri('set_storage_class')
        # StorageClass is defined as a bucket and object param for GCS, but
        # only as a key param for S3.
        if self.scheme != 'gs':
            raise ValueError('set_storage_class() not supported for %s '
                             'URIs.' % self.scheme)
        bucket = self.get_bucket(validate, headers)
        bucket.set_storage_class(storage_class, headers)

    def get_subresource(self, subresource, validate=False, headers=None,
                        version_id=None):
        self._check_bucket_uri('get_subresource')
        bucket = self.get_bucket(validate, headers)
        return bucket.get_subresource(subresource, self.object_name, headers,
                                      version_id)

    def add_group_email_grant(self, permission, email_address, recursive=False,
                              validate=False, headers=None):
        self._check_bucket_uri('add_group_email_grant')
        if self.scheme != 'gs':
            raise ValueError('add_group_email_grant() not supported for %s '
                             'URIs.' % self.scheme)
        if self.object_name:
            if recursive:
                raise ValueError('add_group_email_grant() on key-ful URI cannot '
                                 'specify recursive=True')
            key = self.get_key(validate, headers)
            self.check_response(key, 'key', self.uri)
            key.add_group_email_grant(permission, email_address, headers)
        elif self.bucket_name:
            bucket = self.get_bucket(validate, headers)
            bucket.add_group_email_grant(permission, email_address, recursive,
                                         headers)
        else:
            raise InvalidUriError('add_group_email_grant() on bucket-less URI '
                                  '%s' % self.uri)

    def add_email_grant(self, permission, email_address, recursive=False,
                        validate=False, headers=None):
        self._check_bucket_uri('add_email_grant')
        if not self.object_name:
            bucket = self.get_bucket(validate, headers)
            bucket.add_email_grant(permission, email_address, recursive,
                                   headers)
        else:
            key = self.get_key(validate, headers)
            self.check_response(key, 'key', self.uri)
            key.add_email_grant(permission, email_address)

    def add_user_grant(self, permission, user_id, recursive=False,
                       validate=False, headers=None):
        self._check_bucket_uri('add_user_grant')
        if not self.object_name:
            bucket = self.get_bucket(validate, headers)
            bucket.add_user_grant(permission, user_id, recursive, headers)
        else:
            key = self.get_key(validate, headers)
            self.check_response(key, 'key', self.uri)
            key.add_user_grant(permission, user_id)

    def list_grants(self, headers=None):
        self._check_bucket_uri('list_grants ')
        bucket = self.get_bucket(headers)
        return bucket.list_grants(headers)

    def is_file_uri(self):
        """Returns True if this URI names a file or directory."""
        return False

    def is_cloud_uri(self):
        """Returns True if this URI names a bucket or object."""
        return True

    def names_container(self):
        """
        Returns True if this URI names a directory or bucket. Will return
        False for bucket subdirs; providing bucket subdir semantics needs to
        be done by the caller (like gsutil does).
        """
        return bool(not self.object_name)

    def names_singleton(self):
        """Returns True if this URI names a file or object."""
        return bool(self.object_name)

    def names_directory(self):
        """Returns True if this URI names a directory."""
        return False

    def names_provider(self):
        """Returns True if this URI names a provider."""
        return bool(not self.bucket_name)

    def names_bucket(self):
        """Returns True if this URI names a bucket."""
        return bool(self.bucket_name) and bool(not self.object_name)

    def names_file(self):
        """Returns True if this URI names a file."""
        return False

    def names_object(self):
        """Returns True if this URI names an object."""
        return self.names_singleton()

    def is_stream(self):
        """Returns True if this URI represents input/output stream."""
        return False

    def create_bucket(self, headers=None, location='', policy=None,
                      storage_class=None):
        self._check_bucket_uri('create_bucket ')
        conn = self.connect()
        # Pass storage_class param only if this is a GCS bucket. (In S3 the
        # storage class is specified on the key object.)
        if self.scheme == 'gs':
            return conn.create_bucket(self.bucket_name, headers, location, policy,
                                      storage_class)
        else:
            return conn.create_bucket(self.bucket_name, headers, location, policy)

    def delete_bucket(self, headers=None):
        self._check_bucket_uri('delete_bucket')
        conn = self.connect()
        return conn.delete_bucket(self.bucket_name, headers)

    def get_all_buckets(self, headers=None):
        conn = self.connect()
        return conn.get_all_buckets(headers)

    def get_provider(self):
        conn = self.connect()
        provider = conn.provider
        self.check_response(provider, 'provider', self.uri)
        return provider

    def set_acl(self, acl_or_str, key_name='', validate=False, headers=None,
                version_id=None, if_generation=None, if_metageneration=None):
        """Sets or updates a bucket's ACL."""
        self._check_bucket_uri('set_acl')
        key_name = key_name or self.object_name or ''
        bucket = self.get_bucket(validate, headers)
        if self.generation:
            bucket.set_acl(
                acl_or_str, key_name, headers, generation=self.generation,
                if_generation=if_generation, if_metageneration=if_metageneration)
        else:
            version_id = version_id or self.version_id
            bucket.set_acl(acl_or_str, key_name, headers, version_id)

    def set_xml_acl(self, xmlstring, key_name='', validate=False, headers=None,
                    version_id=None, if_generation=None, if_metageneration=None):
        """Sets or updates a bucket's ACL with an XML string."""
        self._check_bucket_uri('set_xml_acl')
        key_name = key_name or self.object_name or ''
        bucket = self.get_bucket(validate, headers)
        if self.generation:
            bucket.set_xml_acl(
                xmlstring, key_name, headers, generation=self.generation,
                if_generation=if_generation, if_metageneration=if_metageneration)
        else:
            version_id = version_id or self.version_id
            bucket.set_xml_acl(xmlstring, key_name, headers,
                               version_id=version_id)

    def set_def_xml_acl(self, xmlstring, validate=False, headers=None):
        """Sets or updates a bucket's default object ACL with an XML string."""
        self._check_bucket_uri('set_def_xml_acl')
        self.get_bucket(validate, headers).set_def_xml_acl(xmlstring, headers)

    def set_def_acl(self, acl_or_str, validate=False, headers=None,
                    version_id=None):
        """Sets or updates a bucket's default object ACL."""
        self._check_bucket_uri('set_def_acl')
        self.get_bucket(validate, headers).set_def_acl(acl_or_str, headers)

    def set_canned_acl(self, acl_str, validate=False, headers=None,
                       version_id=None):
        """Sets or updates a bucket's acl to a predefined (canned) value."""
        self._check_object_uri('set_canned_acl')
        self._warn_about_args('set_canned_acl', version_id=version_id)
        key = self.get_key(validate, headers)
        self.check_response(key, 'key', self.uri)
        key.set_canned_acl(acl_str, headers)

    def set_def_canned_acl(self, acl_str, validate=False, headers=None,
                           version_id=None):
        """Sets or updates a bucket's default object acl to a predefined
           (canned) value."""
        self._check_bucket_uri('set_def_canned_acl ')
        key = self.get_key(validate, headers)
        self.check_response(key, 'key', self.uri)
        key.set_def_canned_acl(acl_str, headers, version_id)

    def set_subresource(self, subresource, value, validate=False, headers=None,
                        version_id=None):
        self._check_bucket_uri('set_subresource')
        bucket = self.get_bucket(validate, headers)
        bucket.set_subresource(subresource, value, self.object_name, headers,
                               version_id)

    def set_contents_from_string(self, s, headers=None, replace=True,
                                 cb=None, num_cb=10, policy=None, md5=None,
                                 reduced_redundancy=False):
        self._check_object_uri('set_contents_from_string')
        key = self.new_key(headers=headers)
        if self.scheme == 'gs':
            if reduced_redundancy:
                sys.stderr.write('Warning: GCS does not support '
                                 'reduced_redundancy; argument ignored by '
                                 'set_contents_from_string')
            result = key.set_contents_from_string(
                s, headers, replace, cb, num_cb, policy, md5)
        else:
            result = key.set_contents_from_string(
                s, headers, replace, cb, num_cb, policy, md5,
                reduced_redundancy)
        self._update_from_key(key)
        return result

    def set_contents_from_file(self, fp, headers=None, replace=True, cb=None,
                               num_cb=10, policy=None, md5=None, size=None,
                               rewind=False, res_upload_handler=None):
        self._check_object_uri('set_contents_from_file')
        key = self.new_key(headers=headers)
        if self.scheme == 'gs':
            result = key.set_contents_from_file(
                fp, headers, replace, cb, num_cb, policy, md5, size=size,
                rewind=rewind, res_upload_handler=res_upload_handler)
            if res_upload_handler:
                self._update_from_values(None, res_upload_handler.generation,
                                         None, md5)
        else:
            self._warn_about_args('set_contents_from_file',
                                  res_upload_handler=res_upload_handler)
            result = key.set_contents_from_file(
                fp, headers, replace, cb, num_cb, policy, md5, size=size,
                rewind=rewind)
        self._update_from_key(key)
        return result

    def set_contents_from_stream(self, fp, headers=None, replace=True, cb=None,
                                 policy=None, reduced_redundancy=False):
        self._check_object_uri('set_contents_from_stream')
        dst_key = self.new_key(False, headers)
        result = dst_key.set_contents_from_stream(
            fp, headers, replace, cb, policy=policy,
            reduced_redundancy=reduced_redundancy)
        self._update_from_key(dst_key)
        return result

    def copy_key(self, src_bucket_name, src_key_name, metadata=None,
                 src_version_id=None, storage_class='STANDARD',
                 preserve_acl=False, encrypt_key=False, headers=None,
                 query_args=None, src_generation=None):
        """Returns newly created key."""
        self._check_object_uri('copy_key')
        dst_bucket = self.get_bucket(validate=False, headers=headers)
        if src_generation:
            return dst_bucket.copy_key(
                new_key_name=self.object_name,
                src_bucket_name=src_bucket_name,
                src_key_name=src_key_name, metadata=metadata,
                storage_class=storage_class, preserve_acl=preserve_acl,
                encrypt_key=encrypt_key, headers=headers, query_args=query_args,
                src_generation=src_generation)
        else:
            return dst_bucket.copy_key(
                new_key_name=self.object_name,
                src_bucket_name=src_bucket_name, src_key_name=src_key_name,
                metadata=metadata, src_version_id=src_version_id,
                storage_class=storage_class, preserve_acl=preserve_acl,
                encrypt_key=encrypt_key, headers=headers, query_args=query_args)

    def enable_logging(self, target_bucket, target_prefix=None, validate=False,
                       headers=None, version_id=None):
        self._check_bucket_uri('enable_logging')
        bucket = self.get_bucket(validate, headers)
        bucket.enable_logging(target_bucket, target_prefix, headers=headers)

    def disable_logging(self, validate=False, headers=None, version_id=None):
        self._check_bucket_uri('disable_logging')
        bucket = self.get_bucket(validate, headers)
        bucket.disable_logging(headers=headers)

    def get_logging_config(self, validate=False, headers=None, version_id=None):
        self._check_bucket_uri('get_logging_config')
        bucket = self.get_bucket(validate, headers)
        return bucket.get_logging_config(headers=headers)

    def set_website_config(self, main_page_suffix=None, error_key=None,
                           validate=False, headers=None):
        self._check_bucket_uri('set_website_config')
        bucket = self.get_bucket(validate, headers)
        if not (main_page_suffix or error_key):
            bucket.delete_website_configuration(headers)
        else:
            bucket.configure_website(main_page_suffix, error_key, headers)

    def get_website_config(self, validate=False, headers=None):
        self._check_bucket_uri('get_website_config')
        bucket = self.get_bucket(validate, headers)
        return bucket.get_website_configuration(headers)

    def get_versioning_config(self, headers=None):
        self._check_bucket_uri('get_versioning_config')
        bucket = self.get_bucket(False, headers)
        return bucket.get_versioning_status(headers)

    def configure_versioning(self, enabled, headers=None):
        self._check_bucket_uri('configure_versioning')
        bucket = self.get_bucket(False, headers)
        return bucket.configure_versioning(enabled, headers)

    def set_metadata(self, metadata_plus, metadata_minus, preserve_acl,
                     headers=None):
        return self.get_key(False).set_remote_metadata(metadata_plus,
                                                       metadata_minus,
                                                       preserve_acl,
                                                       headers=headers)

    def compose(self, components, content_type=None, headers=None):
        self._check_object_uri('compose')
        component_keys = []
        for suri in components:
            component_keys.append(suri.new_key())
            component_keys[-1].generation = suri.generation
        self.generation = self.new_key().compose(
            component_keys, content_type=content_type, headers=headers)
        self._build_uri_strings()
        return self

    def get_lifecycle_config(self, validate=False, headers=None):
        """Returns a bucket's lifecycle configuration."""
        self._check_bucket_uri('get_lifecycle_config')
        bucket = self.get_bucket(validate, headers)
        lifecycle_config = bucket.get_lifecycle_config(headers)
        self.check_response(lifecycle_config, 'lifecycle', self.uri)
        return lifecycle_config

    def configure_lifecycle(self, lifecycle_config, validate=False,
                            headers=None):
        """Sets or updates a bucket's lifecycle configuration."""
        self._check_bucket_uri('configure_lifecycle')
        bucket = self.get_bucket(validate, headers)
        bucket.configure_lifecycle(lifecycle_config, headers)

    def get_billing_config(self, headers=None):
        self._check_bucket_uri('get_billing_config')
        # billing is defined as a bucket param for GCS, but not for S3.
        if self.scheme != 'gs':
            raise ValueError('get_billing_config() not supported for %s '
                             'URIs.' % self.scheme)
        bucket = self.get_bucket(False, headers)
        return bucket.get_billing_config(headers)

    def configure_billing(self, requester_pays=False, validate=False,
                          headers=None):
        """Sets or updates a bucket's billing configuration."""
        self._check_bucket_uri('configure_billing')
        # billing is defined as a bucket param for GCS, but not for S3.
        if self.scheme != 'gs':
            raise ValueError('configure_billing() not supported for %s '
                             'URIs.' % self.scheme)
        bucket = self.get_bucket(validate, headers)
        bucket.configure_billing(requester_pays=requester_pays, headers=headers)

    def get_encryption_config(self, validate=False, headers=None):
        """Returns a GCS bucket's encryption configuration."""
        self._check_bucket_uri('get_encryption_config')
        # EncryptionConfiguration is defined as a bucket param for GCS, but not
        # for S3.
        if self.scheme != 'gs':
            raise ValueError('get_encryption_config() not supported for %s '
                             'URIs.' % self.scheme)
        bucket = self.get_bucket(validate, headers)
        return bucket.get_encryption_config(headers=headers)

    def set_encryption_config(self, default_kms_key_name=None, validate=False,
                              headers=None):
        """Sets a GCS bucket's encryption configuration."""
        self._check_bucket_uri('set_encryption_config')
        bucket = self.get_bucket(validate, headers)
        bucket.set_encryption_config(default_kms_key_name=default_kms_key_name,
                                     headers=headers)

    def exists(self, headers=None):
        """Returns True if the object exists or False if it doesn't"""
        if not self.object_name:
            raise InvalidUriError('exists on object-less URI (%s)' % self.uri)
        bucket = self.get_bucket(headers)
        key = bucket.get_key(self.object_name, headers=headers)
        return bool(key)


class FileStorageUri(StorageUri):
    """
    StorageUri subclass that handles files in the local file system.
    Callers should instantiate this class by calling boto.storage_uri().

    See file/README about how we map StorageUri operations onto a file system.
    """

    delim = os.sep

    def __init__(self, object_name, debug, is_stream=False):
        """Instantiate a FileStorageUri from a path name.

        @type object_name: string
        @param object_name: object name
        @type debug: boolean
        @param debug: whether to enable debugging on this StorageUri

        After instantiation the components are available in the following
        fields: uri, scheme, bucket_name (always blank for this "anonymous"
        bucket), object_name.
        """

        self.scheme = 'file'
        self.bucket_name = ''
        self.object_name = object_name
        self.uri = 'file://' + object_name
        self.debug = debug
        self.stream = is_stream

    def clone_replace_name(self, new_name):
        """Instantiate a FileStorageUri from the current FileStorageUri,
        but replacing the object_name.

        @type new_name: string
        @param new_name: new object name
        """
        return FileStorageUri(new_name, self.debug, self.stream)

    def is_file_uri(self):
        """Returns True if this URI names a file or directory."""
        return True

    def is_cloud_uri(self):
        """Returns True if this URI names a bucket or object."""
        return False

    def names_container(self):
        """Returns True if this URI names a directory or bucket."""
        return self.names_directory()

    def names_singleton(self):
        """Returns True if this URI names a file (or stream) or object."""
        return not self.names_container()

    def names_directory(self):
        """Returns True if this URI names a directory."""
        if self.stream:
            return False
        return os.path.isdir(self.object_name)

    def names_provider(self):
        """Returns True if this URI names a provider."""
        return False

    def names_bucket(self):
        """Returns True if this URI names a bucket."""
        return False

    def names_file(self):
        """Returns True if this URI names a file."""
        return self.names_singleton()

    def names_object(self):
        """Returns True if this URI names an object."""
        return False

    def is_stream(self):
        """Returns True if this URI represents input/output stream.
        """
        return bool(self.stream)

    def close(self):
        """Closes the underlying file.
        """
        self.get_key().close()

    def exists(self, _headers_not_used=None):
        """Returns True if the file exists or False if it doesn't"""
        # The _headers_not_used parameter is ignored. It is only there to ensure
        # that this method's signature is identical to the exists method on the
        # BucketStorageUri class.
        return os.path.exists(self.object_name)
