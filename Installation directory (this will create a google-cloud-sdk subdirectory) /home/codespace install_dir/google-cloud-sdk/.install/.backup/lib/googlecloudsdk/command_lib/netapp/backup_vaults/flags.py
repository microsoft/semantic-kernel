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
"""Flags and helpers for the Cloud NetApp Backup Vaults commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


BACKUP_VAULTS_LIST_FORMAT = """\
    table(
        name.basename():label=BACKUP_VAULT_NAME:sort=1,
        name.segment(3):label=LOCATION,
        state
    )"""


## Helper functions to combine Backup Vaults args / flags for gcloud commands ##


def AddBackupVaultCreateArgs(parser):
  """Add args for creating a Backup Vault."""
  concept_parsers.ConceptParser(
      [flags.GetBackupVaultPresentationSpec('The Backup Vault to create')]
  ).AddToParser(parser)
  flags.AddResourceDescriptionArg(parser, 'Backup Vault')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddCreateLabelsFlags(parser)


def AddBackupVaultDeleteArgs(parser):
  """Add args for deleting a Backup Vault."""
  concept_parsers.ConceptParser(
      [flags.GetBackupVaultPresentationSpec('The Backup Vault to delete')]
  ).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)


def AddBackupVaultUpdateArgs(parser):
  """Add args for updating a Backup Vault."""
  concept_parsers.ConceptParser(
      [flags.GetBackupVaultPresentationSpec('The Backup Vault to update')]
  ).AddToParser(parser)
  flags.AddResourceDescriptionArg(parser, 'Backup Vault')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddUpdateLabelsFlags(parser)

