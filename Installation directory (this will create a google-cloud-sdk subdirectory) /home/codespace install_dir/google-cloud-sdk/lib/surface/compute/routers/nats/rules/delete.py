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
"""Command for removing a Rule from a Compute Engine NAT."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from googlecloudsdk.command_lib.compute.routers.nats.rules import flags as rules_flags
from googlecloudsdk.command_lib.compute.routers.nats.rules import rules_utils


class Delete(base.DeleteCommand):
  """Delete a Rule in a Compute Engine NAT."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)

    rules_flags.AddRuleNumberArg(parser, plural=True)
    rules_flags.AddNatNameArg(parser)
    compute_flags.AddRegionFlag(
        parser, 'NAT containing the Rule', operation_type='delete', plural=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    objects = client.MakeRequests([
        (client.apitools_client.routers, 'Get',
         client.messages.ComputeRoutersGetRequest(**router_ref.AsDict()))
    ])
    router = objects[0]

    nat_name = args.nat
    rule_numbers = args.rule_number

    nat = nats_utils.FindNatOrRaise(router, nat_name)
    for rule_number in rule_numbers:
      rule = rules_utils.FindRuleOrRaise(nat, rule_number)
      nat.rules.remove(rule)

    utils.PromptForDeletionHelper(
        'Rule', ['{} in NAT {}'.format(args.rule_number, nat_name)])

    return client.MakeRequests(
        [self._GetPatchRequest(client, router_ref, router)])

  def _GetPatchRequest(self, client, router_ref, router):
    return (client.apitools_client.routers, 'Patch',
            client.messages.ComputeRoutersPatchRequest(
                router=router_ref.Name(),
                routerResource=router,
                region=router_ref.region,
                project=router_ref.project))


Delete.detailed_help = {
    'DESCRIPTION':
        textwrap.dedent("""\
          *{command}* is used to delete a Rule on a Compute Engine NAT.
    """),
    'EXAMPLES':
        """\
    To delete Rule 1 in NAT 'n1' in router 'r1', run:

      $ {command} 1 --nat=n1 --router=r1 --region=us-central1
    """
}
