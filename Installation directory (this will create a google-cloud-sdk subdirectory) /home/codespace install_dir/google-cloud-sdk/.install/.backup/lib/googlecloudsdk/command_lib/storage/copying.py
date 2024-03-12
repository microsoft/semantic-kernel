# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Utilities for computing copy operations from command arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.storage import expansion
from googlecloudsdk.command_lib.storage import paths
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core import exceptions


class Error(exceptions.Error):
  pass


class WildcardError(Error):
  pass


class RecursionError(Error):
  pass


class LocationMismatchError(Error):
  pass


class DestinationDirectoryExistsError(Error):
  pass


class DestinationNotDirectoryError(Error):
  pass


class InvalidDestinationError(Error):

  def __init__(self, source, dest):
    super(InvalidDestinationError, self).__init__(
        'Cannot copy [{}] to [{}] because of "." or ".." in the path. '
        'gcloud does not support Cloud Storage paths containing these path '
        'segments and it is recommended that you do not name objects in '
        'this way. Other tooling may convert these paths to incorrect '
        'local directories.'.format(source.path, dest.path))


class CopyTaskGenerator(object):
  """A helper to compute and generate the tasks required to perform a copy."""

  def __init__(self):
    # Create a single instance of each expander so that all expansion uses the
    # same cached data.
    self._local_expander = expansion.LocalPathExpander()
    self._gcs_expander = expansion.GCSPathExpander()

  def _GetExpander(self, path):
    """Get the correct expander for this type of path."""
    if path.is_remote:
      return self._gcs_expander
    return self._local_expander

  def GetCopyTasks(self, sources, dest, recursive=False):
    """Get all the file copy tasks for the sources given to this copier.

    Args:
      sources: [paths.Path], The sources (containing optional wildcards) that
        you want to copy.
      dest: paths.Path, The wildcard-free path you want to copy the sources to.
      recursive: bool, True to allow recursive copying of directories.

    Raises:
      WildcardError: If dest contains a wildcard.
      LocationMismatchError: If you are trying to copy local files to local
        files.
      DestinationNotDirectoryError: If trying to copy multiple files to a single
        dest name.
      RecursionError: If any of sources are directories, but recursive is
        false.

    Returns:
      [storage_parallel.Task], All the tasks that should be executed to perform
      this copy.
    """
    # Sources go through the expander where they are converted to absolute
    # paths. The dest does not, so convert it manually here.
    dest_is_dir = dest.is_dir_like
    dest = paths.Path(self._GetExpander(dest).AbsPath(dest.path))
    if dest_is_dir:
      dest = dest.Join('')

    if expansion.PathExpander.HasExpansion(dest.path):
      raise WildcardError(
          'Destination [{}] cannot contain wildcards.'.format(dest.path))

    if not dest.is_remote:
      local_sources = [s for s in sources if not s.is_remote]
      if local_sources:
        raise LocationMismatchError(
            'When destination is a local path, all sources must be remote '
            'paths.')

    files, dirs = self._ExpandFilesToCopy(sources)

    if not dest.is_dir_like:
      # Destination is a file, we can only perform a single file/dir copy.
      if (len(files) + len(dirs)) > 1:
        raise DestinationNotDirectoryError(
            'When copying multiple sources, destination must be a directory '
            '(a path ending with a slash).')
    if dirs and not recursive:
      raise RecursionError(
          'Source path matches directories but --recursive was not specified.')

    tasks = []
    tasks.extend(self._GetFileCopyTasks(files, dest))
    tasks.extend(self._GetDirCopyTasks(dirs, dest))
    return tasks

  def _ExpandFilesToCopy(self, sources):
    """Do initial expansion of all the wildcard arguments.

    Args:
      sources: [paths.Path], The sources (containing optional wildcards) that
        you want to copy.

    Returns:
      ([paths.Path], [paths.Path]), The file and directory paths that the
      initial set of sources expanded to.
    """
    files = set()
    dirs = set()
    for s in sources:
      expander = self._GetExpander(s)
      (current_files, current_dirs) = expander.ExpandPath(s.path)
      files.update(current_files)
      dirs.update(current_dirs)

    return ([paths.Path(f) for f in sorted(files)],
            [paths.Path(d) for d in sorted(dirs)])

  def _GetDirCopyTasks(self, dirs, dest):
    """Get the Tasks to be executed to copy the given directories.

    If dest is dir-like (ending in a slash), all dirs are copied under the
    destination. If it is file-like, at most one directory can be provided and
    it is copied directly to the destination name.

    File copy tasks are generated recursively for the contents of all
    directories.

    Args:
      dirs: [paths.Path], The directories to copy.
      dest: paths.Path, The destination to copy the directories to.

    Returns:
      [storage_parallel.Task], The file copy tasks to execute.
    """
    tasks = []
    for d in dirs:
      item_dest = self._GetDestinationName(d, dest)
      expander = self._GetExpander(d)
      (files, sub_dirs) = expander.ExpandPath(d.Join('*').path)
      files = [paths.Path(f) for f in sorted(files)]
      sub_dirs = [paths.Path(d) for d in sorted(sub_dirs)]
      tasks.extend(self._GetFileCopyTasks(files, item_dest))
      tasks.extend(self._GetDirCopyTasks(sub_dirs, item_dest))
    return tasks

  def _GetFileCopyTasks(self, sources, dest):
    """Get the Tasks to be executed to copy the given sources.

    If dest is dir-like (ending in a slash), all sources are copied under the
    destination. If it is file-like, at most one source can be provided and it
    is copied directly to the destination name.

    Args:
      sources: [paths.Path], The source files to copy. These must all be files
        not directories.
      dest: paths.Path, The destination to copy the files to.

    Returns:
      [storage_parallel.Task], The file copy tasks to execute.
    """
    if not sources:
      return []
    tasks = []
    for source in sources:
      item_dest = self._GetDestinationName(source, dest)
      tasks.append(self._MakeTask(source, item_dest))

    return tasks

  def _GetDestinationName(self, item, dest):
    """Computes the destination name to copy item to.."""
    expander = self._GetExpander(dest)

    if dest.is_dir_like:
      item_dest = dest.Join(
          os.path.basename(item.path.rstrip('/').rstrip('\\')))
      if item.is_dir_like:
        item_dest = item_dest.Join('')
      if expander.IsFile(dest.path):
        raise DestinationDirectoryExistsError(
            'Cannot copy [{}] to [{}]: [{}] exists and is a file.'.format(
                item.path, item_dest.path, dest.path))
    else:
      item_dest = dest

    # If copying a directory, then if the target exists at all it's a problem.
    # If copying a file we only need to ensure that the target is not a
    # directory. If it's just a file it will be overwritten.
    check_func = expander.Exists if item.is_dir_like else expander.IsDir
    if check_func(item_dest.path):
      raise DestinationDirectoryExistsError(
          'Cannot copy [{}] to [{}]: The destination already exists. If you '
          'meant to copy under this destination, add a slash to the end of its '
          'path.'
          .format(item.path, item_dest.path))

    return item_dest

  def _MakeTask(self, source, dest):
    """Make a file copy Task for a single source.

    Args:
      source: paths.Path, The source file to copy.
      dest: path.Path, The destination to copy the file to.

    Raises:
      InvalidDestinationError: If this would end up copying to a path that has
        '.' or '..' as a segment.
      LocationMismatchError: If trying to copy a local file to a local file.

    Returns:
      storage_parallel.Task, The copy task to execute.
    """
    if not dest.IsPathSafe():
      raise InvalidDestinationError(source, dest)
    if source.is_remote:
      source_obj = storage_util.ObjectReference.FromUrl(source.path)
      if dest.is_remote:
        dest_obj = storage_util.ObjectReference.FromUrl(dest.path)
        return storage_parallel.FileRemoteCopyTask(source_obj, dest_obj)
      return storage_parallel.FileDownloadTask(source_obj, dest.path)

    # Local source file.
    if dest.is_remote:
      dest_obj = storage_util.ObjectReference.FromUrl(dest.path)
      return storage_parallel.FileUploadTask(source.path, dest_obj)

    # Both local, can't do this.
    raise LocationMismatchError(
        'Cannot copy local file [{}] to local file [{}]'.format(
            source.path, dest.path))
