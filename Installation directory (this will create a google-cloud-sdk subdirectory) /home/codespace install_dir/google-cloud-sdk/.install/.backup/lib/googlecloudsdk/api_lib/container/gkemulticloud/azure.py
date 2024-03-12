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
"""Base class for gkemulticloud API clients for Azure resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import client
from googlecloudsdk.api_lib.container.gkemulticloud import update_mask
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import flags


class _AzureClientBase(client.ClientBase):
  """Base class for Azure gkemulticloud API clients."""

  def _Cluster(self, cluster_ref, args):
    azure_client = (
        resource_args.ParseAzureClientResourceArg(args).RelativeName()
        if hasattr(args, 'client') and args.IsSpecified('client')
        else None
    )
    cluster_type = self._messages.GoogleCloudGkemulticloudV1AzureCluster
    kwargs = {
        'annotations': self._Annotations(args, cluster_type),
        'authorization': self._Authorization(args),
        'azureClient': azure_client,
        'azureServicesAuthentication': self._AzureServicesAuthentication(args),
        'azureRegion': flags.GetAzureRegion(args),
        'controlPlane': self._ControlPlane(args),
        'description': flags.GetDescription(args),
        'fleet': self._Fleet(args),
        'loggingConfig': flags.GetLogging(args),
        'monitoringConfig': flags.GetMonitoringConfig(args),
        'name': cluster_ref.azureClustersId,
        'networking': self._ClusterNetworking(args),
        'resourceGroupId': flags.GetResourceGroupId(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureCluster(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _AzureServicesAuthentication(self, args):
    kwargs = {
        'applicationId': flags.GetAzureApplicationID(args),
        'tenantId': flags.GetAzureTenantID(args),
    }
    if not any(kwargs.values()):
      return None
    return self._messages.GoogleCloudGkemulticloudV1AzureServicesAuthentication(
        **kwargs
    )

  def _Client(self, client_ref, args):
    kwargs = {
        'applicationId': getattr(args, 'app_id', None),
        'name': client_ref.azureClientsId,
        'tenantId': getattr(args, 'tenant_id', None),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureClient(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _NodePool(self, node_pool_ref, args):
    nodepool_type = self._messages.GoogleCloudGkemulticloudV1AzureNodePool
    kwargs = {
        'annotations': self._Annotations(args, nodepool_type),
        'autoscaling': self._Autoscaling(args),
        'azureAvailabilityZone': flags.GetAzureAvailabilityZone(args),
        'config': self._NodeConfig(args),
        'management': self._NodeManagement(args),
        'maxPodsConstraint': self._MaxPodsConstraint(args),
        'name': node_pool_ref.azureNodePoolsId,
        'subnetId': flags.GetSubnetID(args),
        'version': flags.GetNodeVersion(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureNodePool(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _DiskTemplate(self, args, kind):
    kwargs = {}
    if kind == 'root':
      kwargs['sizeGib'] = flags.GetRootVolumeSize(args)
    elif kind == 'main':
      kwargs['sizeGib'] = flags.GetMainVolumeSize(args)
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureDiskTemplate(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _ProxyConfig(self, args):
    kwargs = {
        'resourceGroupId': flags.GetProxyResourceGroupId(args),
        'secretId': flags.GetProxySecretId(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureProxyConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _ConfigEncryption(self, args):
    kwargs = {
        'keyId': flags.GetConfigEncryptionKeyId(args),
        'publicKey': flags.GetConfigEncryptionPublicKey(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureConfigEncryption(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _Authorization(self, args):
    admin_users = flags.GetAdminUsers(args)
    admin_groups = flags.GetAdminGroups(args)
    if not admin_users and not admin_groups:
      return None
    kwargs = {}
    if admin_users:
      kwargs['adminUsers'] = [
          self._messages.GoogleCloudGkemulticloudV1AzureClusterUser(
              username=u
          )
          for u in admin_users
      ]
    if admin_groups:
      kwargs['adminGroups'] = [
          self._messages.GoogleCloudGkemulticloudV1AzureClusterGroup(group=g)
          for g in admin_groups
      ]
    if not any(kwargs.values()):
      return None
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureAuthorization(
            **kwargs
        )
    )

  def _ClusterNetworking(self, args):
    kwargs = {
        'podAddressCidrBlocks': flags.GetPodAddressCidrBlocks(args),
        'serviceAddressCidrBlocks': flags.GetServiceAddressCidrBlocks(args),
        'serviceLoadBalancerSubnetId': flags.GetServiceLoadBalancerSubnetId(
            args
        ),
        'virtualNetworkId': flags.GetVnetId(args),
    }
    if not any(kwargs.values()):
      return None
    return self._messages.GoogleCloudGkemulticloudV1AzureClusterNetworking(
        **kwargs
    )

  def _ControlPlane(self, args):
    control_plane_type = (
        self._messages.GoogleCloudGkemulticloudV1AzureControlPlane
    )
    kwargs = {
        'configEncryption': self._ConfigEncryption(args),
        'databaseEncryption': self._DatabaseEncryption(args),
        'endpointSubnetId': flags.GetEndpointSubnetId(args),
        'mainVolume': self._DiskTemplate(args, 'main'),
        'proxyConfig': self._ProxyConfig(args),
        'replicaPlacements': flags.GetReplicaPlacements(args),
        'rootVolume': self._DiskTemplate(args, 'root'),
        'sshConfig': self._SshConfig(args),
        'subnetId': flags.GetSubnetID(args),
        'tags': self._Tags(args, control_plane_type),
        'version': flags.GetClusterVersion(args),
        'vmSize': flags.GetVMSize(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureControlPlane(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _SshConfig(self, args):
    kwargs = {
        'authorizedKey': flags.GetSSHPublicKey(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureSshConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _DatabaseEncryption(self, args):
    kwargs = {
        'keyId': flags.GetDatabaseEncryptionKeyId(args),
    }
    if not any(kwargs.values()):
      return None
    return self._messages.GoogleCloudGkemulticloudV1AzureDatabaseEncryption(
        **kwargs
    )

  def _Autoscaling(self, args):
    kwargs = {
        'minNodeCount': flags.GetMinNodes(args),
        'maxNodeCount': flags.GetMaxNodes(args),
    }
    if not any(kwargs.values()):
      return None
    return self._messages.GoogleCloudGkemulticloudV1AzureNodePoolAutoscaling(
        **kwargs
    )

  def _NodeConfig(self, args):
    node_config_type = self._messages.GoogleCloudGkemulticloudV1AzureNodeConfig
    kwargs = {
        'configEncryption': self._ConfigEncryption(args),
        'imageType': flags.GetImageType(args),
        'labels': self._Labels(args, node_config_type),
        'proxyConfig': self._ProxyConfig(args),
        'rootVolume': self._DiskTemplate(args, 'root'),
        'sshConfig': self._SshConfig(args),
        'tags': self._Tags(args, node_config_type),
        'taints': flags.GetNodeTaints(args),
        'vmSize': flags.GetVMSize(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureNodeConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _NodeManagement(self, args):
    kwargs = {
        'autoRepair': flags.GetAutoRepair(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AzureNodeManagement(**kwargs)
        if any(kwargs.values())
        else None
    )


class ClustersClient(_AzureClientBase):
  """Client for Azure Clusters in the gkemulticloud API."""

  def __init__(self, **kwargs):
    super(ClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_azureClusters
    self._list_result_field = 'azureClusters'

  def Create(self, cluster_ref, args):
    """Creates a new Anthos cluster on Azure."""
    req = (
        self._messages.GkemulticloudProjectsLocationsAzureClustersCreateRequest(
            azureClusterId=cluster_ref.azureClustersId,
            googleCloudGkemulticloudV1AzureCluster=self._Cluster(
                cluster_ref, args
            ),
            parent=cluster_ref.Parent().RelativeName(),
            validateOnly=flags.GetValidateOnly(args),
        )
    )
    return self._service.Create(req)

  def GenerateAccessToken(self, cluster_ref):
    """Generates an access token for an Azure cluster."""
    req = self._service.GetRequestType('GenerateAzureAccessToken')(
        azureCluster=cluster_ref.RelativeName()
    )
    return self._service.GenerateAzureAccessToken(req)

  def Update(self, cluster_ref, args):
    """Updates an Anthos cluster on Azure."""
    req = (
        self._messages.GkemulticloudProjectsLocationsAzureClustersPatchRequest(
            googleCloudGkemulticloudV1AzureCluster=self._Cluster(
                cluster_ref, args
            ),
            name=cluster_ref.RelativeName(),
            updateMask=update_mask.GetUpdateMask(
                args, update_mask.AZURE_CLUSTER_ARGS_TO_UPDATE_MASKS
            ),
            validateOnly=flags.GetValidateOnly(args),
        )
    )
    return self._service.Patch(req)


class NodePoolsClient(_AzureClientBase):
  """Client for Azure Node Pools in the gkemulticloud API."""

  def __init__(self, **kwargs):
    super(NodePoolsClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_azureClusters_azureNodePools
    self._list_result_field = 'azureNodePools'

  def Create(self, nodepool_ref, args):
    """Creates a node pool in an Anthos cluster on Azure."""
    req = self._messages.GkemulticloudProjectsLocationsAzureClustersAzureNodePoolsCreateRequest(
        azureNodePoolId=nodepool_ref.azureNodePoolsId,
        googleCloudGkemulticloudV1AzureNodePool=self._NodePool(
            nodepool_ref, args
        ),
        parent=nodepool_ref.Parent().RelativeName(),
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Create(req)

  def Update(self, nodepool_ref, args):
    """Updates a node pool in an Anthos cluster on Azure."""
    req = self._messages.GkemulticloudProjectsLocationsAzureClustersAzureNodePoolsPatchRequest(
        googleCloudGkemulticloudV1AzureNodePool=self._NodePool(
            nodepool_ref, args
        ),
        name=nodepool_ref.RelativeName(),
        updateMask=update_mask.GetUpdateMask(
            args, update_mask.AZURE_NODEPOOL_ARGS_TO_UPDATE_MASKS
        ),
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Patch(req)


class ClientsClient(_AzureClientBase):
  """Client for Azure Clients in the gkemulticloud API."""

  def __init__(self, **kwargs):
    super(ClientsClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_azureClients
    self._list_result_field = 'azureClients'

  def Create(self, client_ref, args):
    """Creates a new Azure client."""
    req = (
        self._messages.GkemulticloudProjectsLocationsAzureClientsCreateRequest(
            googleCloudGkemulticloudV1AzureClient=self._Client(
                client_ref, args
            ),
            azureClientId=client_ref.azureClientsId,
            parent=client_ref.Parent().RelativeName(),
            validateOnly=flags.GetValidateOnly(args),
        )
    )
    return self._service.Create(req)
