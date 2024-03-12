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
"""Base client for Eventarc API interaction."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources


class EventarcClientBase(object):
  """Base Client for interaction with of Eventarc API."""

  def __init__(self, api_name, api_version, resource_label):
    client = apis.GetClientInstance(api_name, api_version)
    self._operation_service = client.projects_locations_operations
    self._resource_label = resource_label

  def WaitFor(self, operation, operation_type, resource_ref, loading_msg=''):
    """Waits until the given long-running operation is complete.

    Args:
      operation: the long-running operation to wait for.
      operation_type: str, the type of operation (Creating, Updating or
        Deleting).
      resource_ref: Resource to reference.
      loading_msg: str, the message prompt to the user for a long-running
        operation.

    Returns:
      The long-running operation's response.

    Raises:
      HttpException: when failing to pull the long-running operation's status.
    """
    poller = waiter.CloudOperationPollerNoResources(self._operation_service)
    operation_ref = resources.REGISTRY.Parse(
        operation.name, collection='eventarc.projects.locations.operations')
    resource_name = resource_ref.Name()
    project_name = resource_ref.Parent().Parent().Name()
    location_name = resource_ref.Parent().Name()
    message = ('{} {} [{}] in project [{}], '
               'location [{}]').format(operation_type, self._resource_label,
                                       resource_name, project_name,
                                       location_name)
    if loading_msg:
      message = '{}, {}'.format(message, loading_msg)
    try:
      return waiter.WaitFor(
          poller, operation_ref, message, wait_ceiling_ms=20000
      )
    except apitools_exceptions.HttpForbiddenError as e:
      desc_cmd = 'gcloud eventarc {}s describe {} --location={}'.format(
          self._resource_label, resource_name, location_name)
      error_message = (
          'Failed to poll status of the operation due to {status_message}, but '
          'the operation may have succeeded. Please fix the permission issue, '
          'then either check the %s by running `%s`, or rerun the original '
          'command.') % (self._resource_label, desc_cmd)
      raise exceptions.HttpException(e, error_format=error_message)
