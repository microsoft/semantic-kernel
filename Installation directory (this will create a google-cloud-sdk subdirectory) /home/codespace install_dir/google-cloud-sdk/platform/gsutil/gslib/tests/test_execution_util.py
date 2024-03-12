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
"""Tests for execution_util.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import subprocess
from unittest import mock

from gslib import exception
from gslib.tests import testcase
from gslib.utils import execution_util


class TestExecutionUtil(testcase.GsUtilUnitTestCase):
  """Test execution utils."""

  @mock.patch.object(subprocess, 'Popen')
  def testExternalCommandReturnsNoOutput(self, mock_Popen):
    mock_command_process = mock.Mock()
    mock_command_process.returncode = 0
    mock_command_process.communicate.return_value = (None, None)
    mock_Popen.return_value = mock_command_process

    stdout, stderr = execution_util.ExecuteExternalCommand(['fake-command'])
    self.assertIsNone(stdout)
    self.assertIsNone(stderr)

    mock_Popen.assert_called_once_with(['fake-command'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

  @mock.patch.object(subprocess, 'Popen')
  def testExternalCommandReturnsStringOutput(self, mock_Popen):
    mock_command_process = mock.Mock()
    mock_command_process.returncode = 0
    mock_command_process.communicate.return_value = ('a', 'b')
    mock_Popen.return_value = mock_command_process

    stdout, stderr = execution_util.ExecuteExternalCommand(['fake-command'])
    self.assertEqual(stdout, 'a')
    self.assertEqual(stderr, 'b')

    mock_Popen.assert_called_once_with(['fake-command'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

  @mock.patch.object(subprocess, 'Popen')
  def testExternalCommandReturnsBytesOutput(self, mock_Popen):
    mock_command_process = mock.Mock()
    mock_command_process.returncode = 0
    mock_command_process.communicate.return_value = (b'a', b'b')
    mock_Popen.return_value = mock_command_process

    stdout, stderr = execution_util.ExecuteExternalCommand(['fake-command'])
    self.assertEqual(stdout, 'a')
    self.assertEqual(stderr, 'b')

    mock_Popen.assert_called_once_with(['fake-command'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

  @mock.patch.object(subprocess, 'Popen')
  def testExternalCommandReturnsNoOutput(self, mock_Popen):
    mock_command_process = mock.Mock()
    mock_command_process.returncode = 1
    mock_command_process.communicate.return_value = (None, b'error')
    mock_Popen.return_value = mock_command_process

    with self.assertRaises(exception.ExternalBinaryError):
      execution_util.ExecuteExternalCommand(['fake-command'])

    mock_Popen.assert_called_once_with(['fake-command'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

  @mock.patch.object(subprocess, 'Popen')
  def testExternalCommandRaisesFormattedStderr(self, mock_Popen):
    mock_command_process = mock.Mock()
    mock_command_process.returncode = 1
    mock_command_process.communicate.return_value = (None, b'error.\n')
    mock_Popen.return_value = mock_command_process

    with self.assertRaisesRegex(exception.ExternalBinaryError, 'error'):
      execution_util.ExecuteExternalCommand(['fake-command'])
