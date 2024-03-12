# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for listing IP owners in a network."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListIpOwners(base.ListCommand):
  """List IP owners with optional filters in a network."""

  example = """
    List all IP owners in a network:

      $ {command} my-network

    List IP owners only for given owner types:

      $ {command} my-network \
          --owner-types=instance,address,forwardingRule

    List IP owners only for given owner projects:

      $ {command} my-network \
          --owner-projects=p1,p2

    List IP owners only for given subnet:

      $ {command} my-network \
          --subnet-name=subnet-1 --subnet-region=us-central1

    List IP owners whose IP ranges overlap with the given IP CIDR range:

      $ {command} my-network \
          --ip-cidr-range=10.128.10.130/30
  """

  detailed_help = {
      'brief': 'List IP owners in a network.',
      'DESCRIPTION': '*{command}* is used to list IP owners in a network.',
      'EXAMPLES': example
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='The name of the network.')
    parser.add_argument(
        '--subnet-name',
        help=('Only return IP owners in the subnets with the name. '
              'Not applicable for legacy networks.'))
    parser.add_argument(
        '--subnet-region',
        help=('Only return IP owners in the subnets of the region. '
              'Not applicable for legacy networks.'))
    parser.add_argument(
        '--ip-cidr-range',
        help=
        'Only return IP owners whose IP ranges overlap with the IP CIDR range.')
    parser.add_argument(
        '--owner-projects',
        help=('Only return IP owners in the projects. Multiple projects are '
              'separated by comma, e.g., "project-1,project-2".'))
    parser.add_argument(
        '--owner-types',
        help=('Only return IP owners of the types, which can be any '
              'combination of instance, address, forwardingRule, subnetwork, '
              'or network. Multiple types are separated by comma, e.g., '
              '"instance,forwardingRule,address"'))
    parser.display_info.AddFormat("""
        table(
            ipCidrRange:label=IP_CIDR_RANGE,
            systemOwned:label=SYSTEM_OWNED,
            owners.join(','):label=OWNERS)
    """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE
    project = properties.VALUES.core.project.Get(required=True)

    request = messages.ComputeNetworksListIpOwnersRequest(
        project=project,
        network=args.name,
        subnetName=args.subnet_name,
        subnetRegion=args.subnet_region,
        ipCidrRange=args.ip_cidr_range,
        ownerProjects=args.owner_projects,
        ownerTypes=args.owner_types)
    items = list_pager.YieldFromList(
        client.networks,
        request,
        method='ListIpOwners',
        field='items',
        limit=args.limit,
        batch_size=None)
    return items
