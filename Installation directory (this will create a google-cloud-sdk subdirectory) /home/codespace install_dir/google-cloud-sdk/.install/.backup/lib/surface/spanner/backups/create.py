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
"""Command for spanner backup create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import backup_operations
from googlecloudsdk.api_lib.spanner import backups
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Creates a backup of a Cloud Spanner database.

  Creates a backup of a Cloud Spanner database.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To create a backup asynchronously, run:

          $ {command} BACKUP_ID --instance=INSTANCE_NAME --database=DATABASE --expiration-date=2020-03-29T10:49:41Z --async

        To create a backup synchronously, run:

          $ {command} BACKUP_ID --instance=INSTANCE_NAME --database=DATABASE --retention-period=2w
        """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""

    resource_args.AddBackupResourceArg(parser, 'to create')
    parser.add_argument(
        '--database',
        required=True,
        help='ID of the database from which the backup will be created.')

    group_parser = parser.add_argument_group(mutex=True, required=True)
    group_parser.add_argument(
        '--expiration-date',
        help='Expiration time of the backup, must be at least 6 hours and at '
        'most 30 days from the time the request is received. See '
        '`$ gcloud topic datetimes` for information on date/time formats.')
    group_parser.add_argument(
        '--retention-period',
        help='Retention period of the backup relative from now, must be at '
        'least 6 hours and at most 30 days. See `$ gcloud topic '
        'datetimes` for information on duration formats.')

    parser.add_argument(
        '--version-time',
        metavar='TIMESTAMP',
        help='The backup will contain an externally consistent copy of the '
        'database at the timestamp specified by `--version-time`. If '
        '`--version-time` is not specified, the system will use the creation '
        'time of the backup.')

    base.ASYNC_FLAG.AddToParser(parser)
    encryption_group_parser = parser.add_argument_group()
    resource_args.AddCreateBackupEncryptionTypeArg(encryption_group_parser)
    resource_args.AddKmsKeyResourceArg(encryption_group_parser,
                                       'to create the Cloud Spanner backup')

  def Run(self, args):
    """This is what gets called when the user runs this command."""

    backup_ref = args.CONCEPTS.backup.Parse()
    encryption_type = resource_args.GetCreateBackupEncryptionType(args)
    kms_key = resource_args.GetAndValidateKmsKeyName(args)
    op = backups.CreateBackup(backup_ref, args, encryption_type, kms_key)
    if args.async_:
      log.status.Print('Create request issued for: [{}]\n'
                       'Check operation [{}] for status.'.format(
                           args.backup, op.name))
      return op

    op_result = backup_operations.Await(
        op, 'Waiting for operation [{}] to complete'.format(op.name))
    if op.error is None:
      log.CreatedResource(op_result)
    return op_result
