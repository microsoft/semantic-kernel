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

"""Command for describing queued resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags

DETAILED_HELP = {
    'brief': (
        'Describe a Compute Engine managed instance group resize request'
        ' resource.'
    ),
    'EXAMPLES': """

     To describe a resize request for a managed instance group, run the following command:

       $ {command} my-mig --resize-request=resize-request-1
   """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a Compute Engine managed instance group resize request resource.

  *{command}* describes a Compute Engine managed instance group resize request
  resource.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(
        parser)
    parser.add_argument(
        '--resize-request',
        metavar='RESIZE_REQUEST_NAME',
        type=str,
        required=True,
        help="""The name of the resize request to describe.""")

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.get request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      Detailed information about resize request.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister)

    requests = [(
        client.apitools_client.instanceGroupManagerResizeRequests,
        'Get',
        client.messages.ComputeInstanceGroupManagerResizeRequestsGetRequest(
            project=igm_ref.project,
            zone=igm_ref.zone,
            instanceGroupManager=igm_ref.instanceGroupManager,
            resizeRequest=args.resize_request,
        ),
    )]
    return client.MakeRequests(requests)[0]
