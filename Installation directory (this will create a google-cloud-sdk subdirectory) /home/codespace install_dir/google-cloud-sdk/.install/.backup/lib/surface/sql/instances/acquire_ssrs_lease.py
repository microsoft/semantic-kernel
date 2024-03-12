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
"""Acquires a SQL Server Reporting Services lease on a Cloud SQL instance."""

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

DESCRIPTION = """\
    Acquire a SQL Server Reporting Services lease on a Cloud SQL instance.
    """

EXAMPLES = """\
    To acquire a SQL Server Reporting Services lease on an instance:

    $ {command} instance-foo --setup-login=setuplogin --service-login=reportuser --report-database=ReportServer --duration=4h
    """

DETAILED_HELP = {
    'DESCRIPTION': DESCRIPTION,
    'EXAMPLES': EXAMPLES,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AcquireSsrsLease(base.Command):
  """Acquires a SQL Server Reporting Services lease on a Cloud SQL instance."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.

    Returns:
      A dict object representing the operations resource describing the acquire
      SSRS lease operation if the operation was successful.
    """
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID.',
    )

    flags.AddSqlServerSsrs(parser)

  def Run(self, args):
    """Acquires a SQL Server Reporting Services lease on a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the
      acquire-ssrs-lease operation if the acquire-ssrs-lease was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    duration_str = args.duration
    if duration_str is not None:
      duration_str = str(args.duration) + 's'

    request = sql_messages.SqlInstancesAcquireSsrsLeaseRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        instancesAcquireSsrsLeaseRequest=sql_messages.InstancesAcquireSsrsLeaseRequest(
            acquireSsrsLeaseContext=sql_messages.AcquireSsrsLeaseContext(
                setupLogin=args.setup_login,
                serviceLogin=args.service_login,
                reportDatabase=args.report_database,
                duration=duration_str,
            ),),
    )

    result = sql_client.instances.AcquireSsrsLease(request)

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result.operationId,
        project=instance_ref.project)

    operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                  'Acquiring SSRS lease')

    log.status.write('Successfully acquired SSRS lease.\n')
