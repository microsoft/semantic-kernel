# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A module for walking the Cloud SDK CLI tree."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
import six


class Walker(object):
  """Base class for walking the Cloud SDK CLI tree.

  Attributes:
    _roots: The root elements of the CLI tree that will be walked.
    _num_nodes: The total number of nodes in the tree.
    _num_visited: The count of visited nodes so far.
    _progress_callback: The progress bar function to call to update progress.
  """

  def __init__(self, cli, progress_callback=None, ignore_load_errors=False,
               restrict=None):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      ignore_load_errors: bool, True to ignore command load failures. This
        should only be used when it is not critical that all data is returned,
        like for optimizations like static tab completion.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups. When provided here, any groups above the restrictions
        in the tree will not be loaded or visited.
    """
    top = cli._TopElement()  # pylint: disable=protected-access
    if restrict:
      roots = [self._GetSubElement(top, r) for r in restrict]
      self._roots = [r for r in roots if r]
    else:
      self._roots = [top]

    self._num_nodes = 0
    if progress_callback:
      with progress_tracker.ProgressTracker('Loading CLI Tree'):
        for root in self._roots:
          self._num_nodes += 1.0 + root.LoadAllSubElements(
              recursive=True, ignore_load_errors=ignore_load_errors)
    else:
      for root in self._roots:
        self._num_nodes += 1.0 + root.LoadAllSubElements(
            recursive=True, ignore_load_errors=ignore_load_errors)

    self._num_visited = 0
    self._progress_callback = (progress_callback or
                               console_io.DefaultProgressBarCallback)

  def _GetSubElement(self, top_element, path):
    parts = path.split('.')[1:]
    current = top_element
    for part in parts:
      current = current.LoadSubElement(part)
      if not current:
        return None
    return current

  def Walk(self, hidden=False, restrict=None):
    """Calls self.Visit() on each node in the CLI tree.

    The walk is DFS, ordered by command name for reproducability.

    Args:
      hidden: Include hidden groups and commands if True.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups. When provided here, parent groups will still be visited
        as the walk progresses down to these leaves, but only parent groups
        between the restrictions and the root.

    Returns:
      The return value of the top level Visit() call.
    """
    def _Include(command, traverse=False):
      """Determines if command should be included in the walk.

      Args:
        command: CommandCommon command node.
        traverse: If True then check traversal through group to subcommands.

      Returns:
        True if command should be included in the walk.
      """
      if not hidden and command.IsHidden():
        return False
      if not restrict:
        return True
      path = '.'.join(command.GetPath())
      for item in restrict:
        if path.startswith(item):
          return True
        if traverse and item.startswith(path):
          return True
      return False

    def _Walk(node, parent):
      """Walk() helper that calls self.Visit() on each node in the CLI tree.

      Args:
        node: CommandCommon tree node.
        parent: The parent Visit() return value, None at the top level.

      Returns:
        The return value of the outer Visit() call.
      """
      if not node.is_group:
        self._Visit(node, parent, is_group=False)
        return parent

      parent = self._Visit(node, parent, is_group=True)
      commands_and_groups = []

      if node.commands:
        for name, command in six.iteritems(node.commands):
          if _Include(command):
            commands_and_groups.append((name, command, False))
      if node.groups:
        for name, command in six.iteritems(node.groups):
          if _Include(command, traverse=True):
            commands_and_groups.append((name, command, True))
      for _, command, is_group in sorted(commands_and_groups):
        if is_group:
          _Walk(command, parent)
        else:
          self._Visit(command, parent, is_group=False)
      return parent

    self._num_visited = 0
    parent = None
    for root in self._roots:
      parent = _Walk(root, None)
    self.Done()
    return parent

  def _Visit(self, node, parent, is_group):
    self._num_visited += 1
    self._progress_callback(self._num_visited // self._num_nodes)
    return self.Visit(node, parent, is_group)

  def Visit(self, node, parent, is_group):
    """Visits each node in the CLI command tree.

    Called preorder by WalkCLI() using DFS.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      A new parent value for the node subtree. This value is the parent arg
      for the Visit() calls for the children of this node.
    """
    pass

  def Done(self):
    """Cleans up after all nodes in the CLI tree have been visited."""
    pass
