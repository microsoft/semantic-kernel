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
"""Integration tests for top-level gsutil command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import importlib
import unittest
from unittest import mock
from google.auth import exceptions as google_auth_exceptions
from gslib.command_runner import CommandRunner
from gslib.utils import system_util

import gslib
import gslib.tests.testcase as testcase

try:
  from gsutil import _fix_google_module  # pylint: disable=g-import-not-at-top
  FIX_GOOGLE_MODULE_FUNCTION_AVAILABLE = True
except ImportError:
  FIX_GOOGLE_MODULE_FUNCTION_AVAILABLE = False


class TestGsUtil(testcase.GsUtilIntegrationTestCase):
  """Integration tests for top-level gsutil command."""

  def test_long_version_arg(self):
    stdout = self.RunGsUtil(['--version'], return_stdout=True)
    self.assertEqual('gsutil version: %s\n' % gslib.VERSION, stdout)

  def test_version_command(self):
    stdout = self.RunGsUtil(['version'], return_stdout=True)
    self.assertEqual('gsutil version: %s\n' % gslib.VERSION, stdout)

  def test_version_long(self):
    stdout = self.RunGsUtil(['version', '-l'], return_stdout=True)
    self.assertIn('gsutil version: %s\n' % gslib.VERSION, stdout)
    self.assertIn('boto version', stdout)
    self.assertIn('checksum', stdout)
    self.assertIn('config path', stdout)
    self.assertIn('gsutil path', stdout)


class TestGsUtilUnit(testcase.GsUtilUnitTestCase):
  """Unit tests for top-level gsutil command."""

  @unittest.skipUnless(
      FIX_GOOGLE_MODULE_FUNCTION_AVAILABLE,
      'The gsutil.py file is not available for certain installations like pip.')
  @mock.patch.object(importlib, 'reload', autospec=True)
  def test_fix_google_module(self, mock_reload):
    with mock.patch.dict('sys.modules', {'google': 'google'}):
      _fix_google_module()
      mock_reload.assert_called_once_with('google')

  @unittest.skipUnless(
      FIX_GOOGLE_MODULE_FUNCTION_AVAILABLE,
      'The gsutil.py file is not available for certain installations like pip.')
  @mock.patch.object(importlib, 'reload', autospec=True)
  def test_fix_google_module_does_not_reload_if_module_missing(
      self, mock_reload):
    with mock.patch.dict('sys.modules', {}, clear=True):
      _fix_google_module()
      self.assertFalse(mock_reload.called)

  @mock.patch.object(system_util, 'InvokedViaCloudSdk', autospec=True)
  @mock.patch.object(gslib.__main__, '_OutputAndExit', autospec=True)
  def test_translates_oauth_error_cloudsdk(self, mock_output_and_exit,
                                           mock_invoke_via_cloud_sdk):
    mock_invoke_via_cloud_sdk.return_value = True
    command_runner = CommandRunner()
    with mock.patch.object(command_runner, 'RunNamedCommand') as mock_run:
      fake_error = google_auth_exceptions.OAuthError('fake error message')
      mock_run.side_effect = fake_error
      gslib.__main__._RunNamedCommandAndHandleExceptions(command_runner,
                                                         command_name='fake')
      mock_output_and_exit.assert_called_once_with(
          'Your credentials are invalid. Please run\n$ gcloud auth login',
          fake_error)

  @mock.patch.object(system_util, 'InvokedViaCloudSdk', autospec=True)
  @mock.patch.object(gslib.__main__, '_OutputAndExit', autospec=True)
  def test_translates_oauth_error_standalone(self, mock_output_and_exit,
                                             mock_invoke_via_cloud_sdk):
    mock_invoke_via_cloud_sdk.return_value = False
    command_runner = CommandRunner()
    with mock.patch.object(command_runner, 'RunNamedCommand') as mock_run:
      fake_error = google_auth_exceptions.OAuthError('fake error message')
      mock_run.side_effect = fake_error
      gslib.__main__._RunNamedCommandAndHandleExceptions(command_runner,
                                                         command_name='fake')
      mock_output_and_exit.assert_called_once_with(
          'Your credentials are invalid. For more help, see '
          '"gsutil help creds", or re-run the gsutil config command (see '
          '"gsutil help config").', fake_error)
