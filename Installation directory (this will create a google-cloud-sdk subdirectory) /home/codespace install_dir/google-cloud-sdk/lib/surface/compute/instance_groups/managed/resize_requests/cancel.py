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

"""Command for cancelling queued managed instance group resize requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags

DETAILED_HELP = {
    'brief': 'Cancel a Compute Engine managed instance group resize request.',
    'EXAMPLES': """

     To cancel a resize request for a managed instance group, run the following command:

       $ {command} my-mig --resize-requests=resize-request-1
   """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CancelBeta(base.UpdateCommand):
  """Cancel a Compute Engine managed instance group resize request.

  *{command}* cancels one or more Compute Engine managed instance group resize
  requests.

  You can only cancel a resize request when it is in the ACCEPTED state.
  """

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(parser)
    parser.add_argument(
        '--resize-requests',
        type=arg_parsers.ArgList(min_length=1),
        metavar='RESIZE_REQUEST_NAMES',
        required=True,
        help='A list of comma-separated names of resize requests to cancel.',
    )

  def _CreateResizeRequestReferences(self, resize_requests, igm_ref, resources):
    resize_request_references = []
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      for resize_request_name in resize_requests:
        resize_request_references.append(
            resources.Parse(
                resize_request_name,
                {
                    'project': igm_ref.project,
                    'zone': igm_ref.zone,
                    'instanceGroupManager': igm_ref.instanceGroupManager,
                },
                collection='compute.instanceGroupManagerResizeRequests',
            )
        )
      return resize_request_references
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.cancel requests.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      A list of URI paths of the successfully canceled resize requests.
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
        scope_lister=scope_lister,
    )

    resize_request_refs = self._CreateResizeRequestReferences(
        args.resize_requests, igm_ref, holder.resources
    )

    requests = []
    for resize_request_ref in resize_request_refs:
      requests.append((
          client.apitools_client.instanceGroupManagerResizeRequests,
          'Cancel',
          client.messages.ComputeInstanceGroupManagerResizeRequestsCancelRequest(
              project=igm_ref.project,
              zone=igm_ref.zone,
              instanceGroupManager=igm_ref.instanceGroupManager,
              resizeRequest=resize_request_ref.resizeRequest,
          ),
      ))
    return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CancelAlpha(CancelBeta):
  """Cancel a Compute Engine managed instance group resize request.

  *{command}* cancels one or more Compute Engine managed instance group resize
  requests.

  You can only cancel a resize request when it is in the ACCEPTED state.
  """

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(
        parser)
    rr_group = parser.add_group(mutex=True, required=True)
    rr_group.add_argument(
        '--resize-requests',
        type=arg_parsers.ArgList(min_length=1),
        metavar='RESIZE_REQUEST_NAMES',
        required=False,
        help='A list of comma-separated names of resize requests to cancel.',
    )
    rr_group.add_argument(
        '--resize-request',
        metavar='RESIZE_REQUEST_NAME',
        type=str,
        required=False,
        help="""(ALPHA only) The name of the resize request to cancel.""",
    )

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.cancel request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      A URI path of the successfully canceled resize request.
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

    if args.IsKnownAndSpecified('resize_request'):
      resize_request_refs = self._CreateResizeRequestReferences(
          [args.resize_request], igm_ref, holder.resources
      )
    else:
      resize_request_refs = self._CreateResizeRequestReferences(
          args.resize_requests, igm_ref, holder.resources
      )

    requests = []
    for resize_request_ref in resize_request_refs:
      requests.append((
          client.apitools_client.instanceGroupManagerResizeRequests,
          'Cancel',
          client.messages.ComputeInstanceGroupManagerResizeRequestsCancelRequest(
              project=igm_ref.project,
              zone=igm_ref.zone,
              instanceGroupManager=igm_ref.instanceGroupManager,
              resizeRequest=resize_request_ref.resizeRequest,
          ),
      ))
    return client.MakeRequests(requests)
