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
"""Utilities to support identity pools long-running operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter


class IdentityPoolOperationPoller(waiter.CloudOperationPoller):
  """Manages an identity pool long-running operation."""

  def GetResult(self, operation):
    """Overrides.

    Override the default implementation because Identity Pools
    GetOperation does not return anything in the Operation.response field.

    Args:
      operation: api_name_message.Operation.

    Returns:
      result of result_service.Get request.
    """

    request_type = self.result_service.GetRequestType('Get')
    resource_name = '/'.join(operation.name.split('/')[:-2])
    return self.result_service.Get(request_type(name=resource_name))


class IdentityPoolOperationPollerNoResources(waiter.CloudOperationPoller):
  """Manages an identity pool long-running operation that creates no resources."""

  def GetResult(self, operation):
    """Overrides.

    Override the default implementation because Identity Pools
    GetOperation does not return anything in the Operation.response field.

    Args:
      operation: api_name_message.Operation.

    Returns:
      None
    """

    return None
