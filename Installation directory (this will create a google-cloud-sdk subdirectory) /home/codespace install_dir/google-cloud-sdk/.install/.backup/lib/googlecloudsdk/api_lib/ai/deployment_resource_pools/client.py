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
"""Utilities for dealing with AI Platform deployment resource pools API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import flags


class DeploymentResourcePoolsClient(object):
  """High-level client for the AI Platform deployment resource pools surface."""

  def __init__(self, client=None, messages=None, version=None):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE

  def CreateBeta(self,
                 location_ref,
                 deployment_resource_pool_id,
                 autoscaling_metric_specs=None,
                 accelerator_dict=None,
                 min_replica_count=None,
                 max_replica_count=None,
                 machine_type=None):
    """Creates a new deployment resource pool using v1beta1 API.

    Args:
      location_ref: Resource, the parsed location to create a deployment
        resource pool.
      deployment_resource_pool_id: str, The ID to use for the
        DeploymentResourcePool, which will become the final component of the
        DeploymentResourcePool's resource name.
      autoscaling_metric_specs: dict or None, the metric specification that
        defines the target resource utilization for calculating the desired
        replica count.
      accelerator_dict: dict or None, the accelerator attached to the deployment
        resource pool from args.
      min_replica_count: int or None, The minimum number of machine replicas
        this deployment resource pool will be always deployed on. This value
        must be greater than or equal to 1.
      max_replica_count: int or None, The maximum number of replicas this
        deployment resource pool may be deployed on when the traffic against it
        increases.
      machine_type: str or None, Immutable. The type of the machine.

    Returns:
      A long-running operation for Create.
    """

    machine_spec = self.messages.GoogleCloudAiplatformV1beta1MachineSpec()
    if machine_type is not None:
      machine_spec.machineType = machine_type
    accelerator = flags.ParseAcceleratorFlag(accelerator_dict,
                                             constants.BETA_VERSION)
    if accelerator is not None:
      machine_spec.acceleratorType = accelerator.acceleratorType
      machine_spec.acceleratorCount = accelerator.acceleratorCount

    dedicated = self.messages.GoogleCloudAiplatformV1beta1DedicatedResources(
        machineSpec=machine_spec)

    dedicated.minReplicaCount = min_replica_count or 1
    if max_replica_count is not None:
      dedicated.maxReplicaCount = max_replica_count

    if autoscaling_metric_specs is not None:
      autoscaling_metric_specs_list = []
      for name, target in sorted(autoscaling_metric_specs.items()):
        autoscaling_metric_specs_list.append(
            self.messages.GoogleCloudAiplatformV1beta1AutoscalingMetricSpec(
                metricName=constants.OP_AUTOSCALING_METRIC_NAME_MAPPER[name],
                target=target))
      dedicated.autoscalingMetricSpecs = autoscaling_metric_specs_list

    pool = self.messages.GoogleCloudAiplatformV1beta1DeploymentResourcePool(
        dedicatedResources=dedicated)
    pool_request = self.messages.GoogleCloudAiplatformV1beta1CreateDeploymentResourcePoolRequest(
        deploymentResourcePool=pool,
        deploymentResourcePoolId=deployment_resource_pool_id)

    req = self.messages.AiplatformProjectsLocationsDeploymentResourcePoolsCreateRequest(
        parent=location_ref.RelativeName(),
        googleCloudAiplatformV1beta1CreateDeploymentResourcePoolRequest=
        pool_request)

    operation = self.client.projects_locations_deploymentResourcePools.Create(
        req)

    return operation

  def DeleteBeta(self, deployment_resource_pool_ref):
    """Deletes a deployment resource pool using v1beta1 API.

    Args:
      deployment_resource_pool_ref: str, The deployment resource pool to delete.

    Returns:
      A GoogleProtobufEmpty response message for delete.
    """

    req = self.messages.AiplatformProjectsLocationsDeploymentResourcePoolsDeleteRequest(
        name=deployment_resource_pool_ref.RelativeName())

    operation = self.client.projects_locations_deploymentResourcePools.Delete(
        req)

    return operation

  def DescribeBeta(self, deployment_resource_pool_ref):
    """Describes a deployment resource pool using v1beta1 API.

    Args:
      deployment_resource_pool_ref: str, Deployment resource pool to describe.

    Returns:
      GoogleCloudAiplatformV1beta1DeploymentResourcePool response message.
    """
    req = self.messages.AiplatformProjectsLocationsDeploymentResourcePoolsGetRequest(
        name=deployment_resource_pool_ref.RelativeName())

    response = self.client.projects_locations_deploymentResourcePools.Get(req)

    return response

  def ListBeta(self, location_ref):
    """Lists deployment resource pools using v1beta1 API.

    Args:
      location_ref: Resource, the parsed location to list deployment
        resource pools.

    Returns:
      Nested attribute containing list of deployment resource pools.
    """
    req = self.messages.AiplatformProjectsLocationsDeploymentResourcePoolsListRequest(
        parent=location_ref.RelativeName())

    return list_pager.YieldFromList(
        self.client.projects_locations_deploymentResourcePools,
        req,
        field='deploymentResourcePools',
        batch_size_attribute='pageSize')

  def QueryDeployedModelsBeta(self, deployment_resource_pool_ref):
    """Queries deployed models sharing a specified deployment resource pool using v1beta1 API.

    Args:
      deployment_resource_pool_ref: str, Deployment resource pool to query.

    Returns:
      GoogleCloudAiplatformV1beta1QueryDeployedModelsResponse message.
    """
    req = self.messages.AiplatformProjectsLocationsDeploymentResourcePoolsQueryDeployedModelsRequest(
        deploymentResourcePool=deployment_resource_pool_ref.RelativeName())

    response = self.client.projects_locations_deploymentResourcePools.QueryDeployedModels(
        req)

    return response
