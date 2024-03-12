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
"""Updates a Cloud NetApp Volumes Backup Vaults."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_vaults import client as backupvaults_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.backup_vaults import flags as backupvaults_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update a Cloud NetApp Volumes Backup Vault."""

  detailed_help = {
      'DESCRIPTION': """\
          Updates a Backup Vault
          """,
      'EXAMPLES': """\
          The following command updates a Backup Vault instance named BACKUP_VAULT

              $ {command} BACKUP_VAULT --location=us-central1 --description="new description" --update-labels=newkey=newval

          To update a Backup Vault named BACKUP_VAULT asynchronously, run the following command:

              $ {command} BACKUP_VAULT --async --location=us-central1 --description="new description"  --update-labels=newkey=newval """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    backupvaults_flags.AddBackupVaultUpdateArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Backup Vaults in the current project."""
    backupvault_ref = args.CONCEPTS.backup_vault.Parse()
    client = backupvaults_client.BackupVaultsClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_backupvault = client.GetBackupVault(backupvault_ref)
    # Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.BackupVault.LabelsValue, orig_backupvault.labels
      ).GetOrNone()
    else:
      labels = None
    backup_vault = client.ParseUpdatedBackupVault(
        orig_backupvault,
        description=args.description,
        labels=labels,
    )

    updated_fields = []
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateBackupVault(
        backupvault_ref, backup_vault, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp backup-vaults list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated backup vault by listing all kms'
          ' configs:\n  $ {} '.format(command)
      )
    return result
