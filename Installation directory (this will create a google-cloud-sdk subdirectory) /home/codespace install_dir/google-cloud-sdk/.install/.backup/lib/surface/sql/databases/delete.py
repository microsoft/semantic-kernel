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
"""Deletes a database in a given instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Deletes a Cloud SQL database.

  For MySQL, also deletes all files in the database directory.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.AddInstance(parser)
    flags.AddDatabaseName(parser)
    parser.display_info.AddCacheUpdater(flags.DatabaseCompleter)

  def Run(self, args):
    """Deletes a Cloud SQL database.

    For MySQL, also deletes all files in the database directory.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      SQL database resource iterator.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    project_id = properties.VALUES.core.project.Get(required=True)

    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    console_io.PromptContinue(
        message='The database will be deleted. Any data stored in the database '
        'will be destroyed. You cannot undo this action.',
        default=True,
        cancel_on_no=True)

    result_operation = sql_client.databases.Delete(
        sql_messages.SqlDatabasesDeleteRequest(
            project=project_id, instance=args.instance, database=args.database))

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project)

    operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                  'Deleting Cloud SQL database')
    log.DeletedResource(args.database, 'database')
