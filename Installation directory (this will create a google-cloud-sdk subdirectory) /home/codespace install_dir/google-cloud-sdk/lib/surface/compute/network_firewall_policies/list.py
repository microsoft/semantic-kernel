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
"""Command for listing network firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List Compute Engine network firewall policies.

  *{command}* is used to list network firewall policies. A network
  firewall policy is a set of rules that controls access to various resources.
  """

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat("""\
      table(
        name,
        region.basename(),
        description
      )
      """)
    lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)
    parser.display_info.AddCacheUpdater(flags.NetworkFirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE

    if args.project:
      project = args.project
    else:
      project = properties.VALUES.core.project.GetOrFail()

    # List RNFPs in given regions
    if args.regions:
      regional_generators = []
      for region in args.regions:
        regional_generators.append(
            list_pager.YieldFromList(
                client.regionNetworkFirewallPolicies,
                messages.ComputeRegionNetworkFirewallPoliciesListRequest(
                    project=project, region=region.strip()),
                field='items',
                limit=args.limit,
                batch_size=None))
      return itertools.chain.from_iterable(regional_generators)

    # List global NFPs
    if getattr(args, 'global', None):
      return list_pager.YieldFromList(
          client.networkFirewallPolicies,
          messages.ComputeNetworkFirewallPoliciesListRequest(project=project),
          field='items',
          limit=args.limit,
          batch_size=None)

    # Aggregated global NFPs and RNFPs for all regions defined in project
    request = messages.ComputeRegionsListRequest(project=project)
    regions = list_pager.YieldFromList(
        client.regions, request, field='items', batch_size=None)
    aggregated_generators = []
    aggregated_generators.append(
        list_pager.YieldFromList(
            client.networkFirewallPolicies,
            messages.ComputeNetworkFirewallPoliciesListRequest(project=project),
            field='items',
            limit=args.limit,
            batch_size=None))
    for region in regions:
      aggregated_generators.append(
          list_pager.YieldFromList(
              client.regionNetworkFirewallPolicies,
              messages.ComputeRegionNetworkFirewallPoliciesListRequest(
                  project=project, region=region.name),
              field='items',
              limit=args.limit,
              batch_size=None))
    return itertools.chain.from_iterable(aggregated_generators)


List.detailed_help = {
    'EXAMPLES':
        """\
    To list global network firewall policies under project
    ``my-project'', run:

      $ {command} --project=my-project --global

    To list regional network firewall policies under project
    ``my-project'', specify a list of regions with ``--regions'':

      $ {command} --project=my-project --regions="region-a, region-b"

    To list all global and regional network firewall policies under project
    ``my-project'', omit ``--global'' and ``--regions'':

      $ {command} --project=my-project
    """,
}
