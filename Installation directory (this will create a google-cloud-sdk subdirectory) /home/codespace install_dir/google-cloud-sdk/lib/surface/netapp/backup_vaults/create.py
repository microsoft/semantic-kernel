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
"""Create a Cloud NetApp Backup Vault."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_vaults import client as backupvaults_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.backup_vaults import flags as backupvaults_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a Cloud NetApp Backup Vault."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Create a Cloud NetApp Backup Vault.
          """,
      'EXAMPLES': """\
          The following command creates a Backup Vault named BACKUP_VAULT asynchronously using the specified arguments:

              $ {command} BACKUP_VAULT --location=LOCATION --async --description="test"
          """,
  }

  @staticmethod
  def Args(parser):
    backupvaults_flags.AddBackupVaultCreateArgs(parser)

  def Run(self, args):
    """Create a Cloud NetApp Backup Vault in the current project."""
    backupvault_ref = args.CONCEPTS.backup_vault.Parse()
    client = backupvaults_client.BackupVaultsClient(self._RELEASE_TRACK)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.BackupVault.LabelsValue
    )
    backup_vault = client.ParseBackupVault(
        name=backupvault_ref.RelativeName(),
        description=args.description,
        labels=labels,
    )
    result = client.CreateBackupVault(
        backupvault_ref, args.async_, backup_vault
    )
    if args.async_:
      command = 'gcloud {} netapp backup-vaults list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the new backup vault by listing all backup'
          ' vaults:\n  $ {} '.format(command)
      )
    return result
