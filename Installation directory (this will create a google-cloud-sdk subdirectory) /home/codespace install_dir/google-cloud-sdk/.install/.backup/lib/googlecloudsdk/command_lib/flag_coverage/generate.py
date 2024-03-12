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

"""Coverage tree generator. Used for flag coverage kokoro presubmit."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import walker
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_projector


def GenerateCoverageTree(cli, branch=None, restrict=None):
  """Generates and returns the static completion CLI tree.

  Args:
    cli: The CLI.
    branch: The path of the CLI subtree to generate.
    restrict: The paths in the tree that we are allowing the tree to walk under.

  Returns:
    Returns the serialized static completion CLI tree.
  """
  with progress_tracker.ProgressTracker(
      'Generating the flag coverage CLI tree.'):
    return resource_projector.MakeSerializable(
        CoverageTreeGenerator(cli, branch, restrict=restrict).Walk())


class CoverageCommandNode(dict):
  """Command/group info.

  Attributes:
    commands: {str:_Command}, The subcommands in a command group.
    flags: [str], Command flag list. Global flags, available to all commands,
      are in the root command flags list.
  """

  def __init__(self, command, parent):
    super(CoverageCommandNode, self).__init__()
    # _parent is explicitly private so it won't appear in the output.
    self._parent = parent
    if parent is not None:
      name = command.name.replace('_', '-')
      parent[name] = self

    args = command.ai
    # Collect the command specific flags.
    for arg in args.flag_args:
      for name in arg.option_strings:
        if arg.is_hidden:
          continue
        if not name.startswith('--'):
          continue
        if self.IsAncestorFlag(name):
          continue
        self[name] = arg.require_coverage_in_tests

  def IsAncestorFlag(self, flag):
    """Determines if flag is provided by an ancestor command.

    NOTE: This function is used to allow for global flags to be added in at the
          top level but not in subgroups/commands
    Args:
      flag: str, The flag name (no leading '-').

    Returns:
      bool, True if flag provided by an ancestor command, false if not.
    """
    command = self._parent
    while command:
      if flag in command:
        return True
      command = command._parent  # pylint: disable=protected-access
    return False


class CoverageTreeGenerator(walker.Walker):
  """Generates the gcloud static completion CLI tree."""

  def __init__(self, cli=None, branch=None, restrict=None):
    """branch is the command path of the CLI subtree to generate."""
    super(CoverageTreeGenerator, self).__init__(cli=cli, restrict=restrict)
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
    return CoverageCommandNode(node, parent)


def OutputCoverageTree(cli, branch=None, out=None, restrict=None):
  """Lists the flag coverage CLI tree as a Python module file.

  Args:
    cli: The CLI.
    branch: The path of the CLI subtree to generate.
    out: The output stream to write to, sys.stdout by default.
    restrict: The paths in the tree that we are allowing the tree to walk under.

  Returns:
    Returns the serialized coverage CLI tree.
  """
  tree = GenerateCoverageTree(cli=cli, branch=branch, restrict=restrict)
  resource_printer.Print(tree, print_format='json', out=out)
  return tree
