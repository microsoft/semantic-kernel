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
"""Utilities for querying Vertex AI Persistent Resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io


class PersistentResourcesClient(object):
  """Client used for interacting with the PersistentResource endpoint."""

  def __init__(self, version=constants.BETA_VERSION):
    client = apis.GetClientInstance(constants.AI_PLATFORM_API_NAME,
                                    constants.AI_PLATFORM_API_VERSION[version])
    self._messages = client.MESSAGES_MODULE
    self._version = version
    self._service = client.projects_locations_persistentResources
    self._message_prefix = constants.AI_PLATFORM_MESSAGE_PREFIX[version]

  def GetMessage(self, message_name):
    """Returns the API message class by name."""

    return getattr(
        self._messages,
        '{prefix}{name}'.format(prefix=self._message_prefix,
                                name=message_name), None)

  def PersistentResourceMessage(self):
    """Returns the PersistentResource message."""

    return self.GetMessage('PersistentResource')

  def Create(self,
             parent,
             resource_pools,
             persistent_resource_id,
             display_name=None,
             kms_key_name=None,
             labels=None,
             network=None,
             enable_custom_service_account=False,
             service_account=None):
    """Constructs a request and sends it to the endpoint to create a persistent resource.

    Args:
      parent: str, The project resource path of the persistent resource to
      create.
      resource_pools: The PersistentResource message instance for the
      creation request.
      persistent_resource_id: The PersistentResource id for the creation
      request.
      display_name: str, The display name of the persistent resource to create.
      kms_key_name: A customer-managed encryption key to use for the persistent
      resource.
      labels: LabelValues, map-like user-defined metadata to organize the
      resource.
      network: Network to peer with the PersistentResource
      enable_custom_service_account: Whether or not to enable this Persistent
        Resource to use a custom service account.
      service_account: A service account (email address string) to use for
        creating the Persistent Resource.

    Returns:
      A PersistentResource message instance created.
    """
    persistent_resource = self.PersistentResourceMessage()(
        displayName=display_name, resourcePools=resource_pools)

    if kms_key_name is not None:
      persistent_resource.encryptionSpec = self.GetMessage('EncryptionSpec')(
          kmsKeyName=kms_key_name)

    if labels:
      persistent_resource.labels = labels

    if network:
      persistent_resource.network = network

    if enable_custom_service_account:
      persistent_resource.resourceRuntimeSpec = (
          self.GetMessage('ResourceRuntimeSpec')(
              serviceAccountSpec=self.GetMessage('ServiceAccountSpec')(
                  enableCustomServiceAccount=True,
                  serviceAccount=service_account)))

    if self._version == constants.BETA_VERSION:
      return self._service.Create(
          self._messages.AiplatformProjectsLocationsPersistentResourcesCreateRequest(
              parent=parent,
              googleCloudAiplatformV1beta1PersistentResource=persistent_resource,
              persistentResourceId=persistent_resource_id,
          )
      )
    else:
      raise errors.ArgumentError('Persistent Resource is unsupported in GA.')

  def List(self, limit=None, region=None):
    """Constructs a list request and sends it to the Persistent Resources endpoint.

    Args:
      limit: How many items to return in the list
      region: Which region to list resources from

    Returns:
      A Persistent Resource list response message.

    """
    if self._version == constants.BETA_VERSION:
      return list_pager.YieldFromList(
          self._service,
          self._messages.AiplatformProjectsLocationsPersistentResourcesListRequest(
              parent=region
          ),
          field='persistentResources',
          batch_size_attribute='pageSize',
          limit=limit,
      )
    else:
      raise errors.ArgumentError('Persistent Resource is unsupported in GA.')

  def Get(self, name):
    if self._version == constants.BETA_VERSION:
      request = self._messages.AiplatformProjectsLocationsPersistentResourcesGetRequest(
          name=name
      )
      return self._service.Get(request)
    else:
      raise errors.ArgumentError('Persistent Resource is unsupported in GA.')

  def Delete(self, name):
    if self._version == constants.BETA_VERSION:
      request = self._messages.AiplatformProjectsLocationsPersistentResourcesDeleteRequest(
          name=name
      )
      return self._service.Delete(request)
    else:
      raise errors.ArgumentError('Persistent Resource is unsupported in GA.')

  def ImportResourceMessage(self, yaml_file, message_name):
    """Import a messages class instance typed by name from a YAML file."""
    data = console_io.ReadFromFileOrStdin(yaml_file, binary=False)
    message_type = self.GetMessage(message_name)
    return export_util.Import(message_type=message_type, stream=data)
