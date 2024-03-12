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
"""Utils for GEC cluster commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import properties


def SetAdminUsers(messages, args, request):
  """Sets the cluster.authorization.admin_users to the user if unspecified.

  Args:
    messages: message module of edgecontainer cluster.
    args: command line arguments.
    request: API request to be issued
  """

  request.cluster.authorization = messages.Authorization()
  request.cluster.authorization.adminUsers = messages.ClusterUser()
  if flags.FlagIsExplicitlySet(args, 'admin_users'):
    request.cluster.authorization.adminUsers.username = args.admin_users
    return

  if properties.VALUES.auth.credential_file_override.Get() is not None:
    raise gcloud_exceptions.RequiredArgumentException(
        '--admin-users', 'Required if auth/credential_file_override is defined.'
    )

  service_account_override = (
      properties.VALUES.auth.impersonate_service_account.Get()
  )
  if service_account_override is not None:
    request.cluster.authorization.adminUsers.username = service_account_override
  else:
    default_account = properties.VALUES.core.account.Get()
    if default_account is None:
      raise gcloud_exceptions.RequiredArgumentException(
          '--admin-users',
          (
              'Required if no account is active and'
              ' --impersonate-service-account is undefined.'
          ),
      )
    request.cluster.authorization.adminUsers.username = default_account
