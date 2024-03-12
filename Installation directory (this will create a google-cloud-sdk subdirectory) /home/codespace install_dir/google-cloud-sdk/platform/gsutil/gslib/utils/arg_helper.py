# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Contains helper for parsing command arguments and options."""

import getopt
import sys

from gslib.exception import CommandException


def GetArgumentsAndOptions():
  """Gets the list of arguments and options from the command input.

  Returns:
    The return value consists of two elements: the first is a list of (option,
    value) pairs; the second is the list of program arguments left after the
    option list was stripped (this is a trailing slice of the first argument).
  """
  try:
    return getopt.getopt(sys.argv[1:], 'dDvo:?h:i:u:mq', [
        'debug', 'detailedDebug', 'version', 'option', 'help', 'header',
        'impersonate-service-account=', 'multithreaded', 'quiet',
        'testexceptiontraces', 'trace-token=', 'perf-trace-token='
    ])
  except getopt.GetoptError as e:
    raise CommandException(e.msg)
