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

"""Utilities for error reporting."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core.util import encoding

PARTITION_TRACEBACK_PATTERN = (
    r'(?P<stacktrace>'
    r'Traceback \(most recent call last\):\n'
    r'(?: {2}File ".*", line \d+, in .+\n {4}.+\n)+'
    r')'
    r'(?P<exception>\S.+)')

FILE_PATH_PATTERN = (
    r' {2}File "(?P<file>.*)google-cloud-sdk.*", line \d+, in .+')


def RemovePrivateInformationFromTraceback(traceback):
  """Given a stacktrace, only include Cloud SDK files in path.

  Args:
    traceback: str, the original unformatted traceback

  Returns:
    str, A new stacktrace with the private paths removed
    None, If traceback does not match traceback pattern
  """
  # Check that traceback follows pattern
  match = re.search(PARTITION_TRACEBACK_PATTERN, traceback)
  if not match:
    return None

  # Separate to individual lines
  stacktrace_list = traceback.splitlines()
  remove_path_stacktrace_list = []

  pattern_file_path = re.compile(FILE_PATH_PATTERN)

  lines_since_match = 0
  for line in stacktrace_list:
    match = pattern_file_path.match(line)
    if match:
      remove_path_stacktrace_list.append(line.replace(match.group('file'), ''))
      lines_since_match = 0
    else:
      lines_since_match += 1
      # This will only be true for the second and subsequent message lines.
      if lines_since_match > 2:
        # Merge second and subsequent message lines into the first line.
        remove_path_stacktrace_list[-1] += line
      else:
        remove_path_stacktrace_list.append(line)

  # Last line will be the exception type followed by message.
  # Remove the message since it could contain PII.
  exception_line = remove_path_stacktrace_list[-1]
  exception_line = encoding.Decode(exception_line).split(':', 1)[0]
  remove_path_stacktrace_list[-1] = exception_line

  formatted_stacktrace = '\n'.join(
      line for line in remove_path_stacktrace_list) + '\n'
  return formatted_stacktrace
