#!/usr/bin/env python
# Copyright (c) 2013 Google, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto
import tempfile

from boto.exception import InvalidUriError
from boto import storage_uri
from boto.compat import urllib
from boto.s3.keyfile import KeyFile
from tests.integration.s3.mock_storage_service import MockBucket
from tests.integration.s3.mock_storage_service import MockBucketStorageUri
from tests.integration.s3.mock_storage_service import MockConnection
from tests.unit import unittest

"""Unit tests for StorageUri interface."""

class UriTest(unittest.TestCase):

    def test_provider_uri(self):
        for prov in ('gs', 's3'):
            uri_str = '%s://' % prov
            uri = boto.storage_uri(uri_str, validate=False,
                suppress_consec_slashes=False)
            self.assertEqual(prov, uri.scheme)
            self.assertEqual(uri_str, uri.uri)
            self.assertFalse(hasattr(uri, 'versionless_uri'))
            self.assertEqual('', uri.bucket_name)
            self.assertEqual('', uri.object_name)
            self.assertEqual(None, uri.version_id)
            self.assertEqual(None, uri.generation)
            self.assertEqual(uri.names_provider(), True)
            self.assertEqual(uri.names_container(), True)
            self.assertEqual(uri.names_bucket(), False)
            self.assertEqual(uri.names_object(), False)
            self.assertEqual(uri.names_directory(), False)
            self.assertEqual(uri.names_file(), False)
            self.assertEqual(uri.is_stream(), False)
            self.assertEqual(uri.is_version_specific, False)

    def test_bucket_uri_no_trailing_slash(self):
        for prov in ('gs', 's3'):
            uri_str = '%s://bucket' % prov
            uri = boto.storage_uri(uri_str, validate=False,
                suppress_consec_slashes=False)
            self.assertEqual(prov, uri.scheme)
            self.assertEqual('%s/' % uri_str, uri.uri)
            self.assertFalse(hasattr(uri, 'versionless_uri'))
            self.assertEqual('bucket', uri.bucket_name)
            self.assertEqual('', uri.object_name)
            self.assertEqual(None, uri.version_id)
            self.assertEqual(None, uri.generation)
            self.assertEqual(uri.names_provider(), False)
            self.assertEqual(uri.names_container(), True)
            self.assertEqual(uri.names_bucket(), True)
            self.assertEqual(uri.names_object(), False)
            self.assertEqual(uri.names_directory(), False)
            self.assertEqual(uri.names_file(), False)
            self.assertEqual(uri.is_stream(), False)
            self.assertEqual(uri.is_version_specific, False)

    def test_bucket_uri_with_trailing_slash(self):
        for prov in ('gs', 's3'):
            uri_str = '%s://bucket/' % prov
            uri = boto.storage_uri(uri_str, validate=False,
                suppress_consec_slashes=False)
            self.assertEqual(prov, uri.scheme)
            self.assertEqual(uri_str, uri.uri)
            self.assertFalse(hasattr(uri, 'versionless_uri'))
            self.assertEqual('bucket', uri.bucket_name)
            self.assertEqual('', uri.object_name)
            self.assertEqual(None, uri.version_id)
            self.assertEqual(None, uri.generation)
            self.assertEqual(uri.names_provider(), False)
            self.assertEqual(uri.names_container(), True)
            self.assertEqual(uri.names_bucket(), True)
            self.assertEqual(uri.names_object(), False)
            self.assertEqual(uri.names_directory(), False)
            self.assertEqual(uri.names_file(), False)
            self.assertEqual(uri.is_stream(), False)
            self.assertEqual(uri.is_version_specific, False)

    def test_non_versioned_object_uri(self):
        for prov in ('gs', 's3'):
            uri_str = '%s://bucket/obj/a/b' % prov
            uri = boto.storage_uri(uri_str, validate=False,
                suppress_consec_slashes=False)
            self.assertEqual(prov, uri.scheme)
            self.assertEqual(uri_str, uri.uri)
            self.assertEqual(uri_str, uri.versionless_uri)
            self.assertEqual('bucket', uri.bucket_name)
            self.assertEqual('obj/a/b', uri.object_name)
            self.assertEqual(None, uri.version_id)
            self.assertEqual(None, uri.generation)
            self.assertEqual(uri.names_provider(), False)
            self.assertEqual(uri.names_container(), False)
            self.assertEqual(uri.names_bucket(), False)
            self.assertEqual(uri.names_object(), True)
            self.assertEqual(uri.names_directory(), False)
            self.assertEqual(uri.names_file(), False)
            self.assertEqual(uri.is_stream(), False)
            self.assertEqual(uri.is_version_specific, False)

    def test_versioned_gs_object_uri(self):
        uri_str = 'gs://bucket/obj/a/b#1359908801674000'
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual('gs', uri.scheme)
        self.assertEqual(uri_str, uri.uri)
        self.assertEqual('gs://bucket/obj/a/b', uri.versionless_uri)
        self.assertEqual('bucket', uri.bucket_name)
        self.assertEqual('obj/a/b', uri.object_name)
        self.assertEqual(None, uri.version_id)
        self.assertEqual(1359908801674000, uri.generation)
        self.assertEqual(uri.names_provider(), False)
        self.assertEqual(uri.names_container(), False)
        self.assertEqual(uri.names_bucket(), False)
        self.assertEqual(uri.names_object(), True)
        self.assertEqual(uri.names_directory(), False)
        self.assertEqual(uri.names_file(), False)
        self.assertEqual(uri.is_stream(), False)
        self.assertEqual(uri.is_version_specific, True)

    def test_versioned_gs_object_uri_with_legacy_generation_value(self):
        uri_str = 'gs://bucket/obj/a/b#1'
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual('gs', uri.scheme)
        self.assertEqual(uri_str, uri.uri)
        self.assertEqual('gs://bucket/obj/a/b', uri.versionless_uri)
        self.assertEqual('bucket', uri.bucket_name)
        self.assertEqual('obj/a/b', uri.object_name)
        self.assertEqual(None, uri.version_id)
        self.assertEqual(1, uri.generation)
        self.assertEqual(uri.names_provider(), False)
        self.assertEqual(uri.names_container(), False)
        self.assertEqual(uri.names_bucket(), False)
        self.assertEqual(uri.names_object(), True)
        self.assertEqual(uri.names_directory(), False)
        self.assertEqual(uri.names_file(), False)
        self.assertEqual(uri.is_stream(), False)
        self.assertEqual(uri.is_version_specific, True)

    def test_roundtrip_versioned_gs_object_uri_parsed(self):
        uri_str = 'gs://bucket/obj#1359908801674000'
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        roundtrip_uri = boto.storage_uri(uri.uri, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual(uri.uri, roundtrip_uri.uri)
        self.assertEqual(uri.is_version_specific, True)

    def test_versioned_s3_object_uri(self):
        uri_str = 's3://bucket/obj/a/b#eMuM0J15HkJ9QHlktfNP5MfA.oYR2q6S'
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual('s3', uri.scheme)
        self.assertEqual(uri_str, uri.uri)
        self.assertEqual('s3://bucket/obj/a/b', uri.versionless_uri)
        self.assertEqual('bucket', uri.bucket_name)
        self.assertEqual('obj/a/b', uri.object_name)
        self.assertEqual('eMuM0J15HkJ9QHlktfNP5MfA.oYR2q6S', uri.version_id)
        self.assertEqual(None, uri.generation)
        self.assertEqual(uri.names_provider(), False)
        self.assertEqual(uri.names_container(), False)
        self.assertEqual(uri.names_bucket(), False)
        self.assertEqual(uri.names_object(), True)
        self.assertEqual(uri.names_directory(), False)
        self.assertEqual(uri.names_file(), False)
        self.assertEqual(uri.is_stream(), False)
        self.assertEqual(uri.is_version_specific, True)

    def test_explicit_file_uri(self):
        tmp_dir = tempfile.tempdir or ''
        uri_str = 'file://%s' % urllib.request.pathname2url(tmp_dir)
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual('file', uri.scheme)
        self.assertEqual(uri_str, uri.uri)
        self.assertFalse(hasattr(uri, 'versionless_uri'))
        self.assertEqual('', uri.bucket_name)
        self.assertEqual(tmp_dir, uri.object_name)
        self.assertFalse(hasattr(uri, 'version_id'))
        self.assertFalse(hasattr(uri, 'generation'))
        self.assertFalse(hasattr(uri, 'is_version_specific'))
        self.assertEqual(uri.names_provider(), False)
        self.assertEqual(uri.names_bucket(), False)
        # Don't check uri.names_container(), uri.names_directory(),
        # uri.names_file(), or uri.names_object(), because for file URIs these
        # functions look at the file system and apparently unit tests run
        # chroot'd.
        self.assertEqual(uri.is_stream(), False)

    def test_implicit_file_uri(self):
        tmp_dir = tempfile.tempdir or ''
        uri_str = '%s' % urllib.request.pathname2url(tmp_dir)
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual('file', uri.scheme)
        self.assertEqual('file://%s' % tmp_dir, uri.uri)
        self.assertFalse(hasattr(uri, 'versionless_uri'))
        self.assertEqual('', uri.bucket_name)
        self.assertEqual(tmp_dir, uri.object_name)
        self.assertFalse(hasattr(uri, 'version_id'))
        self.assertFalse(hasattr(uri, 'generation'))
        self.assertFalse(hasattr(uri, 'is_version_specific'))
        self.assertEqual(uri.names_provider(), False)
        self.assertEqual(uri.names_bucket(), False)
        # Don't check uri.names_container(), uri.names_directory(),
        # uri.names_file(), or uri.names_object(), because for file URIs these
        # functions look at the file system and apparently unit tests run
        # chroot'd.
        self.assertEqual(uri.is_stream(), False)

    def test_gs_object_uri_contains_sharp_not_matching_version_syntax(self):
        uri_str = 'gs://bucket/obj#13a990880167400'
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual('gs', uri.scheme)
        self.assertEqual(uri_str, uri.uri)
        self.assertEqual('gs://bucket/obj#13a990880167400',
                         uri.versionless_uri)
        self.assertEqual('bucket', uri.bucket_name)
        self.assertEqual('obj#13a990880167400', uri.object_name)
        self.assertEqual(None, uri.version_id)
        self.assertEqual(None, uri.generation)
        self.assertEqual(uri.names_provider(), False)
        self.assertEqual(uri.names_container(), False)
        self.assertEqual(uri.names_bucket(), False)
        self.assertEqual(uri.names_object(), True)
        self.assertEqual(uri.names_directory(), False)
        self.assertEqual(uri.names_file(), False)
        self.assertEqual(uri.is_stream(), False)
        self.assertEqual(uri.is_version_specific, False)

    def test_file_containing_colon(self):
        uri_str = 'abc:def'
        uri = boto.storage_uri(uri_str, validate=False,
            suppress_consec_slashes=False)
        self.assertEqual('file', uri.scheme)
        self.assertEqual('file://%s' % uri_str, uri.uri)

    def test_invalid_scheme(self):
        uri_str = 'mars://bucket/object'
        try:
            boto.storage_uri(uri_str, validate=False,
                suppress_consec_slashes=False)
        except InvalidUriError as e:
            self.assertIn('Unrecognized scheme', e.message)


if __name__ == '__main__':
    unittest.main()
