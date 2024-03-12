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
"""Unit tests for hashing helper functions and classes."""

from gslib.utils import system_util
from gslib.utils.user_agent_helper import GetUserAgent
import gslib.tests.testcase as testcase

import six
from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


class TestUserAgentHelper(testcase.GsUtilUnitTestCase):
  """Unit tests for the GetUserAgent helper function."""

  @mock.patch('gslib.VERSION', '4_test')
  def testNoArgs(self):
    self.assertRegex(GetUserAgent([]), r"^ gsutil/4_test \([^\)]+\)")

  def testAnalyticsFlag(self):
    self.assertRegex(GetUserAgent([], False), r"analytics/enabled")
    self.assertRegex(GetUserAgent([], True), r"analytics/disabled")

  @mock.patch.object(system_util, 'IsRunningInteractively')
  def testInteractiveFlag(self, mock_interactive):
    mock_interactive.return_value = True
    self.assertRegex(GetUserAgent([]), r"interactive/True")
    mock_interactive.return_value = False
    self.assertRegex(GetUserAgent([]), r"interactive/False")

  def testHelp(self):
    self.assertRegex(GetUserAgent(['help']), r"command/help")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testCp(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(
        GetUserAgent(['cp', '-r', '-Z', '1.txt', 'gs://dst']), r"command/cp$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testCpNotEnoughArgs(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['cp']), r"command/cp$")
    self.assertRegex(GetUserAgent(['cp', '1.txt']), r"command/cp$")
    self.assertRegex(GetUserAgent(['cp', '-r', '1.ts']), r"command/cp$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testCpEncoding(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['cp', 'öne', 'twö']), r"command/cp$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testRsync(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['rsync', '1.txt', 'gs://dst']),
                             r"command/rsync$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testMv(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(
        GetUserAgent(['mv', 'gs://src/1.txt', 'gs://dst/1.txt']),
        r"command/mv$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testCpCloudToCloud(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['cp', '-r', 'gs://src', 'gs://dst']),
                             r"command/cp$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testCpForcedDaisyChain(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['cp', '-D', 'gs://src', 'gs://dst']),
                             r"command/cp$")

  def testCpDaisyChain(self):
    self.assertRegex(
        GetUserAgent(['cp', '-r', '-Z', 'gs://src', 's3://dst']),
        r"command/cp-DaisyChain")
    self.assertRegex(
        GetUserAgent(['mv', 'gs://src/1.txt', 's3://dst/1.txt']),
        r"command/mv-DaisyChain")
    self.assertRegex(
        GetUserAgent(['rsync', '-r', 'gs://src', 's3://dst']),
        r"command/rsync-DaisyChain")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testPassOnInvalidUrlError(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(
        GetUserAgent(['cp', '-r', '-Z', 'bad://src', 's3://dst']),
        r"command/cp$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testRewriteEncryptionKey(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['rewrite', '-k', 'gs://dst']),
                             r"command/rewrite-k$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testRewriteStorageClass(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['rewrite', '-s', 'gs://dst']),
                             r"command/rewrite-s$")

  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testRewriteEncryptionKeyAndStorageClass(self, mock_invoked):
    mock_invoked.return_value = False
    self.assertRegex(GetUserAgent(['rewrite', '-k', '-s', 'gs://dst']),
                             r"command/rewrite-k-s$")

  @mock.patch.object(system_util, 'CloudSdkVersion')
  @mock.patch.object(system_util, 'InvokedViaCloudSdk')
  def testCloudSdk(self, mock_invoked, mock_version):
    mock_invoked.return_value = True
    mock_version.return_value = '500.1'
    self.assertRegex(GetUserAgent(['help']), r"google-cloud-sdk/500.1$")
    mock_invoked.return_value = False
    mock_version.return_value = '500.1'
    self.assertRegex(GetUserAgent(['help']), r"command/help$")
