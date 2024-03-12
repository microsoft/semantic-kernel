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
"""Update node group command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.sole_tenancy import node_groups
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.sole_tenancy.node_groups import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Compute Engine node group."""

  detailed_help = {
      'brief':
          'Update a Compute Engine node group.',
      'EXAMPLES':
          """
         To update a node group to have two more nodes, run:

           $ {command} my-node-group --add-nodes=2
       """
  }

  @staticmethod
  def Args(parser):
    flags.MakeNodeGroupArg().AddArgument(parser)
    flags.AddUpdateArgsToParser(parser)
    flags.AddAutoscalingPolicyArgToParser(parser)
    flags.AddShareSettingArgToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    groups_client = node_groups.NodeGroupsClient(holder.client.apitools_client,
                                                 messages, holder.resources)

    node_group_ref = flags.MakeNodeGroupArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    autoscaling_policy = (hasattr(args, 'autoscaler_mode') and args.IsSpecified('autoscaler_mode')) or \
                         (hasattr(args, 'min_nodes') and args.IsSpecified('min_nodes')) or \
                         (hasattr(args, 'max_nodes') and args.IsSpecified('max_nodes'))

    share_setting = (
        args.IsSpecified('share_setting') or args.IsSpecified('share_with'))

    return groups_client.Update(
        node_group_ref,
        node_template=args.node_template,
        additional_node_count=args.add_nodes,
        delete_nodes=args.delete_nodes,
        autoscaling_policy_args=args if autoscaling_policy else None,
        share_setting_args=args if share_setting else None)
