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
"""Command for updating instances in a managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as instance_groups_managed_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import update_instances_utils


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateInstances(base.Command):
  r"""Immediately update selected instances in a Compute Engine managed instance group."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
        table(project(),
              zone(),
              instanceName:label=INSTANCE,
              status)""")
    instance_groups_managed_flags.AddUpdateInstancesArgs(parser=parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
               .ResolveAsResource)(
                   args,
                   holder.resources,
                   default_scope=compute_scope.ScopeEnum.ZONE,
                   scope_lister=flags.GetDefaultScopeLister(client))

    update_instances_utils.ValidateIgmReference(igm_ref)

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      minimal_action = update_instances_utils.ParseInstanceActionFlag(
          '--minimal-action', args.minimal_action or 'none',
          client.messages.InstanceGroupManagersApplyUpdatesRequest
          .MinimalActionValueValuesEnum)
      most_disruptive_allowed_action = (
          update_instances_utils.ParseInstanceActionFlag)(
              '--most-disruptive-allowed-action',
              args.most_disruptive_allowed_action or 'replace',
              client.messages.InstanceGroupManagersApplyUpdatesRequest
              .MostDisruptiveAllowedActionValueValuesEnum)
      instances_holder_field = 'instanceGroupManagersApplyUpdatesRequest'
      request = self._CreateZonalApplyUpdatesRequest(
          igm_ref, minimal_action, most_disruptive_allowed_action, client)
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      minimal_action = update_instances_utils.ParseInstanceActionFlag(
          '--minimal-action', args.minimal_action or 'none',
          client.messages.RegionInstanceGroupManagersApplyUpdatesRequest
          .MinimalActionValueValuesEnum)
      most_disruptive_allowed_action = (
          update_instances_utils.ParseInstanceActionFlag)(
              '--most-disruptive-allowed-action',
              args.most_disruptive_allowed_action or 'replace',
              client.messages.RegionInstanceGroupManagersApplyUpdatesRequest
              .MostDisruptiveAllowedActionValueValuesEnum)
      instances_holder_field = 'regionInstanceGroupManagersApplyUpdatesRequest'
      request = self._CreateRegionalApplyUpdatesRequest(
          igm_ref, minimal_action, most_disruptive_allowed_action, client)
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    if args.all_instances:
      return instance_groups_utils.SendAllInstancesRequest(
          api_holder=holder,
          method_name='ApplyUpdatesToInstances',
          request_template=request,
          all_instances_holder_field=instances_holder_field,
          igm_ref=igm_ref)
    else:
      return instance_groups_utils.SendInstancesRequestsAndPostProcessOutputs(
          api_holder=holder,
          method_name='ApplyUpdatesToInstances',
          request_template=request,
          instances_holder_field=instances_holder_field,
          igm_ref=igm_ref,
          instances=args.instances)

  def _CreateZonalApplyUpdatesRequest(self, igm_ref, minimal_action,
                                      most_disruptive_allowed_action, client):
    return client.messages.ComputeInstanceGroupManagersApplyUpdatesToInstancesRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagersApplyUpdatesRequest=client.messages
        .InstanceGroupManagersApplyUpdatesRequest(
            instances=[],
            minimalAction=minimal_action,
            mostDisruptiveAllowedAction=most_disruptive_allowed_action),
        project=igm_ref.project,
        zone=igm_ref.zone)

  def _CreateRegionalApplyUpdatesRequest(self, igm_ref, minimal_action,
                                         most_disruptive_allowed_action,
                                         client):
    return client.messages.ComputeRegionInstanceGroupManagersApplyUpdatesToInstancesRequest(
        instanceGroupManager=igm_ref.Name(),
        regionInstanceGroupManagersApplyUpdatesRequest=client.messages
        .RegionInstanceGroupManagersApplyUpdatesRequest(
            instances=[],
            minimalAction=minimal_action,
            mostDisruptiveAllowedAction=most_disruptive_allowed_action),
        project=igm_ref.project,
        region=igm_ref.region,
    )


UpdateInstances.detailed_help = {
    'brief':
        'Immediately update selected instances in a Compute Engine '
        'managed instance group.',
    'DESCRIPTION':
        """\
          When using a managed instance group, it's possible that your intended
          specification for a VM is different from the current state of that VM. For
          example, this can happen due to changes to the group's target instance
          template. This command enables you to initiate the update process on the given
          set of instances instantly, thus when your Managed Instance Group is stable
          you can be sure that all the changes were applied.

          *{command}* allows you to specify the least and the most disruptive actions
          that can be performed while updating the instances. This way you can reduce
          the risk of rolling out too many changes at once. Possible actions are:
          `none`, `refresh`, `restart` and `replace`. The level of disruption to the
          instance is ordered as: `none` < `refresh` < `restart` < `replace`.

          The command returns the operation status per instance, which might be
          ``FAIL'', ``SUCCESS'', or ``MEMBER_NOT_FOUND''. ``MEMBER_NOT_FOUND''
          is returned only for regional groups when the gcloud command-line tool
          wasn't able to resolve the zone from the instance name.
        """,
    'EXAMPLES':
        """\
        To update instances `instance-1`, `instance-2` in `my-group`,
        with `minimal-action=none` and `most-disruptive-allowed-action=restart`,
        run:

            $ {command} \\
                  my-group --instances=instance-1,instance2 \\
                  --minimal-action=none
                  --most-disruptive-allowed-action=restart
        """
}
