# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Parse workerpool config files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util

# What we call workerpool.yaml for error messages that try to parse it.
_WORKERPOOL_CONFIG_FRIENDLY_NAME = 'workerpool config'


def LoadWorkerpoolConfigFromStream(stream, messages, path=None):
  """Load a workerpool config file into a WorkerPool message.

  Args:
    stream: file-like object containing the JSON or YAML data to be decoded.
    messages: module, The messages module that has a WorkerPool type.
    path: str or None. Optional path to be used in error messages.

  Raises:
    ParserError: If there was a problem parsing the stream as a dict.
    ParseProtoException: If there was a problem interpreting the stream as the
      given message type.

  Returns:
    WorkerPool message, The worker pool that got decoded.
  """
  wp = cloudbuild_util.LoadMessageFromStream(
      stream, messages.WorkerPool, _WORKERPOOL_CONFIG_FRIENDLY_NAME, [], path)
  return wp


def LoadWorkerpoolConfigFromPath(path, messages):
  """Load a workerpool config file into a WorkerPool message.

  Args:
    path: str. Path to the JSON or YAML data to be decoded.
    messages: module, The messages module that has a WorkerPool type.

  Raises:
    files.MissingFileError: If the file does not exist.
    ParserError: If there was a problem parsing the file as a dict.
    ParseProtoException: If there was a problem interpreting the file as the
      given message type.

  Returns:
    WorkerPool message, The worker pool that got decoded.
  """
  wp = cloudbuild_util.LoadMessageFromPath(path, messages.WorkerPool,
                                           _WORKERPOOL_CONFIG_FRIENDLY_NAME)
  return wp

