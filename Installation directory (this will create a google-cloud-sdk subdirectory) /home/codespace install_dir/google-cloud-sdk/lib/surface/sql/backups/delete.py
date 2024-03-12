# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Deletes a backup run for a Cloud SQL instance."""

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
class Delete(base.DeleteCommand):
  """Delete a backup of a Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddBackupId(parser)
    flags.AddOptionalInstance(parser)
    flags.AddProjectLevelBackupEndpoint(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """Deletes a backup of a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the api request was successful.
    """

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    operation_ref = None

    # TODO(b/36051078): validate on FE that a backup run id is valid.

    console_io.PromptContinue(
        message='The backup will be deleted. You cannot undo this action.',
        default=True,
        cancel_on_no=True,
    )
    if args.project_level:
      result = sql_client.backups.DeleteBackup(
          sql_messages.SqlBackupsDeleteBackupRequest(name=args.id)
      )
      operation_ref = client.resource_parser.Create(
          'sql.operations', operation=result.name, project=args.id.split('/')[1]
      )
    else:
      validate.ValidateInstanceName(args.instance)
      instance_ref = client.resource_parser.Parse(
          args.instance,
          params={'project': properties.VALUES.core.project.GetOrFail},
          collection='sql.instances',
      )
      result = sql_client.backupRuns.Delete(
          sql_messages.SqlBackupRunsDeleteRequest(
              project=instance_ref.project,
              instance=instance_ref.instance,
              id=int(args.id),
          )
      )
      operation_ref = client.resource_parser.Create(
          'sql.operations', operation=result.name, project=instance_ref.project
      )

    if args.async_:
      # Don't wait for the running operation to complete when async is used.
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project, operation=operation_ref.operation
          )
      )

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Deleting backup run'
    )

    log.DeletedResource(args.id, 'backup run')
