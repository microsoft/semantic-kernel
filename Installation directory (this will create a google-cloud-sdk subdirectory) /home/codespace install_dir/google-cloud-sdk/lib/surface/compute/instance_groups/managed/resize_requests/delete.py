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

"""Command for deleting managed instance group resize requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags

DETAILED_HELP = {
    'brief': 'Delete a Compute Engine managed instance group resize request.',
    'EXAMPLES': """

     To delete a resize request for a managed instance group, run the following command:

       $ {command} my-mig --resize-requests=resize-request-1
   """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete a Compute Engine managed instance group resize request.

  *{command}* deletes one or more Compute Engine managed instance
  group resize requests.

  You can only delete a request when it is in a state SUCCEEDED,
  FAILED, or CANCELLED.
  """

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(
        parser
    )
    parser.add_argument(
        '--resize-requests',
        type=arg_parsers.ArgList(min_length=1),
        metavar='RESIZE_REQUEST_NAMES',
        required=True,
        help='A list of comma-separated names of resize requests to delete.',
    )

  def _CreateResizeRequestReferences(self, resize_requests, igm_ref, resources):
    resize_request_references = []
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      for resize_request_name in resize_requests:
        resize_request_references.append(resources.Parse(
            resize_request_name,
            {
                'project': igm_ref.project,
                'zone': igm_ref.zone,
                'instanceGroupManager': igm_ref.instanceGroupManager,
            },
            collection='compute.instanceGroupManagerResizeRequests',
        ))
      return resize_request_references
    raise ValueError(
        'Unknown reference type {0}'.format(igm_ref.Collection())
    )

  def Run(self, args):
    """Creates and issues multiple instanceGroupManagerResizeRequests.delete requests.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      A list of URI paths of the successfully deleted resize requests.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = compute_flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister,
    )

    resize_requests_refs = self._CreateResizeRequestReferences(
        args.resize_requests, igm_ref, holder.resources
    )

    utils.PromptForDeletion(resize_requests_refs)

    requests = []
    for resize_request_ref in resize_requests_refs:
      requests.append((
          client.apitools_client.instanceGroupManagerResizeRequests,
          'Delete',
          client.messages.ComputeInstanceGroupManagerResizeRequestsDeleteRequest(
              project=resize_request_ref.project,
              zone=resize_request_ref.zone,
              instanceGroupManager=resize_request_ref.instanceGroupManager,
              resizeRequest=resize_request_ref.resizeRequest,
          ),
      ))
    return client.MakeRequests(requests)
