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

import fnmatch
import os
import re

_GCLOUDIGNORE_PATH_SEP = '/'
_ENDS_IN_ODD_NUMBER_SLASHES_RE = r'(?<!\\)\\(\\\\)*$'


class InternalParserError(Exception):
  """An internal error in gcloudignore parsing."""


class InvalidLineError(InternalParserError):
  """Error indicating that a line of the ignore file was invalid."""


def _HandleSpaces(line):
  """Handles spaces in a line.

  In particular, deals with trailing spaces (which are stripped unless
  escaped) and escaped spaces throughout the line (which are unescaped).

  Args:
    line: str, the line

  Returns:
    str, the line with spaces handled
  """
  def _Rstrip(line):
    """Strips unescaped trailing spaces."""
    # First, make the string into "tokens": a backslash followed by any
    # character is one token; any other character is a token on its own.
    tokens = []
    i = 0
    while i < len(line):
      curr = line[i]
      if curr == '\\':
        if i + 1 >= len(line):
          tokens.append(curr)
          break  # Pass through trailing backslash
        tokens.append(curr + line[i+1])
        i += 2
      else:
        tokens.append(curr)
        i += 1

    # Then, strip the trailing space tokens.
    res = []
    only_seen_spaces = True
    for curr in reversed(tokens):
      if only_seen_spaces and curr == ' ':
        continue
      only_seen_spaces = False
      res.append(curr)

    return ''.join(reversed(res))

  def _UnescapeSpaces(line):
    """Unescapes all spaces in a line."""
    return line.replace('\\ ', ' ')

  return _UnescapeSpaces(_Rstrip(line))


def _Unescape(line):
  r"""Unescapes a line.

  The escape character is '\'. An escaped backslash turns into one backslash;
  any other escaped character is ignored.

  Args:
    line: str, the line to unescape

  Returns:
    str, the unescaped line

  """
  return re.sub(r'\\([^\\])', r'\1', line).replace('\\\\', '\\')


def GetPathPrefixes(path):
  """Returns all prefixes for the given path, inclusive.

  That is, for 'foo/bar/baz', returns ['', 'foo', 'foo/bar', 'foo/bar/baz'].

  Args:
    path: str, the path for which to get prefixes.

  Returns:
    list of str, the prefixes.
  """
  path_prefixes = [path]
  path_reminder = True
  # Apparently which one is empty when operating on top-level directory depends
  # on your configuration.
  while path and path_reminder:
    path, path_reminder = os.path.split(path)
    path_prefixes.insert(0, path)
  return path_prefixes


class Glob(object):
  """A file-matching glob pattern.

  See https://git-scm.com/docs/gitignore for full syntax specification.

  Attributes:
    pattern: str, a globbing pattern.
    must_be_dir: bool, true if only dirs match.
  """

  def __init__(self, pattern, must_be_dir=False):
    self.pattern = pattern
    self.must_be_dir = must_be_dir

  def _MatchesHelper(self, pattern_parts, path):
    """Determines whether the given pattern matches the given path.

    Args:
      pattern_parts: list of str, the list of pattern parts that must all match
        the path.
      path: str, the path to match.

    Returns:
      bool, whether the patch matches the pattern_parts (Matches() will convert
        this into a Match value).
    """
    # This method works right-to-left. It checks that the right-most pattern
    # part matches the right-most path part, and that the remaining pattern
    # matches the remaining path.
    if not pattern_parts:
      # We've reached the end of the pattern! Success.
      return True
    if path is None:
      # Distinguish between '*' and '/*'. The former should match '' (the root
      # directory) but the latter should not.
      return False

    pattern_part = pattern_parts[-1]
    remaining_pattern = pattern_parts[:-1]
    if path:  # normpath turns '' into '.', which confuses fnmatch later
      path = os.path.normpath(path)
    remaining_path, path_part = os.path.split(path)
    if not path_part:
      # See note above.
      remaining_path = None

    if pattern_part == '**':
      # If the path would match the remaining pattern_parts after skipping 0-all
      # of the trailing path parts, the whole pattern matches.
      #
      # That is, if we have `<pattern>/**` as a pattern and `foo/bar` as our
      # path, if any of ``, `foo`, and `foo/bar` match `<pattern>`, we return
      # true.
      path_prefixes = GetPathPrefixes(path)
      # '**' patterns only match against the full path (essentially, they have
      # an implicit '/' at the front of the pattern). An empty string at the
      # beginning of remaining_pattern simulates this.
      #
      # pylint: disable=g-explicit-bool-comparison
      # In this case, it's much clearer to show what we're checking for.
      if not (remaining_pattern and remaining_pattern[0] == ''):
        remaining_pattern.insert(0, '')
      # pylint: enable=g-explicit-bool-comparison
      return any(self._MatchesHelper(remaining_pattern, prefix) for prefix
                 in path_prefixes)

    if pattern_part == '*' and not remaining_pattern:
      # We need to ensure that a '*' at the beginning of a pattern does not
      # match a part with a '/' in it. That should only happen when '**' is
      # used.
      # For example: '*/bar' should match 'foo/bar', but not 'foo/qux/bar'.
      if remaining_path and len(remaining_path) > 1:
        return False

    if not fnmatch.fnmatch(path_part, pattern_part):
      # If the current pattern part doesn't match the current path part, the
      # whole pattern can't match the whole path. Give up!
      return False

    return self._MatchesHelper(remaining_pattern, remaining_path)

  def Matches(self, path, is_dir=False):
    """Returns a Match for this pattern and the given path."""
    if self.must_be_dir and not is_dir:
      return False
    if self._MatchesHelper(self.pattern.split('/'), path):
      return True
    else:
      return False

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
    if line.endswith('/'):
      line = line[:-1]
      must_be_dir = True
    else:
      must_be_dir = False
    line = _HandleSpaces(line)
    if re.search(_ENDS_IN_ODD_NUMBER_SLASHES_RE, line):
      raise InvalidLineError(
          'Line [{}] ends in an odd number of [\\]s.'.format(line))
    line = _Unescape(line)
    if not line:
      raise InvalidLineError('Line [{}] is blank.'.format(line))
    return cls(line, must_be_dir=must_be_dir)
