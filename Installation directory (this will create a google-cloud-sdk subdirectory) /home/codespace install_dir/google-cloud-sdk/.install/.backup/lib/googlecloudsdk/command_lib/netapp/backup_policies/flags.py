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
"""Flags and helpers for the Cloud NetApp Files Backup Policies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp import util as netapp_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


BACKUP_POLICIES_LIST_FORMAT = """\
    table(
        name.basename():label=BACKUP_POLICY_NAME:sort=1,
        name.segment(3):label=LOCATION,
        enabled,
        state
    )"""

MIN_DAILY_BACKUP_LIMIT = 2

## Helper functions to add args / flags for Backup Policy gcloud commands ##


def AddBackupPolicyEnabledArg(parser):
  """Adds a --enabled arg to the given parser."""
  parser.add_argument(
      '--enabled',
      type=arg_parsers.ArgBoolean(truthy_strings=netapp_util.truthy,
                                  falsey_strings=netapp_util.falsey),
      help="""The Boolean value indiciating whether backups are made automatically according to the schedules.
      If enabled, this will be applied to all volumes that have this backup policy attached and enforced on
      the volume level. If not specified, the default is true."""
  )


def AddBackupPolicyDailyBackupLimitArg(backup_limit_group):
  """Adds a --daily-backup-limit arg to the given parser argument group."""
  backup_limit_group.add_argument(
      '--daily-backup-limit',
      type=arg_parsers.BoundedInt(
          lower_bound=MIN_DAILY_BACKUP_LIMIT, upper_bound=sys.maxsize),
      help="""
          Maximum number of daily backups to keep.
          Note that the minimum daily backup limit is 2.
          """,
  )


def AddBackupPolicyWeeklyBackupLimitArg(backup_limit_group):
  """Adds a --weekly-backup-limit arg to the given parser argument group."""
  backup_limit_group.add_argument(
      '--weekly-backup-limit',
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=sys.maxsize),
      help="""
          Number of weekly backups to keep.
          Note that the sum of daily, weekly and monthly backups
          should be greater than 1
          """,
  )


def AddBackupPolicyMonthlyBackupLimitArg(backup_limit_group):
  """Adds a --monthly-backup-limit arg to the given parser argument group."""
  backup_limit_group.add_argument(
      '--monthly-backup-limit',
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=sys.maxsize),
      help="""
          Number of monthly backups to keep.
          Note that the sum of daily, weekly and monthly backups
          should be greater than 1
          """,
  )


def AddBackupPolicyBackupLimitGroup(parser):
  """Adds a parser argument group for backup limits.

    Flags include:
    --daily-backup-limit
    --weekly-backup-limit
    --monthly-backup-limit

  Args:
    parser: The argparser.
  """
  backup_limit_group = parser.add_group(
      help='Add backup limit arguments.'
  )
  AddBackupPolicyDailyBackupLimitArg(backup_limit_group)
  AddBackupPolicyWeeklyBackupLimitArg(backup_limit_group)
  AddBackupPolicyMonthlyBackupLimitArg(backup_limit_group)

## Helper functions for Backup Policy surface command

## Helper functions to combine Backup Policy args / flags for gcloud commands ##


def AddBackupPolicyCreateArgs(parser):
  """Add args for creating a Backup Policy."""
  concept_parsers.ConceptParser(
      [flags.GetBackupPolicyPresentationSpec('The Backup Policy to create')]
  ).AddToParser(parser)
  AddBackupPolicyEnabledArg(parser)
  AddBackupPolicyBackupLimitGroup(parser)
  flags.AddResourceDescriptionArg(parser, 'Backup Policy')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddCreateLabelsFlags(parser)


def AddBackupPolicyDeleteArgs(parser):
  """Add args for deleting a Backup Policy."""
  concept_parsers.ConceptParser(
      [flags.GetBackupPolicyPresentationSpec('The Backup Policy to delete')]
  ).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)


def AddBackupPolicyUpdateArgs(parser):
  """Add args for updating a Backup Policy."""
  concept_parsers.ConceptParser(
      [flags.GetBackupPolicyPresentationSpec('The Backup Policy to update')]
  ).AddToParser(parser)
  AddBackupPolicyEnabledArg(parser)
  AddBackupPolicyBackupLimitGroup(parser)
  flags.AddResourceDescriptionArg(parser, 'Backup Policy')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddUpdateLabelsFlags(parser)


