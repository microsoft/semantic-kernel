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

"""Command to delete a fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import flags as fleet_flags
from googlecloudsdk.command_lib.container.fleet import util as fleet_util
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as messages


class Delete(base.DeleteCommand):
  """Delete a fleet.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The project specified already has a fleet.
  * The active account does not have permission to access the given project.

  ## EXAMPLES

  To delete a fleet in project `example-foo-bar-1`, run:

    $ {command} --project=example-foo-bar-1
  """

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> messages.Operation:
    flags = fleet_flags.FleetFlags(parser)
    flags.AddAsync()

  def Run(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Runs the fleet delete command.

    A completed fleet delete operation response body is empty, gcloud client
    won't apply the default output format in non-async mode.

    Args:
      args: Arguments received from command line.

    Returns:
      A completed create operation; if `--async` is specified, return a
      long-running operation to be polled manually.
    """
    flag_parser = fleet_flags.FleetFlagParser(
        args, release_track=base.ReleaseTrack.ALPHA
    )

    if '--format' not in args.GetSpecifiedArgNames():
      if flag_parser.Async():
        args.format = fleet_util.OPERATION_FORMAT

    req = flag_parser.messages.GkehubProjectsLocationsFleetsDeleteRequest(
        name=util.FleetResourceName(flag_parser.Project())
    )
    fleetclient = client.FleetClient(release_track=base.ReleaseTrack.ALPHA)
    operation = fleetclient.DeleteFleet(req)
    fleet_ref = util.FleetRef(flag_parser.Project())

    if flag_parser.Async():
      log.DeletedResource(
          fleet_ref, kind='Anthos fleet', is_async=flag_parser.Async()
      )
      return operation

    operation_client = client.OperationClient(
        release_track=base.ReleaseTrack.ALPHA
    )
    operation_ref = util.OperationRef(operation)
    completed_operation = operation_client.Wait(operation_ref)
    log.DeletedResource(
        fleet_ref, kind='Anthos fleet', is_async=flag_parser.Async()
    )
    return completed_operation
