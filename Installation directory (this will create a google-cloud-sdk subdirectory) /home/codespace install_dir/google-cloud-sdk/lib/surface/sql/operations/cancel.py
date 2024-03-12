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
"""Cancels a Cloud SQL instance operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'EXAMPLES':
        """\
        To cancel an operation with the id "prod-operation-id",
        like "acb40108-a483-4a8b-8a5c-e27100000032", run:

          $ {command} prod-operation-id
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Cancel(base.UpdateCommand):
  """Cancels a Cloud SQL instance operation."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        'operation', help='Name that uniquely identifies the operation.')

  def Run(self, args):
    """Cancels a Cloud SQL instance operation.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      An empty response.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    operation_ref = client.resource_parser.Parse(
        args.operation,
        collection='sql.operations',
        params={'project': properties.VALUES.core.project.GetOrFail})

    log.warning('Warning: You are about to cancel [{operation}].'.format(
        operation=operation_ref.operation))
    console_io.PromptContinue(cancel_on_no=True)

    empty = sql_client.operations.Cancel(
        sql_messages.SqlOperationsCancelRequest(
            project=operation_ref.project, operation=operation_ref.operation))
    log.status.write('Cancellation issued on [{operation}].\n'.format(
        operation=operation_ref.operation))
    return empty
