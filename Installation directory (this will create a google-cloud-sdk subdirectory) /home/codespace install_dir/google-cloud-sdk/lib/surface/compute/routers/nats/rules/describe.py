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
"""Command for describing a Rule from a Compute Engine NAT."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils
from googlecloudsdk.command_lib.compute.routers.nats.rules import flags as rules_flags
from googlecloudsdk.command_lib.compute.routers.nats.rules import rules_utils


class Describe(base.DescribeCommand):
  """Describe a Rule in a Compute Engine NAT."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)

    rules_flags.AddRuleNumberArg(parser)
    rules_flags.AddNatNameArg(parser)
    compute_flags.AddRegionFlag(
        parser, 'NAT containing the Rule', operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    router = client.MakeRequests([
        (client.apitools_client.routers, 'Get',
         client.messages.ComputeRoutersGetRequest(**router_ref.AsDict()))
    ])[0]

    nat_name = args.nat
    rule_number = args.rule_number

    nat = nats_utils.FindNatOrRaise(router, nat_name)

    return rules_utils.FindRuleOrRaise(nat, rule_number)


Describe.detailed_help = {
    'DESCRIPTION':
        textwrap.dedent("""\
          *{command}* is used to describe a Rule on a Compute Engine NAT.
    """),
    'EXAMPLES':
        """\
    To describe Rule 1 in NAT 'n1' in router 'r1', run:

      $ {command} 1 --nat=n1 --router=r1 --region=us-central1
    """
}
