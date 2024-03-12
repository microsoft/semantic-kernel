# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helper functions for executing binaries."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import subprocess

from gslib import exception


def ExecuteExternalCommand(command_and_flags):
  """Runs external terminal command.

  Args:
    command_and_flags (List[str]): Ordered command and flag strings.

  Returns:
    (stdout (str|None), stderr (str|None)) from running command.

  Raises:
    OSError for any issues running the command.
  """
  command_process = subprocess.Popen(command_and_flags,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
  command_stdout, command_stderr = command_process.communicate()

  # Python 3 outputs bytes from communicate() by default.
  if command_stdout is not None and not isinstance(command_stdout, str):
    command_stdout = command_stdout.decode()
  if command_stderr is not None and not isinstance(command_stderr, str):
    command_stderr = command_stderr.decode()

  if command_process.returncode != 0:
    raise exception.ExternalBinaryError(command_stderr)

  return command_stdout, command_stderr
