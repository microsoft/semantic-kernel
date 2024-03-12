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
"""Create cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import string

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.command_lib.container import container_command_util as cmd_util
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def _AddAdditionalZonesFlag(parser, deprecated=True):
  action = None
  if deprecated:
    action = actions.DeprecationAction(
        'additional-zones',
        warn='This flag is deprecated. '
        'Use --node-locations=PRIMARY_ZONE,[ZONE,...] instead.')
  parser.add_argument(
      '--additional-zones',
      type=arg_parsers.ArgList(min_length=1),
      action=action,
      metavar='ZONE',
      help="""\
The set of additional zones in which the specified node footprint should be
replicated. All zones must be in the same region as the cluster's primary zone.
If additional-zones is not specified, all nodes will be in the cluster's primary
zone.

Note that `NUM_NODES` nodes will be created in each zone, such that if you
specify `--num-nodes=4` and choose one additional zone, 8 nodes will be created.

Multiple locations can be specified, separated by commas. For example:

  $ {command} example-cluster --zone us-central1-a --additional-zones us-central1-b,us-central1-c
""")


def _AddAdditionalZonesGroup(parser):
  group = parser.add_mutually_exclusive_group()
  _AddAdditionalZonesFlag(group, deprecated=True)
  flags.AddNodeLocationsFlag(group)


def _GetEnableStackdriver(args):
  # hasattr checks if field exists, if not isSpecified would throw exception
  if not hasattr(args, 'enable_stackdriver_kubernetes'):
    return None
  if not args.IsSpecified('enable_stackdriver_kubernetes'):
    return None
  return args.enable_stackdriver_kubernetes


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument(
      'name',
      help="""\
The name of the cluster to create.

The name may contain only lowercase alphanumerics and '-', must start with a
letter and end with an alphanumeric, and must be no longer than 40
characters.
""")
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=3600,
      hidden=True,
      help='Timeout (seconds) for waiting on the operation to complete.')
  flags.AddAsyncFlag(parser)

  parser.add_argument(
      '--subnetwork',
      help="""\
The Google Compute Engine subnetwork
(https://cloud.google.com/compute/docs/subnetworks) to which the cluster is
connected. The subnetwork must belong to the network specified by --network.

Cannot be used with the "--create-subnetwork" option.
""")
  parser.add_argument(
      '--network',
      help='The Compute Engine Network that the cluster will connect to. '
      'Google Kubernetes Engine will use this network when creating routes '
      'and firewalls for the clusters. Defaults to the \'default\' network.')
  parser.add_argument(
      '--cluster-ipv4-cidr',
      help="""\
The IP address range for the pods in this cluster in CIDR notation (e.g.
10.0.0.0/14). Prior to Kubernetes version 1.7.0 this must be a subset of
10.0.0.0/8; however, starting with version 1.7.0 can be any RFC 1918 IP range.

If you omit this option, a range is chosen automatically.  The automatically
chosen range is randomly selected from 10.0.0.0/8 and will not include IP
address ranges allocated to VMs, existing routes, or ranges allocated to other
clusters. The automatically chosen range might conflict with reserved IP
addresses, dynamic routes, or routes within VPCs that peer with this cluster.
You should specify `--cluster-ipv4-cidr` to prevent conflicts.
""")

  parser.display_info.AddFormat(util.CLUSTERS_FORMAT)


def _IsSpecified(args, name):
  """Returns true if an arg is defined and specified, false otherwise."""
  return hasattr(args, name) and args.IsSpecified(name)


cloudNatTemplate = string.Template(
    'Note: This cluster has private nodes. If you need connectivity to the '
    'public internet, for example to pull public containers, you must '
    'configure Cloud NAT. To enable NAT for the network of this cluster, run '
    'the following commands: \n'
    'gcloud compute routers create my-router --region $REGION '
    '--network default --project=$PROJECT_ID \n'
    'gcloud beta compute routers nats create nat --router=my-router '
    '--region=$REGION --auto-allocate-nat-external-ips '
    '--nat-all-subnet-ip-ranges --project=$PROJECT_ID')


def MaybeLogCloudNatHelpText(args, is_autopilot, location, project_id):
  if is_autopilot and (getattr(args, 'enable_private_nodes', False) and
                       (hasattr(args, 'network') or hasattr('subnetwork'))):
    log.status.Print(
        cloudNatTemplate.substitute(REGION=location, PROJECT_ID=project_id))


def ParseCreateOptionsBase(args, is_autopilot, get_default, location,
                           project_id):
  """Parses the flags provided with the cluster creation command."""
  flags.MungeBasicAuthFlags(args)

  enable_ip_alias = get_default('enable_ip_alias')
  if hasattr(args, 'enable_ip_alias'):
    flags.WarnForUnspecifiedIpAllocationPolicy(args)
  flags.WarnForEnablingBetaAPIs(args)
  enable_autorepair = None
  if hasattr(args, 'enable_autorepair'):
    enable_autorepair = cmd_util.GetAutoRepair(args)
    if enable_autorepair:
      flags.WarnForNodeModification(args, enable_autorepair)

  metadata = metadata_utils.ConstructMetadataDict(
      get_default('metadata'), get_default('metadata_from_file'))

  cloud_run_config = flags.GetLegacyCloudRunFlag('{}_config', args, get_default)
  flags.ValidateCloudRunConfigCreateArgs(cloud_run_config,
                                         get_default('addons'))

  MaybeLogCloudNatHelpText(args, is_autopilot, location, project_id)

  flags.ValidateNotificationConfigFlag(args)

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

  addons = get_default('addons')
  if getattr(args, 'enable_backup_restore', None):
    if addons is None:
      addons = api_adapter.BACKUPRESTORE
    else:
      addons += api_adapter.BACKUPRESTORE

  return api_adapter.CreateClusterOptions(
      accelerators=get_default('accelerator'),
      additional_zones=get_default('additional_zones'),
      addons=addons,
      boot_disk_kms_key=get_default('boot_disk_kms_key'),
      cluster_dns=get_default('cluster_dns'),
      cluster_dns_scope=get_default('cluster_dns_scope'),
      additive_vpc_scope_dns_domain=get_default(
          'additive_vpc_scope_dns_domain'
      ),
      disable_additive_vpc_scope=get_default('disable_additive_vpc_scope'),
      cluster_dns_domain=get_default('cluster_dns_domain'),
      cluster_ipv4_cidr=get_default('cluster_ipv4_cidr'),
      cluster_secondary_range_name=get_default('cluster_secondary_range_name'),
      cluster_version=get_default('cluster_version'),
      cloud_run_config=cloud_run_config,
      node_version=get_default('node_version'),
      create_subnetwork=get_default('create_subnetwork'),
      disable_default_snat=get_default('disable_default_snat'),
      dataplane_v2=get_default('enable_dataplane_v2'),
      enable_dataplane_v2_metrics=get_default('enable_dataplane_v2_metrics'),
      disable_dataplane_v2_metrics=get_default('disable_dataplane_v2_metrics'),
      enable_dataplane_v2_flow_observability=get_default(
          'enable_dataplane_v2_flow_observability'
      ),
      disable_dataplane_v2_flow_observability=get_default(
          'disable_dataplane_v2_flow_observability'
      ),
      dataplane_v2_observability_mode=get_default(
          'dataplane_v2_observability_mode'
      ),
      disk_type=get_default('disk_type'),
      enable_autorepair=enable_autorepair,
      enable_autoscaling=get_default('enable_autoscaling'),
      location_policy=get_default('location_policy'),
      enable_autoupgrade=(
          cmd_util.GetAutoUpgrade(args)
          if hasattr(args, 'enable_autoupgrade')
          else None
      ),
      enable_binauthz=get_default('enable_binauthz'),
      binauthz_evaluation_mode=get_default('binauthz_evaluation_mode'),
      binauthz_policy_bindings=get_default('binauthz_policy_bindings'),
      enable_stackdriver_kubernetes=_GetEnableStackdriver(args),
      enable_cloud_logging=(
          args.enable_cloud_logging
          if args.IsKnownAndSpecified('enable_cloud_logging')
          else None
      ),
      enable_cloud_monitoring=(
          args.enable_cloud_monitoring
          if args.IsKnownAndSpecified('enable_cloud_monitoring')
          else None
      ),
      enable_workload_monitoring_eap=get_default(
          'enable_workload_monitoring_eap'
      ),
      logging=get_default('logging'),
      monitoring=get_default('monitoring'),
      enable_l4_ilb_subsetting=get_default('enable_l4_ilb_subsetting'),
      enable_ip_alias=enable_ip_alias,
      enable_intra_node_visibility=get_default('enable_intra_node_visibility'),
      enable_kubernetes_alpha=get_default('enable_kubernetes_alpha'),
      enable_cloud_run_alpha=flags.GetLegacyCloudRunFlag(
          'enable_{}_alpha', args, get_default
      ),
      enable_legacy_authorization=get_default('enable_legacy_authorization'),
      enable_managed_prometheus=get_default('enable_managed_prometheus'),
      enable_master_authorized_networks=get_default(
          'enable_master_authorized_networks'
      ),
      enable_master_global_access=get_default('enable_master_global_access'),
      enable_mesh_certificates=get_default('enable_mesh_certificates'),
      enable_network_policy=get_default('enable_network_policy'),
      enable_private_nodes=get_default('enable_private_nodes'),
      enable_private_endpoint=get_default('enable_private_endpoint'),
      enable_gke_oidc=getattr(args, 'enable_gke_oidc', None),
      enable_identity_service=getattr(args, 'enable_identity_service', None),
      ephemeral_storage_local_ssd=(ephemeral_storage_local_ssd),
      image_type=get_default('image_type'),
      image=get_default('image'),
      image_project=get_default('image_project'),
      image_family=get_default('image_family'),
      issue_client_certificate=get_default('issue_client_certificate'),
      labels=get_default('labels'),
      local_nvme_ssd_block=(local_nvme_ssd_block),
      local_ssd_count=get_default('local_ssd_count'),
      maintenance_window=get_default('maintenance_window'),
      maintenance_window_start=get_default('maintenance_window_start'),
      maintenance_window_end=get_default('maintenance_window_end'),
      maintenance_window_recurrence=get_default(
          'maintenance_window_recurrence'
      ),
      master_authorized_networks=get_default('master_authorized_networks'),
      master_ipv4_cidr=get_default('master_ipv4_cidr'),
      max_nodes=get_default('max_nodes'),
      max_nodes_per_pool=get_default('max_nodes_per_pool'),
      min_cpu_platform=get_default('min_cpu_platform'),
      min_nodes=get_default('min_nodes'),
      total_max_nodes=get_default('total_max_nodes'),
      total_min_nodes=get_default('total_min_nodes'),
      network=get_default('network'),
      node_disk_size_gb=utils.BytesToGb(args.disk_size)
      if hasattr(args, 'disk_size')
      else None,
      node_labels=get_default('node_labels'),
      node_locations=get_default('node_locations'),
      node_machine_type=get_default('machine_type'),
      node_taints=get_default('node_taints'),
      notification_config=get_default('notification_config'),
      autoscaling_profile=getattr(args, 'autoscaling_profile', None),
      num_nodes=get_default('num_nodes'),
      password=get_default('password'),
      preemptible=get_default('preemptible'),
      security_group=get_default('security_group'),
      scopes=get_default('scopes'),
      service_account=get_default('service_account'),
      services_ipv4_cidr=get_default('services_ipv4_cidr'),
      services_secondary_range_name=get_default(
          'services_secondary_range_name'
      ),
      subnetwork=get_default('subnetwork'),
      system_config_from_file=get_default('system_config_from_file'),
      private_ipv6_google_access_type=get_default(
          'private_ipv6_google_access_type'
      ),
      tags=get_default('tags'),
      autoprovisioning_network_tags=get_default(
          'autoprovisioning_network_tags'
      ),
      threads_per_core=get_default('threads_per_core'),
      user=get_default('username'),
      metadata=metadata,
      default_max_pods_per_node=get_default('default_max_pods_per_node'),
      max_pods_per_node=get_default('max_pods_per_node'),
      enable_tpu=get_default('enable_tpu'),
      tpu_ipv4_cidr=get_default('tpu_ipv4_cidr'),
      resource_usage_bigquery_dataset=get_default(
          'resource_usage_bigquery_dataset'
      ),
      enable_network_egress_metering=get_default(
          'enable_network_egress_metering'
      ),
      enable_resource_consumption_metering=get_default(
          'enable_resource_consumption_metering'
      ),
      database_encryption_key=get_default('database_encryption_key'),
      workload_pool=get_default('workload_pool'),
      identity_provider=get_default('identity_provider'),
      workload_metadata=get_default('workload_metadata'),
      workload_metadata_from_node=get_default('workload_metadata_from_node'),
      enable_vertical_pod_autoscaling=get_default(
          'enable_vertical_pod_autoscaling'
      ),
      enable_experimental_vertical_pod_autoscaling=get_default(
          'enable_experimental_vertical_pod_autoscaling'
      ),
      enable_autoprovisioning=get_default('enable_autoprovisioning'),
      autoprovisioning_config_file=get_default('autoprovisioning_config_file'),
      autoprovisioning_service_account=get_default(
          'autoprovisioning_service_account'
      ),
      autoprovisioning_scopes=get_default('autoprovisioning_scopes'),
      autoprovisioning_locations=get_default('autoprovisioning_locations'),
      autoprovisioning_max_surge_upgrade=get_default(
          'autoprovisioning_max_surge_upgrade'
      ),
      autoprovisioning_max_unavailable_upgrade=get_default(
          'autoprovisioning_max_unavailable_upgrade'
      ),
      enable_autoprovisioning_surge_upgrade=get_default(
          'enable_autoprovisioning_surge_upgrade'
      ),
      enable_autoprovisioning_blue_green_upgrade=get_default(
          'enable_autoprovisioning_blue_green_upgrade'
      ),
      autoprovisioning_standard_rollout_policy=get_default(
          'autoprovisioning_standard_rollout_policy'
      ),
      autoprovisioning_node_pool_soak_duration=get_default(
          'autoprovisioning_node_pool_soak_duration'
      ),
      enable_autoprovisioning_autorepair=get_default(
          'enable_autoprovisioning_autorepair'
      ),
      enable_autoprovisioning_autoupgrade=get_default(
          'enable_autoprovisioning_autoupgrade'
      ),
      autoprovisioning_min_cpu_platform=get_default(
          'autoprovisioning_min_cpu_platform'
      ),
      min_cpu=get_default('min_cpu'),
      max_cpu=get_default('max_cpu'),
      min_memory=get_default('min_memory'),
      max_memory=get_default('max_memory'),
      min_accelerator=get_default('min_accelerator'),
      max_accelerator=get_default('max_accelerator'),
      autoprovisioning_image_type=get_default('autoprovisioning_image_type'),
      shielded_secure_boot=get_default('shielded_secure_boot'),
      shielded_integrity_monitoring=get_default(
          'shielded_integrity_monitoring'
      ),
      reservation_affinity=get_default('reservation_affinity'),
      reservation=get_default('reservation'),
      release_channel=get_default('release_channel'),
      enable_shielded_nodes=get_default('enable_shielded_nodes'),
      max_surge_upgrade=get_default('max_surge_upgrade'),
      max_unavailable_upgrade=get_default('max_unavailable_upgrade'),
      autopilot=is_autopilot,
      gvnic=get_default('enable_gvnic'),
      enable_confidential_nodes=get_default('enable_confidential_nodes'),
      enable_confidential_storage=get_default('enable_confidential_storage'),
      storage_pools=get_default('storage_pools'),
      enable_image_streaming=get_default('enable_image_streaming'),
      spot=get_default('spot'),
      enable_service_externalips=get_default('enable_service_externalips'),
      disable_pod_cidr_overprovision=get_default(
          'disable_pod_cidr_overprovision'
      ),
      stack_type=get_default('stack_type'),
      ipv6_access_type=get_default('ipv6_access_type'),
      private_endpoint_subnetwork=get_default('private_endpoint_subnetwork'),
      enable_google_cloud_access=get_default('enable_google_cloud_access'),
      gateway_api=get_default('gateway_api'),
      logging_variant=get_default('logging_variant'),
      enable_cost_allocation=get_default('enable_cost_allocation'),
      enable_multi_networking=get_default('enable_multi_networking'),
      placement_type=get_default('placement_type'),
      placement_policy=get_default('placement_policy'),
      enable_security_posture=get_default('enable_security_posture'),
      network_performance_config=get_default('network_performance_configs'),
      enable_insecure_kubelet_readonly_port=get_default(
          'enable_insecure_kubelet_readonly_port'
      ),
      autoprovisioning_enable_insecure_kubelet_readonly_port=get_default(
          'autoprovisioning_enable_insecure_kubelet_readonly_port'
      ),
      enable_k8s_beta_apis=getattr(args, 'enable_kubernetes_unstable_apis'),
      security_posture=get_default('security_posture'),
      workload_vulnerability_scanning=get_default(
          'workload_vulnerability_scanning'
      ),
      enable_runtime_vulnerability_insight=get_default(
          'enable_runtime_vulnerability_insight'
      ),
      workload_policies=get_default('workload_policies'),
      in_transit_encryption=get_default('in_transit_encryption'),
      containerd_config_from_file=get_default('containerd_config_from_file'),
      fleet_project=get_default('fleet_project'),
      enable_fleet=get_default('enable_fleet'),
      enable_secret_manager=get_default('enable_secret_manager'),
      enable_cilium_clusterwide_network_policy=get_default(
          'enable_cilium_clusterwide_network_policy'
      ),
      resource_manager_tags=get_default('resource_manager_tags'),
      autoprovisioning_resource_manager_tags=get_default(
          'autoprovisioning_resource_manager_tags'
      ),
      enable_fqdn_network_policy=get_default('enable_fqdn_network_policy'),
  )


GA = 'ga'
BETA = 'beta'
ALPHA = 'alpha'


def AddAutoRepair(parser):
  flags.AddEnableAutoRepairFlag(parser, for_create=True)


def AddPrivateClusterDeprecated(parser, default=None):
  default_value = {} if default is None else default
  flags.AddPrivateClusterFlags(
      parser, default=default_value, with_deprecated=True)


def AddEnableAutoUpgradeWithDefault(parser):
  flags.AddEnableAutoUpgradeFlag(parser, default=True)


def AddAutoprovisioning(parser):
  flags.AddAutoprovisioningFlags(parser, hidden=False, for_create=True)


def AddTpuWithServiceNetworking(parser):
  flags.AddTpuFlags(parser, enable_tpu_service_networking=True)


def AddDisableDefaultSnatFlagForClusterCreate(parser):
  flags.AddDisableDefaultSnatFlag(parser, for_cluster_create=True)


def AddMasterSignalsFlag(parser):
  flags.AddEnableMasterSignalsFlags(parser, for_create=True)


def AddPrivateIPv6Flag(api, parser):
  flags.AddPrivateIpv6GoogleAccessTypeFlag(api, parser)


def AddAcceleratorFlag(
    parser,
    enable_gpu_partition,
    enable_gpu_sharing,
    enable_gpu_deprecated_fields,
    enable_gpu_driver_installation,
):
  flags.AddAcceleratorArgs(
      parser,
      enable_gpu_partition=enable_gpu_partition,
      enable_gpu_sharing=enable_gpu_sharing,
      enable_gpu_deprecated_fields=enable_gpu_deprecated_fields,
      enable_gpu_driver_installation=enable_gpu_driver_installation,
  )


def AddKubernetesObjectsExportFlag(parser):
  flags.AddKubernetesObjectsExportConfig(parser, for_create=True)


def DefaultAttribute(flagname, flag_defaults):
  if flagname in flag_defaults:
    return flag_defaults[flagname]
  return None


def AttrValue(args, flagname, flag_defaults):
  return getattr(args, flagname, DefaultAttribute(flagname, flag_defaults))


flags_to_add = {
    GA: {
        'accelerator': lambda p: AddAcceleratorFlag(p, True, True, False, True),
        'additionalzones': _AddAdditionalZonesFlag,
        'addons': flags.AddAddonsFlags,
        'autorepair': AddAutoRepair,
        'autoprovisioning': AddAutoprovisioning,
        'autoscalingprofiles': flags.AddAutoscalingProfilesFlag,
        'autoupgrade': AddEnableAutoUpgradeWithDefault,
        'authenticatorsecurity': flags.AddAuthenticatorSecurityGroupFlags,
        'args': _Args,
        'basicauth': flags.AddBasicAuthFlags,
        'binauthz': lambda p: flags.AddBinauthzFlags(
            p, release_track=base.ReleaseTrack.GA
        ),
        'bootdiskkms': flags.AddBootDiskKmsKeyFlag,
        'cloudlogging': flags.AddEnableCloudLogging,
        'cloudmonitoring': flags.AddEnableCloudMonitoring,
        'cloudrunalpha': flags.AddEnableCloudRunAlphaFlag,
        'cloudrunconfig': flags.AddCloudRunConfigFlag,
        'clusterautoscaling': functools.partial(
            flags.AddClusterAutoscalingFlags
        ),
        'clusterdns': lambda p: flags.AddClusterDNSFlags(
            p, release_track=base.ReleaseTrack.GA
        ),
        'clusterversion': flags.AddClusterVersionFlag,
        'confidentialnodes': flags.AddEnableConfidentialNodesFlag,
        'costmanagementconfig': flags.AddCostManagementConfigFlag,
        'disabledefaultsnat': AddDisableDefaultSnatFlagForClusterCreate,
        'databaseencryption': flags.AddDatabaseEncryptionFlag,
        'dataplanev2': flags.AddDataplaneV2Flag,
        'dataplanev2metrics': flags.AddDataplaneV2MetricsFlag,
        'dataplanev2obs': flags.AddDataplaneV2ObservabilityFlags,
        'disksize': flags.AddDiskSizeFlag,
        'disktype': flags.AddDiskTypeFlag,
        'identityservice': flags.AddIdentityServiceFlag,
        'imagestreaming': flags.AddEnableImageStreamingFlag,
        'ilbsubsetting': flags.AddILBSubsettingFlags,
        'imageflags': flags.AddImageFlagsCreate,
        'intranodevisibility': flags.AddEnableIntraNodeVisibilityFlag,
        'ipalias': flags.AddIpAliasCoreFlag,
        'ipalias_additional': flags.AddIPAliasRelatedFlags,
        'issueclientcert': flags.AddIssueClientCertificateFlag,
        'gatewayapi': flags.AddGatewayFlags,
        'gvnic': flags.AddEnableGvnicFlag,
        'kubernetesalpha': flags.AddEnableKubernetesAlphaFlag,
        'labels': flags.AddLabelsFlag,
        'legacyauth': flags.AddEnableLegacyAuthorizationFlag,
        'localssds': flags.AddLocalSSDsGAFlags,
        'logging': flags.AddLoggingFlag,
        'machinetype': flags.AddMachineTypeFlag,
        'maintenancewindow': flags.AddMaintenanceWindowGroup,
        'managedprometheus': lambda p: flags.AddManagedPrometheusFlags(
            p, for_create=True
        ),
        'masterauth': flags.AddMasterAuthorizedNetworksFlags,
        'masterglobalaccess': flags.AddMasterGlobalAccessFlag,
        'maxnodes': flags.AddMaxNodesPerPool,
        'maxpodspernode': flags.AddMaxPodsPerNodeFlag,
        'maxunavailable': flags.AddMaxUnavailableUpgradeFlag,
        'meshcertificates': flags.AddMeshCertificatesFlags,
        'metadata': flags.AddMetadataFlags,
        'mincpu': flags.AddMinCpuPlatformFlag,
        'monitoring': flags.AddMonitoringFlag,
        'networkpolicy': flags.AddNetworkPolicyFlags,
        'nodeidentity': flags.AddClusterNodeIdentityFlags,
        'nodelabels': flags.AddNodeLabelsFlag,
        'nodelocations': flags.AddNodeLocationsFlag,
        'nodetaints': flags.AddNodeTaintsFlag,
        'nodeversion': flags.AddNodeVersionFlag,
        'notificationconfig': flags.AddNotificationConfigFlag,
        'num_nodes': flags.AddNumNodes,
        'placementtype': flags.AddPlacementTypeFlag,
        'placementpolicy': flags.AddPlacementPolicyFlag,
        'preemptible': flags.AddPreemptibleFlag,
        'privatecluster': flags.AddPrivateClusterFlags,
        'privateipv6type': lambda p: AddPrivateIPv6Flag('v1', p),
        'releasechannel': flags.AddReleaseChannelFlag,
        'resourceManagerTags': flags.AddResourceManagerTagsCreate,
        'autoprovisioningResourceManagerTags': (
            flags.AddAutoprovisioningResourceManagerTagsCreate
        ),
        'reservationaffinity': flags.AddReservationAffinityFlags,
        'resourceusageexport': flags.AddResourceUsageExportFlags,
        'shieldedinstance': flags.AddShieldedInstanceFlags,
        'shieldednodes': flags.AddEnableShieldedNodesFlags,
        'spot': lambda p: flags.AddSpotFlag(p, hidden=False),
        'surgeupgrade': lambda p: flags.AddSurgeUpgradeFlag(p, default=1),
        'systemconfig': lambda p: flags.AddSystemConfigFlag(p, hidden=False),
        'stackdriver': flags.AddEnableStackdriverKubernetesFlag,
        'stacktype': flags.AddStackTypeFlag,
        'ipv6accesstype': flags.AddIpv6AccessTypeFlag,
        'tags': flags.AddTagsCreate,
        'threads_per_core': flags.AddThreadsPerCore,
        'autoprovisioning_network_tags': (
            flags.AddAutoprovisioningNetworkTagsCreate
        ),
        'tpu': flags.AddTpuFlags,
        'verticalpodautoscaling': flags.AddVerticalPodAutoscalingFlags,
        'workloadidentity': flags.AddWorkloadIdentityFlags,
        'workloadmetadata': flags.AddWorkloadMetadataFlag,
        'enableserviceexternalips': flags.AddEnableServiceExternalIPs,
        'disablepodcidroverprovision': (
            lambda p: flags.AddDisablePodCIDROverprovisionFlag(p, hidden=True)
        ),
        'privateEndpointSubnetwork': flags.AddPrivateEndpointSubnetworkFlag,
        'enableGoogleCloudAccess': flags.AddEnableGoogleCloudAccess,
        'fleetProject': flags.AddFleetProjectFlag,
        'loggingvariant': flags.AddLoggingVariantFlag,
        'enableMultiNetworking': flags.AddEnableMultiNetworkingFlag,
        'enableSecurityPosture': flags.AddSecurityPostureFlag,
        'clusterNetworkPerformanceConfig': (
            flags.AddClusterNetworkPerformanceConfigFlags
        ),
        'enableKubeletReadonlyPort': flags.AddEnableKubeletReadonlyPortFlag,
        'autoprovisioningEnableKubeletReadonlyPort': (
            flags.AddAutoprovisioningEnableKubeletReadonlyPortFlag
        ),
        'enableK8sBetaApis': flags.AddEnableK8sBetaAPIs,
        'securityPosture': flags.AddSecurityPostureEnumFlag,
        'workloadVulnerabilityScanning': flags.AddWorkloadVulnScanningEnumFlag,
        'enableRuntimeVulnerabilityInsight': (
            flags.AddRuntimeVulnerabilityInsightFlag
        ),
        'containerdConfig': lambda p: flags.AddContainerdConfigFlag(
            p, hidden=True
        ),
        'InTransitEncryption': flags.AddInTransitEncryptionFlag,
        'enableCiliumClusterwideNetworkPolicy': (
            flags.AddEnableCiliumClusterwideNetworkPolicyFlag
        ),
        'enableFqdnNetworkPolicy': flags.AddEnableFqdnNetworkPolicyFlag,
    },
    BETA: {
        'accelerator': lambda p: AddAcceleratorFlag(p, True, True, True, True),
        'additionalzones': _AddAdditionalZonesGroup,
        'addons': flags.AddBetaAddonsFlags,
        'allowrouteoverlap': flags.AddAllowRouteOverlapFlag,
        'args': _Args,
        'autorepair': AddAutoRepair,
        'autoprovisioning': AddAutoprovisioning,
        'autoscalingprofiles': flags.AddAutoscalingProfilesFlag,
        'authenticatorsecurity': flags.AddAuthenticatorSecurityGroupFlags,
        'autoupgrade': AddEnableAutoUpgradeWithDefault,
        'basicauth': flags.AddBasicAuthFlags,
        'binauthz': lambda p: flags.AddBinauthzFlags(
            p, release_track=base.ReleaseTrack.BETA
        ),
        'bootdiskkms': flags.AddBootDiskKmsKeyFlag,
        'cloudlogging': flags.AddEnableCloudLogging,
        'cloudmonitoring': flags.AddEnableCloudMonitoring,
        'cloudrunalpha': flags.AddEnableCloudRunAlphaFlag,
        'cloudrunconfig': flags.AddCloudRunConfigFlag,
        'clusterautoscaling': functools.partial(
            flags.AddClusterAutoscalingFlags
        ),
        'clusterdns': lambda p: flags.AddClusterDNSFlags(
            p, release_track=base.ReleaseTrack.BETA
        ),
        'clusterversion': flags.AddClusterVersionFlag,
        'costmanagementconfig': flags.AddCostManagementConfigFlag,
        'placementtype': flags.AddPlacementTypeFlag,
        'placementpolicy': flags.AddPlacementPolicyFlag,
        'confidentialnodes': flags.AddEnableConfidentialNodesFlag,
        'enableconfidentialstorage': flags.AddEnableConfidentialStorageFlag,
        'databaseencryption': flags.AddDatabaseEncryptionFlag,
        'datapath': lambda p: flags.AddDatapathProviderFlag(p, hidden=True),
        'dataplanev2': flags.AddDataplaneV2Flag,
        'dataplanev2metrics': flags.AddDataplaneV2MetricsFlag,
        'dataplanev2obs': flags.AddDataplaneV2ObservabilityFlags,
        'disabledefaultsnat': AddDisableDefaultSnatFlagForClusterCreate,
        'disksize': flags.AddDiskSizeFlag,
        'disktype': flags.AddDiskTypeFlag,
        'gatewayapi': flags.AddGatewayFlags,
        'gcfs': flags.AddEnableGcfsFlag,
        'imagestreaming': flags.AddEnableImageStreamingFlag,
        'imageflags': flags.AddImageFlagsCreate,
        'intranodevisibility': flags.AddEnableIntraNodeVisibilityFlag,
        'ipalias': flags.AddIpAliasCoreFlag,
        'ipalias_additional': flags.AddIPAliasRelatedFlags,
        'issueclientcert': flags.AddIssueClientCertificateFlag,
        'istioconfig': flags.AddIstioConfigFlag,
        'kubernetesalpha': flags.AddEnableKubernetesAlphaFlag,
        'kubernetesobjectsexport': AddKubernetesObjectsExportFlag,
        'gvnic': flags.AddEnableGvnicFlag,
        'gkeoidc': flags.AddGkeOidcFlag,
        'hostmaintenanceinterval': flags.AddHostMaintenanceIntervalFlag,
        'identityservice': flags.AddIdentityServiceFlag,
        'ilbsubsetting': flags.AddILBSubsettingFlags,
        'localssds': flags.AddLocalSSDsBetaFlags,
        'loggingmonitoring': flags.AddEnableLoggingMonitoringSystemOnlyFlag,
        'logging': flags.AddLoggingFlag,
        'labels': flags.AddLabelsFlag,
        'legacyauth': flags.AddEnableLegacyAuthorizationFlag,
        'machinetype': flags.AddMachineTypeFlag,
        'maintenancewindow': flags.AddMaintenanceWindowGroup,
        'managedprometheus': lambda p: flags.AddManagedPrometheusFlags(
            p, for_create=True
        ),
        'masterglobalaccess': flags.AddMasterGlobalAccessFlag,
        'masterauth': flags.AddMasterAuthorizedNetworksFlags,
        'mastersignals': AddMasterSignalsFlag,
        'maxnodes': flags.AddMaxNodesPerPool,
        'maxpodspernode': flags.AddMaxPodsPerNodeFlag,
        'maxunavailable': lambda p: flags.AddMaxUnavailableUpgradeFlag(
            p, is_create=True
        ),
        'meshcertificates': flags.AddMeshCertificatesFlags,
        'metadata': flags.AddMetadataFlags,
        'mincpu': flags.AddMinCpuPlatformFlag,
        'maintenanceinterval': flags.AddMaintenanceIntervalFlag,
        'monitoring': flags.AddMonitoringFlag,
        'nestedvirtualization': (
            lambda p: flags.AddEnableNestedVirtualizationFlag(p, hidden=True)
        ),
        'networkpolicy': flags.AddNetworkPolicyFlags,
        'nodetaints': flags.AddNodeTaintsFlag,
        'nodeidentity': flags.AddClusterNodeIdentityFlags,
        'nodeversion': flags.AddNodeVersionFlag,
        'nodelabels': flags.AddNodeLabelsFlag,
        'notificationconfig': flags.AddNotificationConfigFlag,
        'num_nodes': flags.AddNumNodes,
        'podsecuritypolicy': flags.AddPodSecurityPolicyFlag,
        'preemptible': flags.AddPreemptibleFlag,
        'privatecluster': AddPrivateClusterDeprecated,
        'privateipv6type': lambda p: AddPrivateIPv6Flag('v1beta1', p),
        'releasechannel': flags.AddReleaseChannelFlag,
        'resourceManagerTags': flags.AddResourceManagerTagsCreate,
        'autoprovisioningResourceManagerTags': (
            flags.AddAutoprovisioningResourceManagerTagsCreate
        ),
        'resourceusageexport': flags.AddResourceUsageExportFlags,
        'reservationaffinity': flags.AddReservationAffinityFlags,
        'shieldedinstance': flags.AddShieldedInstanceFlags,
        'shieldednodes': flags.AddEnableShieldedNodesFlags,
        'spot': flags.AddSpotFlag,
        'stackdriver': flags.AddEnableStackdriverKubernetesFlag,
        'stacktype': flags.AddStackTypeFlag,
        'storagePools': flags.AddStoragePoolsFlag,
        'ipv6accesstype': flags.AddIpv6AccessTypeFlag,
        'surgeupgrade': lambda p: flags.AddSurgeUpgradeFlag(p, default=1),
        'systemconfig': lambda p: flags.AddSystemConfigFlag(p, hidden=False),
        'tags': flags.AddTagsCreate,
        'autoprovisioning_network_tags': (
            flags.AddAutoprovisioningNetworkTagsCreate
        ),
        'threads_per_core': flags.AddThreadsPerCore,
        'tpu': AddTpuWithServiceNetworking,
        'verticalpodautoscaling': (
            flags.AddVerticalPodAutoscalingFlagsExperimental
        ),
        'workloadAlts': flags.AddWorkloadAltsFlags,
        'workloadcertificates': flags.AddWorkloadCertificatesFlags,
        'workloadidentity': lambda p: flags.AddWorkloadIdentityFlags(p, True),
        'workloadmetadata': lambda p: flags.AddWorkloadMetadataFlag(
            p, use_mode=False
        ),
        'workloadmonitoringeap': flags.AddEnableWorkloadMonitoringEapFlag,
        'privateEndpointSubnetwork': flags.AddPrivateEndpointSubnetworkFlag,
        'crossConnectNetworks': flags.AddCrossConnectSubnetworksFlag,
        'enableserviceexternalips': flags.AddEnableServiceExternalIPs,
        'disablepodcidroverprovision': flags.AddDisablePodCIDROverprovisionFlag,
        'enableworkloadconfigaudit': flags.AddWorkloadConfigAuditFlag,
        'enableworkloadvulnscanning': flags.AddWorkloadVulnScanningFlag,
        'podautoscalingdirectmetricsoptin': (
            flags.AddPodAutoscalingDirectMetricsOptInFlag
        ),
        'enableGoogleCloudAccess': flags.AddEnableGoogleCloudAccess,
        'managedConfig': flags.AddManagedConfigFlag,
        'fleetProject': flags.AddFleetProjectFlag,
        'loggingvariant': flags.AddLoggingVariantFlag,
        'enableMultiNetworking': flags.AddEnableMultiNetworkingFlag,
        'enableSecurityPosture': flags.AddSecurityPostureFlag,
        'clusterNetworkPerformanceConfig': (
            flags.AddClusterNetworkPerformanceConfigFlags
        ),
        'enableKubeletReadonlyPort': flags.AddEnableKubeletReadonlyPortFlag,
        'autoprovisioningEnableKubeletReadonlyPort': (
            flags.AddAutoprovisioningEnableKubeletReadonlyPortFlag
        ),
        'enableK8sBetaApis': flags.AddEnableK8sBetaAPIs,
        'securityPosture': flags.AddSecurityPostureEnumFlag,
        'workloadVulnerabilityScanning': flags.AddWorkloadVulnScanningEnumFlag,
        'enableRuntimeVulnerabilityInsight': (
            flags.AddRuntimeVulnerabilityInsightFlag
        ),
        'enableDnsEndpoint': flags.AddEnableDNSEndpoint,
        'enableFqdnNetworkPolicy': flags.AddEnableFqdnNetworkPolicyFlag,
        'InTransitEncryption': flags.AddInTransitEncryptionFlag,
        'containerdConfig': lambda p: flags.AddContainerdConfigFlag(
            p, hidden=True
        ),
        'secretManagerConfig': lambda p: flags.AddSecretManagerEnableFlag(
            p, hidden=False
        ),
        'enableCiliumClusterwideNetworkPolicy': (
            flags.AddEnableCiliumClusterwideNetworkPolicyFlag
        ),
    },
    ALPHA: {
        'accelerator': lambda p: AddAcceleratorFlag(p, True, True, True, True),
        'additionalzones': _AddAdditionalZonesGroup,
        'addons': flags.AddAlphaAddonsFlags,
        'allowrouteoverlap': flags.AddAllowRouteOverlapFlag,
        'args': _Args,
        'authenticatorsecurity': flags.AddAuthenticatorSecurityGroupFlags,
        'autoprovisioning': AddAutoprovisioning,
        'autorepair': AddAutoRepair,
        'autoscalingprofiles': flags.AddAutoscalingProfilesFlag,
        'basicauth': flags.AddBasicAuthFlags,
        'cloudlogging': flags.AddEnableCloudLogging,
        'clusterversion': flags.AddClusterVersionFlag,
        'autoupgrade': AddEnableAutoUpgradeWithDefault,
        'binauthz': lambda p: flags.AddBinauthzFlags(
            p, release_track=base.ReleaseTrack.ALPHA
        ),
        'bootdiskkms': flags.AddBootDiskKmsKeyFlag,
        'cloudmonitoring': flags.AddEnableCloudMonitoring,
        'cloudrunalpha': flags.AddEnableCloudRunAlphaFlag,
        'cloudrunconfig': flags.AddCloudRunConfigFlag,
        'clusterautoscaling': functools.partial(
            flags.AddClusterAutoscalingFlags
        ),
        'clusterdns': lambda p: flags.AddClusterDNSFlags(
            p, release_track=base.ReleaseTrack.ALPHA
        ),
        'placementtype': flags.AddPlacementTypeFlag,
        'placementpolicy': flags.AddPlacementPolicyFlag,
        'confidentialnodes': flags.AddEnableConfidentialNodesFlag,
        'enableconfidentialstorage': flags.AddEnableConfidentialStorageFlag,
        'costmanagementconfig': flags.AddCostManagementConfigFlag,
        'databaseencryption': flags.AddDatabaseEncryptionFlag,
        'datapath': lambda p: flags.AddDatapathProviderFlag(p, hidden=True),
        'dataplanev2': flags.AddDataplaneV2Flag,
        'dataplanev2metrics': flags.AddDataplaneV2MetricsFlag,
        'dataplanev2obs': flags.AddDataplaneV2ObservabilityFlags,
        'disabledefaultsnat': AddDisableDefaultSnatFlagForClusterCreate,
        'disksize': flags.AddDiskSizeFlag,
        'disktype': flags.AddDiskTypeFlag,
        'gatewayapi': flags.AddGatewayFlags,
        'gcfs': flags.AddEnableGcfsFlag,
        'imagestreaming': flags.AddEnableImageStreamingFlag,
        'gkeoidc': flags.AddGkeOidcFlag,
        'gvnic': flags.AddEnableGvnicFlag,
        'hostmaintenanceinterval': flags.AddHostMaintenanceIntervalFlag,
        'identityservice': flags.AddIdentityServiceFlag,
        'ilbsubsetting': flags.AddILBSubsettingFlags,
        'imageflags': flags.AddImageFlagsCreate,
        'intranodevisibility': flags.AddEnableIntraNodeVisibilityFlag,
        'ipalias': flags.AddIpAliasCoreFlag,
        'ipalias_additional': flags.AddIPAliasRelatedFlags,
        'issueclientcert': flags.AddIssueClientCertificateFlag,
        'istioconfig': flags.AddIstioConfigFlag,
        'kubernetesalpha': flags.AddEnableKubernetesAlphaFlag,
        'labels': flags.AddLabelsFlag,
        'legacyauth': flags.AddEnableLegacyAuthorizationFlag,
        'linuxsysctl': flags.AddLinuxSysctlFlags,
        'localssds': flags.AddLocalSSDsAlphaFlags,
        'logging': flags.AddLoggingFlag,
        'loggingmonitoring': flags.AddEnableLoggingMonitoringSystemOnlyFlag,
        'machinetype': flags.AddMachineTypeFlag,
        'kubernetesobjectsexport': AddKubernetesObjectsExportFlag,
        'npname': lambda p: flags.AddInitialNodePoolNameArg(p, hidden=False),
        'nestedvirtualization': (
            lambda p: flags.AddEnableNestedVirtualizationFlag(p, hidden=True)
        ),
        'maxunavailable': lambda p: flags.AddMaxUnavailableUpgradeFlag(
            p, is_create=True
        ),
        'masterglobalaccess': flags.AddMasterGlobalAccessFlag,
        'maxnodes': flags.AddMaxNodesPerPool,
        'maxpodspernode': flags.AddMaxPodsPerNodeFlag,
        'maintenancewindow': flags.AddMaintenanceWindowGroup,
        'managedprometheus': lambda p: flags.AddManagedPrometheusFlags(
            p, for_create=True
        ),
        'masterauth': flags.AddMasterAuthorizedNetworksFlags,
        'mastersignals': AddMasterSignalsFlag,
        'meshcertificates': flags.AddMeshCertificatesFlags,
        'metadata': flags.AddMetadataFlags,
        'mincpu': flags.AddMinCpuPlatformFlag,
        'maintenanceinterval': flags.AddMaintenanceIntervalFlag,
        'monitoring': flags.AddMonitoringFlag,
        'networkpolicy': flags.AddNetworkPolicyFlags,
        'nodetaints': flags.AddNodeTaintsFlag,
        'nodeidentity': flags.AddClusterNodeIdentityFlags,
        'nodeversion': flags.AddNodeVersionFlag,
        'nodelabels': flags.AddNodeLabelsFlag,
        'notificationconfig': flags.AddNotificationConfigFlag,
        'num_nodes': flags.AddNumNodes,
        'performancemonitoringunit': (
            lambda p: flags.AddPerformanceMonitoringUnit(p, hidden=True)
        ),
        'podsecuritypolicy': flags.AddPodSecurityPolicyFlag,
        'preemptible': flags.AddPreemptibleFlag,
        'privatecluster': AddPrivateClusterDeprecated,
        'privateipv6': lambda p: flags.AddEnablePrivateIpv6AccessFlag(
            p, hidden=True
        ),
        'privateipv6type': lambda p: AddPrivateIPv6Flag('v1alpha1', p),
        'reservationaffinity': flags.AddReservationAffinityFlags,
        'resourceManagerTags': flags.AddResourceManagerTagsCreate,
        'autoprovisioningResourceManagerTags': (
            flags.AddAutoprovisioningResourceManagerTagsCreate
        ),
        'resourceusageexport': flags.AddResourceUsageExportFlags,
        'releasechannel': flags.AddReleaseChannelFlag,
        'shieldedinstance': flags.AddShieldedInstanceFlags,
        'shieldednodes': flags.AddEnableShieldedNodesFlags,
        'spot': flags.AddSpotFlag,
        'stackdriver': flags.AddEnableStackdriverKubernetesFlag,
        'securityprofile': flags.AddSecurityProfileForCreateFlags,
        'stacktype': flags.AddStackTypeFlag,
        'storagePools': flags.AddStoragePoolsFlag,
        'ipv6accesstype': flags.AddIpv6AccessTypeFlag,
        'surgeupgrade': lambda p: flags.AddSurgeUpgradeFlag(p, default=1),
        'systemconfig': lambda p: flags.AddSystemConfigFlag(p, hidden=False),
        'tags': flags.AddTagsCreate,
        'autoprovisioning_network_tags': (
            flags.AddAutoprovisioningNetworkTagsCreate
        ),
        'threads_per_core': flags.AddThreadsPerCore,
        'tpu': AddTpuWithServiceNetworking,
        'verticalpodautoscaling': (
            flags.AddVerticalPodAutoscalingFlagsExperimental
        ),
        'workloadAlts': flags.AddWorkloadAltsFlags,
        'workloadcertificates': flags.AddWorkloadCertificatesFlags,
        'workloadidentity': lambda p: flags.AddWorkloadIdentityFlags(p, True),
        'workloadmetadata': lambda p: flags.AddWorkloadMetadataFlag(
            p, use_mode=False
        ),
        'workloadmonitoringeap': flags.AddEnableWorkloadMonitoringEapFlag,
        'privateEndpointSubnetwork': flags.AddPrivateEndpointSubnetworkFlag,
        'crossConnectNetworks': flags.AddCrossConnectSubnetworksFlag,
        'enableserviceexternalips': flags.AddEnableServiceExternalIPs,
        'disablepodcidroverprovision': flags.AddDisablePodCIDROverprovisionFlag,
        'enableworkloadconfigaudit': flags.AddWorkloadConfigAuditFlag,
        'enableworkloadvulnscanning': flags.AddWorkloadVulnScanningFlag,
        'podautoscalingdirectmetricsoptin': (
            flags.AddPodAutoscalingDirectMetricsOptInFlag
        ),
        'enableGoogleCloudAccess': flags.AddEnableGoogleCloudAccess,
        'managedConfig': flags.AddManagedConfigFlag,
        'fleetProject': flags.AddFleetProjectFlag,
        'loggingvariant': flags.AddLoggingVariantFlag,
        'enableMultiNetworking': flags.AddEnableMultiNetworkingFlag,
        'enableSecurityPosture': flags.AddSecurityPostureFlag,
        'clusterNetworkPerformanceConfig': (
            flags.AddClusterNetworkPerformanceConfigFlags
        ),
        'enableKubeletReadonlyPort': flags.AddEnableKubeletReadonlyPortFlag,
        'autoprovisioningEnableKubeletReadonlyPort': (
            flags.AddAutoprovisioningEnableKubeletReadonlyPortFlag
        ),
        'enableK8sBetaApis': flags.AddEnableK8sBetaAPIs,
        'securityPosture': flags.AddSecurityPostureEnumFlag,
        'workloadVulnerabilityScanning': flags.AddWorkloadVulnScanningEnumFlag,
        'enableRuntimeVulnerabilityInsight': (
            flags.AddRuntimeVulnerabilityInsightFlag
        ),
        'enableDnsEndpoint': flags.AddEnableDNSEndpoint,
        'enableFqdnNetworkPolicy': flags.AddEnableFqdnNetworkPolicyFlag,
        'InTransitEncryption': flags.AddInTransitEncryptionFlag,
        'containerdConfig': lambda p: flags.AddContainerdConfigFlag(
            p, hidden=True
        ),
        'secretManagerConfig': lambda p: flags.AddSecretManagerEnableFlag(
            p, hidden=False
        ),
        'enableCiliumClusterwideNetworkPolicy': (
            flags.AddEnableCiliumClusterwideNetworkPolicyFlag
        ),
    },
}


def AddFlags(channel, parser, flag_defaults, allowlist=None):
  """Adds flags to the current parser.

  Args:
    channel: channel from which to add flags. eg. "GA" or "BETA"
    parser: parser to add current flags to
    flag_defaults: mapping to override the default value of flags
    allowlist: only add intersection of this list and channel flags
  """
  add_flag_for_channel = flags_to_add[channel]

  for flagname in add_flag_for_channel:
    if allowlist is None or (flagname in allowlist):
      if flagname in flag_defaults:
        add_flag_for_channel[flagname](parser, default=flag_defaults[flagname])
      else:
        add_flag_for_channel[flagname](parser)


base_flag_defaults = {
    'num_nodes': 3,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a cluster for running containers."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To create a cluster with the default configuration, run:

            $ {command} sample-cluster
          """,
  }

  autopilot = False
  default_flag_values = base_flag_defaults

  @staticmethod
  def Args(parser):
    AddFlags(GA, parser, base_flag_defaults)

  def ParseCreateOptions(self, args, location, project_id):
    get_default = lambda key: AttrValue(args, key, self.default_flag_values)
    return ParseCreateOptionsBase(args, self.autopilot, get_default, location,
                                  project_id)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully created cluster.

    Raises:
      util.Error, if creation failed.
    """
    if args.async_ and not args.IsSpecified('format'):
      args.format = util.OPERATIONS_FORMAT

    util.CheckKubectlInstalled()

    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args, is_autopilot=self.autopilot)

    cluster_ref = adapter.ParseCluster(args.name, location)
    options = self.ParseCreateOptions(args, location, cluster_ref.projectId)

    if options.private_cluster and not (
        options.enable_master_authorized_networks or
        options.master_authorized_networks):
      log.status.Print(
          'Note: `--private-cluster` makes the master inaccessible from '
          'cluster-external IP addresses, by design. To allow limited '
          'access to the master, see the `--master-authorized-networks` flags '
          'and our documentation on setting up private clusters: '
          'https://cloud.google.com/kubernetes-engine/docs/how-to/private-clusters'
      )

    if not options.enable_ip_alias:
      max_node_number = util.CalculateMaxNodeNumberByPodRange(
          options.cluster_ipv4_cidr)
      if max_node_number > 0:
        log.status.Print(
            'Note: Your Pod address range (`--cluster-ipv4-cidr`) can '
            'accommodate at most %d node(s).' % max_node_number)

    if options.enable_l4_ilb_subsetting:
      log.status.Print(
          'Note: Once enabled, L4 ILB Subsetting cannot be disabled.')

    if options.enable_pod_security_policy:
      log.status.Print(
          'Upcoming breaking change: Kubernetes has officially deprecated '
          'PodSecurityPolicy in version 1.21 and will be removed in 1.25 with '
          'no upgrade path available with this feature enabled. For additional '
          'details, please refer to '
          'https://cloud.google.com/kubernetes-engine/docs/how-to/pod-security-policies'
      )

    if options.enable_kubernetes_alpha:
      console_io.PromptContinue(
          message=constants.KUBERNETES_ALPHA_PROMPT,
          throw_if_unattended=True,
          cancel_on_no=True)

    if options.accelerators is not None:
      log.status.Print('Note: ' + constants.KUBERNETES_GPU_LIMITATION_MSG)

    # image streaming feature requires Container File System API to be enabled.
    # Checking whether the API has been enabled, and warning if not.
    if options.enable_image_streaming:
      util.CheckForContainerFileSystemApiEnablementWithPrompt(
          cluster_ref.projectId)

    operation = None
    try:
      operation_ref = adapter.CreateCluster(cluster_ref, options)
      if args.async_:
        return adapter.GetCluster(cluster_ref)

      operation = adapter.WaitForOperation(
          operation_ref,
          'Creating cluster {0} in {1}'.format(cluster_ref.clusterId,
                                               cluster_ref.zone),
          timeout_s=args.timeout)
      cluster = adapter.GetCluster(cluster_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.CreatedResource(cluster_ref)
    cluster_url = util.GenerateClusterUrl(cluster_ref)
    log.status.Print('To inspect the contents of your cluster, go to: ' +
                     cluster_url)
    if operation.detail:
      # Non-empty detail on a DONE create operation should be surfaced as
      # a warning to end user.
      log.warning(operation.detail)

    try:
      util.ClusterConfig.Persist(cluster, cluster_ref.projectId)
    except kconfig.MissingEnvVarError as error:
      log.warning(error)

    return [cluster]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a cluster for running containers."""

  @staticmethod
  def Args(parser):
    AddFlags(BETA, parser, base_flag_defaults)

  def ParseCreateOptions(self, args, location, project_id):
    get_default = lambda key: AttrValue(args, key, self.default_flag_values)
    ops = ParseCreateOptionsBase(args, self.autopilot, get_default, location,
                                 project_id)
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ephemeral_storage = None
    if args.IsKnownAndSpecified('ephemeral_storage'):
      ephemeral_storage = (
          []
          if args.ephemeral_storage is None
          else args.ephemeral_storage
      )
    ops.boot_disk_kms_key = get_default('boot_disk_kms_key')
    ops.min_cpu_platform = get_default('min_cpu_platform')
    ops.enable_pod_security_policy = get_default('enable_pod_security_policy')

    ops.allow_route_overlap = get_default('allow_route_overlap')
    ops.private_cluster = get_default('private_cluster')
    ops.istio_config = get_default('istio_config')
    ops.enable_vertical_pod_autoscaling = get_default(
        'enable_vertical_pod_autoscaling')
    ops.enable_experimental_vertical_pod_autoscaling = get_default(
        'enable_experimental_vertical_pod_autoscaling')
    ops.security_group = get_default('security_group')
    ops.max_surge_upgrade = get_default('max_surge_upgrade')
    ops.max_unavailable_upgrade = get_default('max_unavailable_upgrade')
    ops.autoscaling_profile = get_default('autoscaling_profile')
    ops.enable_tpu_service_networking = \
        get_default('enable_tpu_service_networking')
    ops.enable_logging_monitoring_system_only = \
        get_default('enable_logging_monitoring_system_only')
    ops.gvnic = get_default('enable_gvnic')
    ops.system_config_from_file = get_default('system_config_from_file')
    ops.datapath_provider = get_default('datapath_provider')
    ops.disable_default_snat = get_default('disable_default_snat')
    ops.enable_master_metrics = get_default('enable_master_metrics')
    ops.master_logs = get_default('master_logs')
    ops.enable_confidential_nodes = get_default('enable_confidential_nodes')
    ops.enable_nested_virtualization = get_default(
        'enable_nested_virtualization')
    ops.kubernetes_objects_changes_target = \
        getattr(args, 'kubernetes_objects_changes_target', None)
    ops.kubernetes_objects_snapshots_target = \
        getattr(args, 'kubernetes_objects_snapshots_target', None)
    ops.enable_gcfs = get_default('enable_gcfs')
    ops.enable_image_streaming = get_default('enable_image_streaming')
    ops.enable_workload_certificates = getattr(args,
                                               'enable_workload_certificates',
                                               None)
    ops.enable_alts = getattr(args, 'enable_alts', None)
    ops.ephemeral_storage = ephemeral_storage
    ops.enable_workload_monitoring_eap = \
      get_default('enable_workload_monitoring_eap')
    ops.private_endpoint_subnetwork = \
        get_default('private_endpoint_subnetwork')
    ops.cross_connect_subnetworks = \
        get_default('cross_connect_subnetworks')
    ops.enable_service_externalips = get_default('enable_service_externalips')
    ops.enable_managed_prometheus = get_default('enable_managed_prometheus')
    ops.spot = get_default('spot')
    ops.maintenance_interval = get_default('maintenance_interval')
    ops.disable_pod_cidr_overprovision = get_default(
        'disable_pod_cidr_overprovision')
    ops.stack_type = get_default('stack_type')
    ops.ipv6_access_type = get_default('ipv6_access_type')
    ops.enable_workload_config_audit = get_default(
        'enable_workload_config_audit')
    ops.pod_autoscaling_direct_metrics_opt_in = get_default(
        'pod_autoscaling_direct_metrics_opt_in')
    ops.enable_workload_vulnerability_scanning = get_default(
        'enable_workload_vulnerability_scanning')
    ops.enable_cost_allocation = get_default('enable_cost_allocation')
    ops.managed_config = get_default('managed_config')
    ops.fleet_project = get_default('fleet_project')
    ops.enable_fleet = get_default('enable_fleet')
    ops.enable_multi_networking = get_default('enable_multi_networking')
    ops.enable_security_posture = get_default('enable_security_posture')
    ops.security_posture = get_default('security_posture')
    ops.workload_vulnerability_scanning = get_default(
        'workload_vulnerability_scanning'
    )
    ops.enable_runtime_vulnerability_insight = get_default(
        'enable_runtime_vulnerability_insight')
    ops.enable_dns_endpoint = get_default('enable_dns_endpoint')
    ops.host_maintenance_interval = get_default('host_maintenance_interval')
    ops.containerd_config_from_file = get_default(
        'containerd_config_from_file',
    )
    ops.enable_confidential_storage = get_default('enable_confidential_storage')
    ops.storage_pools = get_default('storage_pools')
    ops.enable_secret_manager = get_default('enable_secret_manager')
    ops.enable_cilium_clusterwide_networkpolicy = get_default(
        'enable_cilium_clusterwide_networkpolicy'
    )
    return ops


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a cluster for running containers."""

  @staticmethod
  def Args(parser):
    AddFlags(ALPHA, parser, base_flag_defaults)

  def ParseCreateOptions(self, args, location, project_id):
    get_default = lambda key: AttrValue(args, key, self.default_flag_values)
    ops = ParseCreateOptionsBase(args, self.autopilot, get_default, location,
                                 project_id)
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ephemeral_storage = None
    if args.IsKnownAndSpecified('ephemeral_storage'):
      ephemeral_storage = (
          []
          if args.ephemeral_storage is None
          else args.ephemeral_storage
      )
    ops.boot_disk_kms_key = get_default('boot_disk_kms_key')
    ops.autoscaling_profile = get_default('autoscaling_profile')
    ops.local_ssd_volume_configs = get_default('local_ssd_volumes')
    ops.ephemeral_storage = ephemeral_storage
    ops.enable_pod_security_policy = get_default('enable_pod_security_policy')
    ops.allow_route_overlap = get_default('allow_route_overlap')
    ops.private_cluster = get_default('private_cluster')
    ops.enable_private_nodes = get_default('enable_private_nodes')
    ops.enable_private_endpoint = get_default('enable_private_endpoint')
    ops.master_ipv4_cidr = get_default('master_ipv4_cidr')
    ops.enable_tpu_service_networking = \
        get_default('enable_tpu_service_networking')
    ops.istio_config = get_default('istio_config')
    ops.security_group = get_default('security_group')
    ops.enable_vertical_pod_autoscaling = \
        get_default('enable_vertical_pod_autoscaling')
    ops.enable_experimental_vertical_pod_autoscaling = get_default(
        'enable_experimental_vertical_pod_autoscaling')
    ops.security_profile = get_default('security_profile')
    ops.security_profile_runtime_rules = \
        get_default('security_profile_runtime_rules')
    ops.node_pool_name = get_default('node_pool_name')
    ops.enable_network_egress_metering = \
        get_default('enable_network_egress_metering')
    ops.enable_resource_consumption_metering = \
        get_default('enable_resource_consumption_metering')
    ops.enable_private_ipv6_access = get_default('enable_private_ipv6_access')
    ops.max_surge_upgrade = get_default('max_surge_upgrade')
    ops.max_unavailable_upgrade = get_default('max_unavailable_upgrade')
    ops.linux_sysctls = get_default('linux_sysctls')
    ops.disable_default_snat = get_default('disable_default_snat')
    ops.system_config_from_file = get_default('system_config_from_file')
    ops.enable_cost_allocation = get_default('enable_cost_allocation')
    ops.enable_logging_monitoring_system_only = \
        get_default('enable_logging_monitoring_system_only')
    ops.datapath_provider = get_default('datapath_provider')
    ops.gvnic = get_default('enable_gvnic')
    ops.enable_master_metrics = get_default('enable_master_metrics')
    ops.master_logs = get_default('master_logs')
    ops.enable_confidential_nodes = get_default('enable_confidential_nodes')
    ops.enable_nested_virtualization = get_default(
        'enable_nested_virtualization')
    ops.kubernetes_objects_changes_target = \
        getattr(args, 'kubernetes_objects_changes_target', None)
    ops.kubernetes_objects_snapshots_target = \
        getattr(args, 'kubernetes_objects_snapshots_target', None)
    ops.enable_gcfs = get_default('enable_gcfs')
    ops.enable_image_streaming = get_default('enable_image_streaming')
    ops.enable_workload_certificates = getattr(args,
                                               'enable_workload_certificates',
                                               None)
    ops.enable_alts = getattr(args, 'enable_alts', None)
    ops.enable_workload_monitoring_eap = \
      get_default('enable_workload_monitoring_eap')
    ops.private_endpoint_subnetwork = \
        get_default('private_endpoint_subnetwork')
    ops.cross_connect_subnetworks = \
        get_default('cross_connect_subnetworks')
    ops.enable_service_externalips = get_default('enable_service_externalips')
    ops.enable_managed_prometheus = get_default('enable_managed_prometheus')
    ops.spot = get_default('spot')
    ops.maintenance_interval = get_default('maintenance_interval')
    ops.disable_pod_cidr_overprovision = get_default(
        'disable_pod_cidr_overprovision')
    ops.stack_type = get_default('stack_type')
    ops.ipv6_access_type = get_default('ipv6_access_type')
    ops.enable_workload_config_audit = get_default(
        'enable_workload_config_audit')
    ops.performance_monitoring_unit = get_default('performance_monitoring_unit')
    ops.pod_autoscaling_direct_metrics_opt_in = get_default(
        'pod_autoscaling_direct_metrics_opt_in')
    ops.enable_workload_vulnerability_scanning = get_default(
        'enable_workload_vulnerability_scanning')
    ops.managed_config = get_default('managed_config')
    ops.fleet_project = get_default('fleet_project')
    ops.enable_fleet = get_default('enable_fleet')
    ops.enable_multi_networking = get_default('enable_multi_networking')
    ops.enable_security_posture = get_default('enable_security_posture')
    ops.security_posture = get_default('security_posture')
    ops.workload_vulnerability_scanning = get_default(
        'workload_vulnerability_scanning'
    )
    ops.enable_runtime_vulnerability_insight = get_default(
        'enable_runtime_vulnerability_insight'
    )
    ops.enable_dns_endpoint = get_default('enable_dns_endpoint')
    ops.host_maintenance_interval = get_default('host_maintenance_interval')
    ops.contianerd_config_from_file = get_default('contianerd_config_from_file')
    ops.enable_confidential_storage = get_default('enable_confidential_storage')
    ops.storage_pools = get_default('storage_pools')
    ops.enable_secret_manager = get_default('enable_secret_manager')
    ops.enable_cilium_clusterwide_networkpolicy = get_default(
        'enable_cilium_clusterwide_networkpolicy'
    )
    return ops
