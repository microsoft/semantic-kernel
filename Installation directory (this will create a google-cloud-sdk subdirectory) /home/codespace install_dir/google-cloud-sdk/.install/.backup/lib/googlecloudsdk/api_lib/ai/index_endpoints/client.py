# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for dealing with AI Platform index endpoints API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _ParseIndex(index_id, location_id):
  """Parses a index ID into a index resource object."""
  return resources.REGISTRY.Parse(
      index_id,
      params={
          'locationsId': location_id,
          'projectsId': properties.VALUES.core.project.GetOrFail
      },
      collection='aiplatform.projects.locations.indexes')


class IndexEndpointsClient(object):
  """High-level client for the AI Platform index endpoints surface."""

  def __init__(self, client=None, messages=None, version=constants.GA_VERSION):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_indexEndpoints

  def CreateBeta(self, location_ref, args):
    """Create a new index endpoint."""
    labels = labels_util.ParseCreateArgs(
        args,
        self.messages.GoogleCloudAiplatformV1beta1IndexEndpoint.LabelsValue)

    encryption_spec = None
    if args.encryption_kms_key_name is not None:
      encryption_spec = (
          self.messages.GoogleCloudAiplatformV1beta1EncryptionSpec(
              kmsKeyName=args.encryption_kms_key_name))

    private_service_connect_config = None
    if args.enable_private_service_connect:
      private_service_connect_config = (
          self.messages.GoogleCloudAiplatformV1beta1PrivateServiceConnectConfig(
              enablePrivateServiceConnect=args.enable_private_service_connect,
              projectAllowlist=(args.project_allowlist
                                if args.project_allowlist else [])
          )
      )

      req = self.messages.AiplatformProjectsLocationsIndexEndpointsCreateRequest(
          parent=location_ref.RelativeName(),
          googleCloudAiplatformV1beta1IndexEndpoint=self.messages.GoogleCloudAiplatformV1beta1IndexEndpoint(
              displayName=args.display_name,
              description=args.description,
              publicEndpointEnabled=args.public_endpoint_enabled,
              labels=labels,
              encryptionSpec=encryption_spec,
              privateServiceConnectConfig=private_service_connect_config,
          ),
      )
    elif args.network is not None:
      req = self.messages.AiplatformProjectsLocationsIndexEndpointsCreateRequest(
          parent=location_ref.RelativeName(),
          googleCloudAiplatformV1beta1IndexEndpoint=self.messages.GoogleCloudAiplatformV1beta1IndexEndpoint(
              displayName=args.display_name,
              description=args.description,
              network=args.network,
              labels=labels,
          ),
      )
    else:
      req = self.messages.AiplatformProjectsLocationsIndexEndpointsCreateRequest(
          parent=location_ref.RelativeName(),
          googleCloudAiplatformV1beta1IndexEndpoint=self.messages.GoogleCloudAiplatformV1beta1IndexEndpoint(
              displayName=args.display_name,
              description=args.description,
              publicEndpointEnabled=True,
              labels=labels,
              encryptionSpec=encryption_spec,
              privateServiceConnectConfig=private_service_connect_config,
          ),
      )

    return self._service.Create(req)

  def Create(self, location_ref, args):
    """Create a new v1 index endpoint."""
    labels = labels_util.ParseCreateArgs(
        args, self.messages.GoogleCloudAiplatformV1IndexEndpoint.LabelsValue)

    encryption_spec = None
    if args.encryption_kms_key_name is not None:
      encryption_spec = (
          self.messages.GoogleCloudAiplatformV1EncryptionSpec(
              kmsKeyName=args.encryption_kms_key_name))

    private_service_connect_config = None
    if args.enable_private_service_connect:
      private_service_connect_config = (
          self.messages.GoogleCloudAiplatformV1PrivateServiceConnectConfig(
              enablePrivateServiceConnect=args.enable_private_service_connect,
              projectAllowlist=(args.project_allowlist
                                if args.project_allowlist else []),
          )
      )

      req = self.messages.AiplatformProjectsLocationsIndexEndpointsCreateRequest(
          parent=location_ref.RelativeName(),
          googleCloudAiplatformV1IndexEndpoint=self.messages.GoogleCloudAiplatformV1IndexEndpoint(
              displayName=args.display_name,
              description=args.description,
              publicEndpointEnabled=args.public_endpoint_enabled,
              labels=labels,
              encryptionSpec=encryption_spec,
              privateServiceConnectConfig=private_service_connect_config,
          ),
      )
    elif args.network is not None:
      req = self.messages.AiplatformProjectsLocationsIndexEndpointsCreateRequest(
          parent=location_ref.RelativeName(),
          googleCloudAiplatformV1IndexEndpoint=self.messages.GoogleCloudAiplatformV1IndexEndpoint(
              displayName=args.display_name,
              description=args.description,
              network=args.network,
              labels=labels,
          ),
      )
    else:
      req = self.messages.AiplatformProjectsLocationsIndexEndpointsCreateRequest(
          parent=location_ref.RelativeName(),
          googleCloudAiplatformV1IndexEndpoint=self.messages.GoogleCloudAiplatformV1IndexEndpoint(
              displayName=args.display_name,
              description=args.description,
              publicEndpointEnabled=True,
              labels=labels,
              encryptionSpec=encryption_spec,
              privateServiceConnectConfig=private_service_connect_config,
          ),
      )

    return self._service.Create(req)

  def PatchBeta(self, index_endpoint_ref, args):
    """Update an index endpoint."""
    index_endpoint = self.messages.GoogleCloudAiplatformV1beta1IndexEndpoint()
    update_mask = []

    if args.display_name is not None:
      index_endpoint.displayName = args.display_name
      update_mask.append('display_name')

    if args.description is not None:
      index_endpoint.description = args.description
      update_mask.append('description')

    def GetLabels():
      return self.Get(index_endpoint_ref).labels

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        self.messages.GoogleCloudAiplatformV1beta1IndexEndpoint.LabelsValue,
        GetLabels)
    if labels_update.needs_update:
      index_endpoint.labels = labels_update.labels
      update_mask.append('labels')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    request = self.messages.AiplatformProjectsLocationsIndexEndpointsPatchRequest(
        name=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1IndexEndpoint=index_endpoint,
        updateMask=','.join(update_mask))
    return self._service.Patch(request)

  def Patch(self, index_endpoint_ref, args):
    """Update an v1 index endpoint."""
    index_endpoint = self.messages.GoogleCloudAiplatformV1IndexEndpoint()
    update_mask = []

    if args.display_name is not None:
      index_endpoint.displayName = args.display_name
      update_mask.append('display_name')

    if args.description is not None:
      index_endpoint.description = args.description
      update_mask.append('description')

    def GetLabels():
      return self.Get(index_endpoint_ref).labels

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args, self.messages.GoogleCloudAiplatformV1IndexEndpoint.LabelsValue,
        GetLabels)
    if labels_update.needs_update:
      index_endpoint.labels = labels_update.labels
      update_mask.append('labels')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    request = self.messages.AiplatformProjectsLocationsIndexEndpointsPatchRequest(
        name=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1IndexEndpoint=index_endpoint,
        updateMask=','.join(update_mask))
    return self._service.Patch(request)

  def DeployIndexBeta(self, index_endpoint_ref, args):
    """Deploy an index to an index endpoint."""
    index_ref = _ParseIndex(args.index, args.region)
    deployed_index = self.messages.GoogleCloudAiplatformV1beta1DeployedIndex(
        displayName=args.display_name,
        id=args.deployed_index_id,
        index=index_ref.RelativeName(),
    )

    if args.reserved_ip_ranges is not None:
      deployed_index.reservedIpRanges.extend(args.reserved_ip_ranges)

    if args.deployment_group is not None:
      deployed_index.deploymentGroup = args.deployment_group

    if args.enable_access_logging is not None:
      deployed_index.enableAccessLogging = args.enable_access_logging

    if args.audiences is not None and args.allowed_issuers is not None:
      auth_provider = self.messages.GoogleCloudAiplatformV1beta1DeployedIndexAuthConfigAuthProvider()
      auth_provider.audiences.extend(args.audiences)
      auth_provider.allowedIssuers.extend(args.allowed_issuers)
      deployed_index.deployedIndexAuthConfig = (
          self.messages.GoogleCloudAiplatformV1beta1DeployedIndexAuthConfig(
              authProvider=auth_provider))

    if args.machine_type is not None:
      dedicated_resources = (
          self.messages.GoogleCloudAiplatformV1beta1DedicatedResources()
      )
      dedicated_resources.machineSpec = (
          self.messages.GoogleCloudAiplatformV1beta1MachineSpec(
              machineType=args.machine_type
          )
      )
      if args.min_replica_count is not None:
        dedicated_resources.minReplicaCount = args.min_replica_count
      if args.max_replica_count is not None:
        dedicated_resources.maxReplicaCount = args.max_replica_count
      deployed_index.dedicatedResources = dedicated_resources
    else:
      automatic_resources = (
          self.messages.GoogleCloudAiplatformV1beta1AutomaticResources()
      )
      if args.min_replica_count is not None:
        automatic_resources.minReplicaCount = args.min_replica_count
      if args.max_replica_count is not None:
        automatic_resources.maxReplicaCount = args.max_replica_count
      deployed_index.automaticResources = automatic_resources

    deploy_index_req = self.messages.GoogleCloudAiplatformV1beta1DeployIndexRequest(
        deployedIndex=deployed_index)
    request = self.messages.AiplatformProjectsLocationsIndexEndpointsDeployIndexRequest(
        indexEndpoint=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1DeployIndexRequest=deploy_index_req)
    return self._service.DeployIndex(request)

  def DeployIndex(self, index_endpoint_ref, args):
    """Deploy an v1 index to an index endpoint."""
    index_ref = _ParseIndex(args.index, args.region)
    deployed_index = self.messages.GoogleCloudAiplatformV1DeployedIndex(
        displayName=args.display_name,
        id=args.deployed_index_id,
        index=index_ref.RelativeName(),
        enableAccessLogging=args.enable_access_logging
    )

    if args.reserved_ip_ranges is not None:
      deployed_index.reservedIpRanges.extend(args.reserved_ip_ranges)

    if args.deployment_group is not None:
      deployed_index.deploymentGroup = args.deployment_group

    if args.audiences is not None and args.allowed_issuers is not None:
      auth_provider = self.messages.GoogleCloudAiplatformV1DeployedIndexAuthConfigAuthProvider()
      auth_provider.audiences.extend(args.audiences)
      auth_provider.allowedIssuers.extend(args.allowed_issuers)
      deployed_index.deployedIndexAuthConfig = (
          self.messages.GoogleCloudAiplatformV1DeployedIndexAuthConfig(
              authProvider=auth_provider))

    if args.machine_type is not None:
      dedicated_resources = (
          self.messages.GoogleCloudAiplatformV1DedicatedResources()
      )
      dedicated_resources.machineSpec = (
          self.messages.GoogleCloudAiplatformV1MachineSpec(
              machineType=args.machine_type
          )
      )
      if args.min_replica_count is not None:
        dedicated_resources.minReplicaCount = args.min_replica_count
      if args.max_replica_count is not None:
        dedicated_resources.maxReplicaCount = args.max_replica_count
      deployed_index.dedicatedResources = dedicated_resources
    else:
      automatic_resources = (
          self.messages.GoogleCloudAiplatformV1AutomaticResources()
      )
      if args.min_replica_count is not None:
        automatic_resources.minReplicaCount = args.min_replica_count
      if args.max_replica_count is not None:
        automatic_resources.maxReplicaCount = args.max_replica_count
      deployed_index.automaticResources = automatic_resources

    deploy_index_req = self.messages.GoogleCloudAiplatformV1DeployIndexRequest(
        deployedIndex=deployed_index)
    request = self.messages.AiplatformProjectsLocationsIndexEndpointsDeployIndexRequest(
        indexEndpoint=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1DeployIndexRequest=deploy_index_req)
    return self._service.DeployIndex(request)

  def UndeployIndexBeta(self, index_endpoint_ref, args):
    """Undeploy an index to an index endpoint."""
    undeploy_index_req = self.messages.GoogleCloudAiplatformV1beta1UndeployIndexRequest(
        deployedIndexId=args.deployed_index_id)
    request = self.messages.AiplatformProjectsLocationsIndexEndpointsUndeployIndexRequest(
        indexEndpoint=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1UndeployIndexRequest=undeploy_index_req)
    return self._service.UndeployIndex(request)

  def UndeployIndex(self, index_endpoint_ref, args):
    """Undeploy an v1 index to an index endpoint."""
    undeploy_index_req = self.messages.GoogleCloudAiplatformV1UndeployIndexRequest(
        deployedIndexId=args.deployed_index_id)
    request = self.messages.AiplatformProjectsLocationsIndexEndpointsUndeployIndexRequest(
        indexEndpoint=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1UndeployIndexRequest=undeploy_index_req)
    return self._service.UndeployIndex(request)

  def MutateDeployedIndexBeta(self, index_endpoint_ref, args):
    """Mutate a deployed index from an index endpoint."""

    automatic_resources = self.messages.GoogleCloudAiplatformV1beta1AutomaticResources(
    )
    if args.min_replica_count is not None:
      automatic_resources.minReplicaCount = args.min_replica_count
    if args.max_replica_count is not None:
      automatic_resources.maxReplicaCount = args.max_replica_count

    deployed_index = self.messages.GoogleCloudAiplatformV1beta1DeployedIndex(
        automaticResources=automatic_resources, id=args.deployed_index_id,
        enableAccessLogging=args.enable_access_logging)

    if args.reserved_ip_ranges is not None:
      deployed_index.reservedIpRanges.extend(args.reserved_ip_ranges)

    if args.deployment_group is not None:
      deployed_index.deploymentGroup = args.deployment_group

    if args.audiences is not None and args.allowed_issuers is not None:
      auth_provider = self.messages.GoogleCloudAiplatformV1beta1DeployedIndexAuthConfigAuthProvider()
      auth_provider.audiences.extend(args.audiences)
      auth_provider.allowedIssuers.extend(args.allowed_issuers)
      deployed_index.deployedIndexAuthConfig = (
          self.messages.GoogleCloudAiplatformV1beta1DeployedIndexAuthConfig(
              authProvider=auth_provider))

    request = self.messages.AiplatformProjectsLocationsIndexEndpointsMutateDeployedIndexRequest(
        indexEndpoint=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1beta1DeployedIndex=deployed_index)
    return self._service.MutateDeployedIndex(request)

  def MutateDeployedIndex(self, index_endpoint_ref, args):
    """Mutate a deployed index from an index endpoint."""

    automatic_resources = self.messages.GoogleCloudAiplatformV1AutomaticResources(
    )
    if args.min_replica_count is not None:
      automatic_resources.minReplicaCount = args.min_replica_count
    if args.max_replica_count is not None:
      automatic_resources.maxReplicaCount = args.max_replica_count

    deployed_index = self.messages.GoogleCloudAiplatformV1DeployedIndex(
        id=args.deployed_index_id, automaticResources=automatic_resources,
        enableAccessLogging=args.enable_access_logging)

    if args.reserved_ip_ranges is not None:
      deployed_index.reservedIpRanges.extend(args.reserved_ip_ranges)

    if args.deployment_group is not None:
      deployed_index.deploymentGroup = args.deployment_group

    if args.audiences is not None and args.allowed_issuers is not None:
      auth_provider = self.messages.GoogleCloudAiplatformV1DeployedIndexAuthConfigAuthProvider()
      auth_provider.audiences.extend(args.audiences)
      auth_provider.allowedIssuers.extend(args.allowed_issuers)
      deployed_index.deployedIndexAuthConfig = (
          self.messages.GoogleCloudAiplatformV1DeployedIndexAuthConfig(
              authProvider=auth_provider))

    request = self.messages.AiplatformProjectsLocationsIndexEndpointsMutateDeployedIndexRequest(
        indexEndpoint=index_endpoint_ref.RelativeName(),
        googleCloudAiplatformV1DeployedIndex=deployed_index)
    return self._service.MutateDeployedIndex(request)

  def Get(self, index_endpoint_ref):
    request = self.messages.AiplatformProjectsLocationsIndexEndpointsGetRequest(
        name=index_endpoint_ref.RelativeName())
    return self._service.Get(request)

  def List(self, limit=None, region_ref=None):
    return list_pager.YieldFromList(
        self._service,
        self.messages.AiplatformProjectsLocationsIndexEndpointsListRequest(
            parent=region_ref.RelativeName()),
        field='indexEndpoints',
        batch_size_attribute='pageSize',
        limit=limit)

  def Delete(self, index_endpoint_ref):
    request = self.messages.AiplatformProjectsLocationsIndexEndpointsDeleteRequest(
        name=index_endpoint_ref.RelativeName())
    return self._service.Delete(request)
