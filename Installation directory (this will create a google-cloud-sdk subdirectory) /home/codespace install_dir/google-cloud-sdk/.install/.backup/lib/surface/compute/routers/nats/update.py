# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command for updating a NAT on a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags
from googlecloudsdk.command_lib.compute.routers.nats import flags as nats_flags
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  """Update a NAT on a Compute Engine router."""

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)

    base.ASYNC_FLAG.AddToParser(parser)

    compute_flags.AddRegionFlag(parser, 'NAT', operation_type='create')

    nats_flags.AddNatNameArg(parser, operation_type='create')
    nats_flags.AddCommonNatArgs(parser, for_create=False)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    request_type = messages.ComputeRoutersGetRequest
    replacement = service.Get(request_type(**router_ref.AsDict()))

    # Retrieve specified NAT and update base fields.
    existing_nat = nats_utils.FindNatOrRaise(replacement, args.name)
    nat = nats_utils.UpdateNatMessage(existing_nat, args, holder)

    request_type = messages.ComputeRoutersPatchRequest
    result = service.Patch(
        request_type(
            project=router_ref.project,
            region=router_ref.region,
            router=router_ref.Name(),
            routerResource=replacement))

    operation_ref = resources.REGISTRY.Parse(
        result.name,
        collection='compute.regionOperations',
        params={
            'project': router_ref.project,
            'region': router_ref.region,
        })

    if args.async_:
      log.UpdatedResource(
          operation_ref,
          kind='nat [{0}] in router [{1}]'.format(nat.name, router_ref.Name()),
          is_async=True,
          details='Run the [gcloud compute operations describe] command '
          'to check the status of this operation.')
      return result

    target_router_ref = holder.resources.Parse(
        router_ref.Name(),
        collection='compute.routers',
        params={
            'project': router_ref.project,
            'region': router_ref.region,
        })

    operation_poller = poller.Poller(service, target_router_ref)
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Updating nat [{0}] in router [{1}]'.format(nat.name,
                                                    router_ref.Name()))


Update.detailed_help = {
    'DESCRIPTION':
        """
        *{command}* is used to update a NAT in a Compute Engine router.
        """,
    'EXAMPLES':
        """\
        Change subnetworks and IP address resources associated with NAT:

          $ {command} nat1 --router=my-router
            --nat-external-ip-pool=ip-address2,ip-address3
            --nat-custom-subnet-ip-ranges=subnet-2,subnet-3:secondary-range-2

        Change minimum default ports allocated per VM associated with NAT:

          $ {command} nat1 --router=my-router --min-ports-per-vm=128

        Change connection timeouts associated with NAT:

          $ {command} nat1 --router=my-router
            --udp-mapping-idle-timeout=60s
            --icmp-mapping-idle-timeout=60s
            --tcp-established-connection-idle-timeout=60s
            --tcp-transitory-connection-idle-timeout=60s

        Reset connection timeouts associated NAT to default values:

          $ {command} nat1 --router=my-router
            --clear-udp-mapping-idle-timeout --clear-icmp-mapping-idle-timeout
            --clear-tcp-established-connection-idle-timeout
            --clear-tcp-transitory-connection-idle-timeout
        """,
    'API REFERENCE':
        """\
    This command, when specified without alpha or beta, uses the compute/v1/routers API. The full documentation
    for this API can be found at: https://cloud.google.com/compute/docs/reference/rest/v1/routers/

    The beta command uses the compute/beta/routers API. The full documentation
    for this API can be found at: https://cloud.google.com/compute/docs/reference/rest/beta/routers/

    The alpha command uses the compute/alpha/routers API. Full documentation is not available for the alpha API.
    """
}
