# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Unit tests for help command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.command import Command
import gslib.tests.testcase as testcase


class HelpUnitTests(testcase.GsUtilUnitTestCase):
  """Help command unit test suite."""

  def test_help_noargs(self):
    stdout = self.RunCommand('help', return_stdout=True)
    self.assertIn('Available commands', stdout)

  def test_help_subcommand_arg(self):
    stdout = self.RunCommand('help', ['web', 'set'], return_stdout=True)
    self.assertIn('gsutil web set', stdout)
    self.assertNotIn('gsutil web get', stdout)

  def test_help_invalid_subcommand_arg(self):
    stdout = self.RunCommand('help', ['web', 'asdf'], return_stdout=True)
    self.assertIn('help about one of the subcommands', stdout)

  def test_help_with_subcommand_for_command_without_subcommands(self):
    stdout = self.RunCommand('help', ['ls', 'asdf'], return_stdout=True)
    self.assertIn('has no subcommands', stdout)

  def test_help_command_arg(self):
    stdout = self.RunCommand('help', ['ls'], return_stdout=True)
    self.assertIn('ls - List providers, buckets', stdout)

  def test_command_help_arg(self):
    stdout = self.RunCommand('ls', ['--help'], return_stdout=True)
    self.assertIn('ls - List providers, buckets', stdout)

  def test_subcommand_help_arg(self):
    stdout = self.RunCommand('web', ['set', '--help'], return_stdout=True)
    self.assertIn('gsutil web set', stdout)
    self.assertNotIn('gsutil web get', stdout)

  def test_command_args_with_help(self):
    stdout = self.RunCommand('cp', ['foo', 'bar', '--help'], return_stdout=True)
    self.assertIn('cp - Copy files and objects', stdout)


class HelpIntegrationTests(testcase.GsUtilIntegrationTestCase):
  """Help command integration test suite."""

  def test_help_wrong_num_args(self):
    stderr = self.RunGsUtil(['cp'], return_stderr=True, expected_status=1)
    self.assertIn('Usage:', stderr)

  def test_help_runs_for_all_commands(self):
    # This test is particularly helpful because the `help` command can fail
    # under unusual circumstances (e.g. someone adds a new command and they make
    # the "one-line" summary longer than the defined character limit).
    for command in Command.__subclasses__():
      # Raises exception if the exit code is non-zero.
      self.RunGsUtil(['help', command.command_spec.command_name])
