# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Command for updating spokes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a VPC spoke.

  Update the details of a VPC spoke.
  """

  @staticmethod
  def Args(parser):
    flags.AddSpokeResourceArg(parser, 'to update', vpc_spoke_only_command=True)
    flags.AddRegionGroup(parser, hide_global_arg=False, hide_region_arg=True)
    flags.AddDescriptionFlag(parser, 'New description of the spoke.')
    flags.AddAsyncFlag(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = networkconnectivity_api.SpokesClient(
        release_track=self.ReleaseTrack())

    spoke_ref = args.CONCEPTS.spoke.Parse()
    update_mask = []
    description = args.description
    if description is not None:
      update_mask.append('description')

    labels = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      original_spoke = client.Get(spoke_ref)
      labels_update = labels_diff.Apply(client.messages.Spoke.LabelsValue,
                                        original_spoke.labels)
      if labels_update.needs_update:
        labels = labels_update.labels
        update_mask.append('labels')

    # Construct a spoke message with only the updated fields
    spoke = client.messages.Spoke(description=description, labels=labels)

    op_ref = client.UpdateVPCSpoke(spoke_ref, spoke, update_mask)

    log.status.Print('Update request issued for: [{}]'.format(spoke_ref.Name()))

    if op_ref.done:
      log.UpdatedResource(spoke_ref.Name(), kind='spoke')
      return op_ref

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()])
    poller = waiter.CloudOperationPoller(client.spoke_service,
                                         client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.UpdatedResource(spoke_ref.Name(), kind='spoke')
    return res


Update.detailed_help = {
    'EXAMPLES':
        """ \
  To update the description of a global VPC spoke named ``my-spoke'', run:

    $ {command} myspoke --global --description="new spoke description"
  """,
    'API REFERENCE':
        """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
