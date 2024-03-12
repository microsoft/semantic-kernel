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

"""Utilities for configuring platform specific installation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import shutil
import sys

from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

import six

_DEFAULT_SHELL = 'bash'
# Shells supported by this module.
_SUPPORTED_SHELLS = [_DEFAULT_SHELL, 'zsh', 'ksh', 'fish']
# Map of *.{shell}.inc compatible shells. e.g. ksh can source *.bash.inc.
_COMPATIBLE_INC_SHELL = {'ksh': 'bash'}


def _TraceAction(action):
  """Prints action to standard error."""
  print(action, file=sys.stderr)


# pylint:disable=unused-argument
def _UpdatePathForWindows(bin_path):
  """Update the Windows system path to include bin_path.

  Args:
    bin_path: str, The absolute path to the directory that will contain
        Cloud SDK binaries.
  """

  # pylint:disable=g-import-not-at-top, we want to only attempt these imports
  # on windows.
  try:
    import win32con
    import win32gui
    from six.moves import winreg
  except ImportError:
    _TraceAction("""\
The installer is unable to automatically update your system PATH. Please add
  {path}
to your system PATH to enable easy use of the Cloud SDK Command Line Tools.
""".format(path=bin_path))
    return

  def GetEnv(name):
    root = winreg.HKEY_CURRENT_USER
    subkey = 'Environment'
    key = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ)
    try:
      value, _ = winreg.QueryValueEx(key, name)
    # pylint:disable=undefined-variable, This variable is defined in windows.
    except WindowsError:
      return ''
    return value

  def SetEnv(name, value):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0,
                         winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
    winreg.CloseKey(key)
    win32gui.SendMessage(
        win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')
    return value

  def Remove(paths, value):
    while value in paths:
      paths.remove(value)

  def PrependEnv(name, values):
    paths = GetEnv(name).split(';')
    for value in values:
      if value in paths:
        Remove(paths, value)
      paths.insert(0, value)
    SetEnv(name, ';'.join(paths))

  PrependEnv('Path', [bin_path])

  _TraceAction("""\
The following directory has been added to your PATH.
  {bin_path}

Create a new command shell for the changes to take effect.
""".format(bin_path=bin_path))


_INJECT_SH = """
{comment}
if [ -f '{rc_path}' ]; then . '{rc_path}'; fi
"""


_INJECT_FISH = """
{comment}
if [ -f '{rc_path}' ]; . '{rc_path}'; end
"""


def _GetRcContents(comment, rc_path, rc_contents, shell, pattern=None):
  """Generates the RC file contents with new comment and `source rc_path` lines.

  Args:
    comment: The shell comment string that precedes the source line.
    rc_path: The path of the rc file to source.
    rc_contents: The current contents.
    shell: The shell base name, specific to this module.
    pattern: A regex pattern that matches comment, None for exact match on
      comment.

  Returns:
    The comment and `source rc_path` lines to be inserted into a shell rc file.
  """
  if not pattern:
    pattern = re.escape(comment)
  # This pattern handles all three variants that we have injected in user RC
  # files. All have the same sentinel comment line followed by:
  #   1. a single 'source ...' line
  #   2. a 3 line if-fi (a bug because this pattern was previously incorrect)
  #   3. finally a single if-fi line.
  # If you touch this code ONLY INJECT ONE LINE AFTER THE SENTINEL COMMENT LINE.
  #
  # At some point we can drop the alternate patterns and only search for the
  # sentinel comment line and assume the next line is ours too (that was the
  # original intent before the 3-line form was added).
  subre = re.compile('\n' + pattern + '\n('
                     "source '.*'"
                     '|'
                     'if .*; then\n  source .*\nfi'
                     '|'
                     'if .*; then (\\.|source) .*; fi'
                     '|'
                     'if .*; (\\.|source) .*; end'
                     '|'
                     'if .*; if type source .*; end'
                     ')\n', re.MULTILINE)
  # script checks that the rc_path currently exists before sourcing the file
  inject = _INJECT_FISH if shell == 'fish' else _INJECT_SH
  line = inject.format(comment=comment, rc_path=rc_path)
  filtered_contents = subre.sub('', rc_contents)
  rc_contents = '{filtered_contents}{line}'.format(
      filtered_contents=filtered_contents, line=line)
  return rc_contents


class _RcUpdater(object):
  """Updates the RC file completion and PATH code injection."""

  def __init__(self, completion_update, path_update, shell, rc_path, sdk_root):
    self.completion_update = completion_update
    self.path_update = path_update
    self.rc_path = rc_path
    compatible_shell = _COMPATIBLE_INC_SHELL.get(shell, shell)
    self.completion = os.path.join(
        sdk_root, 'completion.{shell}.inc'.format(shell=compatible_shell))
    self.path = os.path.join(
        sdk_root, 'path.{shell}.inc'.format(shell=compatible_shell))
    self.shell = shell

  def _CompletionExists(self):
    return os.path.exists(self.completion)

  def Update(self):
    """Creates or updates the RC file."""
    if self.rc_path:

      # Check whether RC file is a file and store its contents.
      if os.path.isfile(self.rc_path):
        rc_contents = files.ReadFileContents(self.rc_path)
        original_rc_contents = rc_contents
      elif os.path.exists(self.rc_path):
        _TraceAction(
            '[{rc_path}] exists and is not a file, so it cannot be updated.'
            .format(rc_path=self.rc_path))
        return
      else:
        rc_contents = ''
        original_rc_contents = ''

      if self.path_update:
        rc_contents = _GetRcContents(
            '# The next line updates PATH for the Google Cloud SDK.',
            self.path, rc_contents, self.shell)

      # gcloud doesn't (yet?) support completion for Fish, so check whether the
      # completion file exists
      if self.completion_update and self._CompletionExists():
        rc_contents = _GetRcContents(
            '# The next line enables shell command completion for gcloud.',
            self.completion, rc_contents, self.shell,
            pattern=('# The next line enables [a-z][a-z]*'
                     ' command completion for gcloud.'))

      if rc_contents == original_rc_contents:
        _TraceAction('No changes necessary for [{rc}].'.format(rc=self.rc_path))
        return

      if os.path.exists(self.rc_path):
        rc_backup = self.rc_path + '.backup'
        _TraceAction('Backing up [{rc}] to [{backup}].'.format(
            rc=self.rc_path, backup=rc_backup))
        shutil.copyfile(self.rc_path, rc_backup)

      # Update rc file, creating it if it does not exist.
      rc_dir = os.path.dirname(self.rc_path)
      try:
        files.MakeDir(rc_dir)
      except (files.Error, IOError, OSError):
        _TraceAction(
            'Could not create directories for [{rc_path}], so it '
            'cannot be updated.'.format(rc_path=self.rc_path))
        return

      try:
        files.WriteFileContents(self.rc_path, rc_contents)
      except (files.Error, IOError, OSError):
        _TraceAction(
            'Could not update [{rc_path}]. Ensure you have write access to '
            'this location.'.format(rc_path=self.rc_path))
        return

      _TraceAction('[{rc_path}] has been updated.'.format(rc_path=self.rc_path))
      _TraceAction(console_io.FormatRequiredUserAction(
          'Start a new shell for the changes to take effect.'))

    screen_reader = properties.VALUES.accessibility.screen_reader.GetBool()
    prefix = '' if screen_reader else '==> '

    if not self.completion_update and self._CompletionExists():
      _TraceAction(prefix +
                   'Source [{rc}] in your profile to enable shell command '
                   'completion for gcloud.'.format(rc=self.completion))

    if not self.path_update:
      _TraceAction(prefix +
                   'Source [{rc}] in your profile to add the Google Cloud SDK '
                   'command line tools to your $PATH.'.format(rc=self.path))


def _GetPreferredShell(path, default=_DEFAULT_SHELL):
  """Returns the preferred shell name based on the base file name in path.

  Args:
    path: str, The file path to check.
    default: str, The default value to return if a preferred name cannot be
      determined.

  Returns:
    The preferred user shell name or default if none can be determined.
  """
  if not path:
    return default
  name = os.path.basename(path)
  for shell in _SUPPORTED_SHELLS:
    if shell in six.text_type(name):
      return shell
  return default


def _GetShellRcFileName(shell, host_os):
  """Returns the RC file name for shell and host_os.

  Args:
    shell: str, The shell base name.
    host_os: str, The host os identification string.

  Returns:
    The shell RC file name, '.bashrc' by default.
  """
  if shell == 'ksh':
    return encoding.GetEncodedValue(os.environ, 'ENV', None) or '.kshrc'
  elif shell == 'fish':
    return os.path.join('.config', 'fish', 'config.fish')
  elif shell != 'bash':
    return '.{shell}rc'.format(shell=shell)
  elif host_os == platforms.OperatingSystem.LINUX:
    return '.bashrc'
  elif host_os == platforms.OperatingSystem.MACOSX:
    return '.bash_profile'
  elif host_os == platforms.OperatingSystem.MSYS:
    return '.profile'
  return '.bashrc'


def _GetAndUpdateRcPath(completion_update, path_update, rc_path, host_os):
  """Returns an rc path based on the default rc path or user input.

  Gets default rc path based on environment. If prompts are enabled,
  allows user to update to preferred file path. Otherwise, prints a warning
  that the default rc path will be updated.

  Args:
    completion_update: bool, Whether or not to do command completion.
    path_update: bool, Whether or not to update PATH.
    rc_path: str, the rc path given by the user, from --rc-path arg.
    host_os: str, The host os identification string.

  Returns:
    str, A path to the rc file to update.
  """
  # If we aren't updating the RC file for either completions or PATH, there's
  # no point.
  if not (completion_update or path_update):
    return None
  if rc_path:
    return rc_path
  # A first guess at user preferred shell.
  preferred_shell = _GetPreferredShell(
      encoding.GetEncodedValue(os.environ, 'SHELL', '/bin/sh'))
  default_rc_path = os.path.join(
      files.GetHomeDir(), _GetShellRcFileName(preferred_shell, host_os))
  # If in quiet mode, we'll use default path.
  if not console_io.CanPrompt():
    _TraceAction('You specified that you wanted to update your rc file. The '
                 'default file will be updated: [{rc_path}]'
                 .format(rc_path=default_rc_path))
    return default_rc_path
  rc_path_update = console_io.PromptResponse((
      'The Google Cloud SDK installer will now prompt you to update an rc '
      'file to bring the Google Cloud CLIs into your environment.\n\n'
      'Enter a path to an rc file to update, or leave blank to use '
      '[{rc_path}]:  ').format(rc_path=default_rc_path))
  return (files.ExpandHomeDir(rc_path_update) if rc_path_update
          else default_rc_path)


def _GetRcUpdater(completion_update, path_update, rc_path, sdk_root, host_os):
  """Returns an _RcUpdater object for the preferred user shell.

  Args:
    completion_update: bool, Whether or not to do command completion.
    path_update: bool, Whether or not to update PATH.
    rc_path: str, The path to the rc file to update. If None, ask.
    sdk_root: str, The path to the Cloud SDK root.
    host_os: str, The host os identification string.

  Returns:
    An _RcUpdater() object for the preferred user shell.
  """
  rc_path = _GetAndUpdateRcPath(completion_update, path_update, rc_path,
                                host_os)
  # Check the rc_path for a better hint at the user preferred shell.
  preferred_shell = _GetPreferredShell(
      rc_path,
      default=_GetPreferredShell(
          encoding.GetEncodedValue(os.environ, 'SHELL', '/bin/sh')))
  return _RcUpdater(
      completion_update, path_update, preferred_shell, rc_path, sdk_root)


_PATH_PROMPT = 'update your $PATH'
_COMPLETION_PROMPT = 'enable shell command completion'


def _PromptToUpdate(path_update, completion_update):
  """Prompt the user to update path or command completion if unspecified.

  Args:
    path_update: bool, Value of the --update-path arg.
    completion_update: bool, Value of the --command-completion arg.

  Returns:
    (path_update, completion_update) (bool, bool) Whether to update path and
        enable completion, respectively, after prompting the user.
  """
  # If both were specified, no need to prompt.
  if path_update is not None and completion_update is not None:
    return path_update, completion_update

  # Ask the user only one question to see if they want to do any unspecified
  # updates.
  actions = []
  if path_update is None:
    actions.append(_PATH_PROMPT)
  if completion_update is None:
    actions.append(_COMPLETION_PROMPT)
  prompt = '\nModify profile to {}?'.format(' and '.join(actions))
  response = console_io.PromptContinue(prompt)

  # Update unspecified values to equal user response.
  path_update = response if path_update is None else path_update
  completion_update = (response if completion_update is None
                       else completion_update)

  return path_update, completion_update


def UpdateRC(completion_update, path_update, rc_path, bin_path, sdk_root):
  """Update the system path to include bin_path.

  Args:
    completion_update: bool, Whether or not to do command completion. From
      --command-completion arg during install. If None, ask.
    path_update: bool, Whether or not to update PATH. From --path-update arg
      during install. If None, ask.
    rc_path: str, The path to the rc file to update. From --rc-path during
      install. If None, ask.
    bin_path: str, The absolute path to the directory that will contain
      Cloud SDK binaries.
    sdk_root: str, The path to the Cloud SDK root.
  """
  host_os = platforms.OperatingSystem.Current()
  if host_os == platforms.OperatingSystem.WINDOWS:
    if path_update is None:
      path_update = console_io.PromptContinue(
          prompt_string='Update %PATH% to include Cloud SDK binaries?')
    if path_update:
      _UpdatePathForWindows(bin_path)
    return

  if console_io.CanPrompt():
    path_update, completion_update = _PromptToUpdate(path_update,
                                                     completion_update)
  elif rc_path and (path_update is None and completion_update is None):
    # In quiet mode, if the user gave a path to the RC and didn't specify what
    # updates are desired, assume both.
    path_update = True
    completion_update = True
    _TraceAction('Profile will be modified to {} and {}.'
                 .format(_PATH_PROMPT, _COMPLETION_PROMPT))

  _GetRcUpdater(
      completion_update, path_update, rc_path, sdk_root, host_os).Update()
