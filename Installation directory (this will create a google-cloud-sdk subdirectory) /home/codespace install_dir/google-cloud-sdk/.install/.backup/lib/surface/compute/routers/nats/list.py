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
"""Command to list NATs on a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags
from googlecloudsdk.command_lib.compute.routers.nats import flags as nats_flags


class List(base.DescribeCommand):
  """Lists the NATs on a Compute Engine router."""

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgumentForNat()
    cls.ROUTER_ARG.AddArgument(parser)
    parser.display_info.AddFormat(nats_flags.DEFAULT_LIST_FORMAT)

    compute_flags.AddRegionFlag(parser, 'NATs', operation_type='list')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    request_type = messages.ComputeRoutersGetRequest
    router = service.Get(request_type(**router_ref.AsDict()))

    return router.nats


List.detailed_help = {
    'DESCRIPTION':
        textwrap.dedent("""\
        *{command}* is used to list the NATs on a Compute Engine router.
     """),
    'EXAMPLES':
    """\
    To list all NATs in router ``r1'' in region ``us-central1'', run:

        $ {command} --router=r1 --region=us-central1.
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
