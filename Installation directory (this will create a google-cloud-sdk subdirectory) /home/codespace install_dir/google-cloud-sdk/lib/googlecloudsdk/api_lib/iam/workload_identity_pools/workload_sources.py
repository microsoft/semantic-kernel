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
"""Commands for interacting with WorkloadSources API that will be used by multiple commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import List, Optional

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.iam import identity_pool_waiter
from googlecloudsdk.core import resources as sdkresources


# TODO(b/301983349): Delete this once other CLs have been submitted.
def CreateGcpWorkloadSource(
    client,
    messages,
    workload_source_id: str,
    resources: Optional[List[str]],
    attached_service_accounts: Optional[List[str]],
    parent: str,
    for_managed_identity: bool = False,
):
  """Make API calls to Create a GCP workload source.

  Args:
    client: the iam v1 client.
    messages: the iam v1 messages.
    workload_source_id: the workload source id to be created.
    resources: the list of resource attribute conditions to be created
    attached_service_accounts: the list of service account attribute conditions
      to be created
    parent: the parent resource name, should be a namespace or a managed
      identity resource
    for_managed_identity: whether to create the workload source under a managed
      identity

  Returns:
    The LRO ref for a create response
  """
  conditions = []
  if resources is not None:
    conditions += [
        messages.WorkloadSourceCondition(attribute='resource', value=resource)
        for resource in resources
    ]
  if attached_service_accounts is not None:
    conditions += [
        messages.WorkloadSourceCondition(
            attribute='attached_service_account', value=account
        )
        for account in attached_service_accounts
    ]
  new_workload_source = messages.WorkloadSource(
      conditionSet=messages.WorkloadSourceConditionSet(conditions=conditions)
  )
  if for_managed_identity:
    return client.projects_locations_workloadIdentityPools_namespaces_managedIdentities_workloadSources.Create(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesManagedIdentitiesWorkloadSourcesCreateRequest(
            parent=parent,
            workloadSource=new_workload_source,
            workloadSourceId=workload_source_id,
        )
    )
  else:
    return client.projects_locations_workloadIdentityPools_namespaces_workloadSources.Create(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesWorkloadSourcesCreateRequest(
            parent=parent,
            workloadSource=new_workload_source,
            workloadSourceId=workload_source_id,
        )
    )


def WaitForWorkloadSourceOperation(
    client,
    lro_ref,
    for_managed_identity: bool = False,
    delete: bool = False,
):
  """Make API calls to poll for a workload source LRO.

  Args:
    client: the iam v1 client.
    lro_ref: the lro ref returned from a LRO workload source API call.
    for_managed_identity: whether the workload source LRO is under a managed
      identity
    delete: whether it's a delete operation

  Returns:
    The result workload source or None for delete
  """
  lro_resource = sdkresources.REGISTRY.ParseRelativeName(
      lro_ref.name,
      collection=(
          'iam.projects.locations.workloadIdentityPools.namespaces.managedIdentities.workloadSources.operations'
          if for_managed_identity
          else 'iam.projects.locations.workloadIdentityPools.namespaces.workloadSources'
      ),
  )
  if delete:
    result = waiter.WaitFor(
        identity_pool_waiter.IdentityPoolOperationPollerNoResources(
            client.projects_locations_workloadIdentityPools_namespaces_workloadSources,
            client.projects_locations_workloadIdentityPools_namespaces_workloadSources_operations,
        ),
        lro_resource,
        'Waiting for operation [{}] to complete'.format(lro_ref.name),
        # Wait for a maximum of 5 minutes, as the IAM replication has a lag of
        # up to 80 seconds.
        max_wait_ms=300000,
    )
  else:
    result = waiter.WaitFor(
        identity_pool_waiter.IdentityPoolOperationPoller(
            client.projects_locations_workloadIdentityPools_namespaces_workloadSources,
            client.projects_locations_workloadIdentityPools_namespaces_workloadSources_operations,
        ),
        lro_resource,
        'Waiting for operation [{}] to complete'.format(lro_ref.name),
        # Wait for a maximum of 5 minutes, as the IAM replication has a lag of
        # up to 80 seconds.
        max_wait_ms=300000,
    )

  return result
