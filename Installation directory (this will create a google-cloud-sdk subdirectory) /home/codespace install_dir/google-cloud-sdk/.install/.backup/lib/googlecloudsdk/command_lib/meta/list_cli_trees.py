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

"""gcloud CLI tree lister module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.core import module_util
from googlecloudsdk.core.util import files
import six


def _ParameterizePath(path):
  """Return path with $HOME prefix replaced by ~."""
  home = files.GetHomeDir() + os.path.sep
  if path.startswith(home):
    return '~' + os.path.sep + path[len(home):]
  return path


class CliTreeInfo(object):
  """Info for one CLI tree. A list of these is returned by ListAll()."""

  def __init__(self, command, path, version, cli_version, command_installed,
               error):
    self.command = command
    self.path = path
    self.version = version
    self.cli_version = cli_version
    self.command_installed = command_installed
    self.error = error


def ListAll(directory=None):
  """Returns the CliTreeInfo list of all available CLI trees.

  Args:
    directory: The config directory containing the CLI tree modules.

  Raises:
    CliTreeVersionError: loaded tree version mismatch
    ImportModuleError: import errors

  Returns:
    The CLI tree.
  """
  # List all CLIs by searching directories in order. .py, .pyc, and .json
  # files are treated as CLI modules/data, where the file base name is the name
  # of the CLI root command.
  directories = [
      directory,  # Explicit caller override dir
      cli_tree.CliTreeConfigDir(),  # Config dir shared across installations
      cli_tree.CliTreeDir(),  # Installation dir controlled by the updater
  ]

  trees = []
  for directory in directories:
    if not directory or not os.path.exists(directory):
      continue
    for (dirpath, _, filenames) in os.walk(six.text_type(directory)):
      for filename in sorted(filenames):  # For stability across runs.
        base, extension = os.path.splitext(filename)
        if base == '__init__' or '.' in base:
          # Ignore Python droppings and names containing more than one dot.
          continue
        path = os.path.join(dirpath, filename)
        error = ''
        tree = None
        if extension in ('.py', '.pyc'):
          try:
            module = module_util.ImportPath(path)
          except module_util.ImportModuleError as e:
            error = six.text_type(e)
          try:
            tree = module.TREE
          except AttributeError:
            tree = None
        elif extension == '.json':
          try:
            tree = json.loads(files.ReadFileContents(path))
          except Exception as e:  # pylint: disable=broad-except, record all errors
            error = six.text_type(e)
        if tree:
          version = tree.get(cli_tree.LOOKUP_VERSION, 'UNKNOWN')
          cli_version = tree.get(cli_tree.LOOKUP_CLI_VERSION, 'UNKNOWN')
          del tree
        else:
          version = 'UNKNOWN'
          cli_version = 'UNKNOWN'
        trees.append(CliTreeInfo(
            command=base,
            path=_ParameterizePath(path),
            version=version,
            cli_version=cli_version,
            command_installed=bool(files.FindExecutableOnPath(base)),
            error=error))
      # Don't search subdirectories.
      break
  return trees
