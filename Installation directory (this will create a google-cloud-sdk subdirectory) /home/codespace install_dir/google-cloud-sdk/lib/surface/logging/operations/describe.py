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
"""'logging operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_projector


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  """Display the information about a long running operation.

  Display the information about a long running operation which was scheduled
  before. For example, a copy_log_entries operation scheduled by command:
  "gcloud alpha logging copy BUCKET_ID DESTINATION --location=LOCATION"
  OPERATION_ID and LOCATION are required to locate such operation.

  ## EXAMPLES

  To describe an operation, run:

    $ {command} OPERATION_ID --location=LOCATION
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('operation_id', help='The Id of the operation.')
    parser.add_argument(
        '--location', required=True, help='Location of the operation.')

    util.AddParentArgs(parser, 'operation to describe')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A long running operation.
    """

    parent_name = util.CreateResourceName(
        util.CreateResourceName(
            util.GetParentFromArgs(args), 'locations', args.location),
        'operations', args.operation_id)
    request = util.GetMessages().LoggingProjectsLocationsOperationsGetRequest(
        name=parent_name)

    result = util.GetClient().projects_locations_operations.Get(request)
    serialize_op = resource_projector.MakeSerializable(result)
    self._cancellation_requested = serialize_op.get('metadata', {}).get(
        'cancellationRequested', '')

    return result

  def Epilog(self, resources_were_displayed):
    if self._cancellation_requested:
      log.status.Print(
          'Note: Cancellation happens asynchronously. It may take up to 10 '
          "minutes for the operation's status to change to cancelled.")
