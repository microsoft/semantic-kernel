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
"""Base class for gkemulticloud API clients for locations."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container.gkemulticloud import client
from googlecloudsdk.command_lib.container.attached import flags as attached_flags


class LocationsClient(client.ClientBase):
  """Client for managing locations."""

  def __init__(self, **kwargs):
    super(LocationsClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations

  def GetAwsServerConfig(self, location_ref):
    """Gets server config for Anthos on AWS."""
    req = (
        self._messages.GkemulticloudProjectsLocationsGetAwsServerConfigRequest(
            name=location_ref.RelativeName() + '/awsServerConfig'
        )
    )
    return self._service.GetAwsServerConfig(req)

  def GetAzureServerConfig(self, location_ref):
    """Gets server config for Anthos on Azure."""
    req = self._messages.GkemulticloudProjectsLocationsGetAzureServerConfigRequest(
        name=location_ref.RelativeName() + '/azureServerConfig'
    )
    return self._service.GetAzureServerConfig(req)

  def GetAttachedServerConfig(self, location_ref):
    """Gets server config for Anthos Attached Clusters."""
    req = self._messages.GkemulticloudProjectsLocationsGetAttachedServerConfigRequest(
        name=location_ref.RelativeName() + '/attachedServerConfig'
    )
    return self._service.GetAttachedServerConfig(req)

  def GenerateInstallManifest(self, cluster_ref, args):
    """Generates an Attached cluster install manifest."""
    req = self._messages.GkemulticloudProjectsLocationsGenerateAttachedClusterInstallManifestRequest(
        parent=cluster_ref.Parent().RelativeName(),
        attachedClusterId=cluster_ref.attachedClustersId,
        platformVersion=attached_flags.GetPlatformVersion(args),
        proxyConfig_kubernetesSecret_name=attached_flags.GetProxySecretName(args),
        proxyConfig_kubernetesSecret_namespace=
        attached_flags.GetProxySecretNamespace(args),
    )

    # This is a workaround for the limitation in apitools with nested messages.
    encoding.AddCustomJsonFieldMapping(
        self._messages.GkemulticloudProjectsLocationsGenerateAttachedClusterInstallManifestRequest,
        'proxyConfig_kubernetesSecret_name',
        'proxyConfig.kubernetesSecret.name',
    )
    encoding.AddCustomJsonFieldMapping(
        self._messages.GkemulticloudProjectsLocationsGenerateAttachedClusterInstallManifestRequest,
        'proxyConfig_kubernetesSecret_namespace',
        'proxyConfig.kubernetesSecret.namespace',
    )

    return self._service.GenerateAttachedClusterInstallManifest(req)

  def GenerateInstallManifestForImport(
      self, location_ref, memberships_id, args
  ):
    """Generates an Attached cluster install manifest for import."""
    req = self._messages.GkemulticloudProjectsLocationsGenerateAttachedClusterInstallManifestRequest(
        parent=location_ref.RelativeName(),
        attachedClusterId=memberships_id,
        platformVersion=attached_flags.GetPlatformVersion(args),
        proxyConfig_kubernetesSecret_name=attached_flags.GetProxySecretName(args),
        proxyConfig_kubernetesSecret_namespace=
        attached_flags.GetProxySecretNamespace(args),
    )

    # This is a workaround for the limitation in apitools with nested messages.
    encoding.AddCustomJsonFieldMapping(
        self._messages.GkemulticloudProjectsLocationsGenerateAttachedClusterInstallManifestRequest,
        'proxyConfig_kubernetesSecret_name',
        'proxyConfig.kubernetesSecret.name',
    )
    encoding.AddCustomJsonFieldMapping(
        self._messages.GkemulticloudProjectsLocationsGenerateAttachedClusterInstallManifestRequest,
        'proxyConfig_kubernetesSecret_namespace',
        'proxyConfig.kubernetesSecret.namespace',
    )
    return self._service.GenerateAttachedClusterInstallManifest(req)
