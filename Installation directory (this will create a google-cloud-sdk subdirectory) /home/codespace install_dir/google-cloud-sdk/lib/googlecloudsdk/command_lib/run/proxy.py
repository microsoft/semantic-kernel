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
"""Wrapper for cloud-run-proxy binary."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import log

MISSING_BINARY = ('Could not locate Cloud Run executable cloud-run-proxy'
                  ' on the system PATH. '
                  'Please ensure gcloud cloud-run-proxy component is properly '
                  'installed. '
                  'See https://cloud.google.com/sdk/docs/components for '
                  'more details.')
# Logs from the binary to be ignored.
IGNORED_LOGS = [' shutting down.', ' proxies to ']


class ProxyWrapper(binary_operations.StreamingBinaryBackedOperation):
  """Binary operation wrapper for cloud-run-proxy commands."""

  def __init__(self, **kwargs):
    super(ProxyWrapper, self).__init__(
        binary='cloud-run-proxy',
        custom_errors={'MISSING_EXEC': MISSING_BINARY},
        install_if_missing=True,
        std_err_func=StreamErrHandler,
        **kwargs)

  # Function required by StreamingBinaryBackedOperation to map command line args
  # from gcloud to the underlying component.
  def _ParseArgsForCommand(self,
                           host,
                           token=None,
                           bind=None,
                           duration=None,
                           **kwargs):
    del kwargs  # Not used here
    exec_args = ['-host', host]
    if token:
      exec_args.extend(['-token', token])
    if bind:
      exec_args.extend(['-bind', bind])
    if duration:
      exec_args.extend(['-server-up-time', duration])

    return exec_args


def StreamErrHandler(result_holder, capture_output=False):
  """Customized processing for streaming stderr from subprocess."""

  del result_holder, capture_output  # Unused

  def HandleStdErr(line):
    if line:
      for to_be_ignored in IGNORED_LOGS:
        if to_be_ignored in line:
          return
      log.status.Print(line)
      # Check if it is bind used error
      if 'server error:' in line and 'bind: address already in use' in line:
        log.status.Print(
            'You can set the --port flag to specify a different local port')

  return HandleStdErr
