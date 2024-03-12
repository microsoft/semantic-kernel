# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'logging operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_projector


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List long running operations."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--location', required=True, help='Location of the operations.')
    parser.add_argument(
        '--operation-filter',
        required=True,
        help='Filter expression that specifies the operations to return.')
    base.URI_FLAG.RemoveFromParser(parser)
    base.FILTER_FLAG.RemoveFromParser(parser)

    util.AddParentArgs(parser, 'operations to list')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      A list of operations.
    """
    operation_name = util.CreateResourceName(
        util.GetParentFromArgs(args), 'locations', args.location)

    request = util.GetMessages().LoggingProjectsLocationsOperationsListRequest(
        name=operation_name, filter=args.operation_filter)

    result = util.GetClient().projects_locations_operations.List(request)
    self._cancellation_requested = False
    for operation in result.operations:
      yield operation
      if not self._cancellation_requested:
        serialize_op = resource_projector.MakeSerializable(operation)
        self._cancellation_requested = serialize_op.get('metadata', {}).get(
            'cancellationRequested', '')

  def Epilog(self, resources_were_displayed):
    if self._cancellation_requested:
      log.status.Print(
          'Note: Cancellation happens asynchronously. It may take up to 10 '
          "minutes for the operation's status to change to cancelled.")


List.detailed_help = {
    'DESCRIPTION':
        """
        Return a list of long running operation details in given LOCATION. The
        operations were scheduled by other gcloud commands. For example: a
        copy_log_entries operation scheduled by command: gcloud alpha logging
        operations copy BUCKET_ID DESTINATION --location=LOCATION. Note: while
        listing the operations, the request_type must be specified in filter.
        Example: --operation-filter=request_type=CopyLogEntries, Supported
        operation types are: CopyLogEntries, CreateBucket and UpdateBucket.
        Other supported filter expression are: operation_start_time,
        operation_finish_time and operation_state.
        """,
    'EXAMPLES':
        """\
        To list CopyLogEntries operations, run:

            $ {command} --location=LOCATION --operation-filter='request_type=CopyLogEntries'

        To list CopyLogEntries operations that started after a specified time, run:

            $ {command} --location=LOCATION --operation-filter='request_type=CopyLogEntries AND operation_start_time>="2023-11-20T00:00:00Z"'

        To list CopyLogEntries operations that finished before a specified time, run:

            $ {command} --location=LOCATION --operation-filter='request_type=CopyLogEntries AND operation_finish_time<="2023-11-20T00:00:00Z"'

        To list CopyLogEntries operations that have a specified state, run:

            $ {command} --location=LOCATION --operation-filter='request_type=CopyLogEntries AND operation_state=STATE'

        To list CopyLogEntries operations that don't have a specified state, run:

            $ {command} --location=LOCATION --operation-filter='request_type=CopyLogEntries AND operation_state!=STATE'
        """
}
