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
"""Command to update a Distributed Cloud Edge Network router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.networking.routers import routers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.networking import resource_args
from googlecloudsdk.command_lib.edge_cloud.networking.routers import flags as routers_flags
from googlecloudsdk.core import log

DESCRIPTION = """Update a Distributed Cloud Edge Network router.

Note that `update` operations are not thread-safe, meaning that if more than one
user is updating a router at a time, there can be race conditions. Please ensure
that at most one `update` operation is being applied to a given router at a
time.
"""

EXAMPLES = """\
    To add a northbound route advertisement for destination range 8.8.0.0/16 for Distributed Cloud Edge Network router 'my-router' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-router --add-advertisement-ranges=8.8.0.0/16 --location=us-central1 --zone=us-central1-edge-den1

    To remove a northbound route advertisement for destination range 8.8.0.0/16 for Distributed Cloud Edge Network router 'my-router' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-router --remove-advertisement-ranges=8.8.0.0/16 --location=us-central1 --zone=us-central1-edge-den1

    To replace the set of route advertisements with just 8.8.0.0/16 and 1.1.0.0/16, in Distributed Cloud Edge Network router 'my-router' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-router --set-advertisement-ranges=8.8.0.0/16,1.1.0.0/16 --location=us-central1 --zone=us-central1-edge-den1
   """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Distributed Cloud Edge Network router.

  *{command}* is used update a Distributed Cloud Edge Network router.
  """

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddRouterResourceArg(parser, 'to be updated', True)
    routers_flags.AddUpdateArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    routers_client = routers.RoutersClient(self.ReleaseTrack())
    router_ref = args.CONCEPTS.router.Parse()

    if not self.has_routes_arg(args):
      return

    update_req_op = routers_client.ChangeAdvertisements(router_ref, args)

    async_ = getattr(args, 'async_', False)
    if not async_:
      response = routers_client.WaitForOperation(update_req_op)
      log.UpdatedResource(
          router_ref.RelativeName(), details='Operation was successful.')
      return response

    log.status.Print('Updating [{0}] with operation [{1}].'.format(
        router_ref.RelativeName(), update_req_op.name))

  def has_routes_arg(self, args):
    relevant_args = [
        args.add_advertisement_ranges,
        args.remove_advertisement_ranges,
        args.set_advertisement_ranges,
    ]
    filtered = filter(None, relevant_args)
    number_found = sum(1 for _ in filtered)
    if number_found == 0:
      return False
    if number_found == 1:
      return True

    raise ValueError(
        'Invalid argument: Expected at most one of add_advertisement_ranges '
        'remove_advertisement_ranges set_advertisement_ranges')
