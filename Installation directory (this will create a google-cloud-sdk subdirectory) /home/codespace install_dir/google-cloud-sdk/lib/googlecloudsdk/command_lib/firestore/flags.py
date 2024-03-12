# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the firestore related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers


def AddCollectionIdsFlag(parser):
  """Adds flag for collection ids to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--collection-ids',
      metavar='COLLECTION_IDS',
      type=arg_parsers.ArgList(),
      help="""
      List specifying which collections will be included in the operation.
      When omitted, all collections are included.

      For example, to operate on only the `customers` and `orders`
      collections:

        $ {command} --collection-ids='customers','orders'
      """,
  )


def AddDatabaseIdFlag(parser, required=False):
  """Adds flag for database id to the given parser.

  Args:
    parser: The argparse parser.
    required: Whether the flag must be set for running the command, a bool.
  """
  if not required:
    helper_text = """\
      The database to operate on. The default value is `(default)`.

      For example, to operate on database `foo`:

        $ {command} --database='foo'
      """
  else:
    helper_text = """\
      The database to operate on.

      For example, to operate on database `foo`:

        $ {command} --database='foo'
      """
  parser.add_argument(
      '--database',
      metavar='DATABASE',
      type=str,
      default='(default)' if not required else None,
      required=required,
      help=helper_text,
  )


def AddNamespaceIdsFlag(parser):
  """Adds flag for namespace ids to the given parser."""
  parser.add_argument(
      '--namespace-ids',
      metavar='NAMESPACE_IDS',
      type=arg_parsers.ArgList(),
      help="""
      List specifying which namespaces will be included in the operation.
      When omitted, all namespaces are included.

      This is only supported for Datastore Mode databases.

      For example, to operate on only the `customers` and `orders` namespaces:

        $ {command} --namespaces-ids='customers','orders'
      """,
  )


def AddSnapshotTimeFlag(parser):
  """Adds flag for snapshot time to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--snapshot-time',
      metavar='SNAPSHOT_TIME',
      type=str,
      default=None,
      required=False,
      help="""
      The version of the database to export.

      The timestamp must be in the past, rounded to the minute and not older
      than `earliestVersionTime`. If specified, then the exported documents will
      represent a consistent view of the database at the provided time.
      Otherwise, there are no guarantees about the consistency of the exported
      documents.

      For example, to operate on snapshot time `2023-05-26T10:20:00.00Z`:

        $ {command} --snapshot-time='2023-05-26T10:20:00.00Z'
      """,
  )


def AddLocationFlag(
    parser, required=False, hidden=False, suggestion_aliases=None
):
  """Adds flag for location to the given parser.

  Args:
    parser: The argparse parser.
    required: Whether the flag must be set for running the command, a bool.
    hidden: Whether the flag is hidden in document. a bool.
    suggestion_aliases: A list of flag name aliases. A list of string.
  """
  parser.add_argument(
      '--location',
      metavar='LOCATION',
      required=required,
      hidden=hidden,
      type=str,
      suggestion_aliases=suggestion_aliases,
      help="""
      The location to operate on. Available locations are listed at
      https://cloud.google.com/firestore/docs/locations.

      For example, to operate on location `us-east1`:

        $ {command} --location='us-east1'
      """,
  )


def AddBackupFlag(parser):
  """Adds flag for backup to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--backup',
      metavar='BACKUP',
      required=True,
      type=str,
      help="""
      The backup to operate on.

      For example, to operate on backup `cf9f748a-7980-4703-b1a1-d1ffff591db0`:

        $ {command} --backup='cf9f748a-7980-4703-b1a1-d1ffff591db0'
      """,
  )


def AddBackupScheduleFlag(parser):
  """Adds flag for backup schedule id to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--backup-schedule',
      metavar='BACKUP_SCHEDULE',
      required=True,
      type=str,
      help="""
      The backup schedule to operate on.

      For example, to operate on backup schedule `091a49a0-223f-4c98-8c69-a284abbdb26b`:

        $ {command} --backup-schedule='091a49a0-223f-4c98-8c69-a284abbdb26b'
      """,
  )


def AddRetentionFlag(parser, required=False):
  """Adds flag for retention to the given parser.

  Args:
    parser: The argparse parser.
    required: Whether the flag must be set for running the command, a bool.
  """
  parser.add_argument(
      '--retention',
      metavar='RETENTION',
      required=required,
      type=arg_parsers.Duration(),
      help=textwrap.dedent("""\
          The rention of the backup. At what relative time in the future,
          compared to the creation time of the backup should the backup be
          deleted, i.e. keep backups for 7 days.

          For example, to set retention as 7 days.

          $ {command} --retention=7d
          """),
  )


def AddRecurrenceFlag(parser):
  """Adds flag for recurrence to the given parser.

  Args:
    parser: The argparse parser.
  """
  group = parser.add_group(
      help='Recurrence settings of a backup schedule.',
      required=True,
  )
  help_text = """\
      The recurrence settings of a backup schedule.

      Currently only daily and weekly backup schedules are supported.

      When a weekly backup schedule is created, day-of-week is needed.

      For example, to create a weekly backup schedule which creates backups on
      Monday.

        $ {command} --recurrence=weekly --day-of-week=MON
  """
  group.add_argument('--recurrence', type=str, help=help_text, required=True)

  help_text = """\
     The day of week (UTC time zone) of when backups are created.

      The available values are: `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`,`SUN`.
      Values are case insensitive.

      This is required when creating a weekly backup schedule.
  """
  group.add_argument(
      '--day-of-week',
      choices=arg_parsers.DayOfWeek.DAYS,
      type=arg_parsers.DayOfWeek.Parse,
      help=help_text,
      required=False,
  )
