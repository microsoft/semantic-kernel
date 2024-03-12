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
"""Create a Cloud NetApp Backup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_vaults.backups import client as backups_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.backup_vaults.backups import flags as backups_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a Cloud NetApp Backup."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Create a Cloud NetApp Backup.
          """,
      'EXAMPLES': """\
          The following command creates a Backup named BACKUP attached to a Backup Vault named BACKUP_VAULT, and a source volume named SOURCE_VOL asynchronously using the specified arguments:

              $ {command} BACKUP --location=LOCATION --async --backup-vault=BACKUP_VAULT --source-volume=SOURCE_VOL
          """,
  }

  @staticmethod
  def Args(parser):
    backups_flags.AddBackupCreateArgs(parser)

  def Run(self, args):
    """Create a Cloud NetApp Backup in the current project."""
    backup_ref = args.CONCEPTS.backup.Parse()
    client = backups_client.BackupsClient(self._RELEASE_TRACK)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.Backup.LabelsValue
    )
    backup = client.ParseBackup(
        name=backup_ref.RelativeName(),
        source_volume=args.source_volume,
        source_snapshot=args.source_snapshot,
        description=args.description,
        labels=labels,
    )
    result = client.CreateBackup(backup_ref, args.async_, backup)
    if args.async_:
      command = 'gcloud {} netapp backup-vaults backups list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the new backup by listing all backups:\n  $ {} '
          .format(command)
      )
    return result
