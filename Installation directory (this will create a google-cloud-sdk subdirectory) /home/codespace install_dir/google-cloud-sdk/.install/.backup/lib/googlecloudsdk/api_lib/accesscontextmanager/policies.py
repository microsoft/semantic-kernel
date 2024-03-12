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
"""API library for access context manager policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.api_lib.util import waiter

from googlecloudsdk.core import resources


class Client(object):
  """Client for Access Context Manager Access Policies service."""

  def __init__(self, client=None, messages=None, version=None):
    self.client = client or util.GetClient(version=version)
    self.messages = messages or self.client.MESSAGES_MODULE

  def List(self, organization_ref, limit=None):
    req = self.messages.AccesscontextmanagerAccessPoliciesListRequest(
        parent=organization_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.accessPolicies, req,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=None,
        field='accessPolicies')

  def Patch(self, policy_ref, title=None):
    """Patch an access policy.

    Args:
      policy_ref: resources.Resource, reference to the policy to patch
      title: str, title of the policy or None if not updating

    Returns:
      AccessPolicy, the updated access policy
    """
    policy = self.messages.AccessPolicy()
    update_mask = []
    if title is not None:
      update_mask.append('title')
      policy.title = title
    update_mask.sort()  # For ease-of-testing

    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesPatchRequest
    request = request_type(
        accessPolicy=policy,
        name=policy_ref.RelativeName(),
        updateMask=','.join(update_mask),
    )
    operation = self.client.accessPolicies.Patch(request)

    poller = waiter.CloudOperationPoller(self.client.accessPolicies,
                                         self.client.operations)
    poller = util.OperationPoller(
        self.client.accessPolicies, self.client.operations, policy_ref)
    operation_ref = resources.REGISTRY.Parse(
        operation.name, collection='accesscontextmanager.operations')
    return waiter.WaitFor(
        poller, operation_ref,
        'Waiting for PATCH operation [{}]'.format(operation_ref.Name()))
