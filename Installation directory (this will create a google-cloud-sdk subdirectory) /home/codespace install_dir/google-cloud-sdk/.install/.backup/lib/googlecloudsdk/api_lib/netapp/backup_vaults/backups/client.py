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
"""Commands for interacting with the Cloud NetApp Files Backups API resource."""

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


class BackupsClient(object):
  """Wrapper for working with Backups in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    if release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaBackupsAdapter()
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

    Returns:
      The 'response' field of the Operation.

    Raises:
      waiter.OperationError: If the operation contains an error.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            self.client.projects_locations_operations
        ),
        operation_ref,
        'Waiting for [{0}] to finish'.format(operation_ref.Name()),
    )

  def CreateBackup(self, backup_ref, async_, backup):
    """Create a Cloud NetApp Backup."""
    request = (
        self.messages.NetappProjectsLocationsBackupVaultsBackupsCreateRequest(
            parent=backup_ref.Parent().RelativeName(),
            backupId=backup_ref.Name(),
            backup=backup,
        )
    )
    create_op = self.client.projects_locations_backupVaults_backups.Create(
        request
    )
    if async_:
      return create_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseBackup(
      self,
      name=None,
      source_snapshot=None,
      source_volume=None,
      description=None,
      labels=None,
  ):
    """Parses the command line arguments for Create Backup into a message.

    Args:
      name: The name of the Backup.
      source_snapshot: The Source Snapshot of the Backup.
      source_volume: The Source Volume of the Backup.
      description: The description of the Backup.
      labels: The parsed labels value.

    Returns:
      The configuration that will be used ass the request body for creating a
      Cloud NetApp Backup.
    """
    backup = self.messages.Backup()
    backup.name = name
    backup.sourceSnapshot = source_snapshot
    backup.sourceVolume = source_volume
    backup.description = description
    backup.labels = labels
    return backup

  def ListBackups(self, backupvault_ref, limit=None):
    """Make API calls to List Cloud NetApp Backups.

    Args:
      backupvault_ref: The parsed Backup Vault of the listed NetApp Backups.
      limit: The number of Cloud NetApp Backups to limit the results to.
        This limit is passed to the server and the server does the limiting.

    Returns:
      Generator that yields the Cloud NetApp Backups.
    """
    request = (
        self.messages.NetappProjectsLocationsBackupVaultsBackupsListRequest(
            parent=backupvault_ref
        )
    )
    # Check for unreachable locations.
    response = self.client.projects_locations_backupVaults_backups.List(request)
    for location in response.unreachable:
      log.warning('Location {} may be unreachable.'.format(location))
    return list_pager.YieldFromList(
        self.client.projects_locations_backupVaults_backups,
        request,
        field=constants.BACKUP_RESOURCE,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def GetBackup(self, backup_ref):
    """Get Cloud NetApp Backup information."""
    request = (
        self.messages.NetappProjectsLocationsBackupVaultsBackupsGetRequest(
            name=backup_ref.RelativeName()
        )
    )
    return self.client.projects_locations_backupVaults_backups.Get(request)

  def DeleteBackup(self, backup_ref, async_):
    """Deletes an existing Cloud NetApp Backup."""
    request = (
        self.messages.NetappProjectsLocationsBackupVaultsBackupsDeleteRequest(
            name=backup_ref.RelativeName()
        )
    )
    return self._DeleteBackup(async_, request)

  def _DeleteBackup(self, async_, request):
    delete_op = self.client.projects_locations_backupVaults_backups.Delete(
        request
    )
    if async_:
      return delete_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        delete_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def UpdateBackup(
      self, backup_ref, backup, update_mask, async_
  ):
    """Updates a Backup.

    Args:
      backup_ref: The reference to the Backup.
      backup: Backup message, the updated Backup.
      update_mask: str, a comma-separated list of updated fields.
      async_: bool, if False, wait for the operation to complete.

    Returns:
      an Operation or Backup Vault message.
    """
    update_op = self._adapter.UpdateBackup(
        backup_ref, backup, update_mask
    )
    if async_:
      return update_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        update_op.name, collection=constants.OPERATIONS_COLLECTION
    )
    return self.WaitForOperation(operation_ref)

  def ParseUpdatedBackup(
      self,
      backup,
      description=None,
      labels=None,
  ):
    """Parses updates into a Backup."""
    return self._adapter.ParseUpdatedBackup(
        backup,
        description=description,
        labels=labels,
    )


class BetaBackupsAdapter(object):
  """Adapter for the Beta Cloud NetApp Files API for Backups."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_util.GetMessagesModule(
        release_track=self.release_track
    )

  def ParseUpdatedBackup(
      self,
      backup,
      description=None,
      labels=None,
  ):
    """Parses updates into a new Backup."""
    if description is not None:
      backup.description = description
    if labels is not None:
      backup.labels = labels
    return backup

  def UpdateBackup(self, backup_ref, backup, update_mask):
    """Send a Patch request for the Cloud NetApp Backup."""
    update_request = (
        self.messages.NetappProjectsLocationsBackupVaultsBackupsPatchRequest(
            backup=backup,
            name=backup_ref.RelativeName(),
            updateMask=update_mask))
    update_op = self.client.projects_locations_backupVaults_backups.Patch(
        update_request)
    return update_op
