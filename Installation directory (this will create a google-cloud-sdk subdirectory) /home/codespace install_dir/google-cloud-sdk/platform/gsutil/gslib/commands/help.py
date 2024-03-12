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
"""Implementation of gsutil help command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import itertools
import os
import pkgutil
import re
import six
from subprocess import PIPE
from subprocess import Popen

import gslib.addlhelp
from gslib.command import Command
from gslib.command import OLD_ALIAS_MAP
import gslib.commands
from gslib.exception import CommandException
from gslib.help_provider import HelpProvider
from gslib.help_provider import MAX_HELP_NAME_LEN
from gslib.utils import constants
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.system_util import IsRunningInteractively
from gslib.utils.system_util import GetTermLines
from gslib.utils import text_util

_SYNOPSIS = """
  gsutil help [command or topic]
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The following command provides a summary of gsutil commands and additional topics on which
  help is available:

    gsutil help

  The following command provides help about the specified command or topic:

    gsutil help [command or topic]

  The following command provides help about the specified sub-command:

    gsutil help [command] [sub-command]

  For example, running the following provides help about the "set" sub-command of the "acl" command:

    gsutil help acl set

  If you set the PAGER environment variable to the path to a pager program
  (such as /bin/less on Linux), long help sections are piped through
  the specified pager.
""")

top_level_usage_string = (
    'Usage: gsutil [-D] [-DD] [-h header]... [-i service_account] '
    '[-m] [-o section:flag=value]... [-q] [-u user_project] [command [opts...] args...]'
)


class HelpCommand(Command):
  """Implementation of gsutil help command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'help',
      command_name_aliases=['?', 'man'],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=2,
      supported_sub_args='',
      file_url_ok=True,
      provider_url_ok=False,
      urls_start_arg=0,
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='help',
      help_name_aliases=['?'],
      help_type='command_help',
      help_one_line_summary='Get help about commands and topics',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def RunCommand(self):
    """Command entry point for the help command."""
    (help_type_map, help_name_map) = self._LoadHelpMaps()
    output = []
    if not self.args:
      output.append('%s\nAvailable commands:\n' % top_level_usage_string)
      format_str = '  %-' + str(MAX_HELP_NAME_LEN) + 's%s\n'
      for help_prov in sorted(help_type_map['command_help'],
                              key=lambda hp: hp.help_spec.help_name):
        output.append(format_str % (help_prov.help_spec.help_name,
                                    help_prov.help_spec.help_one_line_summary))
      output.append('\nAdditional help topics:\n')
      for help_prov in sorted(help_type_map['additional_help'],
                              key=lambda hp: hp.help_spec.help_name):
        output.append(format_str % (help_prov.help_spec.help_name,
                                    help_prov.help_spec.help_one_line_summary))
      output.append('\nUse gsutil help <command or topic> for detailed help.')
    else:
      invalid_subcommand = False
      arg = self.args[0]
      if arg not in help_name_map:
        output.append('No help available for "%s"' % arg)
      else:
        help_prov = help_name_map[arg]
        help_name = None
        if len(self.args) > 1:  # We also have a subcommand argument.
          subcommand_map = help_prov.help_spec.subcommand_help_text
          if subcommand_map and self.args[1] in subcommand_map:
            help_name = arg + ' ' + self.args[1]
            help_text = subcommand_map[self.args[1]]
          else:
            invalid_subcommand = True
            if not subcommand_map:
              output.append(
                  ('The "%s" command has no subcommands. You can ask for the '
                   'full help by running:\n\n\tgsutil help %s\n') % (arg, arg))
            else:
              subcommand_examples = []
              for subcommand in subcommand_map:
                subcommand_examples.append('\tgsutil help %s %s' %
                                           (arg, subcommand))
              output.append(
                  ('Subcommand "%s" does not exist for command "%s".\n'
                   'You can either ask for the full help about the command by '
                   'running:\n\n\tgsutil help %s\n\n'
                   'Or you can ask for help about one of the subcommands:\n\n%s'
                  ) % (self.args[1], arg, arg, '\n'.join(subcommand_examples)))
        if not invalid_subcommand:
          if not help_name:  # No subcommand or invalid subcommand.
            help_name = help_prov.help_spec.help_name
            help_text = help_prov.help_spec.help_text

          output.append('<B>NAME</B>\n')
          output.append('  %s - %s\n' %
                        (help_name, help_prov.help_spec.help_one_line_summary))
          output.append('\n\n')
          output.append(help_text.strip('\n'))
          new_alias = OLD_ALIAS_MAP.get(arg, [None])[0]
          if new_alias:
            deprecation_warning = """
  The "%s" alias is deprecated, and will eventually be removed completely.
  Please use the "%s" command instead.""" % (arg, new_alias)

            output.append('\n\n\n<B>DEPRECATION WARNING</B>\n')
            output.append(deprecation_warning)
    self._OutputHelp(''.join(output))
    return 0

  def _OutputHelp(self, help_str):
    """Outputs simply formatted string.

    This function paginates if the string is too long, PAGER is defined, and
    the output is a tty.

    Args:
      help_str: String to format.
    """
    # Remove <B> and </B> tags and replace them with ANSI control codes if
    # writing to a compatible tty.
    if IS_WINDOWS or not IsRunningInteractively():
      help_str = re.sub('<B>', '', help_str)
      help_str = re.sub('</B>', '', help_str)
      text_util.print_to_fd(help_str)
      return
    help_str = re.sub('<B>', '\033[1m', help_str)
    help_str = re.sub('</B>', '\033[0;0m', help_str)
    num_lines = len(help_str.split('\n'))
    if 'PAGER' in os.environ and num_lines >= GetTermLines():
      # Use -r option for less to make bolding work right.
      pager = os.environ['PAGER'].split(' ')
      if pager[0].endswith('less'):
        pager.append('-r')
      try:
        if six.PY2:
          input_for_pager = help_str.encode(constants.UTF8)
        else:
          input_for_pager = help_str
        Popen(pager, stdin=PIPE,
              universal_newlines=True).communicate(input=input_for_pager)
      except OSError as e:
        raise CommandException('Unable to open pager (%s): %s' %
                               (' '.join(pager), e))
    else:
      text_util.print_to_fd(help_str)

  def _LoadHelpMaps(self):
    """Returns tuple of help type and help name.

    help type is a dict with key: help type
                             value: list of HelpProviders
    help name is a dict with key: help command name or alias
                             value: HelpProvider

    Returns:
      (help type, help name)
    """

    # Import all gslib.commands submodules.
    for _, module_name, _ in pkgutil.iter_modules(gslib.commands.__path__):
      __import__('gslib.commands.%s' % module_name)
    # Import all gslib.addlhelp submodules.
    for _, module_name, _ in pkgutil.iter_modules(gslib.addlhelp.__path__):
      __import__('gslib.addlhelp.%s' % module_name)

    help_type_map = {}
    help_name_map = {}
    for s in gslib.help_provider.ALL_HELP_TYPES:
      help_type_map[s] = []
    # Only include HelpProvider subclasses in the dict.
    for help_prov in itertools.chain(HelpProvider.__subclasses__(),
                                     Command.__subclasses__()):
      if help_prov is Command:
        # Skip the Command base class itself; we just want its subclasses,
        # where the help command text lives (in addition to non-Command
        # HelpProviders, like naming.py).
        continue
      gslib.help_provider.SanityCheck(help_prov, help_name_map)
      help_name_map[help_prov.help_spec.help_name] = help_prov
      for help_name_aliases in help_prov.help_spec.help_name_aliases:
        help_name_map[help_name_aliases] = help_prov
      help_type_map[help_prov.help_spec.help_type].append(help_prov)
    return (help_type_map, help_name_map)
