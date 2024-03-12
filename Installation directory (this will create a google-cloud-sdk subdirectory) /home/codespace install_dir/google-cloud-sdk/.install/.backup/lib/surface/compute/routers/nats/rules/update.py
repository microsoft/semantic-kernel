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
"""Command for updating a Rule in a Compute Engine NAT."""
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
class Update(base.UpdateCommand):
  """Update a Rule in a Compute Engine NAT."""

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)

    rules_flags.AddRuleNumberArg(parser, operation_type='update', plural=False)
    rules_flags.AddNatNameArg(parser)
    compute_flags.AddRegionFlag(
        parser, 'NAT containing the Rule', operation_type='update'
    )

    rules_flags.AddMatchArg(parser, required=False)
    rules_flags.AddIpAndRangeArgsForUpdate(parser)

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

    nat = nats_utils.FindNatOrRaise(router, nat_name)
    rule = rules_utils.FindRuleOrRaise(nat, rule_number)

    rules_utils.UpdateRuleMessage(rule, args, holder, nat)

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
      log.UpdatedResource(
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
        'Updating Rule [{0}] in NAT [{1}]'.format(rule_number, nat_name))


Update.detailed_help = {
    'DESCRIPTION':
        """
        *{command}* is used to update a Rule in a Compute Engine NAT.
        """,
    'EXAMPLES':
        """\
        To drain connections established using address-1 and use address-2 for
        all new connections matching Rule 1 in NAT nat-1, run:

          $ {command} 1 --nat=nat1 --router=my-router --region=us-central1
            --source-nat-drain-ips=address-1
            --source-nat-active-ips=address-2
        """
}
