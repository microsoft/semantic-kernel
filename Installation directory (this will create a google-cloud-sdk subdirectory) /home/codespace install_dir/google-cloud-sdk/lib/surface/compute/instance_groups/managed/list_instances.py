# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""managed-instance-groups list-instances command.

It's an alias for the instance-groups list-instances command.
"""

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


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListInstances(base.ListCommand):
  """List Compute Engine instances present in managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.AddListInstancesOutputFormat(parser)
    parser.display_info.AddUriFunc(
        instance_groups_utils.UriFuncForListInstanceRelatedObjects)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    """Retrieves response with instance in the instance group."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
                 ResolveAsResource(
                     args,
                     holder.resources,
                     default_scope=compute_scope.ScopeEnum.ZONE,
                     scope_lister=flags.GetDefaultScopeLister(client)))

    if hasattr(group_ref, 'zone'):
      service = client.apitools_client.instanceGroupManagers
      request = (client.messages.
                 ComputeInstanceGroupManagersListManagedInstancesRequest(
                     instanceGroupManager=group_ref.Name(),
                     zone=group_ref.zone,
                     project=group_ref.project))
    elif hasattr(group_ref, 'region'):
      service = client.apitools_client.regionInstanceGroupManagers
      request = (client.messages.
                 ComputeRegionInstanceGroupManagersListManagedInstancesRequest(
                     instanceGroupManager=group_ref.Name(),
                     region=group_ref.region,
                     project=group_ref.project))

    errors = []
    results = list(request_helper.MakeRequests(
        requests=[(service, 'ListManagedInstances', request)],
        http=client.apitools_client.http,
        batch_url=client.batch_url,
        errors=errors))

    if errors:
      utils.RaiseToolException(errors)
    return results


ListInstances.detailed_help = {
    'brief':
        'List instances present in the managed instance group',
    'DESCRIPTION':
        """\
          *{command}* lists instances in a managed instance group.

          The required permission to execute this command is
          `compute.instanceGroupManagers.list`. If needed, you can include this
          permission, or choose any of the following preexisting IAM roles
          that contain this particular permission:

          *   Compute Admin
          *   Compute Viewer
          *   Compute Instance Admin (v1)
          *   Compute Instance Admin (beta)
          *   Compute Network Admin
          *   Editor
          *   Owner
          *   Security Reviewer
          *   Viewer

          For more information regarding permissions required by managed
          instance groups, refer to Compute Engine's access control guide :
          https://cloud.google.com/compute/docs/access/iam#managed-instance-groups-and-iam.
        """,
    'EXAMPLES':
        """\
        To see additional details about the instances in a managed instance
        group `my-group`, including per-instance overrides, run:

            $ {command} \\
                  my-group --format=yaml
        """
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListInstancesBeta(ListInstances):
  """List Compute Engine instances present in managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.AddListInstancesOutputFormat(
        parser, release_track=base.ReleaseTrack.BETA)
    parser.display_info.AddUriFunc(
        instance_groups_utils.UriFuncForListInstanceRelatedObjects)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)


ListInstancesBeta.detailed_help = ListInstances.detailed_help


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListInstancesAlpha(ListInstances):
  """List Compute Engine instances present in managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.AddListInstancesOutputFormat(
        parser, release_track=base.ReleaseTrack.ALPHA)
    parser.display_info.AddUriFunc(
        instance_groups_utils.UriFuncForListInstanceRelatedObjects)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)


ListInstancesAlpha.detailed_help = ListInstancesBeta.detailed_help
