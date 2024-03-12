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
"""Common code for operation pooling."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter


def GetRegionalOperationsCollection():
  return 'compute.regionOperations'


def GetGlobalOperationsCollection():
  return 'compute.globalOperations'


def WaitForOperation(resources, service, operation, collection, resource_ref,
                     message):
  """Waits for the operation to finish.

  Args:
    resources: The resource parser.
    service: apitools.base.py.base_api.BaseApiService, the service representing
      the target of the operation.
    operation: The operation to wait for.
    collection: The operations collection.
    resource_ref: The resource reference.
    message: The message to show.

  Returns:
    The operation result.
  """
  params = {'project': resource_ref.project}
  if collection == 'compute.regionOperations':
    params['region'] = resource_ref.region

  operation_ref = resources.Parse(
      operation.name, params=params, collection=collection)
  operation_poller = poller.Poller(service, resource_ref)
  return waiter.WaitFor(operation_poller, operation_ref, message)
