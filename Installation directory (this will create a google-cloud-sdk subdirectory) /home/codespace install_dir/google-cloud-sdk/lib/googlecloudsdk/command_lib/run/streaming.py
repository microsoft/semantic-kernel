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
"""Wrapper for log-streaming binary."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.anthos import binary_operations

MISSING_BINARY = ('Could not locate executable log-streaming'
                  ' on the system PATH. '
                  'Please ensure gcloud log-streaming component is properly '
                  'installed. '
                  'See https://cloud.google.com/sdk/docs/components for '
                  'more details.')
# Logs from the binary to be ignored.


class LogStreamingWrapper(binary_operations.StreamingBinaryBackedOperation):
  """Binary operation wrapper for log-streaming commands."""

  def __init__(self, **kwargs):
    super(LogStreamingWrapper, self).__init__(
        binary='log-streaming',
        custom_errors={'MISSING_EXEC': MISSING_BINARY},
        install_if_missing=True,
        **kwargs)

  def _ParseArgsForCommand(self,
                           project_id=None,
                           log_filter=None,
                           log_format=None,
                           **kwargs):
    del kwargs
    exec_args = ['-projectId', project_id]
    if log_filter:
      exec_args.extend(['-filter', log_filter])
    if log_format:
      exec_args.extend(['-format', log_format])
    return exec_args
