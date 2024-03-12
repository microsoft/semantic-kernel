# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Update node pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        *{command}* updates a node pool in a Google Kubernetes Engine cluster.
        """,
    'EXAMPLES':
        """\
        To turn on node autoupgrade in "node-pool-1" in the cluster
        "sample-cluster", run:

          $ {command} node-pool-1 --cluster=sample-cluster --enable-autoupgrade
        """,
}


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  flags.AddNodePoolNameArg(parser, 'The name of the node pool.')
  flags.AddNodePoolClusterFlag(parser, 'The name of the cluster.')
  flags.AddAsyncFlag(parser)
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,
      hidden=True,
      help='THIS ARGUMENT NEEDS HELP TEXT.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Updates a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    group = parser.add_mutually_exclusive_group(required=True)

    flags.AddNodePoolLocationsFlag(group)

    node_management_group = group.add_argument_group('Node management')
    flags.AddEnableAutoRepairFlag(node_management_group, for_node_pool=True)
    flags.AddEnableAutoUpgradeFlag(node_management_group, for_node_pool=True)

    autoscaling_group = flags.AddClusterAutoscalingFlags(group)
    flags.AddNodePoolAutoprovisioningFlag(autoscaling_group, hidden=False)
    flags.AddWorkloadMetadataFlag(group)

    upgrade_settings_group = group.add_argument_group('Upgrade settings')
    flags.AddEnableSurgeUpgradeFlag(upgrade_settings_group)
    flags.AddSurgeUpgradeFlag(upgrade_settings_group, for_node_pool=True)
    flags.AddMaxUnavailableUpgradeFlag(
        upgrade_settings_group, for_node_pool=True)

    flags.AddEnableBlueGreenUpgradeFlag(upgrade_settings_group)
    flags.AddStandardRolloutPolicyFlag(
        upgrade_settings_group, for_node_pool=True)
    flags.AddNodePoolSoakDurationFlag(
        upgrade_settings_group, for_node_pool=True)

    flags.AddSystemConfigFlag(group, hidden=False)
    flags.AddLabelsFlag(group, for_node_pool=True)
    flags.AddNodeLabelsFlag(group, for_node_pool=True, for_update=True)
    flags.AddNodeTaintsFlag(group, for_node_pool=True, for_update=True)
    flags.AddTagsNodePoolUpdate(group)
    flags.AddEnableGvnicFlag(group)
    flags.AddEnableImageStreamingFlag(group, for_node_pool=True)
    flags.AddEnableConfidentialNodesFlag(
        group, for_node_pool=True, is_update=True)
    flags.AddNetworkPerformanceConfigFlags(group, hidden=False)
    flags.AddNodePoolEnablePrivateNodes(group)
    flags.AddEnableFastSocketFlag(group)
    flags.AddLoggingVariantFlag(group, for_node_pool=True)
    flags.AddWindowsOsVersionFlag(group)
    flags.AddContainerdConfigFlag(group, hidden=True)
    flags.AddResourceManagerTagsNodePoolUpdate(group)
    flags.AddQueuedProvisioningFlag(group)
    flags.AddEnableKubeletReadonlyPortFlag(group)
    node_config_group = group.add_argument_group('Node config')
    flags.AddMachineTypeFlag(node_config_group, update=True)
    flags.AddDiskTypeFlag(node_config_group)
    flags.AddDiskSizeFlag(node_config_group)

  def ParseUpdateNodePoolOptions(self, args):
    flags.ValidateSurgeUpgradeSettings(args)

    return api_adapter.UpdateNodePoolOptions(
        enable_autorepair=args.enable_autorepair,
        enable_autoupgrade=args.enable_autoupgrade,
        enable_autoscaling=args.enable_autoscaling,
        node_locations=args.node_locations,
        max_nodes=args.max_nodes,
        min_nodes=args.min_nodes,
        total_max_nodes=args.total_max_nodes,
        total_min_nodes=args.total_min_nodes,
        location_policy=args.location_policy,
        workload_metadata=args.workload_metadata,
        workload_metadata_from_node=args.workload_metadata_from_node,
        enable_autoprovisioning=args.enable_autoprovisioning,
        max_surge_upgrade=args.max_surge_upgrade,
        max_unavailable_upgrade=args.max_unavailable_upgrade,
        system_config_from_file=args.system_config_from_file,
        labels=args.labels,
        node_labels=args.node_labels,
        node_taints=args.node_taints,
        tags=args.tags,
        gvnic=args.enable_gvnic,
        enable_image_streaming=args.enable_image_streaming,
        network_performance_config=args.network_performance_configs,
        enable_confidential_nodes=args.enable_confidential_nodes,
        enable_blue_green_upgrade=args.enable_blue_green_upgrade,
        enable_surge_upgrade=args.enable_surge_upgrade,
        node_pool_soak_duration=args.node_pool_soak_duration,
        standard_rollout_policy=args.standard_rollout_policy,
        enable_private_nodes=args.enable_private_nodes,
        enable_fast_socket=args.enable_fast_socket,
        logging_variant=args.logging_variant,
        windows_os_version=args.windows_os_version,
        containerd_config_from_file=args.containerd_config_from_file,
        enable_queued_provisioning=args.enable_queued_provisioning,
        machine_type=args.machine_type,
        disk_type=args.disk_type,
        enable_insecure_kubelet_readonly_port=args.enable_insecure_kubelet_readonly_port,
        disk_size_gb=utils.BytesToGb(args.disk_size)
        if hasattr(args, 'disk_size')
        else None,
        resource_manager_tags=args.resource_manager_tags,
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully updated node pool.

    Raises:
      util.Error, if creation failed.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)
    pool_ref = adapter.ParseNodePool(args.name, location)
    options = self.ParseUpdateNodePoolOptions(args)

    if options.node_labels is not None:
      console_io.PromptContinue(
          message=(
              'The previous user-specified labels on this node pool will be '
              'replaced by \'{labels}\'').format(
                  labels=args.GetValue('node_labels')),
          throw_if_unattended=True,
          cancel_on_no=True)

    if options.node_taints is not None:
      console_io.PromptContinue(
          message=(
              'The previous user-specified taints on this node pool will be '
              'replaced by \'{taints}\'').format(
                  taints=args.GetValue('node_taints')),
          throw_if_unattended=True,
          cancel_on_no=True)

    if options.tags is not None:
      console_io.PromptContinue(
          message=('The previous user-specified tags on this node pool will be '
                   'replaced by \'{tags}\'').format(tags=args.GetValue('tags')),
          throw_if_unattended=True,
          cancel_on_no=True)

    # Image streaming feature requires Container File System API to be enabled.
    # Checking whether the API has been enabled, and warning if not.
    if options.enable_image_streaming:
      util.CheckForContainerFileSystemApiEnablementWithPrompt(
          pool_ref.projectId)

    try:
      operation_ref = adapter.UpdateNodePool(pool_ref, options)

      if args.async_:
        op = adapter.GetOperation(operation_ref)
        if not args.IsSpecified('format'):
          args.format = util.OPERATIONS_FORMAT
        return op
      adapter.WaitForOperation(
          operation_ref,
          'Updating node pool {0}'.format(pool_ref.nodePoolId),
          timeout_s=args.timeout)
      pool = adapter.GetNodePool(pool_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.UpdatedResource(pool_ref)
    return pool


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Updates a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    group = parser.add_mutually_exclusive_group(required=True)

    node_management_group = group.add_argument_group('Node management')
    flags.AddEnableAutoRepairFlag(node_management_group, for_node_pool=True)
    flags.AddEnableAutoUpgradeFlag(node_management_group, for_node_pool=True)
    flags.AddAcceleratorArgs(
        group,
        enable_gpu_partition=True,
        enable_gpu_sharing=True,
        enable_gpu_driver_installation=True,
        hidden=True,
    )

    autoscaling_group = flags.AddClusterAutoscalingFlags(group)
    flags.AddNodePoolAutoprovisioningFlag(autoscaling_group, hidden=False)

    upgrade_settings_group = group.add_argument_group('Upgrade settings')
    flags.AddEnableSurgeUpgradeFlag(upgrade_settings_group)
    flags.AddSurgeUpgradeFlag(upgrade_settings_group, for_node_pool=True)
    flags.AddMaxUnavailableUpgradeFlag(
        upgrade_settings_group, for_node_pool=True)

    flags.AddEnableBlueGreenUpgradeFlag(upgrade_settings_group)
    flags.AddStandardRolloutPolicyFlag(
        upgrade_settings_group, for_node_pool=True)
    flags.AddAutoscaleRolloutPolicyFlag(
        upgrade_settings_group, for_node_pool=True)
    flags.AddNodePoolSoakDurationFlag(
        upgrade_settings_group, for_node_pool=True)

    flags.AddWorkloadMetadataFlag(group, use_mode=False)

    flags.AddNodePoolLocationsFlag(group)

    flags.AddSystemConfigFlag(group, hidden=False)

    flags.AddLabelsFlag(group, for_node_pool=True)
    flags.AddNodeLabelsFlag(group, for_node_pool=True, for_update=True)
    flags.AddNodeTaintsFlag(group, for_node_pool=True, for_update=True)
    flags.AddTagsNodePoolUpdate(group)
    flags.AddNodePoolEnablePrivateNodes(group)
    flags.AddEnableGcfsFlag(group, for_node_pool=True)
    flags.AddEnableGvnicFlag(group)
    flags.AddEnableImageStreamingFlag(group, for_node_pool=True)
    flags.AddNetworkPerformanceConfigFlags(group, hidden=False)
    flags.AddEnableConfidentialNodesFlag(
        group, for_node_pool=True, is_update=True)
    flags.AddEnableFastSocketFlag(group)
    flags.AddLoggingVariantFlag(group, for_node_pool=True)
    flags.AddWindowsOsVersionFlag(group)
    flags.AddResourceManagerTagsNodePoolUpdate(group)
    flags.AddContainerdConfigFlag(group, hidden=True)
    flags.AddQueuedProvisioningFlag(group)
    flags.AddEnableKubeletReadonlyPortFlag(group)

    node_config_group = group.add_argument_group('Node config')
    flags.AddMachineTypeFlag(node_config_group, update=True)
    flags.AddDiskTypeFlag(node_config_group)
    flags.AddDiskSizeFlag(node_config_group)

  def ParseUpdateNodePoolOptions(self, args):
    flags.ValidateSurgeUpgradeSettings(args)

    ops = api_adapter.UpdateNodePoolOptions(
        accelerators=args.accelerator,
        enable_autorepair=args.enable_autorepair,
        enable_autoupgrade=args.enable_autoupgrade,
        enable_autoscaling=args.enable_autoscaling,
        max_nodes=args.max_nodes,
        min_nodes=args.min_nodes,
        total_max_nodes=args.total_max_nodes,
        total_min_nodes=args.total_min_nodes,
        location_policy=args.location_policy,
        enable_autoprovisioning=args.enable_autoprovisioning,
        workload_metadata=args.workload_metadata,
        workload_metadata_from_node=args.workload_metadata_from_node,
        node_locations=args.node_locations,
        max_surge_upgrade=args.max_surge_upgrade,
        max_unavailable_upgrade=args.max_unavailable_upgrade,
        system_config_from_file=args.system_config_from_file,
        labels=args.labels,
        node_labels=args.node_labels,
        node_taints=args.node_taints,
        tags=args.tags,
        enable_private_nodes=args.enable_private_nodes,
        enable_gcfs=args.enable_gcfs,
        gvnic=args.enable_gvnic,
        enable_image_streaming=args.enable_image_streaming,
        enable_blue_green_upgrade=args.enable_blue_green_upgrade,
        enable_surge_upgrade=args.enable_surge_upgrade,
        node_pool_soak_duration=args.node_pool_soak_duration,
        standard_rollout_policy=args.standard_rollout_policy,
        autoscaled_rollout_policy=args.autoscaled_rollout_policy,
        network_performance_config=args.network_performance_configs,
        enable_confidential_nodes=args.enable_confidential_nodes,
        enable_fast_socket=args.enable_fast_socket,
        logging_variant=args.logging_variant,
        windows_os_version=args.windows_os_version,
        resource_manager_tags=args.resource_manager_tags,
        containerd_config_from_file=args.containerd_config_from_file,
        enable_queued_provisioning=args.enable_queued_provisioning,
        machine_type=args.machine_type,
        disk_type=args.disk_type,
        enable_insecure_kubelet_readonly_port=args.enable_insecure_kubelet_readonly_port,
        disk_size_gb=utils.BytesToGb(args.disk_size)
        if hasattr(args, 'disk_size')
        else None,
    )
    return ops


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Updates a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    group = parser.add_mutually_exclusive_group(required=True)

    node_management_group = group.add_argument_group('Node management')
    flags.AddEnableAutoRepairFlag(node_management_group, for_node_pool=True)
    flags.AddEnableAutoUpgradeFlag(node_management_group, for_node_pool=True)
    flags.AddAcceleratorArgs(
        group,
        enable_gpu_partition=True,
        enable_gpu_sharing=True,
        enable_gpu_driver_installation=True,
        hidden=True,
    )

    autoscaling_group = flags.AddClusterAutoscalingFlags(group)
    flags.AddNodePoolAutoprovisioningFlag(autoscaling_group, hidden=False)

    upgrade_settings_group = group.add_argument_group('Upgrade settings')
    flags.AddEnableSurgeUpgradeFlag(upgrade_settings_group)
    flags.AddSurgeUpgradeFlag(upgrade_settings_group, for_node_pool=True)
    flags.AddMaxUnavailableUpgradeFlag(
        upgrade_settings_group, for_node_pool=True)

    flags.AddEnableBlueGreenUpgradeFlag(upgrade_settings_group)
    flags.AddStandardRolloutPolicyFlag(
        upgrade_settings_group, for_node_pool=True)
    flags.AddAutoscaleRolloutPolicyFlag(
        upgrade_settings_group, for_node_pool=True)
    flags.AddNodePoolSoakDurationFlag(
        upgrade_settings_group, for_node_pool=True)

    flags.AddWorkloadMetadataFlag(group, use_mode=False)

    flags.AddNodePoolLocationsFlag(group)

    flags.AddSystemConfigFlag(group, hidden=False)

    flags.AddLabelsFlag(group, for_node_pool=True)
    flags.AddNodeLabelsFlag(group, for_node_pool=True, for_update=True)
    flags.AddNodeTaintsFlag(group, for_node_pool=True, for_update=True)
    flags.AddTagsNodePoolUpdate(group)
    flags.AddNodePoolEnablePrivateNodes(group)
    flags.AddEnableGcfsFlag(group, for_node_pool=True)
    flags.AddEnableGvnicFlag(group)
    flags.AddEnableImageStreamingFlag(group, for_node_pool=True)
    flags.AddNetworkPerformanceConfigFlags(group, hidden=False)
    flags.AddEnableConfidentialNodesFlag(
        group, for_node_pool=True, is_update=True)
    flags.AddEnableFastSocketFlag(group)
    flags.AddLoggingVariantFlag(group, for_node_pool=True)
    flags.AddWindowsOsVersionFlag(group)
    flags.AddResourceManagerTagsNodePoolUpdate(group)
    flags.AddContainerdConfigFlag(group, hidden=True)
    flags.AddQueuedProvisioningFlag(group)
    flags.AddEnableKubeletReadonlyPortFlag(group)

    node_config_group = group.add_argument_group('Node config')
    flags.AddMachineTypeFlag(node_config_group, update=True)
    flags.AddDiskTypeFlag(node_config_group)
    flags.AddDiskSizeFlag(node_config_group)

  def ParseUpdateNodePoolOptions(self, args):
    flags.ValidateSurgeUpgradeSettings(args)

    ops = api_adapter.UpdateNodePoolOptions(
        accelerators=args.accelerator,
        enable_autorepair=args.enable_autorepair,
        enable_autoupgrade=args.enable_autoupgrade,
        enable_autoscaling=args.enable_autoscaling,
        max_nodes=args.max_nodes,
        min_nodes=args.min_nodes,
        total_max_nodes=args.total_max_nodes,
        total_min_nodes=args.total_min_nodes,
        location_policy=args.location_policy,
        enable_autoprovisioning=args.enable_autoprovisioning,
        workload_metadata=args.workload_metadata,
        workload_metadata_from_node=args.workload_metadata_from_node,
        node_locations=args.node_locations,
        max_surge_upgrade=args.max_surge_upgrade,
        max_unavailable_upgrade=args.max_unavailable_upgrade,
        system_config_from_file=args.system_config_from_file,
        labels=args.labels,
        node_labels=args.node_labels,
        node_taints=args.node_taints,
        tags=args.tags,
        enable_private_nodes=args.enable_private_nodes,
        enable_gcfs=args.enable_gcfs,
        gvnic=args.enable_gvnic,
        enable_image_streaming=args.enable_image_streaming,
        enable_blue_green_upgrade=args.enable_blue_green_upgrade,
        enable_surge_upgrade=args.enable_surge_upgrade,
        node_pool_soak_duration=args.node_pool_soak_duration,
        standard_rollout_policy=args.standard_rollout_policy,
        autoscaled_rollout_policy=args.autoscaled_rollout_policy,
        network_performance_config=args.network_performance_configs,
        enable_confidential_nodes=args.enable_confidential_nodes,
        enable_fast_socket=args.enable_fast_socket,
        logging_variant=args.logging_variant,
        windows_os_version=args.windows_os_version,
        resource_manager_tags=args.resource_manager_tags,
        containerd_config_from_file=args.containerd_config_from_file,
        enable_queued_provisioning=args.enable_queued_provisioning,
        machine_type=args.machine_type,
        disk_type=args.disk_type,
        enable_insecure_kubelet_readonly_port=args.enable_insecure_kubelet_readonly_port,
        disk_size_gb=utils.BytesToGb(args.disk_size)
        if hasattr(args, 'disk_size')
        else None,
    )
    return ops


Update.detailed_help = DETAILED_HELP
