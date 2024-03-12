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
"""Utilities Anthos GKE On-Prem resource operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Generator

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages

MAX_LRO_POLL_INTERVAL_MS = 10000  # 10 seconds

MAX_LRO_WAIT_MS = 7200000  # 2 hours


class OperationsClient(client.ClientBase):
  """Client for operations in Anthos GKE On-Prem API resources."""

  def __init__(self, **kwargs):
    super(OperationsClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_operations

  def Wait(
      self, operation=None, operation_ref=None, timeout=None
  ) -> messages.Operation:
    """Waits for an LRO to complete.

    Args:
      operation: object, operation to wait for.
      operation_ref: operation resource argument reference.
      timeout: int, time in seconds to wait for the operation to complete.

    Returns:
      A completed long-running operation.
    """
    if operation:
      operation_ref = resources.REGISTRY.ParseRelativeName(
          operation.name,
          collection='gkeonprem.projects.locations.operations',
      )

    max_wait_ms = timeout * 1000 if timeout is not None else MAX_LRO_WAIT_MS
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(self._service),
        operation_ref,
        'Waiting for operation [{}] to complete'.format(
            operation_ref.RelativeName()
        ),
        wait_ceiling_ms=MAX_LRO_POLL_INTERVAL_MS,
        max_wait_ms=max_wait_ms,
    )

  def List(
      self, args: parser_extensions.Namespace
  ) -> Generator[messages.Operation, None, None]:
    """List operations."""
    list_req = messages.GkeonpremProjectsLocationsOperationsListRequest(
        name=self._location_name(args)
    )
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='operations',
        batch_size=flags.Get(args, 'page_size'),
        limit=flags.Get(args, 'limit'),
        batch_size_attribute='pageSize',
    )


def log_enroll(resource_ref, is_async=False):
  log.Print(
      log_operation(resource_ref, 'Enroll', 'Enrolled', is_async=is_async)
  )


def log_unenroll(resource_ref, is_async=False):
  log.Print(
      log_operation(resource_ref, 'Unenroll', 'Unenrolled', is_async=is_async)
  )


def log_operation(resource_ref, action, past_tense, is_async=False):
  """Logs the long running operation of a resource.

  Args:
    resource_ref: A resource argument.
    action: str, present tense of the operation.
    past_tense: str, past tense of the operation.
    is_async: bool, if async operation is enabled.

  Returns:
    A string that logs the operation status.
  """
  resource_collection = resource_ref.Collection()
  resource_type = resource_collection.split('.')[-1]

  resource_type_to_name = {
      'vmwareClusters': 'user cluster in Anthos on VMware',
      'vmwareNodePools': 'node pool of a user cluster in Anthos on VMware',
      'vmwareAdminClusters': 'admin cluster in Anthos on VMware',
      'bareMetalClusters': 'user cluster in Anthos on bare metal',
      'bareMetalNodePools': (
          'node pool of a user cluster in Anthos on bare metal'
      ),
      'bareMetalAdminClusters': 'admin cluster in Anthos on bare metal',
      'bareMetalStandaloneClusters': (
          'standalone cluster in Anthos on bare metal'
      ),
      'bareMetalStandaloneNodePools': (
          'node pool of a standalone cluster in Anthos on bare metal'
      ),
  }
  resource_name = resource_type_to_name.get(resource_type, 'unknown resource')
  self_link = resource_ref.SelfLink()

  if is_async:
    return '{action} in progress for {resource_name} [{self_link}].'.format(
        action=action,
        resource_name=resource_name,
        self_link=self_link,
    )

  else:
    return '{past_tense} {resource_name} [{self_link}].'.format(
        past_tense=past_tense,
        resource_name=resource_name,
        self_link=self_link,
    )
