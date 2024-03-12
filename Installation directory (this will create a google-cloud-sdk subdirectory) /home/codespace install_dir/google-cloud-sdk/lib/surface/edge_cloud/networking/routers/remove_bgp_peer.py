# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to remove a BGP peer from a Distributed Cloud Edge Network router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.networking.routers import routers
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.networking import resource_args
from googlecloudsdk.core import log

DESCRIPTION = (
    'Delete a list of BGP peer from a Distributed Cloud Edge Network router'
)
EXAMPLES = """\
    To delete a BGP peer 'peer1' from the Distributed Cloud Edge Network router 'my-router' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-router --peer-name=peer1 --location=us-central1 --zone=us-central1-edge-den1

   """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class RemoveBgpPeer(base.UpdateCommand):
  """Remove a BGP peer from a Distributed Cloud Edge Network router.

  *{command}* is used to delete a BGP peer from a Distributed Cloud
  Edge
  Network router.
  """

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddRouterResourceArg(
        parser, 'from which we delete a BGP peer', True
    )
    bgp_peer_parser = parser.add_mutually_exclusive_group(required=True)
    bgp_peer_parser.add_argument(
        '--peer-names',
        type=arg_parsers.ArgList(),
        metavar='PEER_NAME',
        help="""The list of names for peers being removed.
        Only single value allowed currently.
        """,
    )
    bgp_peer_parser.add_argument(
        '--peer-name', help='The name of the BGP peer being removed.'
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    routers_client = routers.RoutersClient(self.ReleaseTrack())
    router_ref = args.CONCEPTS.router.Parse()
    update_req_op = routers_client.RemoveBgpPeer(router_ref, args)

    async_ = args.async_
    if not async_:
      response = routers_client.WaitForOperation(update_req_op)
      log.UpdatedResource(
          router_ref.RelativeName(), details='Operation was successful.'
      )
      return response

    log.status.Print(
        'Updating [{0}] with operation [{1}].'.format(
            router_ref.RelativeName(), update_req_op.name
        )
    )
