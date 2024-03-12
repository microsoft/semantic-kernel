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

"""Command for removing a route policy from a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveRoutePolicy(base.DeleteCommand):
  """Remove a route policy from a Compute Engine router.

  *{command}* removes a route policy from a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    RemoveRoutePolicy.ROUTER_ARG = flags.RouterArgument()
    RemoveRoutePolicy.ROUTER_ARG.AddArgument(parser, operation_type='delete')
    parser.add_argument(
        '--policy-name',
        help="""Name of the route policy to be removed.""",
        required=True,
    )

  def Run(self, args):
    """Issues the request necessary for removing a route policy from a Router.

    Args:
      args: contains arguments passed to the command.

    Returns:
      The result of patching the router removing the route policy.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = RemoveRoutePolicy.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    request = (
        client.apitools_client.routers,
        'DeleteRoutePolicy',
        client.messages.ComputeRoutersDeleteRoutePolicyRequest(
            **router_ref.AsDict(), policy=args.policy_name
        ),
    )

    return client.MakeRequests([request])[0]
