# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Retrieves information about a Cloud SQL instance operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Wait(base.Command):
  """Waits for one or more operations to complete."""

  @staticmethod
  def Args(parser):
    flags.AddOperationArgument(parser)
    parser.add_argument(
        '--timeout',
        type=arg_parsers.BoundedInt(lower_bound=0, unlimited=True),
        default=300,
        help=('Maximum number of seconds to wait for an operation to complete. '
              'By default, wait for 300s. Set to *unlimited* to wait '
              'indefinitely.'))
    parser.display_info.AddFormat(flags.OPERATION_FORMAT_BETA)

  def Run(self, args):
    """Wait for a Cloud SQL instance operation.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Yields:
      Operations that were waited for.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client

    for op in args.operation:
      operation_ref = client.resource_parser.Parse(
          op,
          collection='sql.operations',
          params={'project': properties.VALUES.core.project.GetOrFail})

      yield operations.OperationsV1Beta4.WaitForOperation(
          sql_client,
          operation_ref,
          'Waiting for [{operation}]'.format(operation=operation_ref),
          max_wait_seconds=args.timeout)
