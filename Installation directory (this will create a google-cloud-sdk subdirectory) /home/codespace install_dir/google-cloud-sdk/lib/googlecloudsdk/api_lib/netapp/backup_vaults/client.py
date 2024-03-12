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
"""Commands for interacting with the Cloud NetApp Files Backup Vaults API resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.netapp import constants
from googlecloudsdk.api_lib.netapp import util as netapp_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class BackupVaultsClient(object):
  """Wrapper for working with Backup Vaults in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    if release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaBackupVaultsAdapter()
    else:
      raise ValueError('[{}] is not a valid API version.'.format(
          netapp_util.VERSION_MAP[release_track]))

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def WaitForOperation(self, operation_ref):
    """Waits on the long-running operation until the done field is True.

    Args:
      operation_ref: The operation reference.

    Raises:
      waiter.OperationError: If the operation contains an error.

    Returns:
      The 'response' field of the Operation.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            self.client.projects_locations_operations
        ),
        operation_ref,
        'Waiting for [{0}] to finish'.format(operation_ref.Name()),
    )

  def CreateBackupVault(self, backupvault_ref, async_, backup_vault):
    """Create a Cloud NetApp Backup Vault."""
    request = self.messages.NetappProjectsLocationsBackupVaultsCreateRequest(
        parent=backupvault_ref.Parent().RelativeName(),
        backupVaultId=backupvault_ref.Name(),
        backupVault=backup_vault,
    )
    create_op = self.client.projects_locations_backupVaults.Create(request)
    if async_:
      return create_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseBackupVault(
      self, name=None, description=None, labels=None
  ):
    """Parses the command line arguments for Create BackupVault into a message.

    Args:
      name: The name of the Backup Vault.
      description: The description of the Backup Vault.
      labels: The parsed labels value.

    Returns:
      The configuration that will be used ass the request body for creating a
      Cloud NetApp Backup Vault.
    """
    backup_vault = self.messages.BackupVault()
    backup_vault.name = name
    backup_vault.description = description
    backup_vault.labels = labels
    return backup_vault

  def ListBackupVaults(self, location_ref, limit=None):
    """Make API calls to List Cloud NetApp Backup Vaults.

    Args:
      location_ref: The parsed location of the listed NetApp Backup Vaults.
      limit: The number of Cloud NetApp Backup Vaults to limit the results to.
        This limit is passed to the server and the server does the limiting.

    Returns:
      Generator that yields the Cloud NetApp Backup Vaults.
    """
    request = self.messages.NetappProjectsLocationsBackupVaultsListRequest(
        parent=location_ref)
    # Check for unreachable locations.
    response = self.client.projects_locations_backupVaults.List(request)
    for location in response.unreachable:
      log.warning('Location {} may be unreachable.'.format(location))
    return list_pager.YieldFromList(
        self.client.projects_locations_backupVaults,
        request,
        field=constants.BACKUP_VAULT_RESOURCE,
        limit=limit,
        batch_size_attribute='pageSize')

  def GetBackupVault(self, backupvault_ref):
    """Get Cloud NetApp Backup Vault information."""
    request = self.messages.NetappProjectsLocationsBackupVaultsGetRequest(
        name=backupvault_ref.RelativeName())
    return self.client.projects_locations_backupVaults.Get(request)

  def DeleteBackupVault(self, backupvault_ref, async_):
    """Deletes an existing Cloud NetApp Backup Vault."""
    request = (
        self.messages.NetappProjectsLocationsBackupVaultsDeleteRequest(
            name=backupvault_ref.RelativeName()
        )
    )
    return self._DeleteBackupVault(async_, request)

  def _DeleteBackupVault(self, async_, request):
    delete_op = self.client.projects_locations_backupVaults.Delete(request)
    if async_:
      return delete_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        delete_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def UpdateBackupVault(
      self, backupvault_ref, backup_vault, update_mask, async_
  ):
    """Updates a Backup Vault.

    Args:
      backupvault_ref: The reference to the backup vault.
      backup_vault: Backup Vault message, the updated backup vault.
      update_mask: A comma-separated list of updated fields.
      async_: If False, wait for the operation to complete.

    Returns:
      An Operation or Backup Vault message.
    """
    update_op = self._adapter.UpdateBackupVault(
        backupvault_ref, backup_vault, update_mask
    )
    if async_:
      return update_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        update_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseUpdatedBackupVault(
      self, backup_vault, description=None, labels=None
  ):
    """Parses updates into an kms config."""
    return self._adapter.ParseUpdatedBackupVault(
        backup_vault=backup_vault,
        description=description,
        labels=labels,
    )


class BetaBackupVaultsAdapter(object):
  """Adapter for the Beta Cloud NetApp Files API for Backup Vaults."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_util.GetMessagesModule(
        release_track=self.release_track
    )

  def ParseUpdatedBackupVault(
      self, backup_vault, description=None, labels=None
  ):
    """Parses updates into a new Backup Vault."""
    if description is not None:
      backup_vault.description = description
    if labels is not None:
      backup_vault.labels = labels
    return backup_vault

  def UpdateBackupVault(self, backupvault_ref, backup_vault, update_mask):
    """Send a Patch request for the Cloud NetApp Backup Vault."""
    update_request = (
        self.messages.NetappProjectsLocationsBackupVaultsPatchRequest(
            backupVault=backup_vault,
            name=backupvault_ref.RelativeName(),
            updateMask=update_mask))
    return self.client.projects_locations_backupVaults.Patch(
        update_request
    )
