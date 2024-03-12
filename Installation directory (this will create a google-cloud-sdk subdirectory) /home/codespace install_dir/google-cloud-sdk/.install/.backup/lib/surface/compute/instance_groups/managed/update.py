# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for updating managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute.instance_groups.managed import stateful_policy_utils as policy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as managed_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import auto_healing_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
import six

# Flags valid only for regional MIGs.
REGIONAL_FLAGS = ['instance_redistribution_type', 'target_distribution_shape']


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  r"""Update a Compute Engine managed instance group."""

  support_update_policy_min_ready_flag = False

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser, operation_type='update')

    autohealing_group = parser.add_mutually_exclusive_group()
    autohealing_group.add_argument(
        '--clear-autohealing',
        action='store_true',
        default=None,
        help="""\
        Clears all autohealing policy fields for the managed instance group.
        """)
    autohealing_params_group = autohealing_group.add_group()
    auto_healing_utils.AddAutohealingArgs(autohealing_params_group)
    instance_groups_flags.AddMigUpdateStatefulFlags(parser)
    instance_groups_flags.AddMigUpdateStatefulFlagsIPs(parser)
    instance_groups_flags.AddDescriptionFlag(parser, for_update=True)
    managed_flags.AddMigInstanceRedistributionTypeFlag(parser)
    managed_flags.AddMigDistributionPolicyTargetShapeFlag(parser)
    managed_flags.AddMigListManagedInstancesResultsFlag(parser)
    managed_flags.AddMigUpdatePolicyFlags(
        parser, support_min_ready_flag=cls.support_update_policy_min_ready_flag)
    managed_flags.AddMigForceUpdateOnRepairFlags(parser)
    managed_flags.AddMigDefaultActionOnVmFailure(parser)
    # When adding RMIG-specific flag, update REGIONAL_FLAGS constant.

  def _GetUpdatedStatefulPolicyForDisks(self,
                                        client,
                                        current_stateful_policy,
                                        update_disks=None,
                                        remove_device_names=None):
    patched_disks_map = {}
    if remove_device_names:
      managed_instance_groups_utils.RegisterCustomStatefulDisksPatchEncoders(
          client)
    else:
      # Extract disk protos from current stateful policy proto
      if (current_stateful_policy and current_stateful_policy.preservedState and
          current_stateful_policy.preservedState.disks):
        current_disks = (
            current_stateful_policy.preservedState.disks.additionalProperties)
      else:
        current_disks = []
      # Map of disks to have in the stateful policy, after updating and removing
      # the disks specified by the update and remove flags.
      patched_disks_map = {
          disk_entry.key: disk_entry for disk_entry in current_disks
      }

    # Update the disks specified in --stateful-disk
    for update_disk in (update_disks or []):
      device_name = update_disk.get('device-name')
      updated_preserved_state_disk = (
          policy_utils.MakeStatefulPolicyPreservedStateDiskEntry(
              client.messages, update_disk))
      # Patch semantics on the `--stateful-disk` flag
      if device_name in patched_disks_map:
        policy_utils.PatchStatefulPolicyDisk(patched_disks_map[device_name],
                                             updated_preserved_state_disk)
      else:
        patched_disks_map[device_name] = updated_preserved_state_disk

    # Remove the disks specified in --remove-stateful-disks
    for device_name in remove_device_names or []:
      patched_disks_map[
          device_name] = policy_utils.MakeDiskDeviceNullEntryForDisablingInPatch(
              client, device_name)

    stateful_disks = sorted([
        stateful_disk for _, stateful_disk in six.iteritems(patched_disks_map)
    ],
                            key=lambda x: x.key)
    return stateful_disks

  def _GetUpdatedStatefulPolicy(self, client, current_stateful_policy, args):
    """Create an updated stateful policy based on specified args."""
    update_disks = args.stateful_disk
    remove_device_names = args.remove_stateful_disks
    stateful_disks = self._GetUpdatedStatefulPolicyForDisks(
        client, current_stateful_policy, update_disks, remove_device_names)

    stateful_policy = policy_utils.MakeStatefulPolicy(
        client.messages, stateful_disks
    )

    stateful_internal_ips = self._GetPatchForStatefulPolicyForInternalIPs(
        client, args.stateful_internal_ip, args.remove_stateful_internal_ips
    )

    stateful_external_ips = self._GetPatchForStatefulPolicyForExternalIPs(
        client, args.stateful_external_ip, args.remove_stateful_external_ips
    )

    return policy_utils.UpdateStatefulPolicy(
        client.messages,
        stateful_policy,
        None,
        stateful_internal_ips,
        stateful_external_ips,
    )

  def _StatefulArgsSet(self, args):
    return (
        args.IsSpecified('stateful_disk')
        or args.IsSpecified('remove_stateful_disks')
        or args.IsSpecified('stateful_internal_ip')
        or args.IsSpecified('remove_stateful_internal_ips')
        or args.IsSpecified('stateful_external_ip')
        or args.IsSpecified('remove_stateful_external_ips')
    )

  def _StatefulnessIntroduced(self, args):
    return (
        args.IsSpecified('stateful_disk')
        or args.IsSpecified('stateful_internal_ip')
        or args.IsSpecified('stateful_external_ip')
    )

  def _ValidateStatefulPolicyParams(self, args, stateful_policy):
    instance_groups_flags.ValidateUpdateStatefulPolicyParams(
        args, stateful_policy
    )
    instance_groups_flags.ValidateUpdateStatefulPolicyParamsWithIPs(
        args, stateful_policy
    )

  def _GetStatefulPolicyPatchForStatefulIPsCommon(
      self,
      client,
      update_ip_to_ip_entry_lambda,
      update_ip_to_none_lambda,
      update_ips=None,
      remove_interface_names=None,
  ):
    if remove_interface_names:
      managed_instance_groups_utils.RegisterCustomStatefulIpsPatchEncoders(
          client
      )
    patched_ips_map = {}

    # Update the interfaces specified in IPs to be updated.
    for update_ip in update_ips or []:
      # Interface name is optional, use the default if not specified.
      interface_name = update_ip.get(
          'interface-name',
          instance_groups_flags.STATEFUL_IP_DEFAULT_INTERFACE_NAME,
      )
      updated_preserved_state_ip = update_ip_to_ip_entry_lambda(update_ip)
      patched_ips_map[interface_name] = updated_preserved_state_ip

    # Remove the interfaces specified for removal.
    for interface_name in remove_interface_names or []:
      updated_preserved_state_ip = update_ip_to_none_lambda(interface_name)
      patched_ips_map[interface_name] = updated_preserved_state_ip

    stateful_ips = sorted(
        [stateful_ip for key, stateful_ip in six.iteritems(patched_ips_map)],
        key=lambda x: x.key,
    )
    return stateful_ips

  def _GetPatchForStatefulPolicyForInternalIPs(
      self, client, update_internal_ips=None, remove_interface_names=None
  ):
    # Extract internal IPs protos from current stateful policy proto.
    return self._GetStatefulPolicyPatchForStatefulIPsCommon(
        client,
        functools.partial(policy_utils.MakeInternalIPEntry, client.messages),
        functools.partial(
            policy_utils.MakeInternalIPNullEntryForDisablingInPatch, client
        ),
        update_internal_ips,
        remove_interface_names,
    )

  def _GetPatchForStatefulPolicyForExternalIPs(
      self, client, update_external_ips=None, remove_interface_names=None
  ):
    return self._GetStatefulPolicyPatchForStatefulIPsCommon(
        client,
        functools.partial(policy_utils.MakeExternalIPEntry, client.messages),
        functools.partial(
            policy_utils.MakeExternalIPNullEntryForDisablingInPatch, client
        ),
        update_external_ips,
        remove_interface_names,
    )

  def _PatchStatefulPolicy(self, igm_patch, args, igm_resource, client, holder):
    """Patch the stateful policy specified in args, to igm_patch."""
    # If we're potentially introducing statefulness to the MIG, we should
    # validate if this MIG is allowed to be stateful
    if self._StatefulnessIntroduced(args):
      managed_instance_groups_utils.ValidateIgmReadyForStatefulness(
          igm_resource, client)
    self._ValidateStatefulPolicyParams(args, igm_resource.statefulPolicy)

    igm_patch.statefulPolicy = self._GetUpdatedStatefulPolicy(
        client, igm_resource.statefulPolicy, args)
    return igm_patch

  def _GetValidatedAutohealingPolicies(self, holder, client, args,
                                       igm_resource):
    health_check = managed_instance_groups_utils.GetHealthCheckUri(
        holder.resources, args)
    auto_healing_policies = (
        managed_instance_groups_utils.ModifyAutohealingPolicies(
            igm_resource.autoHealingPolicies, client.messages, args,
            health_check))
    managed_instance_groups_utils.ValidateAutohealingPolicies(
        auto_healing_policies)
    return auto_healing_policies

  def _PatchTargetDistributionShape(self, patch_instance_group_manager,
                                    target_distribution_shape, igm_resource,
                                    client):
    distribution_policy = igm_resource.distributionPolicy
    if distribution_policy is None:
      distribution_policy = client.messages.DistributionPolicy()
    distribution_policy.targetShape = arg_utils.ChoiceToEnum(
        target_distribution_shape,
        client.messages.DistributionPolicy.TargetShapeValueValuesEnum)
    patch_instance_group_manager.distributionPolicy = distribution_policy

  def _MakePatchRequest(self, client, igm_ref, igm_updated_resource):
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = client.apitools_client.instanceGroupManagers
      request = client.messages.ComputeInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_updated_resource,
          project=igm_ref.project,
          zone=igm_ref.zone)
    else:
      service = client.apitools_client.regionInstanceGroupManagers
      request = client.messages.ComputeRegionInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_updated_resource,
          project=igm_ref.project,
          region=igm_ref.region)
    return client.MakeRequests([(service, 'Patch', request)])

  def _CreateInstanceGroupManagerPatch(self, args, igm_ref, igm_resource,
                                       client, holder):
    """Create IGM resource patch."""
    managed_flags.ValidateRegionalMigFlagsUsage(args, REGIONAL_FLAGS, igm_ref)
    patch_instance_group_manager = client.messages.InstanceGroupManager()
    auto_healing_policies = self._GetValidatedAutohealingPolicies(
        holder, client, args, igm_resource)
    if auto_healing_policies is not None:
      patch_instance_group_manager.autoHealingPolicies = auto_healing_policies

    update_policy = managed_instance_groups_utils.PatchUpdatePolicy(
        client, args, igm_resource.updatePolicy)
    if update_policy is not None:
      patch_instance_group_manager.updatePolicy = update_policy

    if self._StatefulArgsSet(args):
      patch_instance_group_manager = (
          self._PatchStatefulPolicy(patch_instance_group_manager, args,
                                    igm_resource, client, holder))
    if args.target_distribution_shape:
      self._PatchTargetDistributionShape(patch_instance_group_manager,
                                         args.target_distribution_shape,
                                         igm_resource, client)
    if args.IsSpecified('description'):
      patch_instance_group_manager.description = args.description
    if args.IsSpecified('list_managed_instances_results'):
      patch_instance_group_manager.listManagedInstancesResults = (
          client.messages.InstanceGroupManager
          .ListManagedInstancesResultsValueValuesEnum)(
              args.list_managed_instances_results.upper())

    patch_instance_group_manager.instanceLifecyclePolicy = (
        managed_instance_groups_utils.CreateInstanceLifecyclePolicy(
            client.messages, args
        )
    )
    return patch_instance_group_manager

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
               .ResolveAsResource)(
                   args,
                   holder.resources,
                   default_scope=compute_scope.ScopeEnum.ZONE,
                   scope_lister=flags.GetDefaultScopeLister(client))

    if igm_ref.Collection() not in [
        'compute.instanceGroupManagers', 'compute.regionInstanceGroupManagers'
    ]:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    igm_resource = managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)

    patch_instance_group_manager = self._CreateInstanceGroupManagerPatch(
        args, igm_ref, igm_resource, client, holder)
    return self._MakePatchRequest(client, igm_ref, patch_instance_group_manager)


UpdateGA.detailed_help = {
    'brief':
        'Update a Compute Engine managed instance group.',
    'DESCRIPTION':
        """\
      Update a Compute Engine managed instance group.

      *{command}* allows you to specify or modify the description and group
      policies for an existing managed instance group, including the group's
      update policy and optional autohealing and stateful policies

      The group's update policy defines how an updated VM configuration is
      applied to existing VMs in the group. For more information, see
      [Applying new configurations]
      (https://cloud.google.com/compute/docs/instance-groups/updating-migs)
      to VMs in a MIG.

      A stateful policy defines which resources should be preserved across the
      group. When instances in the group are recreated, stateful resources are
      preserved. This command allows you to update stateful resources,
      specifically to add or remove stateful disks.

      When updating the autohealing policy, you can specify the health check,
      initial delay, or both. If either field is unspecified, its value won't
      be modified. If `--health-check` is specified, the health check monitors
      the health of your application. Whenever the health check signal for an
      instance becomes `UNHEALTHY`, the autohealer recreates the instance.

      If no health check exists, instance autohealing is triggered only by
      instance status: if an instance is not `RUNNING`, the group recreates it.
      """
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(UpdateGA):
  """Update a Compute Engine managed instance group."""

  support_update_policy_min_ready_flag = True

  @classmethod
  def Args(cls, parser):
    super(UpdateBeta, cls).Args(parser)
    managed_flags.AddStandbyPolicyFlags(parser)

  def _CreateInstanceGroupManagerPatch(self, args, igm_ref, igm_resource,
                                       client, holder):
    patch_instance_group_manager = super(UpdateBeta,
                                         self)._CreateInstanceGroupManagerPatch(
                                             args, igm_ref, igm_resource,
                                             client, holder)
    standby_policy = managed_instance_groups_utils.CreateStandbyPolicy(
        client.messages,
        args.standby_policy_initial_delay,
        args.standby_policy_mode,
    )
    if standby_policy:
      patch_instance_group_manager.standbyPolicy = standby_policy
    if args.suspended_size:
      patch_instance_group_manager.targetSuspendedSize = args.suspended_size
    if args.stopped_size:
      patch_instance_group_manager.targetStoppedSize = args.stopped_size
    return patch_instance_group_manager

UpdateBeta.detailed_help = UpdateGA.detailed_help


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Compute Engine managed instance group."""

  @classmethod
  def Args(cls, parser):
    super(UpdateAlpha, cls).Args(parser)

  def _CreateInstanceGroupManagerPatch(self, args, igm_ref, igm_resource,
                                       client, holder):
    igm_patch = super(UpdateAlpha, self)._CreateInstanceGroupManagerPatch(
        args, igm_ref, igm_resource, client, holder)

    return igm_patch

UpdateAlpha.detailed_help = UpdateBeta.detailed_help
