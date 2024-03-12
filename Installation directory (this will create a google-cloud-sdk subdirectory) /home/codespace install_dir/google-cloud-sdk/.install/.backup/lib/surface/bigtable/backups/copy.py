# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""bigtable backups copy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import backups
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log


class Copy(base.Command):
  """Copy a Cloud Bigtable backup to a new backup."""
  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""
          This command creates a copy of a Cloud Bigtable backup.
          """),
      'EXAMPLES': textwrap.dedent("""\
        To copy a backup within the same project, run:

          $ {command} --source-instance=SOURCE_INSTANCE --source-cluster=SOURCE_CLUSTER  --source-backup=SOURCE_BACKUP --destination-instance=DESTINATION_INSTANCE --destination-cluster=DESTINATION_CLUSTER --destination-backup=DESTINATION_BACKUP --expiration-date=2023-09-01T10:49:41Z

        To copy a backup to a different project, run:

          $ {command} --source-backup=projects/SOURCE_PROJECT/instances/SOURCE_INSTANCE/clusters/SOURCE_CLUSTER/backups/SOURCE_BACKUP --destination-backup=projects/DESTINATION_PROJECT/instances/DESTINATION_INSTANCE/clusters/DESTINATION_CLUSTER/backups/DESTINATION_BACKUP --expiration-date=2022-08-01T10:49:41Z

        To set retention period and run asyncronously, run:

          $ {command} --source-backup=projects/SOURCE_PROJECT/instances/SOURCE_INSTANCE/clusters/SOURCE_CLUSTER/backups/SOURCE_BACKUP --destination-backup=projects/DESTINATION_PROJECT/instances/DESTINATION_INSTANCE/clusters/DESTINATION_CLUSTER/backups/DESTINATION_BACKUP --retention-period=2w --async

        """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""

    arguments.AddCopyBackupResourceArgs(parser)
    group_parser = parser.add_argument_group(mutex=True, required=True)
    group_parser.add_argument(
        '--expiration-date',
        help=(
            'Expiration time of the backup, must be at least 6 hours and at '
            'most 30 days from the time the source backup is created. See '
            '`$ gcloud topic datetimes` for information on date/time formats.'
        ),
    )
    group_parser.add_argument(
        '--retention-period',
        help=(
            'Retention period of the backup relative from now, must be at least'
            ' 6 hours and at most 30 days from the time the source backup is'
            ' created. See `$ gcloud topic datetimes` for information on'
            ' duration formats.'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    source_backup_ref = args.CONCEPTS.source.Parse()
    destination_backup_ref = args.CONCEPTS.destination.Parse()
    op = backups.CopyBackup(source_backup_ref, destination_backup_ref, args)

    operation_ref = util.GetOperationRef(op)
    if args.async_:
      log.status.Print('Copy request issued from [{}] to [{}]\n'
                       'Check operation [{}] for status.'.format(
                           source_backup_ref.RelativeName(),
                           destination_backup_ref.RelativeName(), op.name))
      return op

    op_result = util.AwaitBackup(
        operation_ref, 'Waiting for operation [{}] to complete'.format(op.name))
    if op.error is None:
      log.CreatedResource(op_result)
    return op_result
