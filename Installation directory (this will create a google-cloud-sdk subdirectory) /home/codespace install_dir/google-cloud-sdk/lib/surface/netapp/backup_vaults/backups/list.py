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
"""List Cloud NetApp Backups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_vaults.backups import client as backups_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.backup_vaults.backups import flags as backups_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  """List Cloud NetApp Backups."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Lists Cloud NetApp Backups.
          """,
      'EXAMPLES': """\
          The following command lists all Backups in the given location and Backup Vault named BACKUP_VAULT:

              $ {command} --location=us-central1 --backup-vault=BACKUP_VAULT
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [
            flags.GetResourceListingLocationPresentationSpec(
                'The location in which to list Backups.'
            )
        ]
    ).AddToParser(parser)
    backups_flags.AddBackupBackupVaultResourceArg(parser)

  def Run(self, args):
    """Run the list command."""
    # Ensure that project is set before parsing location resource.
    properties.VALUES.core.project.GetOrFail()

    if args.CONCEPTS.backup_vault.Parse() is None:
      raise exceptions.RequiredArgumentException(
          '--backup-vault', 'Requires a Backup Vault to list Backups of'
      )
    backupvault_ref = args.CONCEPTS.backup_vault.Parse().RelativeName()
    client = backups_client.BackupsClient(
        release_track=self._RELEASE_TRACK
    )
    return list(client.ListBackups(backupvault_ref))


