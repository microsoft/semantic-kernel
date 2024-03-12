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
"""Helpers for interacting with the IAM API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util as iam_api
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log


def AddIamPolicyBindings(resource, members, role):
  """Adds IAM policy bindings for members with the role on resource."""
  iam_client, iam_messages = iam_api.GetClientAndMessages()

  request = iam_messages.IamProjectsServiceAccountsGetIamPolicyRequest(
      resource=resource)
  iam_policy = iam_client.projects_serviceAccounts.GetIamPolicy(request=request)

  binding_updated = False
  for member in members:
    binding_updated |= iam_util.AddBindingToIamPolicy(iam_messages.Binding,
                                                      iam_policy, member, role)

  if not binding_updated:
    log.debug('Skipped setting IAM policy, no changes are needed.')
    return

  log.debug('Setting the updated IAM policy.')
  set_request = iam_messages.IamProjectsServiceAccountsSetIamPolicyRequest(
      resource=resource,
      setIamPolicyRequest=iam_messages.SetIamPolicyRequest(policy=iam_policy))
  iam_policy = iam_client.projects_serviceAccounts.SetIamPolicy(
      request=set_request)
