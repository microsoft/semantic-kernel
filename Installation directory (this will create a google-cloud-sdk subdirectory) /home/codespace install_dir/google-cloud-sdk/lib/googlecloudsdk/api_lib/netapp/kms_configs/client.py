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
"""Commands for interacting with the Cloud NetApp Files KMS Config API resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.netapp import constants
from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class KmsConfigsClient(object):
  """Wrapper for working with KMS Configs in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    if release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaKmsConfigsAdapter()
    elif release_track == base.ReleaseTrack.GA:
      self._adapter = KmsConfigsAdapter()
    else:
      raise ValueError('[{}] is not a valid API version.'.format(
          netapp_api_util.VERSION_MAP[release_track]))

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def WaitForOperation(self, operation_ref):
    """Waits on the long-running operation until the done field is True.

    Args:
      operation_ref: the operation reference.

    Raises:
      waiter.OperationError: if the operation contains an error.

    Returns:
      the 'response' field of the Operation.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            self.client.projects_locations_operations
        ),
        operation_ref,
        'Waiting for [{0}] to finish'.format(operation_ref.Name()),
    )

  def CreateKmsConfig(self, kmsconfig_ref, async_, kms_config):
    """Create a Cloud NetApp KMS Config."""
    request = self.messages.NetappProjectsLocationsKmsConfigsCreateRequest(
        parent=kmsconfig_ref.Parent().RelativeName(),
        kmsConfigId=kmsconfig_ref.Name(),
        kmsConfig=kms_config,
    )
    create_op = self.client.projects_locations_kmsConfigs.Create(request)
    if async_:
      return create_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseKmsConfig(
      self, name=None, crypto_key_name=None, description=None, labels=None
  ):
    """Parses the command line arguments for Create KMS Config into a message.

    Args:
      name: the name of the KMS Config
      crypto_key_name: the crypto key name of the KMS Config
      description: the description of the KMS COnfig
      labels: the parsed labels value

    Returns:
      The configuration that will be used as the request body for creating a
      Cloud NetApp KMS Config.
    """
    kms_config = self.messages.KmsConfig()
    kms_config.name = name
    kms_config.cryptoKeyName = crypto_key_name
    kms_config.description = description
    kms_config.labels = labels
    return kms_config

  def ListKmsConfigs(self, location_ref, limit=None):
    """Make API calls to List Cloud NetApp KMS Configs.

    Args:
      location_ref: The parsed location of the listed NetApp KMS Configs.
      limit: The number of Cloud NetApp KMS Configs to limit the results to.
        This limit is passed to the server and the server does the limiting.

    Returns:
      Generator that yields the Cloud NetApp KMS Config.
    """
    request = self.messages.NetappProjectsLocationsKmsConfigsListRequest(
        parent=location_ref)
    # Check for unreachable locations.
    response = self.client.projects_locations_kmsConfigs.List(request)
    for location in response.unreachable:
      log.warning('Location {} may be unreachable.'.format(location))
    return list_pager.YieldFromList(
        self.client.projects_locations_kmsConfigs,
        request,
        field=constants.KMS_CONFIG_RESOURCE,
        limit=limit,
        batch_size_attribute='pageSize')

  def GetKmsConfig(self, kmsconfig_ref):
    """Get Cloud NetApp KMS Config information."""
    request = self.messages.NetappProjectsLocationsKmsConfigsGetRequest(
        name=kmsconfig_ref.RelativeName())
    return self.client.projects_locations_kmsConfigs.Get(request)

  def DeleteKmsConfig(self, kmsconfig_ref, async_):
    """Deletes an existing Cloud NetApp KMS Config."""
    request = (
        self.messages.NetappProjectsLocationsKmsConfigsDeleteRequest(
            name=kmsconfig_ref.RelativeName()
        )
    )
    return self._DeleteKmsConfig(async_, request)

  def _DeleteKmsConfig(self, async_, request):
    delete_op = self.client.projects_locations_kmsConfigs.Delete(request)
    if async_:
      return delete_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        delete_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def UpdateKmsConfig(self, kmsconfig_ref, kms_config, update_mask, async_):
    """Updates a KMS Config.

    Args:
      kmsconfig_ref: the reference to the kms config.
      kms_config: KMS Config message, the updated kms config.
      update_mask: str, a comma-separated list of updated fields.
      async_: bool, if False, wait for the operation to complete.

    Returns:
      an Operation or KMS Config message.
    """
    update_op = self._adapter.UpdateKmsConfig(kmsconfig_ref,
                                              kms_config, update_mask)
    if async_:
      return update_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        update_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)

  def ParseUpdatedKmsConfig(self,
                            kms_config,
                            crypto_key_name,
                            description=None,
                            labels=None):
    """Parses updates into an kms config."""
    return self._adapter.ParseUpdatedKmsConfig(
        kms_config=kms_config,
        crypto_key_name=crypto_key_name,
        description=description,
        labels=labels)

  def EncryptKmsConfig(self, kmsconfig_ref, async_):
    """Encrypts the volumes attached to the Cloud NetApp KMS Config."""
    request = (
        self.messages.NetappProjectsLocationsKmsConfigsEncryptRequest(
            name=kmsconfig_ref.RelativeName()
        )
    )
    encrypt_op = self.client.projects_locations_kmsConfigs.Encrypt(request)
    if async_:
      return encrypt_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        encrypt_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)

  def VerifyKmsConfig(self, kmsconfig_ref):
    """Verifies the Cloud NetApp Volumes KMS Config is reachable."""
    request = (
        self.messages.NetappProjectsLocationsKmsConfigsVerifyRequest(
            name=kmsconfig_ref.RelativeName()
        )
    )
    return self.client.projects_locations_kmsConfigs.Verify(
        request
    )


class KmsConfigsAdapter(object):
  """Adapter for the Cloud NetApp Files API for KMS Configs."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.GA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )

  def ParseUpdatedKmsConfig(
      self, kms_config, crypto_key_name=None, description=None, labels=None
  ):
    """Parses updates into a new kms config."""
    if crypto_key_name is not None:
      kms_config.cryptoKeyName = crypto_key_name
    if description is not None:
      kms_config.description = description
    if labels is not None:
      kms_config.labels = labels
    return kms_config

  def UpdateKmsConfig(self, kmsconfig_ref, kms_config, update_mask):
    """Send a Patch request for the Cloud NetApp KMS Config."""
    update_request = (
        self.messages.NetappProjectsLocationsKmsConfigsPatchRequest(
            kmsConfig=kms_config,
            name=kmsconfig_ref.RelativeName(),
            updateMask=update_mask))
    update_op = self.client.projects_locations_kmsConfigs.Patch(
        update_request)
    return update_op


class BetaKmsConfigsAdapter(KmsConfigsAdapter):
  """Adapter for the Beta Cloud NetApp Files API for KMS Configs."""

  def __init__(self):
    super(BetaKmsConfigsAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )
