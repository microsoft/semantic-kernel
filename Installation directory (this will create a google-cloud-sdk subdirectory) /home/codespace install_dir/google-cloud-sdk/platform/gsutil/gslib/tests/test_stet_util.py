# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Tests for stet_util.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import shutil

from gslib import storage_url
from gslib.tests import testcase
from gslib.tests import util
from gslib.tests.util import unittest
from gslib.utils import execution_util
from gslib.utils import stet_util

from unittest import mock


class TestStetUtil(testcase.GsUtilUnitTestCase):
  """Test STET utils."""

  @mock.patch.object(execution_util, 'ExecuteExternalCommand')
  def test_stet_upload_uses_binary_and_config_from_boto(
      self, mock_execute_external_command):
    fake_config_path = self.CreateTempFile()
    mock_execute_external_command.return_value = ('stdout', 'stderr')
    mock_logger = mock.Mock()

    source_url = storage_url.StorageUrlFromString('in')
    destination_url = storage_url.StorageUrlFromString('gs://bucket/obj')
    with util.SetBotoConfigForTest([
        ('GSUtil', 'stet_binary_path', 'fake_binary_path'),
        ('GSUtil', 'stet_config_path', fake_config_path),
    ]):
      out_file_url = stet_util.encrypt_upload(source_url, destination_url,
                                              mock_logger)

    self.assertEqual(out_file_url,
                     storage_url.StorageUrlFromString('in_.stet_tmp'))
    mock_execute_external_command.assert_called_once_with([
        'fake_binary_path',
        'encrypt',
        '--config-file={}'.format(fake_config_path),
        '--blob-id=gs://bucket/obj',
        'in',
        'in_.stet_tmp',
    ])
    mock_logger.debug.assert_called_once_with('stderr')

  @mock.patch.object(execution_util, 'ExecuteExternalCommand')
  def test_stet_upload_runs_with_binary_from_path_with_correct_settings(
      self, mock_execute_external_command):
    fake_config_path = self.CreateTempFile()
    temporary_path_directory = self.CreateTempDir()
    fake_stet_binary_path = self.CreateTempFile(tmpdir=temporary_path_directory,
                                                file_name='stet')
    previous_path = os.getenv('PATH')
    os.environ['PATH'] += os.path.pathsep + temporary_path_directory

    mock_execute_external_command.return_value = ('stdout', 'stderr')
    mock_logger = mock.Mock()

    source_url = storage_url.StorageUrlFromString('in')
    destination_url = storage_url.StorageUrlFromString('gs://bucket/obj')
    with util.SetBotoConfigForTest([
        ('GSUtil', 'stet_binary_path', None),
        ('GSUtil', 'stet_config_path', fake_config_path),
    ]):
      out_file_url = stet_util.encrypt_upload(source_url, destination_url,
                                              mock_logger)

    self.assertEqual(out_file_url,
                     storage_url.StorageUrlFromString('in_.stet_tmp'))
    mock_execute_external_command.assert_called_once_with([
        fake_stet_binary_path,
        'encrypt',
        '--config-file={}'.format(fake_config_path),
        '--blob-id=gs://bucket/obj',
        'in',
        'in_.stet_tmp',
    ])
    mock_logger.debug.assert_called_once_with('stderr')

    os.environ['PATH'] = previous_path

  @mock.patch.object(execution_util, 'ExecuteExternalCommand')
  def test_stet_upload_uses_no_config_if_not_provided(
      self, mock_execute_external_command):
    mock_execute_external_command.return_value = ('stdout', 'stderr')
    mock_logger = mock.Mock()

    source_url = storage_url.StorageUrlFromString('in')
    destination_url = storage_url.StorageUrlFromString('gs://bucket/obj')
    with util.SetBotoConfigForTest([
        ('GSUtil', 'stet_binary_path', 'fake_binary_path'),
        ('GSUtil', 'stet_config_path', None),
    ]):
      with mock.patch.object(os.path,
                             'exists',
                             new=mock.Mock(return_value=True)):
        out_file_url = stet_util.encrypt_upload(source_url, destination_url,
                                                mock_logger)

    self.assertEqual(out_file_url,
                     storage_url.StorageUrlFromString('in_.stet_tmp'))
    mock_execute_external_command.assert_called_once_with([
        'fake_binary_path',
        'encrypt',
        '--blob-id=gs://bucket/obj',
        'in',
        'in_.stet_tmp',
    ])
    mock_logger.debug.assert_called_once_with('stderr')

  @mock.patch.object(shutil, 'move')
  @mock.patch.object(execution_util, 'ExecuteExternalCommand')
  def test_stet_download_runs_binary_and_replaces_temp_file(
      self, mock_execute_external_command, mock_move):
    fake_config_path = self.CreateTempFile()
    mock_execute_external_command.return_value = ('stdout', 'stderr')
    mock_logger = mock.Mock()

    source_url = storage_url.StorageUrlFromString('gs://bucket/obj')
    destination_url = storage_url.StorageUrlFromString('out')
    temporary_file_name = 'out_.gstmp'
    with util.SetBotoConfigForTest([
        ('GSUtil', 'stet_binary_path', 'fake_binary_path'),
        ('GSUtil', 'stet_config_path', fake_config_path),
    ]):
      stet_util.decrypt_download(source_url, destination_url,
                                 temporary_file_name, mock_logger)

    mock_execute_external_command.assert_called_once_with([
        'fake_binary_path', 'decrypt',
        '--config-file={}'.format(fake_config_path),
        '--blob-id=gs://bucket/obj', 'out_.gstmp', 'out_.stet_tmp'
    ])
    mock_logger.debug.assert_called_once_with('stderr')
    mock_move.assert_called_once_with('out_.stet_tmp', 'out_.gstmp')

  @mock.patch.object(stet_util,
                     '_get_stet_binary_from_path',
                     new=mock.Mock(return_value=None))
  def test_stet_util_errors_if_no_binary(self):
    fake_config_path = self.CreateTempFile()
    source_url = storage_url.StorageUrlFromString('in')
    destination_url = storage_url.StorageUrlFromString('gs://bucket/obj')
    with util.SetBotoConfigForTest([
        ('GSUtil', 'stet_binary_path', None),
        ('GSUtil', 'stet_config_path', fake_config_path),
    ]):
      with self.assertRaises(KeyError):
        stet_util.encrypt_upload(source_url, destination_url, None)

  @mock.patch.object(os.path, 'expanduser', autospec=True)
  @mock.patch.object(execution_util,
                     'ExecuteExternalCommand',
                     new=mock.Mock(return_value=('stdout', 'stderr')))
  def test_stet_util_expands_home_directory_symbol(self, mock_expanduser):
    fake_config_path = self.CreateTempFile()
    source_url = storage_url.StorageUrlFromString('in')
    destination_url = storage_url.StorageUrlFromString('gs://bucket/obj')
    with util.SetBotoConfigForTest([
        ('GSUtil', 'stet_binary_path', 'fake_binary_path'),
        ('GSUtil', 'stet_config_path', fake_config_path),
    ]):
      stet_util.encrypt_upload(source_url, destination_url, mock.Mock())
    mock_expanduser.assert_has_calls(
        [mock.call('fake_binary_path'),
         mock.call(fake_config_path)])
