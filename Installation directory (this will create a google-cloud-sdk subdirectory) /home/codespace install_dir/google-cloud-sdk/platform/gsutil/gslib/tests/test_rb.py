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
"""Integration tests for rb command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import gslib.tests.testcase as testcase
from gslib.tests.util import ObjectToURI as suri


class TestRb(testcase.GsUtilIntegrationTestCase):
  """Integration tests for rb command."""

  def test_rb_bucket_works(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['rb', suri(bucket_uri)])
    stderr = self.RunGsUtil(
        ['ls', '-Lb', 'gs://%s' % self.nonexistent_bucket_name],
        return_stderr=True,
        expected_status=1)
    self.assertIn('404', stderr)

  def test_rb_bucket_not_empty(self):
    bucket_uri = self.CreateBucket(test_objects=1)
    stderr = self.RunGsUtil(['rb', suri(bucket_uri)],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('Bucket is not empty', stderr)
    else:
      self.assertIn('BucketNotEmpty', stderr)

  def test_rb_versioned_bucket_not_empty(self):
    bucket_uri = self.CreateVersionedBucket(test_objects=1)
    stderr = self.RunGsUtil(['rb', suri(bucket_uri)],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('Bucket is not empty. Note: this is a versioned bucket',
                  stderr)

  def test_rb_nonexistent_bucket(self):
    stderr = self.RunGsUtil(
        ['rb', 'gs://%s' % self.nonexistent_bucket_name],
        return_stderr=True,
        expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn('not found', stderr)
    else:
      self.assertIn('does not exist.', stderr)

  def test_rb_minus_f(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil([
        'rb', '-f',
        'gs://%s' % self.nonexistent_bucket_name,
        suri(bucket_uri)
    ],
                            return_stderr=True,
                            expected_status=1)
    # There should be no error output, and existing bucket named after
    # non-existent bucket should be gone.
    self.assertNotIn('bucket does not exist.', stderr)
    stderr = self.RunGsUtil(['ls', '-Lb', suri(bucket_uri)],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('404', stderr)
