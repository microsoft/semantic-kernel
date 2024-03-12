# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A command that lists all possible gcloud commands, optionally with flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.calliope import walker_util


_LOOKUP_INTERNAL_FLAGS = '_flags_'
_LOOKUP_INTERNAL_NAME = '_name_'


def DisplayFlattenedCommandTree(command, out=None):
  """Displays the commands in the command tree in sorted order on out.

  Args:
    command: dict, The tree (nested dict) of command/group names.
    out: stream, The output stream, sys.stdout if None.
  """

  def WalkCommandTree(commands, command, args):
    """Visit each command and group in the CLI command tree.

    Each command line is added to the commands list.

    Args:
      commands: [str], The list of command strings.
      command: dict, The tree (nested dict) of command/group names.
      args: [str], The subcommand arg prefix.
    """
    args_next = args + [command[_LOOKUP_INTERNAL_NAME]]
    if commands:
      commands.append(' '.join(args_next))
    else:
      # List the global flags with the root command.
      commands.append(' '.join(
          args_next + command.get(_LOOKUP_INTERNAL_FLAGS, [])))
    if cli_tree.LOOKUP_COMMANDS in command:
      for c in command[cli_tree.LOOKUP_COMMANDS]:
        name = c.get(_LOOKUP_INTERNAL_NAME, c)
        flags = c.get(_LOOKUP_INTERNAL_FLAGS, [])
        commands.append(' '.join(args_next + [name] + flags))
    if cli_tree.LOOKUP_GROUPS in command:
      for g in command[cli_tree.LOOKUP_GROUPS]:
        WalkCommandTree(commands, g, args_next)

  commands = []
  WalkCommandTree(commands, command, [])
  if not out:
    out = sys.stdout
  out.write('\n'.join(sorted(commands)) + '\n')


_COMPLETIONS_PREFIX = '_SC_'


def DisplayCompletions(command, out=None):
  """Displays the static tab completion data on out.

  The static completion data is a shell script containing variable definitons
  of the form {_COMPLETIONS_PREFIX}{COMMAND.PATH} for each dotted command path.

  Args:
    command: dict, The tree (nested dict) of command/group names.
    out: stream, The output stream, sys.stdout if None.
  """

  def ConvertPathToIdentifier(path):
    return _COMPLETIONS_PREFIX + '__'.join(path).replace('-', '_')

  def WalkCommandTree(command, prefix):
    """Visit each command and group in the CLI command tree.

    Args:
      command: dict, The tree (nested dict) of command/group names.
      prefix: [str], The subcommand arg prefix.
    """
    name = command.get(_LOOKUP_INTERNAL_NAME)
    args = prefix + [name]
    commands = command.get(cli_tree.LOOKUP_COMMANDS, [])
    groups = command.get(cli_tree.LOOKUP_GROUPS, [])
    names = []
    for c in commands + groups:
      names.append(c.get(_LOOKUP_INTERNAL_NAME, c))
    if names:
      flags = command.get(_LOOKUP_INTERNAL_FLAGS, [])
      if prefix:
        out.write('{identifier}=({args})\n'.format(
            identifier=ConvertPathToIdentifier(args),
            args=' '.join(names + flags)))
      else:
        out.write('{identifier}=({args})\n'.format(
            identifier=ConvertPathToIdentifier(['-GCLOUD-WIDE-FLAGS-']),
            args=' '.join(flags)))
        out.write('{identifier}=({args})\n'.format(
            identifier=ConvertPathToIdentifier(args),
            args=' '.join(names)))
      for c in commands:
        name = c.get(_LOOKUP_INTERNAL_NAME, c)
        flags = c.get(_LOOKUP_INTERNAL_FLAGS, [])
        out.write('{identifier}=({args})\n'.format(
            identifier=ConvertPathToIdentifier(args + [name]),
            args=' '.join(flags)))
    for g in groups:
      WalkCommandTree(g, args)

  if not out:
    out = sys.stdout
  WalkCommandTree(command, [])


class ListCommands(base.Command):
  """List all possible gcloud commands excluding flags."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--completions',
        action='store_true',
        help=("""\
              Write the static TAB completion data on the standard output. The
              data is a shell script containing variable definitons of the
              form ```""" +
              _COMPLETIONS_PREFIX +
              '{COMMAND.PATH}``` for each dotted command path.')
    )
    parser.add_argument(
        '--flags',
        action='store_true',
        help='Include the non-global flags for each command/group.')
    parser.add_argument(
        '--flag-values',
        action='store_true',
        help="""\
        Include the non-global flags and flag values/types for each
        command/group. Flags with fixed choice values will be listed as
        --flag=choice1,..., and flags with typed values will be listed
        as --flag=:type:.""")
    parser.add_argument(
        '--hidden',
        action='store_true',
        help='Include hidden commands and groups.')
    parser.add_argument(
        'restrict',
        metavar='COMMAND/GROUP',
        nargs='*',
        help=('Restrict the listing to these dotted command paths. '
              'For example: gcloud.alpha gcloud.beta.test'))

  def Run(self, args):
    if args.completions:
      args.flags = True
      args.flag_values = True
      args.hidden = True
    return walker_util.CommandTreeGenerator(
        self._cli_power_users_only, with_flags=args.flags,
        with_flag_values=args.flag_values).Walk(args.hidden, args.restrict)

  def Display(self, args, result):
    if args.completions:
      return DisplayCompletions(result)
    return DisplayFlattenedCommandTree(result)
