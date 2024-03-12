# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for removing a NAT from a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags
from googlecloudsdk.command_lib.compute.routers.nats import flags as nats_flags
from googlecloudsdk.command_lib.compute.routers.nats import nats_utils


class AlphaDelete(base.DeleteCommand):
  """Remove a NAT from a Compute Engine router.

  *{command}* removes a NAT from a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)

    compute_flags.AddRegionFlag(
        parser, 'NAT', operation_type='delete', plural=True)

    nats_flags.AddNatNameArg(parser, operation_type='delete', plural=True)

  def _GetPatchRequest(self, client, router_ref, replacement):
    return (client.apitools_client.routers, 'Patch',
            client.messages.ComputeRoutersPatchRequest(
                router=router_ref.Name(),
                routerResource=replacement,
                region=router_ref.region,
                project=router_ref.project))

  def Modify(self, args, existing, cleared_fields):
    """Mutate the router and record any cleared_fields for Patch request."""
    replacement = encoding.CopyProtoMessage(existing)

    for name in args.name:
      nat = nats_utils.FindNatOrRaise(replacement, name)
      replacement.nats.remove(nat)

    # If all NATs have been removed, add this field to cleared_fields.
    if not replacement.nats:
      cleared_fields.append('nats')

    return replacement

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    objects = client.MakeRequests(
        [(client.apitools_client.routers, 'Get',
          client.messages.ComputeRoutersGetRequest(**router_ref.AsDict()))])

    # Cleared list fields need to be explicitly identified for Patch API.
    cleared_fields = []
    new_object = self.Modify(args, objects[0], cleared_fields)

    utils.PromptForDeletionHelper(
        'NAT', ['{} in router {}'.format(args.name, router_ref.Name())])

    with client.apitools_client.IncludeFields(cleared_fields):
      # There is only one response because one request is made above
      result = client.MakeRequests(
          [self._GetPatchRequest(client, router_ref, new_object)])
    return result


AlphaDelete.detailed_help = {
    'DESCRIPTION':
        textwrap.dedent("""\
          *{command}* is used to delete a NAT on a Compute Engine router.
    """),
    'EXAMPLES':
    """\
    To delete NAT 'n1' in router 'r1', run:

      $ {command} n1 --router=r1 --region=us-central1
    """,
    'API REFERENCE':
    """\
    This command, when specified without alpha or beta, uses the compute/v1/routers API. The full documentation
    for this API can be found at: https://cloud.google.com/compute/docs/reference/rest/v1/routers/

    The beta command uses the compute/beta/routers API. The full documentation
    for this API can be found at: https://cloud.google.com/compute/docs/reference/rest/beta/routers/

    The alpha command uses the compute/alpha/routers API. Full documentation is not available for the alpha API.
    """
}
