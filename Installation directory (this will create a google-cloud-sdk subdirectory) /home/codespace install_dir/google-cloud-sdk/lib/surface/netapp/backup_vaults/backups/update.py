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
"""Update a Cloud NetApp Backups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_vaults.backups import client as backups_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.backup_vaults.backups import flags as backups_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update a Cloud NetApp Backup."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Update a Cloud NetApp Backup and its specified parameters.
          """,
      'EXAMPLES': """\
          The following command updates a Backup named BACKUP and its specified parameters:

              $ {command} NAME --location=us-central1 --description="new description"
          """,
  }

  @staticmethod
  def Args(parser):
    """Add args for updating a Backup."""
    backups_flags.AddBackupUpdateArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Backup in the current project."""
    backup_ref = args.CONCEPTS.backup.Parse()

    client = backups_client.BackupsClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    original_backup = client.GetBackup(backup_ref)

    # Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.Backup.LabelsValue, original_backup.labels
      ).GetOrNone()
    else:
      labels = None

    backup = client.ParseUpdatedBackup(
        original_backup, description=args.description, labels=labels,
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

    result = client.UpdateBackup(
        backup_ref, backup, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp backup-vaults backups list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated backup by listing all'
          ' backups:\n  $ {} '.format(command)
      )
    return result

