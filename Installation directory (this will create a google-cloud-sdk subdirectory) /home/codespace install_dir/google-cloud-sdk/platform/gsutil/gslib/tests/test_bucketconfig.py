# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Integration tests for multiple bucket configuration commands."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import json
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.utils.constants import UTF8


class TestBucketConfig(testcase.GsUtilIntegrationTestCase):
  """Integration tests for multiple bucket configuration commands."""

  _set_cors_command = ['cors', 'set']
  _get_cors_command = ['cors', 'get']

  empty_cors = '[]'

  cors_doc = (
      '[{"origin": ["http://origin1.example.com", '
      '"http://origin2.example.com"], '
      '"responseHeader": ["foo", "bar"], "method": ["GET", "PUT", "POST"], '
      '"maxAgeSeconds": 3600},'
      '{"origin": ["http://origin3.example.com"], '
      '"responseHeader": ["foo2", "bar2"], "method": ["GET", "DELETE"]}]\n')
  cors_json_obj = json.loads(cors_doc)

  _set_lifecycle_command = ['lifecycle', 'set']
  _get_lifecycle_command = ['lifecycle', 'get']

  empty_lifecycle = '{}'

  lifecycle_doc = (
      '{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 365}}]}\n')
  lifecycle_json_obj = json.loads(lifecycle_doc)

  _set_acl_command = ['acl', 'set']
  _get_acl_command = ['acl', 'get']
  _set_defacl_command = ['defacl', 'set']
  _get_defacl_command = ['defacl', 'get']

  @SkipForS3('A number of configs in this test are not supported by S3')
  def test_set_multi_config(self):
    """Tests that bucket config patching affects only the desired config."""
    bucket_uri = self.CreateBucket()
    lifecycle_path = self.CreateTempFile(
        contents=self.lifecycle_doc.encode(UTF8))
    cors_path = self.CreateTempFile(contents=self.cors_doc.encode(UTF8))

    self.RunGsUtil(self._set_cors_command + [cors_path, suri(bucket_uri)])
    cors_out = self.RunGsUtil(self._get_cors_command + [suri(bucket_uri)],
                              return_stdout=True)
    self.assertEqual(json.loads(cors_out), self.cors_json_obj)

    self.RunGsUtil(self._set_lifecycle_command +
                   [lifecycle_path, suri(bucket_uri)])
    cors_out = self.RunGsUtil(self._get_cors_command + [suri(bucket_uri)],
                              return_stdout=True)
    lifecycle_out = self.RunGsUtil(self._get_lifecycle_command +
                                   [suri(bucket_uri)],
                                   return_stdout=True)
    self.assertEqual(json.loads(cors_out), self.cors_json_obj)
    self.assertEqual(json.loads(lifecycle_out), self.lifecycle_json_obj)

    if not self._ServiceAccountCredentialsPresent():
      # See comments in _ServiceAccountCredentialsPresent
      self.RunGsUtil(
          self._set_acl_command +
          ['authenticated-read', suri(bucket_uri)])

    cors_out = self.RunGsUtil(self._get_cors_command + [suri(bucket_uri)],
                              return_stdout=True)
    lifecycle_out = self.RunGsUtil(self._get_lifecycle_command +
                                   [suri(bucket_uri)],
                                   return_stdout=True)
    self.assertEqual(json.loads(cors_out), self.cors_json_obj)
    self.assertEqual(json.loads(lifecycle_out), self.lifecycle_json_obj)

    if not self._ServiceAccountCredentialsPresent():
      acl_out = self.RunGsUtil(self._get_acl_command + [suri(bucket_uri)],
                               return_stdout=True)
      self.assertIn('allAuthenticatedUsers', acl_out)

    self.RunGsUtil(self._set_defacl_command + ['public-read', suri(bucket_uri)])

    cors_out = self.RunGsUtil(self._get_cors_command + [suri(bucket_uri)],
                              return_stdout=True)
    lifecycle_out = self.RunGsUtil(self._get_lifecycle_command +
                                   [suri(bucket_uri)],
                                   return_stdout=True)
    def_acl_out = self.RunGsUtil(self._get_defacl_command + [suri(bucket_uri)],
                                 return_stdout=True)
    self.assertEqual(json.loads(cors_out), self.cors_json_obj)
    self.assertEqual(json.loads(lifecycle_out), self.lifecycle_json_obj)
    self.assertIn('allUsers', def_acl_out)

    if not self._ServiceAccountCredentialsPresent():
      acl_out = self.RunGsUtil(self._get_acl_command + [suri(bucket_uri)],
                               return_stdout=True)
      self.assertIn('allAuthenticatedUsers', acl_out)
