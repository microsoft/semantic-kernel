# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for adding a Rule to a Compute Engine NAT."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from googlecloudsdk.command_lib.compute.routers.nats.rules import flags as rules_flags
from googlecloudsdk.command_lib.compute.routers.nats.rules import rules_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Add a Rule to a Compute Engine NAT."""

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)

    rules_flags.AddRuleNumberArg(parser, operation_type='create', plural=False)
    rules_flags.AddNatNameArg(parser)
    compute_flags.AddRegionFlag(parser, 'NAT', operation_type='create')

    rules_flags.AddMatchArg(parser, required=True)
    rules_flags.AddIpAndRangeArgsForCreate(parser)

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    request_type = messages.ComputeRoutersGetRequest
    router = service.Get(request_type(**router_ref.AsDict()))

    rule_number = args.rule_number
    nat_name = args.nat

    existing_nat = nats_utils.FindNatOrRaise(router, nat_name)

    rule = rules_utils.CreateRuleMessage(args, holder, existing_nat)
    existing_nat.rules.append(rule)

    result = service.Patch(
        messages.ComputeRoutersPatchRequest(
            project=router_ref.project,
            region=router_ref.region,
            router=router_ref.Name(),
            routerResource=router))

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
          kind='Rule [{0}] in NAT [{1}]'.format(rule_number, nat_name),
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
        'Creating Rule [{0}] in NAT [{1}]'.format(rule_number, nat_name))


Create.detailed_help = {
    'DESCRIPTION':
        """
        *{command}* is used to create a Rule on a Compute Engine NAT.
        """,
    'EXAMPLES':
        """\
        Create a rule to use the IP Address address-1 to talk to destination IPs
        in the CIDR Range "203.0.113.0/24".

          $ {command} 1 --nat=my-nat --router=my-router --region=us-central1
            --match='inIpRange(destination.ip, "203.0.113.0/24")'
            --source-nat-active-ips=a1
        """
}
