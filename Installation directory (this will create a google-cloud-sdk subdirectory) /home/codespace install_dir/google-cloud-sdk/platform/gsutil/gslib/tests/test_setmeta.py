# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Integration tests for setmeta command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re
from unittest import mock

import six

from gslib.commands import setmeta
from gslib.cs_api_map import ApiSelector
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import unittest
from gslib.utils.retry_util import Retry
from gslib.utils import shim_util

if six.PY3:
  long = int


class TestSetMeta(testcase.GsUtilIntegrationTestCase):
  """Integration tests for setmeta command."""

  def test_initial_metadata(self):
    """Tests copying file to an object with metadata."""
    objuri = suri(self.CreateObject(contents=b'foo'))
    inpath = self.CreateTempFile()
    ct = 'image/gif'
    self.RunGsUtil([
        '-h',
        'x-%s-meta-xyz:abc' % self.provider_custom_meta, '-h',
        'Content-Type:%s' % ct, 'cp', inpath, objuri
    ])
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', objuri], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+%s' % ct)
      self.assertRegex(stdout, r'xyz:\s+abc')

    _Check1()

  def test_overwrite_existing(self):
    """Tests overwriting an object's metadata."""
    objuri = suri(self.CreateObject(contents=b'foo'))
    inpath = self.CreateTempFile()
    self.RunGsUtil([
        '-h',
        'x-%s-meta-xyz:abc' % self.provider_custom_meta, '-h',
        'Content-Type:image/gif', 'cp', inpath, objuri
    ])
    self.RunGsUtil([
        'setmeta', '-h', 'Content-Type:text/html', '-h',
        'x-%s-meta-xyz' % self.provider_custom_meta, objuri
    ])
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', objuri], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+text/html')
      self.assertNotIn('xyz', stdout)

    _Check1()

  @SkipForS3('Preconditions not supported for s3 objects')
  def test_generation_precondition(self):
    """Tests setting metadata with a generation precondition."""
    object_uri = self.CreateObject(contents=b'foo')
    generation = object_uri.generation
    ct = 'image/gif'
    stderr = self.RunGsUtil([
        '-h',
        'x-goog-if-generation-match:%d' %
        (long(generation) + 1), 'setmeta', '-h',
        'x-%s-meta-xyz:abc' % self.provider_custom_meta, '-h',
        'Content-Type:%s' % ct,
        suri(object_uri)
    ],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('pre-condition', stderr)
    else:
      self.assertIn('Precondition', stderr)

    self.RunGsUtil([
        '-h',
        'x-goog-generation-match:%s' % generation, 'setmeta', '-h',
        'x-%s-meta-xyz:abc' % self.provider_custom_meta, '-h',
        'Content-Type:%s' % ct,
        suri(object_uri)
    ])
    stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)], return_stdout=True)
    self.assertRegex(stdout, r'Content-Type:\s+%s' % ct)
    self.assertRegex(stdout, r'xyz:\s+abc')

  @SkipForS3('Preconditions not supported for s3 objects')
  def test_metageneration_precondition(self):
    """Tests setting metadata with a metageneration precondition."""
    object_uri = self.CreateObject(contents=b'foo')
    ct = 'image/gif'
    stderr = self.RunGsUtil([
        '-h', 'x-goog-if-metageneration-match:5', 'setmeta', '-h',
        'x-%s-meta-xyz:abc' % self.provider_custom_meta, '-h',
        'Content-Type:%s' % ct,
        suri(object_uri)
    ],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('pre-condition', stderr)
    else:
      self.assertIn('Precondition', stderr)

    self.RunGsUtil([
        '-h', 'x-goog-metageneration-match:1', 'setmeta', '-h',
        'x-%s-meta-xyz:abc' % self.provider_custom_meta, '-h',
        'Content-Type:%s' % ct,
        suri(object_uri)
    ])
    stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)], return_stdout=True)
    self.assertRegex(stdout, r'Content-Type:\s+%s' % ct)
    self.assertRegex(stdout, r'xyz:\s+abc')

  def test_duplicate_header_removal(self):
    stderr = self.RunGsUtil([
        'setmeta', '-h', 'Content-Type:text/html', '-h', 'Content-Type',
        'gs://foo/bar'
    ],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('Each header must appear at most once', stderr)

  def test_duplicate_header(self):
    stderr = self.RunGsUtil([
        'setmeta', '-h', 'Content-Type:text/html', '-h', 'Content-Type:foobar',
        'gs://foo/bar'
    ],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('Each header must appear at most once', stderr)

  def test_setmeta_seek_ahead(self):
    object_uri = self.CreateObject(contents=b'foo')
    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '1'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(
          ['-m', 'setmeta', '-h', 'content-type:footype',
           suri(object_uri)],
          return_stderr=True)
      self.assertIn('Estimated work for this command: objects: 1\n', stderr)

  def test_recursion_works(self):
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    self.RunGsUtil(
        ['setmeta', '-R', '-h', 'content-type:footype',
         suri(bucket_uri)])

    for obj_uri in [object1_uri, object2_uri]:
      stdout = self.RunGsUtil(['stat', suri(obj_uri)], return_stdout=True)
      self.assertIn('footype', stdout)

  def test_metadata_parallelism(self):
    """Ensure that custom metadata works in the multi-thread/process case."""
    # If this test hangs, it can indicate a pickling error.
    bucket_uri = self.CreateBucket(test_objects=2)
    self.AssertNObjectsInBucket(bucket_uri, 2)
    self.RunGsUtil([
        'setmeta', '-h',
        'x-%s-meta-abc:123' % self.provider_custom_meta,
        suri(bucket_uri, '**')
    ])

  def test_invalid_non_ascii_custom_header(self):
    unicode_header = 'x-%s-meta-soufflé:5' % self.provider_custom_meta
    stderr = self.RunGsUtil([
        'setmeta', '-h', unicode_header,
        '%s://foo/bar' % self.default_provider
    ],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('Invalid non-ASCII header', stderr)

  @SkipForS3('Only ASCII characters are supported for x-amz-meta headers')
  def test_valid_non_ascii_custom_header(self):
    """Tests setting custom metadata with a non-ASCII content."""
    objuri = self.CreateObject(contents=b'foo')
    unicode_header = 'x-%s-meta-dessert:soufflé' % self.provider_custom_meta
    self.RunGsUtil(['setmeta', '-h', unicode_header, suri(objuri)])
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', suri(objuri)], return_stdout=True)
      self.assertTrue(re.search('dessert:\\s+soufflé', stdout))

    _Check1()

  @SkipForS3('XML header keys are case-insensitive')
  def test_uppercase_header(self):
    """Tests setting custom metadata with an uppercase value."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip('XML header keys are case-insensitive.')
    objuri = self.CreateObject(contents=b'foo')
    self.RunGsUtil([
        'setmeta', '-h',
        'x-%s-meta-CaSe:SeNsItIvE' % self.provider_custom_meta,
        suri(objuri)
    ])
    stdout = self.RunGsUtil(['stat', suri(objuri)], return_stdout=True)
    self.assertRegex(stdout, r'CaSe:\s+SeNsItIvE')

  def test_remove_header(self):
    """Tests removing a header"""
    objuri = self.CreateObject(contents=b'foo')

    def _Check1():
      self.RunGsUtil(['setmeta', '-h', 'content-disposition:br', suri(objuri)])
      stdout = self.RunGsUtil(['stat', suri(objuri)], return_stdout=True)
      self.assertRegex(stdout, r'Content-Disposition')

    def _Check2():
      self.RunGsUtil(['setmeta', '-h', 'content-disposition', suri(objuri)])
      stdout = self.RunGsUtil(['stat', suri(objuri)], return_stdout=True)
      self.assertRegex(stdout, r'(?!Content-Disposition)')

    _Check1()
    _Check2()

  def test_disallowed_header(self):
    stderr = self.RunGsUtil(
        ['setmeta', '-h', 'Content-Length:5', 'gs://foo/bar'],
        expected_status=1,
        return_stderr=True)
    self.assertIn('Invalid or disallowed header', stderr)

  def test_setmeta_bucket(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil([
        'setmeta', '-h',
        'x-%s-meta-foo:5' % self.provider_custom_meta,
        suri(bucket_uri)
    ],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('ERROR', stderr)
    else:
      self.assertIn('must name an object', stderr)

  def test_setmeta_valid_with_multiple_colons_in_value(self):
    obj_uri = self.CreateObject(contents=b'foo')
    self.RunGsUtil([
        'setmeta', '-h',
        'x-%s-meta-foo:bar:baz' % self.provider_custom_meta,
        suri(obj_uri)
    ])
    stdout = self.RunGsUtil(['stat', suri(obj_uri)], return_stdout=True)
    self.assertRegex(stdout, r'foo:\s+bar:baz')

  def test_setmeta_with_canned_acl(self):
    stderr = self.RunGsUtil([
        'setmeta', '-h',
        'x-%s-acl:public-read' % self.provider_custom_meta, 'gs://foo/bar'
    ],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('gsutil setmeta no longer allows canned ACLs', stderr)

  def test_invalid_non_ascii_header_value(self):
    unicode_header = 'Content-Type:dessert/soufflé'
    stderr = self.RunGsUtil(['setmeta', '-h', unicode_header, 'gs://foo/bar'],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('Invalid non-ASCII value', stderr)

  def test_setmeta_raises_error_if_not_provided_headers(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(['setmeta', suri(bucket_uri)],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn(
        'gsutil setmeta requires one or more headers to be provided with the'
        ' -h flag. See "gsutil help setmeta" for more information.', stderr)


class TestSetMetaShim(testcase.GsUtilUnitTestCase):

  @mock.patch.object(setmeta.SetMetaCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_setmeta_set_and_clear_flags(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('setmeta', [
            '-r',
            '-h',
            'Cache-Control:',
            '-h',
            'Content-Type:fake-content-type',
            'gs://bucket/object',
        ],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage objects update'
             ' --recursive --clear-cache-control'
             ' --content-type=fake-content-type gs://bucket/object').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)
