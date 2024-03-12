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
"""Base class for gkemulticloud API clients for AWS resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import client
from googlecloudsdk.api_lib.container.gkemulticloud import update_mask
from googlecloudsdk.command_lib.container.aws import flags as aws_flags
from googlecloudsdk.command_lib.container.gkemulticloud import flags


class _AwsClientBase(client.ClientBase):
  """Base class for AWS gkemulticloud API clients."""

  def _Cluster(self, cluster_ref, args):
    cluster_type = self._messages.GoogleCloudGkemulticloudV1AwsCluster
    kwargs = {
        'annotations': self._Annotations(args, cluster_type),
        'authorization': self._Authorization(args),
        'awsRegion': aws_flags.GetAwsRegion(args),
        'binaryAuthorization': self._BinaryAuthorization(args),
        'controlPlane': self._ControlPlane(args),
        'description': flags.GetDescription(args),
        'fleet': self._Fleet(args),
        'loggingConfig': flags.GetLogging(args),
        'monitoringConfig': flags.GetMonitoringConfig(args),
        'name': cluster_ref.awsClustersId,
        'networking': self._ClusterNetworking(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsCluster(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _NodePool(self, node_pool_ref, args):
    nodepool_type = self._messages.GoogleCloudGkemulticloudV1AwsNodePool
    kwargs = {
        'annotations': self._Annotations(args, nodepool_type),
        'autoscaling': self._NodePoolAutoscaling(args),
        'config': self._NodeConfig(args),
        'maxPodsConstraint': self._MaxPodsConstraint(args),
        'management': self._NodeManagement(args),
        'name': node_pool_ref.awsNodePoolsId,
        'subnetId': flags.GetSubnetID(args),
        'updateSettings': self._UpdateSettings(args),
        'version': flags.GetNodeVersion(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsNodePool(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _ClusterNetworking(self, args):
    kwargs = {
        'podAddressCidrBlocks': flags.GetPodAddressCidrBlocks(args),
        'serviceAddressCidrBlocks': flags.GetServiceAddressCidrBlocks(args),
        'vpcId': aws_flags.GetVpcId(args),
        'perNodePoolSgRulesDisabled': aws_flags.GetPerNodePoolSGRulesDisabled(
            args
        ),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsClusterNetworking(**kwargs)
        if any(x is not None for x in kwargs.values())
        else None
    )

  def _ControlPlane(self, args):
    control_plane_type = (
        self._messages.GoogleCloudGkemulticloudV1AwsControlPlane
    )
    kwargs = {
        'awsServicesAuthentication': self._ServicesAuthentication(args),
        'configEncryption': self._ConfigEncryption(args),
        'databaseEncryption': self._DatabaseEncryption(args),
        'iamInstanceProfile': aws_flags.GetIamInstanceProfile(args),
        'instancePlacement': self._InstancePlacement(args),
        'instanceType': aws_flags.GetInstanceType(args),
        'mainVolume': self._VolumeTemplate(args, 'main'),
        'proxyConfig': self._ProxyConfig(args),
        'rootVolume': self._VolumeTemplate(args, 'root'),
        'securityGroupIds': aws_flags.GetSecurityGroupIds(args),
        'sshConfig': self._SshConfig(args),
        'subnetIds': aws_flags.GetSubnetIds(args),
        'version': flags.GetClusterVersion(args),
        'tags': self._Tags(args, control_plane_type),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsControlPlane(**kwargs)
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
          self._messages.GoogleCloudGkemulticloudV1AwsClusterUser(
              username=u
          )
          for u in admin_users
      ]
    if admin_groups:
      kwargs['adminGroups'] = [
          self._messages.GoogleCloudGkemulticloudV1AwsClusterGroup(group=g)
          for g in admin_groups
      ]
    if not any(kwargs.values()):
      return None
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsAuthorization(
            **kwargs
        )
    )

  def _ServicesAuthentication(self, args):
    kwargs = {
        'roleArn': aws_flags.GetRoleArn(args),
        'roleSessionName': aws_flags.GetRoleSessionName(args),
    }
    if not any(kwargs.values()):
      return None
    return self._messages.GoogleCloudGkemulticloudV1AwsServicesAuthentication(
        **kwargs
    )

  def _ProxyConfig(self, args):
    kwargs = {
        'secretArn': aws_flags.GetProxySecretArn(args),
        'secretVersion': aws_flags.GetProxySecretVersionId(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsProxyConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _VolumeTemplate(self, args, kind):
    kwargs = {}
    if kind == 'main':
      kwargs['iops'] = aws_flags.GetMainVolumeIops(args)
      kwargs['kmsKeyArn'] = aws_flags.GetMainVolumeKmsKeyArn(args)
      kwargs['sizeGib'] = flags.GetMainVolumeSize(args)
      kwargs['volumeType'] = aws_flags.GetMainVolumeType(args)
      kwargs['throughput'] = aws_flags.GetMainVolumeThroughput(args)
    elif kind == 'root':
      kwargs['iops'] = aws_flags.GetRootVolumeIops(args)
      kwargs['kmsKeyArn'] = aws_flags.GetRootVolumeKmsKeyArn(args)
      kwargs['sizeGib'] = flags.GetRootVolumeSize(args)
      kwargs['volumeType'] = aws_flags.GetRootVolumeType(args)
      kwargs['throughput'] = aws_flags.GetRootVolumeThroughput(args)
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsVolumeTemplate(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _DatabaseEncryption(self, args):
    kwargs = {'kmsKeyArn': aws_flags.GetDatabaseEncryptionKmsKeyArn(args)}
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsDatabaseEncryption(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _ConfigEncryption(self, args):
    kwargs = {'kmsKeyArn': aws_flags.GetConfigEncryptionKmsKeyArn(args)}
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsConfigEncryption(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _SshConfig(self, args):
    kwargs = {'ec2KeyPair': aws_flags.GetSshEC2KeyPair(args)}
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsSshConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _SpotConfig(self, args):
    kwargs = {'instanceTypes': aws_flags.GetSpotInstanceTypes(args)}
    return (
        self._messages.GoogleCloudGkemulticloudV1SpotConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _InstancePlacement(self, args):
    kwargs = {'tenancy': aws_flags.GetInstancePlacement(args)}
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsInstancePlacement(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _AutoScalingMetricsCollection(self, args):
    kwargs = {
        'granularity': aws_flags.GetAutoscalingMetricsGranularity(args),
        'metrics': aws_flags.GetAutoscalingMetrics(args),
    }
    if not any(kwargs.values()):
      return None
    return self._messages.GoogleCloudGkemulticloudV1AwsAutoscalingGroupMetricsCollection(
        **kwargs
    )

  def _NodeManagement(self, args):
    kwargs = {
        'autoRepair': flags.GetAutoRepair(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsNodeManagement(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _UpdateSettings(self, args):
    kwargs = {
        'surgeSettings': self._SurgeSettings(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1UpdateSettings(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _SurgeSettings(self, args):
    kwargs = {
        'maxSurge': flags.GetMaxSurgeUpdate(args),
        'maxUnavailable': flags.GetMaxUnavailableUpdate(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1SurgeSettings(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _NodeConfig(self, args):
    node_config_type = self._messages.GoogleCloudGkemulticloudV1AwsNodeConfig
    kwargs = {
        'configEncryption': self._ConfigEncryption(args),
        'iamInstanceProfile': aws_flags.GetIamInstanceProfile(args),
        'imageType': flags.GetImageType(args),
        'instancePlacement': self._InstancePlacement(args),
        'instanceType': aws_flags.GetInstanceType(args),
        'proxyConfig': self._ProxyConfig(args),
        'rootVolume': self._VolumeTemplate(args, 'root'),
        'securityGroupIds': aws_flags.GetSecurityGroupIds(args),
        'spotConfig': self._SpotConfig(args),
        'sshConfig': self._SshConfig(args),
        'taints': flags.GetNodeTaints(args),
        'labels': self._Labels(args, node_config_type),
        'tags': self._Tags(args, node_config_type),
        'autoscalingMetricsCollection': self._AutoScalingMetricsCollection(
            args
        ),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AwsNodeConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _NodePoolAutoscaling(self, args):
    kwargs = {
        'minNodeCount': flags.GetMinNodes(args),
        'maxNodeCount': flags.GetMaxNodes(args),
    }
    if not any(kwargs.values()):
      return None
    return self._messages.GoogleCloudGkemulticloudV1AwsNodePoolAutoscaling(
        **kwargs
    )


class ClustersClient(_AwsClientBase):
  """Client for AWS Clusters in the gkemulticloud API."""

  def __init__(self, **kwargs):
    super(ClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_awsClusters
    self._list_result_field = 'awsClusters'

  def Create(self, cluster_ref, args):
    """Creates an Anthos cluster on AWS."""
    req = self._messages.GkemulticloudProjectsLocationsAwsClustersCreateRequest(
        awsClusterId=cluster_ref.awsClustersId,
        googleCloudGkemulticloudV1AwsCluster=self._Cluster(cluster_ref, args),
        parent=cluster_ref.Parent().RelativeName(),
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Create(req)

  def GenerateAccessToken(self, cluster_ref):
    """Generates an access token for an Anthos cluster on AWS."""
    req = self._messages.GkemulticloudProjectsLocationsAwsClustersGenerateAwsAccessTokenRequest(
        awsCluster=cluster_ref.RelativeName()
    )
    return self._service.GenerateAwsAccessToken(req)

  def Update(self, cluster_ref, args):
    """Updates an Anthos cluster on AWS."""
    req = self._messages.GkemulticloudProjectsLocationsAwsClustersPatchRequest(
        googleCloudGkemulticloudV1AwsCluster=self._Cluster(cluster_ref, args),
        name=cluster_ref.RelativeName(),
        updateMask=update_mask.GetUpdateMask(
            args, update_mask.AWS_CLUSTER_ARGS_TO_UPDATE_MASKS
        ),
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Patch(req)


class NodePoolsClient(_AwsClientBase):
  """Client for AWS node pools in the gkemulticloud API."""

  def __init__(self, **kwargs):
    super(NodePoolsClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_awsClusters_awsNodePools
    self._list_result_field = 'awsNodePools'

  def Create(self, node_pool_ref, args):
    """Creates an node pool in an Anthos cluster on AWS."""
    req = self._messages.GkemulticloudProjectsLocationsAwsClustersAwsNodePoolsCreateRequest(
        awsNodePoolId=node_pool_ref.awsNodePoolsId,
        googleCloudGkemulticloudV1AwsNodePool=self._NodePool(
            node_pool_ref, args
        ),
        parent=node_pool_ref.Parent().RelativeName(),
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Create(req)

  def Update(self, node_pool_ref, args):
    """Updates a node pool in an Anthos cluster on AWS."""
    req = self._messages.GkemulticloudProjectsLocationsAwsClustersAwsNodePoolsPatchRequest(
        googleCloudGkemulticloudV1AwsNodePool=self._NodePool(
            node_pool_ref, args
        ),
        name=node_pool_ref.RelativeName(),
        updateMask=update_mask.GetUpdateMask(
            args, update_mask.AWS_NODEPOOL_ARGS_TO_UPDATE_MASKS
        ),
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Patch(req)

  def Rollback(self, node_pool_ref, args):
    """Rolls back a node pool in an Anthos cluster on AWS."""
    req = self._messages.GkemulticloudProjectsLocationsAwsClustersAwsNodePoolsRollbackRequest(
        name=node_pool_ref.RelativeName(),
        googleCloudGkemulticloudV1RollbackAwsNodePoolUpdateRequest=self._messages.GoogleCloudGkemulticloudV1RollbackAwsNodePoolUpdateRequest(
            respectPdb=flags.GetRespectPodDisruptionBudget(args),
        ),
    )
    return self._service.Rollback(req)
