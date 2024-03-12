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
"""Create node pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.command_lib.container import container_command_util as cmd_util
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        *{command}* facilitates the creation of a node pool in a Google
        Kubernetes Engine cluster. A variety of options exists to customize the
        node configuration and the number of nodes created.
        """,
    'EXAMPLES':
        """\
        To create a new node pool "node-pool-1" with the default options in the
        cluster "sample-cluster", run:

          $ {command} node-pool-1 --cluster=sample-cluster

        The new node pool will show up in the cluster after all the nodes have
        been provisioned.

        To create a node pool with 5 nodes, run:

          $ {command} node-pool-1 --cluster=sample-cluster --num-nodes=5
        """,
}

WARN_WINDOWS_SAC_SUPPORT_LIFECYCLE = (
    'Note: Windows SAC node pools must be upgraded regularly to remain '
    'operational. Please refer to '
    'https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-cluster-windows#choose_your_windows_server_node_image'
    ' for more information.')


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  flags.AddNodePoolNameArg(parser, 'The name of the node pool to create.')
  flags.AddNodePoolClusterFlag(parser, 'The cluster to add the node pool to.')
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,
      hidden=True,
      help='THIS ARGUMENT NEEDS HELP TEXT.')
  parser.add_argument(
      '--num-nodes',
      type=int,
      help='The number of nodes in the node pool in each of the '
      'cluster\'s zones.',
      default=3)
  flags.AddMachineTypeFlag(parser)
  parser.add_argument(
      '--disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help='Size for node VM boot disks in GB. Defaults to 100GB.')
  flags.AddImageTypeFlag(parser, 'node pool')
  flags.AddImageFlag(parser, hidden=True)
  flags.AddImageProjectFlag(parser, hidden=True)
  flags.AddImageFamilyFlag(parser, hidden=True)
  flags.AddLabelsFlag(parser, for_node_pool=True)
  flags.AddNodeLabelsFlag(parser, for_node_pool=True)
  flags.AddTagsFlag(
      parser, """\
Applies the given Compute Engine tags (comma separated) on all nodes in the new
node-pool. Example:

  $ {command} node-pool-1 --cluster=example-cluster --tags=tag1,tag2

New nodes, including ones created by resize or recreate, will have these tags
on the Compute Engine API instance object and can be used in firewall rules.
See https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create
for examples.
""")
  parser.display_info.AddFormat(util.NODEPOOLS_FORMAT)
  flags.AddNodeVersionFlag(parser)
  flags.AddDiskTypeFlag(parser)
  flags.AddMetadataFlags(parser)
  flags.AddShieldedInstanceFlags(parser)
  flags.AddNetworkConfigFlags(parser)
  flags.AddThreadsPerCore(parser)
  flags.AddAdditionalNodeNetworkFlag(parser)
  flags.AddAdditionalPodNetworkFlag(parser)
  flags.AddAsyncFlag(parser)
  flags.AddSoleTenantNodeAffinityFileFlag(parser)
  flags.AddContainerdConfigFlag(parser)
  flags.AddEnableKubeletReadonlyPortFlag(parser)


def ParseCreateNodePoolOptionsBase(args):
  """Parses the flags provided with the node pool creation command."""
  enable_autorepair = cmd_util.GetAutoRepair(args)
  flags.WarnForNodeModification(args, enable_autorepair)
  flags.ValidateSurgeUpgradeSettings(args)
  metadata = metadata_utils.ConstructMetadataDict(args.metadata,
                                                  args.metadata_from_file)
  ephemeral_storage_local_ssd = None
  if args.IsKnownAndSpecified('ephemeral_storage_local_ssd'):
    ephemeral_storage_local_ssd = (
        []
        if args.ephemeral_storage_local_ssd is None
        else args.ephemeral_storage_local_ssd
    )

  local_nvme_ssd_block = None
  if args.IsKnownAndSpecified('local_nvme_ssd_block'):
    local_nvme_ssd_block = (
        []
        if args.local_nvme_ssd_block is None
        else args.local_nvme_ssd_block
    )
  return api_adapter.CreateNodePoolOptions(
      accelerators=args.accelerator,
      boot_disk_kms_key=args.boot_disk_kms_key,
      machine_type=args.machine_type,
      disk_size_gb=utils.BytesToGb(args.disk_size),
      scopes=args.scopes,
      node_version=args.node_version,
      num_nodes=args.num_nodes,
      local_ssd_count=args.local_ssd_count,
      local_nvme_ssd_block=local_nvme_ssd_block,
      ephemeral_storage_local_ssd=ephemeral_storage_local_ssd,
      tags=args.tags,
      threads_per_core=args.threads_per_core,
      labels=args.labels,
      node_labels=args.node_labels,
      node_taints=args.node_taints,
      enable_autoscaling=args.enable_autoscaling,
      max_nodes=args.max_nodes,
      min_cpu_platform=args.min_cpu_platform,
      min_nodes=args.min_nodes,
      total_max_nodes=args.total_max_nodes,
      total_min_nodes=args.total_min_nodes,
      location_policy=args.location_policy,
      image_type=args.image_type,
      image=args.image,
      image_project=args.image_project,
      image_family=args.image_family,
      preemptible=args.preemptible,
      enable_autorepair=enable_autorepair,
      enable_autoupgrade=cmd_util.GetAutoUpgrade(args),
      service_account=args.service_account,
      disk_type=args.disk_type,
      metadata=metadata,
      max_pods_per_node=args.max_pods_per_node,
      enable_autoprovisioning=args.enable_autoprovisioning,
      workload_metadata=args.workload_metadata,
      workload_metadata_from_node=args.workload_metadata_from_node,
      shielded_secure_boot=args.shielded_secure_boot,
      shielded_integrity_monitoring=args.shielded_integrity_monitoring,
      reservation_affinity=args.reservation_affinity,
      reservation=args.reservation,
      sandbox=args.sandbox,
      max_surge_upgrade=args.max_surge_upgrade,
      max_unavailable_upgrade=args.max_unavailable_upgrade,
      node_group=args.node_group,
      system_config_from_file=args.system_config_from_file,
      pod_ipv4_range=args.pod_ipv4_range,
      create_pod_ipv4_range=args.create_pod_ipv4_range,
      gvnic=args.enable_gvnic,
      enable_image_streaming=args.enable_image_streaming,
      spot=args.spot,
      enable_confidential_nodes=args.enable_confidential_nodes,
      enable_blue_green_upgrade=args.enable_blue_green_upgrade,
      enable_surge_upgrade=args.enable_surge_upgrade,
      node_pool_soak_duration=args.node_pool_soak_duration,
      standard_rollout_policy=args.standard_rollout_policy,
      enable_private_nodes=args.enable_private_nodes,
      enable_fast_socket=args.enable_fast_socket,
      logging_variant=args.logging_variant,
      windows_os_version=args.windows_os_version,
      additional_node_network=args.additional_node_network,
      additional_pod_network=args.additional_pod_network,
      sole_tenant_node_affinity_file=args.sole_tenant_node_affinity_file,
      containerd_config_from_file=args.containerd_config_from_file,
      resource_manager_tags=args.resource_manager_tags,
      enable_insecure_kubelet_readonly_port=args.enable_insecure_kubelet_readonly_port,
  )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddAcceleratorArgs(
        parser,
        enable_gpu_partition=True,
        enable_gpu_sharing=True,
        enable_gpu_deprecated_fields=False,
        enable_gpu_driver_installation=True)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddLocalSSDsGAFlags(parser, for_node_pool=True)
    flags.AddPreemptibleFlag(parser, for_node_pool=True)
    flags.AddEnableAutoRepairFlag(parser, for_node_pool=True, for_create=True)
    flags.AddMinCpuPlatformFlag(parser, for_node_pool=True)
    flags.AddWorkloadMetadataFlag(parser)
    flags.AddNodeTaintsFlag(parser, for_node_pool=True)
    flags.AddNodePoolNodeIdentityFlags(parser)
    flags.AddNodePoolAutoprovisioningFlag(parser, hidden=False)
    flags.AddMaxPodsPerNodeFlag(parser, for_node_pool=True)
    flags.AddEnableAutoUpgradeFlag(parser, for_node_pool=True, default=True)
    flags.AddReservationAffinityFlags(parser, for_node_pool=True)
    flags.AddSandboxFlag(parser)
    flags.AddNodePoolLocationsFlag(parser, for_create=True)
    flags.AddSurgeUpgradeFlag(parser, for_node_pool=True, default=1)
    flags.AddMaxUnavailableUpgradeFlag(
        parser, for_node_pool=True, is_create=True)
    flags.AddSystemConfigFlag(parser, hidden=False)
    flags.AddNodeGroupFlag(parser)
    flags.AddEnableGvnicFlag(parser)
    flags.AddEnableImageStreamingFlag(parser, for_node_pool=True)
    flags.AddSpotFlag(parser, for_node_pool=True)
    flags.AddEnableConfidentialNodesFlag(parser, for_node_pool=True)
    flags.AddDisablePodCIDROverprovisionFlag(parser, hidden=True)
    flags.AddNetworkPerformanceConfigFlags(parser, hidden=False)
    flags.AddEnableSurgeUpgradeFlag(parser)
    flags.AddEnableBlueGreenUpgradeFlag(parser)
    flags.AddStandardRolloutPolicyFlag(parser)
    flags.AddNodePoolSoakDurationFlag(parser)
    flags.AddNodePoolEnablePrivateNodes(parser)
    flags.AddEnableFastSocketFlag(parser)
    flags.AddLoggingVariantFlag(parser, for_node_pool=True)
    flags.AddWindowsOsVersionFlag(parser)
    flags.AddPlacementTypeFlag(parser, for_node_pool=True, hidden=False)
    flags.AddQueuedProvisioningFlag(parser)
    flags.AddBestEffortProvisionFlags(parser)
    flags.AddPlacementPolicyFlag(parser)
    flags.AddTPUTopologyFlag(parser)
    flags.AddResourceManagerTagsCreate(parser, for_node_pool=True)

  def ParseCreateNodePoolOptions(self, args):
    ops = ParseCreateNodePoolOptionsBase(args)
    ops.node_locations = args.node_locations
    ops.network_performance_config = args.network_performance_configs
    ops.disable_pod_cidr_overprovision = args.disable_pod_cidr_overprovision
    ops.placement_type = args.placement_type
    ops.enable_best_effort_provision = args.enable_best_effort_provision
    ops.min_provision_nodes = args.min_provision_nodes
    ops.placement_policy = args.placement_policy
    ops.enable_queued_provisioning = args.enable_queued_provisioning
    ops.tpu_topology = args.tpu_topology
    return ops

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully created node pool.

    Raises:
      util.Error, if creation failed.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    try:
      pool_ref = adapter.ParseNodePool(args.name, location)
      options = self.ParseCreateNodePoolOptions(args)

      if options.accelerators is not None:
        log.status.Print('Note: ' + constants.KUBERNETES_GPU_LIMITATION_MSG)

      elif options.image_type and options.image_type.upper().startswith(
          'WINDOWS_SAC'):
        log.status.Print(WARN_WINDOWS_SAC_SUPPORT_LIFECYCLE)

      # Image streaming feature requires Container File System API to be
      # enabled.
      # Checking whether the API has been enabled, and warning if not.
      if options.enable_image_streaming:
        util.CheckForContainerFileSystemApiEnablementWithPrompt(
            pool_ref.projectId)

      operation_ref = adapter.CreateNodePool(pool_ref, options)
      if args.async_:
        op = adapter.GetOperation(operation_ref)
        if not args.IsSpecified('format'):
          args.format = util.OPERATIONS_FORMAT
        return op
      adapter.WaitForOperation(
          operation_ref,
          'Creating node pool {0}'.format(pool_ref.nodePoolId),
          timeout_s=args.timeout)
      pool = adapter.GetNodePool(pool_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.CreatedResource(pool_ref)
    return [pool]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddAcceleratorArgs(
        parser,
        enable_gpu_partition=True,
        enable_gpu_sharing=True,
        enable_gpu_deprecated_fields=True,
        enable_gpu_driver_installation=True)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddLocalSSDsBetaFlags(parser, for_node_pool=True)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddPreemptibleFlag(parser, for_node_pool=True)
    flags.AddEnableAutoRepairFlag(parser, for_node_pool=True, for_create=True)
    flags.AddMinCpuPlatformFlag(parser, for_node_pool=True)
    flags.AddWorkloadMetadataFlag(parser, use_mode=False)
    flags.AddNodeTaintsFlag(parser, for_node_pool=True)
    flags.AddNodePoolNodeIdentityFlags(parser)
    flags.AddNodePoolAutoprovisioningFlag(parser, hidden=False)
    flags.AddMaxPodsPerNodeFlag(parser, for_node_pool=True)
    flags.AddEnableAutoUpgradeFlag(parser, for_node_pool=True, default=True)
    flags.AddSandboxFlag(parser)
    flags.AddNodePoolLocationsFlag(parser, for_create=True)
    flags.AddSurgeUpgradeFlag(parser, for_node_pool=True, default=1)
    flags.AddMaxUnavailableUpgradeFlag(
        parser, for_node_pool=True, is_create=True)
    flags.AddReservationAffinityFlags(parser, for_node_pool=True)
    flags.AddSystemConfigFlag(parser, hidden=False)
    flags.AddNodeGroupFlag(parser)
    flags.AddEnableGcfsFlag(parser, for_node_pool=True)
    flags.AddEnableImageStreamingFlag(parser, for_node_pool=True)
    flags.AddNodePoolEnablePrivateNodes(parser)
    flags.AddEnableGvnicFlag(parser)
    flags.AddSpotFlag(parser, for_node_pool=True)
    flags.AddPlacementTypeFlag(parser, for_node_pool=True, hidden=False)
    flags.AddPlacementPolicyFlag(parser)
    flags.AddEnableSurgeUpgradeFlag(parser)
    flags.AddEnableBlueGreenUpgradeFlag(parser)
    flags.AddStandardRolloutPolicyFlag(parser)
    flags.AddAutoscaleRolloutPolicyFlag(parser)
    flags.AddNodePoolSoakDurationFlag(parser)
    flags.AddMaintenanceIntervalFlag(parser, for_node_pool=True, hidden=True)
    flags.AddNetworkPerformanceConfigFlags(parser, hidden=False)
    flags.AddEnableConfidentialNodesFlag(parser, for_node_pool=True)
    flags.AddEnableConfidentialStorageFlag(parser, for_node_pool=True)
    flags.AddStoragePoolsFlag(
        parser, for_node_pool=True, for_create=True, hidden=False)
    flags.AddDisablePodCIDROverprovisionFlag(parser)
    flags.AddEnableFastSocketFlag(parser)
    flags.AddLoggingVariantFlag(parser, for_node_pool=True)
    flags.AddWindowsOsVersionFlag(parser)
    flags.AddBestEffortProvisionFlags(parser, hidden=False)
    flags.AddQueuedProvisioningFlag(parser)
    flags.AddTPUTopologyFlag(parser)
    flags.AddEnableNestedVirtualizationFlag(
        parser, for_node_pool=True, hidden=True)
    flags.AddHostMaintenanceIntervalFlag(
        parser, for_node_pool=True, hidden=True)
    flags.AddResourceManagerTagsCreate(parser, for_node_pool=True)
    flags.AddSecondaryBootDisksArgs(parser, hidden=True)

  def ParseCreateNodePoolOptions(self, args):
    ops = ParseCreateNodePoolOptionsBase(args)
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ephemeral_storage = None
    if args.IsKnownAndSpecified('ephemeral_storage'):
      ephemeral_storage = (
          []
          if args.ephemeral_storage is None
          else args.ephemeral_storage
      )
    ops.boot_disk_kms_key = args.boot_disk_kms_key
    ops.sandbox = args.sandbox
    ops.node_locations = args.node_locations
    ops.system_config_from_file = args.system_config_from_file
    ops.enable_gcfs = args.enable_gcfs
    ops.enable_image_streaming = args.enable_image_streaming
    ops.ephemeral_storage = ephemeral_storage
    ops.spot = args.spot
    ops.placement_type = args.placement_type
    ops.placement_policy = args.placement_policy
    ops.location_policy = args.location_policy
    ops.enable_blue_green_upgrade = args.enable_blue_green_upgrade
    ops.enable_surge_upgrade = args.enable_surge_upgrade
    ops.node_pool_soak_duration = args.node_pool_soak_duration
    ops.standard_rollout_policy = args.standard_rollout_policy
    ops.autoscaled_rollout_policy = args.autoscaled_rollout_policy
    ops.maintenance_interval = args.maintenance_interval
    ops.network_performance_config = args.network_performance_configs
    ops.enable_confidential_nodes = args.enable_confidential_nodes
    ops.disable_pod_cidr_overprovision = args.disable_pod_cidr_overprovision
    ops.enable_fast_socket = args.enable_fast_socket
    ops.enable_queued_provisioning = args.enable_queued_provisioning
    ops.tpu_topology = args.tpu_topology
    ops.enable_nested_virtualization = args.enable_nested_virtualization
    ops.enable_best_effort_provision = args.enable_best_effort_provision
    ops.min_provision_nodes = args.min_provision_nodes
    ops.host_maintenance_interval = args.host_maintenance_interval
    ops.secondary_boot_disks = args.secondary_boot_disk
    ops.enable_confidential_storage = args.enable_confidential_storage
    ops.storage_pools = args.storage_pools
    return ops


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a node pool in a running cluster."""

  def ParseCreateNodePoolOptions(self, args):
    ops = ParseCreateNodePoolOptionsBase(args)
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ephemeral_storage = None
    if args.IsKnownAndSpecified('ephemeral_storage'):
      ephemeral_storage = (
          []
          if args.ephemeral_storage is None
          else args.ephemeral_storage
      )
    ops.local_ssd_volume_configs = args.local_ssd_volumes
    ops.boot_disk_kms_key = args.boot_disk_kms_key
    ops.sandbox = args.sandbox
    ops.linux_sysctls = args.linux_sysctls
    ops.node_locations = args.node_locations
    ops.system_config_from_file = args.system_config_from_file
    ops.enable_gcfs = args.enable_gcfs
    ops.enable_image_streaming = args.enable_image_streaming
    ops.spot = args.spot
    ops.placement_type = args.placement_type
    ops.placement_policy = args.placement_policy
    ops.location_policy = args.location_policy
    ops.enable_blue_green_upgrade = args.enable_blue_green_upgrade
    ops.enable_surge_upgrade = args.enable_surge_upgrade
    ops.node_pool_soak_duration = args.node_pool_soak_duration
    ops.standard_rollout_policy = args.standard_rollout_policy
    ops.maintenance_interval = args.maintenance_interval
    ops.network_performance_config = args.network_performance_configs
    ops.enable_confidential_nodes = args.enable_confidential_nodes
    ops.disable_pod_cidr_overprovision = args.disable_pod_cidr_overprovision
    ops.enable_fast_socket = args.enable_fast_socket
    ops.enable_queued_provisioning = args.enable_queued_provisioning
    ops.tpu_topology = args.tpu_topology
    ops.enable_nested_virtualization = args.enable_nested_virtualization
    ops.enable_best_effort_provision = args.enable_best_effort_provision
    ops.min_provision_nodes = args.min_provision_nodes
    ops.host_maintenance_interval = args.host_maintenance_interval
    ops.performance_monitoring_unit = args.performance_monitoring_unit
    ops.autoscaled_rollout_policy = args.autoscaled_rollout_policy
    ops.ephemeral_storage = ephemeral_storage
    ops.secondary_boot_disks = args.secondary_boot_disk
    ops.enable_confidential_storage = args.enable_confidential_storage
    ops.storage_pools = args.storage_pools
    return ops

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddAcceleratorArgs(
        parser,
        enable_gpu_partition=True,
        enable_gpu_sharing=True,
        enable_gpu_deprecated_fields=True,
        enable_gpu_driver_installation=True)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddNodePoolAutoprovisioningFlag(parser, hidden=False)
    flags.AddLocalSSDsAlphaFlags(parser, for_node_pool=True)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddPreemptibleFlag(parser, for_node_pool=True)
    flags.AddEnableAutoRepairFlag(parser, for_node_pool=True, for_create=True)
    flags.AddMinCpuPlatformFlag(parser, for_node_pool=True)
    flags.AddWorkloadMetadataFlag(parser, use_mode=False)
    flags.AddNodeTaintsFlag(parser, for_node_pool=True)
    flags.AddNodePoolNodeIdentityFlags(parser)
    flags.AddMaxPodsPerNodeFlag(parser, for_node_pool=True)
    flags.AddSandboxFlag(parser)
    flags.AddNodeGroupFlag(parser)
    flags.AddEnableAutoUpgradeFlag(parser, for_node_pool=True, default=True)
    flags.AddLinuxSysctlFlags(parser, for_node_pool=True)
    flags.AddSurgeUpgradeFlag(parser, for_node_pool=True, default=1)
    flags.AddMaxUnavailableUpgradeFlag(
        parser, for_node_pool=True, is_create=True)
    flags.AddNodePoolLocationsFlag(parser, for_create=True)
    flags.AddSystemConfigFlag(parser, hidden=False)
    flags.AddReservationAffinityFlags(parser, for_node_pool=True)
    flags.AddEnableGcfsFlag(parser, for_node_pool=True)
    flags.AddEnableImageStreamingFlag(parser, for_node_pool=True)
    flags.AddNodePoolEnablePrivateNodes(parser)
    flags.AddEnableGvnicFlag(parser)
    flags.AddSpotFlag(parser, for_node_pool=True)
    flags.AddPlacementTypeFlag(parser, for_node_pool=True, hidden=False)
    flags.AddPlacementPolicyFlag(parser)
    flags.AddEnableSurgeUpgradeFlag(parser)
    flags.AddEnableBlueGreenUpgradeFlag(parser)
    flags.AddStandardRolloutPolicyFlag(parser, for_node_pool=True)
    flags.AddNodePoolSoakDurationFlag(parser, for_node_pool=True)
    flags.AddMaintenanceIntervalFlag(parser, for_node_pool=True, hidden=True)
    flags.AddNetworkPerformanceConfigFlags(parser, hidden=False)
    flags.AddEnableConfidentialNodesFlag(parser, for_node_pool=True)
    flags.AddEnableConfidentialStorageFlag(parser, for_node_pool=True)
    flags.AddStoragePoolsFlag(
        parser, for_node_pool=True, for_create=True, hidden=False)
    flags.AddDisablePodCIDROverprovisionFlag(parser)
    flags.AddEnableFastSocketFlag(parser)
    flags.AddLoggingVariantFlag(parser, for_node_pool=True)
    flags.AddWindowsOsVersionFlag(parser)
    flags.AddBestEffortProvisionFlags(parser, hidden=False)
    flags.AddQueuedProvisioningFlag(parser)
    flags.AddTPUTopologyFlag(parser)
    flags.AddEnableNestedVirtualizationFlag(parser, hidden=True)
    flags.AddHostMaintenanceIntervalFlag(
        parser, for_node_pool=True, hidden=True)
    flags.AddPerformanceMonitoringUnit(parser, hidden=True)
    flags.AddAutoscaleRolloutPolicyFlag(parser)
    flags.AddResourceManagerTagsCreate(parser, for_node_pool=True)
    flags.AddSecondaryBootDisksArgs(parser, hidden=True)

Create.detailed_help = DETAILED_HELP
