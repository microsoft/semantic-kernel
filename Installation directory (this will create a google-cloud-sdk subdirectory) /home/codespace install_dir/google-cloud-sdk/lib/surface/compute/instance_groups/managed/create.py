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
"""Command for creating managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.api_lib.compute.instance_groups.managed import stateful_policy_utils as policy_utils
from googlecloudsdk.api_lib.compute.managed_instance_groups_utils import ValueOrNone
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import resource_manager_tags_utils
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as managed_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import auto_healing_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties
import six

# API allows up to 58 characters but asked us to send only 54 (unless user
# explicitly asks us for more).
_MAX_LEN_FOR_DEDUCED_BASE_INSTANCE_NAME = 54

# Flags valid only for regional MIGs.
REGIONAL_FLAGS = ['instance_redistribution_type', 'target_distribution_shape']


def _AddInstanceGroupManagerArgs(parser):
  """Adds args."""
  parser.add_argument(
      '--base-instance-name',
      help=('Base name to use for the Compute Engine instances that will '
            'be created with the managed instance group. If not provided '
            'base instance name will be the prefix of instance group name.'))
  parser.add_argument(
      '--size',
      required=True,
      type=arg_parsers.BoundedInt(0, sys.maxsize, unlimited=True),
      help='Initial number of instances you want in this group.')
  instance_groups_flags.AddDescriptionFlag(parser)
  parser.add_argument(
      '--target-pool',
      type=arg_parsers.ArgList(),
      metavar='TARGET_POOL',
      help=('Specifies any target pools you want the instances of this '
            'managed instance group to be part of.'))
  managed_flags.INSTANCE_TEMPLATE_ARG.AddArgument(parser)


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


def ValidateUpdatePolicyAgainstStateful(update_policy, group_ref,
                                        stateful_policy, client):
  """Validates and fixed update policy for stateful MIG.

  Sets default values in update_policy for stateful IGMs or throws exception
  if the wrong value is set explicitly.

  Args:
    update_policy: Update policy to be validated
    group_ref: Reference of IGM being validated
    stateful_policy: Stateful policy to check if the group is stateful
    client: The compute API client
  """
  if stateful_policy is None or _IsZonalGroup(group_ref):
    return
  redistribution_type_none = (
      client.messages.InstanceGroupManagerUpdatePolicy
      .InstanceRedistributionTypeValueValuesEnum.NONE)
  if (not update_policy or
      update_policy.instanceRedistributionType != redistribution_type_none):
    raise exceptions.RequiredArgumentException(
        '--instance-redistribution-type',
        'Stateful regional IGMs need to have instance redistribution type '
        'set to \'NONE\'. Use \'--instance-redistribution-type=NONE\'.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create Compute Engine managed instance groups."""

  support_update_policy_min_ready_flag = False
  support_resource_manager_tags = False

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(managed_flags.DEFAULT_CREATE_OR_LIST_FORMAT)
    _AddInstanceGroupManagerArgs(parser)
    auto_healing_utils.AddAutohealingArgs(parser)
    igm_arg = instance_groups_flags.GetInstanceGroupManagerArg(zones_flag=True)
    igm_arg.AddArgument(parser, operation_type='create')
    instance_groups_flags.AddZonesFlag(parser)
    instance_groups_flags.AddMigCreateStatefulFlags(parser)
    instance_groups_flags.AddMigCreateStatefulIPsFlags(parser)
    managed_flags.AddMigInstanceRedistributionTypeFlag(parser)
    managed_flags.AddMigDistributionPolicyTargetShapeFlag(parser)
    managed_flags.AddMigListManagedInstancesResultsFlag(parser)
    managed_flags.AddMigUpdatePolicyFlags(
        parser, support_min_ready_flag=cls.support_update_policy_min_ready_flag)
    managed_flags.AddMigForceUpdateOnRepairFlags(parser)
    if cls.support_resource_manager_tags:
      managed_flags.AddMigResourceManagerTagsFlags(parser)
    managed_flags.AddMigDefaultActionOnVmFailure(parser)
    # When adding RMIG-specific flag, update REGIONAL_FLAGS constant.

  def _HandleStatefulArgs(self, instance_group_manager, args, client):
    instance_groups_flags.ValidateManagedInstanceGroupStatefulDisksProperties(
        args)
    instance_groups_flags.ValidateManagedInstanceGroupStatefulIPsProperties(
        args
    )
    if (
        args.stateful_disk
        or args.stateful_internal_ip
        or args.stateful_external_ip
    ):
      instance_group_manager.statefulPolicy = (
          self._CreateStatefulPolicy(args, client))

  def _CreateStatefulPolicy(self, args, client):
    """Create stateful policy from disks of args --stateful-disk, and ips of args --stateful-external-ips and --stateful-internal-ips."""
    stateful_disks = []
    for stateful_disk_dict in (args.stateful_disk or []):
      stateful_disks.append(
          policy_utils.MakeStatefulPolicyPreservedStateDiskEntry(
              client.messages, stateful_disk_dict))
    stateful_disks.sort(key=lambda x: x.key)
    stateful_policy = policy_utils.MakeStatefulPolicy(
        client.messages, stateful_disks
    )

    stateful_internal_ips = []
    for stateful_ip_dict in args.stateful_internal_ip or []:
      stateful_internal_ips.append(
          policy_utils.MakeStatefulPolicyPreservedStateInternalIPEntry(
              client.messages, stateful_ip_dict
          )
      )
    stateful_internal_ips.sort(key=lambda x: x.key)
    stateful_policy.preservedState.internalIPs = (
        client.messages.StatefulPolicyPreservedState.InternalIPsValue(
            additionalProperties=stateful_internal_ips
        )
    )

    stateful_external_ips = []
    for stateful_ip_dict in args.stateful_external_ip or []:
      stateful_external_ips.append(
          policy_utils.MakeStatefulPolicyPreservedStateExternalIPEntry(
              client.messages, stateful_ip_dict
          )
      )
    stateful_external_ips.sort(key=lambda x: x.key)
    stateful_policy.preservedState.externalIPs = (
        client.messages.StatefulPolicyPreservedState.ExternalIPsValue(
            additionalProperties=stateful_external_ips
        )
    )

    return stateful_policy

  def _CreateGroupReference(self, args, client, resources):
    if args.zones:
      zone_ref = resources.Parse(
          args.zones[0],
          collection='compute.zones',
          params={'project': properties.VALUES.core.project.GetOrFail})
      region = utils.ZoneNameToRegionName(zone_ref.Name())
      return resources.Parse(
          args.name,
          params={
              'region': region,
              'project': properties.VALUES.core.project.GetOrFail
          },
          collection='compute.regionInstanceGroupManagers')
    group_ref = (
        instance_groups_flags.GetInstanceGroupManagerArg().ResolveAsResource)(
            args,
            resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(client))
    if _IsZonalGroup(group_ref):
      zonal_resource_fetcher = zone_utils.ZoneResourceFetcher(client)
      zonal_resource_fetcher.WarnForZonalCreation([group_ref])
    return group_ref

  def _CreateDistributionPolicy(self, args, resources, messages):
    distribution_policy = messages.DistributionPolicy()

    if args.zones:
      policy_zones = []
      for zone in args.zones:
        zone_ref = resources.Parse(
            zone,
            collection='compute.zones',
            params={'project': properties.VALUES.core.project.GetOrFail})
        policy_zones.append(
            messages.DistributionPolicyZoneConfiguration(
                zone=zone_ref.SelfLink()))
      distribution_policy.zones = policy_zones

    if args.target_distribution_shape:
      distribution_policy.targetShape = arg_utils.ChoiceToEnum(
          args.target_distribution_shape,
          messages.DistributionPolicy.TargetShapeValueValuesEnum)
    return ValueOrNone(distribution_policy)

  def _GetRegionForGroup(self, group_ref):
    if _IsZonalGroup(group_ref):
      return utils.ZoneNameToRegionName(group_ref.zone)
    else:
      return group_ref.region

  def _GetServiceForGroup(self, group_ref, compute):
    if _IsZonalGroup(group_ref):
      return compute.instanceGroupManagers
    else:
      return compute.regionInstanceGroupManagers

  def _CreateResourceRequest(self, group_ref, instance_group_manager, client,
                             resources):
    if _IsZonalGroup(group_ref):
      instance_group_manager.zone = group_ref.zone
      return client.messages.ComputeInstanceGroupManagersInsertRequest(
          instanceGroupManager=instance_group_manager,
          project=group_ref.project,
          zone=group_ref.zone)
    else:
      region_link = resources.Parse(
          group_ref.region,
          params={'project': properties.VALUES.core.project.GetOrFail},
          collection='compute.regions')
      instance_group_manager.region = region_link.SelfLink()
      return client.messages.ComputeRegionInstanceGroupManagersInsertRequest(
          instanceGroupManager=instance_group_manager,
          project=group_ref.project,
          region=group_ref.region)

  def _GetInstanceGroupManagerTargetPools(self, target_pools, group_ref,
                                          holder):
    pool_refs = []
    if target_pools:
      region = self._GetRegionForGroup(group_ref)
      for pool in target_pools:
        pool_refs.append(
            holder.resources.Parse(
                pool,
                params={
                    'project': properties.VALUES.core.project.GetOrFail,
                    'region': region
                },
                collection='compute.targetPools'))
    return [pool_ref.SelfLink() for pool_ref in pool_refs]

  def _CreateParams(self, client, resource_manager_tags):
    resource_manager_tags_map = (
        resource_manager_tags_utils.GetResourceManagerTags(
            resource_manager_tags
        )
    )
    params = client.messages.InstanceGroupManagerParams
    additional_properties = [
        params.ResourceManagerTagsValue.AdditionalProperty(key=key, value=value)
        for key, value in sorted(six.iteritems(resource_manager_tags_map))
    ]
    return params(
        resourceManagerTags=params.ResourceManagerTagsValue(
            additionalProperties=additional_properties
        )
    )

  def _CreateInstanceGroupManager(self, args, group_ref, template_ref, client,
                                  holder):
    """Create parts of Instance Group Manager shared for the track."""
    managed_flags.ValidateRegionalMigFlagsUsage(args, REGIONAL_FLAGS, group_ref)
    instance_groups_flags.ValidateManagedInstanceGroupScopeArgs(
        args, holder.resources)
    health_check = managed_instance_groups_utils.GetHealthCheckUri(
        holder.resources, args)
    auto_healing_policies = (
        managed_instance_groups_utils.CreateAutohealingPolicies(
            client.messages, health_check, args.initial_delay))
    managed_instance_groups_utils.ValidateAutohealingPolicies(
        auto_healing_policies)
    update_policy = managed_instance_groups_utils.PatchUpdatePolicy(
        client, args, None)

    instance_lifecycle_policy = (
        managed_instance_groups_utils.CreateInstanceLifecyclePolicy(
            client.messages, args
        )
    )

    instance_group_manager = client.messages.InstanceGroupManager(
        name=group_ref.Name(),
        description=args.description,
        instanceTemplate=template_ref.SelfLink(),
        baseInstanceName=args.base_instance_name,
        targetPools=self._GetInstanceGroupManagerTargetPools(
            args.target_pool, group_ref, holder
        ),
        targetSize=int(args.size),
        autoHealingPolicies=auto_healing_policies,
        distributionPolicy=self._CreateDistributionPolicy(
            args, holder.resources, client.messages
        ),
        updatePolicy=update_policy,
        instanceLifecyclePolicy=instance_lifecycle_policy,
    )

    if args.IsSpecified('list_managed_instances_results'):
      instance_group_manager.listManagedInstancesResults = (
          client.messages.InstanceGroupManager
          .ListManagedInstancesResultsValueValuesEnum)(
              args.list_managed_instances_results.upper())

    if self.support_resource_manager_tags and args.resource_manager_tags:
      instance_group_manager.params = self._CreateParams(
          client, args.resource_manager_tags
      )

    self._HandleStatefulArgs(instance_group_manager, args, client)

    # Validate updatePolicy + statefulPolicy combination
    ValidateUpdatePolicyAgainstStateful(instance_group_manager.updatePolicy,
                                        group_ref,
                                        instance_group_manager.statefulPolicy,
                                        client)

    return instance_group_manager

  def _PostProcessOutput(self, holder, migs):
    # 0 to 1 MIGs.
    for mig in [encoding.MessageToDict(m) for m in migs]:
      # At this point we're missing information about autoscaler and current
      # size. To avoid making additional calls to API, we assume current size to
      # be 0, since MIG has just been created. We also assume that there's no
      # autoscaler, since API doesn't allow to insert MIG simultaneously with
      # autoscaler.
      mig['size'] = 0
      # Same as "mig['autoscaled'] = 'no'", but making sure that property value
      # is consistent with the one used to list groups.
      managed_instance_groups_utils.ResolveAutoscalingStatusForMig(
          holder.client, mig)
      yield mig

  def Run(self, args):
    """Creates and issues an instanceGroupManagers.Insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      List containing one dictionary: resource augmented with 'autoscaled'
      property
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = self._CreateGroupReference(args, client, holder.resources)

    template_ref = managed_flags.INSTANCE_TEMPLATE_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=flags.compute_scope.ScopeEnum.GLOBAL,
    )

    instance_group_manager = self._CreateInstanceGroupManager(
        args, group_ref, template_ref, client, holder)
    request = self._CreateResourceRequest(group_ref, instance_group_manager,
                                          client, holder.resources)
    service = self._GetServiceForGroup(group_ref, client.apitools_client)
    migs = client.MakeRequests([(service, 'Insert', request)])
    return self._PostProcessOutput(holder, migs)


CreateGA.detailed_help = {
    'brief': 'Create a Compute Engine managed instance group',
    'DESCRIPTION': """\
        *{command}* creates a Compute Engine managed instance group.
    """,
    'EXAMPLES': """\
      Running:

              $ {command} example-managed-instance-group --zone=us-central1-a --template=example-global-instance-template --size=1

      will create a managed instance group called 'example-managed-instance-group'
      in the ``us-central1-a'' zone with a global instance template resource
      'example-global-instance-template'.

      To use a regional instance template, specify the full or partial URL of the template.

      Running:

              $ {command} example-managed-instance-group --zone=us-central1-a \\
            --template=projects/example-project/regions/us-central1/instanceTemplates/example-regional-instance-template \\
            --size=1

      will create a managed instance group called
      'example-managed-instance-group' in the ``us-central1-a'' zone with a
      regional instance template resource 'example-regional-instance-template'.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create Compute Engine managed instance groups."""

  support_update_policy_min_ready_flag = True
  support_resource_manager_tags = False

  @classmethod
  def Args(cls, parser):
    super(CreateBeta, cls).Args(parser)
    managed_flags.AddStandbyPolicyFlags(parser)

  def _CreateInstanceGroupManager(self, args, group_ref, template_ref, client,
                                  holder):
    instance_group_manager = super(CreateBeta,
                                   self)._CreateInstanceGroupManager(
                                       args, group_ref, template_ref, client,
                                       holder)
    standby_policy = managed_instance_groups_utils.CreateStandbyPolicy(
        client.messages,
        args.standby_policy_initial_delay,
        args.standby_policy_mode,
    )
    if standby_policy:
      instance_group_manager.standbyPolicy = standby_policy
    if args.suspended_size:
      instance_group_manager.targetSuspendedSize = args.suspended_size
    if args.stopped_size:
      instance_group_manager.targetStoppedSize = args.stopped_size
    return instance_group_manager


CreateBeta.detailed_help = CreateGA.detailed_help


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create Compute Engine managed instance groups."""

  support_resource_manager_tags = True

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    managed_flags.AddInstanceFlexibilityPolicyArgs(parser)

  def _CreateInstanceGroupManager(self, args, group_ref, template_ref, client,
                                  holder):
    instance_group_manager = super(CreateAlpha,
                                   self)._CreateInstanceGroupManager(
                                       args, group_ref, template_ref, client,
                                       holder)
    instance_flexibility_policy = (
        managed_instance_groups_utils.CreateInstanceFlexibilityPolicy(
            client.messages, args
        )
    )
    instance_group_manager.instanceFlexibilityPolicy = (
        instance_flexibility_policy
    )
    return instance_group_manager

CreateAlpha.detailed_help = CreateGA.detailed_help
