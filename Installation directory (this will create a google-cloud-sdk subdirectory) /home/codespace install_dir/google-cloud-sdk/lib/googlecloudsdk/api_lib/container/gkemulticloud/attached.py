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
"""Base class for gkemulticloud API clients for Attached resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import client
from googlecloudsdk.api_lib.container.gkemulticloud import update_mask
from googlecloudsdk.command_lib.container.attached import flags as attached_flags
from googlecloudsdk.command_lib.container.gkemulticloud import flags


class _AttachedClientBase(client.ClientBase):
  """Base class for Attached gkemulticloud API clients."""

  def _Cluster(self, cluster_ref, args):
    cluster_type = self._messages.GoogleCloudGkemulticloudV1AttachedCluster
    kwargs = {
        'annotations': self._Annotations(args, cluster_type),
        'binaryAuthorization': self._BinaryAuthorization(args),
        'platformVersion': attached_flags.GetPlatformVersion(args),
        'fleet': self._Fleet(args),
        'name': cluster_ref.attachedClustersId,
        'description': flags.GetDescription(args),
        'oidcConfig': self._OidcConfig(args),
        'distribution': attached_flags.GetDistribution(args),
        'authorization': self._Authorization(args),
        'loggingConfig': flags.GetLogging(args, True),
        'monitoringConfig': flags.GetMonitoringConfig(args),
        'proxyConfig': self._ProxyConfig(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1AttachedCluster(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _OidcConfig(self, args):
    kwargs = {
        'issuerUrl': attached_flags.GetIssuerUrl(args),
    }
    oidc = attached_flags.GetOidcJwks(args)
    if oidc:
      kwargs['jwks'] = oidc.encode(encoding='utf-8')
    return (
        self._messages.GoogleCloudGkemulticloudV1AttachedOidcConfig(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _ProxyConfig(self, args):
    secret_name = attached_flags.GetProxySecretName(args)
    secret_namespace = attached_flags.GetProxySecretNamespace(args)
    if secret_name or secret_namespace:
      kwargs = {
          'kubernetesSecret':
          self._messages.GoogleCloudGkemulticloudV1KubernetesSecret(
              name=secret_name,
              namespace=secret_namespace,
          )
      }
      return (
          self._messages.GoogleCloudGkemulticloudV1AttachedProxyConfig(
              **kwargs
              )
      )
    return None

  def _Authorization(self, args):
    admin_users = attached_flags.GetAdminUsers(args)
    admin_groups = flags.GetAdminGroups(args)
    if not admin_users and not admin_groups:
      return None
    kwargs = {}
    if admin_users:
      kwargs['adminUsers'] = [
          self._messages.GoogleCloudGkemulticloudV1AttachedClusterUser(
              username=u
          )
          for u in admin_users
      ]
    if admin_groups:
      kwargs['adminGroups'] = [
          self._messages.GoogleCloudGkemulticloudV1AttachedClusterGroup(group=g)
          for g in admin_groups
      ]
    if not any(kwargs.values()):
      return None
    return (
        self._messages.GoogleCloudGkemulticloudV1AttachedClustersAuthorization(
            **kwargs
        )
    )


class ClustersClient(_AttachedClientBase):
  """Client for Attached Clusters in the gkemulticloud API."""

  def __init__(self, **kwargs):
    super(ClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_attachedClusters
    self._list_result_field = 'attachedClusters'

  def Create(self, cluster_ref, args):
    """Creates an Attached cluster."""
    req = self._messages.GkemulticloudProjectsLocationsAttachedClustersCreateRequest(
        parent=cluster_ref.Parent().RelativeName(),
        googleCloudGkemulticloudV1AttachedCluster=self._Cluster(
            cluster_ref, args
        ),
        attachedClusterId=cluster_ref.attachedClustersId,
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Create(req)

  def Update(self, cluster_ref, args):
    """Updates an Attached cluster."""
    req = self._messages.GkemulticloudProjectsLocationsAttachedClustersPatchRequest(
        googleCloudGkemulticloudV1AttachedCluster=self._Cluster(
            cluster_ref, args
        ),
        name=cluster_ref.RelativeName(),
        updateMask=update_mask.GetUpdateMask(
            args, update_mask.ATTACHED_CLUSTER_ARGS_TO_UPDATE_MASKS
        ),
        validateOnly=flags.GetValidateOnly(args),
    )
    return self._service.Patch(req)

  def Import(self, location_ref, fleet_membership_ref, args):
    """Imports an Attached cluster fleet membership."""
    req = self._messages.GkemulticloudProjectsLocationsAttachedClustersImportRequest(
        parent=location_ref.RelativeName(),
        googleCloudGkemulticloudV1ImportAttachedClusterRequest=self._messages.GoogleCloudGkemulticloudV1ImportAttachedClusterRequest(
            fleetMembership=fleet_membership_ref.RelativeName(),
            platformVersion=attached_flags.GetPlatformVersion(args),
            distribution=attached_flags.GetDistribution(args),
            proxyConfig=self._ProxyConfig(args),
            validateOnly=flags.GetValidateOnly(args),
        ),
    )
    return self._service.Import(req)
