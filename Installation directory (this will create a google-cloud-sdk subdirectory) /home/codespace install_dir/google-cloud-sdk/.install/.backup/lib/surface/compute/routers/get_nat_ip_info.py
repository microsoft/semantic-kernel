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
"""Command for getting NAT IP information from Compute Engine routers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags


class GetNatIpInfo(base.DescribeCommand):
  """Display NAT IP information in a router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='get NAT IP info')
    routers_flags.AddGetNatIpInfoArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = self.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    params = router_ref.AsDict()
    if args.nat_name:
      params['natName'] = args.nat_name

    request = client.messages.ComputeRoutersGetNatIpInfoRequest(**params)

    return client.MakeRequests([(client.apitools_client.routers,
                                 'GetNatIpInfo', request)])[0]

GetNatIpInfo.detailed_help = {
    'DESCRIPTION': """
        $ {command}

        shows a mapping of IP:[usage, mode]
        allocated to each NAT via the specified router.""",
    'EXAMPLES': """\
        To show NAT IP information from all NATs in router 'r1' in region
        'us-central1', run:

            $ {command} r1 --region=us-central1

        To show NAT IP information for a specific NAT 'nat1' in router 'r1' in
        region 'us-central1', run:

            $ {command} r1 --region=us-central1 --nat-name="nat1"
        """
}
