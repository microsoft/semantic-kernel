# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Library for ignoring files for upload.

This library very closely mimics the semantics of Git's gitignore file:
https://git-scm.com/docs/gitignore

See `gcloud topic gcloudignore` for details.

A typical use would be:

  file_chooser = gcloudignore.GetFileChooserForDir(upload_directory)
  for f in file_chooser.GetIncludedFiles('some/path'):
    print 'uploading {}'.format(f)
    # actually do the upload, too
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

import enum

from googlecloudsdk.command_lib.util import glob
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

import six
from six.moves import map  # pylint: disable=redefined-builtin

IGNORE_FILE_NAME = '.gcloudignore'
GIT_FILES = ['.git', '.gitignore']
DEFAULT_IGNORE_FILE = """\
# This file specifies files that are *not* uploaded to Google Cloud
# using gcloud. It follows the same syntax as .gitignore, with the addition of
# "#!include" directives (which insert the entries of the given .gitignore-style
# file at that point).
#
# For more information, run:
#   $ gcloud topic gcloudignore
#
.gcloudignore
# If you would like to upload your .git directory, .gitignore file or files
# from your .gitignore file, remove the corresponding line
# below:
.git
.gitignore
"""
_GCLOUDIGNORE_PATH_SEP = '/'
_ENDS_IN_ODD_NUMBER_SLASHES_RE = r'(?<!\\)\\(\\\\)*$'


class InternalParserError(Exception):
  """An internal error in ignore file parsing."""


class BadFileError(InternalParserError):
  """Error indicating that a provided file was invalid."""


class BadIncludedFileError(exceptions.Error):
  """Error indicating that a provided file was invalid."""


class SymlinkLoopError(exceptions.Error):
  """Error indicating that there is a symlink loop."""


class Match(enum.Enum):
  """Indicates whether an ignore pattern matches or explicitly includes a path.

  INCLUDE: path matches, and is included
  IGNORE: path matches, and is ignored
  NO_MATCH: file is not matched
  """

  INCLUDE = 1
  IGNORE = 2
  NO_MATCH = 3


class Pattern(object):
  """An ignore-file pattern.

  Corresponds to one non-blank, non-comment line in the ignore-file.

  See https://git-scm.com/docs/gitignore for full syntax specification.

  If it matches a string, will return Match.IGNORE (or Match.INCLUDE if
  negated).
  """

  def __init__(self, pattern, negated=False, must_be_dir=False):
    self.pattern = pattern
    self.negated = negated
    self.must_be_dir = must_be_dir

  def Matches(self, path, is_dir=False):
    """Returns a Match for this pattern and the given path."""
    if self.pattern.Matches(path, is_dir=is_dir):
      return Match.INCLUDE if self.negated else Match.IGNORE
    else:
      return Match.NO_MATCH

  @classmethod
  def FromString(cls, line):
    """Creates a pattern for an individual line of an ignore file.

    Windows-style newlines must be removed.

    Args:
      line: str, The line to parse.

    Returns:
      Pattern.

    Raises:
      InvalidLineError: if the line was invalid (comment, blank, contains
        invalid consecutive stars).
    """
    if line.startswith('#'):
      raise glob.InvalidLineError('Line [{}] begins with `#`.'.format(line))
    if line.startswith('!'):
      line = line[1:]
      negated = True
    else:
      negated = False
    return cls(glob.Glob.FromString(line), negated=negated)


class FileChooser(object):
  """A FileChooser determines which files in a directory to upload.

  It's a fancy way of constructing a predicate (IsIncluded) along with a
  convenience method for walking a directory (GetIncludedFiles) and listing
  files to be uploaded based on that predicate.

  How the predicate operates is based on a gcloudignore file (see module
  docstring for details).
  """

  _INCLUDE_DIRECTIVE = '!include:'

  def __init__(self, patterns):
    self.patterns = patterns

  def IsIncluded(self, path, is_dir=False):
    """Returns whether the given file/directory should be included.

    This is determined according to the rules at
    https://git-scm.com/docs/gitignore except that symlinks are followed.

    In particular:
    - the method goes through pattern-by-pattern in-order
    - any matches of a parent directory on a particular pattern propagate to its
      children
    - if a parent directory is ignored, its children cannot be re-included

    Args:
      path: str, the path (relative to the root upload directory) to test.
      is_dir: bool, whether the path is a directory (or symlink to a directory).

    Returns:
      bool, whether the file should be uploaded
    """
    path_prefixes = glob.GetPathPrefixes(path)[1:]  # root dir can't be matched
    for path_prefix in path_prefixes:
      prefix_match = Match.NO_MATCH
      for pattern in self.patterns:
        is_prefix_dir = path_prefix != path or is_dir
        match = pattern.Matches(path_prefix, is_dir=is_prefix_dir)
        if match is not Match.NO_MATCH:
          prefix_match = match
      if prefix_match is Match.IGNORE:
        log.debug('Skipping file [{}]'.format(path))
        return False
    return True

  def _RaiseOnSymlinkLoop(self, full_path):
    """Raise SymlinkLoopError if the given path is a symlink loop."""
    if not os.path.islink(encoding.Encode(full_path, encoding='utf-8')):
      return

    # Does it refer to itself somehow?
    p = os.readlink(full_path)
    targets = set()
    while os.path.islink(p):
      if p in targets:
        raise SymlinkLoopError(
            'The symlink [{}] refers to itself.'.format(full_path))
      targets.add(p)
      p = os.readlink(p)
    # Does it refer to its containing directory?
    p = os.path.dirname(full_path)
    while p and os.path.basename(p):
      if os.path.samefile(p, full_path):
        raise SymlinkLoopError(
            'The symlink [{}] refers to its own containing directory.'.format(
                full_path))
      p = os.path.dirname(p)

  def GetIncludedFiles(self, upload_directory, include_dirs=True):
    """Yields the files in the given directory that this FileChooser includes.

    Args:
      upload_directory: str, the path of the directory to upload.
      include_dirs: bool, whether to include directories

    Yields:
      str, the files and directories that should be uploaded.
    Raises:
      SymlinkLoopError: if there is a symlink referring to its own containing
      dir or itself.
    """
    for dirpath, orig_dirnames, filenames in os.walk(
        six.ensure_str(upload_directory), followlinks=True):
      dirpath = encoding.Decode(dirpath)
      dirnames = [encoding.Decode(dirname) for dirname in orig_dirnames]
      filenames = [encoding.Decode(filename) for filename in filenames]
      if dirpath == upload_directory:
        relpath = ''
      else:
        relpath = os.path.relpath(dirpath, upload_directory)
      for filename in filenames:
        file_relpath = os.path.join(relpath, filename)
        self._RaiseOnSymlinkLoop(os.path.join(dirpath, filename))
        if self.IsIncluded(file_relpath):
          yield file_relpath
      for dirname in dirnames:  # make a copy since we modify the original
        file_relpath = os.path.join(relpath, dirname)
        full_path = os.path.join(dirpath, dirname)
        if self.IsIncluded(file_relpath, is_dir=True):
          self._RaiseOnSymlinkLoop(full_path)
          if include_dirs:
            yield file_relpath
        else:
          # Don't bother recursing into skipped directories
          orig_dirnames.remove(dirname)

  @classmethod
  def FromString(cls, text, recurse=0, dirname=None):
    """Constructs a FileChooser from the given string.

    See `gcloud topic gcloudignore` for details.

    Args:
      text: str, the string (many lines, in the format specified in the
        documentation).
      recurse: int, how many layers of "#!include" directives to respect. 0
        means don't respect the directives, 1 means to respect the directives,
        but *not* in any "#!include"d files, etc.
      dirname: str, the base directory from which to "#!include"

    Raises:
      BadIncludedFileError: if a file being included does not exist or is not
        in the same directory.

    Returns:
      FileChooser.
    """
    patterns = []
    for line in text.splitlines():
      if line.startswith('#'):
        if line[1:].lstrip().startswith(cls._INCLUDE_DIRECTIVE):
          patterns.extend(cls._GetIncludedPatterns(line, dirname, recurse))
        continue  # lines beginning with '#' are comments
      try:
        patterns.append(Pattern.FromString(line))
      except glob.InvalidLineError:
        pass  # Ignore invalid lines
    return cls(patterns)

  @classmethod
  def _GetIncludedPatterns(cls, line, dirname, recurse):
    """Gets the patterns from an '#!include' line.

    Args:
      line: str, the line containing the '#!include' directive
      dirname: str, the name of the base directory from which to include files
      recurse: int, how many layers of "#!include" directives to respect. 0
        means don't respect the directives, 1 means to respect the directives,
        but *not* in any "#!include"d files, etc.

    Returns:
      list of Pattern, the patterns recursively included from the specified
        file.

    Raises:
      ValueError: if dirname is not provided
      BadIncludedFileError: if the file being included does not exist or is not
        in the same directory.
    """
    if not dirname:
      raise ValueError('dirname must be provided in order to include a file.')
    start_idx = line.find(cls._INCLUDE_DIRECTIVE)
    included_file = line[start_idx + len(cls._INCLUDE_DIRECTIVE):]
    if _GCLOUDIGNORE_PATH_SEP in included_file:
      raise BadIncludedFileError(
          'May only include files in the same directory.')
    if not recurse:
      log.info('Not respecting `#!include` directive: [%s].', line)
      return []

    included_path = os.path.join(dirname, included_file)
    try:
      return cls.FromFile(included_path, recurse - 1).patterns
    except BadFileError as err:
      raise BadIncludedFileError(six.text_type(err))

  @classmethod
  def FromFile(cls, ignore_file_path, recurse=1):
    """Constructs a FileChooser from the given file path.

    See `gcloud topic gcloudignore` for details.

    Args:
      ignore_file_path: str, the path to the file in .gcloudignore format.
      recurse: int, how many layers of "#!include" directives to respect. 0
        means don't respect the directives, 1 means to respect the directives,
        but *not* in any "#!include"d files, etc.

    Raises:
      BadIncludedFileError: if the file being included does not exist or is not
        in the same directory.

    Returns:
      FileChooser.
    """
    try:
      text = files.ReadFileContents(ignore_file_path)
    except files.Error as err:
      raise BadFileError(
          'Could not read ignore file [{}]: {}'.format(ignore_file_path, err))
    return cls.FromString(text, dirname=os.path.dirname(ignore_file_path),
                          recurse=recurse)


def AnyFileOrDirExists(directory, names):
  files_to_check = [os.path.join(directory, name) for name in names]
  return any(map(os.path.exists, files_to_check))


def _GitFilesExist(directory):
  return AnyFileOrDirExists(directory, GIT_FILES)


def _GetIgnoreFileContents(default_ignore_file,
                           directory,
                           include_gitignore=True):
  ignore_file_contents = default_ignore_file
  if include_gitignore and os.path.exists(
      os.path.join(directory, '.gitignore')):
    ignore_file_contents += '#!include:.gitignore\n'
  return ignore_file_contents


def GetFileChooserForDir(
    directory, default_ignore_file=DEFAULT_IGNORE_FILE, write_on_disk=True,
    gcloud_ignore_creation_predicate=_GitFilesExist, include_gitignore=True,
    ignore_file=None):
  """Gets the FileChooser object for the given directory.

  In order of preference:
  - If ignore_file is not none, use it to skip files.
    If the specified file does not exist, raise error.
  - Use .gcloudignore file in the top-level directory.
  - Evaluates creation predicate to determine whether to generate .gcloudignore.
    include_gitignore determines whether the generated .gcloudignore will
    include the user's .gitignore if one exists. If the directory is not
    writable, the file chooser corresponding to the ignore file that would have
    been generated is used.
  - If the creation predicate evaluates to false, returned FileChooser
    will choose all files.

  Args:
    directory: str, the path of the top-level directory to upload
    default_ignore_file: str, the ignore file to use if one is not found (and
      the directory has Git files).
    write_on_disk: bool, whether to save the generated gcloudignore to disk.
    gcloud_ignore_creation_predicate: one argument function, indicating if a
      .gcloudignore file should be created. The argument is the path of the
      directory that would contain the .gcloudignore file. By default
      .gcloudignore file will be created if and only if the directory contains
      .gitignore file or .git directory.
    include_gitignore: bool, whether the generated gcloudignore should include
      the user's .gitignore if present.
    ignore_file: custom ignore_file name.
              Override .gcloudignore file to customize files to be skipped.

  Raises:
    BadIncludedFileError: if a file being included does not exist or is not in
      the same directory.

  Returns:
    FileChooser: the FileChooser for the directory. If there is no .gcloudignore
    file and it can't be created the returned FileChooser will choose all files.
  """

  if ignore_file:
    gcloudignore_path = os.path.join(directory, ignore_file)
  else:
    if not properties.VALUES.gcloudignore.enabled.GetBool():
      log.info('Not using a .gcloudignore file since gcloudignore is globally '
               'disabled.')
      return FileChooser([])
    gcloudignore_path = os.path.join(directory, IGNORE_FILE_NAME)
  try:
    chooser = FileChooser.FromFile(gcloudignore_path)
  except BadFileError:
    pass
  else:
    log.info('Using ignore file at [{}].'.format(gcloudignore_path))
    return chooser
  if not gcloud_ignore_creation_predicate(directory):
    log.info('Not using ignore file.')
    return FileChooser([])

  ignore_contents = _GetIgnoreFileContents(default_ignore_file, directory,
                                           include_gitignore)
  log.info('Using default gcloudignore file:\n{0}\n{1}\n{0}'.format(
      '--------------------------------------------------', ignore_contents))
  if write_on_disk:
    try:
      files.WriteFileContents(gcloudignore_path, ignore_contents,
                              overwrite=False)
    except files.Error as err:
      log.info('Could not write .gcloudignore file: {}'.format(err))
    else:
      log.status.Print('Created .gcloudignore file. See `gcloud topic '
                       'gcloudignore` for details.')
  return FileChooser.FromString(ignore_contents, recurse=1, dirname=directory)
