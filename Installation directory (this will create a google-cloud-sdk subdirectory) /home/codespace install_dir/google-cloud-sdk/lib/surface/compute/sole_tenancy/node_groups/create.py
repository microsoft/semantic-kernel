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
"""Create node group command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.sole_tenancy.node_groups import flags
from googlecloudsdk.command_lib.compute.sole_tenancy.node_groups import util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine node group."""

  detailed_help = {
      'brief': 'Create a Compute Engine node group.',
      'EXAMPLES': """
         To create a node group, run:

           $ {command} my-node-group --node-template=example-template --target-size=4
       """,
  }

  @staticmethod
  def Args(parser):
    flags.MakeNodeGroupArg().AddArgument(parser)
    flags.AddCreateArgsToParser(parser)
    flags.AddAutoscalingPolicyArgToParser(parser, required_mode=True)
    flags.AddMaintenanceWindowArgToParser(parser)
    flags.AddLocationHintArgToParser(parser)
    flags.AddShareSettingArgToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    node_group_ref = flags.MakeNodeGroupArg().ResolveAsResource(
        args, holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    node_template_ref = util.ParseNodeTemplate(
        holder.resources,
        args.node_template,
        project=node_group_ref.project,
        region=compute_utils.ZoneNameToRegionName(node_group_ref.zone))

    node_group = messages.NodeGroup(
        name=node_group_ref.Name(),
        description=args.description,
        nodeTemplate=node_template_ref.SelfLink())

    if hasattr(args, 'maintenance_policy'):
      mapper = flags.GetMaintenancePolicyEnumMapper(messages)
      maintenance_policy = mapper.GetEnumForChoice(args.maintenance_policy)
      node_group.maintenancePolicy = maintenance_policy

    if hasattr(args, 'maintenance_interval'):
      mapper = flags.GetMaintenanceIntervalEnumMapper(messages)
      maintenance_interval = mapper.GetEnumForChoice(args.maintenance_interval)
      node_group.maintenanceInterval = maintenance_interval

    if hasattr(args, 'autoscaler_mode') and args.autoscaler_mode:
      if args.autoscaler_mode != 'off' and args.max_nodes is None:
        raise exceptions.RequiredArgumentException('--max-nodes',
                                                   '--autoscaler-mode is on')
      autoscaling_policy = util.BuildAutoscaling(args, messages)
      node_group.autoscalingPolicy = autoscaling_policy

    if args.maintenance_window_start_time:
      node_group.maintenanceWindow = messages.NodeGroupMaintenanceWindow(
          startTime=args.maintenance_window_start_time)

    if hasattr(args, 'location_hint') and args.location_hint:
      node_group.locationHint = args.location_hint

    if args.share_setting:
      node_group.shareSettings = util.BuildShareSettings(messages, args)

    request = messages.ComputeNodeGroupsInsertRequest(
        nodeGroup=node_group,
        initialNodeCount=args.target_size,
        project=node_group_ref.project,
        zone=node_group_ref.zone)

    service = holder.client.apitools_client.nodeGroups
    return client.MakeRequests([(service, 'Insert', request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Compute Engine node group."""

  @staticmethod
  def Args(parser):
    Create.Args(parser)
    flags.AddMaintenanceIntervalArgToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Compute Engine node group."""

  @staticmethod
  def Args(parser):
    Create.Args(parser)
    flags.AddMaintenanceIntervalArgToParser(parser)
