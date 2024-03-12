# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utility functions for task execution."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import optimize_parameters_util
from googlecloudsdk.core import properties


def get_first_matching_message_payload(messages, topic):
  """Gets first item with matching topic from list of task output messages."""
  for message in messages:
    if topic is message.topic:
      return message.payload
  return None


def should_use_parallelism():
  """Checks execution settings to determine if parallelism should be used.

  This function is called in some tasks to determine how they are being
  executed, and should include as many of the relevant conditions as possible.

  Returns:
    True if parallel execution should be used, False otherwise.
  """
  process_count = properties.VALUES.storage.process_count.GetInt()
  thread_count = properties.VALUES.storage.thread_count.GetInt()
  if process_count is None or thread_count is None:
    # This can arise if optimize_parameters_util.detect_and_set_best_config has
    # not been called before this method is called. This indicates that the user
    # has not opted out of parallelism.
    return optimize_parameters_util.DEFAULT_TO_PARALLELISM
  return process_count > 1 or thread_count > 1


def require_python_3_5():
  """Task execution assumes Python versions >=3.5.

  Raises:
    InvalidPythonVersionError: if the Python version is not 3.5+.
  """
  if sys.version_info.major < 3 or (sys.version_info.major == 3 and
                                    sys.version_info.minor < 5):
    raise errors.InvalidPythonVersionError(
        'This functionality does not support Python {}.{}.{}. Please upgrade '
        'to Python 3.5 or greater.'.format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        ))
