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
"""Delete a Cloud NetApp Backup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_vaults.backups import client as backups_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.backup_vaults.backups import flags as backups_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(base.DeleteCommand):
  """Delete a Cloud NetApp Backup."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Delete a Cloud NetApp Backup.
          """,
      'EXAMPLES': """\
          The following command deletes a Backup named BACKUP inside a backup vault named BACKUP_VAULT using the required arguments:

              $ {command} BACKUP --location=us-central1 --backup-vault=BACKUP_VAULT

          To delete a Backup named BACKUP asynchronously, run the following command:

              $ {command} BACKUP --location=us-central1 --backup-vault=BACKUP_VAULT --async
          """,
  }

  @staticmethod
  def Args(parser):
    """Add args for deleting a Backup."""
    concept_parsers.ConceptParser([
        flags.GetBackupPresentationSpec('The Backup to delete.')
    ]).AddToParser(parser)
    backups_flags.AddBackupBackupVaultResourceArg(parser)
    flags.AddResourceAsyncFlag(parser)

  def Run(self, args):
    """Delete a Cloud NetApp Backup in the current project."""
    backup_ref = args.CONCEPTS.backup.Parse()

    if not args.quiet:
      delete_warning = (
          'You are about to delete a Backup {}.\nAre you sure?'.format(
              backup_ref.RelativeName()
          )
      )
      if not console_io.PromptContinue(message=delete_warning):
        return None

    client = backups_client.BackupsClient(self._RELEASE_TRACK)
    result = client.DeleteBackup(backup_ref, args.async_)
    if args.async_:
      command = 'gcloud {} netapp backup-vaults backups list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the deletion by listing all backups:\n  '
          '$ {} '.format(command)
      )
    return result

