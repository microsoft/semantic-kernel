# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Switches over a Cloud SQL instance to one of its replicas.

Switches over a Cloud SQL instance to one of its replicas. Currently only
supported on Cloud SQL for SQL Server and MySQL instances. MySQL instances are
only supperted on gcloud ALPHA.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import instances
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

DETAILED_HELP_ALPHA = {
    'EXAMPLES':
        """\
        To switch over an instance to its replica called replica-instance:

          $ gcloud alpha sql instances switchover replica-instance
        """,
}

DETAILED_HELP_BETA = {
    'EXAMPLES':
        """\
        To switch over an instance to its replica called replica-instance:

          $ gcloud beta sql instances switchover replica-instance
        """,
}


def AddBaseArgs(parser):
  """Declare flag and positional arguments for this command parser."""
  base.ASYNC_FLAG.AddToParser(parser)
  parser.add_argument(
      'replica', completer=flags.InstanceCompleter, help='Cloud SQL replica ID.'
  )


def RunBaseSwitchoverCommand(args, allow_mysql):
  """Switches over a Cloud SQL instance to one of its replicas.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    allow_mysql: whether to allow MySQL on the gcloud version or not.

  Returns:
    A dict object representing the operations resource describing the
    switchover operation if the switchover was successful.
  """
  client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  validate.ValidateInstanceName(args.replica)
  instance_ref = client.resource_parser.Parse(
      args.replica,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances',
  )

  instance_resource = sql_client.instances.Get(
      sql_messages.SqlInstancesGetRequest(
          project=instance_ref.project, instance=instance_ref.instance
      )
  )

  if not instances.InstancesV1Beta4.IsSqlServerDatabaseVersion(
      instance_resource.databaseVersion
  ):
    if not allow_mysql:
      raise exceptions.OperationError(
          'Switchover operation is currently supported for Cloud SQL for SQL'
          ' Server instances only'
      )
    elif not instances.InstancesV1Beta4.IsMysqlDatabaseVersion(
        instance_resource.databaseVersion
    ):
      raise exceptions.OperationError(
          'Switchover operation is currently supported for Cloud SQL for SQL'
          ' Server and MySQL instances only'
      )

  # Format the message ourselves here rather than supplying it as part of the
  # 'message' to PromptContinue. Having the whole paragraph be automatically
  # formatted by PromptContinue would leave it with a line break in the middle
  # of the URL, rendering it unclickable.
  sys.stderr.write(
      textwrap.TextWrapper().fill(
          'Switching over to a replica leads to a short period of downtime'
          ' and results in the primary and replica instances "switching"'
          ' roles. Before switching over to the replica, you must verify'
          ' that both the primary and replica instances are online.'
          ' Otherwise, use a promote operation.'
      )
      + '\n\n'
  )

  console_io.PromptContinue(message='', default=True, cancel_on_no=True)

  result = sql_client.instances.Switchover(
      sql_messages.SqlInstancesSwitchoverRequest(
          project=instance_ref.project, instance=instance_ref.instance
      )
  )
  operation_ref = client.resource_parser.Create(
      'sql.operations', operation=result.name, project=instance_ref.project
  )

  if args.async_:
    return sql_client.operations.Get(
        sql_messages.SqlOperationsGetRequest(
            project=operation_ref.project, operation=operation_ref.operation
        )
    )

  operations.OperationsV1Beta4.WaitForOperation(
      sql_client, operation_ref, 'Switching over to Cloud SQL replica'
  )

  log.status.write(
      'Switched over [{instance}].\n'.format(instance=instance_ref)
  )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SwitchoverAlpha(base.Command):
  """Switches over a Cloud SQL instance to one of its replicas.

  Switches over a Cloud SQL instance to one of its replicas. Only supported on
  Cloud SQL for SQL Server and MySQL instances.
  """

  detailed_help = DETAILED_HELP_ALPHA

  def Run(self, args):
    return RunBaseSwitchoverCommand(args, allow_mysql=True)

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    AddBaseArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SwitchoverBeta(base.Command):
  """Switches over a Cloud SQL instance to one of its replicas.

  Switches over a Cloud SQL instance to one of its replicas. Currently only
  supported on Cloud SQL for SQL Server instances.
  """

  detailed_help = DETAILED_HELP_BETA

  def Run(self, args):
    return RunBaseSwitchoverCommand(args, allow_mysql=False)

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    AddBaseArgs(parser)
