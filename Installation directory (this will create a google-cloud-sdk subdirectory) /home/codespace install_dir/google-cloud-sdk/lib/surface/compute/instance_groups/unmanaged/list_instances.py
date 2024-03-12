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


class ListInstances(base.ListCommand):
  """Lists instances attached to specified Instance Group."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(instance.basename():label=NAME, status)')
    parser.display_info.AddUriFunc(
        instance_groups_utils.UriFuncForListInstanceRelatedObjects)
    ListInstances.ZonalInstanceGroupArg = (
        instance_groups_flags.MakeZonalInstanceGroupArg())
    ListInstances.ZonalInstanceGroupArg.AddArgument(parser)
    flags.AddRegexArg(parser)

  def Run(self, args):
    """Retrieves response with instance in the instance group."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    # Note: only zonal resources parsed here.
    group_ref = (
        ListInstances.ZonalInstanceGroupArg.ResolveAsResource(
            args, holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(client)))

    if args.regexp:
      filter_expr = 'instance eq {0}'.format(args.regexp)
    else:
      filter_expr = None

    request = client.messages.ComputeInstanceGroupsListInstancesRequest(
        instanceGroup=group_ref.Name(),
        instanceGroupsListInstancesRequest=(
            client.messages.InstanceGroupsListInstancesRequest()),
        zone=group_ref.zone,
        filter=filter_expr,
        project=group_ref.project)

    errors = []
    results = list(
        request_helper.MakeRequests(
            requests=[(client.apitools_client.instanceGroups, 'ListInstances',
                       request)],
            http=client.apitools_client.http,
            batch_url=client.batch_url,
            errors=errors))

    if errors:
      utils.RaiseToolException(errors)

    return results


ListInstances.detailed_help = {
    'brief':
        'List instances present in the instance group',
    'DESCRIPTION':
        """\
        *{command}* list instances in an instance group.
        """,
}
