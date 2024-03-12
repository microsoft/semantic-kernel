# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for spanner restore database."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.core import log


class Restore(base.RestoreCommand):
  """Restore a Cloud Spanner database."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""
          Restores from a backup to a new Cloud Spanner database."""),
      'EXAMPLES':
          textwrap.dedent("""
          To restore a backup, run:

            $ {command} --source-backup=BACKUP_ID --source-instance=SOURCE_INSTANCE --destination-database=DATABASE --destination-instance=INSTANCE_NAME

          To restore a backup using relative names, run:

            $ {command} --source-backup=projects/PROJECT_ID/instances/SOURCE_INSTANCE_ID/backups/BACKUP_ID --destination-database=projects/PROJECT_ID/instances/SOURCE_INSTANCE_ID/databases/DATABASE_ID
      """)
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    resource_args.AddRestoreResourceArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    encryption_group_parser = parser.add_argument_group()
    resource_args.AddRestoreDbEncryptionTypeArg(encryption_group_parser)
    resource_args.AddKmsKeyResourceArg(encryption_group_parser,
                                       'to restore the Cloud Spanner database')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A message indicating database is restoring or when async, the operation.
    """
    backup_ref = args.CONCEPTS.source.Parse()
    database_ref = args.CONCEPTS.destination.Parse()
    encryption_type = resource_args.GetRestoreDbEncryptionType(args)
    kms_key = resource_args.GetAndValidateKmsKeyName(args)
    op = databases.Restore(database_ref, backup_ref, encryption_type, kms_key)

    if args.async_:
      return log.status.Print(
          'Restore database in progress. Operation name={}'.format(op.name))
    return database_operations.Await(
        op,
        'Restoring backup {0} to database {1}'.format(backup_ref.Name(),
                                                      database_ref.Name()))
