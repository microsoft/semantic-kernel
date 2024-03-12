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

"""Command to update fleet information."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import flags as fleet_flags
from googlecloudsdk.command_lib.container.fleet import update_mask
from googlecloudsdk.command_lib.container.fleet import util as fleet_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as messages


class Update(base.UpdateCommand):
  """Update a fleet.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The project specified already has a fleet.
  * The active account does not have permission to access the given project.

  ## EXAMPLES

  To update the display name of the fleet in project `example-foo-bar-1`
  to `updated-name`, run:

    $ {command} --display-name=updated-name --project=example-foo-bar-1
  """

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    flags = fleet_flags.FleetFlags(parser)
    flags.AddAsync()
    flags.AddDisplayName()
    flags.AddDefaultClusterConfig()
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Runs the fleet update command.

    User specified --format takes the highest priority. If not specified, it
    returns the default format of long-running operation or fleet, depending on
    whether --async is specified.

    $ {command} --async
      The output is in default operation format.

    $ {command} --async --format
      The output is in user specified format.

    $ {command}
      The output is in default fleet format.

    $ {command} --format
      The output is in user specified format.

    Args:
      args: Arguments received from command line.

    Returns:
      A completed update operation; if `--async` is specified, return a
      long-running operation to be polled manually.
    """
    flag_parser = fleet_flags.FleetFlagParser(
        args, release_track=base.ReleaseTrack.ALPHA
    )

    if '--format' not in args.GetSpecifiedArgNames():
      if flag_parser.Async():
        args.format = fleet_util.OPERATION_FORMAT
      else:
        args.format = fleet_util.FLEET_FORMAT
    fleetclient = client.FleetClient(release_track=base.ReleaseTrack.ALPHA)

    # update GCP labels for namespace resource
    new_labels = None
    mask = []

    # Fetch existing fleet.
    current_fleet = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates() or update_mask.HasBinauthzConfig(args):
      current_fleet = fleetclient.GetFleet(flag_parser.Project())

      new_labels = labels_diff.Apply(
          fleetclient.messages.Fleet.LabelsValue,
          current_fleet.labels,
      ).GetOrNone()
    if new_labels:
      mask.append('labels')

    if update_mask.GetFleetUpdateMask(args):
      mask.append(update_mask.GetFleetUpdateMask(args))

    fleet = flag_parser.Fleet(current_fleet)
    fleet.labels = new_labels
    req = flag_parser.messages.GkehubProjectsLocationsFleetsPatchRequest(
        fleet=fleet,
        name=util.FleetResourceName(flag_parser.Project()),
        updateMask=','.join(mask),
    )

    operation = fleetclient.UpdateFleet(req)
    fleet_ref = util.FleetRef(flag_parser.Project())

    if flag_parser.Async():
      log.UpdatedResource(
          fleet_ref, 'Anthos fleet', is_async=flag_parser.Async()
      )
      return operation

    operation_client = client.OperationClient(
        release_track=base.ReleaseTrack.ALPHA
    )
    operation_ref = util.OperationRef(operation)
    completed_operation = operation_client.Wait(operation_ref)
    log.UpdatedResource(
        fleet_ref, kind='Anthos fleet', is_async=flag_parser.Async()
    )
    return completed_operation
