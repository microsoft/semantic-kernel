# -*- coding: utf-8 -*-
# Copyright 2022 Google LLC All Rights Reserved.
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
"""Tests for posix_util.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os

from gslib.tests import testcase
from gslib.tests.util import unittest
from gslib.utils import posix_util
from gslib.utils.system_util import IS_WINDOWS

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


class TestPosixUtil(testcase.GsUtilUnitTestCase):
  """Unit tests for POSIX utils."""

  @mock.patch.object(posix_util, 'InitializeUserGroups', autospec=True)
  @mock.patch.object(posix_util, 'InitializeDefaultMode', autospec=True)
  def test_initialize_preserve_posix_data_calls_correct_functions(
      self, mock_initialize_default_mode, mock_initialize_user_groups):
    posix_util.InitializePreservePosixData()
    mock_initialize_default_mode.assert_called_once_with()
    mock_initialize_user_groups.assert_called_once_with()

  @unittest.skipIf(IS_WINDOWS, 'os.umask always returns 0 on Windows.')
  @mock.patch.object(os, 'umask', autospec=True)
  def test_initialize_mode_sets_umask_to_correct_temporary_value_not_windows(
      self, mock_umask):
    # Abort before setting SYSTEM_POSIX_MODE to avoid side effects.
    mock_umask.side_effect = ValueError
    with self.assertRaises(ValueError):
      posix_util.InitializeDefaultMode()
    mock_umask.assert_called_once_with(0o177)
