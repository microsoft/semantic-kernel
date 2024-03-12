# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""The edit module allows you to edit a text blob without leaving the shell.

When a user needs to edit a blob of text and you don't want to save to
some location, tell them about it, and have the user re-upload the file, this
module can be used to do a quick inline edit.

It will inspect the environment variable EDITOR to see what tool to use
for editing, defaulting to vi. Then, the EDITOR will be opened in the current
terminal; when it exits, the file will be reread and returned with any edits
that the user may have saved while in the EDITOR.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import subprocess
import tempfile

from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


class Error(Exception):
  """Exceptions for this module."""


class NoSaveException(Error):
  """NoSaveException is thrown when the user did not save the file."""


class EditorException(Error):
  """EditorException is thrown when the editor returns a non-zero exit code."""


def FileModifiedTime(file_name):
  """Enables mocking in the unit test."""
  return os.stat(file_name).st_mtime


def SubprocessCheckCall(*args, **kargs):
  """Enables mocking in the unit test."""
  return subprocess.check_call(*args, **kargs)


def OnlineEdit(text):
  """Edit will edit the provided text.

  Args:
    text: The initial text blob to provide for editing.

  Returns:
    The edited text blob.

  Raises:
    NoSaveException: If the user did not save the temporary file.
    EditorException: If the process running the editor has a
        problem.
  """
  fname = tempfile.NamedTemporaryFile(suffix='.txt').name
  files.WriteFileContents(fname, text)

  # Get the mod time, so we can check if anything was actually done.
  start_mtime = FileModifiedTime(fname)
  if (platforms.OperatingSystem.Current() is
      platforms.OperatingSystem.WINDOWS):
    try:
      SubprocessCheckCall([fname], shell=True)
    except subprocess.CalledProcessError as error:
      raise EditorException('Your editor exited with return code {0}; '
                            'please try again.'.format(error.returncode))
  else:
    try:
      editor = encoding.GetEncodedValue(os.environ, 'EDITOR', 'vi')
      # We use shell=True and manual smashing of the args to permit users to set
      # EDITOR="emacs -nw", or similar things.
      # We used suprocess.check_call instead of subprocess.check_output because
      # subprocess.check_output requires a direct connection to a terminal.
      SubprocessCheckCall('{editor} {file}'.format(
          editor=editor, file=fname), shell=True)
    except subprocess.CalledProcessError as error:
      raise EditorException('Your editor exited with return code {0}; '
                            'please try again. You may set the EDITOR '
                            'environment to use a different text '
                            'editor.'.format(error.returncode))
  end_mtime = FileModifiedTime(fname)
  if start_mtime == end_mtime:
    raise NoSaveException('edit aborted by user')

  return files.ReadFileContents(fname)
