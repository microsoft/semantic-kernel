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
"""Command for spanner backup copy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import backup_operations
from googlecloudsdk.api_lib.spanner import backups
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.core import log


class Copy(base.Command):
  """Copies a backup of a Cloud Spanner database."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To copy a backup within the same project, run:

          $ {command} --source-instance=SOURCE_INSTANCE_ID --source-backup=SOURCE_BACKUP_ID  --destination-instance=DESTINATION_INSTANCE_ID --destination-backup=DESTINATION_BACKUP_ID --expiration-date=2020-03-29T10:49:41Z

        To copy a backup to a different project, run:

          $ {command} --source-backup=projects/SOURCE_PROJECT_ID/instances/SOURCE_INSTANCE_ID/backups/SOURCE_BACKUP_ID --destination-backup=projects/DESTINATION_PROJECT_ID/instances/DESTINATION_INSTANCE_ID/backups/DESTINATION_BACKUP_ID --expiration-date=2020-03-29T10:49:41Z

        """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""

    resource_args.AddCopyBackupResourceArgs(parser)
    group_parser = parser.add_argument_group(mutex=True, required=True)
    group_parser.add_argument(
        '--expiration-date',
        help='Expiration time of the backup, must be at least 6 hours and at '
        'most 366 days from the time when the source backup is created. See '
        '`$ gcloud topic datetimes` for information on date/time formats.')
    group_parser.add_argument(
        '--retention-period',
        help='Retention period of the backup relative from now, must be at '
        'least 6 hours and at most 366 days from the time when the source '
        'backup is created. See `$ gcloud topic datetimes` for information '
        'on duration formats.')
    base.ASYNC_FLAG.AddToParser(parser)
    encryption_group_parser = parser.add_argument_group()
    resource_args.AddCopyBackupEncryptionTypeArg(encryption_group_parser)
    resource_args.AddKmsKeyResourceArg(encryption_group_parser,
                                       'to copy the Cloud Spanner backup')

  def Run(self, args):
    """This is what gets called when the user runs this command."""

    source_backup_ref = args.CONCEPTS.source.Parse()
    destination_backup_ref = args.CONCEPTS.destination.Parse()
    encryption_type = resource_args.GetCopyBackupEncryptionType(args)
    kms_key = resource_args.GetAndValidateKmsKeyName(args)
    op = backups.CopyBackup(source_backup_ref, destination_backup_ref, args,
                            encryption_type, kms_key)
    if args.async_:
      log.status.Print('Copy request issued from [{}] to [{}]\n'
                       'Check operation [{}] for status.'.format(
                           source_backup_ref.RelativeName(),
                           destination_backup_ref.RelativeName(), op.name))
      return op

    op_result = backup_operations.Await(
        op, 'Waiting for operation [{}] to complete'.format(op.name))
    if op.error is None:
      log.CreatedResource(op_result)
    return op_result
