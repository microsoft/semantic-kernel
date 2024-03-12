# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Restores a backup of a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class RestoreBackup(base.Command):
  """Restores a backup of a Cloud SQL instance.

  DEPRECATED: This command is deprecated and will be removed.
  Use 'gcloud beta sql backups restore' instead.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID that will be restored.')
    parser.add_argument(
        '--backup-id',
        type=int,
        help='The ID of the backup run to restore from.')
    parser.add_argument(
        '--backup-instance',
        completer=flags.InstanceCompleter,
        help='The ID of the instance that the backup was taken from.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Restores a backup of a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the
      restoreBackup operation if the restoreBackup was successful.
    """
    validate.ValidateInstanceName(args.instance)
    console_io.PromptContinue(
        message=('All current data on the instance will be lost when the '
                 'backup is restored'),
        default=True,
        cancel_on_no=True)

    return self._HandleBackupId(args)

  def _HandleBackupId(self, args):
    """Restores a backup using v1beta4. The backup is specified with backup_id.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the
      restoreBackup operation if the restoreBackup was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    if not args.backup_instance:
      args.backup_instance = args.instance

    result_operation = sql_client.instances.RestoreBackup(
        sql_messages.SqlInstancesRestoreBackupRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            instancesRestoreBackupRequest=(
                sql_messages.InstancesRestoreBackupRequest(
                    restoreBackupContext=sql_messages.RestoreBackupContext(
                        backupRunId=args.backup_id,
                        instanceId=args.backup_instance,)))))

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project)

    if args.async_:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project, operation=operation_ref.operation))

    # TODO(b/37302484): Use standard gcloud poller instead of WaitForOperation
    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Restoring Cloud SQL instance')

    log.status.write('Restored [{instance}].\n'.format(instance=instance_ref))

    return None
