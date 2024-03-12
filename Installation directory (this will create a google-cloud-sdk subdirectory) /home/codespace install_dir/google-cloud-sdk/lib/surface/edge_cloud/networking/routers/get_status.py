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
"""Command to get the status of a Distributed Cloud Edge Network router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.networking.routers import routers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.networking import resource_args

DESCRIPTION = (
    'Get the status of a specified Distributed Cloud Edge Network router.')
EXAMPLES = """\
    To get the status of the Distributed Cloud Edge Network router
    'my-router' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-router --location=us-central1 --zone=us-central1-edge-den1

   """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class GetStatus(base.Command):
  """Get the status of a specified Distributed Cloud Edge Network router.

  *{command}* is used to get the status of a Distributed Cloud Edge Network
  router.
  """

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddRouterResourceArg(parser, 'to get status', True)

  def _PreprocessResult(self, router_status):
    """Make the nextHopReachable value explicit for each route status."""
    # This is necessary because if nextHopReachable == false, then when it's
    # serialized by the server it will not be included, but we want to print it
    # out explicitly, whether it's true or false.
    for route_status in router_status.result.staticRouteStatus:
      route_status.nextHopReachable = bool(route_status.nextHopReachable)
    return router_status

  def Run(self, args):
    routers_client = routers.RoutersClient(self.ReleaseTrack())
    router_ref = args.CONCEPTS.router.Parse()
    if self.ReleaseTrack() == base.ReleaseTrack.GA:
      return routers_client.GetStatus(router_ref)
    return self._PreprocessResult(routers_client.GetStatus(router_ref))
