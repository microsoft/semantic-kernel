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
"""Describe a Cloud NetApp Backup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_vaults.backups import client as backups_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.backup_vaults.backups import flags as backups_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(base.DescribeCommand):
  """Describe a Cloud NetApp Backup."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Describe a Cloud NetApp Backup.
          """,
      'EXAMPLES': """\
          The following command describes a Backup named BACKUP in the given location and backup vault:

              $ {command} NAME --location=us-central1 --backup-vault=BACKUP_VAULT
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [flags.GetBackupPresentationSpec('The Backup to describe.')]
    ).AddToParser(parser)
    backups_flags.AddBackupBackupVaultResourceArg(parser)

  def Run(self, args):
    """Get a Cloud NetApp Backup in the current project."""
    backup_ref = args.CONCEPTS.backup.Parse()

    client = backups_client.BackupsClient(
        release_track=self._RELEASE_TRACK
    )
    return client.GetBackup(backup_ref)


