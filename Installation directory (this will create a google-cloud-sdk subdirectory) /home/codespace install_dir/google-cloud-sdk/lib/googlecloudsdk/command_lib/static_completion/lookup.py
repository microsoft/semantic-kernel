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

"""Methods for looking up completions from the static CLI tree."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shlex
import sys
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms
import six


LINE_ENV_VAR = 'COMP_LINE'
POINT_ENV_VAR = 'COMP_POINT'
IFS_ENV_VAR = '_ARGCOMPLETE_IFS'
IFS_ENV_DEFAULT = '\013'
COMPLETIONS_OUTPUT_FD = 8

FLAG_PREFIX = '--'

FLAG_BOOLEAN = 'bool'
FLAG_DYNAMIC = 'dynamic'
FLAG_VALUE = 'value'
ENV_VAR = 'env_var'

LOOKUP_COMMANDS = 'commands'
LOOKUP_FLAGS = 'flags'

_EMPTY_STRING = ''
_VALUE_SEP = '='
_SPACE = ' '


class CannotHandleCompletionError(Exception):
  """Error for when completions cannot be handled."""
  pass


def _GetCmdLineFromEnv():
  """Gets the command line from the environment.

  Returns:
    str, Command line.
  """
  cmd_line = encoding.GetEncodedValue(os.environ, LINE_ENV_VAR)
  completion_point = int(encoding.GetEncodedValue(os.environ, POINT_ENV_VAR))
  cmd_line = cmd_line[:completion_point]
  return cmd_line


def _GetCmdWordQueue(cmd_line):
  """Converts the given cmd_line to a queue of command line words.

  Args:
    cmd_line: str, full command line before parsing.

  Returns:
    [str], Queue of command line words.
  """
  cmd_words = shlex.split(cmd_line)[1:]  # First word should always be 'gcloud'

  # We need to know if last word was empty. Shlex removes trailing whitespaces.
  if cmd_line[-1] == _SPACE:
    cmd_words.append(_EMPTY_STRING)

  # Reverse so we can use as a queue
  cmd_words.reverse()
  return cmd_words


def GetEnvVarPrefix():
  # TODO(b/207384119) support powershell environment variables
  return '%' if platforms.OperatingSystem.IsWindows() else '$'


def MatchEnvVars(word, env_vars):
  """Returns environment variables beginning with `word`.

  Args:
    word: The word that is being compared to environment variables.
    env_vars: The list of environment variables.

  Returns:
    []: No completions.
    [completions]: List, all possible sorted completions.
  """
  completions = []
  prefix = word[1:]  # exclude '$' or '%' and only use the variable name
  for child in env_vars:
    if child.startswith(prefix):
      if platforms.OperatingSystem.IsWindows():
        completions.append('%' + child + '%')
      else:
        completions.append('$' + child)
  return completions


def _FindCompletions(root, cmd_line):
  """Try to perform a completion based on the static CLI tree.

  Args:
    root: The root of the tree that will be traversed to find completions.
    cmd_line: [str], original command line.

  Raises:
    CannotHandleCompletionError: If FindCompletions cannot handle completion.

  Returns:
    []: No completions.
    [completions]: List, all possible sorted completions.
  """
  words = _GetCmdWordQueue(cmd_line)
  node = root

  global_flags = node[LOOKUP_FLAGS]

  completions = []
  flag_mode = FLAG_BOOLEAN

  env_var_prefix = GetEnvVarPrefix()
  env_vars = os.environ
  while words:
    word = words.pop()

    if word.startswith(FLAG_PREFIX):
      is_flag_word = True
      child_nodes = node.get(LOOKUP_FLAGS, {})
      child_nodes.update(global_flags)
      # Add the value part back to the queue if it exists
      if _VALUE_SEP in word:
        word, flag_value = word.split(_VALUE_SEP, 1)
        # This predates the env var completion but is necessary for completing
        # environment variables that are flag values.
        words.append(flag_value)
    elif word.startswith(env_var_prefix):
      is_flag_word = False
      child_nodes = env_vars
      flag_mode = ENV_VAR
    else:
      is_flag_word = False
      child_nodes = node.get(LOOKUP_COMMANDS, {})

    # Consume word
    if words:
      if word in child_nodes:
        if is_flag_word:
          flag_mode = child_nodes[word]
        else:
          flag_mode = FLAG_BOOLEAN
          node = child_nodes[word]  # Progress to next command node
      elif flag_mode == ENV_VAR:
        continue
      elif flag_mode != FLAG_BOOLEAN:
        flag_mode = FLAG_BOOLEAN
        continue  # Just consume if we are expecting a flag value
      elif not is_flag_word and not node.get(LOOKUP_COMMANDS):
        # If we're at a leaf command node, this could be a positional arg, so
        # consume it and move on.
        flag_mode = FLAG_BOOLEAN
        continue
      else:
        return []  # Non-existing command/flag, so nothing to do

    # Complete word
    else:
      if flag_mode == FLAG_DYNAMIC:
        raise CannotHandleCompletionError(
            'Dynamic completions are not handled by this module')
      elif flag_mode == FLAG_VALUE:
        return []  # Cannot complete, so nothing to do
      elif flag_mode == ENV_VAR:
        completions += MatchEnvVars(word, child_nodes)
      elif flag_mode != FLAG_BOOLEAN:  # Must be list of choices
        for value in flag_mode:
          if value.startswith(word):
            completions.append(value)
      elif not child_nodes:
        raise CannotHandleCompletionError(
            'Positional completions are not handled by this module')
      else:  # Command/flag completion
        for child, value in six.iteritems(child_nodes):
          if not child.startswith(word):
            continue
          if is_flag_word and value != FLAG_BOOLEAN:
            child += _VALUE_SEP
          completions.append(child)
  return sorted(completions)


def _GetInstallationRootDir():
  """Returns the SDK installation root dir."""
  # Intentionally ignoring config path abstraction imports.
  return os.path.sep.join(__file__.split(os.path.sep)[:-5])


def _GetCompletionCliTreeDir():
  """Returns the SDK static completion CLI tree dir."""
  # Intentionally ignoring config path abstraction imports.
  return os.path.join(_GetInstallationRootDir(), 'data', 'cli')


def CompletionCliTreePath(directory=None):
  """Returns the SDK static completion CLI tree path."""
  # Intentionally ignoring config path abstraction imports.
  return os.path.join(
      directory or _GetCompletionCliTreeDir(), 'gcloud_completions.py')


def LoadCompletionCliTree():
  """Loads and returns the static completion CLI tree."""
  try:
    sys_path = sys.path[:]
    sys.path.append(_GetCompletionCliTreeDir())
    import gcloud_completions  # pylint: disable=g-import-not-at-top
    tree = gcloud_completions.STATIC_COMPLETION_CLI_TREE
  except ImportError:
    raise CannotHandleCompletionError(
        'Cannot find static completion CLI tree module.')
  finally:
    sys.path = sys_path
  return tree


def _OpenCompletionsOutputStream():
  """Returns the completions output stream."""
  return os.fdopen(COMPLETIONS_OUTPUT_FD, 'wb')


def _GetCompletions():
  """Returns the static completions, None if there are none."""
  root = LoadCompletionCliTree()
  cmd_line = _GetCmdLineFromEnv()
  return _FindCompletions(root, cmd_line)


def Complete():
  """Attempts completions and writes them to the completion stream."""
  completions = _GetCompletions()
  if completions:
    # The bash/zsh completion scripts set IFS_ENV_VAR to one character.
    ifs = encoding.GetEncodedValue(os.environ, IFS_ENV_VAR, IFS_ENV_DEFAULT)
    # Write completions to stream
    f = None
    try:
      f = _OpenCompletionsOutputStream()
      # the other side also uses the console encoding
      f.write(ifs.join(completions).encode())
    finally:
      if f:
        f.close()
