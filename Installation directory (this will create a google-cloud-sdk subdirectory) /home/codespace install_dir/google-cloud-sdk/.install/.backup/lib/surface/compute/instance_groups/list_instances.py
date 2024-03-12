# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for listing instances in instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


class ListInstances(base.ListCommand):
  """List Compute Engine instances present in instance group."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(instance.basename():label=NAME,
          instance.scope().segment(0):label=ZONE,
          status)""")
    parser.display_info.AddUriFunc(
        instance_groups_utils.UriFuncForListInstanceRelatedObjects)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG.AddArgument(parser)
    flags.AddRegexArg(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """Retrieves response with instance in the instance group."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = (
        instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG.ResolveAsResource(
            args, holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(client)))

    if args.regexp:
      # Regexp interprested as RE2 by Instance Group API
      filter_expr = 'instance eq {0}'.format(args.regexp)
    else:
      filter_expr = None

    if group_ref.Collection() == 'compute.instanceGroups':
      service = client.apitools_client.instanceGroups
      request = client.messages.ComputeInstanceGroupsListInstancesRequest(
          instanceGroup=group_ref.Name(),
          instanceGroupsListInstancesRequest=(
              client.messages.InstanceGroupsListInstancesRequest()),
          zone=group_ref.zone,
          filter=filter_expr,
          project=group_ref.project)
    else:
      service = client.apitools_client.regionInstanceGroups
      request = client.messages.ComputeRegionInstanceGroupsListInstancesRequest(
          instanceGroup=group_ref.Name(),
          regionInstanceGroupsListInstancesRequest=(
              client.messages.RegionInstanceGroupsListInstancesRequest()),
          region=group_ref.region,
          filter=filter_expr,
          project=group_ref.project)

    errors = []
    results = request_helper.MakeRequests(
        requests=[(service, 'ListInstances', request)],
        http=client.apitools_client.http,
        batch_url=client.batch_url,
        errors=errors)

    if errors:
      utils.RaiseToolException(errors)
    return results


ListInstances.detailed_help = {
    'brief':
        'List instances present in the instance group',
    'DESCRIPTION':
        """\
          *{command}* list instances in an instance group.

          The required permission to execute this command is
          `compute.instanceGroups.list`. If needed, you can include this
          permission, or choose any of the following preexisting IAM roles
          that contain this particular permission:

          *   Compute Admin
          *   Compute Viewer
          *   Compute Instance Admin (v1)
          *   Compute Instance Admin (beta)
          *   Compute Network Admin
          *   Compute Network Viewer
          *   Editor
          *   Owner
          *   Security Reviewer
          *   Viewer

          For more information regarding permissions required by
          instance groups, refer to Compute Engine's access control guide:
          https://cloud.google.com/compute/docs/access/iam.
        """,
}
