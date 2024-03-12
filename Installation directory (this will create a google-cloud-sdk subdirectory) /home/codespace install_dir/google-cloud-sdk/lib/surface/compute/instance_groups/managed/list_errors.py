# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""managed-instance-groups list-errors command.

Command for listing errors that are produced by managed instances in a managed
instance group.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListErrors(base.ListCommand):
  """List errors produced by managed instances in a managed instance group."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(instanceActionDetails.instance:label=INSTANCE_URL,
              instanceActionDetails.action:label=ACTION,
              error.code:label=ERROR_CODE,
              error.message:label=ERROR_MESSAGE,
              timestamp:label=TIMESTAMP,
              instanceActionDetails.version.instance_template:label=INSTANCE_TEMPLATE,
              instanceActionDetails.version.name:label=VERSION_NAME
        )""")
    parser.display_info.AddUriFunc(
        instance_groups_utils.UriFuncForListInstanceRelatedObjects)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = (
        instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
        .ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(client)))

    if hasattr(group_ref, 'zone'):
      service = client.apitools_client.instanceGroupManagers
      request = (
          client.messages.ComputeInstanceGroupManagersListErrorsRequest(
              instanceGroupManager=group_ref.Name(),
              zone=group_ref.zone,
              project=group_ref.project))

    elif hasattr(group_ref, 'region'):
      service = client.apitools_client.regionInstanceGroupManagers
      request = (
          client.messages.ComputeRegionInstanceGroupManagersListErrorsRequest(
              instanceGroupManager=group_ref.Name(),
              region=group_ref.region,
              project=group_ref.project))

    batch_size = 500
    if args.page_size is not None:
      batch_size = args.page_size

    results = list_pager.YieldFromList(
        service,
        request=request,
        method='ListErrors',
        field='items',
        batch_size=batch_size,
    )
    return results


ListErrors.detailed_help = {
    'brief':
        'List errors produced by managed instances in a managed instance group.',
    'DESCRIPTION':
        """\
        *{command}*
        List errors that are produced by managed instances in a managed instance
        group.

        The required permission to execute this command is
        `compute.instanceGroupManagers.list`. If needed, you can include this
        permission in a custom IAM role, or choose any of the following
        preexisting IAM roles that contain this particular permission:

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
        instance groups, refer to Compute Engine's access control guide:
        https://cloud.google.com/compute/docs/access/iam#managed-instance-groups-and-iam.
      """,
    'EXAMPLES':
        """\
        To list errors on managed instance group 'my-group', run:

            $ {command} \\
                  my-group --format=yaml
        """
}
