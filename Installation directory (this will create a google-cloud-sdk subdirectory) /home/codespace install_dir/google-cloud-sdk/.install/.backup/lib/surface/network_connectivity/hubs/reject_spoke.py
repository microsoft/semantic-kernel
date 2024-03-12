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

"""Command for rejecting spokes from hubs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RejectSpoke(base.Command):
  """Reject a spoke from a hub.

  Reject a VPC spoke. By rejecting a spoke,
  you prevent or remove connectivity between the associated VPC network
  and any other VPC networks that are attached to the same hub.
  """

  @staticmethod
  def Args(parser):
    flags.AddHubResourceArg(parser, 'to reject the spoke from')
    flags.AddSpokeFlag(parser, 'URI of the spoke to reject')
    flags.AddRejectionDetailsFlag(parser)
    flags.AddAsyncFlag(parser)

  def Run(self, args):
    client = networkconnectivity_api.HubsClient(
        release_track=self.ReleaseTrack())
    hub_ref = args.CONCEPTS.hub.Parse()
    op_ref = client.RejectSpoke(hub_ref, args.spoke, args.details)

    log.status.Print('Reject spoke request issued for: [{}]'.format(
        hub_ref.Name()))

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()])
    poller = waiter.CloudOperationPollerNoResources(client.operation_service)

    if op_ref.done:
      return poller.GetResult(op_resource)

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    return res


RejectSpoke.detailed_help = {
    'EXAMPLES':
        """ \
  To reject a spoke named ``my-spoke'' from a hub named ``my-hub'' with reason ``my-reason'', run:

    $ {command} my-hub --spoke="https://www.googleapis.com/networkconnectivity/v1/projects/spoke-project/locations/global/hubs/my-spoke" --details=my-reason
  """,
    'API REFERENCE':
        """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
