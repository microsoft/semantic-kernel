# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""Unit and integration tests for gsutil command_runner module."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import time

import six
from six.moves import input
import boto
import sys

import gslib
from gslib import command_runner
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.command_runner import CommandRunner
from gslib.command_runner import HandleArgCoding
from gslib.command_runner import HandleHeaderCoding
from gslib.exception import CommandException
from gslib.tab_complete import CloudObjectCompleter
from gslib.tab_complete import CloudOrLocalObjectCompleter
from gslib.tab_complete import LocalObjectCompleter
from gslib.tab_complete import LocalObjectOrCannedACLCompleter
from gslib.tab_complete import NoOpCompleter
import gslib.tests.testcase as testcase
import gslib.tests.util as util
from gslib.tests.util import ARGCOMPLETE_AVAILABLE
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import unittest
from gslib.utils import system_util
from gslib.utils.constants import GSUTIL_PUB_TARBALL
from gslib.utils.text_util import InsistAscii
from gslib.utils.unit_util import SECONDS_PER_DAY

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock

SKIP_BECAUSE_RETRIES_ARE_SLOW = (
    'gs_host is set to non-default value; trying to fetch gsutil version '
    'metadata from the wrong host would fail repeatedly, taking a long time '
    'for retry backoffs before finally failing the test.')


class FakeArgparseArgument(object):
  """Fake for argparse parser argument."""
  pass


class FakeArgparseParser(object):
  """Fake for argparse parser."""

  def __init__(self, name='Default'):
    self.arguments = []
    self.subparsers = None
    self.name = name

  def add_argument(self, *unused_args, **unused_kwargs):
    argument = FakeArgparseArgument()
    self.arguments.append(argument)
    return argument

  def add_subparsers(self):
    self.subparsers = FakeArgparseSubparsers()
    return self.subparsers


class FakeArgparseSubparsers(object):
  """Container for nested parsers."""

  def __init__(self):
    self.parsers = []

  def add_parser(self, name='Default', **unused_kwargs):
    parser = FakeArgparseParser(name=name)
    self.parsers.append(parser)
    return parser


class FakeCommandWithInvalidCompleter(Command):
  """Command with an invalid completer on an argument."""

  command_spec = Command.CreateCommandSpec(
      'fake1', argparse_arguments=[CommandArgument('arg', completer='BAD')])

  help_spec = Command.HelpSpec(help_name='fake1',
                               help_name_aliases=[],
                               help_type='command_help',
                               help_one_line_summary='fake command for tests',
                               help_text='fake command for tests',
                               subcommand_help_text={})

  def __init__(self):
    pass


class FakeCommandWithNestedArguments(object):
  subcommand_name = 'event'
  subcommand_subname = 'set'
  # Matches the number of CommandArguments in argparse_arguments below.
  num_args = 2

  command_spec = Command.CreateCommandSpec('FakeCommandWithNestedArguments',
                                           argparse_arguments={
                                               subcommand_name: {
                                                   subcommand_subname: [
                                                       CommandArgument('arg1'),
                                                       CommandArgument('arg2'),
                                                   ]
                                               }
                                           })


class FakeCommandWithCompleters(Command):
  """Command with various completer types."""

  command_spec = Command.CreateCommandSpec(
      'fake2',
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudURLsArgument(),
          CommandArgument.MakeZeroOrMoreFileURLsArgument(),
          CommandArgument.MakeZeroOrMoreCloudOrFileURLsArgument(),
          CommandArgument.MakeFreeTextArgument(),
          CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
          CommandArgument.MakeFileURLOrCannedACLArgument(),
      ])

  help_spec = Command.HelpSpec(help_name='fake2',
                               help_name_aliases=[],
                               help_type='command_help',
                               help_one_line_summary='fake command for tests',
                               help_text='fake command for tests',
                               subcommand_help_text={})

  def __init__(self):
    pass


class TestCommandRunnerUnitTests(testcase.unit_testcase.GsUtilUnitTestCase):
  """Unit tests for gsutil update check in command_runner module."""

  def setUp(self):
    """Sets up the command runner mock objects."""
    super(TestCommandRunnerUnitTests, self).setUp()

    # Mock out the timestamp file so we can manipulate it.
    self.timestamp_file_path = self.CreateTempFile()
    get_timestamp_file_patcher = mock.patch.object(
        command_runner.boto_util,
        'GetLastCheckedForGsutilUpdateTimestampFile',
        return_value=self.timestamp_file_path)
    self.addCleanup(get_timestamp_file_patcher.stop)
    get_timestamp_file_patcher.start()

    # Mock out the gsutil version checker.
    base_version = six.text_type(gslib.VERSION)
    while not base_version.isnumeric():
      if not base_version:
        raise CommandException('Version number (%s) is not numeric.' %
                               gslib.VERSION)
      base_version = base_version[:-1]
    self.old_look_up_gsutil_version = command_runner.LookUpGsutilVersion
    command_runner.LookUpGsutilVersion = lambda u, v: float(base_version) + 1

    # Mock out input to trigger yes prompt.
    command_runner.input = lambda p: 'y'

    # Mock out TTY check to pretend we're on a TTY even if we're not.
    self.running_interactively = True
    command_runner.system_util.IsRunningInteractively = (
        lambda: self.running_interactively)

    # Mock out the modified time of the VERSION file.
    self.version_mod_time = 0
    self.previous_version_mod_time = gslib.GetGsutilVersionModifiedTime
    gslib.GetGsutilVersionModifiedTime = lambda: self.version_mod_time

    # Create a fake pub tarball that will be used to check for gsutil version.
    self.pub_bucket_uri = self.CreateBucket('pub')
    self.gsutil_tarball_uri = self.CreateObject(bucket_uri=self.pub_bucket_uri,
                                                object_name='gsutil.tar.gz',
                                                contents='foo')

  def tearDown(self):
    """Tears down the command runner mock objects."""
    super(TestCommandRunnerUnitTests, self).tearDown()

    command_runner.LookUpGsutilVersion = self.old_look_up_gsutil_version
    command_runner.input = input

    gslib.GetGsutilVersionModifiedTime = self.previous_version_mod_time

    command_runner.IsRunningInteractively = (
        gslib.utils.system_util.IsRunningInteractively)

    self.gsutil_tarball_uri.delete_key()
    self.pub_bucket_uri.delete_bucket()

  def _IsPackageOrCloudSDKInstall(self):
    # Update should not trigger for package installs or Cloud SDK installs.
    return gslib.IS_PACKAGE_INSTALL or system_util.InvokedViaCloudSdk()

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_py3_not_interactive(self):
    """Tests that py3 prompt is not triggered if not running interactively."""
    with mock.patch.object(sys, 'version_info') as version_info:
      version_info.major = 2
      self.running_interactively = False
      self.assertFalse(self.command_runner.MaybePromptForPythonUpdate('ver'))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_py3_skipped_in_boto(self):
    """Tests that py3 prompt is not triggered if skipped in boto config."""
    with SetBotoConfigForTest([('GSUtil', 'skip_python_update_prompt', 'True')
                              ]):
      with mock.patch.object(sys, 'version_info') as version_info:
        version_info.major = 2
        self.assertFalse(self.command_runner.MaybePromptForPythonUpdate('ver'))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_py3_prompt_on_py2(self):
    """Tests that py3 prompt is triggered on Python 2."""
    with mock.patch.object(sys, 'version_info') as version_info:
      version_info.major = 2
      self.assertEqual(True,
                       self.command_runner.MaybePromptForPythonUpdate('ver'))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_py3_prompt_on_py3(self):
    """Tests that py3 prompt is not triggered on Python 3."""
    with mock.patch.object(sys, 'version_info') as version_info:
      version_info.major = 3
      self.assertEqual(False,
                       self.command_runner.MaybePromptForPythonUpdate('ver'))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_not_interactive(self):
    """Tests that update is not triggered if not running interactively."""
    with SetBotoConfigForTest([('GSUtil', 'software_update_check_period', '1')
                              ]):
      with open(self.timestamp_file_path, 'w') as f:
        f.write(str(int(time.time() - 2 * SECONDS_PER_DAY)))
      self.running_interactively = False
      self.assertEqual(
          False,
          self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_no_tracker_file_version_recent(self):
    """Tests when no timestamp file exists and VERSION file is recent."""
    if os.path.exists(self.timestamp_file_path):
      os.remove(self.timestamp_file_path)
    self.assertFalse(os.path.exists(self.timestamp_file_path))
    self.version_mod_time = time.time()
    self.assertEqual(
        False, self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_no_tracker_file_version_old(self):
    """Tests when no timestamp file exists and VERSION file is old."""
    if os.path.exists(self.timestamp_file_path):
      os.remove(self.timestamp_file_path)
    self.assertFalse(os.path.exists(self.timestamp_file_path))
    self.version_mod_time = 0
    expected = not self._IsPackageOrCloudSDKInstall()
    self.assertEqual(
        expected,
        self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_invalid_commands(self):
    """Tests that update is not triggered for certain commands."""
    self.assertEqual(
        False,
        self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('update', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_fails_silently_when_version_check_fails(self):
    """Tests that update is not triggered for certain commands."""

    command_runner.LookUpGsutilVersion = self.old_look_up_gsutil_version
    self.assertEqual(
        False,
        self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('update', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_invalid_file_contents(self):
    """Tests no update if timestamp file has invalid value."""
    with open(self.timestamp_file_path, 'w') as f:
      f.write('NaN')
    self.assertEqual(
        False, self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_update_should_trigger(self):
    """Tests update should be triggered if time is up."""
    with SetBotoConfigForTest([('GSUtil', 'software_update_check_period', '1')
                              ]):
      with open(self.timestamp_file_path, 'w') as f:
        f.write(str(int(time.time() - 2 * SECONDS_PER_DAY)))
      expected = not self._IsPackageOrCloudSDKInstall()
      self.assertEqual(
          expected,
          self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_not_time_for_update_yet(self):
    """Tests update not triggered if not time yet."""
    with SetBotoConfigForTest([('GSUtil', 'software_update_check_period', '3')
                              ]):
      with open(self.timestamp_file_path, 'w') as f:
        f.write(str(int(time.time() - 2 * SECONDS_PER_DAY)))
      self.assertEqual(
          False,
          self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

  def test_user_says_no_to_update(self):
    """Tests no update triggered if user says no at the prompt."""
    with SetBotoConfigForTest([('GSUtil', 'software_update_check_period', '1')
                              ]):
      with open(self.timestamp_file_path, 'w') as f:
        f.write(str(int(time.time() - 2 * SECONDS_PER_DAY)))
      command_runner.input = lambda p: 'n'
      self.assertEqual(
          False,
          self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_update_check_skipped_with_quiet_mode(self):
    """Tests that update isn't triggered when loglevel is in quiet mode."""
    with SetBotoConfigForTest([('GSUtil', 'software_update_check_period', '1')
                              ]):
      with open(self.timestamp_file_path, 'w') as f:
        f.write(str(int(time.time() - 2 * SECONDS_PER_DAY)))

      expected = not self._IsPackageOrCloudSDKInstall()
      self.assertEqual(
          expected,
          self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))

      prev_loglevel = logging.getLogger().getEffectiveLevel()
      try:
        logging.getLogger().setLevel(logging.ERROR)
        # With reduced loglevel, should return False.
        self.assertEqual(
            False,
            self.command_runner.MaybeCheckForAndOfferSoftwareUpdate('ls', 0))
      finally:
        logging.getLogger().setLevel(prev_loglevel)

  def test_command_argument_parser_setup_invalid_completer(self):

    command_map = {
        FakeCommandWithInvalidCompleter.command_spec.command_name:
            FakeCommandWithInvalidCompleter()
    }

    runner = CommandRunner(
        bucket_storage_uri_class=self.mock_bucket_storage_uri,
        gsutil_api_class_map_factory=self.mock_gsutil_api_class_map_factory,
        command_map=command_map)

    parser = FakeArgparseParser()
    try:
      runner.ConfigureCommandArgumentParsers(parser)
    except RuntimeError as e:
      self.assertIn('Unknown completer', str(e))

  @unittest.skipUnless(ARGCOMPLETE_AVAILABLE,
                       'Tab completion requires argcomplete')
  def test_command_argument_parser_setup_nested_argparse_arguments(self):
    command_map = {
        FakeCommandWithNestedArguments.command_spec.command_name:
            FakeCommandWithNestedArguments(),
    }
    runner = CommandRunner(
        bucket_storage_uri_class=self.mock_bucket_storage_uri,
        gsutil_api_class_map_factory=self.mock_gsutil_api_class_map_factory,
        command_map=command_map)
    parser = FakeArgparseParser()
    runner.ConfigureCommandArgumentParsers(parser)

    # Start at first level of subparsers.
    cur_subparser = parser.subparsers.parsers[0]
    self.assertEqual(cur_subparser.name,
                     FakeCommandWithNestedArguments.command_spec.command_name)

    # Go one level further, checking the current subparser's first subparser.
    cur_subparser = cur_subparser.subparsers.parsers[0]
    self.assertEqual(cur_subparser.name,
                     FakeCommandWithNestedArguments.subcommand_name)

    cur_subparser = cur_subparser.subparsers.parsers[0]
    self.assertEqual(cur_subparser.name,
                     FakeCommandWithNestedArguments.subcommand_subname)

    # FakeArgparseParser adds a FakeArgparseArgument in place of any arguments
    # passed in via add_argument(), so we can't check for anything beyond the
    # presence of the correct number of arguments here.
    self.assertEqual(len(cur_subparser.arguments),
                     FakeCommandWithNestedArguments.num_args)

  @unittest.skipUnless(ARGCOMPLETE_AVAILABLE,
                       'Tab completion requires argcomplete')
  def test_command_argument_parser_setup_completers(self):

    command_map = {
        FakeCommandWithCompleters.command_spec.command_name:
            FakeCommandWithCompleters()
    }

    runner = CommandRunner(
        bucket_storage_uri_class=self.mock_bucket_storage_uri,
        gsutil_api_class_map_factory=self.mock_gsutil_api_class_map_factory,
        command_map=command_map)

    main_parser = FakeArgparseParser()

    runner.ConfigureCommandArgumentParsers(main_parser)

    self.assertEqual(1, len(main_parser.subparsers.parsers))
    subparser = main_parser.subparsers.parsers[0]
    self.assertEqual(6, len(subparser.arguments))
    self.assertEqual(CloudObjectCompleter,
                     type(subparser.arguments[0].completer))
    self.assertEqual(LocalObjectCompleter,
                     type(subparser.arguments[1].completer))
    self.assertEqual(CloudOrLocalObjectCompleter,
                     type(subparser.arguments[2].completer))
    self.assertEqual(NoOpCompleter, type(subparser.arguments[3].completer))
    self.assertEqual(CloudObjectCompleter,
                     type(subparser.arguments[4].completer))
    self.assertEqual(LocalObjectOrCannedACLCompleter,
                     type(subparser.arguments[5].completer))

  # pylint: disable=invalid-encoded-data
  def test_valid_arg_coding(self):
    """Tests that gsutil encodes valid args correctly."""
    # Args should be unicode; if they are not unicode, they should be utf-8
    # decoded.
    args = ['ls', '-p', 'abc:def', 'gs://bucket']
    HandleArgCoding(args)
    for a in args:
      self.assertTrue(isinstance(a, six.text_type))

  def test_valid_header_coding(self):
    headers = {
        'content-type': 'text/plain',
        'x-goog-meta-foo': 'bãr',
    }
    HandleHeaderCoding(headers)
    # Custom metadata header values should be decoded to unicode; others should
    # not be decoded, but should contain only ASCII characters.
    self.assertTrue(isinstance(headers['x-goog-meta-foo'], six.text_type))
    InsistAscii(
        headers['content-type'],
        'Value of non-custom-metadata header contained non-ASCII characters')

  def test_invalid_header_coding_fails(self):
    headers = {'content-type': 'bãr'}
    with self.assertRaisesRegex(CommandException, r'Invalid non-ASCII'):
      HandleHeaderCoding(headers)


class TestCommandRunnerIntegrationTests(testcase.GsUtilIntegrationTestCase):
  """Integration tests for gsutil update check in command_runner module."""

  def setUp(self):
    """Sets up the command runner mock objects."""
    super(TestCommandRunnerIntegrationTests, self).setUp()

    # Mock out the timestamp file so we can manipulate it.
    self.timestamp_file_path = self.CreateTempFile(contents='0')
    get_timestamp_file_patcher = mock.patch.object(
        command_runner.boto_util,
        'GetLastCheckedForGsutilUpdateTimestampFile',
        return_value=self.timestamp_file_path)
    self.addCleanup(get_timestamp_file_patcher.stop)
    get_timestamp_file_patcher.start()

    # Mock out input to trigger yes prompt.
    command_runner.input = lambda p: 'y'

  def tearDown(self):
    """Tears down the command runner mock objects."""
    super(TestCommandRunnerIntegrationTests, self).tearDown()
    command_runner.input = input

  @unittest.skipIf(util.HAS_NON_DEFAULT_GS_HOST, SKIP_BECAUSE_RETRIES_ARE_SLOW)
  def test_lookup_version_without_credentials(self):
    """Tests that gsutil tarball version lookup works without credentials."""
    with SetBotoConfigForTest([('GSUtil', 'software_update_check_period', '1')],
                              use_existing_config=False):
      self.command_runner = command_runner.CommandRunner()
      # Looking up software version shouldn't get auth failure exception.
      self.command_runner.RunNamedCommand('ls', [GSUTIL_PUB_TARBALL])
