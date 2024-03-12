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
"""Command for listing internal IP addresses in a network."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListIpAddresses(base.ListCommand):
  """List internal IP addresses/ranges related a network."""

  example = """\
    List all internal IP addresses in a network:

      $ {command} my-network

    List IP addresses only for given types:

      $ {command} my-network \
          --types=SUBNETWORK,PEER_USED,REMOTE_USED
  """

  detailed_help = {
      'brief':
          'List internal IP addresses in a network.',
      'DESCRIPTION': """\
      *{command}* is used to list internal IP addresses in a network.
      """,
      'EXAMPLES': example
  }

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument('name', help='The name of the network.')
    parser.add_argument(
        '--types',
        type=lambda x: x.replace('-', '_').upper(),
        help="""\
        Optional comma separate list of ip address types to filter on. Valid
        values are `SUBNETWORK`, `RESERVED`, `PEER_USED`, `PEER_RESERVED`,
        `REMOTE_USED` and `REMOTE_RESERVED`.
        """)

    parser.display_info.AddFormat("""\
        table(
            type,
            cidr:label=IP_RANGE,
            region,
            owner,
            purpose)
    """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE
    project = properties.VALUES.core.project.Get(required=True)

    request = messages.ComputeNetworksListIpAddressesRequest(
        project=project, network=args.name, types=args.types)
    items = list_pager.YieldFromList(
        client.networks,
        request,
        method='ListIpAddresses',
        field='items',
        limit=args.limit,
        batch_size=None)
    return items
