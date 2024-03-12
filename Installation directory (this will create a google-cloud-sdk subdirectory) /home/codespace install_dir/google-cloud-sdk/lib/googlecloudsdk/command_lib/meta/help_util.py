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

"""Utilities for gcloud help document differences."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import contextlib
import os
import shutil
import time

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import parallel
from googlecloudsdk.core.util import text
import six


# Max number of test changes to display.
TEST_CHANGES_DISPLAY_MAX = 32


class Error(exceptions.Error):
  """Errors for this module."""


class HelpUpdateError(Error):
  """Update errors."""


def IsOwnersFile(path):
  """Return True if path refers to an OWNERS file."""
  return os.path.basename(path) == 'OWNERS'


def GetFileContents(file):
  """Returns the file contents and whether or not the file contains binary data.

  Args:
    file: A file path.

  Returns:
    A tuple of the file contents and whether or not the file contains binary
    contents.
  """
  try:
    contents = file_utils.ReadFileContents(file)
    is_binary = False
  except UnicodeError:
    contents = file_utils.ReadBinaryFileContents(file)
    is_binary = True
  return contents, is_binary


def GetDirFilesRecursive(directory):
  """Generates the set of all files in directory and its children recursively.

  Args:
    directory: The directory path name.

  Returns:
    A set of all files in directory and its children recursively, relative to
    the directory.
  """
  dirfiles = set()
  for dirpath, _, files in os.walk(six.text_type(directory)):
    for name in files:
      file = os.path.join(dirpath, name)
      relative_file = os.path.relpath(file, directory)
      dirfiles.add(relative_file)

  return dirfiles


@contextlib.contextmanager
def TimeIt(message):
  """Context manager to track progress and time blocks of code."""
  with progress_tracker.ProgressTracker(message, autotick=True):
    start = time.time()
    yield
    elapsed_time = time.time() - start
    log.status.Print('{} took {}'.format(message, elapsed_time))


class DiffAccumulator(object):
  """A module for accumulating DirDiff() differences."""

  def __init__(self):
    self._changes = 0

  # pylint: disable=unused-argument
  def Ignore(self, relative_file):
    """Checks if relative_file should be ignored by DirDiff().

    Args:
      relative_file: A relative file path name to be checked.

    Returns:
      True if path is to be ignored in the directory differences.
    """
    return False

  # pylint: disable=unused-argument
  def AddChange(self, op, relative_file, old_contents=None, new_contents=None):
    """Called for each file difference.

    AddChange() can construct the {'add', 'delete', 'edit'} file operations that
    convert old_dir to match new_dir. Directory differences are ignored.

    This base implementation counts the number of changes.

    Args:
      op: The change operation string;
        'add'; relative_file is not in old_dir.
        'delete'; relative_file is not in new_dir.
        'edit'; relative_file is different in new_dir.
      relative_file: The old_dir and new_dir relative path name of a file that
        changed.
      old_contents: The old file contents.
      new_contents: The new file contents.

    Returns:
      A prune value. If non-zero then DirDiff() returns immediately with that
      value.
    """
    self._changes += 1
    return None

  def GetChanges(self):
    """Returns the accumulated changes."""
    return self._changes

  def Validate(self, relative_file, contents):
    """Called for each file for content validation.

    Args:
      relative_file: The old_dir and new_dir relative path name of an existing
        file.
      contents: The file contents string.
    """
    pass


def DirDiff(old_dir, new_dir, diff):
  """Calls diff.AddChange(op, file) on files that changed from old_dir new_dir.

  diff.AddChange() can construct the {'add', 'delete', 'edit'} file operations
  that convert old_dir to match new_dir. Directory differences are ignored.

  Args:
    old_dir: The old directory path name.
    new_dir: The new directory path name.
    diff: A DiffAccumulator instance.

  Returns:
    The return value of the first diff.AddChange() call that returns non-zero
    or None if all diff.AddChange() calls returned zero.
  """
  with TimeIt('GetDirFilesRecursive new files'):
    new_files = GetDirFilesRecursive(new_dir)
  with TimeIt('GetDirFilesRecursive old files'):
    old_files = GetDirFilesRecursive(old_dir)

  def _FileDiff(file):
    """Diffs a file in new_dir and old_dir."""
    new_contents, new_binary = GetFileContents(os.path.join(new_dir, file))
    if not new_binary:
      diff.Validate(file, new_contents)

    if file in old_files:
      old_contents, old_binary = GetFileContents(os.path.join(old_dir, file))
      if old_binary == new_binary and old_contents == new_contents:
        return
      return 'edit', file, old_contents, new_contents
    else:
      return 'add', file, None, new_contents

  with parallel.GetPool(16) as pool:
    results = []
    for file in new_files:
      if diff.Ignore(file):
        continue
      result = pool.ApplyAsync(_FileDiff, (file,))
      results.append(result)

    for result_future in results:
      result = result_future.Get()
      if result:
        op, file, old_contents, new_contents = result
        prune = diff.AddChange(op, file, old_contents, new_contents)
        if prune:
          return prune

  for file in old_files:
    if diff.Ignore(file):
      continue
    if file not in new_files:
      prune = diff.AddChange('delete', file)
      if prune:
        return prune
  return None


class HelpAccumulator(DiffAccumulator):
  """Accumulates help document directory differences.

  Attributes:
    _changes: The list of DirDiff() (op, path) difference tuples.
    _restrict: The set of file path prefixes that the accumulator should be
      restricted to.
  """

  def __init__(self, restrict=None):
    super(HelpAccumulator, self).__init__()
    self._changes = []
    self._restrict = ({os.sep.join(r.split('.')[1:]) for r in restrict}
                      if restrict else {})

  def Ignore(self, relative_file):
    """Checks if relative_file should be ignored by DirDiff().

    Args:
      relative_file: A relative file path name to be checked.

    Returns:
      True if path is to be ignored in the directory differences.
    """
    if IsOwnersFile(relative_file):
      return True
    if not self._restrict:
      return False
    for item in self._restrict:
      if relative_file == item or relative_file.startswith(item + os.sep):
        return False
    return True

  def AddChange(self, op, relative_file, old_contents=None, new_contents=None):
    """Adds an DirDiff() difference tuple to the list of changes.

    Args:
      op: The difference operation, one of {'add', 'delete', 'edit'}.
      relative_file: The relative path of a file that has changed.
      old_contents: The old file contents.
      new_contents: The new file contents.

    Returns:
      None which signals DirDiff() to continue.
    """
    self._changes.append((op, relative_file))
    return None


class HelpUpdater(object):
  """Updates the document directory to match the current CLI.

  Attributes:
    _cli: The Current CLI.
    _directory: The help document directory.
    _generator: The document generator.
    _hidden: Boolean indicating whether to update hidden commands.
    _test: Show but do not apply operations if True.
  """

  def __init__(self, cli, directory, generator, test=False, hidden=False):
    """Constructor.

    Args:
      cli: The Current CLI.
      directory: The help document directory.
      generator: An uninstantiated walker_util document generator.
      test: Show but do not apply operations if True.
      hidden: Boolean indicating whether the hidden commands should be used.

    Raises:
      HelpUpdateError: If the destination directory does not exist.
    """
    if not os.path.isabs(directory):
      raise HelpUpdateError(
          'Destination directory [%s] must be absolute.' % directory)
    self._cli = cli
    self._directory = directory
    self._generator = generator
    self._hidden = hidden
    self._test = test

  def _Update(self, restrict):
    """Update() helper method. Returns the number of changed help doc files."""
    with file_utils.TemporaryDirectory() as temp_dir:
      pb = console_io.ProgressBar(label='Generating Help Document Files')
      with TimeIt('Creating walker'):
        walker = self._generator(
            self._cli, temp_dir, pb.SetProgress, restrict=restrict)
      start = time.time()
      pb.Start()
      walker.Walk(hidden=True)
      pb.Finish()
      elapsed_time = time.time() - start
      log.info('Generating Help Document Files took {}'.format(elapsed_time))

      diff = HelpAccumulator(restrict=restrict)
      with TimeIt('Diffing'):
        DirDiff(self._directory, temp_dir, diff)
      ops = collections.defaultdict(list)

      changes = 0
      with TimeIt('Getting diffs'):
        for op, path in sorted(diff.GetChanges()):
          changes += 1
          if not self._test or changes < TEST_CHANGES_DISPLAY_MAX:
            log.status.Print('{0} {1}'.format(op, path))
          ops[op].append(path)

      if self._test:
        if changes:
          if changes >= TEST_CHANGES_DISPLAY_MAX:
            log.status.Print('...')
          log.status.Print('{0} help text {1} changed'.format(
              changes, text.Pluralize(changes, 'file')))
        return changes

      with TimeIt('Updating destination files'):
        for op in ('add', 'edit', 'delete'):
          for path in ops[op]:
            dest_path = os.path.join(self._directory, path)
            if op in ('add', 'edit'):
              if op == 'add':
                subdir = os.path.dirname(dest_path)
                if subdir:
                  file_utils.MakeDir(subdir)
              temp_path = os.path.join(temp_dir, path)
              shutil.copyfile(temp_path, dest_path)
            elif op == 'delete':
              try:
                os.remove(dest_path)
              except OSError:
                pass

      return changes

  def Update(self, restrict=None):
    """Updates the help document directory to match the current CLI.

    Args:
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.

    Raises:
      HelpUpdateError: If the destination directory does not exist.

    Returns:
      The number of changed help document files.
    """
    if not os.path.isdir(self._directory):
      raise HelpUpdateError(
          'Destination directory [%s] must exist and be searchable.' %
          self._directory)
    try:
      return self._Update(restrict)
    except (IOError, OSError, SystemError) as e:
      raise HelpUpdateError('Update failed: %s' % six.text_type(e))

  def GetDiffFiles(self, restrict=None):
    """Print a list of help text files that are distinct from source, if any."""
    with file_utils.TemporaryDirectory() as temp_dir:
      walker = self._generator(
          self._cli, temp_dir, None, restrict=restrict)
      walker.Walk(hidden=True)
      diff = HelpAccumulator(restrict=restrict)
      DirDiff(self._directory, temp_dir, diff)
      return sorted(diff.GetChanges())
