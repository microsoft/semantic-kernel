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
"""API library for access context manager levels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.api_lib.util import waiter

from googlecloudsdk.core import resources


class Client(object):

  def __init__(self, client=None, messages=None, version=None):
    self.client = client or util.GetClient(version=version)
    self.messages = messages or self.client.MESSAGES_MODULE

  def List(self, policy_ref, limit=None):
    req = (
        self.messages.AccesscontextmanagerAccessPoliciesAccessLevelsListRequest(
            parent=policy_ref.RelativeName()
        )
    )
    return list_pager.YieldFromList(
        self.client.accessPolicies_accessLevels,
        req,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=None,
        field='accessLevels',
    )

  def Patch(
      self,
      level_ref,
      description=None,
      title=None,
      basic_level_combine_function=None,
      basic_level_conditions=None,
      custom_level_expr=None,
  ):
    """Patch an access level.

    Args:
      level_ref: resources.Resource, reference to the level to patch
      description: str, description of the level or None if not updating
      title: str, title of the level or None if not updating
      basic_level_combine_function: ZoneTypeValueValuesEnum, combine function
        enum value of the level or None if not updating
      basic_level_conditions: list of Condition, the conditions for a basic
        level or None if not updating
      custom_level_expr: the expression of the Custom level, or none if not
        updating.

    Returns:
      AccessLevel, the updated access level
    """
    level = self.messages.AccessLevel()
    update_mask = []
    if description is not None:
      update_mask.append('description')
      level.description = description
    if title is not None:
      update_mask.append('title')
      level.title = title
    if basic_level_combine_function is not None:
      update_mask.append('basic.combiningFunction')
      level.basic = level.basic or self.messages.BasicLevel()
      level.basic.combiningFunction = basic_level_combine_function
    if basic_level_conditions is not None:
      update_mask.append('basic.conditions')
      level.basic = level.basic or self.messages.BasicLevel()
      level.basic.conditions = basic_level_conditions
    if custom_level_expr is not None:
      update_mask.append('custom')
      level.custom = level.custom or self.messages.CustomLevel()
      level.custom.expr = custom_level_expr
    update_mask.sort()  # For ease-of-testing

    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsPatchRequest
    request = request_type(
        accessLevel=level,
        name=level_ref.RelativeName(),
        updateMask=','.join(update_mask),
    )
    operation = self.client.accessPolicies_accessLevels.Patch(request)

    poller = util.OperationPoller(self.client.accessPolicies_accessLevels,
                                  self.client.operations, level_ref)
    operation_ref = resources.REGISTRY.Parse(
        operation.name, collection='accesscontextmanager.operations')
    return waiter.WaitFor(
        poller, operation_ref,
        'Waiting for PATCH operation [{}]'.format(operation_ref.Name()))
