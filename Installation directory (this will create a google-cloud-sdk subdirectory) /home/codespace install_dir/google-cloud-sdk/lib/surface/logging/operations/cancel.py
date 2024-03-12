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
"""'logging operations cancel' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Cancel(base.Command):
  """Cancel a long running operation.

  Cancel a long running operation with given OPERATION_ID in given LOCATION.
  This operation can be a copy_log_entries operation which is scheduled before.

  ## EXAMPLES

  To cancel an operation, run:

    $ {command} OPERATION_ID --location=LOCATION
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('operation_id', help='The Id of the operation.')
    parser.add_argument(
        '--location', required=True, help='Location of the operation.')

    util.AddParentArgs(parser, 'operation to cancel')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A long running operation.
    """

    operation_name = util.CreateResourceName(
        util.CreateResourceName(
            util.GetParentFromArgs(args), 'locations', args.location),
        'operations', args.operation_id)
    operation_reference = util.GetOperationReference(args.operation_id, args)

    console_io.PromptContinue('Really cancel operation [%s]?' % operation_name,
                              cancel_on_no=True)

    request = util.GetMessages(
    ).LoggingProjectsLocationsOperationsCancelRequest(name=operation_name)

    util.GetClient().projects_locations_operations.Cancel(request)
    print('Cancelled [%s]' % operation_reference)
    print('Note:it may take up to 10 minutes for the '
          "operation's status to be updated.")
