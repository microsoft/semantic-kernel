# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Wrapper to invoke the kuberun golang binary."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk.command_lib.kuberun import messages
from googlecloudsdk.command_lib.util.anthos import binary_operations


def GetEnvArgsForCommand(extra_vars=None, exclude_vars=None):
  """Return an env dict to be passed on command invocation."""
  env = copy.deepcopy(os.environ)
  if extra_vars:
    env.update(extra_vars)
  if exclude_vars:
    for k in exclude_vars:
      env.pop(k)
  return env


class KubeRunStreamingCli(binary_operations.StreamingBinaryBackedOperation):
  """Binary operation wrapper for kuberun commands that require streaming output."""

  def __init__(self, **kwargs):
    custom_errors = {
        'MISSING_EXEC': messages.MISSING_BINARY.format(binary='kuberun')
    }
    super(KubeRunStreamingCli, self).__init__(
        binary='kuberun',
        check_hidden=True,
        custom_errors=custom_errors,
        **kwargs)

  def _ParseArgsForCommand(self, command, **kwargs):
    # TODO(b/168745545) this should return only arguments, however by the time
    # the execution gets here, arguments are parsed and added to 'command' list.
    return command
