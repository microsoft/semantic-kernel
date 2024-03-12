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
"""Integration tests for the defacl command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re

import six
from gslib.commands import defacl
from gslib.cs_api_map import ApiSelector
import gslib.tests.testcase as case
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import unittest
from gslib.utils.constants import UTF8
from gslib.utils import shim_util

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock

PUBLIC_READ_JSON_ACL_TEXT = '"entity":"allUsers","role":"READER"'


@SkipForS3('S3 does not support default object ACLs.')
class TestDefacl(case.GsUtilIntegrationTestCase):
  """Integration tests for the defacl command."""

  _defacl_ch_prefix = ['defacl', 'ch']
  _defacl_get_prefix = ['defacl', 'get']
  _defacl_set_prefix = ['defacl', 'set']

  def _MakeScopeRegex(self, role, entity_type, email_address):
    template_regex = (r'\{.*"entity":\s*"%s-%s".*"role":\s*"%s".*\}' %
                      (entity_type, email_address, role))
    return re.compile(template_regex, flags=re.DOTALL)

  def testChangeDefaultAcl(self):
    """Tests defacl ch."""
    bucket = self.CreateBucket()

    test_regex = self._MakeScopeRegex('OWNER', 'group', self.GROUP_TEST_ADDRESS)
    test_regex2 = self._MakeScopeRegex('READER', 'group',
                                       self.GROUP_TEST_ADDRESS)
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                               return_stdout=True)
    self.assertNotRegex(json_text, test_regex)

    self.RunGsUtil(self._defacl_ch_prefix +
                   ['-g', self.GROUP_TEST_ADDRESS +
                    ':FC', suri(bucket)])
    json_text2 = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                                return_stdout=True)
    self.assertRegex(json_text2, test_regex)

    self.RunGsUtil(self._defacl_ch_prefix +
                   ['-g', self.GROUP_TEST_ADDRESS + ':READ',
                    suri(bucket)])
    json_text3 = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                                return_stdout=True)
    self.assertRegex(json_text3, test_regex2)

    stderr = self.RunGsUtil(
        self._defacl_ch_prefix +
        ['-g', self.GROUP_TEST_ADDRESS + ':WRITE',
         suri(bucket)],
        return_stderr=True,
        expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn('WRITER is not a valid value', stderr)
    else:
      self.assertIn('WRITER cannot be set as a default object ACL', stderr)

  def testChangeDefaultAclEmpty(self):
    """Tests adding and removing an entry from an empty default object ACL."""

    bucket = self.CreateBucket()

    # First, clear out the default object ACL on the bucket.
    self.RunGsUtil(self._defacl_set_prefix + ['private', suri(bucket)])
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                               return_stdout=True)
    empty_regex = r'\[\]\s*'
    self.assertRegex(json_text, empty_regex)

    group_regex = self._MakeScopeRegex('READER', 'group',
                                       self.GROUP_TEST_ADDRESS)
    self.RunGsUtil(self._defacl_ch_prefix +
                   ['-g', self.GROUP_TEST_ADDRESS + ':READ',
                    suri(bucket)])
    json_text2 = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                                return_stdout=True)
    self.assertRegex(json_text2, group_regex)

    if self.test_api == ApiSelector.JSON:
      # TODO: Enable when JSON service respects creating a private (no entries)
      # default object ACL via PATCH. For now, only supported in XML.
      return

    # After adding and removing a group, the default object ACL should be empty.
    self.RunGsUtil(self._defacl_ch_prefix +
                   ['-d', self.GROUP_TEST_ADDRESS,
                    suri(bucket)])
    json_text3 = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                                return_stdout=True)
    self.assertRegex(json_text3, empty_regex)

  def testChangeMultipleBuckets(self):
    """Tests defacl ch on multiple buckets."""
    bucket1 = self.CreateBucket()
    bucket2 = self.CreateBucket()

    test_regex = self._MakeScopeRegex('READER', 'group',
                                      self.GROUP_TEST_ADDRESS)
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket1)],
                               return_stdout=True)
    self.assertNotRegex(json_text, test_regex)
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket2)],
                               return_stdout=True)
    self.assertNotRegex(json_text, test_regex)

    self.RunGsUtil(
        self._defacl_ch_prefix +
        ['-g', self.GROUP_TEST_ADDRESS + ':READ',
         suri(bucket1),
         suri(bucket2)])
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket1)],
                               return_stdout=True)
    self.assertRegex(json_text, test_regex)
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket2)],
                               return_stdout=True)
    self.assertRegex(json_text, test_regex)

  def testChangeMultipleAcls(self):
    """Tests defacl ch with multiple ACL entries."""
    bucket = self.CreateBucket()

    test_regex_group = self._MakeScopeRegex('READER', 'group',
                                            self.GROUP_TEST_ADDRESS)
    test_regex_user = self._MakeScopeRegex('OWNER', 'user',
                                           self.USER_TEST_ADDRESS)
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                               return_stdout=True)
    self.assertNotRegex(json_text, test_regex_group)
    self.assertNotRegex(json_text, test_regex_user)

    self.RunGsUtil(self._defacl_ch_prefix + [
        '-g', self.GROUP_TEST_ADDRESS + ':READ', '-u', self.USER_TEST_ADDRESS +
        ':fc',
        suri(bucket)
    ])
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                               return_stdout=True)
    self.assertRegex(json_text, test_regex_group)
    self.assertRegex(json_text, test_regex_user)

  def testEmptyDefAcl(self):
    bucket = self.CreateBucket()
    self.RunGsUtil(self._defacl_set_prefix + ['private', suri(bucket)])
    stdout = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                            return_stdout=True)
    self.assertEqual(stdout.rstrip(), '[]')
    self.RunGsUtil(self._defacl_ch_prefix +
                   ['-u', self.USER_TEST_ADDRESS +
                    ':fc', suri(bucket)])

  def testDeletePermissionsWithCh(self):
    """Tests removing permissions with defacl ch."""
    bucket = self.CreateBucket()

    test_regex = self._MakeScopeRegex('OWNER', 'user', self.USER_TEST_ADDRESS)
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                               return_stdout=True)
    self.assertNotRegex(json_text, test_regex)

    self.RunGsUtil(self._defacl_ch_prefix +
                   ['-u', self.USER_TEST_ADDRESS +
                    ':fc', suri(bucket)])
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                               return_stdout=True)
    self.assertRegex(json_text, test_regex)

    self.RunGsUtil(self._defacl_ch_prefix +
                   ['-d', self.USER_TEST_ADDRESS,
                    suri(bucket)])
    json_text = self.RunGsUtil(self._defacl_get_prefix + [suri(bucket)],
                               return_stdout=True)
    self.assertNotRegex(json_text, test_regex)

  def testTooFewArgumentsFails(self):
    """Tests calling defacl with insufficient number of arguments."""
    # No arguments for get, but valid subcommand.
    stderr = self.RunGsUtil(self._defacl_get_prefix,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

    # No arguments for set, but valid subcommand.
    stderr = self.RunGsUtil(self._defacl_set_prefix,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

    # No arguments for ch, but valid subcommand.
    stderr = self.RunGsUtil(self._defacl_ch_prefix,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

    # Neither arguments nor subcommand.
    stderr = self.RunGsUtil(['defacl'], return_stderr=True, expected_status=1)
    self.assertIn('command requires at least', stderr)


class TestDefaclShim(case.GsUtilUnitTestCase):

  @mock.patch.object(defacl.DefAclCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_defacl_get(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('defacl', ['get', 'gs://bucket'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(('Gcloud Storage Command: {} storage buckets describe'
                       ' --format=multi(defaultObjectAcl:format=json)'
                       ' --raw gs://bucket').format(
                           shim_util._get_gcloud_binary_path('fake_dir')),
                      info_lines)

  @mock.patch.object(defacl.DefAclCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_set_defacl_file(self):
    acl_string = 'acl_string'
    inpath = self.CreateTempFile(contents=acl_string.encode(UTF8))
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'defacl', ['set', inpath, 'gs://b1', 'gs://b2'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(('Gcloud Storage Command: {} storage buckets update'
                       ' --default-object-acl-file={} gs://b1 gs://b2').format(
                           shim_util._get_gcloud_binary_path('fake_dir'),
                           inpath), info_lines)

  @mock.patch.object(defacl.DefAclCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_set_predefined_defacl(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'defacl', ['set', 'bucket-owner-read', 'gs://b1', 'gs://b2'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage buckets update'
             ' --predefined-default-object-acl={} gs://b1 gs://b2').format(
                 shim_util._get_gcloud_binary_path('fake_dir'),
                 'bucketOwnerRead'), info_lines)

  @mock.patch.object(defacl.DefAclCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_xml_predefined_defacl_for_set(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'defacl', ['set', 'authenticated-read', 'gs://b1', 'gs://b2'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage buckets update'
             ' --predefined-default-object-acl={} gs://b1 gs://b2').format(
                 shim_util._get_gcloud_binary_path('fake_dir'),
                 'authenticatedRead'), info_lines)

  @mock.patch.object(defacl.DefAclCommand, 'RunCommand', new=mock.Mock())
  def test_shim_changes_defacls_for_user(self):
    # The helper function this behavior relies on is tested more
    # thoroughly in test_acl.py.
    inpath = self.CreateTempFile()
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'defacl', ['ch', '-f', '-u', 'user@example.com:R', 'gs://bucket1'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn((
            'Gcloud Storage Command: {} storage buckets update'
            ' --continue-on-error'
            ' --add-default-object-acl-grant entity=user-user@example.com,role=READER'
            ' gs://bucket1').format(
                shim_util._get_gcloud_binary_path('fake_dir'), inpath),
                      info_lines)


class TestDefaclOldAlias(TestDefacl):
  _defacl_ch_prefix = ['chdefacl']
  _defacl_get_prefix = ['getdefacl']
  _defacl_set_prefix = ['setdefacl']
