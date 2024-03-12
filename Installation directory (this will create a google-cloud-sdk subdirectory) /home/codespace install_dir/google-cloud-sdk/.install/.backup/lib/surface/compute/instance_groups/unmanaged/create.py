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

"""Command for creating unmanaged instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.unmanaged import flags as instance_groups_unmanaged_flags


class Create(base.CreateCommand):
  """Create a Compute Engine unmanaged instance group.

    *{command}* creates a new Compute Engine unmanaged
  instance group.
  For example:

    $ {command} example-instance-group --zone us-central1-a

  The above example creates one unmanaged instance group called
  'example-instance-group' in the ``us-central1-a'' zone.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(instance_groups_unmanaged_flags.LIST_FORMAT)
    Create.ZONAL_INSTANCE_GROUP_ARG = (
        instance_groups_flags.MakeZonalInstanceGroupArg())
    Create.ZONAL_INSTANCE_GROUP_ARG.AddArgument(parser, operation_type='create')
    parser.add_argument(
        '--description',
        help=('Specifies a textual description for the '
              'unmanaged instance group.'))

  def Run(self, args):
    """Creates and returns an InstanceGroups.Insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      request: a ComputeInstanceGroupsInsertRequest message object
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = (
        Create.ZONAL_INSTANCE_GROUP_ARG.ResolveAsResource(
            args, holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(client)))
    zone_resource_fetcher = zone_utils.ZoneResourceFetcher(client)
    zone_resource_fetcher.WarnForZonalCreation([group_ref])

    request = client.messages.ComputeInstanceGroupsInsertRequest(
        instanceGroup=client.messages.InstanceGroup(
            name=group_ref.Name(),
            description=args.description),
        zone=group_ref.zone,
        project=group_ref.project)

    return client.MakeRequests([(client.apitools_client.instanceGroups,
                                 'Insert', request)])
