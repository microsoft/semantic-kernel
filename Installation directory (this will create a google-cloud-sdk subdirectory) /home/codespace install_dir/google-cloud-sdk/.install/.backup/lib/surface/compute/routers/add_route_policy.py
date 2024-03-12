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

"""Command for adding an empty route policy to a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.util.apis import arg_utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddRoutePolicy(base.CreateCommand):
  """Add an empty route policy to a Compute Engine router.

  *{command}* adds an empty route policy to a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    AddRoutePolicy.ROUTER_ARG = flags.RouterArgument()
    AddRoutePolicy.ROUTER_ARG.AddArgument(parser, operation_type='insert')
    parser.add_argument(
        '--policy-name',
        help="""Name of the route policy to add.""",
        required=True,
    )
    parser.add_argument(
        '--policy-type',
        type=arg_utils.ChoiceToEnumName,
        choices={
            'IMPORT': 'The Route Policy is an Import Policy.',
            'EXPORT': 'The Route Policy is an Export Policy.',
        },
        help="""Type of the route policy to add.""",
        required=True,
    )

  def Run(self, args):
    """Issues the requests needed for adding an empty route policy to a Router.

    Args:
      args: contains arguments passed to the command.

    Returns:
      The result of patching the router adding the empty route policy.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = AddRoutePolicy.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )
    route_policy = client.messages.RoutePolicy(
        name=args.policy_name,
        type=client.messages.RoutePolicy.TypeValueValuesEnum(
            self.ConvertRouteType(args.policy_type)
        ),
    )

    self.RequireRoutePolicyDoesNotExist(client, router_ref, args.policy_name)
    request = (
        client.apitools_client.routers,
        'UpdateRoutePolicy',
        client.messages.ComputeRoutersUpdateRoutePolicyRequest(
            **router_ref.AsDict(), routePolicy=route_policy
        ),
    )

    return client.MakeRequests([request])[0]

  def RequireRoutePolicyDoesNotExist(self, client, router_ref, policy_name):
    request = (
        client.apitools_client.routers,
        'GetRoutePolicy',
        client.messages.ComputeRoutersGetRoutePolicyRequest(
            **router_ref.AsDict(), policy=policy_name
        ),
    )
    try:
      client.MakeRequests([request])
    except Exception as exception:
      if (
          "Could not fetch resource:\n - Invalid value for field 'policy': "
          in exception.__str__()
      ):
        return
      raise
    raise exceptions.BadArgumentException(
        'policy-name', "A policy named '{0}' already exists".format(policy_name)
    )

  def ConvertRouteType(self, route_type):
    if route_type == 'IMPORT':
      return 'ROUTE_POLICY_TYPE_IMPORT'
    elif route_type == 'EXPORT':
      return 'ROUTE_POLICY_TYPE_EXPORT'
    else:
      return route_type
