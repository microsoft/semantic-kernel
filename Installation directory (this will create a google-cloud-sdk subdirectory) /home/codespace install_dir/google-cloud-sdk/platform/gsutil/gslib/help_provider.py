# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Module defining help types and providers for gsutil commands."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import collections
from gslib.exception import CommandException

ALL_HELP_TYPES = ['command_help', 'additional_help']

# Constants enforced by SanityCheck
# Mainly here for help output formatting purposes, can be changed if necessary.
MAX_HELP_NAME_LEN = 17
MIN_ONE_LINE_SUMMARY_LEN = 10
MAX_ONE_LINE_SUMMARY_LEN = 80 - MAX_HELP_NAME_LEN

DESCRIPTION_PREFIX = """
<B>DESCRIPTION</B>"""

SYNOPSIS_PREFIX = """
<B>SYNOPSIS</B>"""


class HelpProvider(object):
  """Interface for providing help."""

  # Each subclass of HelpProvider define a property named 'help_spec' that is
  # an instance of the following class.
  HelpSpec = collections.namedtuple(
      'HelpSpec',
      [
          # Name of command or auxiliary help info for which this help applies.
          'help_name',
          # List of help name aliases.
          'help_name_aliases',
          # Type of help.
          'help_type',
          # One line summary of this help.
          'help_one_line_summary',
          # The full help text.
          'help_text',
          # Help text for subcommands of the command's help being specified.
          'subcommand_help_text',
      ])

  # Each subclass must override this with an instance of HelpSpec.
  help_spec = None


# This is a static helper instead of a class method because the help loader
# (gslib.commands.help._LoadHelpMaps()) operates on classes not instances.
def SanityCheck(help_provider, help_name_map):
  """Helper for checking that a HelpProvider has minimally adequate content."""
  # Sanity check the content.
  help_name_len = len(help_provider.help_spec.help_name)
  assert (help_name_len > 1 and help_name_len < MAX_HELP_NAME_LEN
         ), 'The help name "{text}" must be less then {max}'.format(
             text=help_provider.help_spec.help_name, max=MAX_HELP_NAME_LEN)
  for hna in help_provider.help_spec.help_name_aliases:
    assert hna
  one_line_summary_len = len(help_provider.help_spec.help_one_line_summary)
  assert (one_line_summary_len >= MIN_ONE_LINE_SUMMARY_LEN), (
      'The one line summary "{text}" with a length of {length} must be ' +
      'more then {min} characters').format(
          text=help_provider.help_spec.help_one_line_summary,
          length=one_line_summary_len,
          min=MIN_ONE_LINE_SUMMARY_LEN)
  assert (one_line_summary_len <= MAX_ONE_LINE_SUMMARY_LEN), (
      'The one line summary "{text}" with a length of {length} must be ' +
      'less then {max} characters').format(
          text=help_provider.help_spec.help_one_line_summary,
          length=one_line_summary_len,
          max=MAX_ONE_LINE_SUMMARY_LEN)
  assert len(help_provider.help_spec.help_text
            ) > 10, 'The length of "{text}" must be less then 10'.format(
                text=help_provider.help_spec.help_text)

  # Ensure there are no dupe help names or aliases across commands.
  name_check_list = [help_provider.help_spec.help_name]
  name_check_list.extend(help_provider.help_spec.help_name_aliases)
  for name_or_alias in name_check_list:
    if name_or_alias in help_name_map:
      raise CommandException(
          'Duplicate help name/alias "%s" found while loading help from %s. '
          'That name/alias was already taken by %s' %
          (name_or_alias, help_provider.__module__,
           help_name_map[name_or_alias].__module__))


def CreateHelpText(synopsis, description):
  """Helper for adding help text headers given synopsis and description."""
  return SYNOPSIS_PREFIX + synopsis + DESCRIPTION_PREFIX + description
