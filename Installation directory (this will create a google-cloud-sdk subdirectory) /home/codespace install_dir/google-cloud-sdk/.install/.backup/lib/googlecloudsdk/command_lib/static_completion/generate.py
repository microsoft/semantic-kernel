# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Static completion CLI tree generator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import walker
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_projector


class _Command(object):
  """Command/group info.

  Attributes:
    commands: {str:_Command}, The subcommands in a command group.
    flags: [str], Command flag list. Global flags, available to all commands,
      are in the root command flags list.
  """

  def __init__(self, command, parent):
    self.commands = {}
    self.flags = {}

    # _parent is explicitly private so it won't appear in the output.
    self._parent = parent
    if parent:
      name = command.name.replace('_', '-')
      parent.commands[name] = self

    args = command.ai

    # Collect the command specific flags.
    for arg in args.flag_args:
      for name in arg.option_strings:
        if arg.is_hidden:
          continue
        if not name.startswith('--'):
          continue
        if self.__Ancestor(name):
          continue
        self.__AddFlag(arg, name)

    # Collect the ancestor flags.
    for arg in args.ancestor_flag_args:
      for name in arg.option_strings:
        # NOTICE: The full CLI tree includes is_global ancestor flags.
        if arg.is_global or arg.is_hidden:
          continue
        if not name.startswith('--'):
          continue
        self.__AddFlag(arg, name)

  def __AddFlag(self, flag, name):
    choices = 'bool'
    if flag.choices:
      choices = sorted(flag.choices)
      if choices == ['false', 'true']:
        choices = 'bool'
    elif flag.nargs != 0:
      choices = 'dynamic' if getattr(flag, 'completer', None) else 'value'
    self.flags[name] = choices

  def __Ancestor(self, flag):
    """Determines if flag is provided by an ancestor command.

    Args:
      flag: str, The flag name (no leading '-').

    Returns:
      bool, True if flag provided by an ancestor command, false if not.
    """
    command = self._parent
    while command:
      if flag in command.flags:
        return True
      command = command._parent  # pylint: disable=protected-access
    return False


class _CompletionTreeGenerator(walker.Walker):
  """Generates the gcloud static completion CLI tree."""

  def __init__(self, cli=None, branch=None, ignore_load_errors=False):
    """branch is the command path of the CLI subtree to generate."""
    super(_CompletionTreeGenerator, self).__init__(
        cli=cli, ignore_load_errors=ignore_load_errors)
    self._branch = branch

  def Visit(self, node, parent, is_group):
    """Visits each node in the CLI command tree to construct the external rep.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a command group.

    Returns:
      The subtree parent value, used here to construct an external rep node.
    """
    if self._Prune(node):
      return parent
    return _Command(node, parent)

  def _Prune(self, command):
    """Returns True if command should be pruned from the CLI tree.

    Branch pruning is mainly for generating static unit test data. The static
    tree for the entire CLI would be an unnecessary burden on the depot.

    self._branch, if not None, is already split into a path with the first
    name popped. If branch is not a prefix of command.GetPath()[1:] it will
    be pruned.

    Args:
      command: The calliope Command object to check.

    Returns:
      True if command should be pruned from the CLI tree.
    """
    # Only prune if branch is not empty.
    if not self._branch:
      return False
    path = command.GetPath()
    # The top level command is never pruned.
    if len(path) < 2:
      return False
    path = path[1:]
    # All tracks in the branch are active.
    if path[0] in ('alpha', 'beta'):
      path = path[1:]
    for name in self._branch:
      # branch is longer than path => don't prune.
      if not path:
        return False
      # prefix mismatch => prune.
      if path[0] != name:
        return True
      path.pop(0)
    # branch is a prefix of path => don't prune.
    return False


def GenerateCompletionTree(cli, branch=None, ignore_load_errors=False):
  """Generates and returns the static completion CLI tree.

  Args:
    cli: The CLI.
    branch: The path of the CLI subtree to generate.
    ignore_load_errors: Ignore CLI tree load errors if True.

  Returns:
    Returns the serialized static completion CLI tree.
  """
  with progress_tracker.ProgressTracker(
      'Generating the static completion CLI tree.'):
    return resource_projector.MakeSerializable(
        _CompletionTreeGenerator(
            cli, branch=branch, ignore_load_errors=ignore_load_errors).Walk())


def ListCompletionTree(cli, branch=None, out=None):
  """Lists the static completion CLI tree as a Python module file.

  Args:
    cli: The CLI.
    branch: The path of the CLI subtree to generate.
    out: The output stream to write to, sys.stdout by default.

  Returns:
    Returns the serialized static completion CLI tree.
  """
  tree = GenerateCompletionTree(cli=cli, branch=branch)
  (out or sys.stdout).write('''\
# -*- coding: utf-8 -*- #
"""Cloud SDK static completion CLI tree."""
# pylint: disable=line-too-long,bad-continuation
STATIC_COMPLETION_CLI_TREE = ''')
  resource_printer.Print(tree, print_format='json', out=out)
  return tree
