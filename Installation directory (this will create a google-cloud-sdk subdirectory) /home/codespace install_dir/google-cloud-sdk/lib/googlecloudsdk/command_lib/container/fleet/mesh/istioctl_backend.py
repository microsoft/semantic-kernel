# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""istioctl backed gcloud container fleet mesh debug API."""
import copy
import json
import os

from googlecloudsdk.command_lib.anthos.common import messages
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import exceptions as c_except
from googlecloudsdk.core.credentials import store as c_store


def GetEnvArgsForCommand(extra_vars=None, exclude_vars=None):
  """Return an env dict to be passed on command invocation."""
  env = copy.deepcopy(os.environ)
  if extra_vars:
    env.update(extra_vars)
  if exclude_vars:
    for k in exclude_vars:
      env.pop(k)
  return env


def GetAuthToken(account, operation, impersonated=False):
  """Generate a JSON object containing the current gcloud auth token."""
  try:
    access_token = c_store.GetFreshAccessToken(
        account, allow_account_impersonation=impersonated)
    output = {
        'auth_token': access_token,
    }
  except Exception as e:  # pylint: disable=broad-except
    raise c_except.Error(
        'Error retrieving auth credentials for {operation}: {error}. '.format(
            operation=operation, error=e))
  return json.dumps(output, sort_keys=True)


class IstioctlWrapper(binary_operations.StreamingBinaryBackedOperation):
  """`istioctl_backend` wrapper."""

  def __init__(self, **kwargs):
    custom_errors = {
        'MISSING_EXEC': messages.MISSING_BINARY.format(binary='istioctl')
    }
    super(IstioctlWrapper, self).__init__(
        binary='istioctl',
        custom_errors=custom_errors,
        **kwargs
    )

  def _ParseArgsForCommand(self, command, **kwargs):
    if command == 'bug-report':
      return self._ParseBugReportArgs(**kwargs)
    elif command == 'proxy-config':
      return self._ParseProxyConfigArgs(**kwargs)
    elif command == 'proxy-status':
      return self._ParseProxyStatusArgs(**kwargs)

  def _ParseBugReportArgs(self, context, **kwargs):
    del kwargs
    exec_args = ['bug-report', '--context', context]
    return exec_args

  def _ParseProxyConfigArgs(
      self, proxy_config_type, pod_name_namespace, context, **kwargs
  ):
    del kwargs
    exec_args = [
        'proxy-config',
        proxy_config_type,
        pod_name_namespace,
        '--context',
        context,
    ]
    return exec_args

  def _ParseProxyStatusArgs(
      self, context, pod_name, mesh_name, project_number, **kwargs
  ):
    del kwargs
    exec_args = [
        'experimental',
        'proxy-status',
        '--xds-via-agents'
    ]
    if pod_name:
      exec_args.extend([pod_name])
    exec_args.extend(['--context', context])
    if mesh_name:
      exec_args.extend(['--meshName', 'mesh:' + mesh_name])
    if project_number:
      exec_args.extend(['--projectNumber', project_number])
    return exec_args
