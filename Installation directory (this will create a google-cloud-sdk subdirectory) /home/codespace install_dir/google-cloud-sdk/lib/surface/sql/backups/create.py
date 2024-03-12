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
"""Creates a backup of a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import instances as command_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class CreateBackup(base.CreateCommand):
  """Creates a backup of a Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.AddInstance(parser)
    flags.AddProjectLevelBackupEndpoint(parser)
    parser.add_argument(
        '--description', help='A friendly description of the backup.')
    parser.add_argument(
        '--location',
        help=('Choose where to store your backup. Backups are stored in the '
              'closest multi-region location to you by default. Only '
              'customize if needed.'))
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """Restores a backup of a Cloud SQL instance.

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

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    # Check if instance has customer-managed key; show warning if so.
    try:
      instance_resource = sql_client.instances.Get(
          sql_messages.SqlInstancesGetRequest(
              project=instance_ref.project, instance=instance_ref.instance))
      if instance_resource.diskEncryptionConfiguration:
        command_util.ShowCmekWarning('backup', 'this instance')
    except apitools_exceptions.HttpError:
      # This is for informational purposes, so don't throw an error if failure.
      pass

    if args.project_level:
      result_operation = sql_client.backups.CreateBackup(
          sql_messages.SqlBackupsCreateBackupRequest(
              parent='projects/'+instance_ref.project,
              backup=sql_messages.Backup(
                  description=args.description,
                  instance=instance_ref.instance,
                  location=args.location,
                  kind='sql#backup',
              ),
          )
      )
    else:
      result_operation = sql_client.backupRuns.Insert(
          sql_messages.SqlBackupRunsInsertRequest(
              project=instance_ref.project,
              instance=instance_ref.instance,
              backupRun=sql_messages.BackupRun(
                  description=args.description,
                  instance=instance_ref.instance,
                  location=args.location,
                  kind='sql#backupRun',
              ),
          )
      )

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project)

    if args.async_:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project, operation=operation_ref.operation))

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Backing up Cloud SQL instance')

    log.status.write('[{instance}] backed up.\n'.format(instance=instance_ref))

    return None
