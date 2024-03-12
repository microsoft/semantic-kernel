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

"""Command for accepting spokes into hubs."""

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
class AcceptSpoke(base.Command):
  """Accept a spoke into a hub.

  Accept a proposed or previously rejected VPC spoke. By accepting a spoke,
  you permit connectivity between the associated VPC network
  and other VPC networks that are attached to the same hub.
  """

  @staticmethod
  def Args(parser):
    flags.AddHubResourceArg(parser, 'to accept the spoke into')
    flags.AddSpokeFlag(parser, 'URI of the spoke to accept')
    flags.AddAsyncFlag(parser)

  def Run(self, args):
    client = networkconnectivity_api.HubsClient(
        release_track=self.ReleaseTrack())
    hub_ref = args.CONCEPTS.hub.Parse()
    op_ref = client.AcceptSpoke(hub_ref, args.spoke)

    log.status.Print('Accept spoke request issued for: [{}]'.format(
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


AcceptSpoke.detailed_help = {
    'EXAMPLES':
        """ \
  To accept a spoke named ``my-spoke'' into a hub named ``my-hub'', run:

    $ {command} my-hub --spoke="https://www.googleapis.com/networkconnectivity/v1/projects/spoke-project/locations/global/hubs/my-spoke"
  """,
    'API REFERENCE':
        """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
