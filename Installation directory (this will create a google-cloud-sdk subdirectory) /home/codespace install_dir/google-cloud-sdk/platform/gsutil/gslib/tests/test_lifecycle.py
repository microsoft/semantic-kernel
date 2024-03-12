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
"""Integration tests for lifecycle command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import json
import os
import posixpath
from unittest import mock
from xml.dom.minidom import parseString

from gslib.cs_api_map import ApiSelector
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import unittest
from gslib.utils.retry_util import Retry
from gslib.utils.translation_helper import LifecycleTranslation
from gslib.utils import shim_util


@SkipForS3('Lifecycle command is only supported for gs:// URLs')
class TestSetLifecycle(testcase.GsUtilIntegrationTestCase):
  """Integration tests for lifecycle command."""

  empty_doc1 = '{}'

  xml_doc = parseString(
      '<LifecycleConfiguration><Rule>'
      '<Action><Delete/></Action>'
      '<Condition><Age>365</Age></Condition>'
      '</Rule></LifecycleConfiguration>').toprettyxml(indent='    ')

  bad_doc = (
      '{"rule": [{"action": {"type": "Add"}, "condition": {"age": 365}}]}\n')

  lifecycle_doc = (
      '{"rule": ['
      '{"action": {"type": "Delete"}, "condition": {"age": 365}}, '
      '{"action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},'
      ' "condition": {"matchesStorageClass": ["STANDARD"], "age": 366}}]}\n')
  lifecycle_json_obj = json.loads(lifecycle_doc)

  lifecycle_doc_bucket_style = ('{"lifecycle": ' + lifecycle_doc.rstrip() +
                                '}\n')

  # TODO: Remove once Boto is updated to support new fields.
  lifecycle_doc_without_storage_class_fields = (
      '{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 365}}]}\n')

  lifecycle_created_before_doc = (
      '{"rule": [{"action": {"type": "Delete"}, "condition": '
      '{"createdBefore": "2014-10-01"}}]}\n')
  lifecycle_created_before_json_obj = json.loads(lifecycle_created_before_doc)

  lifecycle_with_falsy_condition_values = (
      '{"rule": [{"action": {"type": "Delete"}, "condition": {'
      '"age": 0, "isLive": false, "numNewerVersions": 0}}]}')

  no_lifecycle_config = 'has no lifecycle configuration.'
  empty_lifecycle_config = '[]'

  def test_lifecycle_translation(self):
    """Tests lifecycle translation for various formats."""
    # TODO: Use lifecycle_doc again once Boto is updated to support new fields.
    # json_text = self.lifecycle_doc
    json_text = self.lifecycle_doc_without_storage_class_fields

    entries_list = LifecycleTranslation.JsonLifecycleToMessage(json_text)
    boto_lifecycle = LifecycleTranslation.BotoLifecycleFromMessage(entries_list)
    converted_entries_list = LifecycleTranslation.BotoLifecycleToMessage(
        boto_lifecycle)
    converted_json_text = LifecycleTranslation.JsonLifecycleFromMessage(
        converted_entries_list)
    self.assertEqual(json.loads(json_text), json.loads(converted_json_text))

  def test_default_lifecycle(self):
    bucket_uri = self.CreateBucket()
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)
    if self._use_gcloud_storage:
      self.assertIn(self.empty_lifecycle_config, stdout)
    else:
      self.assertIn(self.no_lifecycle_config, stdout)

  def test_set_empty_lifecycle1(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.empty_doc1.encode('ascii'))
    self.RunGsUtil(['lifecycle', 'set', fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)
    if self._use_gcloud_storage:
      self.assertIn(self.empty_lifecycle_config, stdout)
    else:
      self.assertIn(self.no_lifecycle_config, stdout)

  def test_valid_lifecycle(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.lifecycle_doc.encode('ascii'))
    self.RunGsUtil(['lifecycle', 'set', fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_json_obj)

  def test_valid_lifecycle_bucket_style(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(
        contents=self.lifecycle_doc_bucket_style.encode('ascii'))
    self.RunGsUtil(['lifecycle', 'set', fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_json_obj)

  def test_created_before_lifecycle(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(
        contents=self.lifecycle_created_before_doc.encode('ascii'))
    self.RunGsUtil(['lifecycle', 'set', fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_created_before_json_obj)

  def test_bad_lifecycle(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.bad_doc.encode('ascii'))
    stderr = self.RunGsUtil(
        ['lifecycle', 'set', fpath, suri(bucket_uri)],
        expected_status=1,
        return_stderr=True)
    self.assertNotIn('XML lifecycle data provided', stderr)

  def test_bad_xml_lifecycle(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.xml_doc.encode('ascii'))
    stderr = self.RunGsUtil(
        ['lifecycle', 'set', fpath, suri(bucket_uri)],
        expected_status=1,
        return_stderr=True)
    self.assertIn('XML lifecycle data provided', stderr)

  def test_translation_for_falsy_values_works_correctly(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(
        contents=self.lifecycle_with_falsy_condition_values.encode('ascii'))

    self.RunGsUtil(['lifecycle', 'set', fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)

    # The lifecycle policy we fetch should include all the False- and 0-valued
    # attributes that we just set.
    self.assertRegex(stdout, r'"age":\s+0')
    self.assertRegex(stdout, r'"isLive":\s+false')
    self.assertRegex(stdout, r'"numNewerVersions":\s+0')

  def test_set_lifecycle_and_reset(self):
    """Tests setting and turning off lifecycle configuration."""
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()
    fpath = self.CreateTempFile(tmpdir=tmpdir,
                                contents=self.lifecycle_doc.encode('ascii'))
    self.RunGsUtil(['lifecycle', 'set', fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_json_obj)

    fpath = self.CreateTempFile(tmpdir=tmpdir,
                                contents=self.empty_doc1.encode('ascii'))
    self.RunGsUtil(['lifecycle', 'set', fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket_uri)], return_stdout=True)
    if self._use_gcloud_storage:
      self.assertIn(self.empty_lifecycle_config, stdout)
    else:
      self.assertIn(self.no_lifecycle_config, stdout)

  def test_set_lifecycle_multi_buckets(self):
    """Tests setting lifecycle configuration on multiple buckets."""
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.lifecycle_doc.encode('ascii'))
    self.RunGsUtil(
        ['lifecycle', 'set', fpath,
         suri(bucket1_uri),
         suri(bucket2_uri)])
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket1_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_json_obj)
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket2_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_json_obj)

  def test_set_lifecycle_wildcard(self):
    """Tests setting lifecycle with a wildcarded bucket URI."""
    if self.test_api == ApiSelector.XML:
      # This test lists buckets with wildcards, but it is possible that another
      # test being run in parallel (in the same project) deletes a bucket after
      # it is listed in this test. This causes the subsequent XML metadata get
      # for the lifecycle configuration to fail on that just-deleted bucket,
      # even though that bucket is not used directly in this test.
      return unittest.skip('XML wildcard behavior can cause test to flake '
                           'if a bucket in the same project is deleted '
                           'during execution.')

    random_prefix = self.MakeRandomTestString()
    bucket1_name = self.MakeTempName('bucket', prefix=random_prefix)
    bucket2_name = self.MakeTempName('bucket', prefix=random_prefix)
    bucket1_uri = self.CreateBucket(bucket_name=bucket1_name)
    bucket2_uri = self.CreateBucket(bucket_name=bucket2_name)
    # This just double checks that the common prefix of the two buckets is what
    # we think it should be (based on implementation detail of CreateBucket).
    # We want to be careful when setting a wildcard on buckets to make sure we
    # don't step outside the test buckets to affect other buckets.
    common_prefix = posixpath.commonprefix(
        [suri(bucket1_uri), suri(bucket2_uri)])
    self.assertTrue(
        common_prefix.startswith(
            'gs://%sgsutil-test-test-set-lifecycle-wildcard-' % random_prefix))
    wildcard = '%s*' % common_prefix

    fpath = self.CreateTempFile(contents=self.lifecycle_doc.encode('ascii'))

    actual_lines = set()
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stderr = self.RunGsUtil(['lifecycle', 'set', fpath, wildcard],
                              return_stderr=True)
      actual_lines.update(stderr.splitlines())
      if self._use_gcloud_storage:
        # Gcloud may have unrelated characters on status line
        # as a result of output logic so can't do direct line string comparison.
        self.assertIn('Updating %s/...' % suri(bucket1_uri), stderr)
        self.assertIn('Updating %s/...' % suri(bucket2_uri), stderr)
        status_message = 'Updating'
      else:
        expected_lines = set([
            'Setting lifecycle configuration on %s/...' % suri(bucket1_uri),
            'Setting lifecycle configuration on %s/...' % suri(bucket2_uri)
        ])
        self.assertEqual(expected_lines, actual_lines)
        status_message = 'Setting lifecycle configuration'
      self.assertEqual(stderr.count(status_message), 2)

    _Check1()

    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket1_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_json_obj)
    stdout = self.RunGsUtil(
        ['lifecycle', 'get', suri(bucket2_uri)], return_stdout=True)
    self.assertEqual(json.loads(stdout), self.lifecycle_json_obj)


class TestLifecycleUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for gsutil lifecycle."""

  def test_shim_translates_lifecycle_get_correctly(self):
    bucket_uri = self.CreateBucket()
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('lifecycle',
                                           args=[
                                               'get',
                                               suri(bucket_uri),
                                           ],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage buckets'
             ' describe --format="gsutiljson[key=lifecycle_config,empty=\' has'
             ' no lifecycle configuration.\',empty_prefix_key=storage_url]"'
             ' --raw {}').format(shim_util._get_gcloud_binary_path('fake_dir'),
                                 suri(bucket_uri)), info_lines)

  @mock.patch('gslib.commands.lifecycle.LifecycleCommand._SetLifecycleConfig',
              new=mock.Mock())
  def test_shim_translates_lifecycle_set_correctly(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('lifecycle',
                                           args=[
                                               'set',
                                               'fake-lifecycle-config.json',
                                               'gs://fake-bucket1',
                                               'gs://fake-bucket2',
                                           ],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(('Gcloud Storage Command: {} storage buckets'
                       ' update --lifecycle-file=fake-lifecycle-config.json'
                       ' gs://fake-bucket1 gs://fake-bucket2').format(
                           shim_util._get_gcloud_binary_path('fake_dir')),
                      info_lines)
