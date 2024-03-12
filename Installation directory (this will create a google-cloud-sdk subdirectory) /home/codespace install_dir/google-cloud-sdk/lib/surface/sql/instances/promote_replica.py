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
"""Promotes Cloud SQL read replica to a stand-alone instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import instances
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class PromoteReplica(base.Command):
  """Promotes Cloud SQL read replica to a stand-alone instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'replica',
        completer=flags.InstanceCompleter,
        help='Cloud SQL read replica ID.')
    flags.AddFailoverFlag(parser)

  def Run(self, args):
    """Promotes Cloud SQL read replica to a stand-alone instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the
      promote-replica operation if the promote-replica was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.replica)
    instance_ref = client.resource_parser.Parse(
        args.replica,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    instance_resource = sql_client.instances.Get(
        sql_messages.SqlInstancesGetRequest(
            project=instance_ref.project, instance=instance_ref.instance))

    if instances.InstancesV1Beta4.IsMysqlDatabaseVersion(
        instance_resource.databaseVersion):
      database_type_fragment = 'mysql'
    elif instances.InstancesV1Beta4.IsPostgresDatabaseVersion(
        instance_resource.databaseVersion):
      database_type_fragment = 'postgres'
    else:
      # TODO(b/144067325): currently the link below goes to extremely
      # database-specific instructions to query the replication lag, so in case
      # we (...somehow...) end up here for a db other than mysql or postgres,
      # it's probably better to show nothing than to link to misleading info.
      # Once the metrics are made uniform in b/144067325, then we could default
      # to something here as we'd be giving the same instructions for all dbs
      # anyway.
      database_type_fragment = None
    promote_replica_docs_link = None
    if database_type_fragment:
      promote_replica_docs_link = (
          'Learn more:\n' +
          'https://cloud.google.com/sql/docs/{}/replication/manage-replicas#promote-replica\n\n'
          .format(database_type_fragment))

    # Format the message ourselves here rather than supplying it as part of the
    # 'message' to PromptContinue. Having the whole paragraph be automatically
    # formatted by PromptContinue would leave it with a line break in the middle
    # of the URL, rendering it unclickable.
    sys.stderr.write(textwrap.TextWrapper().fill(
        'Promoting a read replica stops replication and converts the instance '
        'to a standalone primary instance with read and write capabilities. '
        'This can\'t be undone. To avoid loss of data, before promoting the '
        'replica, you should verify that the replica has applied all '
        'transactions received from the primary.') + '\n\n')
    if promote_replica_docs_link:
      sys.stderr.write(promote_replica_docs_link)

    console_io.PromptContinue(message='', default=True, cancel_on_no=True)

    result = sql_client.instances.PromoteReplica(
        sql_messages.SqlInstancesPromoteReplicaRequest(
            project=instance_ref.project, instance=instance_ref.instance,
            failover=args.failover))
    operation_ref = client.resource_parser.Create(
        'sql.operations', operation=result.name, project=instance_ref.project)

    if args.async_:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project, operation=operation_ref.operation))

    operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                  'Promoting Cloud SQL replica')

    log.status.write('Promoted [{instance}].\n'.format(instance=instance_ref))
