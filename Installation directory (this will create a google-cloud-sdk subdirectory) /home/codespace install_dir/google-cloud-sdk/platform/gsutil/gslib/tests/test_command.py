# -*- coding: utf-8 -*-
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Tests for command.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from unittest import mock

from gslib import command
from gslib.tests import testcase
from gslib.utils import constants


class FakeGsutilCommand(command.Command):
  """Implementation of a fake gsutil command."""
  command_spec = command.Command.CreateCommandSpec('fake_gsutil',
                                                   min_args=1,
                                                   max_args=constants.NO_MAX,
                                                   supported_sub_args='rz:',
                                                   file_url_ok=True)
  help_spec = command.Command.HelpSpec(
      help_name='fake_gsutil',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary='Fake one line summary for the command.',
      help_text='Help text for fake command.',
      subcommand_help_text={},
  )


class TestParseSubOpts(testcase.GsUtilUnitTestCase):
  """Test Command.ParseSubOpts method.
  
  Only testing cases which are not tested indirectly by other tests.
  """

  def setUp(self):
    super().setUp()
    self._fake_command = FakeGsutilCommand(
        command_runner=mock.ANY,
        args=['-z', 'opt1', '-r', 'arg1', 'arg2'],
        headers={},
        debug=mock.ANY,
        trace_token=mock.ANY,
        parallel_operations=mock.ANY,
        bucket_storage_uri_class=mock.ANY,
        gsutil_api_class_map_factory=mock.MagicMock())

  def test_raises_error_with_check_args_set_and_update_sub_opts_and_args_unset(
      self):
    with self.assertRaisesRegex(
        TypeError, 'Requested to check arguments but sub_opts and args have'
        ' not been updated.'):
      self._fake_command.ParseSubOpts(check_args=True,
                                      should_update_sub_opts_and_args=False)

  def test_uses_self_args_if_args_passed_is_None(self):
    args_list = ['fake', 'args']
    self._fake_command.args = args_list
    _, parsed_args = self._fake_command.ParseSubOpts(
        should_update_sub_opts_and_args=False)
    self.assertEqual(parsed_args, args_list)

  @mock.patch.object(command, 'CreateOrGetGsutilLogger', autospec=True)
  def test_quiet_mode_gets_set(self, mock_logger):
    mock_logger.return_value.isEnabledFor.return_value = False
    self._fake_command = FakeGsutilCommand(
        command_runner=mock.ANY,
        args=['-z', 'opt1', '-r', 'arg1', 'arg2'],
        headers={},
        debug=mock.ANY,
        trace_token=mock.ANY,
        parallel_operations=mock.ANY,
        bucket_storage_uri_class=mock.ANY,
        gsutil_api_class_map_factory=mock.MagicMock())
    self.assertTrue(self._fake_command.quiet_mode)
    mock_logger.assert_called_once_with('fake_gsutil')
