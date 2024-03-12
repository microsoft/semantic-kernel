# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for local mode."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import subprocess
import sys

from googlecloudsdk.core.util import files


def ExecuteCommand(cmd, input_str=None, file=None):
  """Executes shell commands in subprocess.

  Executes the supplied command with the supplied standard input string, streams
  the output to stdout, and returns the process's return code.

  Args:
    cmd: (List[str]) Strings to send in as the command.
    input_str: (str) if supplied, it will be passed as stdin to the supplied
      command. if None, stdin will get closed immediately.
    file: optional file-like object (stream), the output from the executed
      process's stdout will get sent to this stream. Defaults to sys.stdout.

  Returns:
    return code of the process
  """
  if file is None:
    file = sys.stdout

  with subprocess.Popen(
      cmd,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      universal_newlines=False,
      bufsize=1) as p:
    if input_str:
      p.stdin.write(input_str.encode('utf-8'))
    p.stdin.close()

    out = io.TextIOWrapper(p.stdout, newline='')

    for line in out:
      file.write(line)
      file.flush()
    else:
      # Flush to force the contents to display.
      file.flush()

  return p.returncode


def ModuleToPath(module_name):
  """Converts the supplied python module into corresponding python file.

  Args:
    module_name: (str) A python module name (separated by dots)

  Returns:
    A string representing a python file path.
  """
  return module_name.replace('.', os.path.sep) + '.py'


def ClearPyCache(root_dir=None):
  """Removes generic `__pycache__` folder and  '*.pyc' '*.pyo' files."""
  root_dir = root_dir or files.GetCWD()

  is_cleaned = False
  for name in os.listdir(root_dir):
    item = os.path.join(root_dir, name)
    if os.path.isdir(item):
      if name == '__pycache__':
        files.RmTree(item)
        is_cleaned = True
    else:
      _, ext = os.path.splitext(name)
      if ext in ['.pyc', '.pyo']:
        os.remove(item)
        is_cleaned = True

  return is_cleaned
