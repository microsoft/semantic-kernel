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
"""Command for adding a NAT to a Compute Engine router."""

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
class Create(base.CreateCommand):
  """Add a NAT to a Compute Engine router."""

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)

    base.ASYNC_FLAG.AddToParser(parser)

    compute_flags.AddRegionFlag(parser, 'NAT', operation_type='create')

    nats_flags.AddNatNameArg(parser, operation_type='create')
    nats_flags.AddTypeArg(parser)

    nats_flags.AddEndpointTypesArg(parser)
    nats_flags.AddCommonNatArgs(parser, for_create=True)

  def Run(self, args):
    """See base.CreateCommand."""

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    request_type = messages.ComputeRoutersGetRequest
    replacement = service.Get(request_type(**router_ref.AsDict()))

    nat = nats_utils.CreateNatMessage(args, holder)

    replacement.nats.append(nat)

    result = service.Patch(
        messages.ComputeRoutersPatchRequest(
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
      log.CreatedResource(
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
        'Creating NAT [{0}] in router [{1}]'.format(nat.name,
                                                    router_ref.Name()))


Create.detailed_help = {
    'DESCRIPTION':
        """
        *{command}* is used to create a NAT on a Compute Engine router.
        """,
    'EXAMPLES':
        """\
        Auto-allocate NAT for all IP addresses of all subnets in the region:

          $ {command} nat1 --router=my-router
            --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges

        Specify IP addresses for NAT:
        Each IP address is the name of a reserved static IP address resource in
        the same region.

          $ {command} nat1 --router=my-router
            --nat-external-ip-pool=ip-address1,ip-address2

        Specify subnet ranges for NAT:

        By default, NAT works for all primary and secondary IP ranges for all
        subnets in the region for the given VPC network. You can restrict which
        subnet primary and secondary ranges can use NAT.

          $ {command} nat1 --router=my-router
            --auto-allocate-nat-external-ips
            --nat-custom-subnet-ip-ranges=subnet-1,subnet-3:secondary-range-1
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
