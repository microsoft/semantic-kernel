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
"""Api client adapter containers commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import time

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.container import constants as gke_constants
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources as cloud_resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import times
import six
from six.moves import range  # pylint: disable=redefined-builtin
import six.moves.http_client

WRONG_ZONE_ERROR_MSG = """\
{error}
Could not find [{name}] in [{wrong_zone}].
Did you mean [{name}] in [{zone}]?"""

NO_SUCH_CLUSTER_ERROR_MSG = """\
{error}
No cluster named '{name}' in {project}."""

NO_SUCH_NODE_POOL_ERROR_MSG = """\
No node pool named '{name}' in {cluster}."""

NO_NODE_POOL_SELECTED_ERROR_MSG = """\
Please specify one of the following node pools:
"""

MISMATCH_AUTHORIZED_NETWORKS_ERROR_MSG = """\
Cannot use --master-authorized-networks \
if --enable-master-authorized-networks is not \
specified."""

NO_AUTOPROVISIONING_MSG = """\
Node autoprovisioning is currently in beta.
"""

NO_AUTOPROVISIONING_LIMITS_ERROR_MSG = """\
Must specify both --max-cpu and --max-memory to enable autoprovisioning.
"""

LIMITS_WITHOUT_AUTOPROVISIONING_MSG = """\
Must enable node autoprovisioning to specify resource limits for autoscaling.
"""

DEFAULTS_WITHOUT_AUTOPROVISIONING_MSG = """\
Must enable node autoprovisioning to specify defaults for node autoprovisioning.
"""

BOTH_AUTOPROVISIONING_UPGRADE_SETTINGS_ERROR_MSG = """\
Must specify both 'maxSurgeUpgrade' and 'maxUnavailableUpgrade' in \
'upgradeSettings' in --autoprovisioning-config-file, or both \
'--autoprovisioning-max-surge-upgrade' and '--autoprovisioning-max-unavailable-upgrade' \
from cmd argument to set a surge upgrade strategy.
"""

BOTH_AUTOPROVISIONING_MANAGEMENT_SETTINGS_ERROR_MSG = """\
Must specify both 'autoUpgrade' and 'autoRepair' in 'management' in \
--autoprovisioning-config-file to set management settings.
"""

BOTH_AUTOPROVISIONING_SHIELDED_INSTANCE_SETTINGS_ERROR_MSG = """\
Must specify both 'enableSecureBoot' and 'enableIntegrityMonitoring' \
in 'shieldedInstanceConfig' in --autoprovisioning-config-file to set \
management settings.
"""

BOTH_SHIELDED_INSTANCE_SETTINGS_ERROR_MSG = """\
Must specify both or none of --shielded-secure-boot and \
--shielded-integrity-monitoring.
"""

LIMITS_WITHOUT_AUTOPROVISIONING_FLAG_MSG = """\
Must specify --enable-autoprovisioning to specify resource limits for autoscaling.
"""

MISMATCH_ACCELERATOR_TYPE_LIMITS_ERROR_MSG = """\
Maximum and minimum accelerator limits must be set on the same accelerator type.
"""

NO_SUCH_LABEL_ERROR_MSG = """\
No label named '{name}' found on cluster '{cluster}'."""

NO_LABELS_ON_CLUSTER_ERROR_MSG = """\
Cluster '{cluster}' has no labels to remove."""

CREATE_SUBNETWORK_INVALID_KEY_ERROR_MSG = """\
Invalid key '{key}' for --create-subnetwork (must be one of 'name', 'range').
"""

CREATE_SUBNETWORK_WITH_SUBNETWORK_ERROR_MSG = """\
Cannot specify both --subnetwork and --create-subnetwork at the same time.
"""

CREATE_POD_RANGE_INVALID_KEY_ERROR_MSG = """
Invalid key '{key}' for --create-pod-ipv4-range (must be one of 'name', 'range').
"""

NODE_TAINT_INCORRECT_FORMAT_ERROR_MSG = """\
Invalid value [{key}={value}] for argument --node-taints. Node taint is of format key=value:effect
"""

NODE_TAINT_INCORRECT_EFFECT_ERROR_MSG = """\
Invalid taint effect [{effect}] for argument --node-taints. Valid effect values are NoSchedule, PreferNoSchedule, NoExecute'
"""

LOCAL_SSD_INCORRECT_FORMAT_ERROR_MSG = """\
Invalid local SSD format [{err_format}] for argument --local-ssd-volumes. Valid formats are fs, block
"""

UNKNOWN_WORKLOAD_METADATA_ERROR_MSG = """\
Invalid option '{option}' for '--workload-metadata' (must be one of 'gce_metadata', 'gke_metadata').
"""

ALLOW_ROUTE_OVERLAP_WITHOUT_EXPLICIT_NETWORK_MODE = """\
Flag --allow-route-overlap must be used with either --enable-ip-alias or --no-enable-ip-alias.
"""

ALLOW_ROUTE_OVERLAP_WITHOUT_CLUSTER_CIDR_ERROR_MSG = """\
Flag --cluster-ipv4-cidr must be fully specified (e.g. `10.96.0.0/14`, but not `/14`) with --allow-route-overlap.
"""

ALLOW_ROUTE_OVERLAP_WITHOUT_SERVICES_CIDR_ERROR_MSG = """\
Flag --services-ipv4-cidr must be fully specified (e.g. `10.96.0.0/14`, but not `/14`) with --allow-route-overlap and --enable-ip-alias.
"""

PREREQUISITE_OPTION_ERROR_MSG = """\
Cannot specify --{opt} without --{prerequisite}.
"""

CLOUD_LOGGING_OR_MONITORING_DISABLED_ERROR_MSG = """\
Flag --enable-stackdriver-kubernetes requires Cloud Logging and Cloud Monitoring enabled with --enable-cloud-logging and --enable-cloud-monitoring.
"""

CLOUDRUN_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG = """\
The CloudRun-on-GKE addon (--addons=CloudRun) requires System Logging and Monitoring to be enabled via the --monitoring=SYSTEM and --logging=SYSTEM flags.
"""

CLOUDRUN_INGRESS_KUBERNETES_DISABLED_ERROR_MSG = """\
The CloudRun-on-GKE addon (--addons=CloudRun) requires HTTP Load Balancing to be enabled via the --addons=HttpLoadBalancing flag.
"""

CONFIGCONNECTOR_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG = """\
The ConfigConnector-on-GKE addon (--addons=ConfigConnector) requires System Logging and Monitoring to be enabled via the --monitoring=SYSTEM and --logging=SYSTEM flags.
"""

CONFIGCONNECTOR_WORKLOAD_IDENTITY_DISABLED_ERROR_MSG = """\
The ConfigConnector-on-GKE addon (--addons=ConfigConnector) requires workload identity to be enabled via the --workload-pool=WORKLOAD_POOL flag.
"""

CLOUDBUILD_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG = """\
Cloud Build for Anthos (--addons=CloudBuild) requires System Logging and Monitoring to be enabled via the --monitoring=SYSTEM and --logging=SYSTEM flags.
"""

DEFAULT_MAX_PODS_PER_NODE_WITHOUT_IP_ALIAS_ERROR_MSG = """\
Cannot use --default-max-pods-per-node without --enable-ip-alias.
"""

MAX_PODS_PER_NODE_WITHOUT_IP_ALIAS_ERROR_MSG = """\
Cannot use --max-pods-per-node without --enable-ip-alias.
"""

NOTHING_TO_UPDATE_ERROR_MSG = """\
Nothing to update.
"""

ENABLE_PRIVATE_NODES_WITH_PRIVATE_CLUSTER_ERROR_MSG = """\
Cannot specify both --[no-]enable-private-nodes and --[no-]private-cluster at the same time.
"""

ENABLE_NETWORK_EGRESS_METERING_ERROR_MSG = """\
Cannot use --[no-]enable-network-egress-metering without --resource-usage-bigquery-dataset.
"""

ENABLE_RESOURCE_CONSUMPTION_METERING_ERROR_MSG = """\
Cannot use --[no-]enable-resource-consumption-metering without --resource-usage-bigquery-dataset.
"""

DISABLE_DEFAULT_SNAT_WITHOUT_IP_ALIAS_ERROR_MSG = """\
Cannot use --disable-default-snat without --enable-ip-alias.
"""

DISABLE_DEFAULT_SNAT_WITHOUT_PRIVATE_NODES_ERROR_MSG = """\
Cannot use --disable-default-snat without --enable-private-nodes.
"""

RESERVATION_AFFINITY_SPECIFIC_WITHOUT_RESERVATION_NAME_ERROR_MSG = """\
Must specify --reservation for --reservation-affinity=specific.
"""

RESERVATION_AFFINITY_NON_SPECIFIC_WITH_RESERVATION_NAME_ERROR_MSG = """\
Cannot specify --reservation for --reservation-affinity={affinity}.
"""

DATAPATH_PROVIDER_ILL_SPECIFIED_ERROR_MSG = """\
Invalid provider '{provider}' for argument --datapath-provider. Valid providers are legacy, advanced.
"""

DPV2_OBS_ERROR_MSG = """\
Invalid '{mode}' for argument --dataplane-v2-observability-mode. Valid modes are DISABLED, INTERNAL_VPC_LB, EXTERNAL_LB.
"""

SANDBOX_TYPE_NOT_PROVIDED = """\
Must specify sandbox type.
"""

SANDBOX_TYPE_NOT_SUPPORTED = """\
Provided sandbox type '{type}' not supported.
"""
TPU_SERVING_MODE_ERROR = """\
Cannot specify --tpu-ipv4-cidr with --enable-tpu-service-networking."""

GPU_SHARING_STRATEGY_ERROR_MSG = """\
Invalid gpu sharing strategy [{gpu-sharing-strategy}] for argument --accelerator. Valid values are time-sharing, mps'
"""

GPU_DRIVER_VERSION_ERROR_MSG = """\
Invalid gpu driver version [{gpu-driver-version}] for argument --accelerator. Valid values are default, latest, or disabled'
"""

MAINTENANCE_INTERVAL_TYPE_NOT_SUPPORTED = """\
Provided maintenance interval type '{type}' not supported.
"""

MANGED_CONFIG_TYPE_NOT_SUPPORTED = """\
Invalid managed config type '{type}' for argument --managed-config. Valid values are: autofleet, disabled'
"""

SECURITY_POSTURE_MODE_NOT_SUPPORTED = """\
Invalid mode '{mode}' for '--security-posture' (must be one of 'disabled', 'standard').
"""

WORKLOAD_VULNERABILITY_SCANNING_MODE_NOT_SUPPORTED = """\
Invalid mode '{mode}' for '--workload-vulnerability-scanning' (must be one of 'disabled', 'standard', 'enterprise').
"""

HOST_MAINTENANCE_INTERVAL_TYPE_NOT_SUPPORTED = """\
Provided host maintenance interval type '{type}' is not supported.
"""

NODECONFIGDEFAULTS_READONLY_PORT_NOT_SUPPORTED = """\
nodePoolDefaults.nodeKubeletConfig is not supported on GKE Autopilot clusters.
"""

MAX_NODES_PER_POOL = 1000

MAX_AUTHORIZED_NETWORKS_CIDRS_PRIVATE = 100
MAX_AUTHORIZED_NETWORKS_CIDRS_PUBLIC = 50

INGRESS = 'HttpLoadBalancing'
HPA = 'HorizontalPodAutoscaling'
DASHBOARD = 'KubernetesDashboard'
CLOUDBUILD = 'CloudBuild'
BACKUPRESTORE = 'BackupRestore'
CONFIGCONNECTOR = 'ConfigConnector'
GCEPDCSIDRIVER = 'GcePersistentDiskCsiDriver'
GCPFILESTORECSIDRIVER = 'GcpFilestoreCsiDriver'
GCSFUSECSIDRIVER = 'GcsFuseCsiDriver'
STATEFULHA = 'StatefulHA'
PARALLELSTORECSIDRIVER = 'ParallelstoreCsiDriver'
ISTIO = 'Istio'
NETWORK_POLICY = 'NetworkPolicy'
NODELOCALDNS = 'NodeLocalDNS'
APPLICATIONMANAGER = 'ApplicationManager'
RESOURCE_LIMITS = 'resourceLimits'
SERVICE_ACCOUNT = 'serviceAccount'
MIN_CPU_PLATFORM = 'minCpuPlatform'
UPGRADE_SETTINGS = 'upgradeSettings'
MAX_SURGE_UPGRADE = 'maxSurgeUpgrade'
MAX_UNAVAILABLE_UPGRADE = 'maxUnavailableUpgrade'
NODE_MANAGEMENT = 'management'
ENABLE_AUTO_UPGRADE = 'autoUpgrade'
ENABLE_AUTO_REPAIR = 'autoRepair'
SCOPES = 'scopes'
AUTOPROVISIONING_LOCATIONS = 'autoprovisioningLocations'
BOOT_DISK_KMS_KEY = 'bootDiskKmsKey'
DISK_SIZE_GB = 'diskSizeGb'
DISK_TYPE = 'diskType'
IMAGE_TYPE = 'imageType'
SHIELDED_INSTANCE_CONFIG = 'shieldedInstanceConfig'
ENABLE_SECURE_BOOT = 'enableSecureBoot'
ENABLE_INTEGRITY_MONITORING = 'enableIntegrityMonitoring'
DEFAULT_ADDONS = [INGRESS, HPA]
CLOUDRUN_ADDONS = ['CloudRun', 'KubeRun']
VISIBLE_CLOUDRUN_ADDONS = ['CloudRun']
ADDONS_OPTIONS = DEFAULT_ADDONS + [
    DASHBOARD,
    NETWORK_POLICY,
    NODELOCALDNS,
    CONFIGCONNECTOR,
    GCEPDCSIDRIVER,
    GCPFILESTORECSIDRIVER,
    BACKUPRESTORE,
    GCSFUSECSIDRIVER,
    STATEFULHA,
    PARALLELSTORECSIDRIVER,
]
BETA_ADDONS_OPTIONS = ADDONS_OPTIONS + [
    ISTIO,
    APPLICATIONMANAGER,
]
ALPHA_ADDONS_OPTIONS = BETA_ADDONS_OPTIONS + [CLOUDBUILD]

NONE = 'NONE'
SYSTEM = 'SYSTEM'
WORKLOAD = 'WORKLOAD'
# TODO(b/187793166): Remove APISERVER when deprecating the legacy API.
APISERVER = 'APISERVER'
API_SERVER = 'API_SERVER'
SCHEDULER = 'SCHEDULER'
CONTROLLER_MANAGER = 'CONTROLLER_MANAGER'
ADDON_MANAGER = 'ADDON_MANAGER'
STORAGE = 'STORAGE'
HPA_COMPONENT = 'HPA'
POD = 'POD'
DAEMONSET = 'DAEMONSET'
DEPLOYMENT = 'DEPLOYMENT'
STATEFULSET = 'STATEFULSET'
CADVISOR = 'CADVISOR'
KUBELET = 'KUBELET'
LOGGING_OPTIONS = [
    NONE,
    SYSTEM,
    WORKLOAD,
    API_SERVER,
    SCHEDULER,
    CONTROLLER_MANAGER,
    ADDON_MANAGER,
]
MONITORING_OPTIONS = [
    NONE,
    SYSTEM,
    WORKLOAD,
    API_SERVER,
    SCHEDULER,
    CONTROLLER_MANAGER,
    STORAGE,
    HPA_COMPONENT,
    POD,
    DAEMONSET,
    DEPLOYMENT,
    STATEFULSET,
    CADVISOR,
    KUBELET,
]
PRIMARY_LOGS_OPTIONS = [
    APISERVER,
    SCHEDULER,
    CONTROLLER_MANAGER,
    ADDON_MANAGER,
]
PLACEMENT_OPTIONS = ['UNSPECIFIED', 'COMPACT']
LOCATION_POLICY_OPTIONS = ['BALANCED', 'ANY']


def CheckResponse(response):
  """Wrap http_wrapper.CheckResponse to skip retry on 503."""
  if response.status_code == 503:
    raise apitools_exceptions.HttpError.FromResponse(response)
  return http_wrapper.CheckResponse(response)


def APIVersionFromReleaseTrack(release_track):
  if release_track == base.ReleaseTrack.GA:
    return 'v1'
  elif release_track == base.ReleaseTrack.BETA:
    return 'v1beta1'
  elif release_track == base.ReleaseTrack.ALPHA:
    return 'v1alpha1'
  else:
    raise ValueError('Unsupported Release Track: {}'.format(release_track))


def NewAPIAdapter(api_version):
  if api_version == 'v1alpha1':
    return NewV1Alpha1APIAdapter()
  elif api_version == 'v1beta1':
    return NewV1Beta1APIAdapter()
  else:
    return NewV1APIAdapter()


def NewV1APIAdapter():
  return InitAPIAdapter('v1', V1Adapter)


def NewV1Beta1APIAdapter():
  return InitAPIAdapter('v1beta1', V1Beta1Adapter)


def NewV1Alpha1APIAdapter():
  return InitAPIAdapter('v1alpha1', V1Alpha1Adapter)


def InitAPIAdapter(api_version, adapter):
  """Initialize an api adapter.

  Args:
    api_version: the api version we want.
    adapter: the api adapter constructor.

  Returns:
    APIAdapter object.
  """

  api_client = core_apis.GetClientInstance('container', api_version)
  api_client.check_response_func = CheckResponse
  messages = core_apis.GetMessagesModule('container', api_version)

  registry = cloud_resources.REGISTRY.Clone()
  registry.RegisterApiByName('container', api_version)
  registry.RegisterApiByName('compute', 'v1')

  return adapter(registry, api_client, messages)


_SERVICE_ACCOUNT_SCOPES = ('https://www.googleapis.com/auth/cloud-platform',
                           'https://www.googleapis.com/auth/userinfo.email')


def NodeIdentityOptionsToNodeConfig(options, node_config):
  """Convert node identity options into node config.

  If scopes are specified with the `--scopes` flag, respect them.
  If no scopes are presented, 'gke-default' will be passed here indicating that
  we should use the default set:
  - If no service account is specified, default set is GKE_DEFAULT_SCOPES which
    is handled by ExpandScopeURIs:
    - https://www.googleapis.com/auth/devstorage.read_only,
    - https://www.googleapis.com/auth/logging.write',
    - https://www.googleapis.com/auth/monitoring,
    - https://www.googleapis.com/auth/servicecontrol,
    - https://www.googleapis.com/auth/service.management.readonly,
    - https://www.googleapis.com/auth/trace.append,
  - If a service account is specified, default set is _SERVICE_ACCOUNT_SCOPES:
    - https://www.googleapis.com/auth/cloud-platform
    - https://www.googleapis.com/auth/userinfo.email
  Args:
    options: the CreateCluster or CreateNodePool options.
    node_config: the messages.node_config object to be populated.
  """
  if options.service_account:
    node_config.serviceAccount = options.service_account
    replaced_scopes = []
    for scope in options.scopes:
      if scope == 'gke-default':
        replaced_scopes.extend(_SERVICE_ACCOUNT_SCOPES)
      else:
        replaced_scopes.append(scope)
    options.scopes = replaced_scopes

  options.scopes = ExpandScopeURIs(options.scopes)
  node_config.oauthScopes = sorted(set(options.scopes))


def ExpandScopeURIs(scopes):
  """Expand scope names to the fully qualified uris.

  Args:
    scopes: [str,] list of scope names. Can be short names ('compute-rw') or
      full urls ('https://www.googleapis.com/auth/compute'). See SCOPES in
      api_lib/container/constants.py & api_lib/compute/constants.py.

  Returns:
    list of str, full urls for recognized scopes.
  """

  scope_uris = []
  for scope in scopes:
    # Expand any scope aliases (like 'storage-rw') that the user provided
    # to their official URL representation.
    expanded = constants.SCOPES.get(scope, [scope])
    scope_uris.extend(expanded)
  return scope_uris


class CreateClusterOptions(object):
  """Options to pass to CreateCluster."""

  def __init__(
      self,
      node_machine_type=None,
      node_source_image=None,
      node_disk_size_gb=None,
      scopes=None,
      num_nodes=None,
      additional_zones=None,
      node_locations=None,
      user=None,
      password=None,
      cluster_version=None,
      node_version=None,
      network=None,
      cluster_ipv4_cidr=None,
      enable_cloud_logging=None,
      enable_cloud_monitoring=None,
      enable_stackdriver_kubernetes=None,
      enable_logging_monitoring_system_only=None,
      enable_workload_monitoring_eap=None,
      subnetwork=None,
      addons=None,
      istio_config=None,
      cloud_run_config=None,
      local_ssd_count=None,
      local_ssd_volume_configs=None,
      local_nvme_ssd_block=None,
      ephemeral_storage=None,
      ephemeral_storage_local_ssd=None,
      boot_disk_kms_key=None,
      node_pool_name=None,
      tags=None,
      autoprovisioning_network_tags=None,
      node_labels=None,
      node_taints=None,
      enable_autoscaling=None,
      min_nodes=None,
      max_nodes=None,
      total_min_nodes=None,
      total_max_nodes=None,
      location_policy=None,
      image_type=None,
      image=None,
      image_project=None,
      image_family=None,
      issue_client_certificate=None,
      max_nodes_per_pool=None,
      enable_kubernetes_alpha=None,
      enable_cloud_run_alpha=None,
      preemptible=None,
      spot=None,
      placement_type=None,
      placement_policy=None,
      enable_queued_provisioning=None,
      enable_autorepair=None,
      enable_autoupgrade=None,
      service_account=None,
      enable_master_authorized_networks=None,
      master_authorized_networks=None,
      enable_legacy_authorization=None,
      labels=None,
      disk_type=None,
      enable_network_policy=None,
      enable_l4_ilb_subsetting=None,
      services_ipv4_cidr=None,
      enable_ip_alias=None,
      create_subnetwork=None,
      cluster_secondary_range_name=None,
      services_secondary_range_name=None,
      accelerators=None,
      enable_binauthz=None,
      binauthz_evaluation_mode=None,
      binauthz_policy_bindings=None,
      min_cpu_platform=None,
      workload_metadata=None,
      workload_metadata_from_node=None,
      maintenance_window=None,
      enable_pod_security_policy=None,
      allow_route_overlap=None,
      private_cluster=None,
      enable_private_nodes=None,
      enable_private_endpoint=None,
      master_ipv4_cidr=None,
      tpu_ipv4_cidr=None,
      enable_tpu=None,
      enable_tpu_service_networking=None,
      default_max_pods_per_node=None,
      max_pods_per_node=None,
      resource_usage_bigquery_dataset=None,
      security_group=None,
      enable_private_ipv6_access=None,
      enable_intra_node_visibility=None,
      enable_vertical_pod_autoscaling=None,
      enable_experimental_vertical_pod_autoscaling=None,
      security_profile=None,
      security_profile_runtime_rules=None,
      autoscaling_profile=None,
      database_encryption_key=None,
      metadata=None,
      enable_network_egress_metering=None,
      enable_resource_consumption_metering=None,
      workload_pool=None,
      identity_provider=None,
      enable_workload_certificates=None,
      enable_mesh_certificates=None,
      enable_alts=None,
      enable_gke_oidc=None,
      enable_identity_service=None,
      enable_shielded_nodes=None,
      linux_sysctls=None,
      disable_default_snat=None,
      dataplane_v2=None,
      enable_dataplane_v2_metrics=None,
      disable_dataplane_v2_metrics=None,
      enable_dataplane_v2_flow_observability=None,
      disable_dataplane_v2_flow_observability=None,
      dataplane_v2_observability_mode=None,
      shielded_secure_boot=None,
      shielded_integrity_monitoring=None,
      system_config_from_file=None,
      maintenance_window_start=None,
      maintenance_window_end=None,
      maintenance_window_recurrence=None,
      enable_cost_allocation=None,
      max_surge_upgrade=None,
      max_unavailable_upgrade=None,
      enable_autoprovisioning=None,
      autoprovisioning_config_file=None,
      autoprovisioning_service_account=None,
      autoprovisioning_scopes=None,
      autoprovisioning_locations=None,
      min_cpu=None,
      max_cpu=None,
      min_memory=None,
      max_memory=None,
      min_accelerator=None,
      max_accelerator=None,
      autoprovisioning_image_type=None,
      autoprovisioning_max_surge_upgrade=None,
      autoprovisioning_max_unavailable_upgrade=None,
      enable_autoprovisioning_autoupgrade=None,
      enable_autoprovisioning_autorepair=None,
      reservation_affinity=None,
      reservation=None,
      autoprovisioning_min_cpu_platform=None,
      enable_master_global_access=None,
      gvnic=None,
      enable_master_metrics=None,
      master_logs=None,
      release_channel=None,
      notification_config=None,
      autopilot=None,
      private_ipv6_google_access_type=None,
      enable_confidential_nodes=None,
      enable_confidential_storage=None,
      cluster_dns=None,
      cluster_dns_scope=None,
      cluster_dns_domain=None,
      additive_vpc_scope_dns_domain=None,
      disable_additive_vpc_scope=None,
      kubernetes_objects_changes_target=None,
      kubernetes_objects_snapshots_target=None,
      enable_gcfs=None,
      enable_image_streaming=None,
      private_endpoint_subnetwork=None,
      cross_connect_subnetworks=None,
      enable_service_externalips=None,
      threads_per_core=None,
      logging=None,
      monitoring=None,
      enable_managed_prometheus=None,
      maintenance_interval=None,
      disable_pod_cidr_overprovision=None,
      stack_type=None,
      ipv6_access_type=None,
      enable_workload_config_audit=None,
      pod_autoscaling_direct_metrics_opt_in=None,
      enable_workload_vulnerability_scanning=None,
      enable_autoprovisioning_surge_upgrade=None,
      enable_autoprovisioning_blue_green_upgrade=None,
      autoprovisioning_standard_rollout_policy=None,
      autoprovisioning_node_pool_soak_duration=None,
      enable_google_cloud_access=None,
      managed_config=None,
      fleet_project=None,
      enable_fleet=None,
      gateway_api=None,
      logging_variant=None,
      enable_multi_networking=None,
      enable_security_posture=None,
      enable_nested_virtualization=None,
      performance_monitoring_unit=None,
      network_performance_config=None,
      enable_insecure_kubelet_readonly_port=None,
      autoprovisioning_enable_insecure_kubelet_readonly_port=None,
      enable_k8s_beta_apis=None,
      security_posture=None,
      workload_vulnerability_scanning=None,
      enable_runtime_vulnerability_insight=None,
      enable_dns_endpoint=None,
      workload_policies=None,
      enable_fqdn_network_policy=None,
      host_maintenance_interval=None,
      in_transit_encryption=None,
      containerd_config_from_file=None,
      resource_manager_tags=None,
      autoprovisioning_resource_manager_tags=None,
      enable_secret_manager=None,
      enable_cilium_clusterwide_network_policy=None,
      storage_pools=None,
  ):
    self.node_machine_type = node_machine_type
    self.node_source_image = node_source_image
    self.node_disk_size_gb = node_disk_size_gb
    self.scopes = scopes
    self.num_nodes = num_nodes
    self.additional_zones = additional_zones
    self.node_locations = node_locations
    self.user = user
    self.password = password
    self.cluster_version = cluster_version
    self.node_version = node_version
    self.network = network
    self.cluster_ipv4_cidr = cluster_ipv4_cidr
    self.enable_cloud_logging = enable_cloud_logging
    self.enable_cloud_monitoring = enable_cloud_monitoring
    self.enable_stackdriver_kubernetes = enable_stackdriver_kubernetes
    self.enable_logging_monitoring_system_only = enable_logging_monitoring_system_only
    self.enable_workload_monitoring_eap = enable_workload_monitoring_eap,
    self.subnetwork = subnetwork
    self.addons = addons
    self.istio_config = istio_config
    self.cloud_run_config = cloud_run_config
    self.local_ssd_count = local_ssd_count
    self.local_ssd_volume_configs = local_ssd_volume_configs
    self.ephemeral_storage = ephemeral_storage
    self.ephemeral_storage_local_ssd = ephemeral_storage_local_ssd
    self.local_nvme_ssd_block = local_nvme_ssd_block
    self.boot_disk_kms_key = boot_disk_kms_key
    self.node_pool_name = node_pool_name
    self.tags = tags
    self.autoprovisioning_network_tags = autoprovisioning_network_tags
    self.node_labels = node_labels
    self.node_taints = node_taints
    self.enable_autoscaling = enable_autoscaling
    self.min_nodes = min_nodes
    self.max_nodes = max_nodes
    self.total_min_nodes = total_min_nodes
    self.total_max_nodes = total_max_nodes
    self.location_policy = location_policy
    self.image_type = image_type
    self.image = image
    self.image_project = image_project
    self.image_family = image_family
    self.max_nodes_per_pool = max_nodes_per_pool
    self.enable_kubernetes_alpha = enable_kubernetes_alpha
    self.enable_cloud_run_alpha = enable_cloud_run_alpha
    self.preemptible = preemptible
    self.spot = spot
    self.placement_type = placement_type
    self.placement_policy = placement_policy
    self.enable_queued_provisioning = enable_queued_provisioning
    self.enable_autorepair = enable_autorepair
    self.enable_autoupgrade = enable_autoupgrade
    self.service_account = service_account
    self.enable_master_authorized_networks = enable_master_authorized_networks
    self.master_authorized_networks = master_authorized_networks
    self.enable_legacy_authorization = enable_legacy_authorization
    self.enable_network_policy = enable_network_policy
    self.enable_l4_ilb_subsetting = enable_l4_ilb_subsetting
    self.labels = labels
    self.disk_type = disk_type
    self.services_ipv4_cidr = services_ipv4_cidr
    self.enable_ip_alias = enable_ip_alias
    self.create_subnetwork = create_subnetwork
    self.cluster_secondary_range_name = cluster_secondary_range_name
    self.services_secondary_range_name = services_secondary_range_name
    self.accelerators = accelerators
    self.enable_binauthz = enable_binauthz
    self.binauthz_evaluation_mode = binauthz_evaluation_mode
    self.binauthz_policy_bindings = binauthz_policy_bindings
    self.min_cpu_platform = min_cpu_platform
    self.workload_metadata = workload_metadata
    self.workload_metadata_from_node = workload_metadata_from_node
    self.maintenance_window = maintenance_window
    self.enable_pod_security_policy = enable_pod_security_policy
    self.allow_route_overlap = allow_route_overlap
    self.private_cluster = private_cluster
    self.enable_private_nodes = enable_private_nodes
    self.enable_private_endpoint = enable_private_endpoint
    self.master_ipv4_cidr = master_ipv4_cidr
    self.tpu_ipv4_cidr = tpu_ipv4_cidr
    self.enable_tpu_service_networking = enable_tpu_service_networking
    self.enable_tpu = enable_tpu
    self.issue_client_certificate = issue_client_certificate
    self.default_max_pods_per_node = default_max_pods_per_node
    self.max_pods_per_node = max_pods_per_node
    self.resource_usage_bigquery_dataset = resource_usage_bigquery_dataset
    self.security_group = security_group
    self.enable_private_ipv6_access = enable_private_ipv6_access
    self.enable_intra_node_visibility = enable_intra_node_visibility
    self.enable_vertical_pod_autoscaling = enable_vertical_pod_autoscaling
    self.enable_experimental_vertical_pod_autoscaling = enable_experimental_vertical_pod_autoscaling
    self.security_profile = security_profile
    self.security_profile_runtime_rules = security_profile_runtime_rules
    self.autoscaling_profile = autoscaling_profile
    self.database_encryption_key = database_encryption_key
    self.metadata = metadata
    self.enable_network_egress_metering = enable_network_egress_metering
    self.enable_resource_consumption_metering = enable_resource_consumption_metering
    self.workload_pool = workload_pool
    self.identity_provider = identity_provider
    self.enable_workload_certificates = enable_workload_certificates
    self.enable_mesh_certificates = enable_mesh_certificates
    self.enable_alts = enable_alts
    self.enable_gke_oidc = enable_gke_oidc
    self.enable_identity_service = enable_identity_service
    self.enable_shielded_nodes = enable_shielded_nodes
    self.linux_sysctls = linux_sysctls
    self.disable_default_snat = disable_default_snat
    self.dataplane_v2 = dataplane_v2
    self.enable_dataplane_v2_metrics = enable_dataplane_v2_metrics
    self.disable_dataplane_v2_metrics = disable_dataplane_v2_metrics
    self.enable_dataplane_v2_flow_observability = (
        enable_dataplane_v2_flow_observability
    )
    self.disable_dataplane_v2_flow_observability = (
        disable_dataplane_v2_flow_observability
    )
    self.dataplane_v2_observability_mode = dataplane_v2_observability_mode
    self.shielded_secure_boot = shielded_secure_boot
    self.shielded_integrity_monitoring = shielded_integrity_monitoring
    self.system_config_from_file = system_config_from_file
    self.maintenance_window_start = maintenance_window_start
    self.maintenance_window_end = maintenance_window_end
    self.maintenance_window_recurrence = maintenance_window_recurrence
    self.enable_cost_allocation = enable_cost_allocation
    self.max_surge_upgrade = max_surge_upgrade
    self.max_unavailable_upgrade = max_unavailable_upgrade
    self.enable_autoprovisioning = enable_autoprovisioning
    self.autoprovisioning_config_file = autoprovisioning_config_file
    self.autoprovisioning_service_account = autoprovisioning_service_account
    self.autoprovisioning_scopes = autoprovisioning_scopes
    self.autoprovisioning_locations = autoprovisioning_locations
    self.min_cpu = min_cpu
    self.max_cpu = max_cpu
    self.min_memory = min_memory
    self.max_memory = max_memory
    self.min_accelerator = min_accelerator
    self.max_accelerator = max_accelerator
    self.autoprovisioning_image_type = autoprovisioning_image_type
    self.autoprovisioning_max_surge_upgrade = autoprovisioning_max_surge_upgrade
    self.autoprovisioning_max_unavailable_upgrade = autoprovisioning_max_unavailable_upgrade
    self.enable_autoprovisioning_autoupgrade = enable_autoprovisioning_autoupgrade
    self.enable_autoprovisioning_autorepair = enable_autoprovisioning_autorepair
    self.reservation_affinity = reservation_affinity
    self.reservation = reservation
    self.autoprovisioning_min_cpu_platform = autoprovisioning_min_cpu_platform
    self.enable_master_global_access = enable_master_global_access
    self.gvnic = gvnic
    self.enable_master_metrics = enable_master_metrics
    self.master_logs = master_logs
    self.release_channel = release_channel
    self.notification_config = notification_config
    self.autopilot = autopilot
    self.private_ipv6_google_access_type = private_ipv6_google_access_type
    self.enable_confidential_nodes = enable_confidential_nodes
    self.enable_confidential_storage = enable_confidential_storage
    self.storage_pools = storage_pools
    self.cluster_dns = cluster_dns
    self.cluster_dns_scope = cluster_dns_scope
    self.cluster_dns_domain = cluster_dns_domain
    self.additive_vpc_scope_dns_domain = additive_vpc_scope_dns_domain
    self.disable_additive_vpc_scope = disable_additive_vpc_scope
    self.kubernetes_objects_changes_target = kubernetes_objects_changes_target
    self.kubernetes_objects_snapshots_target = kubernetes_objects_snapshots_target
    self.enable_gcfs = enable_gcfs
    self.enable_image_streaming = enable_image_streaming
    self.private_endpoint_subnetwork = private_endpoint_subnetwork
    self.cross_connect_subnetworks = cross_connect_subnetworks
    self.enable_service_externalips = enable_service_externalips
    self.threads_per_core = threads_per_core
    self.enable_nested_virtualization = enable_nested_virtualization
    self.performance_monitoring_unit = performance_monitoring_unit
    self.logging = logging
    self.monitoring = monitoring
    self.enable_managed_prometheus = enable_managed_prometheus
    self.maintenance_interval = maintenance_interval
    self.disable_pod_cidr_overprovision = disable_pod_cidr_overprovision
    self.stack_type = stack_type
    self.ipv6_access_type = ipv6_access_type
    self.enable_workload_config_audit = enable_workload_config_audit
    self.pod_autoscaling_direct_metrics_opt_in = pod_autoscaling_direct_metrics_opt_in
    self.enable_workload_vulnerability_scanning = enable_workload_vulnerability_scanning
    self.enable_autoprovisioning_surge_upgrade = enable_autoprovisioning_surge_upgrade
    self.enable_autoprovisioning_blue_green_upgrade = enable_autoprovisioning_blue_green_upgrade
    self.autoprovisioning_standard_rollout_policy = autoprovisioning_standard_rollout_policy
    self.autoprovisioning_node_pool_soak_duration = autoprovisioning_node_pool_soak_duration
    self.enable_google_cloud_access = enable_google_cloud_access
    self.managed_config = managed_config
    self.fleet_project = fleet_project
    self.enable_fleet = enable_fleet
    self.gateway_api = gateway_api
    self.logging_variant = logging_variant
    self.enable_multi_networking = enable_multi_networking
    self.enable_security_posture = enable_security_posture
    self.network_performance_config = network_performance_config
    self.enable_insecure_kubelet_readonly_port = (
        enable_insecure_kubelet_readonly_port
    )
    self.autoprovisioning_enable_insecure_kubelet_readonly_port = (
        autoprovisioning_enable_insecure_kubelet_readonly_port
    )

    self.enable_k8s_beta_apis = enable_k8s_beta_apis
    self.security_posture = security_posture
    self.workload_vulnerability_scanning = workload_vulnerability_scanning
    self.enable_runtime_vulnerability_insight = (
        enable_runtime_vulnerability_insight
    )
    self.enable_dns_endpoint = enable_dns_endpoint
    self.workload_policies = workload_policies
    self.enable_fqdn_network_policy = enable_fqdn_network_policy
    self.host_maintenance_interval = host_maintenance_interval
    self.in_transit_encryption = in_transit_encryption
    self.containerd_config_from_file = containerd_config_from_file
    self.resource_manager_tags = resource_manager_tags
    self.autoprovisioning_resource_manager_tags = (
        autoprovisioning_resource_manager_tags
    )
    self.enable_secret_manager = enable_secret_manager
    self.enable_cilium_clusterwide_network_policy = (
        enable_cilium_clusterwide_network_policy
    )


class UpdateClusterOptions(object):
  """Options to pass to UpdateCluster."""

  def __init__(
      self,
      version=None,
      update_master=None,
      update_nodes=None,
      node_pool=None,
      monitoring_service=None,
      logging_service=None,
      enable_stackdriver_kubernetes=None,
      enable_logging_monitoring_system_only=None,
      enable_workload_monitoring_eap=None,
      master_logs=None,
      no_master_logs=None,
      enable_master_metrics=None,
      logging=None,
      monitoring=None,
      disable_addons=None,
      istio_config=None,
      cloud_run_config=None,
      cluster_dns=None,
      cluster_dns_scope=None,
      cluster_dns_domain=None,
      disable_additive_vpc_scope=None,
      additive_vpc_scope_dns_domain=None,
      enable_autoscaling=None,
      min_nodes=None,
      max_nodes=None,
      total_min_nodes=None,
      total_max_nodes=None,
      location_policy=None,
      image_type=None,
      image=None,
      image_project=None,
      locations=None,
      enable_master_authorized_networks=None,
      master_authorized_networks=None,
      enable_pod_security_policy=None,
      enable_vertical_pod_autoscaling=None,
      enable_experimental_vertical_pod_autoscaling=None,
      enable_intra_node_visibility=None,
      enable_l4_ilb_subsetting=None,
      security_profile=None,
      security_profile_runtime_rules=None,
      autoscaling_profile=None,
      enable_peering_route_sharing=None,
      workload_pool=None,
      identity_provider=None,
      disable_workload_identity=None,
      enable_workload_certificates=None,
      enable_mesh_certificates=None,
      enable_alts=None,
      enable_gke_oidc=None,
      enable_identity_service=None,
      enable_shielded_nodes=None,
      disable_default_snat=None,
      resource_usage_bigquery_dataset=None,
      enable_network_egress_metering=None,
      enable_resource_consumption_metering=None,
      database_encryption_key=None,
      disable_database_encryption=None,
      enable_cost_allocation=None,
      enable_autoprovisioning=None,
      autoprovisioning_config_file=None,
      autoprovisioning_service_account=None,
      autoprovisioning_scopes=None,
      autoprovisioning_locations=None,
      min_cpu=None,
      max_cpu=None,
      min_memory=None,
      max_memory=None,
      min_accelerator=None,
      max_accelerator=None,
      release_channel=None,
      autoprovisioning_image_type=None,
      autoprovisioning_max_surge_upgrade=None,
      autoprovisioning_max_unavailable_upgrade=None,
      enable_autoprovisioning_autoupgrade=None,
      enable_autoprovisioning_autorepair=None,
      autoprovisioning_min_cpu_platform=None,
      enable_tpu=None,
      tpu_ipv4_cidr=None,
      enable_master_global_access=None,
      enable_tpu_service_networking=None,
      notification_config=None,
      private_ipv6_google_access_type=None,
      kubernetes_objects_changes_target=None,
      kubernetes_objects_snapshots_target=None,
      disable_autopilot=None,
      add_cross_connect_subnetworks=None,
      remove_cross_connect_subnetworks=None,
      clear_cross_connect_subnetworks=None,
      enable_service_externalips=None,
      security_group=None,
      enable_gcfs=None,
      autoprovisioning_network_tags=None,
      enable_image_streaming=None,
      enable_managed_prometheus=None,
      disable_managed_prometheus=None,
      maintenance_interval=None,
      dataplane_v2=None,
      enable_dataplane_v2_metrics=None,
      disable_dataplane_v2_metrics=None,
      enable_dataplane_v2_flow_observability=None,
      disable_dataplane_v2_flow_observability=None,
      dataplane_v2_observability_mode=None,
      enable_workload_config_audit=None,
      pod_autoscaling_direct_metrics_opt_in=None,
      enable_workload_vulnerability_scanning=None,
      enable_autoprovisioning_surge_upgrade=None,
      enable_autoprovisioning_blue_green_upgrade=None,
      autoprovisioning_standard_rollout_policy=None,
      autoprovisioning_node_pool_soak_duration=None,
      enable_private_endpoint=None,
      enable_google_cloud_access=None,
      stack_type=None,
      gateway_api=None,
      logging_variant=None,
      additional_pod_ipv4_ranges=None,
      removed_additional_pod_ipv4_ranges=None,
      fleet_project=None,
      enable_fleet=None,
      clear_fleet_project=None,
      enable_security_posture=None,
      network_performance_config=None,
      enable_k8s_beta_apis=None,
      security_posture=None,
      workload_vulnerability_scanning=None,
      enable_runtime_vulnerability_insight=None,
      workload_policies=None,
      remove_workload_policies=None,
      enable_fqdn_network_policy=None,
      host_maintenance_interval=None,
      in_transit_encryption=None,
      enable_multi_networking=None,
      containerd_config_from_file=None,
      autoprovisioning_resource_manager_tags=None,
      convert_to_autopilot=None,
      convert_to_standard=None,
      enable_secret_manager=None,
      enable_cilium_clusterwide_network_policy=None,
      enable_insecure_kubelet_readonly_port=None,
      autoprovisioning_enable_insecure_kubelet_readonly_port=None,
  ):
    self.version = version
    self.update_master = bool(update_master)
    self.update_nodes = bool(update_nodes)
    self.node_pool = node_pool
    self.monitoring_service = monitoring_service
    self.logging_service = logging_service
    self.enable_stackdriver_kubernetes = enable_stackdriver_kubernetes
    self.enable_logging_monitoring_system_only = enable_logging_monitoring_system_only
    self.enable_workload_monitoring_eap = enable_workload_monitoring_eap
    self.no_master_logs = no_master_logs
    self.master_logs = master_logs
    self.enable_master_metrics = enable_master_metrics
    self.logging = logging
    self.monitoring = monitoring
    self.disable_addons = disable_addons
    self.istio_config = istio_config
    self.cloud_run_config = cloud_run_config
    self.cluster_dns = cluster_dns
    self.cluster_dns_scope = cluster_dns_scope
    self.cluster_dns_domain = cluster_dns_domain
    self.disable_additive_vpc_scope = disable_additive_vpc_scope
    self.additive_vpc_scope_dns_domain = additive_vpc_scope_dns_domain
    self.enable_autoscaling = enable_autoscaling
    self.min_nodes = min_nodes
    self.max_nodes = max_nodes
    self.total_min_nodes = total_min_nodes
    self.total_max_nodes = total_max_nodes
    self.location_policy = location_policy
    self.image_type = image_type
    self.image = image
    self.image_project = image_project
    self.locations = locations
    self.enable_master_authorized_networks = enable_master_authorized_networks
    self.master_authorized_networks = master_authorized_networks
    self.enable_pod_security_policy = enable_pod_security_policy
    self.enable_vertical_pod_autoscaling = enable_vertical_pod_autoscaling
    self.enable_experimental_vertical_pod_autoscaling = enable_experimental_vertical_pod_autoscaling
    self.security_profile = security_profile
    self.security_profile_runtime_rules = security_profile_runtime_rules
    self.autoscaling_profile = autoscaling_profile
    self.enable_intra_node_visibility = enable_intra_node_visibility
    self.enable_l4_ilb_subsetting = enable_l4_ilb_subsetting
    self.enable_peering_route_sharing = enable_peering_route_sharing
    self.workload_pool = workload_pool
    self.identity_provider = identity_provider
    self.disable_workload_identity = disable_workload_identity
    self.enable_workload_certificates = enable_workload_certificates
    self.enable_mesh_certificates = enable_mesh_certificates
    self.enable_alts = enable_alts
    self.enable_gke_oidc = enable_gke_oidc
    self.enable_identity_service = enable_identity_service
    self.enable_shielded_nodes = enable_shielded_nodes
    self.disable_default_snat = disable_default_snat
    self.resource_usage_bigquery_dataset = resource_usage_bigquery_dataset
    self.enable_network_egress_metering = enable_network_egress_metering
    self.enable_resource_consumption_metering = (
        enable_resource_consumption_metering)
    self.database_encryption_key = database_encryption_key
    self.disable_database_encryption = disable_database_encryption
    self.enable_cost_allocation = enable_cost_allocation
    self.enable_autoprovisioning = enable_autoprovisioning
    self.autoprovisioning_config_file = autoprovisioning_config_file
    self.autoprovisioning_service_account = autoprovisioning_service_account
    self.autoprovisioning_scopes = autoprovisioning_scopes
    self.autoprovisioning_locations = autoprovisioning_locations
    self.min_cpu = min_cpu
    self.max_cpu = max_cpu
    self.min_memory = min_memory
    self.max_memory = max_memory
    self.min_accelerator = min_accelerator
    self.max_accelerator = max_accelerator
    self.release_channel = release_channel
    self.autoprovisioning_image_type = autoprovisioning_image_type
    self.autoprovisioning_max_surge_upgrade = autoprovisioning_max_surge_upgrade
    self.autoprovisioning_max_unavailable_upgrade = autoprovisioning_max_unavailable_upgrade
    self.enable_autoprovisioning_autoupgrade = enable_autoprovisioning_autoupgrade
    self.enable_autoprovisioning_autorepair = enable_autoprovisioning_autorepair
    self.autoprovisioning_min_cpu_platform = autoprovisioning_min_cpu_platform
    self.enable_tpu = enable_tpu
    self.tpu_ipv4_cidr = tpu_ipv4_cidr
    self.enable_tpu_service_networking = enable_tpu_service_networking
    self.enable_master_global_access = enable_master_global_access
    self.notification_config = notification_config
    self.private_ipv6_google_access_type = private_ipv6_google_access_type
    self.kubernetes_objects_changes_target = kubernetes_objects_changes_target
    self.kubernetes_objects_snapshots_target = kubernetes_objects_snapshots_target
    self.disable_autopilot = disable_autopilot
    self.add_cross_connect_subnetworks = add_cross_connect_subnetworks
    self.remove_cross_connect_subnetworks = remove_cross_connect_subnetworks
    self.clear_cross_connect_subnetworks = clear_cross_connect_subnetworks
    self.enable_service_externalips = enable_service_externalips
    self.security_group = security_group
    self.enable_gcfs = enable_gcfs
    self.autoprovisioning_network_tags = autoprovisioning_network_tags
    self.enable_image_streaming = enable_image_streaming
    self.enable_managed_prometheus = enable_managed_prometheus
    self.disable_managed_prometheus = disable_managed_prometheus
    self.maintenance_interval = maintenance_interval
    self.dataplane_v2 = dataplane_v2
    self.enable_dataplane_v2_metrics = enable_dataplane_v2_metrics
    self.disable_dataplane_v2_metrics = disable_dataplane_v2_metrics
    self.enable_dataplane_v2_flow_observability = (
        enable_dataplane_v2_flow_observability
    )
    self.disable_dataplane_v2_flow_observability = (
        disable_dataplane_v2_flow_observability
    )
    self.dataplane_v2_observability_mode = dataplane_v2_observability_mode
    self.enable_workload_config_audit = enable_workload_config_audit
    self.pod_autoscaling_direct_metrics_opt_in = pod_autoscaling_direct_metrics_opt_in
    self.enable_workload_vulnerability_scanning = enable_workload_vulnerability_scanning
    self.enable_autoprovisioning_surge_upgrade = enable_autoprovisioning_surge_upgrade
    self.enable_autoprovisioning_blue_green_upgrade = enable_autoprovisioning_blue_green_upgrade
    self.autoprovisioning_standard_rollout_policy = autoprovisioning_standard_rollout_policy
    self.autoprovisioning_node_pool_soak_duration = autoprovisioning_node_pool_soak_duration
    self.enable_private_endpoint = enable_private_endpoint
    self.enable_google_cloud_access = enable_google_cloud_access
    self.stack_type = stack_type
    self.gateway_api = gateway_api
    self.logging_variant = logging_variant
    self.additional_pod_ipv4_ranges = additional_pod_ipv4_ranges
    self.removed_additional_pod_ipv4_ranges = removed_additional_pod_ipv4_ranges
    self.fleet_project = fleet_project
    self.enable_fleet = enable_fleet
    self.clear_fleet_project = clear_fleet_project
    self.enable_security_posture = enable_security_posture
    self.network_performance_config = network_performance_config
    self.enable_k8s_beta_apis = enable_k8s_beta_apis
    self.security_posture = security_posture
    self.workload_vulnerability_scanning = workload_vulnerability_scanning
    self.enable_runtime_vulnerability_insight = (
        enable_runtime_vulnerability_insight
    )
    self.workload_policies = workload_policies
    self.remove_workload_policies = remove_workload_policies
    self.enable_fqdn_network_policy = enable_fqdn_network_policy
    self.host_maintenance_interval = host_maintenance_interval
    self.in_transit_encryption = in_transit_encryption
    self.enable_multi_networking = enable_multi_networking
    self.containerd_config_from_file = containerd_config_from_file
    self.autoprovisioning_resource_manager_tags = (
        autoprovisioning_resource_manager_tags
    )
    self.convert_to_autopilot = convert_to_autopilot
    self.convert_to_standard = convert_to_standard
    self.enable_secret_manager = enable_secret_manager
    self.enable_cilium_clusterwide_network_policy = (
        enable_cilium_clusterwide_network_policy
    )
    self.enable_insecure_kubelet_readonly_port = (
        enable_insecure_kubelet_readonly_port
    )
    self.autoprovisioning_enable_insecure_kubelet_readonly_port = (
        autoprovisioning_enable_insecure_kubelet_readonly_port
    )


class SetMasterAuthOptions(object):
  """Options to pass to SetMasterAuth."""

  SET_PASSWORD = 'SetPassword'
  GENERATE_PASSWORD = 'GeneratePassword'
  SET_USERNAME = 'SetUsername'

  def __init__(self, action=None, username=None, password=None):
    self.action = action
    self.username = username
    self.password = password


class SetNetworkPolicyOptions(object):

  def __init__(self, enabled):
    self.enabled = enabled


class CreateNodePoolOptions(object):
  """Options to pass to CreateNodePool."""

  def __init__(
      self,
      machine_type=None,
      disk_size_gb=None,
      scopes=None,
      node_version=None,
      num_nodes=None,
      local_ssd_count=None,
      local_ssd_volume_configs=None,
      ephemeral_storage=None,
      local_nvme_ssd_block=None,
      ephemeral_storage_local_ssd=None,
      boot_disk_kms_key=None,
      tags=None,
      node_labels=None,
      labels=None,
      node_taints=None,
      enable_autoscaling=None,
      max_nodes=None,
      min_nodes=None,
      total_max_nodes=None,
      total_min_nodes=None,
      location_policy=None,
      enable_autoprovisioning=None,
      image_type=None,
      image=None,
      image_project=None,
      image_family=None,
      preemptible=None,
      spot=None,
      placement_type=None,
      placement_policy=None,
      tpu_topology=None,
      enable_queued_provisioning=None,
      enable_autorepair=None,
      enable_autoupgrade=None,
      service_account=None,
      disk_type=None,
      accelerators=None,
      min_cpu_platform=None,
      workload_metadata=None,
      workload_metadata_from_node=None,
      max_pods_per_node=None,
      sandbox=None,
      metadata=None,
      linux_sysctls=None,
      max_surge_upgrade=None,
      max_unavailable_upgrade=None,
      node_locations=None,
      shielded_secure_boot=None,
      shielded_integrity_monitoring=None,
      system_config_from_file=None,
      reservation_affinity=None,
      reservation=None,
      node_group=None,
      enable_gcfs=None,
      enable_image_streaming=None,
      gvnic=None,
      pod_ipv4_range=None,
      create_pod_ipv4_range=None,
      enable_private_nodes=None,
      threads_per_core=None,
      enable_blue_green_upgrade=None,
      enable_surge_upgrade=None,
      node_pool_soak_duration=None,
      standard_rollout_policy=None,
      autoscaled_rollout_policy=None,
      maintenance_interval=None,
      network_performance_config=None,
      enable_confidential_nodes=None,
      enable_confidential_storage=None,
      disable_pod_cidr_overprovision=None,
      enable_fast_socket=None,
      logging_variant=None,
      windows_os_version=None,
      enable_best_effort_provision=None,
      min_provision_nodes=None,
      additional_node_network=None,
      additional_pod_network=None,
      enable_nested_virtualization=None,
      performance_monitoring_unit=None,
      sole_tenant_node_affinity_file=None,
      host_maintenance_interval=None,
      enable_insecure_kubelet_readonly_port=None,
      resource_manager_tags=None,
      containerd_config_from_file=None,
      secondary_boot_disks=None,
      storage_pools=None,
  ):
    self.machine_type = machine_type
    self.disk_size_gb = disk_size_gb
    self.scopes = scopes
    self.node_version = node_version
    self.num_nodes = num_nodes
    self.local_ssd_count = local_ssd_count
    self.local_ssd_volume_configs = local_ssd_volume_configs
    self.ephemeral_storage = ephemeral_storage
    self.ephemeral_storage_local_ssd = ephemeral_storage_local_ssd
    self.local_nvme_ssd_block = local_nvme_ssd_block
    self.boot_disk_kms_key = boot_disk_kms_key
    self.tags = tags
    self.labels = labels
    self.node_labels = node_labels
    self.node_taints = node_taints
    self.enable_autoscaling = enable_autoscaling
    self.max_nodes = max_nodes
    self.min_nodes = min_nodes
    self.total_max_nodes = total_max_nodes
    self.total_min_nodes = total_min_nodes
    self.enable_autoprovisioning = enable_autoprovisioning
    self.image_type = image_type
    self.location_policy = location_policy
    self.image = image
    self.image_project = image_project
    self.image_family = image_family
    self.preemptible = preemptible
    self.spot = spot
    self.placement_type = placement_type
    self.placement_policy = placement_policy
    self.tpu_topology = tpu_topology
    self.enable_queued_provisioning = enable_queued_provisioning
    self.enable_autorepair = enable_autorepair
    self.enable_autoupgrade = enable_autoupgrade
    self.service_account = service_account
    self.disk_type = disk_type
    self.accelerators = accelerators
    self.min_cpu_platform = min_cpu_platform
    self.workload_metadata = workload_metadata
    self.workload_metadata_from_node = workload_metadata_from_node
    self.max_pods_per_node = max_pods_per_node
    self.sandbox = sandbox
    self.metadata = metadata
    self.linux_sysctls = linux_sysctls
    self.max_surge_upgrade = max_surge_upgrade
    self.max_unavailable_upgrade = max_unavailable_upgrade
    self.node_locations = node_locations
    self.shielded_secure_boot = shielded_secure_boot
    self.shielded_integrity_monitoring = shielded_integrity_monitoring
    self.system_config_from_file = system_config_from_file
    self.reservation_affinity = reservation_affinity
    self.reservation = reservation
    self.node_group = node_group
    self.enable_gcfs = enable_gcfs
    self.enable_image_streaming = enable_image_streaming
    self.gvnic = gvnic
    self.pod_ipv4_range = pod_ipv4_range
    self.create_pod_ipv4_range = create_pod_ipv4_range
    self.enable_private_nodes = enable_private_nodes
    self.threads_per_core = threads_per_core
    self.enable_nested_virtualization = enable_nested_virtualization
    self.performance_monitoring_unit = performance_monitoring_unit
    self.enable_blue_green_upgrade = enable_blue_green_upgrade
    self.enable_surge_upgrade = enable_surge_upgrade
    self.node_pool_soak_duration = node_pool_soak_duration
    self.standard_rollout_policy = standard_rollout_policy
    self.autoscaled_rollout_policy = autoscaled_rollout_policy
    self.maintenance_interval = maintenance_interval
    self.network_performance_config = network_performance_config
    self.enable_confidential_nodes = enable_confidential_nodes
    self.enable_confidential_storage = enable_confidential_storage
    self.disable_pod_cidr_overprovision = disable_pod_cidr_overprovision
    self.enable_fast_socket = enable_fast_socket
    self.logging_variant = logging_variant
    self.windows_os_version = windows_os_version
    self.enable_best_effort_provision = enable_best_effort_provision
    self.min_provision_nodes = min_provision_nodes
    self.additional_node_network = additional_node_network
    self.additional_pod_network = additional_pod_network
    self.sole_tenant_node_affinity_file = sole_tenant_node_affinity_file
    self.host_maintenance_interval = host_maintenance_interval
    self.enable_insecure_kubelet_readonly_port = (
        enable_insecure_kubelet_readonly_port)
    self.resource_manager_tags = resource_manager_tags
    self.containerd_config_from_file = containerd_config_from_file
    self.secondary_boot_disks = secondary_boot_disks
    self.storage_pools = storage_pools


class UpdateNodePoolOptions(object):
  """Options to pass to UpdateNodePool."""

  def __init__(self,
               enable_autorepair=None,
               enable_autoupgrade=None,
               enable_autoscaling=None,
               max_nodes=None,
               min_nodes=None,
               total_max_nodes=None,
               total_min_nodes=None,
               location_policy=None,
               enable_autoprovisioning=None,
               workload_metadata=None,
               workload_metadata_from_node=None,
               node_locations=None,
               max_surge_upgrade=None,
               max_unavailable_upgrade=None,
               system_config_from_file=None,
               node_labels=None,
               labels=None,
               node_taints=None,
               tags=None,
               enable_private_nodes=None,
               enable_gcfs=None,
               gvnic=None,
               enable_image_streaming=None,
               enable_blue_green_upgrade=None,
               enable_surge_upgrade=None,
               node_pool_soak_duration=None,
               standard_rollout_policy=None,
               autoscaled_rollout_policy=None,
               network_performance_config=None,
               enable_confidential_nodes=None,
               enable_fast_socket=None,
               logging_variant=None,
               accelerators=None,
               windows_os_version=None,
               enable_insecure_kubelet_readonly_port=None,
               resource_manager_tags=None,
               containerd_config_from_file=None,
               secondary_boot_disks=None,
               machine_type=None,
               disk_type=None,
               disk_size_gb=None,
               enable_queued_provisioning=None):
    self.enable_autorepair = enable_autorepair
    self.enable_autoupgrade = enable_autoupgrade
    self.enable_autoscaling = enable_autoscaling
    self.max_nodes = max_nodes
    self.min_nodes = min_nodes
    self.accelerators = accelerators
    self.total_max_nodes = total_max_nodes
    self.total_min_nodes = total_min_nodes
    self.location_policy = location_policy
    self.enable_autoprovisioning = enable_autoprovisioning
    self.workload_metadata = workload_metadata
    self.workload_metadata_from_node = workload_metadata_from_node
    self.node_locations = node_locations
    self.max_surge_upgrade = max_surge_upgrade
    self.max_unavailable_upgrade = max_unavailable_upgrade
    self.system_config_from_file = system_config_from_file
    self.labels = labels
    self.node_labels = node_labels
    self.node_taints = node_taints
    self.tags = tags
    self.enable_private_nodes = enable_private_nodes
    self.enable_gcfs = enable_gcfs
    self.gvnic = gvnic
    self.enable_image_streaming = enable_image_streaming
    self.enable_blue_green_upgrade = enable_blue_green_upgrade
    self.enable_surge_upgrade = enable_surge_upgrade
    self.node_pool_soak_duration = node_pool_soak_duration
    self.standard_rollout_policy = standard_rollout_policy
    self.autoscaled_rollout_policy = autoscaled_rollout_policy
    self.network_performance_config = network_performance_config
    self.enable_confidential_nodes = enable_confidential_nodes
    self.enable_fast_socket = enable_fast_socket
    self.logging_variant = logging_variant
    self.windows_os_version = windows_os_version
    self.enable_insecure_kubelet_readonly_port = (
        enable_insecure_kubelet_readonly_port)
    self.resource_manager_tags = resource_manager_tags
    self.containerd_config_from_file = containerd_config_from_file
    self.secondary_boot_disks = secondary_boot_disks
    self.machine_type = machine_type
    self.disk_type = disk_type
    self.disk_size_gb = disk_size_gb
    self.enable_queued_provisioning = enable_queued_provisioning
    self.enable_insecure_kubelet_readonly_port = (
        enable_insecure_kubelet_readonly_port
    )

  def IsAutoscalingUpdate(self):
    return (self.enable_autoscaling is not None or self.max_nodes is not None or
            self.min_nodes is not None or self.total_max_nodes is not None or
            self.total_min_nodes is not None or
            self.enable_autoprovisioning is not None or
            self.location_policy is not None)

  def IsNodePoolManagementUpdate(self):
    return (self.enable_autorepair is not None or
            self.enable_autoupgrade is not None)

  def IsUpdateNodePoolRequest(self):
    return (self.workload_metadata is not None or
            self.workload_metadata_from_node is not None or
            self.node_locations is not None or
            self.max_surge_upgrade is not None or
            self.max_unavailable_upgrade is not None or
            self.system_config_from_file is not None or
            self.labels is not None or self.node_labels is not None or
            self.node_taints is not None or self.tags is not None or
            self.enable_private_nodes is not None or
            self.enable_gcfs is not None or self.gvnic is not None or
            self.enable_image_streaming is not None or
            self.enable_surge_upgrade is not None or
            self.enable_blue_green_upgrade is not None or
            self.node_pool_soak_duration is not None or
            self.standard_rollout_policy is not None or
            self.network_performance_config is not None or
            self.enable_confidential_nodes is not None or
            self.enable_fast_socket is not None or
            self.logging_variant is not None or
            self.windows_os_version is not None or
            self.accelerators is not None or
            self.resource_manager_tags is not None or
            self.containerd_config_from_file is not None or
            self.machine_type is not None or
            self.disk_type is not None or
            self.disk_size_gb is not None or
            self.enable_queued_provisioning is not None)


class APIAdapter(object):
  """Handles making api requests in a version-agnostic way."""

  def __init__(self, registry, client, messages):
    self.registry = registry
    self.client = client
    self.messages = messages

  def ParseCluster(self, name, location, project=None):
    project = project or properties.VALUES.core.project.GetOrFail()
    # Note: we don't directly use container.projects.locations.clusters, etc,
    # because it has different fields and thus would change the rest of our
    # code heavily.
    return self.registry.Parse(
        util.LocationalResourceToZonal(name),
        params={
            'projectId': project,
            'zone': location,
        },
        collection='container.projects.zones.clusters')

  def ParseOperation(self, operation_id, location, project=None):
    project = project or properties.VALUES.core.project.GetOrFail()
    return self.registry.Parse(
        util.LocationalResourceToZonal(operation_id),
        params={
            'projectId': project,
            'zone': location,
        },
        collection='container.projects.zones.operations')

  def ParseNodePool(self, node_pool_id, location, project=None):
    project = project or properties.VALUES.core.project.GetOrFail()
    return self.registry.Parse(
        util.LocationalResourceToZonal(node_pool_id),
        params={
            'projectId': project,
            'clusterId': properties.VALUES.container.cluster.GetOrFail,
            'zone': location,
        },
        collection='container.projects.zones.clusters.nodePools')

  def GetCluster(self, cluster_ref):
    """Get a running cluster.

    Args:
      cluster_ref: cluster Resource to describe.

    Returns:
      Cluster message.
    Raises:
      Error: if cluster cannot be found or caller is missing permissions. Will
        attempt to find similar clusters in other zones for a more useful error
        if the user has list permissions.
    """
    try:
      return self.client.projects_locations_clusters.Get(
          self.messages.ContainerProjectsLocationsClustersGetRequest(
              name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref
                                          .zone, cluster_ref.clusterId)))
    except apitools_exceptions.HttpNotFoundError as error:
      api_error = exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
      # Cluster couldn't be found, maybe user got the location wrong?
      self.CheckClusterOtherZones(cluster_ref, api_error)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

  def CheckAutopilotCompatibility(self, cluster_ref):
    """Check autopilot compatibility of a cluster.

    Args:
      cluster_ref: cluster resource to check.

    Returns:
      A list of autopilot compatibility issues.
    Raises:
      Error: if cluster cannot be found or caller is missing permissions. Will
        attempt to find similar clusters in other zones for a more useful error
        if the user has list permissions.
    """
    try:
      return self.client.projects_locations_clusters.CheckAutopilotCompatibility(
          self.messages
          .ContainerProjectsLocationsClustersCheckAutopilotCompatibilityRequest(
              name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref
                                          .zone, cluster_ref.clusterId)))
    except apitools_exceptions.HttpNotFoundError as error:
      api_error = exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
      # Cluster couldn't be found, maybe user got the location wrong?
      self.CheckClusterOtherZones(cluster_ref, api_error)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

  def CheckClusterOtherZones(self, cluster_ref, api_error):
    """Searches for similar clusters in other locations and reports via error.

    Args:
      cluster_ref: cluster Resource to look for others with the same ID in
        different locations.
      api_error: current error from original request.

    Raises:
      Error: wrong zone error if another similar cluster found, otherwise not
      found error.
    """
    not_found_error = util.Error(
        NO_SUCH_CLUSTER_ERROR_MSG.format(
            error=api_error,
            name=cluster_ref.clusterId,
            project=cluster_ref.projectId))
    try:
      clusters = self.ListClusters(cluster_ref.projectId).clusters
    except apitools_exceptions.HttpForbiddenError as error:
      # Raise the default 404 Not Found error.
      # 403 Forbidden error shouldn't be raised for this unrequested list.
      raise not_found_error
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
    for cluster in clusters:
      if cluster.name == cluster_ref.clusterId:
        # Fall back to generic not found error if we *did* have the zone right.
        # Don't allow the case of a same-name cluster in a different zone to
        # be hinted (confusing!).
        if cluster.zone == cluster_ref.zone:
          raise api_error

        # User likely got zone wrong.
        raise util.Error(
            WRONG_ZONE_ERROR_MSG.format(
                error=api_error,
                name=cluster_ref.clusterId,
                wrong_zone=self.Zone(cluster_ref),
                zone=cluster.zone))
    # Couldn't find a cluster with that name.
    raise not_found_error

  def FindNodePool(self, cluster, pool_name=None):
    """Find the node pool with the given name in the cluster."""
    msg = ''
    if pool_name:
      for np in cluster.nodePools:
        if np.name == pool_name:
          return np
      msg = NO_SUCH_NODE_POOL_ERROR_MSG.format(
          cluster=cluster.name, name=pool_name) + os.linesep
    elif len(cluster.nodePools) == 1:
      return cluster.nodePools[0]
    # Couldn't find a node pool with that name or a node pool was not specified.
    msg += NO_NODE_POOL_SELECTED_ERROR_MSG + os.linesep.join(
        [np.name for np in cluster.nodePools])
    raise util.Error(msg)

  def GetOperation(self, operation_ref):
    return self.client.projects_locations_operations.Get(
        self.messages.ContainerProjectsLocationsOperationsGetRequest(
            name=ProjectLocationOperation(operation_ref.projectId, operation_ref
                                          .zone, operation_ref.operationId)))

  def WaitForOperation(self,
                       operation_ref,
                       message,
                       timeout_s=1200,
                       poll_period_s=5):
    """Poll container Operation until its status is done or timeout reached.

    Args:
      operation_ref: operation resource.
      message: str, message to display to user while polling.
      timeout_s: number, seconds to poll with retries before timing out.
      poll_period_s: number, delay in seconds between requests.

    Returns:
      Operation: the return value of the last successful operations.get
      request.

    Raises:
      Error: if the operation times out or finishes with an error.
    """
    detail_message = None
    with progress_tracker.ProgressTracker(
        message, autotick=True, detail_message_callback=lambda: detail_message):
      start_time = time.time()
      while timeout_s > (time.time() - start_time):
        try:
          operation = self.GetOperation(operation_ref)
          if self.IsOperationFinished(operation):
            # Success!
            log.info('Operation %s succeeded after %.3f seconds', operation,
                     (time.time() - start_time))
            break
          detail_message = operation.detail
        except apitools_exceptions.HttpError as error:
          log.debug('GetOperation failed: %s', error)
          if error.status_code == six.moves.http_client.FORBIDDEN:
            raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
          # Keep trying until we timeout in case error is transient.
        time.sleep(poll_period_s)
    if not self.IsOperationFinished(operation):
      log.err.Print('Timed out waiting for operation {0}'.format(operation))
      raise util.Error(
          'Operation [{0}] is still running, check its status via \'gcloud container operations describe {1}\''
          .format(operation, operation.name))
    if self.GetOperationError(operation):
      raise util.Error('Operation [{0}] finished with error: {1}'.format(
          operation, self.GetOperationError(operation)))

    return operation

  def Zone(self, cluster_ref):
    # TODO(b/72146704): Remove this method.
    return cluster_ref.zone

  def CreateClusterCommon(self, cluster_ref, options):
    """Returns a CreateCluster operation."""
    node_config = self.ParseNodeConfig(options)
    pools = self.ParseNodePools(options, node_config)

    cluster = self.messages.Cluster(name=cluster_ref.clusterId, nodePools=pools)
    if options.additional_zones:
      cluster.locations = sorted([cluster_ref.zone] + options.additional_zones)
    if options.node_locations:
      cluster.locations = sorted(options.node_locations)
    if options.cluster_version:
      cluster.initialClusterVersion = options.cluster_version
    if options.network:
      cluster.network = options.network
    if options.cluster_ipv4_cidr:
      cluster.clusterIpv4Cidr = options.cluster_ipv4_cidr
    if options.enable_stackdriver_kubernetes is not None:
      # When "enable-stackdriver-kubernetes" is specified, either true or false.
      if options.enable_stackdriver_kubernetes:
        cluster.loggingService = 'logging.googleapis.com/kubernetes'
        cluster.monitoringService = 'monitoring.googleapis.com/kubernetes'
        # When "enable-stackdriver-kubernetes" is true, the
        # "enable-cloud-logging" and "enable-cloud-monitoring" flags can be
        # used to explicitly disable logging or monitoring
        if (options.enable_cloud_logging is not None and
            not options.enable_cloud_logging):
          cluster.loggingService = 'none'
        if (options.enable_cloud_monitoring is not None and
            not options.enable_cloud_monitoring):
          cluster.monitoringService = 'none'
      else:
        cluster.loggingService = 'none'
        cluster.monitoringService = 'none'
    # When "enable-stackdriver-kubernetes" is unspecified, checks whether
    # "enable-cloud-logging" or "enable-cloud-monitoring" options are specified.
    else:
      if options.enable_cloud_logging is not None:
        if options.enable_cloud_logging:
          cluster.loggingService = 'logging.googleapis.com'
        else:
          cluster.loggingService = 'none'
      if options.enable_cloud_monitoring is not None:
        if options.enable_cloud_monitoring:
          cluster.monitoringService = 'monitoring.googleapis.com'
        else:
          cluster.monitoringService = 'none'
    if options.subnetwork:
      cluster.subnetwork = options.subnetwork
    if options.addons:
      addons = self._AddonsConfig(
          disable_ingress=INGRESS not in options.addons
          and not options.autopilot,
          disable_hpa=HPA not in options.addons and not options.autopilot,
          disable_dashboard=DASHBOARD not in options.addons,
          disable_network_policy=(NETWORK_POLICY not in options.addons),
          enable_node_local_dns=(NODELOCALDNS in options.addons or None),
          enable_gcepd_csi_driver=(GCEPDCSIDRIVER in options.addons),
          enable_filestore_csi_driver=(GCPFILESTORECSIDRIVER in options.addons),
          enable_application_manager=(APPLICATIONMANAGER in options.addons),
          enable_cloud_build=(CLOUDBUILD in options.addons),
          enable_backup_restore=(BACKUPRESTORE in options.addons),
          enable_gcsfuse_csi_driver=(GCSFUSECSIDRIVER in options.addons),
          enable_stateful_ha=(STATEFULHA in options.addons),
          enable_parallelstore_csi_driver=(
              PARALLELSTORECSIDRIVER in options.addons
          ),
      )
      # CONFIGCONNECTOR is disabled by default.
      if CONFIGCONNECTOR in options.addons:
        if not options.enable_stackdriver_kubernetes and (
            (options.monitoring is not None and
             SYSTEM not in options.monitoring) or
            (options.logging is not None and SYSTEM not in options.logging)):
          raise util.Error(
              CONFIGCONNECTOR_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG)
        if options.workload_pool is None:
          raise util.Error(CONFIGCONNECTOR_WORKLOAD_IDENTITY_DISABLED_ERROR_MSG)
        addons.configConnectorConfig = self.messages.ConfigConnectorConfig(
            enabled=True)
      cluster.addonsConfig = addons
    self.ParseMasterAuthorizedNetworkOptions(options, cluster)

    if options.enable_kubernetes_alpha:
      cluster.enableKubernetesAlpha = options.enable_kubernetes_alpha

    if options.default_max_pods_per_node is not None:
      if not options.enable_ip_alias:
        raise util.Error(DEFAULT_MAX_PODS_PER_NODE_WITHOUT_IP_ALIAS_ERROR_MSG)
      cluster.defaultMaxPodsConstraint = self.messages.MaxPodsConstraint(
          maxPodsPerNode=options.default_max_pods_per_node)

    if options.disable_default_snat:
      if not options.enable_ip_alias:
        raise util.Error(DISABLE_DEFAULT_SNAT_WITHOUT_IP_ALIAS_ERROR_MSG)
      if not options.enable_private_nodes:
        raise util.Error(DISABLE_DEFAULT_SNAT_WITHOUT_PRIVATE_NODES_ERROR_MSG)
      default_snat_status = self.messages.DefaultSnatStatus(
          disabled=options.disable_default_snat)
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            defaultSnatStatus=default_snat_status)
      else:
        cluster.networkConfig.defaultSnatStatus = default_snat_status

    if options.dataplane_v2 is not None and options.dataplane_v2:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.datapathProvider = \
            self.messages.NetworkConfig.DatapathProviderValueValuesEnum.ADVANCED_DATAPATH

    if options.enable_l4_ilb_subsetting:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            enableL4ilbSubsetting=options.enable_l4_ilb_subsetting)
      else:
        cluster.networkConfig.enableL4ilbSubsetting = options.enable_l4_ilb_subsetting

    dns_config = self.ParseClusterDNSOptions(options)
    if dns_config is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            dnsConfig=dns_config)
      else:
        cluster.networkConfig.dnsConfig = dns_config

    gateway_config = self.ParseGatewayOptions(options)
    if gateway_config is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            gatewayApiConfig=gateway_config)
      else:
        cluster.networkConfig.gatewayApiConfig = gateway_config

    if options.enable_legacy_authorization is not None:
      cluster.legacyAbac = self.messages.LegacyAbac(
          enabled=bool(options.enable_legacy_authorization))

    # Only Calico is currently supported as a network policy provider.
    if options.enable_network_policy:
      cluster.networkPolicy = self.messages.NetworkPolicy(
          enabled=options.enable_network_policy,
          provider=self.messages.NetworkPolicy.ProviderValueValuesEnum.CALICO)

    if options.enable_binauthz is not None:
      cluster.binaryAuthorization = self.messages.BinaryAuthorization(
          enabled=options.enable_binauthz)

    if options.binauthz_evaluation_mode is not None:
      if options.binauthz_policy_bindings is not None:
        cluster.binaryAuthorization = self.messages.BinaryAuthorization(
            evaluationMode=util.GetBinauthzEvaluationModeMapper(
                self.messages, hidden=False
            ).GetEnumForChoice(options.binauthz_evaluation_mode),
        )
        for binding in options.binauthz_policy_bindings:
          cluster.binaryAuthorization.policyBindings.append(
              self.messages.PolicyBinding(name=binding['name'])
          )
      else:
        cluster.binaryAuthorization = self.messages.BinaryAuthorization(
            evaluationMode=util.GetBinauthzEvaluationModeMapper(
                self.messages, hidden=False
            ).GetEnumForChoice(options.binauthz_evaluation_mode),
        )

    # Policy bindings only makes sense in the context of an evaluation mode.
    if (
        options.binauthz_policy_bindings
        and not options.binauthz_evaluation_mode
    ):
      raise util.Error(
          PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='binauthz-evaluation-mode',
              opt='binauthz-policy-bindings',
          )
      )

    if options.maintenance_window is not None:
      cluster.maintenancePolicy = self.messages.MaintenancePolicy(
          window=self.messages.MaintenanceWindow(
              dailyMaintenanceWindow=self.messages.DailyMaintenanceWindow(
                  startTime=options.maintenance_window)))
    elif options.maintenance_window_start is not None:
      window_start = options.maintenance_window_start.isoformat()
      window_end = options.maintenance_window_end.isoformat()
      cluster.maintenancePolicy = self.messages.MaintenancePolicy(
          window=self.messages.MaintenanceWindow(
              recurringWindow=self.messages.RecurringTimeWindow(
                  window=self.messages.TimeWindow(
                      startTime=window_start, endTime=window_end),
                  recurrence=options.maintenance_window_recurrence)))

    self.ParseResourceLabels(options, cluster)

    if options.enable_pod_security_policy is not None:
      cluster.podSecurityPolicyConfig = self.messages.PodSecurityPolicyConfig(
          enabled=options.enable_pod_security_policy)

    if options.security_group is not None:
      # The presence of the --security_group="foo" flag implies enabled=True.
      cluster.authenticatorGroupsConfig = (
          self.messages.AuthenticatorGroupsConfig(
              enabled=True, securityGroup=options.security_group))
    if options.enable_shielded_nodes is not None:
      cluster.shieldedNodes = self.messages.ShieldedNodes(
          enabled=options.enable_shielded_nodes)

    if options.workload_pool:
      cluster.workloadIdentityConfig = self.messages.WorkloadIdentityConfig(
          workloadPool=options.workload_pool)

    self.ParseIPAliasOptions(options, cluster)
    self.ParseAllowRouteOverlapOptions(options, cluster)
    self.ParsePrivateClusterOptions(options, cluster)
    self.ParseTpuOptions(options, cluster)
    if options.enable_vertical_pod_autoscaling is not None:
      cluster.verticalPodAutoscaling = self.messages.VerticalPodAutoscaling(
          enabled=options.enable_vertical_pod_autoscaling)

    if options.resource_usage_bigquery_dataset:
      bigquery_destination = self.messages.BigQueryDestination(
          datasetId=options.resource_usage_bigquery_dataset)
      cluster.resourceUsageExportConfig = \
          self.messages.ResourceUsageExportConfig(
              bigqueryDestination=bigquery_destination)
      if options.enable_network_egress_metering:
        cluster.resourceUsageExportConfig.enableNetworkEgressMetering = True
      if options.enable_resource_consumption_metering is not None:
        cluster.resourceUsageExportConfig.consumptionMeteringConfig = \
            self.messages.ConsumptionMeteringConfig(
                enabled=options.enable_resource_consumption_metering)
    elif options.enable_network_egress_metering is not None:
      raise util.Error(ENABLE_NETWORK_EGRESS_METERING_ERROR_MSG)
    elif options.enable_resource_consumption_metering is not None:
      raise util.Error(ENABLE_RESOURCE_CONSUMPTION_METERING_ERROR_MSG)

    # Only instantiate the masterAuth struct if one or both of `user` or
    # `issue_client_certificate` is configured. Server-side Basic auth default
    # behavior is dependent on the absence of the MasterAuth struct. For this
    # reason, if only `issue_client_certificate` is configured, Basic auth will
    # be disabled.
    if options.user is not None or options.issue_client_certificate is not None:
      cluster.masterAuth = self.messages.MasterAuth(
          username=options.user, password=options.password)
      if options.issue_client_certificate is not None:
        cluster.masterAuth.clientCertificateConfig = (
            self.messages.ClientCertificateConfig(
                issueClientCertificate=options.issue_client_certificate))

    if options.enable_intra_node_visibility is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            enableIntraNodeVisibility=options.enable_intra_node_visibility)
      else:
        cluster.networkConfig.enableIntraNodeVisibility = \
            options.enable_intra_node_visibility

    if options.database_encryption_key:
      cluster.databaseEncryption = self.messages.DatabaseEncryption(
          keyName=options.database_encryption_key,
          state=self.messages.DatabaseEncryption.StateValueValuesEnum.ENCRYPTED)

    if options.boot_disk_kms_key:
      for pool in cluster.nodePools:
        pool.config.bootDiskKmsKey = options.boot_disk_kms_key

    cluster.releaseChannel = _GetReleaseChannel(options, self.messages)

    if options.autopilot:
      cluster.autopilot = self.messages.Autopilot()
      cluster.autopilot.enabled = True

      if options.workload_policies:
        if cluster.autopilot.workloadPolicyConfig is None:
          cluster.autopilot.workloadPolicyConfig = (
              self.messages.WorkloadPolicyConfig())
        if options.workload_policies == 'allow-net-admin':
          cluster.autopilot.workloadPolicyConfig.allowNetAdmin = True

      if options.enable_secret_manager:
        if cluster.secretManagerConfig is None:
          cluster.secretManagerConfig = self.messages.SecretManagerConfig(
              enabled=False
          )
      if options.boot_disk_kms_key:
        if cluster.autoscaling is None:
          cluster.autoscaling = self.messages.ClusterAutoscaling()
        if cluster.autoscaling.autoprovisioningNodePoolDefaults is None:
          cluster.autoscaling.autoprovisioningNodePoolDefaults = self.messages.AutoprovisioningNodePoolDefaults(
          )
        cluster.autoscaling.autoprovisioningNodePoolDefaults.bootDiskKmsKey = options.boot_disk_kms_key

    if options.enable_confidential_nodes:
      cluster.confidentialNodes = self.messages.ConfidentialNodes(
          enabled=options.enable_confidential_nodes)

    if options.private_ipv6_google_access_type is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.privateIpv6GoogleAccess = util.GetPrivateIpv6GoogleAccessTypeMapper(
          self.messages, hidden=False).GetEnumForChoice(
              options.private_ipv6_google_access_type)

    # Apply node kubelet config on non-autopilot clusters.
    if options.enable_insecure_kubelet_readonly_port is not None:
      if options.autopilot:
        raise util.Error(NODECONFIGDEFAULTS_READONLY_PORT_NOT_SUPPORTED)

      if cluster.nodePoolDefaults is None:
        cluster.nodePoolDefaults = self.messages.NodePoolDefaults()

      if cluster.nodePoolDefaults.nodeConfigDefaults is None:
        cluster.nodePoolDefaults.nodeConfigDefaults = (
            self.messages.NodeConfigDefaults()
        )

      if cluster.nodePoolDefaults.nodeConfigDefaults.nodeKubeletConfig is None:
        cluster.nodePoolDefaults.nodeConfigDefaults.nodeKubeletConfig = (
            self.messages.NodeKubeletConfig()
        )

      cluster.nodePoolDefaults.nodeConfigDefaults.nodeKubeletConfig.insecureKubeletReadonlyPortEnabled = (
          options.enable_insecure_kubelet_readonly_port
      )

    # Apply nodePoolAutoconfig on both autopilot and standard clusters.
    # pylint: disable=line-too-long
    if (
        options.autoprovisioning_enable_insecure_kubelet_readonly_port
        is not None
    ):
      if cluster.nodePoolAutoConfig is None:
        cluster.nodePoolAutoConfig = self.messages.NodePoolAutoConfig()

      if cluster.nodePoolAutoConfig.nodeKubeletConfig is None:
        cluster.nodePoolAutoConfig.nodeKubeletConfig = (
            self.messages.NodeKubeletConfig()
        )

      cluster.nodePoolAutoConfig.nodeKubeletConfig.insecureKubeletReadonlyPortEnabled = (
          options.autoprovisioning_enable_insecure_kubelet_readonly_port
      )

    if options.enable_gcfs:
      if cluster.nodePoolDefaults is None:
        cluster.nodePoolDefaults = self.messages.NodePoolDefaults()
      if cluster.nodePoolDefaults.nodeConfigDefaults is None:
        cluster.nodePoolDefaults.nodeConfigDefaults = (
            self.messages.NodeConfigDefaults())
      cluster.nodePoolDefaults.nodeConfigDefaults.gcfsConfig = (
          self.messages.GcfsConfig(enabled=options.enable_gcfs))

    if options.containerd_config_from_file is not None:
      if cluster.nodePoolDefaults is None:
        cluster.nodePoolDefaults = self.messages.NodePoolDefaults()
      if cluster.nodePoolDefaults.nodeConfigDefaults is None:
        cluster.nodePoolDefaults.nodeConfigDefaults = (
            self.messages.NodeConfigDefaults())
      cluster.nodePoolDefaults.nodeConfigDefaults.containerdConfig = (
          self.messages.ContainerdConfig())
      util.LoadContainerdConfigFromYAML(
          cluster.nodePoolDefaults.nodeConfigDefaults.containerdConfig,
          options.containerd_config_from_file,
          self.messages,
      )

    if options.autoprovisioning_network_tags:
      if cluster.nodePoolAutoConfig is None:
        cluster.nodePoolAutoConfig = self.messages.NodePoolAutoConfig()
      cluster.nodePoolAutoConfig.networkTags = (
          self.messages.NetworkTags(tags=options.autoprovisioning_network_tags))

    if options.autoprovisioning_resource_manager_tags is not None:
      if cluster.nodePoolAutoConfig is None:
        cluster.nodePoolAutoConfig = self.messages.NodePoolAutoConfig()
      rm_tags = self._ResourceManagerTags(
          options.autoprovisioning_resource_manager_tags
      )
      cluster.nodePoolAutoConfig.resourceManagerTags = rm_tags

    if options.enable_image_streaming:
      if cluster.nodePoolDefaults is None:
        cluster.nodePoolDefaults = self.messages.NodePoolDefaults()
      if cluster.nodePoolDefaults.nodeConfigDefaults is None:
        cluster.nodePoolDefaults.nodeConfigDefaults = (
            self.messages.NodeConfigDefaults())
      cluster.nodePoolDefaults.nodeConfigDefaults.gcfsConfig = (
          self.messages.GcfsConfig(enabled=options.enable_image_streaming))

    if options.maintenance_interval:
      if cluster.nodePoolDefaults is None:
        cluster.nodePoolDefaults = self.messages.NodePoolDefaults()
      if cluster.nodePoolDefaults.nodeConfigDefaults is None:
        cluster.nodePoolDefaults.nodeConfigDefaults = (
            self.messages.NodeConfigDefaults())
      cluster.nodePoolDefaults.nodeConfigDefaults.stableFleetConfig = (
          _GetStableFleetConfig(options, self.messages))

    if options.enable_mesh_certificates:
      if not options.workload_pool:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='workload-pool', opt='enable-mesh-certificates'))
      if cluster.meshCertificates is None:
        cluster.meshCertificates = self.messages.MeshCertificates()
      cluster.meshCertificates.enableCertificates = options.enable_mesh_certificates

    _AddNotificationConfigToCluster(cluster, options, self.messages)

    cluster.loggingConfig = _GetLoggingConfig(options, self.messages)
    cluster.monitoringConfig = _GetMonitoringConfig(options, self.messages)

    if options.enable_service_externalips is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.serviceExternalIpsConfig = self.messages.ServiceExternalIPsConfig(
          enabled=options.enable_service_externalips)

    if options.enable_identity_service:
      cluster.identityServiceConfig = self.messages.IdentityServiceConfig(
          enabled=options.enable_identity_service)

    if options.enable_workload_config_audit is not None:
      if cluster.protectConfig is None:
        cluster.protectConfig = self.messages.ProtectConfig(
            workloadConfig=self.messages.WorkloadConfig())
      if options.enable_workload_config_audit:
        cluster.protectConfig.workloadConfig.auditMode = (
            self.messages.WorkloadConfig.AuditModeValueValuesEnum.BASIC)
      else:
        cluster.protectConfig.workloadConfig.auditMode = (
            self.messages.WorkloadConfig.AuditModeValueValuesEnum.DISABLED)

    if options.enable_workload_vulnerability_scanning is not None:
      if cluster.protectConfig is None:
        cluster.protectConfig = self.messages.ProtectConfig()
      if options.enable_workload_vulnerability_scanning:
        cluster.protectConfig.workloadVulnerabilityMode = (
            self.messages.ProtectConfig.WorkloadVulnerabilityModeValueValuesEnum
            .BASIC)
      else:
        cluster.protectConfig.workloadVulnerabilityMode = (
            self.messages.ProtectConfig.WorkloadVulnerabilityModeValueValuesEnum
            .DISABLED)

    if options.pod_autoscaling_direct_metrics_opt_in is not None:
      pod_autoscaling_config = self.messages.PodAutoscaling(
          directMetricsOptIn=options.pod_autoscaling_direct_metrics_opt_in)
      cluster.podAutoscaling = pod_autoscaling_config

    if options.private_endpoint_subnetwork is not None:
      if cluster.privateClusterConfig is None:
        cluster.privateClusterConfig = self.messages.PrivateClusterConfig()
      cluster.privateClusterConfig.privateEndpointSubnetwork = options.private_endpoint_subnetwork

    if options.managed_config is not None:
      if options.managed_config.lower() == 'autofleet':
        cluster.managedConfig = self.messages.ManagedConfig(
            type=self.messages.ManagedConfig.TypeValueValuesEnum.AUTOFLEET)
      elif options.managed_config.lower() == 'disabled':
        cluster.managedConfig = self.messages.ManagedConfig(
            type=self.messages.ManagedConfig.TypeValueValuesEnum.DISABLED)
      else:
        raise util.Error(
            MANGED_CONFIG_TYPE_NOT_SUPPORTED.format(
                type=options.managed_config))

    if options.enable_fleet:
      if cluster.fleet is None:
        cluster.fleet = self.messages.Fleet()
      cluster.fleet.project = cluster_ref.projectId

    if options.fleet_project:
      if cluster.fleet is None:
        cluster.fleet = self.messages.Fleet()
      cluster.fleet.project = options.fleet_project

    if options.logging_variant is not None:
      if cluster.nodePoolDefaults is None:
        cluster.nodePoolDefaults = self.messages.NodePoolDefaults()
      if cluster.nodePoolDefaults.nodeConfigDefaults is None:
        cluster.nodePoolDefaults.nodeConfigDefaults = (
            self.messages.NodeConfigDefaults())
      if cluster.nodePoolDefaults.nodeConfigDefaults.loggingConfig is None:
        cluster.nodePoolDefaults.nodeConfigDefaults.loggingConfig = (
            self.messages.NodePoolLoggingConfig())
      cluster.nodePoolDefaults.nodeConfigDefaults.loggingConfig.variantConfig = (
          self.messages.LoggingVariantConfig(
              variant=VariantConfigEnumFromString(self.messages,
                                                  options.logging_variant)))

    if options.enable_cost_allocation:
      cluster.costManagementConfig = self.messages.CostManagementConfig(
          enabled=True)

    if options.enable_multi_networking:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            enableMultiNetworking=options.enable_multi_networking)
      else:
        cluster.networkConfig.enableMultiNetworking = options.enable_multi_networking

    if options.enable_security_posture is not None:
      if cluster.securityPostureConfig is None:
        cluster.securityPostureConfig = self.messages.SecurityPostureConfig()
      if options.enable_security_posture:
        cluster.securityPostureConfig.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.BASIC
        )
      else:
        cluster.securityPostureConfig.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.DISABLED
        )

    if options.security_posture is not None:
      if cluster.securityPostureConfig is None:
        cluster.securityPostureConfig = self.messages.SecurityPostureConfig()
      if options.security_posture.lower() == 'standard':
        cluster.securityPostureConfig.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.BASIC
        )
      elif options.security_posture.lower() == 'disabled':
        cluster.securityPostureConfig.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.DISABLED
        )
      else:
        raise util.Error(
            SECURITY_POSTURE_MODE_NOT_SUPPORTED.format(
                mode=options.security_posture.lower()
            )
        )

    if options.workload_vulnerability_scanning is not None:
      if cluster.securityPostureConfig is None:
        cluster.securityPostureConfig = self.messages.SecurityPostureConfig()
      if options.workload_vulnerability_scanning.lower() == 'standard':
        cluster.securityPostureConfig.vulnerabilityMode = (
            self.messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum.VULNERABILITY_BASIC
        )
      elif options.workload_vulnerability_scanning.lower() == 'disabled':
        cluster.securityPostureConfig.vulnerabilityMode = (
            self.messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum.VULNERABILITY_DISABLED
        )
      elif options.workload_vulnerability_scanning.lower() == 'enterprise':
        cluster.securityPostureConfig.vulnerabilityMode = (
            self.messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum.VULNERABILITY_ENTERPRISE
        )
      else:
        raise util.Error(
            WORKLOAD_VULNERABILITY_SCANNING_MODE_NOT_SUPPORTED.format(
                mode=options.workload_vulnerability_scanning.lower()
            )
        )

    if options.enable_runtime_vulnerability_insight is not None:
      if cluster.runtimeVulnerabilityInsightConfig is None:
        cluster.runtimeVulnerabilityInsightConfig = (
            self.messages.RuntimeVulnerabilityInsightConfig())
      if options.enable_runtime_vulnerability_insight:
        cluster.runtimeVulnerabilityInsightConfig.mode = (
            self.messages.RuntimeVulnerabilityInsightConfig.ModeValueValuesEnum.PREMIUM_VULNERABILITY_SCAN
        )
      else:
        cluster.runtimeVulnerabilityInsightConfig.mode = (
            self.messages.RuntimeVulnerabilityInsightConfig.ModeValueValuesEnum.DISABLED
        )

    if options.network_performance_config:
      perf = self._GetClusterNetworkPerformanceConfig(options)
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            networkPerformanceConfig=perf)
      else:
        cluster.networkConfig.networkPerformanceConfig = perf

    if options.enable_k8s_beta_apis:
      cluster.enableK8sBetaApis = self.messages.K8sBetaAPIConfig()
      cluster.enableK8sBetaApis.enabledApis = options.enable_k8s_beta_apis

    if options.host_maintenance_interval:
      if cluster.nodePoolDefaults is None:
        cluster.nodePoolDefaults = self.messages.NodePoolDefaults()
      if cluster.nodePoolDefaults.nodeConfigDefaults is None:
        cluster.nodePoolDefaults.nodeConfigDefaults = (
            self.messages.NodeConfigDefaults())
      cluster.nodePoolDefaults.nodeConfigDefaults.hostMaintenancePolicy = (
          _GetHostMaintenancePolicy(options, self.messages))

    if options.in_transit_encryption is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.inTransitEncryptionConfig = (
          util.GetCreateInTransitEncryptionConfigMapper(
              self.messages
          ).GetEnumForChoice(options.in_transit_encryption)
      )

    if options.enable_secret_manager is not None:
      if cluster.secretManagerConfig is None:
        cluster.secretManagerConfig = self.messages.SecretManagerConfig()
      cluster.secretManagerConfig.enabled = options.enable_secret_manager

    if options.enable_cilium_clusterwide_network_policy is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.enableCiliumClusterwideNetworkPolicy = (
          options.enable_cilium_clusterwide_network_policy
      )

    if options.enable_fqdn_network_policy is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.enableFqdnNetworkPolicy = (
          options.enable_fqdn_network_policy)

    return cluster

  def _GetClusterNetworkPerformanceConfig(self, options):
    network_perf_args = options.network_performance_config
    network_perf_configs = self.messages.ClusterNetworkPerformanceConfig()

    for config in network_perf_args:
      total_tier = config.get('total-egress-bandwidth-tier', '').upper()
      if total_tier:
        network_perf_configs.totalEgressBandwidthTier = (
            self.messages.ClusterNetworkPerformanceConfig
            .TotalEgressBandwidthTierValueValuesEnum(total_tier))

    return network_perf_configs

  def ParseNodeConfig(self, options):
    """Creates node config based on node config options."""
    node_config = self.messages.NodeConfig()
    if options.node_machine_type:
      node_config.machineType = options.node_machine_type
    if options.node_disk_size_gb:
      node_config.diskSizeGb = options.node_disk_size_gb
    if options.disk_type:
      node_config.diskType = options.disk_type
    if options.node_source_image:
      raise util.Error('cannot specify node source image in container v1 api')

    NodeIdentityOptionsToNodeConfig(options, node_config)

    if options.local_ssd_count:
      node_config.localSsdCount = options.local_ssd_count
    self._AddLocalSSDVolumeConfigsToNodeConfig(node_config, options)
    self._AddEphemeralStorageToNodeConfig(node_config, options)
    self._AddEphemeralStorageLocalSsdToNodeConfig(node_config, options)
    self._AddLocalNvmeSsdBlockToNodeConfig(node_config, options)
    self._AddEnableConfidentialStorageToNodeConfig(node_config, options)
    self._AddStoragePoolsToNodeConfig(node_config, options)

    if options.tags:
      node_config.tags = options.tags
    else:
      node_config.tags = []

    if options.image_type:
      node_config.imageType = options.image_type

    self.ParseCustomNodeConfig(options, node_config)

    _AddNodeLabelsToNodeConfig(node_config, options)
    _AddLabelsToNodeConfig(node_config, options)
    _AddMetadataToNodeConfig(node_config, options)
    self._AddNodeTaintsToNodeConfig(node_config, options)

    if options.resource_manager_tags is not None:
      tags = options.resource_manager_tags
      node_config.resourceManagerTags = self._ResourceManagerTags(tags)

    if options.preemptible:
      node_config.preemptible = options.preemptible

    if options.spot:
      node_config.spot = options.spot

    self.ParseAcceleratorOptions(options, node_config)

    if options.min_cpu_platform is not None:
      node_config.minCpuPlatform = options.min_cpu_platform

    self._AddWorkloadMetadataToNodeConfig(node_config, options, self.messages)
    _AddLinuxNodeConfigToNodeConfig(node_config, options, self.messages)
    _AddShieldedInstanceConfigToNodeConfig(node_config, options, self.messages)
    _AddReservationAffinityToNodeConfig(node_config, options, self.messages)

    if options.system_config_from_file is not None:
      util.LoadSystemConfigFromYAML(
          node_config,
          options.system_config_from_file,
          options.enable_insecure_kubelet_readonly_port,
          self.messages,
      )

    self.ParseAdvancedMachineFeatures(options, node_config)

    if options.gvnic is not None:
      gvnic = self.messages.VirtualNIC(enabled=options.gvnic)
      node_config.gvnic = gvnic

    return node_config

  def ParseAdvancedMachineFeatures(self, options, node_config):
    """Parses advanced machine feature node config options."""
    features = self.messages.AdvancedMachineFeatures()
    if options.threads_per_core:
      features.threadsPerCore = options.threads_per_core
    if options.enable_nested_virtualization:
      features.enableNestedVirtualization = options.enable_nested_virtualization
    if options.performance_monitoring_unit:
      features.performanceMonitoringUnit = (
          features.PerformanceMonitoringUnitValueValuesEnum(
              options.performance_monitoring_unit.upper()))

    if (options.threads_per_core
        or options.enable_nested_virtualization
        or options.performance_monitoring_unit):
      node_config.advancedMachineFeatures = features

  def ParseCustomNodeConfig(self, options, node_config):
    """Parses custom node config options."""
    custom_config = self.messages.CustomImageConfig()
    if options.image:
      custom_config.image = options.image
    if options.image_project:
      custom_config.imageProject = options.image_project
    if options.image_family:
      custom_config.imageFamily = options.image_family
    if options.image or options.image_project or options.image_family:
      node_config.nodeImageConfig = custom_config

  def ParseNodePools(self, options, node_config):
    """Creates a list of node pools for the cluster by parsing options.

    Args:
      options: cluster creation options
      node_config: node configuration for nodes in the node pools

    Returns:
      List of node pools.
    """
    max_nodes_per_pool = options.max_nodes_per_pool or MAX_NODES_PER_POOL
    pools = (options.num_nodes + max_nodes_per_pool - 1) // max_nodes_per_pool
    if pools == 1:
      pool_names = ['default-pool']  # pool consistency with server default
    else:
      # default-pool-0, -1, ...
      pool_names = ['default-pool-{0}'.format(i) for i in range(0, pools)]

    pools = []
    per_pool = (options.num_nodes + len(pool_names) - 1) // len(pool_names)
    to_add = options.num_nodes
    for name in pool_names:
      nodes = per_pool if (to_add > per_pool) else to_add
      pool = self.messages.NodePool(
          name=name,
          initialNodeCount=nodes,
          config=node_config,
          version=options.node_version,
          management=self._GetNodeManagement(options),
      )
      if options.enable_autoscaling:
        pool.autoscaling = self.messages.NodePoolAutoscaling(
            enabled=options.enable_autoscaling,
            minNodeCount=options.min_nodes,
            maxNodeCount=options.max_nodes,
            totalMinNodeCount=options.total_min_nodes,
            totalMaxNodeCount=options.total_max_nodes,
        )
        if options.location_policy is not None:
          pool.autoscaling.locationPolicy = LocationPolicyEnumFromString(
              self.messages, options.location_policy
          )
      if options.max_pods_per_node:
        if not options.enable_ip_alias:
          raise util.Error(MAX_PODS_PER_NODE_WITHOUT_IP_ALIAS_ERROR_MSG)
        pool.maxPodsConstraint = self.messages.MaxPodsConstraint(
            maxPodsPerNode=options.max_pods_per_node
        )
      if (
          options.max_surge_upgrade is not None
          or options.max_unavailable_upgrade is not None
      ):
        pool.upgradeSettings = self.messages.UpgradeSettings()
        pool.upgradeSettings.maxSurge = options.max_surge_upgrade
        pool.upgradeSettings.maxUnavailable = options.max_unavailable_upgrade
      if (
          options.placement_type == 'COMPACT'
          or options.placement_policy is not None
      ):
        pool.placementPolicy = self.messages.PlacementPolicy()
      if options.placement_type == 'COMPACT':
        pool.placementPolicy.type = (
            self.messages.PlacementPolicy.TypeValueValuesEnum.COMPACT
        )
      if options.placement_policy is not None:
        pool.placementPolicy.policyName = options.placement_policy
      if options.enable_queued_provisioning is not None:
        pool.queuedProvisioning = self.messages.QueuedProvisioning()
        pool.queuedProvisioning.enabled = options.enable_queued_provisioning
      pools.append(pool)
      to_add -= nodes
    return pools

  def ParseAcceleratorOptions(self, options, node_config):
    """Parses accrelerator options for the nodes in the cluster."""
    if options.accelerators is not None:
      type_name = options.accelerators['type']
      # Accelerator count defaults to 1.
      count = int(options.accelerators.get('count', 1))
      accelerator_config = self.messages.AcceleratorConfig(
          acceleratorType=type_name, acceleratorCount=count)

      gpu_partition_size = options.accelerators.get('gpu-partition-size', '')
      if gpu_partition_size:
        accelerator_config.gpuPartitionSize = gpu_partition_size

      max_time_shared_clients_per_gpu = int(
          options.accelerators.get('max-time-shared-clients-per-gpu', 0))
      if max_time_shared_clients_per_gpu:
        accelerator_config.maxTimeSharedClientsPerGpu = max_time_shared_clients_per_gpu

      gpu_sharing_strategy = options.accelerators.get('gpu-sharing-strategy',
                                                      None)
      max_shared_clients_per_gpu = options.accelerators.get(
          'max-shared-clients-per-gpu', None)
      if max_shared_clients_per_gpu or gpu_sharing_strategy:
        if max_shared_clients_per_gpu is None:
          # The validation for this field is handled in the server.
          max_shared_clients_per_gpu = 2
        else:
          max_shared_clients_per_gpu = int(max_shared_clients_per_gpu)

        strategy_enum = self.messages.GPUSharingConfig.GpuSharingStrategyValueValuesEnum
        if gpu_sharing_strategy is None:
          # The GPU sharing strategy will be time-sharing by default.
          gpu_sharing_strategy = strategy_enum.TIME_SHARING
        elif gpu_sharing_strategy == 'time-sharing':
          gpu_sharing_strategy = strategy_enum.TIME_SHARING
        elif gpu_sharing_strategy == 'mps':
          gpu_sharing_strategy = strategy_enum.MPS
        else:
          raise util.Error(GPU_SHARING_STRATEGY_ERROR_MSG)

        gpu_sharing_config = self.messages.GPUSharingConfig(
            maxSharedClientsPerGpu=max_shared_clients_per_gpu,
            gpuSharingStrategy=gpu_sharing_strategy)
        accelerator_config.gpuSharingConfig = gpu_sharing_config

      gpu_driver_version = options.accelerators.get(
          'gpu-driver-version', None
      )
      if gpu_driver_version is not None:
        if gpu_driver_version.lower() == 'default':
          gpu_driver_version = (
              self.messages.GPUDriverInstallationConfig.GpuDriverVersionValueValuesEnum.DEFAULT
          )
        elif gpu_driver_version.lower() == 'latest':
          gpu_driver_version = (
              self.messages.GPUDriverInstallationConfig.GpuDriverVersionValueValuesEnum.LATEST
          )
        elif gpu_driver_version.lower() == 'disabled':
          gpu_driver_version = (
              self.messages.GPUDriverInstallationConfig.GpuDriverVersionValueValuesEnum.INSTALLATION_DISABLED
          )
        else:
          raise util.Error(GPU_DRIVER_VERSION_ERROR_MSG)

        gpu_driver_installation_config = (
            self.messages.GPUDriverInstallationConfig(
                gpuDriverVersion=gpu_driver_version
            )
        )
        accelerator_config.gpuDriverInstallationConfig = (
            gpu_driver_installation_config
        )

      node_config.accelerators = [
          accelerator_config,
      ]

  def ParseResourceLabels(self, options, cluster):
    """Parses resource labels options for the cluster."""
    if options.labels is not None:
      labels = self.messages.Cluster.ResourceLabelsValue()
      props = []
      for k, v in sorted(six.iteritems(options.labels)):
        props.append(labels.AdditionalProperty(key=k, value=v))
      labels.additionalProperties = props
      cluster.resourceLabels = labels

  def ParseIPAliasOptions(self, options, cluster):
    """Parses the options for IP Alias."""
    ip_alias_only_options = [('services-ipv4-cidr', options.services_ipv4_cidr),
                             ('create-subnetwork', options.create_subnetwork),
                             ('cluster-secondary-range-name',
                              options.cluster_secondary_range_name),
                             ('services-secondary-range-name',
                              options.services_secondary_range_name),
                             ('disable-pod-cidr-overprovision',
                              options.disable_pod_cidr_overprovision),
                             ('stack-type', options.stack_type),
                             ('ipv6-access-type', options.ipv6_access_type)]
    if not options.enable_ip_alias:
      for name, opt in ip_alias_only_options:
        if opt:
          raise util.Error(
              PREREQUISITE_OPTION_ERROR_MSG.format(
                  prerequisite='enable-ip-alias', opt=name))

    if options.subnetwork and options.create_subnetwork is not None:
      raise util.Error(CREATE_SUBNETWORK_WITH_SUBNETWORK_ERROR_MSG)

    if options.enable_ip_alias:
      subnetwork_name = None
      node_ipv4_cidr = None

      if options.create_subnetwork is not None:
        for key in options.create_subnetwork:
          if key not in ['name', 'range']:
            raise util.Error(
                CREATE_SUBNETWORK_INVALID_KEY_ERROR_MSG.format(key=key))
        subnetwork_name = options.create_subnetwork.get('name', None)
        node_ipv4_cidr = options.create_subnetwork.get('range', None)

      policy = self.messages.IPAllocationPolicy(
          useIpAliases=options.enable_ip_alias,
          createSubnetwork=options.create_subnetwork is not None,
          subnetworkName=subnetwork_name,
          clusterIpv4CidrBlock=options.cluster_ipv4_cidr,
          nodeIpv4CidrBlock=node_ipv4_cidr,
          servicesIpv4CidrBlock=options.services_ipv4_cidr,
          clusterSecondaryRangeName=options.cluster_secondary_range_name,
          servicesSecondaryRangeName=options.services_secondary_range_name)
      if options.disable_pod_cidr_overprovision is not None:
        policy.podCidrOverprovisionConfig = self.messages.PodCIDROverprovisionConfig(
            disable=options.disable_pod_cidr_overprovision)
      if options.tpu_ipv4_cidr:
        policy.tpuIpv4CidrBlock = options.tpu_ipv4_cidr
      if options.stack_type is not None:
        policy.stackType = util.GetCreateStackTypeMapper(
            self.messages).GetEnumForChoice(options.stack_type)
      if options.ipv6_access_type is not None:
        policy.ipv6AccessType = util.GetIpv6AccessTypeMapper(
            self.messages).GetEnumForChoice(options.ipv6_access_type)

      cluster.clusterIpv4Cidr = None
      cluster.ipAllocationPolicy = policy
    elif options.enable_ip_alias is not None:
      cluster.ipAllocationPolicy = self.messages.IPAllocationPolicy(
          useRoutes=True)

    return cluster

  def ParseAllowRouteOverlapOptions(self, options, cluster):
    """Parse the options for allow route overlap."""
    if not options.allow_route_overlap:
      return
    if options.enable_ip_alias is None:
      raise util.Error(ALLOW_ROUTE_OVERLAP_WITHOUT_EXPLICIT_NETWORK_MODE)
    # Validate required flags are set.
    if options.cluster_ipv4_cidr is None:
      raise util.Error(ALLOW_ROUTE_OVERLAP_WITHOUT_CLUSTER_CIDR_ERROR_MSG)
    if options.enable_ip_alias and options.services_ipv4_cidr is None:
      raise util.Error(ALLOW_ROUTE_OVERLAP_WITHOUT_SERVICES_CIDR_ERROR_MSG)

    # Fill in corresponding field.
    if cluster.ipAllocationPolicy is None:
      policy = self.messages.IPAllocationPolicy(allowRouteOverlap=True)
      cluster.ipAllocationPolicy = policy
    else:
      cluster.ipAllocationPolicy.allowRouteOverlap = True

  def ParsePrivateClusterOptions(self, options, cluster):
    """Parses the options for Private Clusters."""
    if (options.enable_private_nodes is not None and
        options.private_cluster is not None):
      raise util.Error(ENABLE_PRIVATE_NODES_WITH_PRIVATE_CLUSTER_ERROR_MSG)

    if options.enable_private_nodes is None:
      options.enable_private_nodes = options.private_cluster

    if options.enable_private_nodes and not options.enable_ip_alias:
      raise util.Error(
          PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias', opt='enable-private-nodes'))

    if options.enable_private_endpoint and not options.enable_private_nodes:
      raise util.Error(
          PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-nodes',
              opt='enable-private-endpoint'))

    if options.master_ipv4_cidr and not options.enable_private_nodes:
      raise util.Error(
          PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-nodes', opt='master-ipv4-cidr'))

    if options.enable_private_nodes:
      config = self.messages.PrivateClusterConfig(
          enablePrivateNodes=options.enable_private_nodes,
          enablePrivateEndpoint=options.enable_private_endpoint,
          masterIpv4CidrBlock=options.master_ipv4_cidr)
      cluster.privateClusterConfig = config
    return cluster

  def ParseTpuOptions(self, options, cluster):
    """Parses the options for TPUs."""
    if options.enable_tpu and not options.enable_ip_alias:
      # Raises error if use --enable-tpu without --enable-ip-alias.
      raise util.Error(
          PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias', opt='enable-tpu'))

    if not options.enable_tpu and options.tpu_ipv4_cidr:
      # Raises error if use --tpu-ipv4-cidr without --enable-tpu.
      raise util.Error(
          PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-tpu', opt='tpu-ipv4-cidr'))

    if not options.enable_tpu and options.enable_tpu_service_networking:
      # Raises error if use --enable-tpu-service-networking without
      # --enable-tpu.
      raise util.Error(
          PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-tpu', opt='enable-tpu-service-networking'))

    if options.enable_tpu:
      cluster.enableTpu = options.enable_tpu
      if options.enable_tpu_service_networking:
        tpu_config = self.messages.TpuConfig(
            enabled=options.enable_tpu,
            ipv4CidrBlock=options.tpu_ipv4_cidr,
            useServiceNetworking=options.enable_tpu_service_networking)
        cluster.tpuConfig = tpu_config

  def ParseMasterAuthorizedNetworkOptions(self, options, cluster):
    """Parses the options for master authorized networks."""
    if (options.master_authorized_networks and
        not options.enable_master_authorized_networks):
      # Raise error if use --master-authorized-networks without
      # --enable-master-authorized-networks.
      raise util.Error(MISMATCH_AUTHORIZED_NETWORKS_ERROR_MSG)
    elif options.enable_master_authorized_networks is None:
      cluster.masterAuthorizedNetworksConfig = None
    elif not options.enable_master_authorized_networks:
      authorized_networks = self.messages.MasterAuthorizedNetworksConfig(
          enabled=False)
      cluster.masterAuthorizedNetworksConfig = authorized_networks
    else:
      authorized_networks = self.messages.MasterAuthorizedNetworksConfig(
          enabled=options.enable_master_authorized_networks)
      if options.master_authorized_networks:
        for network in options.master_authorized_networks:
          authorized_networks.cidrBlocks.append(
              self.messages.CidrBlock(cidrBlock=network))
      cluster.masterAuthorizedNetworksConfig = authorized_networks

    if options.enable_google_cloud_access is not None:
      if cluster.masterAuthorizedNetworksConfig is None:
        cluster.masterAuthorizedNetworksConfig = (
            self.messages.MasterAuthorizedNetworksConfig(enabled=False))

      cluster.masterAuthorizedNetworksConfig.gcpPublicCidrsAccessEnabled = (
          options.enable_google_cloud_access)

  def ParseClusterDNSOptions(self, options, is_update=False):
    """Parses the options for ClusterDNS."""
    if options.cluster_dns is None:
      if options.cluster_dns_scope:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='cluster-dns', opt='cluster-dns-scope'))
      if options.cluster_dns_domain:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='cluster-dns', opt='cluster-dns-domain'))

    # Check if the request has no flags related to DNS.
    if (
        options.cluster_dns is None
        and options.cluster_dns_scope is None
        and options.cluster_dns_domain is None
        and (not is_update or options.disable_additive_vpc_scope is None)
        and options.additive_vpc_scope_dns_domain is None
    ):
      return

    dns_config = self.messages.DNSConfig()

    if options.cluster_dns is not None:
      provider_enum = self.messages.DNSConfig.ClusterDnsValueValuesEnum
      if options.cluster_dns.lower() == 'clouddns':
        dns_config.clusterDns = provider_enum.CLOUD_DNS
      elif options.cluster_dns.lower() == 'kubedns':
        dns_config.clusterDns = provider_enum.KUBE_DNS
      else:  # 'default' or not specified
        dns_config.clusterDns = provider_enum.PLATFORM_DEFAULT

    if options.cluster_dns_scope is not None:
      scope_enum = self.messages.DNSConfig.ClusterDnsScopeValueValuesEnum
      if options.cluster_dns_scope.lower() == 'cluster':
        dns_config.clusterDnsScope = scope_enum.CLUSTER_SCOPE
      else:
        dns_config.clusterDnsScope = scope_enum.VPC_SCOPE

    if options.cluster_dns_domain is not None:
      dns_config.clusterDnsDomain = options.cluster_dns_domain

    if options.additive_vpc_scope_dns_domain is not None:
      dns_config.additiveVpcScopeDnsDomain = (
          options.additive_vpc_scope_dns_domain
      )

    if is_update and options.disable_additive_vpc_scope:
      dns_config.additiveVpcScopeDnsDomain = ''

    return dns_config

  def ParseGatewayOptions(self, options):
    """Parses the options for Gateway."""

    if options.gateway_api is None:
      return None
    gateway_config = self.messages.GatewayAPIConfig()
    channel_enum = self.messages.GatewayAPIConfig.ChannelValueValuesEnum
    if options.gateway_api.lower() == 'disabled':
      gateway_config.channel = channel_enum.CHANNEL_DISABLED
    elif options.gateway_api.lower() == 'standard':
      gateway_config.channel = channel_enum.CHANNEL_STANDARD
    else:
      gateway_config.channel = channel_enum.CHANNEL_DISABLED

    return gateway_config

  def CreateCluster(self, cluster_ref, options):
    """Handles CreateCluster options that are specific to a release track.

    Overridden in each release track.

    Args:
      cluster_ref: Name and location of the cluster.
      options: An UpdateClusterOptions containining the user-specified options.

    Returns:
      The operation to be executed.
    """
    cluster = self.CreateClusterCommon(cluster_ref, options)
    if (options.enable_autoprovisioning is not None or
        options.autoscaling_profile is not None):
      cluster.autoscaling = self.CreateClusterAutoscalingCommon(
          cluster_ref, options, False)
    if options.addons:
      # CloudRun is disabled by default.
      if any((v in options.addons) for v in CLOUDRUN_ADDONS):
        if not options.enable_stackdriver_kubernetes and (
            (options.monitoring is not None and
             SYSTEM not in options.monitoring) or
            (options.logging is not None and SYSTEM not in options.logging)):
          raise util.Error(CLOUDRUN_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG)
        if INGRESS not in options.addons:
          raise util.Error(CLOUDRUN_INGRESS_KUBERNETES_DISABLED_ERROR_MSG)
        load_balancer_type = _GetCloudRunLoadBalancerType(
            options, self.messages)
        cluster.addonsConfig.cloudRunConfig = self.messages.CloudRunConfig(
            disabled=False, loadBalancerType=load_balancer_type)

    if options.enable_master_global_access is not None:
      if cluster.privateClusterConfig is None:
        cluster.privateClusterConfig = self.messages.PrivateClusterConfig()
      cluster.privateClusterConfig.masterGlobalAccessConfig = \
          self.messages.PrivateClusterMasterGlobalAccessConfig(
              enabled=options.enable_master_global_access)

    req = self.messages.CreateClusterRequest(
        parent=ProjectLocation(cluster_ref.projectId, cluster_ref.zone),
        cluster=cluster)
    operation = self.client.projects_locations_clusters.Create(req)
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def CreateClusterAutoscalingCommon(self, cluster_ref, options, for_update):
    """Create cluster's autoscaling configuration.

    Args:
      cluster_ref: Cluster reference.
      options: Either CreateClusterOptions or UpdateClusterOptions.
      for_update: Is function executed for update operation.

    Returns:
      Cluster's autoscaling configuration.
    """

    # Patch cluster autoscaling if cluster_ref is provided.
    autoscaling = self.messages.ClusterAutoscaling()
    if for_update:
      cluster = self.GetCluster(cluster_ref) if cluster_ref else None
      if cluster and cluster.autoscaling:
        autoscaling.enableNodeAutoprovisioning = cluster.autoscaling.enableNodeAutoprovisioning
    else:
      autoscaling.enableNodeAutoprovisioning = options.enable_autoprovisioning

    resource_limits = []
    if options.autoprovisioning_config_file is not None:
      util.ValidateAutoprovisioningConfigFile(
          options.autoprovisioning_config_file)
      # Create using config file only.
      config = yaml.load(options.autoprovisioning_config_file)
      resource_limits = config.get(RESOURCE_LIMITS)
      service_account = config.get(SERVICE_ACCOUNT)
      scopes = config.get(SCOPES)
      max_surge_upgrade = None
      max_unavailable_upgrade = None
      upgrade_settings = config.get(UPGRADE_SETTINGS)
      if upgrade_settings:
        max_surge_upgrade = upgrade_settings.get(MAX_SURGE_UPGRADE)
        max_unavailable_upgrade = upgrade_settings.get(MAX_UNAVAILABLE_UPGRADE)
      management_settings = config.get(NODE_MANAGEMENT)
      enable_autoupgrade = None
      enable_autorepair = None
      if management_settings:
        enable_autoupgrade = management_settings.get(ENABLE_AUTO_UPGRADE)
        enable_autorepair = management_settings.get(ENABLE_AUTO_REPAIR)
      autoprovisioning_locations = \
          config.get(AUTOPROVISIONING_LOCATIONS)
      min_cpu_platform = config.get(MIN_CPU_PLATFORM)
      autoprovisioning_image_type = config.get(IMAGE_TYPE)
      boot_disk_kms_key = config.get(BOOT_DISK_KMS_KEY)
      disk_type = config.get(DISK_TYPE)
      disk_size_gb = config.get(DISK_SIZE_GB)
      shielded_instance_config = config.get(SHIELDED_INSTANCE_CONFIG)
      enable_secure_boot = None
      enable_integrity_monitoring = None
      if shielded_instance_config:
        enable_secure_boot = shielded_instance_config.get(ENABLE_SECURE_BOOT)
        enable_integrity_monitoring = \
            shielded_instance_config.get(ENABLE_INTEGRITY_MONITORING)
    else:
      resource_limits = self.ResourceLimitsFromFlags(options)
      service_account = options.autoprovisioning_service_account
      scopes = options.autoprovisioning_scopes
      max_surge_upgrade = options.autoprovisioning_max_surge_upgrade
      max_unavailable_upgrade = options.autoprovisioning_max_unavailable_upgrade
      enable_autoupgrade = options.enable_autoprovisioning_autoupgrade
      enable_autorepair = options.enable_autoprovisioning_autorepair
      autoprovisioning_locations = options.autoprovisioning_locations
      min_cpu_platform = options.autoprovisioning_min_cpu_platform
      autoprovisioning_image_type = options.autoprovisioning_image_type
      boot_disk_kms_key = None
      disk_type = None
      disk_size_gb = None
      enable_secure_boot = None
      enable_integrity_monitoring = None

    if options.enable_autoprovisioning is not None:
      autoscaling.enableNodeAutoprovisioning = options.enable_autoprovisioning
      if resource_limits is None:
        resource_limits = []
      autoscaling.resourceLimits = resource_limits
      if scopes is None:
        scopes = []
      management = None
      upgrade_settings = None
      if (max_surge_upgrade is not None or
          max_unavailable_upgrade is not None or
          options.enable_autoprovisioning_blue_green_upgrade or
          options.enable_autoprovisioning_surge_upgrade or
          options.autoprovisioning_standard_rollout_policy is not None or
          options.autoprovisioning_node_pool_soak_duration is not None):
        upgrade_settings = self.UpdateUpgradeSettingsForNAP(
            options, max_surge_upgrade, max_unavailable_upgrade)
      if enable_autorepair is not None or enable_autoupgrade is not None:
        management = (
            self.messages.NodeManagement(
                autoUpgrade=enable_autoupgrade, autoRepair=enable_autorepair))
      shielded_instance_config = None
      if (enable_secure_boot is not None or
          enable_integrity_monitoring is not None):
        shielded_instance_config = self.messages.ShieldedInstanceConfig()
        shielded_instance_config.enableSecureBoot = enable_secure_boot
        shielded_instance_config.enableIntegrityMonitoring = \
            enable_integrity_monitoring
      if for_update:
        autoscaling.autoprovisioningNodePoolDefaults = (
            self.messages.AutoprovisioningNodePoolDefaults(
                serviceAccount=service_account,
                oauthScopes=scopes,
                upgradeSettings=upgrade_settings,
                management=management,
                minCpuPlatform=min_cpu_platform,
                bootDiskKmsKey=boot_disk_kms_key,
                diskSizeGb=disk_size_gb,
                diskType=disk_type,
                imageType=autoprovisioning_image_type,
                shieldedInstanceConfig=shielded_instance_config,
            )
        )
      else:
        autoscaling.autoprovisioningNodePoolDefaults = (
            self.messages.AutoprovisioningNodePoolDefaults(
                serviceAccount=service_account,
                oauthScopes=scopes,
                upgradeSettings=upgrade_settings,
                management=management,
                minCpuPlatform=min_cpu_platform,
                bootDiskKmsKey=boot_disk_kms_key,
                diskSizeGb=disk_size_gb,
                diskType=disk_type,
                imageType=autoprovisioning_image_type,
                shieldedInstanceConfig=shielded_instance_config,
            )
        )
      if autoprovisioning_locations:
        autoscaling.autoprovisioningLocations = \
            sorted(autoprovisioning_locations)

    if options.autoscaling_profile is not None:
      autoscaling.autoscalingProfile = self.CreateAutoscalingProfileCommon(
          options)

    self.ValidateClusterAutoscaling(autoscaling, for_update)
    return autoscaling

  def UpdateUpgradeSettingsForNAP(self, options, max_surge, max_unavailable):
    """Updates upgrade setting for autoprovisioned node pool."""

    if options.enable_autoprovisioning_surge_upgrade and options.enable_autoprovisioning_blue_green_upgrade:
      raise util.Error(
          'UpgradeSettings must contain only one of: --enable-autoprovisioning-surge-upgrade, --enable-autoprovisioning-blue-green-upgrade'
      )

    upgrade_settings = self.messages.UpgradeSettings()
    upgrade_settings.maxSurge = max_surge
    upgrade_settings.maxUnavailable = max_unavailable
    if options.enable_autoprovisioning_surge_upgrade:
      upgrade_settings.strategy = self.messages.UpgradeSettings.StrategyValueValuesEnum.SURGE
    if options.enable_autoprovisioning_blue_green_upgrade:
      upgrade_settings.strategy = self.messages.UpgradeSettings.StrategyValueValuesEnum.BLUE_GREEN
    if options.autoprovisioning_standard_rollout_policy is not None or options.autoprovisioning_node_pool_soak_duration is not None:
      upgrade_settings.blueGreenSettings = self.UpdateBlueGreenSettingsForNAP(
          upgrade_settings, options)
    return upgrade_settings

  def UpdateBlueGreenSettingsForNAP(self, upgrade_settings, options):
    """Update blue green settings field in upgrade_settings for autoprovisioned node pool.
    """
    blue_green_settings = upgrade_settings.blueGreenSettings or self.messages.BlueGreenSettings(
    )
    if options.autoprovisioning_node_pool_soak_duration is not None:
      blue_green_settings.nodePoolSoakDuration = options.autoprovisioning_node_pool_soak_duration

    if options.autoprovisioning_standard_rollout_policy is not None:
      standard_rollout_policy = blue_green_settings.standardRolloutPolicy or self.messages.StandardRolloutPolicy(
      )

      if 'batch-node-count' in options.autoprovisioning_standard_rollout_policy and 'batch-percent' in options.autoprovisioning_standard_rollout_policy:
        raise util.Error(
            'Autoprovisioning StandardRolloutPolicy must contain only one of: batch-node-count, batch-percent'
        )

      standard_rollout_policy.batchPercentage = standard_rollout_policy.batchNodeCount = None
      if 'batch-node-count' in options.autoprovisioning_standard_rollout_policy:
        standard_rollout_policy.batchNodeCount = options.autoprovisioning_standard_rollout_policy[
            'batch-node-count']
      elif 'batch-percent' in options.autoprovisioning_standard_rollout_policy:
        standard_rollout_policy.batchPercentage = options.autoprovisioning_standard_rollout_policy[
            'batch-percent']

      if 'batch-soak-duration' in options.autoprovisioning_standard_rollout_policy:
        standard_rollout_policy.batchSoakDuration = options.autoprovisioning_standard_rollout_policy[
            'batch-soak-duration']
      blue_green_settings.standardRolloutPolicy = standard_rollout_policy
    return blue_green_settings

  def CreateAutoscalingProfileCommon(self, options):
    """Create and validate cluster's autoscaling profile configuration.

    Args:
      options: Either CreateClusterOptions or UpdateClusterOptions.

    Returns:
      Cluster's autoscaling profile configuration.
    """

    cluster_autoscaling = self.messages.ClusterAutoscaling
    profiles_enum = cluster_autoscaling.AutoscalingProfileValueValuesEnum
    valid_choices = [
        arg_utils.EnumNameToChoice(n)
        for n in profiles_enum.names()
        if n != 'profile-unspecified'
    ]
    return arg_utils.ChoiceToEnum(
        choice=arg_utils.EnumNameToChoice(options.autoscaling_profile),
        enum_type=profiles_enum,
        valid_choices=valid_choices)

  def ValidateClusterAutoscaling(self, autoscaling, for_update):
    """Validate cluster autoscaling configuration.

    Args:
      autoscaling: autoscaling configuration to be validated.
      for_update: Is function executed for update operation.

    Raises:
      Error if the new configuration is invalid.
    """
    if autoscaling.enableNodeAutoprovisioning:
      if not for_update or autoscaling.resourceLimits:
        cpu_found = any(
            limit.resourceType == 'cpu' for limit in autoscaling.resourceLimits)
        mem_found = any(limit.resourceType == 'memory'
                        for limit in autoscaling.resourceLimits)
        if not cpu_found or not mem_found:
          raise util.Error(NO_AUTOPROVISIONING_LIMITS_ERROR_MSG)
        defaults = autoscaling.autoprovisioningNodePoolDefaults
        if defaults:
          if defaults.upgradeSettings:
            max_surge_found = defaults.upgradeSettings.maxSurge is not None
            max_unavailable_found = defaults.upgradeSettings.maxUnavailable is not None
            if max_unavailable_found != max_surge_found:
              raise util.Error(BOTH_AUTOPROVISIONING_UPGRADE_SETTINGS_ERROR_MSG)
          if defaults.management:
            auto_upgrade_found = defaults.management.autoUpgrade is not None
            auto_repair_found = defaults.management.autoRepair is not None
            if auto_repair_found != auto_upgrade_found:
              raise util.Error(
                  BOTH_AUTOPROVISIONING_MANAGEMENT_SETTINGS_ERROR_MSG)
          if defaults.shieldedInstanceConfig:
            secure_boot_found = defaults.shieldedInstanceConfig.enableSecureBoot is not None
            integrity_monitoring_found = defaults.shieldedInstanceConfig.enableIntegrityMonitoring is not None
            if secure_boot_found != integrity_monitoring_found:
              raise util.Error(
                  BOTH_AUTOPROVISIONING_SHIELDED_INSTANCE_SETTINGS_ERROR_MSG)
    elif autoscaling.resourceLimits:
      raise util.Error(LIMITS_WITHOUT_AUTOPROVISIONING_MSG)
    elif autoscaling.autoprovisioningNodePoolDefaults and \
        (autoscaling.autoprovisioningNodePoolDefaults.serviceAccount or
         autoscaling.autoprovisioningNodePoolDefaults.oauthScopes):
      raise util.Error(DEFAULTS_WITHOUT_AUTOPROVISIONING_MSG)

  def _GetClusterTelemetryType(self, options, logging_service,
                               monitoring_service):
    """Gets the cluster telemetry from create options."""
    # If enable_stackdriver_kubernetes is set to false cluster telemetry
    # will be set to DISABLED.
    if (options.enable_stackdriver_kubernetes is not None and
        not options.enable_stackdriver_kubernetes):
      return self.messages.ClusterTelemetry.TypeValueValuesEnum.DISABLED

    # If either logging service or monitoring service is explicitly disabled we
    # do not set the cluster telemtry.
    if (options.enable_stackdriver_kubernetes and
        (logging_service == 'none' or monitoring_service == 'none')):
      return None

    # When enable_stackdriver_kubernetes is set to true and neither logging nor
    # monitoring service are explicitly disabled we set the Cluster Telemetry
    # to ENABLED.
    if (options.enable_stackdriver_kubernetes and logging_service != 'none' and
        monitoring_service != 'none'):
      return self.messages.ClusterTelemetry.TypeValueValuesEnum.ENABLED

    # When enable_logging_monitoring_system_only is set to true we set the
    # telemetry to SYSTEM_ONLY. In case of SYSTEM_ONLY it's not possible to
    # disable either logging or monitoring.
    if options.enable_logging_monitoring_system_only:
      return self.messages.ClusterTelemetry.TypeValueValuesEnum.SYSTEM_ONLY
    return None

  def ResourceLimitsFromFlags(self, options):
    """Create cluster's autoscaling resource limits from command line flags.

    Args:
      options: Either CreateClusterOptions or UpdateClusterOptions.

    Returns:
      Cluster's new autoscaling resource limits.
    """
    new_resource_limits = []
    if options.min_cpu is not None or options.max_cpu is not None:
      new_resource_limits.append(
          self.messages.ResourceLimit(
              resourceType='cpu',
              minimum=options.min_cpu,
              maximum=options.max_cpu))
    if options.min_memory is not None or options.max_memory is not None:
      new_resource_limits.append(
          self.messages.ResourceLimit(
              resourceType='memory',
              minimum=options.min_memory,
              maximum=options.max_memory))
    if options.max_accelerator is not None:
      accelerator_type = options.max_accelerator.get('type')
      min_count = 0
      if options.min_accelerator is not None:
        if options.min_accelerator.get('type') != accelerator_type:
          raise util.Error(MISMATCH_ACCELERATOR_TYPE_LIMITS_ERROR_MSG)
        min_count = options.min_accelerator.get('count', 0)
      new_resource_limits.append(
          self.messages.ResourceLimit(
              resourceType=options.max_accelerator.get('type'),
              minimum=min_count,
              maximum=options.max_accelerator.get('count', 0)))
    return new_resource_limits

  def UpdateClusterCommon(self, cluster_ref, options):
    """Returns an UpdateCluster operation."""

    update = None
    if not options.version:
      options.version = '-'
    if options.update_nodes:
      update = self.messages.ClusterUpdate(
          desiredNodeVersion=options.version,
          desiredNodePoolId=options.node_pool,
          desiredImageType=options.image_type,
          desiredImage=options.image,
          desiredImageProject=options.image_project)
      # security_profile may be set in upgrade command
      if options.security_profile is not None:
        update.securityProfile = self.messages.SecurityProfile(
            name=options.security_profile)
    elif options.update_master:
      update = self.messages.ClusterUpdate(desiredMasterVersion=options.version)
      # security_profile may be set in upgrade command
      if options.security_profile is not None:
        update.securityProfile = self.messages.SecurityProfile(
            name=options.security_profile)
    elif options.enable_stackdriver_kubernetes:
      update = self.messages.ClusterUpdate()
      update.desiredLoggingService = 'logging.googleapis.com/kubernetes'
      update.desiredMonitoringService = 'monitoring.googleapis.com/kubernetes'
    elif options.enable_stackdriver_kubernetes is not None:
      update = self.messages.ClusterUpdate()
      update.desiredLoggingService = 'none'
      update.desiredMonitoringService = 'none'
    elif options.monitoring_service or options.logging_service:
      update = self.messages.ClusterUpdate()
      if options.monitoring_service:
        update.desiredMonitoringService = options.monitoring_service
      if options.logging_service:
        update.desiredLoggingService = options.logging_service
    elif (options.logging or options.monitoring or
          options.enable_managed_prometheus or
          options.disable_managed_prometheus or
          options.enable_dataplane_v2_metrics or
          options.disable_dataplane_v2_metrics or
          options.enable_dataplane_v2_flow_observability or
          options.disable_dataplane_v2_flow_observability or
          options.dataplane_v2_observability_mode):
      logging = _GetLoggingConfig(options, self.messages)
      # Fix incorrectly omitting required field.
      if ((options.dataplane_v2_observability_mode or
           options.enable_dataplane_v2_flow_observability or
           options.disable_dataplane_v2_flow_observability) and
          options.enable_dataplane_v2_metrics is None and
          options.disable_dataplane_v2_metrics is None):
        cluster = self.GetCluster(cluster_ref)
        if (cluster and cluster.monitoringConfig and
            cluster.monitoringConfig.advancedDatapathObservabilityConfig):
          if cluster.monitoringConfig.advancedDatapathObservabilityConfig.enableMetrics:
            options.enable_dataplane_v2_metrics = True
          else:
            options.disable_dataplane_v2_metrics = True
      monitoring = _GetMonitoringConfig(options, self.messages)
      update = self.messages.ClusterUpdate()
      if logging:
        update.desiredLoggingConfig = logging
      if monitoring:
        update.desiredMonitoringConfig = monitoring
    elif options.disable_addons:
      disable_node_local_dns = options.disable_addons.get(NODELOCALDNS)
      addons = self._AddonsConfig(
          disable_ingress=options.disable_addons.get(INGRESS),
          disable_hpa=options.disable_addons.get(HPA),
          disable_dashboard=options.disable_addons.get(DASHBOARD),
          disable_network_policy=options.disable_addons.get(NETWORK_POLICY),
          enable_node_local_dns=not disable_node_local_dns if \
             disable_node_local_dns is not None else None)
      if options.disable_addons.get(CONFIGCONNECTOR) is not None:
        addons.configConnectorConfig = (
            self.messages.ConfigConnectorConfig(
                enabled=(not options.disable_addons.get(CONFIGCONNECTOR))))
      if options.disable_addons.get(GCEPDCSIDRIVER) is not None:
        addons.gcePersistentDiskCsiDriverConfig = (
            self.messages.GcePersistentDiskCsiDriverConfig(
                enabled=not options.disable_addons.get(GCEPDCSIDRIVER)))
      if options.disable_addons.get(GCPFILESTORECSIDRIVER) is not None:
        addons.gcpFilestoreCsiDriverConfig = self.messages.GcpFilestoreCsiDriverConfig(
            enabled=not options.disable_addons.get(GCPFILESTORECSIDRIVER))
      if options.disable_addons.get(GCSFUSECSIDRIVER) is not None:
        addons.gcsFuseCsiDriverConfig = self.messages.GcsFuseCsiDriverConfig(
            enabled=not options.disable_addons.get(GCSFUSECSIDRIVER))
      if options.disable_addons.get(STATEFULHA) is not None:
        addons.statefulHaConfig = (
            self.messages.StatefulHAConfig(
                enabled=not options.disable_addons.get(STATEFULHA)))
      if options.disable_addons.get(PARALLELSTORECSIDRIVER) is not None:
        addons.parallelstoreCsiDriverConfig = (
            self.messages.ParallelstoreCsiDriverConfig(
                enabled=not options.disable_addons.get(PARALLELSTORECSIDRIVER)
            )
        )
      if options.disable_addons.get(BACKUPRESTORE) is not None:
        addons.gkeBackupAgentConfig = (
            self.messages.GkeBackupAgentConfig(
                enabled=not options.disable_addons.get(BACKUPRESTORE)))
      update = self.messages.ClusterUpdate(desiredAddonsConfig=addons)
    elif options.enable_autoscaling is not None:
      # For update, we can either enable or disable.
      autoscaling = self.messages.NodePoolAutoscaling(
          enabled=options.enable_autoscaling)
      if options.enable_autoscaling:
        autoscaling.minNodeCount = options.min_nodes
        autoscaling.maxNodeCount = options.max_nodes
        autoscaling.totalMinNodeCount = options.total_min_nodes
        autoscaling.totalMaxNodeCount = options.total_max_nodes
        if options.location_policy is not None:
          autoscaling.locationPolicy = LocationPolicyEnumFromString(
              self.messages, options.location_policy)
      update = self.messages.ClusterUpdate(
          desiredNodePoolId=options.node_pool,
          desiredNodePoolAutoscaling=autoscaling)
    elif options.locations:
      update = self.messages.ClusterUpdate(desiredLocations=options.locations)
    elif options.enable_master_authorized_networks is not None:
      # For update, we can either enable or disable.
      authorized_networks = self.messages.MasterAuthorizedNetworksConfig(
          enabled=options.enable_master_authorized_networks)
      if options.master_authorized_networks:
        for network in options.master_authorized_networks:
          authorized_networks.cidrBlocks.append(
              self.messages.CidrBlock(cidrBlock=network))
      update = self.messages.ClusterUpdate(
          desiredMasterAuthorizedNetworksConfig=authorized_networks)
    elif options.enable_autoprovisioning is not None or \
         options.autoscaling_profile is not None:
      autoscaling = self.CreateClusterAutoscalingCommon(cluster_ref, options,
                                                        True)
      update = self.messages.ClusterUpdate(
          desiredClusterAutoscaling=autoscaling)
    elif options.enable_pod_security_policy is not None:
      config = self.messages.PodSecurityPolicyConfig(
          enabled=options.enable_pod_security_policy)
      update = self.messages.ClusterUpdate(
          desiredPodSecurityPolicyConfig=config)
    elif options.enable_vertical_pod_autoscaling is not None:
      vertical_pod_autoscaling = self.messages.VerticalPodAutoscaling(
          enabled=options.enable_vertical_pod_autoscaling)
      update = self.messages.ClusterUpdate(
          desiredVerticalPodAutoscaling=vertical_pod_autoscaling)
    elif options.resource_usage_bigquery_dataset is not None:
      export_config = self.messages.ResourceUsageExportConfig(
          bigqueryDestination=self.messages.BigQueryDestination(
              datasetId=options.resource_usage_bigquery_dataset))
      if options.enable_network_egress_metering:
        export_config.enableNetworkEgressMetering = True
      if options.enable_resource_consumption_metering is not None:
        export_config.consumptionMeteringConfig = \
            self.messages.ConsumptionMeteringConfig(
                enabled=options.enable_resource_consumption_metering)
      update = self.messages.ClusterUpdate(
          desiredResourceUsageExportConfig=export_config)
    elif options.enable_network_egress_metering is not None:
      raise util.Error(ENABLE_NETWORK_EGRESS_METERING_ERROR_MSG)
    elif options.enable_resource_consumption_metering is not None:
      raise util.Error(ENABLE_RESOURCE_CONSUMPTION_METERING_ERROR_MSG)
    elif options.clear_resource_usage_bigquery_dataset is not None:
      export_config = self.messages.ResourceUsageExportConfig()
      update = self.messages.ClusterUpdate(
          desiredResourceUsageExportConfig=export_config)
    elif options.security_profile is not None:
      # security_profile is set in update command
      security_profile = self.messages.SecurityProfile(
          name=options.security_profile)
      update = self.messages.ClusterUpdate(securityProfile=security_profile)
    elif options.enable_intra_node_visibility is not None:
      intra_node_visibility_config = self.messages.IntraNodeVisibilityConfig(
          enabled=options.enable_intra_node_visibility)
      update = self.messages.ClusterUpdate(
          desiredIntraNodeVisibilityConfig=intra_node_visibility_config)
    elif options.enable_master_global_access is not None:
      # For update, we can either enable or disable.
      master_global_access_config = self.messages.PrivateClusterMasterGlobalAccessConfig(
          enabled=options.enable_master_global_access)
      private_cluster_config = self.messages.PrivateClusterConfig(
          masterGlobalAccessConfig=master_global_access_config)
      update = self.messages.ClusterUpdate(
          desiredPrivateClusterConfig=private_cluster_config)

    if (options.security_profile is not None and
        options.security_profile_runtime_rules is not None):
      update.securityProfile.disableRuntimeRules = \
          not options.security_profile_runtime_rules
    if (options.master_authorized_networks and
        not options.enable_master_authorized_networks):
      # Raise error if use --master-authorized-networks without
      # --enable-master-authorized-networks.
      raise util.Error(MISMATCH_AUTHORIZED_NETWORKS_ERROR_MSG)

    if options.database_encryption_key:
      update = self.messages.ClusterUpdate(
          desiredDatabaseEncryption=self.messages.DatabaseEncryption(
              keyName=options.database_encryption_key,
              state=self.messages.DatabaseEncryption.StateValueValuesEnum
              .ENCRYPTED))

    elif options.disable_database_encryption:
      update = self.messages.ClusterUpdate(
          desiredDatabaseEncryption=self.messages.DatabaseEncryption(
              state=self.messages.DatabaseEncryption.StateValueValuesEnum
              .DECRYPTED))

    if options.enable_shielded_nodes is not None:
      update = self.messages.ClusterUpdate(
          desiredShieldedNodes=self.messages.ShieldedNodes(
              enabled=options.enable_shielded_nodes))
    if options.enable_tpu is not None:
      update = self.messages.ClusterUpdate(
          desiredTpuConfig=_GetTpuConfigForClusterUpdate(
              options, self.messages))

    if options.release_channel is not None:
      update = self.messages.ClusterUpdate(
          desiredReleaseChannel=_GetReleaseChannel(options, self.messages))

    if options.disable_default_snat is not None:
      disable_default_snat = self.messages.DefaultSnatStatus(
          disabled=options.disable_default_snat)
      update = self.messages.ClusterUpdate(
          desiredDefaultSnatStatus=disable_default_snat)
    if options.enable_l4_ilb_subsetting is not None:
      ilb_subsettting_config = self.messages.ILBSubsettingConfig(
          enabled=options.enable_l4_ilb_subsetting)
      update = self.messages.ClusterUpdate(
          desiredL4ilbSubsettingConfig=ilb_subsettting_config)
    if options.private_ipv6_google_access_type is not None:
      update = self.messages.ClusterUpdate(
          desiredPrivateIpv6GoogleAccess=util
          .GetPrivateIpv6GoogleAccessTypeMapperForUpdate(
              self.messages, hidden=False).GetEnumForChoice(
                  options.private_ipv6_google_access_type))

    dns_config = self.ParseClusterDNSOptions(options, is_update=True)
    if dns_config is not None:
      update = self.messages.ClusterUpdate(desiredDnsConfig=dns_config)

    gateway_config = self.ParseGatewayOptions(options)
    if gateway_config is not None:
      update = self.messages.ClusterUpdate(
          desiredGatewayApiConfig=gateway_config)

    if options.notification_config is not None:
      update = self.messages.ClusterUpdate(
          desiredNotificationConfig=_GetNotificationConfigForClusterUpdate(
              options, self.messages))

    if options.disable_autopilot is not None:
      update = self.messages.ClusterUpdate(
          desiredAutopilot=self.messages.Autopilot(enabled=False))

    if options.security_group is not None:
      update = self.messages.ClusterUpdate(
          desiredAuthenticatorGroupsConfig=self.messages
          .AuthenticatorGroupsConfig(
              enabled=True, securityGroup=options.security_group))

    if options.enable_gcfs is not None:
      update = self.messages.ClusterUpdate(
          desiredGcfsConfig=self.messages.GcfsConfig(
              enabled=options.enable_gcfs))

    if options.autoprovisioning_network_tags is not None:
      update = self.messages.ClusterUpdate(
          desiredNodePoolAutoConfigNetworkTags=self.messages.NetworkTags(
              tags=options.autoprovisioning_network_tags))

    if options.autoprovisioning_resource_manager_tags is not None:
      tags = options.autoprovisioning_resource_manager_tags
      rm_tags = self._ResourceManagerTags(tags)
      update = self.messages.ClusterUpdate(
          desiredNodePoolAutoConfigResourceManagerTags=rm_tags)

    if options.enable_image_streaming is not None:
      update = self.messages.ClusterUpdate(
          desiredGcfsConfig=self.messages.GcfsConfig(
              enabled=options.enable_image_streaming))

    if options.enable_mesh_certificates is not None:
      update = self.messages.ClusterUpdate(
          desiredMeshCertificates=self.messages.MeshCertificates(
              enableCertificates=options.enable_mesh_certificates))

    if options.maintenance_interval is not None:
      update = self.messages.ClusterUpdate(
          desiredStableFleetConfig=_GetStableFleetConfig(
              options, self.messages))

    if options.enable_service_externalips is not None:
      update = self.messages.ClusterUpdate(
          desiredServiceExternalIpsConfig=self.messages
          .ServiceExternalIPsConfig(enabled=options.enable_service_externalips))

    if options.enable_identity_service is not None:
      update = self.messages.ClusterUpdate(
          desiredIdentityServiceConfig=self.messages.IdentityServiceConfig(
              enabled=options.enable_identity_service))

    if options.enable_workload_config_audit is not None or options.enable_workload_vulnerability_scanning is not None:
      protect_config = self.messages.ProtectConfig()
      if options.enable_workload_config_audit is not None:
        protect_config.workloadConfig = self.messages.WorkloadConfig()
        if options.enable_workload_config_audit:
          protect_config.workloadConfig.auditMode = (
              self.messages.WorkloadConfig.AuditModeValueValuesEnum.BASIC)
        else:
          protect_config.workloadConfig.auditMode = (
              self.messages.WorkloadConfig.AuditModeValueValuesEnum.DISABLED)

      if options.enable_workload_vulnerability_scanning is not None:
        if options.enable_workload_vulnerability_scanning:
          protect_config.workloadVulnerabilityMode = (
              self.messages.ProtectConfig
              .WorkloadVulnerabilityModeValueValuesEnum.BASIC)
        else:
          protect_config.workloadVulnerabilityMode = (
              self.messages.ProtectConfig
              .WorkloadVulnerabilityModeValueValuesEnum.DISABLED)
      update = self.messages.ClusterUpdate(desiredProtectConfig=protect_config)

    if options.pod_autoscaling_direct_metrics_opt_in is not None:
      pod_autoscaling_config = self.messages.PodAutoscaling(
          directMetricsOptIn=options.pod_autoscaling_direct_metrics_opt_in)
      update = self.messages.ClusterUpdate(
          desiredPodAutoscaling=pod_autoscaling_config)

    if options.enable_private_endpoint is not None:
      update = self.messages.ClusterUpdate(
          desiredEnablePrivateEndpoint=options.enable_private_endpoint)

    if options.logging_variant is not None:
      logging_config = self.messages.NodePoolLoggingConfig()
      logging_config.variantConfig = self.messages.LoggingVariantConfig(
          variant=VariantConfigEnumFromString(
              self.messages, options.logging_variant
          )
      )
      update = self.messages.ClusterUpdate(
          desiredNodePoolLoggingConfig=logging_config
      )

    if (
        options.additional_pod_ipv4_ranges
        or options.removed_additional_pod_ipv4_ranges
    ):
      update = self.messages.ClusterUpdate()
      if options.additional_pod_ipv4_ranges:
        update.additionalPodRangesConfig = (
            self.messages.AdditionalPodRangesConfig(
                podRangeNames=options.additional_pod_ipv4_ranges))
      if options.removed_additional_pod_ipv4_ranges:
        update.removedAdditionalPodRangesConfig = (
            self.messages.AdditionalPodRangesConfig(
                podRangeNames=options.removed_additional_pod_ipv4_ranges))

    if options.stack_type is not None:
      update = self.messages.ClusterUpdate(
          desiredStackType=util.GetUpdateStackTypeMapper(
              self.messages).GetEnumForChoice(options.stack_type))

    if options.enable_cost_allocation is not None:
      update = self.messages.ClusterUpdate(
          desiredCostManagementConfig=self.messages.CostManagementConfig(
              enabled=options.enable_cost_allocation))

    if options.enable_fleet:
      update = self.messages.ClusterUpdate(
          desiredFleet=self.messages.Fleet(project=cluster_ref.projectId))

    if options.fleet_project:
      update = self.messages.ClusterUpdate(
          desiredFleet=self.messages.Fleet(project=options.fleet_project))

    if options.enable_k8s_beta_apis is not None:
      config_obj = self.messages.K8sBetaAPIConfig()
      config_obj.enabledApis = options.enable_k8s_beta_apis
      update = self.messages.ClusterUpdate(desiredK8sBetaApis=config_obj)

    if options.clear_fleet_project:
      update = self.messages.ClusterUpdate(
          desiredFleet=self.messages.Fleet(project=''))

    if options.enable_security_posture is not None:
      security_posture_config = self.messages.SecurityPostureConfig()
      if options.enable_security_posture:
        security_posture_config.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.BASIC
        )
      else:
        security_posture_config.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.DISABLED
        )
      update = self.messages.ClusterUpdate(
          desiredSecurityPostureConfig=security_posture_config)

    if options.security_posture is not None:
      security_posture_config = self.messages.SecurityPostureConfig()
      if options.security_posture.lower() == 'standard':
        security_posture_config.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.BASIC
        )
      elif options.security_posture.lower() == 'disabled':
        security_posture_config.mode = (
            self.messages.SecurityPostureConfig.ModeValueValuesEnum.DISABLED
        )
      else:
        raise util.Error(
            SECURITY_POSTURE_MODE_NOT_SUPPORTED.format(
                mode=options.security_posture.lower()
            )
        )
      update = self.messages.ClusterUpdate(
          desiredSecurityPostureConfig=security_posture_config
      )

    if options.workload_vulnerability_scanning is not None:
      security_posture_config = self.messages.SecurityPostureConfig()
      if options.workload_vulnerability_scanning.lower() == 'standard':
        security_posture_config.vulnerabilityMode = (
            self.messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum.VULNERABILITY_BASIC
        )
      elif options.workload_vulnerability_scanning.lower() == 'disabled':
        security_posture_config.vulnerabilityMode = (
            self.messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum.VULNERABILITY_DISABLED
        )
      elif options.workload_vulnerability_scanning.lower() == 'enterprise':
        security_posture_config.vulnerabilityMode = (
            self.messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum.VULNERABILITY_ENTERPRISE
        )
      else:
        raise util.Error(
            WORKLOAD_VULNERABILITY_SCANNING_MODE_NOT_SUPPORTED.format(
                mode=options.workload_vulnerability_scanning.lower()
            )
        )
      update = self.messages.ClusterUpdate(
          desiredSecurityPostureConfig=security_posture_config
      )

    if options.enable_runtime_vulnerability_insight is not None:
      runtime_vulnerability_insight_config = (
          self.messages.RuntimeVulnerabilityInsightConfig())
      if options.enable_runtime_vulnerability_insight:
        runtime_vulnerability_insight_config.mode = (
            self.messages.RuntimeVulnerabilityInsightConfig.ModeValueValuesEnum.PREMIUM_VULNERABILITY_SCAN
        )
      else:
        runtime_vulnerability_insight_config.mode = (
            self.messages.RuntimeVulnerabilityInsightConfig.ModeValueValuesEnum.DISABLED
        )
      update = self.messages.ClusterUpdate(
          desiredRuntimeVulnerabilityInsightConfig=(
              runtime_vulnerability_insight_config))

    if options.network_performance_config:
      perf = self._GetClusterNetworkPerformanceConfig(options)
      update = self.messages.ClusterUpdate(
          desiredNetworkPerformanceConfig=perf)

    if options.workload_policies is not None:
      workload_policies = self.messages.WorkloadPolicyConfig()
      if options.workload_policies == 'allow-net-admin':
        workload_policies.allowNetAdmin = True
      update = self.messages.ClusterUpdate(
          desiredAutopilotWorkloadPolicyConfig=workload_policies
      )

    if options.remove_workload_policies is not None:
      workload_policies = self.messages.WorkloadPolicyConfig()
      if options.remove_workload_policies == 'allow-net-admin':
        workload_policies.allowNetAdmin = False
      update = self.messages.ClusterUpdate(
          desiredAutopilotWorkloadPolicyConfig=workload_policies
      )

    if options.host_maintenance_interval is not None:
      update = self.messages.ClusterUpdate(
          desiredHostMaintenancePolicy=_GetHostMaintenancePolicy(
              options, self.messages)
      )

    if options.in_transit_encryption is not None:
      update = self.messages.ClusterUpdate(
          desiredInTransitEncryptionConfig=util.GetUpdateInTransitEncryptionConfigMapper(
              self.messages
          ).GetEnumForChoice(
              options.in_transit_encryption
          )
      )

    if options.enable_multi_networking is not None:
      update = self.messages.ClusterUpdate(
          desiredEnableMultiNetworking=options.enable_multi_networking)

    if options.containerd_config_from_file is not None:
      update = self.messages.ClusterUpdate(
          desiredContainerdConfig=self.messages.ContainerdConfig())
      util.LoadContainerdConfigFromYAML(
          update.desiredContainerdConfig,
          options.containerd_config_from_file,
          self.messages,
      )

    if options.enable_secret_manager is not None:
      update = self.messages.ClusterUpdate(
          desiredSecretManagerConfig=self.messages.SecretManagerConfig(
              enabled=options.enable_secret_manager
          )
      )

    if options.enable_cilium_clusterwide_network_policy is not None:
      update = self.messages.ClusterUpdate(
          desiredEnableCiliumClusterwideNetworkPolicy=(
              options.enable_cilium_clusterwide_network_policy
          )
      )

    if options.enable_fqdn_network_policy is not None:
      update = self.messages.ClusterUpdate(
          desiredEnableFqdnNetworkPolicy=options.enable_fqdn_network_policy)

    return update

  def UpdateCluster(self, cluster_ref, options):
    """Handles UpdateCluster options that are specific to a release track.

    Overridden in each release track.

    Args:
      cluster_ref: Name and location of the cluster.
      options: An UpdateClusterOptions containining the user-specified options.

    Returns:
      The operation to be executed.
    """

    update = self.UpdateClusterCommon(cluster_ref, options)

    if options.workload_pool:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              workloadPool=options.workload_pool))
    elif options.disable_workload_identity:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              workloadPool=''))

    if not update:
      # if reached here, it's possible:
      # - someone added update flags but not handled
      # - none of the update flags specified from command line
      # so raise an error with readable message like:
      #   Nothing to update
      # to catch this error.
      raise util.Error(NOTHING_TO_UPDATE_ERROR_MSG)

    if options.disable_addons is not None:
      if any(
          (options.disable_addons.get(v) is not None) for v in CLOUDRUN_ADDONS):
        load_balancer_type = _GetCloudRunLoadBalancerType(
            options, self.messages)
        update.desiredAddonsConfig.cloudRunConfig = (
            self.messages.CloudRunConfig(
                disabled=any(
                    options.disable_addons.get(v) or False
                    for v in CLOUDRUN_ADDONS),
                loadBalancerType=load_balancer_type))

    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            update=update))

    return self.ParseOperation(op.name, cluster_ref.zone)

  def SetLoggingService(self, cluster_ref, logging_service):
    op = self.client.projects_locations_clusters.SetLogging(
        self.messages.SetLoggingServiceRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            loggingService=logging_service))
    return self.ParseOperation(op.name, cluster_ref.zone)

  def SetLegacyAuthorization(self, cluster_ref, enable_legacy_authorization):
    op = self.client.projects_locations_clusters.SetLegacyAbac(
        self.messages.SetLegacyAbacRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            enabled=bool(enable_legacy_authorization)))
    return self.ParseOperation(op.name, cluster_ref.zone)

  def _AddonsConfig(self,
                    disable_ingress=None,
                    disable_hpa=None,
                    disable_dashboard=None,
                    disable_network_policy=None,
                    enable_node_local_dns=None,
                    enable_gcepd_csi_driver=None,
                    enable_filestore_csi_driver=None,
                    enable_application_manager=None,
                    enable_cloud_build=None,
                    enable_backup_restore=None,
                    enable_gcsfuse_csi_driver=None,
                    enable_stateful_ha=None,
                    enable_parallelstore_csi_driver=None):
    """Generates an AddonsConfig object given specific parameters.

    Args:
      disable_ingress: whether to disable the GCLB ingress controller.
      disable_hpa: whether to disable the horizontal pod autoscaling controller.
      disable_dashboard: whether to disable the Kubernetes Dashboard.
      disable_network_policy: whether to disable NetworkPolicy enforcement.
      enable_node_local_dns: whether to enable NodeLocalDNS cache.
      enable_gcepd_csi_driver: whether to enable GcePersistentDiskCsiDriver.
      enable_filestore_csi_driver: wherher to enable GcpFilestoreCsiDriver.
      enable_application_manager: whether to enable ApplicationManager.
      enable_cloud_build: whether to enable CloudBuild.
      enable_backup_restore: whether to enable BackupRestore.
      enable_gcsfuse_csi_driver: whether to enable GcsFuseCsiDriver.
      enable_stateful_ha: whether to enable StatefulHA addon.
      enable_parallelstore_csi_driver: whether to enable ParallelstoreCsiDriver.

    Returns:
      An AddonsConfig object that contains the options defining what addons to
      run in the cluster.
    """
    addons = self.messages.AddonsConfig()
    if disable_ingress is not None:
      addons.httpLoadBalancing = self.messages.HttpLoadBalancing(
          disabled=disable_ingress)
    if disable_hpa is not None:
      addons.horizontalPodAutoscaling = self.messages.HorizontalPodAutoscaling(
          disabled=disable_hpa)
    if disable_dashboard is not None:
      addons.kubernetesDashboard = self.messages.KubernetesDashboard(
          disabled=disable_dashboard)
    # Network policy is disabled by default.
    if disable_network_policy is not None:
      addons.networkPolicyConfig = self.messages.NetworkPolicyConfig(
          disabled=disable_network_policy)
    if enable_node_local_dns is not None:
      addons.dnsCacheConfig = self.messages.DnsCacheConfig(
          enabled=enable_node_local_dns)
    if enable_gcepd_csi_driver:
      addons.gcePersistentDiskCsiDriverConfig = self.messages.GcePersistentDiskCsiDriverConfig(
          enabled=True)
    if enable_filestore_csi_driver:
      addons.gcpFilestoreCsiDriverConfig = self.messages.GcpFilestoreCsiDriverConfig(
          enabled=True)
    if enable_application_manager:
      addons.kalmConfig = self.messages.KalmConfig(enabled=True)
    if enable_cloud_build:
      addons.cloudBuildConfig = self.messages.CloudBuildConfig(enabled=True)
    if enable_backup_restore:
      addons.gkeBackupAgentConfig = self.messages.GkeBackupAgentConfig(
          enabled=True)
    if enable_gcsfuse_csi_driver:
      addons.gcsFuseCsiDriverConfig = self.messages.GcsFuseCsiDriverConfig(
          enabled=True)
    if enable_stateful_ha:
      addons.statefulHaConfig = self.messages.StatefulHAConfig(enabled=True)
    if enable_parallelstore_csi_driver:
      addons.parallelstoreCsiDriverConfig = (
          self.messages.ParallelstoreCsiDriverConfig(enabled=True)
      )

    return addons

  def _AddLocalSSDVolumeConfigsToNodeConfig(self, node_config, options):
    """Add LocalSSDVolumeConfigs to nodeConfig."""
    if not options.local_ssd_volume_configs:
      return
    format_enum = self.messages.LocalSsdVolumeConfig.FormatValueValuesEnum
    local_ssd_volume_configs_list = []
    for config in options.local_ssd_volume_configs:
      count = int(config['count'])
      ssd_type = config['type'].lower()
      if config['format'].lower() == 'fs':
        ssd_format = format_enum.FS
      elif config['format'].lower() == 'block':
        ssd_format = format_enum.BLOCK
      else:
        raise util.Error(
            LOCAL_SSD_INCORRECT_FORMAT_ERROR_MSG.format(
                err_format=config['format']))
      local_ssd_volume_configs_list.append(
          self.messages.LocalSsdVolumeConfig(
              count=count, type=ssd_type, format=ssd_format))
    node_config.localSsdVolumeConfigs = local_ssd_volume_configs_list

  def _AddEphemeralStorageToNodeConfig(self, node_config, options):
    if options.ephemeral_storage is None:
      return
    config = options.ephemeral_storage
    count = None
    if 'local-ssd-count' in config:
      count = config['local-ssd-count']
    node_config.ephemeralStorageConfig = self.messages.EphemeralStorageConfig(
        localSsdCount=count)

  def _AddEphemeralStorageLocalSsdToNodeConfig(self, node_config, options):
    if options.ephemeral_storage_local_ssd is None:
      return
    config = options.ephemeral_storage_local_ssd
    count = None
    if 'count' in config:
      count = config['count']
    node_config.ephemeralStorageLocalSsdConfig = self.messages.EphemeralStorageLocalSsdConfig(
        localSsdCount=count)

  def _AddLocalNvmeSsdBlockToNodeConfig(self, node_config, options):
    if options.local_nvme_ssd_block is None:
      return
    config = options.local_nvme_ssd_block
    count = None
    if 'count' in config:
      count = config['count']
    node_config.localNvmeSsdBlockConfig = self.messages.LocalNvmeSsdBlockConfig(
        localSsdCount=count)

  def _AddEnableConfidentialStorageToNodeConfig(self, node_config, options):
    if not options.enable_confidential_storage:
      return
    node_config.enableConfidentialStorage = options.enable_confidential_storage

  def _AddStoragePoolsToNodeConfig(self, node_config, options):
    if not options.storage_pools:
      return
    node_config.storagePools = options.storage_pools

  def _AddNodeTaintsToNodeConfig(self, node_config, options):
    """Add nodeTaints to nodeConfig."""
    if options.node_taints is None:
      return
    taints = []
    effect_enum = self.messages.NodeTaint.EffectValueValuesEnum
    for key, value in sorted(six.iteritems(options.node_taints)):
      strs = value.split(':')
      if len(strs) != 2:
        raise util.Error(
            NODE_TAINT_INCORRECT_FORMAT_ERROR_MSG.format(key=key, value=value))
      value = strs[0]
      taint_effect = strs[1]
      if taint_effect == 'NoSchedule':
        effect = effect_enum.NO_SCHEDULE
      elif taint_effect == 'PreferNoSchedule':
        effect = effect_enum.PREFER_NO_SCHEDULE
      elif taint_effect == 'NoExecute':
        effect = effect_enum.NO_EXECUTE
      else:
        raise util.Error(
            NODE_TAINT_INCORRECT_EFFECT_ERROR_MSG.format(effect=strs[1]))
      taints.append(
          self.messages.NodeTaint(key=key, value=value, effect=effect))

    node_config.taints = taints

  def _ResourceManagerTags(self, tags):
    if tags is None:
      return
    rm_tags = self.messages.ResourceManagerTags.TagsValue()
    props = []
    for key, value in six.iteritems(tags):
      props.append(rm_tags.AdditionalProperty(key=key, value=value))
    rm_tags.additionalProperties = props
    return self.messages.ResourceManagerTags(tags=rm_tags)

  def _AddWorkloadMetadataToNodeConfig(self, node_config, options, messages):
    """Adds WorkLoadMetadata to NodeConfig."""
    if options.workload_metadata is not None:
      option = options.workload_metadata
      if option == 'GCE_METADATA':
        node_config.workloadMetadataConfig = messages.WorkloadMetadataConfig(
            mode=messages.WorkloadMetadataConfig.ModeValueValuesEnum
            .GCE_METADATA)
      elif option == 'GKE_METADATA':
        node_config.workloadMetadataConfig = messages.WorkloadMetadataConfig(
            mode=messages.WorkloadMetadataConfig.ModeValueValuesEnum
            .GKE_METADATA)
      else:
        raise util.Error(
            UNKNOWN_WORKLOAD_METADATA_ERROR_MSG.format(option=option))
    elif options.workload_metadata_from_node is not None:
      option = options.workload_metadata_from_node
      if option == 'GCE_METADATA':
        node_config.workloadMetadataConfig = messages.WorkloadMetadataConfig(
            mode=messages.WorkloadMetadataConfig.ModeValueValuesEnum
            .GCE_METADATA)
      elif option == 'GKE_METADATA':
        node_config.workloadMetadataConfig = messages.WorkloadMetadataConfig(
            mode=messages.WorkloadMetadataConfig.ModeValueValuesEnum
            .GKE_METADATA)
      # the following options are deprecated
      elif option == 'SECURE':
        node_config.workloadMetadataConfig = messages.WorkloadMetadataConfig(
            nodeMetadata=messages.WorkloadMetadataConfig
            .NodeMetadataValueValuesEnum.SECURE)
      elif option == 'EXPOSED':
        node_config.workloadMetadataConfig = messages.WorkloadMetadataConfig(
            nodeMetadata=messages.WorkloadMetadataConfig
            .NodeMetadataValueValuesEnum.EXPOSE)
      elif option == 'GKE_METADATA_SERVER':
        node_config.workloadMetadataConfig = messages.WorkloadMetadataConfig(
            nodeMetadata=messages.WorkloadMetadataConfig
            .NodeMetadataValueValuesEnum.GKE_METADATA_SERVER)
      else:
        raise util.Error(
            UNKNOWN_WORKLOAD_METADATA_ERROR_MSG.format(option=option))

  def SetNetworkPolicyCommon(self, options):
    """Returns a SetNetworkPolicy operation."""
    return self.messages.NetworkPolicy(
        enabled=options.enabled,
        # Only Calico is currently supported as a network policy provider.
        provider=self.messages.NetworkPolicy.ProviderValueValuesEnum.CALICO)

  def SetNetworkPolicy(self, cluster_ref, options):
    netpol = self.SetNetworkPolicyCommon(options)
    req = self.messages.SetNetworkPolicyRequest(
        name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                    cluster_ref.clusterId),
        networkPolicy=netpol)
    return self.ParseOperation(
        self.client.projects_locations_clusters.SetNetworkPolicy(req).name,
        cluster_ref.zone)

  def SetMasterAuthCommon(self, options):
    """Returns a SetMasterAuth action."""
    update = self.messages.MasterAuth(
        username=options.username, password=options.password)
    if options.action == SetMasterAuthOptions.SET_PASSWORD:
      action = (
          self.messages.SetMasterAuthRequest.ActionValueValuesEnum.SET_PASSWORD)
    elif options.action == SetMasterAuthOptions.GENERATE_PASSWORD:
      action = (
          self.messages.SetMasterAuthRequest.ActionValueValuesEnum
          .GENERATE_PASSWORD)
    else:  # options.action == SetMasterAuthOptions.SET_USERNAME
      action = (
          self.messages.SetMasterAuthRequest.ActionValueValuesEnum.SET_USERNAME)
    return update, action

  def SetMasterAuth(self, cluster_ref, options):
    update, action = self.SetMasterAuthCommon(options)
    req = self.messages.SetMasterAuthRequest(
        name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                    cluster_ref.clusterId),
        action=action,
        update=update)
    op = self.client.projects_locations_clusters.SetMasterAuth(req)
    return self.ParseOperation(op.name, cluster_ref.zone)

  def StartIpRotation(self, cluster_ref, rotate_credentials):
    operation = self.client.projects_locations_clusters.StartIpRotation(
        self.messages.StartIPRotationRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            rotateCredentials=rotate_credentials))
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def CompleteIpRotation(self, cluster_ref):
    operation = self.client.projects_locations_clusters.CompleteIpRotation(
        self.messages.CompleteIPRotationRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId)))
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def _SendMaintenancePolicyRequest(self, cluster_ref, policy):
    """Given a policy, sends a SetMaintenancePolicy request and returns the operation.
    """
    req = self.messages.SetMaintenancePolicyRequest(
        name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                    cluster_ref.clusterId),
        maintenancePolicy=policy)
    operation = self.client.projects_locations_clusters.SetMaintenancePolicy(
        req)
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def SetDailyMaintenanceWindow(self, cluster_ref, existing_policy,
                                maintenance_window):
    """Sets the daily maintenance window for a cluster."""
    # Special behavior for removing the window. This actually removes the
    # recurring window too, if set (since anyone using this command if there's
    # actually a recurring window probably intends that!).
    if maintenance_window == 'None':
      daily_window = None
    else:
      daily_window = self.messages.DailyMaintenanceWindow(
          startTime=maintenance_window)

    if existing_policy is None:
      existing_policy = self.messages.MaintenancePolicy()
    if existing_policy.window is None:
      existing_policy.window = self.messages.MaintenanceWindow()

    # Temporary until in GA:
    if hasattr(existing_policy.window, 'recurringWindow'):
      existing_policy.window.recurringWindow = None
    existing_policy.window.dailyMaintenanceWindow = daily_window

    return self._SendMaintenancePolicyRequest(cluster_ref, existing_policy)

  def DeleteCluster(self, cluster_ref):
    """Delete a running cluster.

    Args:
      cluster_ref: cluster Resource to describe

    Returns:
      Cluster message.
    Raises:
      Error: if cluster cannot be found or caller is missing permissions. Will
        attempt to find similar clusters in other zones for a more useful error
        if the user has list permissions.
    """
    try:
      operation = self.client.projects_locations_clusters.Delete(
          self.messages.ContainerProjectsLocationsClustersDeleteRequest(
              name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref
                                          .zone, cluster_ref.clusterId)))
      return self.ParseOperation(operation.name, cluster_ref.zone)
    except apitools_exceptions.HttpNotFoundError as error:
      api_error = exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
      # Cluster couldn't be found, maybe user got the location wrong?
      self.CheckClusterOtherZones(cluster_ref, api_error)

  def ListClusters(self, project, location=None):
    if not location:
      location = '-'
    req = self.messages.ContainerProjectsLocationsClustersListRequest(
        parent=ProjectLocation(project, location))
    return self.client.projects_locations_clusters.List(req)

  def CreateNodePoolCommon(self, node_pool_ref, options):
    """Returns a CreateNodePool operation."""
    node_config = self.messages.NodeConfig()
    if options.machine_type:
      node_config.machineType = options.machine_type
    if options.disk_size_gb:
      node_config.diskSizeGb = options.disk_size_gb
    if options.disk_type:
      node_config.diskType = options.disk_type
    if options.image_type:
      node_config.imageType = options.image_type

    self.ParseAdvancedMachineFeatures(options, node_config)

    custom_config = self.messages.CustomImageConfig()
    if options.image:
      custom_config.image = options.image
    if options.image_project:
      custom_config.imageProject = options.image_project
    if options.image_family:
      custom_config.imageFamily = options.image_family
    if options.image or options.image_project or options.image_family:
      node_config.nodeImageConfig = custom_config

    NodeIdentityOptionsToNodeConfig(options, node_config)

    if options.local_ssd_count:
      node_config.localSsdCount = options.local_ssd_count
    self._AddLocalSSDVolumeConfigsToNodeConfig(node_config, options)
    self._AddEphemeralStorageToNodeConfig(node_config, options)
    self._AddEphemeralStorageLocalSsdToNodeConfig(node_config, options)
    self._AddLocalNvmeSsdBlockToNodeConfig(node_config, options)
    self._AddStoragePoolsToNodeConfig(node_config, options)
    if options.enable_confidential_storage:
      node_config.enableConfidentialStorage = (
          options.enable_confidential_storage
      )
    if options.boot_disk_kms_key:
      node_config.bootDiskKmsKey = options.boot_disk_kms_key
    if options.tags:
      node_config.tags = options.tags
    else:
      node_config.tags = []

    self.ParseAcceleratorOptions(options, node_config)

    _AddMetadataToNodeConfig(node_config, options)
    _AddLabelsToNodeConfig(node_config, options)
    _AddNodeLabelsToNodeConfig(node_config, options)
    self._AddNodeTaintsToNodeConfig(node_config, options)

    if options.resource_manager_tags is not None:
      tags = options.resource_manager_tags
      node_config.resourceManagerTags = self._ResourceManagerTags(tags)

    if options.preemptible:
      node_config.preemptible = options.preemptible

    if options.spot:
      node_config.spot = options.spot

    if options.min_cpu_platform is not None:
      node_config.minCpuPlatform = options.min_cpu_platform

    if options.node_group is not None:
      node_config.nodeGroup = options.node_group

    if options.enable_gcfs is not None:
      gcfs_config = self.messages.GcfsConfig(enabled=options.enable_gcfs)
      node_config.gcfsConfig = gcfs_config

    if options.enable_image_streaming is not None:
      gcfs_config = self.messages.GcfsConfig(
          enabled=options.enable_image_streaming)
      node_config.gcfsConfig = gcfs_config

    if options.gvnic is not None:
      gvnic = self.messages.VirtualNIC(enabled=options.gvnic)
      node_config.gvnic = gvnic

    if options.enable_confidential_nodes:
      confidential_nodes = self.messages.ConfidentialNodes(
          enabled=options.enable_confidential_nodes)
      node_config.confidentialNodes = confidential_nodes

    if options.enable_fast_socket is not None:
      fast_socket = self.messages.FastSocket(enabled=options.enable_fast_socket)
      node_config.fastSocket = fast_socket

    if options.maintenance_interval:
      node_config.stableFleetConfig = _GetStableFleetConfig(
          options, self.messages)

    if options.logging_variant is not None:
      logging_config = self.messages.NodePoolLoggingConfig()
      logging_config.variantConfig = self.messages.LoggingVariantConfig(
          variant=VariantConfigEnumFromString(self.messages,
                                              options.logging_variant))
      node_config.loggingConfig = logging_config

    if options.host_maintenance_interval:
      node_config.hostMaintenancePolicy = _GetHostMaintenancePolicy(
          options, self.messages)

    if options.containerd_config_from_file is not None:
      node_config.containerdConfig = self.messages.ContainerdConfig()
      util.LoadContainerdConfigFromYAML(
          node_config.containerdConfig,
          options.containerd_config_from_file,
          self.messages,
      )

    self._AddWorkloadMetadataToNodeConfig(node_config, options, self.messages)
    _AddLinuxNodeConfigToNodeConfig(node_config, options, self.messages)
    _AddShieldedInstanceConfigToNodeConfig(node_config, options, self.messages)
    _AddReservationAffinityToNodeConfig(node_config, options, self.messages)
    _AddSandboxConfigToNodeConfig(node_config, options, self.messages)
    _AddWindowsNodeConfigToNodeConfig(node_config, options, self.messages)

    pool = self.messages.NodePool(
        name=node_pool_ref.nodePoolId,
        initialNodeCount=options.num_nodes,
        config=node_config,
        version=options.node_version,
        management=self._GetNodeManagement(options))

    if options.enable_autoscaling or options.enable_autoprovisioning:
      pool.autoscaling = self.messages.NodePoolAutoscaling()

    if options.enable_autoscaling:
      pool.autoscaling.enabled = options.enable_autoscaling
      pool.autoscaling.minNodeCount = options.min_nodes
      pool.autoscaling.maxNodeCount = options.max_nodes
      pool.autoscaling.totalMinNodeCount = options.total_min_nodes
      pool.autoscaling.totalMaxNodeCount = options.total_max_nodes
      if options.location_policy is not None:
        pool.autoscaling.locationPolicy = LocationPolicyEnumFromString(
            self.messages, options.location_policy
        )

    if options.enable_best_effort_provision:
      pool.bestEffortProvisioning = self.messages.BestEffortProvisioning()
      pool.bestEffortProvisioning.enabled = True
      pool.bestEffortProvisioning.minProvisionNodes = (
          options.min_provision_nodes
      )

    if options.enable_autoprovisioning:
      pool.autoscaling.autoprovisioned = options.enable_autoprovisioning

    if options.max_pods_per_node is not None:
      pool.maxPodsConstraint = self.messages.MaxPodsConstraint(
          maxPodsPerNode=options.max_pods_per_node
      )

    if (
        options.enable_surge_upgrade
        or options.enable_blue_green_upgrade
        or options.max_surge_upgrade is not None
        or options.max_unavailable_upgrade is not None
        or options.standard_rollout_policy is not None
        or options.autoscaled_rollout_policy is not None
        or options.node_pool_soak_duration is not None
    ):
      pool.upgradeSettings = self.messages.UpgradeSettings()
      pool.upgradeSettings = self.UpdateUpgradeSettings(
          None, options, pool=pool
      )

    if options.node_locations is not None:
      pool.locations = sorted(options.node_locations)

    if options.system_config_from_file is not None:
      util.LoadSystemConfigFromYAML(
          node_config,
          options.system_config_from_file,
          options.enable_insecure_kubelet_readonly_port,
          self.messages,
      )

    if options.enable_insecure_kubelet_readonly_port is not None:
      if node_config.kubeletConfig is None:
        node_config.kubeletConfig = self.messages.NodeKubeletConfig()
      node_config.kubeletConfig.insecureKubeletReadonlyPortEnabled = (
          options.enable_insecure_kubelet_readonly_port
      )

    pool.networkConfig = self._GetNetworkConfig(options)

    if options.network_performance_config:
      pool.networkConfig.networkPerformanceConfig = (
          self._GetNetworkPerformanceConfig(options)
      )

    if (
        options.placement_type == 'COMPACT'
        or options.placement_policy is not None
    ):
      pool.placementPolicy = self.messages.PlacementPolicy()
    if options.placement_type == 'COMPACT':
      pool.placementPolicy.type = (
          self.messages.PlacementPolicy.TypeValueValuesEnum.COMPACT
      )
    if options.placement_policy is not None:
      pool.placementPolicy.policyName = options.placement_policy

    if options.tpu_topology:
      if pool.placementPolicy is None:
        pool.placementPolicy = self.messages.PlacementPolicy()
      pool.placementPolicy.tpuTopology = options.tpu_topology

    if options.enable_queued_provisioning is not None:
      pool.queuedProvisioning = self.messages.QueuedProvisioning()
      pool.queuedProvisioning.enabled = options.enable_queued_provisioning

    # Explicitly check None for empty list
    if options.sole_tenant_node_affinity_file is not None:
      node_config.soleTenantConfig = (
          util.LoadSoleTenantConfigFromNodeAffinityYaml(
              options.sole_tenant_node_affinity_file, self.messages
          )
      )

    if options.secondary_boot_disks is not None:
      mode_enum = self.messages.SecondaryBootDisk.ModeValueValuesEnum
      mode_map = {
          'CONTAINER_IMAGE_CACHE': mode_enum.CONTAINER_IMAGE_CACHE,
      }
      node_config.secondaryBootDisks = []
      for disk_config in options.secondary_boot_disks:
        disk_image = disk_config['disk-image']

        # convert mode string to corresponding enum value
        mode = None
        if 'mode' in disk_config:
          if disk_config['mode'] in mode_map:
            mode = mode_map[disk_config['mode']]
          else:
            mode = mode_enum.MODE_UNSPECIFIED

        node_config.secondaryBootDisks.append(
            self.messages.SecondaryBootDisk(
                diskImage=disk_image,
                mode=mode,
            )
        )

    return pool

  def CreateNodePool(self, node_pool_ref, options):
    """CreateNodePool creates a node pool and returns the operation."""
    pool = self.CreateNodePoolCommon(node_pool_ref, options)
    req = self.messages.CreateNodePoolRequest(
        nodePool=pool,
        parent=ProjectLocationCluster(node_pool_ref.projectId,
                                      node_pool_ref.zone,
                                      node_pool_ref.clusterId))
    operation = self.client.projects_locations_clusters_nodePools.Create(req)
    return self.ParseOperation(operation.name, node_pool_ref.zone)

  def ListNodePools(self, cluster_ref):
    req = self.messages.ContainerProjectsLocationsClustersNodePoolsListRequest(
        parent=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                      cluster_ref.clusterId))
    return self.client.projects_locations_clusters_nodePools.List(req)

  def GetNodePool(self, node_pool_ref):
    req = self.messages.ContainerProjectsLocationsClustersNodePoolsGetRequest(
        name=ProjectLocationClusterNodePool(
            node_pool_ref.projectId, node_pool_ref.zone,
            node_pool_ref.clusterId, node_pool_ref.nodePoolId))
    return self.client.projects_locations_clusters_nodePools.Get(req)

  def UpdateNodePoolNodeManagement(self, node_pool_ref, options):
    """Updates node pool's node management configuration.

    Args:
      node_pool_ref: node pool Resource to update.
      options: node pool update options

    Returns:
      Updated node management configuration.
    """
    pool = self.GetNodePool(node_pool_ref)
    node_management = pool.management
    if node_management is None:
      node_management = self.messages.NodeManagement()
    if options.enable_autorepair is not None:
      node_management.autoRepair = options.enable_autorepair
    if options.enable_autoupgrade is not None:
      node_management.autoUpgrade = options.enable_autoupgrade
    return node_management

  def UpdateNodePoolAutoscaling(self, node_pool_ref, options):
    """Update node pool's autoscaling configuration.

    Args:
      node_pool_ref: node pool Resource to update.
      options: node pool update options

    Returns:
      Updated autoscaling configuration for the node pool.
    """
    pool = self.GetNodePool(node_pool_ref)
    autoscaling = pool.autoscaling
    if autoscaling is None:
      autoscaling = self.messages.NodePoolAutoscaling()
    if options.enable_autoscaling is not None:
      autoscaling.enabled = options.enable_autoscaling
      if not autoscaling.enabled:
        # clear limits and autoprovisioned when disabling autoscaling
        autoscaling.minNodeCount = 0
        autoscaling.maxNodeCount = 0
        autoscaling.totalMinNodeCount = 0
        autoscaling.totalMaxNodeCount = 0
        autoscaling.autoprovisioned = False
        autoscaling.locationPolicy = self.messages.NodePoolAutoscaling.LocationPolicyValueValuesEnum.LOCATION_POLICY_UNSPECIFIED
    if options.enable_autoprovisioning is not None:
      autoscaling.autoprovisioned = options.enable_autoprovisioning
      if autoscaling.autoprovisioned:
        # clear min nodes limit when enabling autoprovisioning
        autoscaling.minNodeCount = 0
        autoscaling.totalMinNodeCount = 0
    if options.max_nodes is not None:
      autoscaling.maxNodeCount = options.max_nodes
    if options.min_nodes is not None:
      autoscaling.minNodeCount = options.min_nodes
    if options.total_max_nodes is not None:
      autoscaling.totalMaxNodeCount = options.total_max_nodes
    if options.total_min_nodes is not None:
      autoscaling.totalMinNodeCount = options.total_min_nodes
    if options.location_policy is not None:
      autoscaling.locationPolicy = LocationPolicyEnumFromString(
          self.messages, options.location_policy)
    return autoscaling

  def UpdateBlueGreenSettings(self, upgrade_settings, options):
    """Update blue green settings field in upgrade_settings."""
    blue_green_settings = upgrade_settings.blueGreenSettings or self.messages.BlueGreenSettings(
    )
    if options.node_pool_soak_duration is not None:
      blue_green_settings.nodePoolSoakDuration = options.node_pool_soak_duration

    if options.standard_rollout_policy is not None:
      standard_rollout_policy = blue_green_settings.standardRolloutPolicy or self.messages.StandardRolloutPolicy(
      )

      if 'batch-node-count' in options.standard_rollout_policy and 'batch-percent' in options.standard_rollout_policy:
        raise util.Error(
            'StandardRolloutPolicy must contain only one of: batch-node-count, batch-percent'
        )

      standard_rollout_policy.batchPercentage = standard_rollout_policy.batchNodeCount = None
      if 'batch-node-count' in options.standard_rollout_policy:
        standard_rollout_policy.batchNodeCount = options.standard_rollout_policy[
            'batch-node-count']
      elif 'batch-percent' in options.standard_rollout_policy:
        standard_rollout_policy.batchPercentage = options.standard_rollout_policy[
            'batch-percent']

      if 'batch-soak-duration' in options.standard_rollout_policy:
        standard_rollout_policy.batchSoakDuration = options.standard_rollout_policy[
            'batch-soak-duration']
      blue_green_settings.standardRolloutPolicy = standard_rollout_policy
    # autoscaled rollout policy has no fields yet.
    if options.autoscaled_rollout_policy:
      blue_green_settings.autoscaledRolloutPolicy = (
          self.messages.AutoscaledRolloutPolicy()
      )
    return blue_green_settings

  def UpdateUpgradeSettings(self, node_pool_ref, options, pool=None):
    """Updates node pool's upgrade setting."""
    if pool is None:
      pool = self.GetNodePool(node_pool_ref)

    if options.enable_surge_upgrade and options.enable_blue_green_upgrade:
      raise util.Error(
          'UpgradeSettings must contain only one of: --enable-surge-upgrade, --enable-blue-green-upgrade'
      )

    upgrade_settings = pool.upgradeSettings
    if upgrade_settings is None:
      upgrade_settings = self.messages.UpgradeSettings()
    if options.max_surge_upgrade is not None:
      upgrade_settings.maxSurge = options.max_surge_upgrade
    if options.max_unavailable_upgrade is not None:
      upgrade_settings.maxUnavailable = options.max_unavailable_upgrade
    if options.enable_surge_upgrade:
      upgrade_settings.strategy = self.messages.UpgradeSettings.StrategyValueValuesEnum.SURGE
    if options.enable_blue_green_upgrade:
      upgrade_settings.strategy = self.messages.UpgradeSettings.StrategyValueValuesEnum.BLUE_GREEN
    if options.standard_rollout_policy is not None or options.node_pool_soak_duration is not None:
      upgrade_settings.blueGreenSettings = self.UpdateBlueGreenSettings(
          upgrade_settings, options)
    if options.autoscaled_rollout_policy:
      upgrade_settings.blueGreenSettings = self.UpdateBlueGreenSettings(
          upgrade_settings, options)
    return upgrade_settings

  def UpdateNodePoolRequest(self, node_pool_ref, options):
    """Creates an UpdateNodePoolRequest from the provided options.

    Arguments:
      node_pool_ref: The node pool to act on.
      options: UpdateNodePoolOptions with the user-specified options.

    Returns:

      An UpdateNodePoolRequest.
    """

    update_request = self.messages.UpdateNodePoolRequest(
        name=ProjectLocationClusterNodePool(
            node_pool_ref.projectId,
            node_pool_ref.zone,
            node_pool_ref.clusterId,
            node_pool_ref.nodePoolId,
        ))

    self.ParseAcceleratorOptions(options, update_request)

    if options.workload_metadata is not None or options.workload_metadata_from_node is not None:
      self._AddWorkloadMetadataToNodeConfig(update_request, options,
                                            self.messages)
    elif options.node_locations is not None:
      update_request.locations = sorted(options.node_locations)
    elif (options.enable_blue_green_upgrade or options.enable_surge_upgrade or
          options.max_surge_upgrade is not None or
          options.max_unavailable_upgrade is not None or
          options.standard_rollout_policy is not None or
          options.node_pool_soak_duration is not None
          or options.autoscaled_rollout_policy):
      update_request.upgradeSettings = self.UpdateUpgradeSettings(
          node_pool_ref, options)
    elif (
        options.system_config_from_file is not None
        or options.enable_insecure_kubelet_readonly_port is not None
    ):
      node_config = self.messages.NodeConfig()
      if options.system_config_from_file is not None:
        util.LoadSystemConfigFromYAML(
            node_config,
            options.system_config_from_file,
            options.enable_insecure_kubelet_readonly_port,
            self.messages,
        )
      if options.enable_insecure_kubelet_readonly_port is not None:
        if node_config.kubeletConfig is None:
          node_config.kubeletConfig = self.messages.NodeKubeletConfig()
        node_config.kubeletConfig.insecureKubeletReadonlyPortEnabled = (
            options.enable_insecure_kubelet_readonly_port
        )

      # set the update request
      update_request.linuxNodeConfig = node_config.linuxNodeConfig
      update_request.kubeletConfig = node_config.kubeletConfig

    elif options.containerd_config_from_file is not None:
      containerd_config = self.messages.ContainerdConfig()
      util.LoadContainerdConfigFromYAML(containerd_config,
                                        options.containerd_config_from_file,
                                        self.messages)
      update_request.containerdConfig = containerd_config
    elif options.labels is not None:
      resource_labels = self.messages.ResourceLabels()
      labels = resource_labels.LabelsValue()
      props = []
      for key, value in six.iteritems(options.labels):
        props.append(labels.AdditionalProperty(key=key, value=value))
      labels.additionalProperties = props
      resource_labels.labels = labels
      update_request.resourceLabels = resource_labels
    elif options.node_labels is not None:
      node_labels = self.messages.NodeLabels()
      labels = node_labels.LabelsValue()
      props = []
      for key, value in six.iteritems(options.node_labels):
        props.append(labels.AdditionalProperty(key=key, value=value))
      labels.additionalProperties = props
      node_labels.labels = labels
      update_request.labels = node_labels
    elif options.node_taints is not None:
      taints = []
      effect_enum = self.messages.NodeTaint.EffectValueValuesEnum
      for key, value in sorted(six.iteritems(options.node_taints)):
        strs = value.split(':')
        if len(strs) != 2:
          raise util.Error(
              NODE_TAINT_INCORRECT_FORMAT_ERROR_MSG.format(
                  key=key, value=value))
        value = strs[0]
        taint_effect = strs[1]
        if taint_effect == 'NoSchedule':
          effect = effect_enum.NO_SCHEDULE
        elif taint_effect == 'PreferNoSchedule':
          effect = effect_enum.PREFER_NO_SCHEDULE
        elif taint_effect == 'NoExecute':
          effect = effect_enum.NO_EXECUTE
        else:
          raise util.Error(
              NODE_TAINT_INCORRECT_EFFECT_ERROR_MSG.format(effect=strs[1]))
        taints.append(
            self.messages.NodeTaint(key=key, value=value, effect=effect))
      node_taints = self.messages.NodeTaints()
      node_taints.taints = taints
      update_request.taints = node_taints
    elif options.tags is not None:
      node_tags = self.messages.NetworkTags()
      node_tags.tags = options.tags
      update_request.tags = node_tags
    elif options.enable_private_nodes is not None:
      network_config = self.messages.NodeNetworkConfig()
      network_config.enablePrivateNodes = options.enable_private_nodes
      update_request.nodeNetworkConfig = network_config
    elif options.enable_gcfs is not None:
      gcfs_config = self.messages.GcfsConfig(enabled=options.enable_gcfs)
      update_request.gcfsConfig = gcfs_config
    elif options.gvnic is not None:
      gvnic = self.messages.VirtualNIC(enabled=options.gvnic)
      update_request.gvnic = gvnic
    elif options.enable_image_streaming is not None:
      gcfs_config = self.messages.GcfsConfig(
          enabled=options.enable_image_streaming)
      update_request.gcfsConfig = gcfs_config
    elif options.network_performance_config is not None:
      network_config = self.messages.NodeNetworkConfig()
      network_config.networkPerformanceConfig = self._GetNetworkPerformanceConfig(
          options)
      update_request.nodeNetworkConfig = network_config
    elif options.enable_confidential_nodes is not None:
      confidential_nodes = self.messages.ConfidentialNodes(
          enabled=options.enable_confidential_nodes)
      update_request.confidentialNodes = confidential_nodes
    elif options.enable_fast_socket is not None:
      fast_socket = self.messages.FastSocket(enabled=options.enable_fast_socket)
      update_request.fastSocket = fast_socket
    elif options.logging_variant is not None:
      logging_config = self.messages.NodePoolLoggingConfig()
      logging_config.variantConfig = self.messages.LoggingVariantConfig(
          variant=VariantConfigEnumFromString(self.messages,
                                              options.logging_variant))
      update_request.loggingConfig = logging_config
    elif options.windows_os_version is not None:
      windows_node_config = self.messages.WindowsNodeConfig()
      if options.windows_os_version == 'ltsc2022':
        windows_node_config.osVersion = self.messages.WindowsNodeConfig.OsVersionValueValuesEnum.OS_VERSION_LTSC2022
      else:
        windows_node_config.osVersion = self.messages.WindowsNodeConfig.OsVersionValueValuesEnum.OS_VERSION_LTSC2019
      update_request.windowsNodeConfig = windows_node_config
    elif options.resource_manager_tags is not None:
      tags = options.resource_manager_tags
      update_request.resourceManagerTags = self._ResourceManagerTags(tags)
    elif (options.machine_type is not None or
          options.disk_type is not None or
          options.disk_size_gb is not None):
      update_request.machineType = options.machine_type
      update_request.diskType = options.disk_type
      update_request.diskSizeGb = options.disk_size_gb
    elif options.enable_queued_provisioning is not None:
      update_request.queuedProvisioning = self.messages.QueuedProvisioning()
      update_request.queuedProvisioning.enabled = (
          options.enable_queued_provisioning)
    return update_request

  def UpdateNodePool(self, node_pool_ref, options):
    """Updates nodePool on a cluster."""
    if options.IsAutoscalingUpdate():
      autoscaling = self.UpdateNodePoolAutoscaling(node_pool_ref, options)
      update = self.messages.ClusterUpdate(
          desiredNodePoolId=node_pool_ref.nodePoolId,
          desiredNodePoolAutoscaling=autoscaling)
      operation = self.client.projects_locations_clusters.Update(
          self.messages.UpdateClusterRequest(
              name=ProjectLocationCluster(node_pool_ref.projectId,
                                          node_pool_ref.zone,
                                          node_pool_ref.clusterId),
              update=update))
      return self.ParseOperation(operation.name, node_pool_ref.zone)
    elif options.IsNodePoolManagementUpdate():
      management = self.UpdateNodePoolNodeManagement(node_pool_ref, options)
      req = (
          self.messages.SetNodePoolManagementRequest(
              name=ProjectLocationClusterNodePool(node_pool_ref.projectId,
                                                  node_pool_ref.zone,
                                                  node_pool_ref.clusterId,
                                                  node_pool_ref.nodePoolId),
              management=management))
      operation = (
          self.client.projects_locations_clusters_nodePools.SetManagement(req))
    elif options.IsUpdateNodePoolRequest():
      req = self.UpdateNodePoolRequest(node_pool_ref, options)
      operation = self.client.projects_locations_clusters_nodePools.Update(req)
    else:
      raise util.Error('Unhandled node pool update mode')

    return self.ParseOperation(operation.name, node_pool_ref.zone)

  def DeleteNodePool(self, node_pool_ref):
    operation = self.client.projects_locations_clusters_nodePools.Delete(
        self.messages.ContainerProjectsLocationsClustersNodePoolsDeleteRequest(
            name=ProjectLocationClusterNodePool(
                node_pool_ref.projectId, node_pool_ref.zone,
                node_pool_ref.clusterId, node_pool_ref.nodePoolId)))
    return self.ParseOperation(operation.name, node_pool_ref.zone)

  def RollbackUpgrade(self, node_pool_ref, respect_pdb=None):
    operation = self.client.projects_locations_clusters_nodePools.Rollback(
        self.messages.RollbackNodePoolUpgradeRequest(
            name=ProjectLocationClusterNodePool(
                node_pool_ref.projectId, node_pool_ref.zone,
                node_pool_ref.clusterId, node_pool_ref.nodePoolId),
            respectPdb=respect_pdb))
    return self.ParseOperation(operation.name, node_pool_ref.zone)

  def CompleteNodePoolUpgrade(self, node_pool_ref):
    req = self.messages.ContainerProjectsLocationsClustersNodePoolsCompleteUpgradeRequest(
        name=ProjectLocationClusterNodePool(
            node_pool_ref.projectId, node_pool_ref.zone,
            node_pool_ref.clusterId, node_pool_ref.nodePoolId))
    return self.client.projects_locations_clusters_nodePools.CompleteUpgrade(
        req)

  def CancelOperation(self, op_ref):
    req = self.messages.CancelOperationRequest(
        name=ProjectLocationOperation(op_ref.projectId, op_ref.zone,
                                      op_ref.operationId))
    return self.client.projects_locations_operations.Cancel(req)

  def IsRunning(self, cluster):
    return (
        cluster.status == self.messages.Cluster.StatusValueValuesEnum.RUNNING)

  def IsDegraded(self, cluster):
    return (
        cluster.status == self.messages.Cluster.StatusValueValuesEnum.DEGRADED)

  def GetDegradedWarning(self, cluster):
    if cluster.conditions:
      codes = [condition.code for condition in cluster.conditions]
      messages = [condition.message for condition in cluster.conditions]
      return ('Codes: {0}\n' 'Messages: {1}.').format(codes, messages)
    else:
      return gke_constants.DEFAULT_DEGRADED_WARNING

  def GetOperationError(self, operation):
    return operation.statusMessage

  def ListOperations(self, project, location=None):
    if not location:
      location = '-'
    req = self.messages.ContainerProjectsLocationsOperationsListRequest(
        parent=ProjectLocation(project, location))
    return self.client.projects_locations_operations.List(req)

  def IsOperationFinished(self, operation):
    return (
        operation.status == self.messages.Operation.StatusValueValuesEnum.DONE)

  def GetServerConfig(self, project, location):
    req = self.messages.ContainerProjectsLocationsGetServerConfigRequest(
        name=ProjectLocation(project, location))
    return self.client.projects_locations.GetServerConfig(req)

  def ResizeNodePool(self, cluster_ref, pool_name, size):
    req = self.messages.SetNodePoolSizeRequest(
        name=ProjectLocationClusterNodePool(cluster_ref.projectId,
                                            cluster_ref.zone,
                                            cluster_ref.clusterId, pool_name),
        nodeCount=size)
    operation = self.client.projects_locations_clusters_nodePools.SetSize(req)
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def _GetNodeManagement(self, options):
    """Gets a wrapper containing the options for how nodes are managed.

    Args:
      options: node management options

    Returns:
      A NodeManagement object that contains the options indicating how nodes
      are managed. This is currently quite simple, containing only two options.
      However, there are more options planned for node management.
    """
    if options.enable_autorepair is None and options.enable_autoupgrade is None:
      return None

    node_management = self.messages.NodeManagement()
    node_management.autoRepair = options.enable_autorepair
    node_management.autoUpgrade = options.enable_autoupgrade
    return node_management

  def _GetNetworkConfig(self, options):
    """Gets a wrapper containing the network config for the node pool.

    Args:
      options: Network config options

    Returns:
      A NetworkConfig object that contains the options for how the network
      for the nodepool needs to be configured.
    """
    if (options.pod_ipv4_range is None and
        options.create_pod_ipv4_range is None and
        options.enable_private_nodes is None and
        options.network_performance_config is None and
        options.disable_pod_cidr_overprovision is None and
        options.additional_node_network is None and
        options.additional_pod_network is None):
      return None

    network_config = self.messages.NodeNetworkConfig()
    if options.pod_ipv4_range is not None:
      network_config.podRange = options.pod_ipv4_range
    if options.create_pod_ipv4_range is not None:
      for key in options.create_pod_ipv4_range:
        if key not in ['name', 'range']:
          raise util.Error(
              CREATE_POD_RANGE_INVALID_KEY_ERROR_MSG.format(key=key))
      network_config.createPodRange = True
      network_config.podRange = options.create_pod_ipv4_range.get('name', None)
      network_config.podIpv4CidrBlock = options.create_pod_ipv4_range.get(
          'range', None)
    if options.enable_private_nodes is not None:
      network_config.enablePrivateNodes = options.enable_private_nodes
    if options.disable_pod_cidr_overprovision is not None:
      network_config.podCidrOverprovisionConfig = self.messages.PodCIDROverprovisionConfig(
          disable=options.disable_pod_cidr_overprovision)

    if options.additional_node_network is not None:
      network_config.additionalNodeNetworkConfigs = []
      for node_network_option in options.additional_node_network:
        node_network_config_msg = self.messages.AdditionalNodeNetworkConfig()
        node_network_config_msg.network = node_network_option['network']
        node_network_config_msg.subnetwork = node_network_option['subnetwork']
        network_config.additionalNodeNetworkConfigs.append(
            node_network_config_msg)

    if options.additional_pod_network is not None:
      network_config.additionalPodNetworkConfigs = []
      for pod_network_option in options.additional_pod_network:
        pod_network_config_msg = self.messages.AdditionalPodNetworkConfig()
        pod_network_config_msg.subnetwork = pod_network_option.get(
            'subnetwork', None)
        pod_network_config_msg.secondaryPodRange = pod_network_option[
            'pod-ipv4-range']
        pod_network_config_msg.maxPodsPerNode = self.messages.MaxPodsConstraint(
            maxPodsPerNode=pod_network_option.get('max-pods-per-node', None))
        network_config.additionalPodNetworkConfigs.append(
            pod_network_config_msg)

    return network_config

  def _GetNetworkPerformanceConfig(self, options):
    """Get NetworkPerformanceConfig message for the instance."""

    network_perf_args = options.network_performance_config
    network_perf_configs = self.messages.NetworkPerformanceConfig()

    for config in network_perf_args:
      total_tier = config.get('total-egress-bandwidth-tier', '').upper()
      if total_tier:
        network_perf_configs.totalEgressBandwidthTier = self.messages.NetworkPerformanceConfig.TotalEgressBandwidthTierValueValuesEnum(
            total_tier)

    return network_perf_configs

  def UpdateLabelsCommon(self, cluster_ref, update_labels):
    """Update labels on a cluster.

    Args:
      cluster_ref: cluster to update.
      update_labels: labels to set.

    Returns:
      Operation ref for label set operation.
    """
    clus = None
    try:
      clus = self.GetCluster(cluster_ref)
    except apitools_exceptions.HttpNotFoundError:
      pass
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    labels = self.messages.SetLabelsRequest.ResourceLabelsValue()
    props = []
    for k, v in sorted(six.iteritems(update_labels)):
      props.append(labels.AdditionalProperty(key=k, value=v))
    labels.additionalProperties = props
    return labels, clus.labelFingerprint

  def UpdateLabels(self, cluster_ref, update_labels):
    """Updates labels for a cluster."""
    labels, fingerprint = self.UpdateLabelsCommon(cluster_ref, update_labels)
    operation = self.client.projects_locations_clusters.SetResourceLabels(
        self.messages.SetLabelsRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            resourceLabels=labels,
            labelFingerprint=fingerprint))
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def RemoveLabelsCommon(self, cluster_ref, remove_labels):
    """Removes labels from a cluster.

    Args:
      cluster_ref: cluster to update.
      remove_labels: labels to remove.

    Returns:
      Operation ref for label set operation.
    """
    clus = None
    try:
      clus = self.GetCluster(cluster_ref)
    except apitools_exceptions.HttpNotFoundError:
      pass
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    clus_labels = {}
    if clus.resourceLabels:
      for item in clus.resourceLabels.additionalProperties:
        clus_labels[item.key] = str(item.value)

    # if clusLabels empty, nothing to do
    if not clus_labels:
      raise util.Error(NO_LABELS_ON_CLUSTER_ERROR_MSG.format(cluster=clus.name))

    for k in remove_labels:
      try:
        clus_labels.pop(k)
      except KeyError as error:
        # if at least one label not found on cluster, raise error
        raise util.Error(
            NO_SUCH_LABEL_ERROR_MSG.format(cluster=clus.name, name=k))

    labels = self.messages.SetLabelsRequest.ResourceLabelsValue()
    for k, v in sorted(six.iteritems(clus_labels)):
      labels.additionalProperties.append(
          labels.AdditionalProperty(key=k, value=v))
    return labels, clus.labelFingerprint

  def RemoveLabels(self, cluster_ref, remove_labels):
    """Removes labels from a cluster."""
    labels, fingerprint = self.RemoveLabelsCommon(cluster_ref, remove_labels)
    operation = self.client.projects_locations_clusters.SetResourceLabels(
        self.messages.SetLabelsRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            resourceLabels=labels,
            labelFingerprint=fingerprint))
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def GetIamPolicy(self, cluster_ref):
    raise NotImplementedError('GetIamPolicy is not overridden')

  def SetIamPolicy(self, cluster_ref):
    raise NotImplementedError('GetIamPolicy is not overridden')

  def SetRecurringMaintenanceWindow(self, cluster_ref, existing_policy,
                                    window_start, window_end,
                                    window_recurrence):
    """Sets a recurring maintenance window as the maintenance policy for a cluster.

    Args:
      cluster_ref: The cluster to update.
      existing_policy: The existing maintenance policy, if any.
      window_start: Start time of the window as a datetime.datetime.
      window_end: End time of the window as a datetime.datetime.
      window_recurrence: RRULE str defining how the window will recur.

    Returns:
      The operation from this cluster update.
    """
    recurring_window = self.messages.RecurringTimeWindow(
        window=self.messages.TimeWindow(
            startTime=window_start.isoformat(), endTime=window_end.isoformat()),
        recurrence=window_recurrence)
    if existing_policy is None:
      existing_policy = self.messages.MaintenancePolicy()
    if existing_policy.window is None:
      existing_policy.window = self.messages.MaintenanceWindow()
    existing_policy.window.dailyMaintenanceWindow = None
    existing_policy.window.recurringWindow = recurring_window
    return self._SendMaintenancePolicyRequest(cluster_ref, existing_policy)

  def RemoveMaintenanceWindow(self, cluster_ref, existing_policy):
    """Removes the recurring or daily maintenance policy."""
    if (existing_policy is None or existing_policy.window is None or
        (existing_policy.window.dailyMaintenanceWindow is None and
         existing_policy.window.recurringWindow is None)):
      raise util.Error(NOTHING_TO_UPDATE_ERROR_MSG)
    existing_policy.window.dailyMaintenanceWindow = None
    existing_policy.window.recurringWindow = None
    return self._SendMaintenancePolicyRequest(cluster_ref, existing_policy)

  def _NormalizeMaintenanceExclusionsForPolicy(self, policy):
    """Given a maintenance policy (can be None), return a normalized form.

    This makes it easier to add and remove blackouts because the blackouts
    list will definitely exist.

    Args:
      policy: The policy to normalize.

    Returns:
      The modified policy (note: modifies in place, but there might not have
      even been an existing policy).
    """
    empty_excl = self.messages.MaintenanceWindow.MaintenanceExclusionsValue()
    if policy is None:
      policy = self.messages.MaintenancePolicy(
          window=self.messages.MaintenanceWindow(
              maintenanceExclusions=empty_excl))
    elif policy.window is None:
      # Shouldn't happen due to defaulting on the server, but easy enough to
      # handle.
      policy.window = self.messages.MaintenanceWindow(
          maintenanceExclusions=empty_excl)
    elif policy.window.maintenanceExclusions is None:
      policy.window.maintenanceExclusions = empty_excl
    return policy

  def _GetMaintenanceExclusionNames(self, maintenance_policy):
    """Returns a list of maintenance exclusion names from the policy."""
    return [
        p.key for p in
        maintenance_policy.window.maintenanceExclusions.additionalProperties
    ]

  def AddMaintenanceExclusion(self, cluster_ref, existing_policy, window_name,
                              window_start, window_end, window_scope):
    """Adds a maintenance exclusion to the cluster's maintenance policy.

    Args:
      cluster_ref: The cluster to update.
      existing_policy: The existing maintenance policy, if any.
      window_name: Unique name for the exclusion. Can be None (will be
        autogenerated if so).
      window_start: Start time of the window as a datetime.datetime. Can be
        None.
      window_end: End time of the window as a datetime.datetime.
      window_scope: Scope that the current exclusion will apply to.

    Returns:
      Operation from this cluster update.

    Raises:
      Error if a maintenance exclusion of that name already exists.
    """
    existing_policy = self._NormalizeMaintenanceExclusionsForPolicy(
        existing_policy)

    if window_start is None:
      window_start = times.Now(times.UTC)
    if window_name is None:
      # Collisions from this shouldn't be an issue because this has millisecond
      # resolution.
      window_name = 'generated-exclusion-' + times.Now(times.UTC).isoformat()

    if window_name in self._GetMaintenanceExclusionNames(existing_policy):
      raise util.Error(
          'A maintenance exclusion named {0} already exists.'.format(
              window_name))

    # Note: we're using external/python/gcloud_deps/apitools/base/protorpclite
    # which does *not* handle maps very nicely. We actually have a
    # MaintenanceExclusionsValue field that has a repeated additionalProperties
    # field that has key and value fields. See
    # third_party/apis/container/v1alpha1/container_v1alpha1_messages.py.
    exclusions = existing_policy.window.maintenanceExclusions
    window = self.messages.TimeWindow(
        startTime=window_start.isoformat(), endTime=window_end.isoformat())
    if window_scope is not None:
      if window_scope == 'no_upgrades':
        window.maintenanceExclusionOptions = self.messages.MaintenanceExclusionOptions(
            scope=self.messages.MaintenanceExclusionOptions.ScopeValueValuesEnum
            .NO_UPGRADES)
      if window_scope == 'no_minor_upgrades':
        window.maintenanceExclusionOptions = self.messages.MaintenanceExclusionOptions(
            scope=self.messages.MaintenanceExclusionOptions.ScopeValueValuesEnum
            .NO_MINOR_UPGRADES)
      if window_scope == 'no_minor_or_node_upgrades':
        window.maintenanceExclusionOptions = self.messages.MaintenanceExclusionOptions(
            scope=self.messages.MaintenanceExclusionOptions.ScopeValueValuesEnum
            .NO_MINOR_OR_NODE_UPGRADES)

    exclusions.additionalProperties.append(
        exclusions.AdditionalProperty(key=window_name, value=window))
    return self._SendMaintenancePolicyRequest(cluster_ref, existing_policy)

  def RemoveMaintenanceExclusion(self, cluster_ref, existing_policy,
                                 exclusion_name):
    """Removes a maintenance exclusion from the maintenance policy by name."""
    existing_policy = self._NormalizeMaintenanceExclusionsForPolicy(
        existing_policy)
    existing_exclusions = self._GetMaintenanceExclusionNames(existing_policy)
    if exclusion_name not in existing_exclusions:
      message = ('No maintenance exclusion with name {0} exists. Existing '
                 'exclusions: {1}.').format(exclusion_name,
                                            ', '.join(existing_exclusions))
      raise util.Error(message)

    props = []
    for ex in existing_policy.window.maintenanceExclusions.additionalProperties:
      if ex.key != exclusion_name:
        props.append(ex)
    existing_policy.window.maintenanceExclusions.additionalProperties = props

    return self._SendMaintenancePolicyRequest(cluster_ref, existing_policy)

  def ListUsableSubnets(self, project_ref, network_project, filter_arg):
    """List usable subnets for a given project.

    Args:
      project_ref: project where clusters will be created.
      network_project: project ID where clusters will be created.
      filter_arg: value of filter flag.

    Returns:
      Response containing the list of subnetworks and a next page token.
    """
    filters = []
    if network_project is not None:
      filters.append('networkProjectId=' + network_project)

    if filter_arg is not None:
      filters.append(filter_arg)

    filters = ' AND '.join(filters)

    req = self.messages.ContainerProjectsAggregatedUsableSubnetworksListRequest(
        # parent example: 'projects/abc'
        parent=project_ref.RelativeName(),
        # max pageSize accepted by GKE
        pageSize=500,
        filter=filters)
    return self.client.projects_aggregated_usableSubnetworks.List(req)

  def ModifyCrossConnectSubnetworks(self,
                                    cluster_ref,
                                    existing_cross_connect_config,
                                    add_subnetworks=None,
                                    remove_subnetworks=None,
                                    clear_all_subnetworks=None):
    """Add/Remove/Clear cross connect subnetworks and schedule cluster update request.
    """
    items = existing_cross_connect_config.items
    if clear_all_subnetworks:
      items = []
    if remove_subnetworks:
      items = [x for x in items if x.subnetwork not in remove_subnetworks]
    if add_subnetworks:
      existing_subnetworks = set([x.subnetwork for x in items])
      items.extend([
          self.messages.CrossConnectItem(subnetwork=subnetwork)
          for subnetwork in add_subnetworks
          if subnetwork not in existing_subnetworks
      ])

    cross_connect_config = self.messages.CrossConnectConfig(
        fingerprint=existing_cross_connect_config.fingerprint, items=items)
    private_cluster_config = self.messages.PrivateClusterConfig(
        crossConnectConfig=cross_connect_config)
    update = self.messages.ClusterUpdate(
        desiredPrivateClusterConfig=private_cluster_config)
    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            update=update))

    return self.ParseOperation(op.name, cluster_ref.zone)

  def ModifyGoogleCloudAccess(self, cluster_ref, existing_authorized_networks,
                              goole_cloud_access):
    """Update enable_google_cloud_access and schedule cluster update request."""
    authorized_networks = self.messages.MasterAuthorizedNetworksConfig(
        enabled=existing_authorized_networks.enabled,
        cidrBlocks=existing_authorized_networks.cidrBlocks,
        gcpPublicCidrsAccessEnabled=goole_cloud_access)
    update = self.messages.ClusterUpdate(
        desiredMasterAuthorizedNetworksConfig=authorized_networks)
    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            update=update))
    return self.ParseOperation(op.name, cluster_ref.zone)

  def ModifyInsecureKubeletReadonlyPortEnabled(
      self, cluster_ref, readonly_port_enabled
  ):
    """Updates default for Kubelet Readonly Port on new node-pools."""
    nkc = self.messages.NodeKubeletConfig(
        insecureKubeletReadonlyPortEnabled=readonly_port_enabled,
    )
    update = self.messages.ClusterUpdate()
    update.desiredNodeKubeletConfig = nkc
    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(
                cluster_ref.projectId, cluster_ref.zone, cluster_ref.clusterId
            ),
            update=update,
        )
    )
    return self.ParseOperation(op.name, cluster_ref.zone)

  def ModifyAutoprovisioningInsecureKubeletReadonlyPortEnabled(
      self, cluster_ref, request_roport_enabled
  ):
    """Updates the kubelet readonly port on autoprovsioned node-pools or on autopilot clusters."""
    nkc = self.messages.NodeKubeletConfig(
        insecureKubeletReadonlyPortEnabled=request_roport_enabled,
    )
    update = self.messages.ClusterUpdate(
        desiredNodePoolAutoConfigKubeletConfig=nkc,
    )
    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(
                cluster_ref.projectId, cluster_ref.zone, cluster_ref.clusterId
            ),
            update=update,
        )
    )
    return self.ParseOperation(op.name, cluster_ref.zone)

  def ModifyBinaryAuthorization(
      self,
      cluster_ref,
      existing_binauthz_config,
      enable_binauthz,
      binauthz_evaluation_mode,
      binauthz_policy_bindings,
  ):
    """Updates the binary_authorization message."""

    # If the --(no-)binauthz-enabled flag is present the evaluation mode and
    # policy fields are set to None (if the user is enabling binauthz and
    # is currently using a platform policy evaluation mode the user is prompted
    # before performing this action). If either the --binauthz-evaluation-mode
    # or --binauthz-policy-bindings flags are passed the enabled field is set to
    # False and existing fields not overridden by a flag are preserved.
    if existing_binauthz_config is not None:
      binary_authorization = self.messages.BinaryAuthorization(
          evaluationMode=existing_binauthz_config.evaluationMode,
          policyBindings=existing_binauthz_config.policyBindings,
      )
    else:
      binary_authorization = self.messages.BinaryAuthorization()

    if enable_binauthz is not None:
      if enable_binauthz and BinauthzEvaluationModeRequiresPolicy(
          self.messages, binary_authorization.evaluationMode
      ):
        console_io.PromptContinue(
            message=(
                'This will cause the current version of Binary Authorization to'
                ' be downgraded (not recommended).'
            ),
            cancel_on_no=True,
        )
      binary_authorization = self.messages.BinaryAuthorization(
          enabled=enable_binauthz
      )
    else:
      if binauthz_evaluation_mode is not None:
        binary_authorization.evaluationMode = (
            util.GetBinauthzEvaluationModeMapper(
                self.messages, hidden=False
            ).GetEnumForChoice(binauthz_evaluation_mode)
        )

        # Clear the policy and policyBindings field if the updated evaluation
        # mode does not require a policy.
        if not BinauthzEvaluationModeRequiresPolicy(
            self.messages, binary_authorization.evaluationMode
        ):
          binary_authorization.policyBindings = []
      if binauthz_policy_bindings is not None:
        # New policy bindings passed to the cluster update command override
        # existing policy bindings.
        binary_authorization.policyBindings = []
        for binding in binauthz_policy_bindings:
          binary_authorization.policyBindings.append(
              self.messages.PolicyBinding(name=binding['name'])
          )
    update = self.messages.ClusterUpdate(
        desiredBinaryAuthorization=binary_authorization)
    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            update=update))
    return self.ParseOperation(op.name, cluster_ref.zone)


class V1Adapter(APIAdapter):
  """APIAdapter for v1."""


class V1Beta1Adapter(V1Adapter):
  """APIAdapter for v1beta1."""

  def CreateCluster(self, cluster_ref, options):
    cluster = self.CreateClusterCommon(cluster_ref, options)
    if options.addons:
      # CloudRun is disabled by default.
      if any((v in options.addons) for v in CLOUDRUN_ADDONS):
        if not options.enable_stackdriver_kubernetes and (
            (options.monitoring is not None and
             SYSTEM not in options.monitoring) or
            (options.logging is not None and SYSTEM not in options.logging)):
          raise util.Error(CLOUDRUN_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG)
        if INGRESS not in options.addons:
          raise util.Error(CLOUDRUN_INGRESS_KUBERNETES_DISABLED_ERROR_MSG)
        load_balancer_type = _GetCloudRunLoadBalancerType(
            options, self.messages)
        cluster.addonsConfig.cloudRunConfig = self.messages.CloudRunConfig(
            disabled=False, loadBalancerType=load_balancer_type)
      # CloudBuild is disabled by default.
      if CLOUDBUILD in options.addons:
        if not options.enable_stackdriver_kubernetes and (
            (options.monitoring is not None and
             SYSTEM not in options.monitoring) or
            (options.logging is not None and SYSTEM not in options.logging)):
          raise util.Error(CLOUDBUILD_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG)
        cluster.addonsConfig.cloudBuildConfig = self.messages.CloudBuildConfig(
            enabled=True)
      # BackupRestore is disabled by default.
      if BACKUPRESTORE in options.addons:
        cluster.addonsConfig.gkeBackupAgentConfig = self.messages.GkeBackupAgentConfig(
            enabled=True)
      # Istio is disabled by default.
      if ISTIO in options.addons:
        istio_auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
        mtls = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_MUTUAL_TLS
        istio_config = options.istio_config
        if istio_config is not None:
          auth_config = istio_config.get('auth')
          if auth_config is not None:
            if auth_config == 'MTLS_STRICT':
              istio_auth = mtls
        cluster.addonsConfig.istioConfig = self.messages.IstioConfig(
            disabled=False, auth=istio_auth)
    if (options.enable_autoprovisioning is not None or
        options.autoscaling_profile is not None):
      cluster.autoscaling = self.CreateClusterAutoscalingCommon(
          None, options, False)
    if options.enable_workload_certificates:
      if not options.workload_pool:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='workload-pool',
                opt='enable-workload-certificates'))
      if cluster.workloadCertificates is None:
        cluster.workloadCertificates = self.messages.WorkloadCertificates()
      cluster.workloadCertificates.enableCertificates = options.enable_workload_certificates
    if options.enable_alts:
      if not options.workload_pool:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='workload-pool', opt='enable-alts'))
      if cluster.workloadAltsConfig is None:
        cluster.workloadAltsConfig = self.messages.WorkloadALTSConfig()
      cluster.workloadAltsConfig.enableAlts = options.enable_alts
    if options.enable_gke_oidc:
      cluster.gkeOidcConfig = self.messages.GkeOidcConfig(
          enabled=options.enable_gke_oidc)
    if options.enable_identity_service:
      cluster.identityServiceConfig = self.messages.IdentityServiceConfig(
          enabled=options.enable_identity_service)
    if options.enable_master_global_access is not None:
      if cluster.privateClusterConfig is None:
        cluster.privateClusterConfig = self.messages.PrivateClusterConfig()
      cluster.privateClusterConfig.masterGlobalAccessConfig = \
          self.messages.PrivateClusterMasterGlobalAccessConfig(
              enabled=options.enable_master_global_access)
    if options.security_group is not None:
      # The presence of the --security_group="foo" flag implies enabled=True.
      cluster.authenticatorGroupsConfig = (
          self.messages.AuthenticatorGroupsConfig(
              enabled=True, securityGroup=options.security_group))
    _AddPSCPrivateClustersOptionsToClusterForCreateCluster(
        cluster, options, self.messages)

    cluster_telemetry_type = self._GetClusterTelemetryType(
        options, cluster.loggingService, cluster.monitoringService)
    if cluster_telemetry_type is not None:
      cluster.clusterTelemetry = self.messages.ClusterTelemetry()
      cluster.clusterTelemetry.type = cluster_telemetry_type

    if cluster.clusterTelemetry:
      cluster.loggingService = None
      cluster.monitoringService = None

    if options.enable_workload_monitoring_eap:
      cluster.workloadMonitoringEnabledEap = True

    if options.enable_service_externalips is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.serviceExternalIpsConfig = self.messages.ServiceExternalIPsConfig(
          enabled=options.enable_service_externalips)
    if options.identity_provider:
      if options.workload_pool:
        cluster.workloadIdentityConfig.identityProvider = options.identity_provider
      else:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='workload-pool', opt='identity-provider'))

    if options.datapath_provider is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      if options.datapath_provider.lower() == 'legacy':
        cluster.networkConfig.datapathProvider = \
            self.messages.NetworkConfig.DatapathProviderValueValuesEnum.LEGACY_DATAPATH
      elif options.datapath_provider.lower() == 'advanced':
        cluster.networkConfig.datapathProvider = \
            self.messages.NetworkConfig.DatapathProviderValueValuesEnum.ADVANCED_DATAPATH
      else:
        raise util.Error(
            DATAPATH_PROVIDER_ILL_SPECIFIED_ERROR_MSG.format(
                provider=options.datapath_provider))

    cluster.master = _GetMasterForClusterCreate(options, self.messages)

    cluster.kubernetesObjectsExportConfig = _GetKubernetesObjectsExportConfigForClusterCreate(
        options, self.messages)

    if options.enable_experimental_vertical_pod_autoscaling is not None:
      cluster.verticalPodAutoscaling = self.messages.VerticalPodAutoscaling(
          enableExperimentalFeatures=options
          .enable_experimental_vertical_pod_autoscaling)
      if options.enable_experimental_vertical_pod_autoscaling:
        cluster.verticalPodAutoscaling.enabled = True

    if options.enable_cost_allocation:
      cluster.costManagementConfig = self.messages.CostManagementConfig(
          enabled=True)

    if options.stack_type is not None:
      cluster.ipAllocationPolicy.stackType = util.GetCreateStackTypeMapper(
          self.messages).GetEnumForChoice(options.stack_type)
    if options.ipv6_access_type is not None:
      cluster.ipAllocationPolicy.ipv6AccessType = util.GetIpv6AccessTypeMapper(
          self.messages).GetEnumForChoice(options.ipv6_access_type)

    if options.enable_dns_endpoint is not None:
      if cluster.controlPlaneEndpointsConfig is None:
        cluster.controlPlaneEndpointsConfig = (
            self.messages.ControlPlaneEndpointsConfig()
        )
      dns_endpoint_config = self.messages.DNSEndpointConfig(
          enabled=options.enable_dns_endpoint)
      cluster.controlPlaneEndpointsConfig.dnsEndpointConfig = (
          dns_endpoint_config
      )

    req = self.messages.CreateClusterRequest(
        parent=ProjectLocation(cluster_ref.projectId, cluster_ref.zone),
        cluster=cluster)
    operation = self.client.projects_locations_clusters.Create(req)
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def CreateNodePool(self, node_pool_ref, options):
    pool = self.CreateNodePoolCommon(node_pool_ref, options)
    req = self.messages.CreateNodePoolRequest(
        nodePool=pool,
        parent=ProjectLocationCluster(node_pool_ref.projectId,
                                      node_pool_ref.zone,
                                      node_pool_ref.clusterId))
    operation = self.client.projects_locations_clusters_nodePools.Create(req)
    return self.ParseOperation(operation.name, node_pool_ref.zone)

  def UpdateCluster(self, cluster_ref, options):
    update = self.UpdateClusterCommon(cluster_ref, options)

    if options.workload_pool:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              workloadPool=options.workload_pool))
    elif options.identity_provider:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              identityProvider=options.identity_provider))
    elif options.disable_workload_identity:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              workloadPool=''))

    if options.enable_workload_certificates is not None:
      update = self.messages.ClusterUpdate(
          desiredWorkloadCertificates=self.messages.WorkloadCertificates(
              enableCertificates=options.enable_workload_certificates))

    if options.enable_alts is not None:
      update = self.messages.ClusterUpdate(
          desiredWorkloadAltsConfig=self.messages.WorkloadALTSConfig(
              enableAlts=options.enable_alts))

    if options.enable_gke_oidc is not None:
      update = self.messages.ClusterUpdate(
          desiredGkeOidcConfig=self.messages.GkeOidcConfig(
              enabled=options.enable_gke_oidc))

    if options.enable_identity_service is not None:
      update = self.messages.ClusterUpdate(
          desiredIdentityServiceConfig=self.messages.IdentityServiceConfig(
              enabled=options.enable_identity_service))

    if options.enable_stackdriver_kubernetes:
      update = self.messages.ClusterUpdate(
          desiredClusterTelemetry=self.messages.ClusterTelemetry(
              type=self.messages.ClusterTelemetry.TypeValueValuesEnum.ENABLED))
    elif options.enable_logging_monitoring_system_only:
      update = self.messages.ClusterUpdate(
          desiredClusterTelemetry=self.messages.ClusterTelemetry(
              type=self.messages.ClusterTelemetry.TypeValueValuesEnum
              .SYSTEM_ONLY))
    elif options.enable_stackdriver_kubernetes is not None:
      update = self.messages.ClusterUpdate(
          desiredClusterTelemetry=self.messages.ClusterTelemetry(
              type=self.messages.ClusterTelemetry.TypeValueValuesEnum.DISABLED))

    if options.enable_workload_monitoring_eap is not None:
      update = self.messages.ClusterUpdate(
          desiredWorkloadMonitoringEapConfig=self.messages
          .WorkloadMonitoringEapConfig(
              enabled=options.enable_workload_monitoring_eap))

    if options.enable_experimental_vertical_pod_autoscaling is not None:
      update = self.messages.ClusterUpdate(
          desiredVerticalPodAutoscaling=self.messages.VerticalPodAutoscaling(
              enableExperimentalFeatures=options
              .enable_experimental_vertical_pod_autoscaling))
      if options.enable_experimental_vertical_pod_autoscaling:
        update.desiredVerticalPodAutoscaling.enabled = True

    if options.security_group is not None:
      update = self.messages.ClusterUpdate(
          desiredAuthenticatorGroupsConfig=self.messages
          .AuthenticatorGroupsConfig(
              enabled=True, securityGroup=options.security_group))

    master = _GetMasterForClusterUpdate(options, self.messages)
    if master is not None:
      update = self.messages.ClusterUpdate(desiredMaster=master)

    kubernetes_objects_export_config = _GetKubernetesObjectsExportConfigForClusterUpdate(
        options, self.messages)
    if kubernetes_objects_export_config is not None:
      update = self.messages.ClusterUpdate(
          desiredKubernetesObjectsExportConfig=kubernetes_objects_export_config)

    if options.enable_service_externalips is not None:
      update = self.messages.ClusterUpdate(
          desiredServiceExternalIpsConfig=self.messages
          .ServiceExternalIPsConfig(enabled=options.enable_service_externalips))

    if options.dataplane_v2:
      update = self.messages.ClusterUpdate(
          desiredDatapathProvider=(
              self.messages.ClusterUpdate.DesiredDatapathProviderValueValuesEnum
              .ADVANCED_DATAPATH))

    if options.enable_cost_allocation is not None:
      update = self.messages.ClusterUpdate(
          desiredCostManagementConfig=self.messages.CostManagementConfig(
              enabled=options.enable_cost_allocation))

    if options.convert_to_autopilot is not None:
      update = self.messages.ClusterUpdate(
          desiredAutopilot=self.messages.Autopilot(enabled=True))

    if options.convert_to_standard is not None:
      update = self.messages.ClusterUpdate(
          desiredAutopilot=self.messages.Autopilot(enabled=False))

    if not update:
      # if reached here, it's possible:
      # - someone added update flags but not handled
      # - none of the update flags specified from command line
      # so raise an error with readable message like:
      #   Nothing to update
      # to catch this error.
      raise util.Error(NOTHING_TO_UPDATE_ERROR_MSG)

    if options.disable_addons is not None:
      if options.disable_addons.get(ISTIO) is not None:
        istio_auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
        mtls = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_MUTUAL_TLS
        istio_config = options.istio_config
        if istio_config is not None:
          auth_config = istio_config.get('auth')
          if auth_config is not None:
            if auth_config == 'MTLS_STRICT':
              istio_auth = mtls
        update.desiredAddonsConfig.istioConfig = self.messages.IstioConfig(
            disabled=options.disable_addons.get(ISTIO), auth=istio_auth)
      if any(
          (options.disable_addons.get(v) is not None) for v in CLOUDRUN_ADDONS):
        load_balancer_type = _GetCloudRunLoadBalancerType(
            options, self.messages)
        update.desiredAddonsConfig.cloudRunConfig = (
            self.messages.CloudRunConfig(
                disabled=any(
                    options.disable_addons.get(v) or False
                    for v in CLOUDRUN_ADDONS),
                loadBalancerType=load_balancer_type))
      if options.disable_addons.get(APPLICATIONMANAGER) is not None:
        update.desiredAddonsConfig.kalmConfig = (
            self.messages.KalmConfig(
                enabled=(not options.disable_addons.get(APPLICATIONMANAGER))))
      if options.disable_addons.get(CLOUDBUILD) is not None:
        update.desiredAddonsConfig.cloudBuildConfig = (
            self.messages.CloudBuildConfig(
                enabled=(not options.disable_addons.get(CLOUDBUILD))))

    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            update=update))
    return self.ParseOperation(op.name, cluster_ref.zone)

  def CompleteConvertToAutopilot(self, cluster_ref):
    """Commmit the Autopilot conversion operation.

    Args:
      cluster_ref: cluster resource to commit conversion.

    Returns:
      The operation to be executed.

    Raises:
      exceptions.HttpException: if cluster cannot be found or caller is missing
        permissions. Will attempt to find similar clusters in other zones for a
        more useful error if the user has list permissions.
    """
    try:
      op = self.client.projects_locations_clusters.CompleteConvertToAutopilot(
          self.messages.ContainerProjectsLocationsClustersCompleteConvertToAutopilotRequest(
              name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref
                                          .zone, cluster_ref.clusterId)))
      return self.ParseOperation(op.name, cluster_ref.zone)
    except apitools_exceptions.HttpNotFoundError as error:
      api_error = exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
      # Cluster couldn't be found, maybe user got the location wrong?
      self.CheckClusterOtherZones(cluster_ref, api_error)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

  def CreateClusterAutoscalingCommon(self, cluster_ref, options, for_update):
    """Create cluster's autoscaling configuration.

    Args:
      cluster_ref: Cluster reference.
      options: Either CreateClusterOptions or UpdateClusterOptions.
      for_update: Is function executed for update operation.

    Returns:
      Cluster's autoscaling configuration.
    """

    # Patch cluster autoscaling if cluster_ref is provided.
    autoscaling = self.messages.ClusterAutoscaling()
    cluster = self.GetCluster(cluster_ref) if cluster_ref else None
    if cluster and cluster.autoscaling:
      autoscaling.enableNodeAutoprovisioning = \
          cluster.autoscaling.enableNodeAutoprovisioning

    resource_limits = []
    if options.autoprovisioning_config_file is not None:
      # Create using config file only.
      config = yaml.load(options.autoprovisioning_config_file)
      resource_limits = config.get(RESOURCE_LIMITS)
      service_account = config.get(SERVICE_ACCOUNT)
      scopes = config.get(SCOPES)
      max_surge_upgrade = None
      max_unavailable_upgrade = None
      upgrade_settings = config.get(UPGRADE_SETTINGS)
      if upgrade_settings:
        max_surge_upgrade = upgrade_settings.get(MAX_SURGE_UPGRADE)
        max_unavailable_upgrade = upgrade_settings.get(MAX_UNAVAILABLE_UPGRADE)
      management_settings = config.get(NODE_MANAGEMENT)
      enable_autoupgrade = None
      enable_autorepair = None
      if management_settings:
        enable_autoupgrade = management_settings.get(ENABLE_AUTO_UPGRADE)
        enable_autorepair = management_settings.get(ENABLE_AUTO_REPAIR)
      autoprovisioning_locations = \
        config.get(AUTOPROVISIONING_LOCATIONS)
      min_cpu_platform = config.get(MIN_CPU_PLATFORM)
      boot_disk_kms_key = config.get(BOOT_DISK_KMS_KEY)
      disk_type = config.get(DISK_TYPE)
      disk_size_gb = config.get(DISK_SIZE_GB)
      autoprovisioning_image_type = config.get(IMAGE_TYPE)
      shielded_instance_config = config.get(SHIELDED_INSTANCE_CONFIG)
      enable_secure_boot = None
      enable_integrity_monitoring = None
      if shielded_instance_config:
        enable_secure_boot = shielded_instance_config.get(ENABLE_SECURE_BOOT)
        enable_integrity_monitoring = \
            shielded_instance_config.get(ENABLE_INTEGRITY_MONITORING)
    else:
      resource_limits = self.ResourceLimitsFromFlags(options)
      service_account = options.autoprovisioning_service_account
      scopes = options.autoprovisioning_scopes
      autoprovisioning_locations = options.autoprovisioning_locations
      max_surge_upgrade = options.autoprovisioning_max_surge_upgrade
      max_unavailable_upgrade = options.autoprovisioning_max_unavailable_upgrade
      enable_autoupgrade = options.enable_autoprovisioning_autoupgrade
      enable_autorepair = options.enable_autoprovisioning_autorepair
      min_cpu_platform = options.autoprovisioning_min_cpu_platform
      boot_disk_kms_key = None
      disk_type = None
      disk_size_gb = None
      autoprovisioning_image_type = options.autoprovisioning_image_type
      enable_secure_boot = None
      enable_integrity_monitoring = None

    if options.enable_autoprovisioning is not None:
      autoscaling.enableNodeAutoprovisioning = options.enable_autoprovisioning
      autoscaling.resourceLimits = resource_limits or []
      if scopes is None:
        scopes = []
      management = None
      upgrade_settings = None
      if (max_surge_upgrade is not None or
          max_unavailable_upgrade is not None or
          options.enable_autoprovisioning_blue_green_upgrade or
          options.enable_autoprovisioning_surge_upgrade or
          options.autoprovisioning_standard_rollout_policy is not None or
          options.autoprovisioning_node_pool_soak_duration is not None):
        upgrade_settings = self.UpdateUpgradeSettingsForNAP(
            options, max_surge_upgrade, max_unavailable_upgrade)
      if enable_autorepair is not None or enable_autoupgrade is not None:
        management = (
            self.messages.NodeManagement(
                autoUpgrade=enable_autoupgrade, autoRepair=enable_autorepair))
      shielded_instance_config = None
      if enable_secure_boot is not None or \
          enable_integrity_monitoring is not None:
        shielded_instance_config = self.messages.ShieldedInstanceConfig()
        shielded_instance_config.enableSecureBoot = enable_secure_boot
        shielded_instance_config.enableIntegrityMonitoring = \
            enable_integrity_monitoring
      if for_update:
        autoscaling.autoprovisioningNodePoolDefaults = (
            self.messages.AutoprovisioningNodePoolDefaults(
                serviceAccount=service_account,
                oauthScopes=scopes,
                upgradeSettings=upgrade_settings,
                management=management,
                minCpuPlatform=min_cpu_platform,
                bootDiskKmsKey=boot_disk_kms_key,
                diskSizeGb=disk_size_gb,
                diskType=disk_type,
                imageType=autoprovisioning_image_type,
                shieldedInstanceConfig=shielded_instance_config,
            )
        )
      else:
        autoscaling.autoprovisioningNodePoolDefaults = (
            self.messages.AutoprovisioningNodePoolDefaults(
                serviceAccount=service_account,
                oauthScopes=scopes,
                upgradeSettings=upgrade_settings,
                management=management,
                minCpuPlatform=min_cpu_platform,
                bootDiskKmsKey=boot_disk_kms_key,
                diskSizeGb=disk_size_gb,
                diskType=disk_type,
                imageType=autoprovisioning_image_type,
                shieldedInstanceConfig=shielded_instance_config,
            )
        )
      if autoprovisioning_locations:
        autoscaling.autoprovisioningLocations = \
          sorted(autoprovisioning_locations)

    if options.autoscaling_profile is not None:
      autoscaling.autoscalingProfile = \
          self.CreateAutoscalingProfileCommon(options)

    self.ValidateClusterAutoscaling(autoscaling, for_update)
    return autoscaling

  def ValidateClusterAutoscaling(self, autoscaling, for_update):
    """Validate cluster autoscaling configuration.

    Args:
      autoscaling: autoscaling configuration to be validated.
      for_update: Is function executed for update operation.

    Raises:
      Error if the new configuration is invalid.
    """
    if autoscaling.enableNodeAutoprovisioning:
      if not for_update or autoscaling.resourceLimits:
        cpu_found = any(
            limit.resourceType == 'cpu' for limit in autoscaling.resourceLimits)
        mem_found = any(limit.resourceType == 'memory'
                        for limit in autoscaling.resourceLimits)
        if not cpu_found or not mem_found:
          raise util.Error(NO_AUTOPROVISIONING_LIMITS_ERROR_MSG)
        defaults = autoscaling.autoprovisioningNodePoolDefaults
        if defaults:
          if defaults.upgradeSettings:
            max_surge_found = defaults.upgradeSettings.maxSurge is not None
            max_unavailable_found = defaults.upgradeSettings.maxUnavailable is not None
            if max_unavailable_found != max_surge_found:
              raise util.Error(BOTH_AUTOPROVISIONING_UPGRADE_SETTINGS_ERROR_MSG)
          if defaults.management:
            auto_upgrade_found = defaults.management.autoUpgrade is not None
            auto_repair_found = defaults.management.autoRepair is not None
            if auto_repair_found != auto_upgrade_found:
              raise util.Error(
                  BOTH_AUTOPROVISIONING_MANAGEMENT_SETTINGS_ERROR_MSG)
          if defaults.shieldedInstanceConfig:
            secure_boot_found = defaults.shieldedInstanceConfig.enableSecureBoot is not None
            integrity_monitoring_found = defaults.shieldedInstanceConfig.enableIntegrityMonitoring is not None
            if secure_boot_found != integrity_monitoring_found:
              raise util.Error(
                  BOTH_AUTOPROVISIONING_SHIELDED_INSTANCE_SETTINGS_ERROR_MSG)
    elif autoscaling.resourceLimits:
      raise util.Error(LIMITS_WITHOUT_AUTOPROVISIONING_MSG)
    elif autoscaling.autoprovisioningNodePoolDefaults and \
        (autoscaling.autoprovisioningNodePoolDefaults.serviceAccount or
         autoscaling.autoprovisioningNodePoolDefaults.oauthScopes or
         autoscaling.autoprovisioningNodePoolDefaults.management or
         autoscaling.autoprovisioningNodePoolDefaults.upgradeSettings):
      raise util.Error(DEFAULTS_WITHOUT_AUTOPROVISIONING_MSG)

  def UpdateNodePool(self, node_pool_ref, options):
    if options.IsAutoscalingUpdate():
      autoscaling = self.UpdateNodePoolAutoscaling(node_pool_ref, options)
      update = self.messages.ClusterUpdate(
          desiredNodePoolId=node_pool_ref.nodePoolId,
          desiredNodePoolAutoscaling=autoscaling)
      operation = self.client.projects_locations_clusters.Update(
          self.messages.UpdateClusterRequest(
              name=ProjectLocationCluster(node_pool_ref.projectId,
                                          node_pool_ref.zone,
                                          node_pool_ref.clusterId),
              update=update))
      return self.ParseOperation(operation.name, node_pool_ref.zone)
    elif options.IsNodePoolManagementUpdate():
      management = self.UpdateNodePoolNodeManagement(node_pool_ref, options)
      req = (
          self.messages.SetNodePoolManagementRequest(
              name=ProjectLocationClusterNodePool(node_pool_ref.projectId,
                                                  node_pool_ref.zone,
                                                  node_pool_ref.clusterId,
                                                  node_pool_ref.nodePoolId),
              management=management))
      operation = (
          self.client.projects_locations_clusters_nodePools.SetManagement(req))
    elif options.IsUpdateNodePoolRequest():
      req = self.UpdateNodePoolRequest(node_pool_ref, options)
      operation = self.client.projects_locations_clusters_nodePools.Update(req)
    else:
      raise util.Error('Unhandled node pool update mode')

    return self.ParseOperation(operation.name, node_pool_ref.zone)


class V1Alpha1Adapter(V1Beta1Adapter):
  """APIAdapter for v1alpha1."""

  def CreateCluster(self, cluster_ref, options):
    cluster = self.CreateClusterCommon(cluster_ref, options)
    if (options.enable_autoprovisioning is not None or
        options.autoscaling_profile is not None):
      cluster.autoscaling = self.CreateClusterAutoscalingCommon(
          None, options, False)
    if options.addons:
      # CloudRun is disabled by default.
      if any((v in options.addons) for v in CLOUDRUN_ADDONS):
        if not options.enable_stackdriver_kubernetes and (
            (options.monitoring is not None and
             SYSTEM not in options.monitoring) or
            (options.logging is not None and SYSTEM not in options.logging)):
          raise util.Error(CLOUDRUN_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG)
        if INGRESS not in options.addons:
          raise util.Error(CLOUDRUN_INGRESS_KUBERNETES_DISABLED_ERROR_MSG)
        enable_alpha_features = options.enable_cloud_run_alpha if \
            options.enable_cloud_run_alpha is not None else False
        load_balancer_type = _GetCloudRunLoadBalancerType(
            options, self.messages)
        cluster.addonsConfig.cloudRunConfig = self.messages.CloudRunConfig(
            disabled=False,
            enableAlphaFeatures=enable_alpha_features,
            loadBalancerType=load_balancer_type)
      # Cloud Build is disabled by default.
      if CLOUDBUILD in options.addons:
        if not options.enable_stackdriver_kubernetes and (
            (options.monitoring is not None and
             SYSTEM not in options.monitoring) or
            (options.logging is not None and SYSTEM not in options.logging)):
          raise util.Error(CLOUDBUILD_STACKDRIVER_KUBERNETES_DISABLED_ERROR_MSG)
        cluster.addonsConfig.cloudBuildConfig = self.messages.CloudBuildConfig(
            enabled=True)
      # BackupRestore is disabled by default.
      if BACKUPRESTORE in options.addons:
        cluster.addonsConfig.gkeBackupAgentConfig = self.messages.GkeBackupAgentConfig(
            enabled=True)
      # Istio is disabled by default
      if ISTIO in options.addons:
        istio_auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
        mtls = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_MUTUAL_TLS
        istio_config = options.istio_config
        if istio_config is not None:
          auth_config = istio_config.get('auth')
          if auth_config is not None:
            if auth_config == 'MTLS_STRICT':
              istio_auth = mtls
        cluster.addonsConfig.istioConfig = self.messages.IstioConfig(
            disabled=False, auth=istio_auth)
    if options.enable_workload_certificates:
      if not options.workload_pool:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='workload-pool',
                opt='enable-workload-certificates'))
      if cluster.workloadCertificates is None:
        cluster.workloadCertificates = self.messages.WorkloadCertificates()
      cluster.workloadCertificates.enableCertificates = options.enable_workload_certificates
    if options.enable_alts:
      if not options.workload_pool:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='workload-pool', opt='enable-alts'))
      if cluster.workloadAltsConfig is None:
        cluster.workloadAltsConfig = self.messages.WorkloadALTSConfig()
      cluster.workloadAltsConfig.enableAlts = options.enable_alts
    if options.enable_gke_oidc:
      cluster.gkeOidcConfig = self.messages.GkeOidcConfig(
          enabled=options.enable_gke_oidc)
    if options.enable_identity_service:
      cluster.identityServiceConfig = self.messages.IdentityServiceConfig(
          enabled=options.enable_identity_service)
    if options.security_profile is not None:
      cluster.securityProfile = self.messages.SecurityProfile(
          name=options.security_profile)
      if options.security_profile_runtime_rules is not None:
        cluster.securityProfile.disableRuntimeRules = \
          not options.security_profile_runtime_rules
    if options.enable_private_ipv6_access is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig(
            enablePrivateIpv6Access=options.enable_private_ipv6_access)
      else:
        cluster.networkConfig.enablePrivateIpv6Access = \
            options.enable_private_ipv6_access
    if options.enable_service_externalips is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      cluster.networkConfig.serviceExternalIpsConfig = self.messages.ServiceExternalIPsConfig(
          enabled=options.enable_service_externalips)
    if options.enable_master_global_access is not None:
      if cluster.privateClusterConfig is None:
        cluster.privateClusterConfig = self.messages.PrivateClusterConfig()
      cluster.privateClusterConfig.masterGlobalAccessConfig = \
          self.messages.PrivateClusterMasterGlobalAccessConfig(
              enabled=options.enable_master_global_access)
    if options.security_group is not None:
      # The presence of the --security_group="foo" flag implies enabled=True.
      cluster.authenticatorGroupsConfig = (
          self.messages.AuthenticatorGroupsConfig(
              enabled=True, securityGroup=options.security_group))
    _AddPSCPrivateClustersOptionsToClusterForCreateCluster(
        cluster, options, self.messages)

    cluster.releaseChannel = _GetReleaseChannel(options, self.messages)
    if options.enable_cost_allocation:
      cluster.costManagementConfig = self.messages.CostManagementConfig(
          enabled=True)

    cluster_telemetry_type = self._GetClusterTelemetryType(
        options, cluster.loggingService, cluster.monitoringService)
    if cluster_telemetry_type is not None:
      cluster.clusterTelemetry = self.messages.ClusterTelemetry()
      cluster.clusterTelemetry.type = cluster_telemetry_type

    if cluster.clusterTelemetry:
      cluster.loggingService = None
      cluster.monitoringService = None

    if options.enable_workload_monitoring_eap:
      cluster.workloadMonitoringEnabledEap = True

    if options.datapath_provider is not None:
      if cluster.networkConfig is None:
        cluster.networkConfig = self.messages.NetworkConfig()
      if options.datapath_provider.lower() == 'legacy':
        cluster.networkConfig.datapathProvider = \
            self.messages.NetworkConfig.DatapathProviderValueValuesEnum.LEGACY_DATAPATH
      elif options.datapath_provider.lower() == 'advanced':
        cluster.networkConfig.datapathProvider = \
            self.messages.NetworkConfig.DatapathProviderValueValuesEnum.ADVANCED_DATAPATH
      else:
        raise util.Error(
            DATAPATH_PROVIDER_ILL_SPECIFIED_ERROR_MSG.format(
                provider=options.datapath_provider))

    if options.enable_experimental_vertical_pod_autoscaling is not None:
      cluster.verticalPodAutoscaling = self.messages.VerticalPodAutoscaling(
          enableExperimentalFeatures=options
          .enable_experimental_vertical_pod_autoscaling)
      if options.enable_experimental_vertical_pod_autoscaling:
        cluster.verticalPodAutoscaling.enabled = True

    if options.identity_provider:
      if options.workload_pool:
        cluster.workloadIdentityConfig.identityProvider = options.identity_provider
      else:
        raise util.Error(
            PREREQUISITE_OPTION_ERROR_MSG.format(
                prerequisite='workload-pool', opt='identity-provider'))

    if options.stack_type is not None:
      cluster.ipAllocationPolicy.stackType = util.GetCreateStackTypeMapper(
          self.messages).GetEnumForChoice(options.stack_type)

    if options.ipv6_access_type is not None:
      cluster.ipAllocationPolicy.ipv6AccessType = util.GetIpv6AccessTypeMapper(
          self.messages).GetEnumForChoice(options.ipv6_access_type)
    cluster.master = _GetMasterForClusterCreate(options, self.messages)

    if options.enable_dns_endpoint is not None:
      if cluster.controlPlaneEndpointsConfig is None:
        cluster.controlPlaneEndpointsConfig = (
            self.messages.ControlPlaneEndpointsConfig()
        )
      dns_endpoint_config = self.messages.DNSEndpointConfig(
          enabled=options.enable_dns_endpoint)
      cluster.controlPlaneEndpointsConfig.dnsEndpointConfig = (
          dns_endpoint_config
      )

    cluster.kubernetesObjectsExportConfig = _GetKubernetesObjectsExportConfigForClusterCreate(
        options, self.messages)

    req = self.messages.CreateClusterRequest(
        parent=ProjectLocation(cluster_ref.projectId, cluster_ref.zone),
        cluster=cluster)
    operation = self.client.projects_locations_clusters.Create(req)
    return self.ParseOperation(operation.name, cluster_ref.zone)

  def UpdateCluster(self, cluster_ref, options):
    update = self.UpdateClusterCommon(cluster_ref, options)

    if options.workload_pool:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              workloadPool=options.workload_pool))
    elif options.identity_provider:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              identityProvider=options.identity_provider))
    elif options.disable_workload_identity:
      update = self.messages.ClusterUpdate(
          desiredWorkloadIdentityConfig=self.messages.WorkloadIdentityConfig(
              workloadPool=''))

    if options.enable_workload_certificates is not None:
      update = self.messages.ClusterUpdate(
          desiredWorkloadCertificates=self.messages.WorkloadCertificates(
              enableCertificates=options.enable_workload_certificates))

    if options.enable_alts is not None:
      update = self.messages.ClusterUpdate(
          desiredWorkloadAltsConfig=self.messages.WorkloadALTSConfig(
              enableAlts=options.enable_alts))

    if options.enable_gke_oidc is not None:
      update = self.messages.ClusterUpdate(
          desiredGkeOidcConfig=self.messages.GkeOidcConfig(
              enabled=options.enable_gke_oidc))

    if options.enable_identity_service is not None:
      update = self.messages.ClusterUpdate(
          desiredIdentityServiceConfig=self.messages.IdentityServiceConfig(
              enabled=options.enable_identity_service))

    if options.enable_cost_allocation is not None:
      update = self.messages.ClusterUpdate(
          desiredCostManagementConfig=self.messages.CostManagementConfig(
              enabled=options.enable_cost_allocation))

    if options.release_channel is not None:
      update = self.messages.ClusterUpdate(
          desiredReleaseChannel=_GetReleaseChannel(options, self.messages))

    if options.enable_stackdriver_kubernetes:
      update = self.messages.ClusterUpdate(
          desiredClusterTelemetry=self.messages.ClusterTelemetry(
              type=self.messages.ClusterTelemetry.TypeValueValuesEnum.ENABLED))
    elif options.enable_logging_monitoring_system_only:
      update = self.messages.ClusterUpdate(
          desiredClusterTelemetry=self.messages.ClusterTelemetry(
              type=self.messages.ClusterTelemetry.TypeValueValuesEnum
              .SYSTEM_ONLY))
    elif options.enable_stackdriver_kubernetes is not None:
      update = self.messages.ClusterUpdate(
          desiredClusterTelemetry=self.messages.ClusterTelemetry(
              type=self.messages.ClusterTelemetry.TypeValueValuesEnum.DISABLED))

    if options.enable_workload_monitoring_eap is not None:
      update = self.messages.ClusterUpdate(
          desiredWorkloadMonitoringEapConfig=self.messages
          .WorkloadMonitoringEapConfig(
              enabled=options.enable_workload_monitoring_eap))

    if options.enable_experimental_vertical_pod_autoscaling is not None:
      update = self.messages.ClusterUpdate(
          desiredVerticalPodAutoscaling=self.messages.VerticalPodAutoscaling(
              enableExperimentalFeatures=options
              .enable_experimental_vertical_pod_autoscaling))
      if options.enable_experimental_vertical_pod_autoscaling:
        update.desiredVerticalPodAutoscaling.enabled = True

    if options.security_group is not None:
      update = self.messages.ClusterUpdate(
          desiredAuthenticatorGroupsConfig=self.messages
          .AuthenticatorGroupsConfig(
              enabled=True, securityGroup=options.security_group))

    master = _GetMasterForClusterUpdate(options, self.messages)
    if master is not None:
      update = self.messages.ClusterUpdate(desiredMaster=master)

    kubernetes_objects_export_config = _GetKubernetesObjectsExportConfigForClusterUpdate(
        options, self.messages)
    if kubernetes_objects_export_config is not None:
      update = self.messages.ClusterUpdate(
          desiredKubernetesObjectsExportConfig=kubernetes_objects_export_config)

    if options.enable_service_externalips is not None:
      update = self.messages.ClusterUpdate(
          desiredServiceExternalIpsConfig=self.messages
          .ServiceExternalIPsConfig(enabled=options.enable_service_externalips))

    if options.dataplane_v2:
      update = self.messages.ClusterUpdate(
          desiredDatapathProvider=(
              self.messages.ClusterUpdate.DesiredDatapathProviderValueValuesEnum
              .ADVANCED_DATAPATH))

    if options.convert_to_autopilot is not None:
      update = self.messages.ClusterUpdate(
          desiredAutopilot=self.messages.Autopilot(enabled=True))

    if options.convert_to_standard is not None:
      update = self.messages.ClusterUpdate(
          desiredAutopilot=self.messages.Autopilot(enabled=False))

    if not update:
      # if reached here, it's possible:
      # - someone added update flags but not handled
      # - none of the update flags specified from command line
      # so raise an error with readable message like:
      #   Nothing to update
      # to catch this error.
      raise util.Error(NOTHING_TO_UPDATE_ERROR_MSG)

    if options.disable_addons is not None:
      if options.disable_addons.get(ISTIO) is not None:
        istio_auth = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
        mtls = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_MUTUAL_TLS
        istio_config = options.istio_config
        if istio_config is not None:
          auth_config = istio_config.get('auth')
          if auth_config is not None:
            if auth_config == 'MTLS_STRICT':
              istio_auth = mtls
        update.desiredAddonsConfig.istioConfig = self.messages.IstioConfig(
            disabled=options.disable_addons.get(ISTIO), auth=istio_auth)
      if any(
          (options.disable_addons.get(v) is not None) for v in CLOUDRUN_ADDONS):
        load_balancer_type = _GetCloudRunLoadBalancerType(
            options, self.messages)
        update.desiredAddonsConfig.cloudRunConfig = (
            self.messages.CloudRunConfig(
                disabled=any(
                    options.disable_addons.get(v) or False
                    for v in CLOUDRUN_ADDONS),
                loadBalancerType=load_balancer_type))
      if options.disable_addons.get(APPLICATIONMANAGER) is not None:
        update.desiredAddonsConfig.kalmConfig = (
            self.messages.KalmConfig(
                enabled=(not options.disable_addons.get(APPLICATIONMANAGER))))
      if options.disable_addons.get(CLOUDBUILD) is not None:
        update.desiredAddonsConfig.cloudBuildConfig = (
            self.messages.CloudBuildConfig(
                enabled=(not options.disable_addons.get(CLOUDBUILD))))

    op = self.client.projects_locations_clusters.Update(
        self.messages.UpdateClusterRequest(
            name=ProjectLocationCluster(cluster_ref.projectId, cluster_ref.zone,
                                        cluster_ref.clusterId),
            update=update))
    return self.ParseOperation(op.name, cluster_ref.zone)

  def CreateNodePool(self, node_pool_ref, options):
    pool = self.CreateNodePoolCommon(node_pool_ref, options)
    req = self.messages.CreateNodePoolRequest(
        nodePool=pool,
        parent=ProjectLocationCluster(node_pool_ref.projectId,
                                      node_pool_ref.zone,
                                      node_pool_ref.clusterId))
    operation = self.client.projects_locations_clusters_nodePools.Create(req)
    return self.ParseOperation(operation.name, node_pool_ref.zone)

  def CreateClusterAutoscalingCommon(self, cluster_ref, options, for_update):
    """Create cluster's autoscaling configuration.

    Args:
      cluster_ref: Cluster reference.
      options: Either CreateClusterOptions or UpdateClusterOptions.
      for_update: Is function executed for update operation.

    Returns:
      Cluster's autoscaling configuration.
    """
    # Patch cluster autoscaling if cluster_ref is provided.
    cluster = None
    autoscaling = self.messages.ClusterAutoscaling()
    if cluster_ref:
      cluster = self.GetCluster(cluster_ref)
    if cluster and cluster.autoscaling:
      autoscaling.enableNodeAutoprovisioning = \
          cluster.autoscaling.enableNodeAutoprovisioning

    resource_limits = []
    if options.autoprovisioning_config_file is not None:
      # Create using config file only.
      config = yaml.load(options.autoprovisioning_config_file)
      resource_limits = config.get(RESOURCE_LIMITS)
      service_account = config.get(SERVICE_ACCOUNT)
      scopes = config.get(SCOPES)
      max_surge_upgrade = None
      max_unavailable_upgrade = None
      upgrade_settings = config.get(UPGRADE_SETTINGS)
      if upgrade_settings:
        max_surge_upgrade = upgrade_settings.get(MAX_SURGE_UPGRADE)
        max_unavailable_upgrade = upgrade_settings.get(MAX_UNAVAILABLE_UPGRADE)
      management_settings = config.get(NODE_MANAGEMENT)
      enable_autoupgrade = None
      enable_autorepair = None
      if management_settings is not None:
        enable_autoupgrade = management_settings.get(ENABLE_AUTO_UPGRADE)
        enable_autorepair = management_settings.get(ENABLE_AUTO_REPAIR)
      autoprovisioning_locations = \
          config.get(AUTOPROVISIONING_LOCATIONS)
      min_cpu_platform = config.get(MIN_CPU_PLATFORM)
      boot_disk_kms_key = config.get(BOOT_DISK_KMS_KEY)
      disk_type = config.get(DISK_TYPE)
      disk_size_gb = config.get(DISK_SIZE_GB)
      autoprovisioning_image_type = config.get(IMAGE_TYPE)
      shielded_instance_config = config.get(SHIELDED_INSTANCE_CONFIG)
      enable_secure_boot = None
      enable_integrity_monitoring = None
      if shielded_instance_config:
        enable_secure_boot = shielded_instance_config.get(ENABLE_SECURE_BOOT)
        enable_integrity_monitoring = \
            shielded_instance_config.get(ENABLE_INTEGRITY_MONITORING)
    else:
      resource_limits = self.ResourceLimitsFromFlags(options)
      service_account = options.autoprovisioning_service_account
      scopes = options.autoprovisioning_scopes
      autoprovisioning_locations = options.autoprovisioning_locations
      max_surge_upgrade = options.autoprovisioning_max_surge_upgrade
      max_unavailable_upgrade = options.autoprovisioning_max_unavailable_upgrade
      enable_autoupgrade = options.enable_autoprovisioning_autoupgrade
      enable_autorepair = options.enable_autoprovisioning_autorepair
      min_cpu_platform = options.autoprovisioning_min_cpu_platform
      boot_disk_kms_key = None
      disk_type = None
      disk_size_gb = None
      autoprovisioning_image_type = options.autoprovisioning_image_type
      enable_secure_boot = None
      enable_integrity_monitoring = None

    if options.enable_autoprovisioning is not None:
      autoscaling.enableNodeAutoprovisioning = options.enable_autoprovisioning
      if resource_limits is None:
        resource_limits = []
      autoscaling.resourceLimits = resource_limits
      if scopes is None:
        scopes = []
      management = None
      upgrade_settings = None
      if (max_surge_upgrade is not None or
          max_unavailable_upgrade is not None or
          options.enable_autoprovisioning_blue_green_upgrade or
          options.enable_autoprovisioning_surge_upgrade or
          options.autoprovisioning_standard_rollout_policy is not None or
          options.autoprovisioning_node_pool_soak_duration is not None):
        upgrade_settings = self.UpdateUpgradeSettingsForNAP(
            options, max_surge_upgrade, max_unavailable_upgrade)
      if enable_autorepair is not None or enable_autorepair is not None:
        management = self.messages \
          .NodeManagement(autoUpgrade=enable_autoupgrade,
                          autoRepair=enable_autorepair)
      shielded_instance_config = None
      if enable_secure_boot is not None or \
          enable_integrity_monitoring is not None:
        shielded_instance_config = self.messages.ShieldedInstanceConfig()
        shielded_instance_config.enableSecureBoot = enable_secure_boot
        shielded_instance_config.enableIntegrityMonitoring = \
            enable_integrity_monitoring

      if for_update:
        autoscaling.autoprovisioningNodePoolDefaults = (
            self.messages.AutoprovisioningNodePoolDefaults(
                serviceAccount=service_account,
                oauthScopes=scopes,
                upgradeSettings=upgrade_settings,
                management=management,
                minCpuPlatform=min_cpu_platform,
                bootDiskKmsKey=boot_disk_kms_key,
                diskSizeGb=disk_size_gb,
                diskType=disk_type,
                imageType=autoprovisioning_image_type,
                shieldedInstanceConfig=shielded_instance_config,
            )
        )
      else:
        autoscaling.autoprovisioningNodePoolDefaults = (
            self.messages.AutoprovisioningNodePoolDefaults(
                serviceAccount=service_account,
                oauthScopes=scopes,
                upgradeSettings=upgrade_settings,
                management=management,
                minCpuPlatform=min_cpu_platform,
                bootDiskKmsKey=boot_disk_kms_key,
                diskSizeGb=disk_size_gb,
                diskType=disk_type,
                imageType=autoprovisioning_image_type,
                shieldedInstanceConfig=shielded_instance_config,
            )
        )

      if autoprovisioning_locations:
        autoscaling.autoprovisioningLocations = \
            sorted(autoprovisioning_locations)

    if options.autoscaling_profile is not None:
      autoscaling.autoscalingProfile = \
          self.CreateAutoscalingProfileCommon(options)

    self.ValidateClusterAutoscaling(autoscaling, for_update)
    return autoscaling

  def ParseNodePools(self, options, node_config):
    """Creates a list of node pools for the cluster by parsing options.

    Args:
      options: cluster creation options
      node_config: node configuration for nodes in the node pools

    Returns:
      List of node pools.
    """
    max_nodes_per_pool = options.max_nodes_per_pool or MAX_NODES_PER_POOL
    num_pools = (options.num_nodes + max_nodes_per_pool -
                 1) // max_nodes_per_pool
    # pool consistency with server default
    node_pool_name = options.node_pool_name or 'default-pool'

    if num_pools == 1:
      pool_names = [node_pool_name]
    else:
      # default-pool-0, -1, ... or some-pool-0, -1 where some-pool is user
      # supplied
      pool_names = [
          '{0}-{1}'.format(node_pool_name, i) for i in range(0, num_pools)
      ]

    pools = []
    nodes_per_pool = (options.num_nodes + num_pools - 1) // len(pool_names)
    to_add = options.num_nodes
    for name in pool_names:
      nodes = nodes_per_pool if (to_add > nodes_per_pool) else to_add
      pool = self.messages.NodePool(
          name=name,
          initialNodeCount=nodes,
          config=node_config,
          version=options.node_version,
          management=self._GetNodeManagement(options))
      if options.enable_autoscaling:
        pool.autoscaling = self.messages.NodePoolAutoscaling(
            enabled=options.enable_autoscaling,
            minNodeCount=options.min_nodes,
            maxNodeCount=options.max_nodes,
            totalMinNodeCount=options.total_min_nodes,
            totalMaxNodeCount=options.total_max_nodes)
        if options.location_policy is not None:
          pool.autoscaling.locationPolicy = LocationPolicyEnumFromString(
              self.messages, options.location_policy)
      if options.max_pods_per_node:
        if not options.enable_ip_alias:
          raise util.Error(MAX_PODS_PER_NODE_WITHOUT_IP_ALIAS_ERROR_MSG)
        pool.maxPodsConstraint = self.messages.MaxPodsConstraint(
            maxPodsPerNode=options.max_pods_per_node)
      if (options.max_surge_upgrade is not None or
          options.max_unavailable_upgrade is not None):
        pool.upgradeSettings = self.messages.UpgradeSettings()
        pool.upgradeSettings.maxSurge = options.max_surge_upgrade
        pool.upgradeSettings.maxUnavailable = options.max_unavailable_upgrade
      if (
          options.placement_type == 'COMPACT'
          or options.placement_policy is not None
      ):
        pool.placementPolicy = self.messages.PlacementPolicy()
      if options.placement_type == 'COMPACT':
        pool.placementPolicy.type = self.messages.PlacementPolicy.TypeValueValuesEnum.COMPACT
      if options.placement_policy is not None:
        pool.placementPolicy.policyName = options.placement_policy
      if options.enable_queued_provisioning is not None:
        pool.queuedProvisioning = self.messages.QueuedProvisioning()
        pool.queuedProvisioning.enabled = options.enable_queued_provisioning
      pools.append(pool)
      to_add -= nodes
    return pools

  def GetIamPolicy(self, cluster_ref):
    return self.client.projects.GetIamPolicy(
        self.messages.ContainerProjectsGetIamPolicyRequest(
            resource=ProjectLocationCluster(cluster_ref.projectId, cluster_ref
                                            .zone, cluster_ref.clusterId)))

  def SetIamPolicy(self, cluster_ref, policy):
    return self.client.projects.SetIamPolicy(
        self.messages.ContainerProjectsSetIamPolicyRequest(
            googleIamV1SetIamPolicyRequest=self.messages
            .GoogleIamV1SetIamPolicyRequest(policy=policy),
            resource=ProjectLocationCluster(cluster_ref.projectId,
                                            cluster_ref.zone,
                                            cluster_ref.clusterId)))


def _GetCloudRunLoadBalancerType(options, messages):
  if options.cloud_run_config is not None:
    input_load_balancer_type = options.cloud_run_config.get(
        'load-balancer-type')
    if input_load_balancer_type is not None:
      if input_load_balancer_type == 'INTERNAL':
        return messages.CloudRunConfig.LoadBalancerTypeValueValuesEnum.LOAD_BALANCER_TYPE_INTERNAL
      return messages.CloudRunConfig.LoadBalancerTypeValueValuesEnum.LOAD_BALANCER_TYPE_EXTERNAL
  return None


def _AddMetadataToNodeConfig(node_config, options):
  if not options.metadata:
    return
  metadata = node_config.MetadataValue()
  props = []
  for key, value in six.iteritems(options.metadata):
    props.append(metadata.AdditionalProperty(key=key, value=value))
  metadata.additionalProperties = props
  node_config.metadata = metadata


def _AddLabelsToNodeConfig(node_config, options):
  node_config.resourceLabels = labels_util.ParseCreateArgs(
      options, node_config.ResourceLabelsValue)


def _AddNodeLabelsToNodeConfig(node_config, options):
  if options.node_labels is None:
    return
  labels = node_config.LabelsValue()
  props = []
  for key, value in six.iteritems(options.node_labels):
    props.append(labels.AdditionalProperty(key=key, value=value))
  labels.additionalProperties = props
  node_config.labels = labels


def _AddLinuxNodeConfigToNodeConfig(node_config, options, messages):
  """Adds LinuxNodeConfig to NodeConfig."""

  # Linux kernel parameters (sysctls).
  if options.linux_sysctls:
    if not node_config.linuxNodeConfig:
      node_config.linuxNodeConfig = messages.LinuxNodeConfig()
    linux_sysctls = node_config.linuxNodeConfig.SysctlsValue()
    props = []
    for key, value in six.iteritems(options.linux_sysctls):
      props.append(linux_sysctls.AdditionalProperty(key=key, value=value))
    linux_sysctls.additionalProperties = props

    node_config.linuxNodeConfig.sysctls = linux_sysctls


def _AddWindowsNodeConfigToNodeConfig(node_config, options, messages):
  """ "Adds WindowsNodeConfig to NodeConfig."""

  if options.windows_os_version is not None:
    if node_config.windowsNodeConfig is None:
      node_config.windowsNodeConfig = messages.WindowsNodeConfig()
    if options.windows_os_version == 'ltsc2022':
      node_config.windowsNodeConfig.osVersion = messages.WindowsNodeConfig.OsVersionValueValuesEnum.OS_VERSION_LTSC2022
    else:
      node_config.windowsNodeConfig.osVersion = messages.WindowsNodeConfig.OsVersionValueValuesEnum.OS_VERSION_LTSC2019


def _AddShieldedInstanceConfigToNodeConfig(node_config, options, messages):
  """Adds ShieldedInstanceConfig to NodeConfig."""
  if (options.shielded_secure_boot is not None or
      options.shielded_integrity_monitoring is not None):

    # Setting any of the ShieldedInstanceConfig options here
    # overrides the defaulting on the server.
    #
    # Require all or none of the ShieldedInstanceConfig fields to be
    # set.
    secure_boot_set = options.shielded_secure_boot is not None
    integrity_monitoring_set = options.shielded_integrity_monitoring is not None
    if secure_boot_set != integrity_monitoring_set:
      raise util.Error(BOTH_SHIELDED_INSTANCE_SETTINGS_ERROR_MSG)

    node_config.shieldedInstanceConfig = messages.ShieldedInstanceConfig()
    if options.shielded_secure_boot is not None:
      node_config.shieldedInstanceConfig.enableSecureBoot = (
          options.shielded_secure_boot)
    if options.shielded_integrity_monitoring is not None:
      node_config.shieldedInstanceConfig.enableIntegrityMonitoring = (
          options.shielded_integrity_monitoring)


def _AddReservationAffinityToNodeConfig(node_config, options, messages):
  """Adds ReservationAffinity to NodeConfig."""
  affinity = options.reservation_affinity
  if options.reservation and affinity != 'specific':
    raise util.Error(
        RESERVATION_AFFINITY_NON_SPECIFIC_WITH_RESERVATION_NAME_ERROR_MSG
        .format(affinity=affinity))

  if not options.reservation and affinity == 'specific':
    raise util.Error(
        RESERVATION_AFFINITY_SPECIFIC_WITHOUT_RESERVATION_NAME_ERROR_MSG)

  if affinity == 'none':
    node_config.reservationAffinity = messages.ReservationAffinity(
        consumeReservationType=messages.ReservationAffinity
        .ConsumeReservationTypeValueValuesEnum.NO_RESERVATION)
  elif affinity == 'any':
    node_config.reservationAffinity = messages.ReservationAffinity(
        consumeReservationType=messages.ReservationAffinity
        .ConsumeReservationTypeValueValuesEnum.ANY_RESERVATION)
  elif affinity == 'specific':
    node_config.reservationAffinity = messages.ReservationAffinity(
        consumeReservationType=messages.ReservationAffinity
        .ConsumeReservationTypeValueValuesEnum.SPECIFIC_RESERVATION,
        key='compute.googleapis.com/reservation-name',
        values=[options.reservation])


def _AddSandboxConfigToNodeConfig(node_config, options, messages):
  """Adds SandboxConfig to NodeConfig."""
  if options.sandbox is not None:
    if 'type' not in options.sandbox:
      raise util.Error(SANDBOX_TYPE_NOT_PROVIDED)
    sandbox_types = {
        'unspecified': messages.SandboxConfig.TypeValueValuesEnum.UNSPECIFIED,
        'gvisor': messages.SandboxConfig.TypeValueValuesEnum.GVISOR,
    }
    if options.sandbox['type'] not in sandbox_types:
      raise util.Error(
          SANDBOX_TYPE_NOT_SUPPORTED.format(type=options.sandbox['type']))
    node_config.sandboxConfig = messages.SandboxConfig(
        type=sandbox_types[options.sandbox['type']])


def _GetStableFleetConfig(options, messages):
  """Get StableFleetConfig from options."""
  if options.maintenance_interval is not None:
    maintenance_interval_types = {
        'UNSPECIFIED':
            messages.StableFleetConfig.MaintenanceIntervalValueValuesEnum
            .MAINTENANCE_INTERVAL_UNSPECIFIED,
        'PERIODIC':
            messages.StableFleetConfig.MaintenanceIntervalValueValuesEnum
            .PERIODIC,
        'AS_NEEDED':
            messages.StableFleetConfig.MaintenanceIntervalValueValuesEnum
            .AS_NEEDED,
    }
    if options.maintenance_interval not in maintenance_interval_types:
      raise util.Error(
          MAINTENANCE_INTERVAL_TYPE_NOT_SUPPORTED.FORMAT(
              type=options.maintenance_interval))
    return messages.StableFleetConfig(
        maintenanceInterval=maintenance_interval_types[
            options.maintenance_interval])


def _AddNotificationConfigToCluster(cluster, options, messages):
  """Adds notification config to Cluster."""
  nc = options.notification_config
  if nc is not None:
    pubsub = messages.PubSub()
    if 'pubsub' in nc:
      pubsub.enabled = nc['pubsub'] == 'ENABLED'
    if 'pubsub-topic' in nc:
      pubsub.topic = nc['pubsub-topic']
    if 'filter' in nc:
      pubsub.filter = _GetFilterFromArg(nc['filter'], messages)

    cluster.notificationConfig = messages.NotificationConfig(pubsub=pubsub)


def _GetFilterFromArg(filter_arg, messages):
  """Gets a Filter message object from a filter phrase."""
  if not filter_arg:
    return None
  flag_event_types_to_enum = {
      'upgradeevent':
          messages.Filter.EventTypeValueListEntryValuesEnum.UPGRADE_EVENT,
      'upgradeavailableevent':
          messages.Filter.EventTypeValueListEntryValuesEnum
          .UPGRADE_AVAILABLE_EVENT,
      'securitybulletinevent':
          messages.Filter.EventTypeValueListEntryValuesEnum
          .SECURITY_BULLETIN_EVENT
  }
  to_return = messages.Filter()
  for event_type in filter_arg.split('|'):
    event_type = event_type.lower()
    if flag_event_types_to_enum[event_type]:
      to_return.eventType.append(flag_event_types_to_enum[event_type])
  return to_return


def _GetReleaseChannel(options, messages):
  """Gets the ReleaseChannel from options."""
  if options.release_channel is not None:
    channels = {
        'rapid': messages.ReleaseChannel.ChannelValueValuesEnum.RAPID,
        'regular': messages.ReleaseChannel.ChannelValueValuesEnum.REGULAR,
        'stable': messages.ReleaseChannel.ChannelValueValuesEnum.STABLE,
        'None': messages.ReleaseChannel.ChannelValueValuesEnum.UNSPECIFIED,
    }
    return messages.ReleaseChannel(channel=channels[options.release_channel])


def _GetNotificationConfigForClusterUpdate(options, messages):
  """Gets the NotificationConfig from update options."""
  nc = options.notification_config
  if nc is not None:
    pubsub = messages.PubSub()
    if 'pubsub' in nc:
      pubsub.enabled = nc['pubsub'] == 'ENABLED'
    if 'pubsub-topic' in nc:
      pubsub.topic = nc['pubsub-topic']
    if 'filter' in nc:
      pubsub.filter = _GetFilterFromArg(nc['filter'], messages)
    return messages.NotificationConfig(pubsub=pubsub)


def _GetTpuConfigForClusterUpdate(options, messages):
  """Gets the TpuConfig from update options."""
  if options.enable_tpu is not None:
    if options.tpu_ipv4_cidr and options.enable_tpu_service_networking:
      raise util.Error(TPU_SERVING_MODE_ERROR)
    return messages.TpuConfig(
        enabled=options.enable_tpu,
        ipv4CidrBlock=options.tpu_ipv4_cidr,
        useServiceNetworking=options.enable_tpu_service_networking,
    )


def _GetMasterForClusterCreate(options, messages):
  """Gets the Master from create options."""
  if options.master_logs is not None or options.enable_master_metrics is not None:
    config = messages.MasterSignalsConfig()

    if options.master_logs is not None:
      if APISERVER in options.master_logs:
        config.logEnabledComponents.append(
            messages.MasterSignalsConfig
            .LogEnabledComponentsValueListEntryValuesEnum.APISERVER)
      if SCHEDULER in options.master_logs:
        config.logEnabledComponents.append(
            messages.MasterSignalsConfig
            .LogEnabledComponentsValueListEntryValuesEnum.SCHEDULER)
      if CONTROLLER_MANAGER in options.master_logs:
        config.logEnabledComponents.append(
            messages.MasterSignalsConfig
            .LogEnabledComponentsValueListEntryValuesEnum.CONTROLLER_MANAGER)
      if ADDON_MANAGER in options.master_logs:
        config.logEnabledComponents.append(
            messages.MasterSignalsConfig
            .LogEnabledComponentsValueListEntryValuesEnum.ADDON_MANAGER)
    if options.enable_master_metrics is not None:
      config.enableMetrics = options.enable_master_metrics
    return messages.Master(signalsConfig=config)


def _GetMasterForClusterUpdate(options, messages):
  """Gets the Master from update options."""
  if options.no_master_logs:
    options.master_logs = []
  if options.master_logs is not None:
    config = messages.MasterSignalsConfig()
    if APISERVER in options.master_logs:
      config.logEnabledComponents.append(
          messages.MasterSignalsConfig
          .LogEnabledComponentsValueListEntryValuesEnum.APISERVER)
    if SCHEDULER in options.master_logs:
      config.logEnabledComponents.append(
          messages.MasterSignalsConfig
          .LogEnabledComponentsValueListEntryValuesEnum.SCHEDULER)
    if CONTROLLER_MANAGER in options.master_logs:
      config.logEnabledComponents.append(
          messages.MasterSignalsConfig
          .LogEnabledComponentsValueListEntryValuesEnum.CONTROLLER_MANAGER)
    if ADDON_MANAGER in options.master_logs:
      config.logEnabledComponents.append(
          messages.MasterSignalsConfig
          .LogEnabledComponentsValueListEntryValuesEnum.ADDON_MANAGER)
    return messages.Master(signalsConfig=config)

  if options.enable_master_metrics is not None:
    config = messages.MasterSignalsConfig(
        enableMetrics=options.enable_master_metrics,
        logEnabledComponents=[
            messages.MasterSignalsConfig
            .LogEnabledComponentsValueListEntryValuesEnum.COMPONENT_UNSPECIFIED
        ])
    return messages.Master(signalsConfig=config)


def _GetLoggingConfig(options, messages):
  """Gets the LoggingConfig from create and update options."""
  if options.logging is None:
    return None

  # TODO(b/195524749): Validate the input in flags.py after Control Plane
  # Signals is GA.
  if any(c not in LOGGING_OPTIONS for c in options.logging):
    raise util.Error('[' + ', '.join(options.logging) +
                     '] contains option(s) that are not supported for logging.')

  config = messages.LoggingComponentConfig()
  if NONE in options.logging:
    if len(options.logging) > 1:
      raise util.Error('Cannot include other values when None is specified.')
    return messages.LoggingConfig(componentConfig=config)
  if SYSTEM not in options.logging:
    raise util.Error('Must include system logging if any logging is enabled.')
  config.enableComponents.append(
      messages.LoggingComponentConfig.EnableComponentsValueListEntryValuesEnum
      .SYSTEM_COMPONENTS)
  if WORKLOAD in options.logging:
    config.enableComponents.append(
        messages.LoggingComponentConfig.EnableComponentsValueListEntryValuesEnum
        .WORKLOADS)
  if API_SERVER in options.logging:
    config.enableComponents.append(
        messages.LoggingComponentConfig.EnableComponentsValueListEntryValuesEnum
        .APISERVER)
  if SCHEDULER in options.logging:
    config.enableComponents.append(
        messages.LoggingComponentConfig.EnableComponentsValueListEntryValuesEnum
        .SCHEDULER)
  if CONTROLLER_MANAGER in options.logging:
    config.enableComponents.append(
        messages.LoggingComponentConfig.EnableComponentsValueListEntryValuesEnum
        .CONTROLLER_MANAGER)
  if ADDON_MANAGER in options.logging:
    config.enableComponents.append(
        messages.LoggingComponentConfig.EnableComponentsValueListEntryValuesEnum
        .ADDON_MANAGER)

  return messages.LoggingConfig(componentConfig=config)


def _GetHostMaintenancePolicy(options, messages):
  """Get HostMaintenancePolicy from options."""
  if options.host_maintenance_interval is not None:
    maintenance_interval_types = {
        'UNSPECIFIED':
            messages.HostMaintenancePolicy.MaintenanceIntervalValueValuesEnum
            .MAINTENANCE_INTERVAL_UNSPECIFIED,
        'PERIODIC':
            messages.HostMaintenancePolicy.MaintenanceIntervalValueValuesEnum
            .PERIODIC,
        'AS_NEEDED':
            messages.HostMaintenancePolicy.MaintenanceIntervalValueValuesEnum
            .AS_NEEDED,
    }
    if options.host_maintenance_interval not in maintenance_interval_types:
      raise util.Error(
          HOST_MAINTENANCE_INTERVAL_TYPE_NOT_SUPPORTED.FORMAT(
              type=options.host_maintenance_interval
          )
      )
    return messages.HostMaintenancePolicy(
        maintenanceInterval=maintenance_interval_types[
            options.host_maintenance_interval
        ]
    )


def _GetMonitoringConfig(options, messages):
  """Gets the MonitoringConfig from create and update options."""

  comp = None
  prom = None
  adv_obs = None
  config = messages.MonitoringConfig()

  if options.enable_managed_prometheus is not None:
    prom = messages.ManagedPrometheusConfig(
        enabled=options.enable_managed_prometheus)
    config.managedPrometheusConfig = prom

  # Disable flag only on cluster updates, check first.
  if hasattr(options, 'disable_managed_prometheus'):
    if options.disable_managed_prometheus is not None:
      prom = messages.ManagedPrometheusConfig(
          enabled=(not options.disable_managed_prometheus))
      config.managedPrometheusConfig = prom

  if options.monitoring is not None:
    # TODO(b/195524749): Validate the input in flags.py after Control Plane
    # Signals is GA.
    if any(c not in MONITORING_OPTIONS for c in options.monitoring):
      raise util.Error(
          '[' + ', '.join(options.monitoring) +
          '] contains option(s) that are not supported for monitoring.')

    comp = messages.MonitoringComponentConfig()
    if NONE in options.monitoring:
      if len(options.monitoring) > 1:
        raise util.Error('Cannot include other values when None is specified.')
      else:
        config.componentConfig = comp
        return config
    if SYSTEM not in options.monitoring:
      raise util.Error(
          'Must include system monitoring if any monitoring is enabled.')
    comp.enableComponents.append(
        messages.MonitoringComponentConfig
        .EnableComponentsValueListEntryValuesEnum.SYSTEM_COMPONENTS)

    if WORKLOAD in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.WORKLOADS)
    if API_SERVER in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.APISERVER)
    if SCHEDULER in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.SCHEDULER)
    if CONTROLLER_MANAGER in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.CONTROLLER_MANAGER)
    if STORAGE in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.STORAGE)
    if HPA_COMPONENT in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.HPA)
    if POD in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.POD)
    if DAEMONSET in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.DAEMONSET)
    if DEPLOYMENT in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.DEPLOYMENT)
    if STATEFULSET in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.STATEFULSET)
    if CADVISOR in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.CADVISOR)
    if KUBELET in options.monitoring:
      comp.enableComponents.append(
          messages.MonitoringComponentConfig
          .EnableComponentsValueListEntryValuesEnum.KUBELET)

    config.componentConfig = comp

  if options.enable_dataplane_v2_metrics:
    adv_obs = messages.AdvancedDatapathObservabilityConfig(
        enableMetrics=True)

  if options.disable_dataplane_v2_metrics:
    adv_obs = messages.AdvancedDatapathObservabilityConfig(
        enableMetrics=False)

  if options.dataplane_v2_observability_mode:
    relay_mode = None
    opts_name = options.dataplane_v2_observability_mode.upper()
    if opts_name == 'DISABLED':
      relay_mode = (messages.AdvancedDatapathObservabilityConfig
                    .RelayModeValueValuesEnum.DISABLED)
    elif opts_name == 'INTERNAL_CLUSTER_SERVICE':
      relay_mode = (messages.AdvancedDatapathObservabilityConfig
                    .RelayModeValueValuesEnum.INTERNAL_CLUSTER_SERVICE)
    elif opts_name == 'INTERNAL_VPC_LB':
      relay_mode = (messages.AdvancedDatapathObservabilityConfig
                    .RelayModeValueValuesEnum.INTERNAL_VPC_LB)
    elif opts_name == 'EXTERNAL_LB':
      relay_mode = (messages.AdvancedDatapathObservabilityConfig
                    .RelayModeValueValuesEnum.EXTERNAL_LB)
    else:
      raise util.Error(DPV2_OBS_ERROR_MSG.format(
          mode=options.dataplane_v2_observability_mode))
    if adv_obs:
      adv_obs = messages.AdvancedDatapathObservabilityConfig(
          enableMetrics=adv_obs.enableMetrics, relayMode=relay_mode)
    else:
      adv_obs = messages.AdvancedDatapathObservabilityConfig(
          relayMode=relay_mode)

  if options.enable_dataplane_v2_flow_observability:
    if adv_obs:
      adv_obs = messages.AdvancedDatapathObservabilityConfig(
          enableMetrics=adv_obs.enableMetrics, enableRelay=True)
    else:
      adv_obs = messages.AdvancedDatapathObservabilityConfig(enableRelay=True)

  if options.disable_dataplane_v2_flow_observability:
    if adv_obs:
      adv_obs = messages.AdvancedDatapathObservabilityConfig(
          enableMetrics=adv_obs.enableMetrics, enableRelay=False)
    else:
      adv_obs = messages.AdvancedDatapathObservabilityConfig(enableRelay=False)

  if comp is None and prom is None and adv_obs is None:
    return None

  if hasattr(config, 'advancedDatapathObservabilityConfig'):
    config.advancedDatapathObservabilityConfig = adv_obs

  return config


def _GetKubernetesObjectsExportConfigForClusterCreate(options, messages):
  """Gets the KubernetesObjectsExportConfig from create options."""
  if options.kubernetes_objects_changes_target is not None or options.kubernetes_objects_snapshots_target is not None:
    config = messages.KubernetesObjectsExportConfig()
    if options.kubernetes_objects_changes_target is not None:
      config.kubernetesObjectsChangesTarget = options.kubernetes_objects_changes_target
    if options.kubernetes_objects_snapshots_target is not None:
      config.kubernetesObjectsSnapshotsTarget = options.kubernetes_objects_snapshots_target
    return config


def _GetKubernetesObjectsExportConfigForClusterUpdate(options, messages):
  """Gets the KubernetesObjectsExportConfig from update options."""
  if options.kubernetes_objects_changes_target is not None or options.kubernetes_objects_snapshots_target is not None:
    changes_target = None
    snapshots_target = None
    if options.kubernetes_objects_changes_target is not None:
      changes_target = options.kubernetes_objects_changes_target
      if changes_target == 'NONE':
        changes_target = ''
    if options.kubernetes_objects_snapshots_target is not None:
      snapshots_target = options.kubernetes_objects_snapshots_target
      if snapshots_target == 'NONE':
        snapshots_target = ''
    return messages.KubernetesObjectsExportConfig(
        kubernetesObjectsSnapshotsTarget=snapshots_target,
        kubernetesObjectsChangesTarget=changes_target)


def _AddPSCPrivateClustersOptionsToClusterForCreateCluster(
    cluster, options, messages):
  """Adds all PSC private cluster options to cluster during create cluster."""
  if options.cross_connect_subnetworks is not None:
    items = []
    for subnetwork in sorted(options.cross_connect_subnetworks):
      items.append(messages.CrossConnectItem(subnetwork=subnetwork))
    cluster.privateClusterConfig.crossConnectConfig = messages.CrossConnectConfig(
        items=items)


def LocationPolicyEnumFromString(messages, location_policy):
  location_policy_enum = messages.NodePoolAutoscaling.LocationPolicyValueValuesEnum.LOCATION_POLICY_UNSPECIFIED
  if location_policy == 'BALANCED':
    location_policy_enum = messages.NodePoolAutoscaling.LocationPolicyValueValuesEnum.BALANCED
  elif location_policy == 'ANY':
    location_policy_enum = messages.NodePoolAutoscaling.LocationPolicyValueValuesEnum.ANY
  return location_policy_enum


def ProjectLocation(project, location):
  return 'projects/' + project + '/locations/' + location


def ProjectLocationCluster(project, location, cluster):
  return ProjectLocation(project, location) + '/clusters/' + cluster


def ProjectLocationClusterNodePool(project, location, cluster, nodepool):
  return (ProjectLocationCluster(project, location, cluster) + '/nodePools/' +
          nodepool)


def ProjectLocationOperation(project, location, operation):
  return ProjectLocation(project, location) + '/operations/' + operation


def NormalizeBinauthzEvaluationMode(evaluation_mode):
  """Converts an evaluation mode to lowercase format.

  e.g. Converts 'PROJECT_SINGLETON_POLICY_ENFORCE' to
  'project-singleton-policy-enforce'

  Args:
    evaluation_mode: An evaluation mode.

  Returns:
    The evaluation mode in lowercase form.
  """
  return evaluation_mode.replace('_', '-').lower()


def GetBinauthzEvaluationModeOptions(messages, release_track):
  """Returns all valid options for --binauthz-evaluation-mode."""
  # Only expose DISABLED AND PROJECT_SINGLETON_POLICY_ENFORCE evaluation modes
  # in the GA track.
  if release_track == base.ReleaseTrack.GA:
    return ['DISABLED', 'PROJECT_SINGLETON_POLICY_ENFORCE']
  options = list(
      messages.BinaryAuthorization.EvaluationModeValueValuesEnum.to_dict()
  )
  options.remove('EVALUATION_MODE_UNSPECIFIED')
  return sorted(options)


def BinauthzEvaluationModeRequiresPolicy(messages, evaluation_mode):
  evaluation_mode_enum = (
      messages.BinaryAuthorization.EvaluationModeValueValuesEnum
  )
  if evaluation_mode in (
      evaluation_mode_enum.EVALUATION_MODE_UNSPECIFIED,
      evaluation_mode_enum.DISABLED,
      evaluation_mode_enum.PROJECT_SINGLETON_POLICY_ENFORCE,
  ):
    return False
  return True


def VariantConfigEnumFromString(messages, variant):
  variant_config_enum = messages.LoggingVariantConfig.VariantValueValuesEnum.VARIANT_UNSPECIFIED
  if variant == 'DEFAULT':
    variant_config_enum = messages.LoggingVariantConfig.VariantValueValuesEnum.DEFAULT
  elif variant == 'MAX_THROUGHPUT':
    variant_config_enum = messages.LoggingVariantConfig.VariantValueValuesEnum.MAX_THROUGHPUT
  return variant_config_enum
