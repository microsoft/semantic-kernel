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
"""Utilities for calling the Composer Environments API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer.flags import CONNECTION_TYPE_FLAG_ALPHA
from googlecloudsdk.command_lib.composer.flags import CONNECTION_TYPE_FLAG_BETA
from googlecloudsdk.command_lib.composer.flags import CONNECTION_TYPE_FLAG_GA
from googlecloudsdk.command_lib.composer.flags import ENVIRONMENT_SIZE_ALPHA
from googlecloudsdk.command_lib.composer.flags import ENVIRONMENT_SIZE_BETA
from googlecloudsdk.command_lib.composer.flags import ENVIRONMENT_SIZE_GA


def GetService(release_track=base.ReleaseTrack.GA):
  return api_util.GetClientInstance(
      release_track).projects_locations_environments


class CreateEnvironmentFlags:
  """Container holding environment creation flag values.

  Attributes:
    node_count: int or None, the number of VMs to create for the environment
    environment_size: str or None, one of small, medium and large.
    labels: dict(str->str), a dict of user-provided resource labels to apply to
      the environment and its downstream resources
    location: str or None, the Compute Engine zone in which to create the
      environment specified as relative resource name.
    machine_type: str or None, the Compute Engine machine type of the VMs to
      create specified as relative resource name.
    network: str or None, the Compute Engine network to which to connect the
      environment specified as relative resource name.
    subnetwork: str or None, the Compute Engine subnetwork to which to connect
      the environment specified as relative resource name.
    network_attachment: str or None, the Compute Engine network attachment that
      is used as PSC Network entry point.
    env_variables: dict(str->str), a dict of user-provided environment variables
      to provide to the Airflow scheduler, worker, and webserver processes.
    airflow_config_overrides: dict(str->str), a dict of user-provided Airflow
      configuration overrides.
    service_account: str or None, the user-provided service account
    oauth_scopes: [str], the user-provided OAuth scopes
    tags: [str], the user-provided networking tags
    disk_size_gb: int, the disk size of node VMs, in GB
    python_version: str or None, major python version to use within created
      environment.
    image_version: str or None, the desired image for created environment in the
      format of 'composer-(version)-airflow-(version)'
    airflow_executor_type: str or None, the airflow executor type to run task
      instances.
    use_ip_aliases: bool or None, create env cluster nodes using alias IPs.
    cluster_secondary_range_name: str or None, the name of secondary range to
      allocate IP addresses to pods in GKE cluster.
    services_secondary_range_name: str or None, the name of the secondary range
      to allocate IP addresses to services in GKE cluster.
    cluster_ipv4_cidr_block: str or None, the IP address range to allocate IP
      adresses to pods in GKE cluster.
    services_ipv4_cidr_block: str or None, the IP address range to allocate IP
      addresses to services in GKE cluster.
    max_pods_per_node: int or None, the maximum number of pods that can be
      assigned to a GKE cluster node.
    enable_ip_masq_agent: bool or None, when enabled, the GKE IP Masq Agent is
      deployed to the cluster.
    private_environment: bool or None, create env cluster nodes with no public
      IP addresses.
    private_endpoint: bool or None, managed env cluster using the private IP
      address of the master API endpoint.
    master_ipv4_cidr: IPv4 CIDR range to use for the cluster master network.
    privately_used_public_ips: bool or None, when enabled, GKE pod and services
      can use IPs from public (non-RFC1918) ranges.
    web_server_ipv4_cidr: IPv4 CIDR range to use for Web Server network.
    cloud_sql_ipv4_cidr: IPv4 CIDR range to use for Cloud SQL network.
    composer_network_ipv4_cidr: IPv4 CIDR range to use for Composer network.
    connection_subnetwork: str or None, the Compute Engine subnetwork from which
      to reserve the IP address for internal connections, specified as relative
      resource name.
    connection_type: str or None, mode of internal connectivity within the Cloud
      Composer environment. Can be VPC_PEERING or PRIVATE_SERVICE_CONNECT.
    web_server_access_control: [{string: string}], List of IP ranges with
      descriptions to allow access to the web server.
    cloud_sql_machine_type: str or None, Cloud SQL machine type used by the
      Airflow database.
    cloud_sql_preferred_zone: str or None, Cloud SQL db preferred zone. Can be
      specified only in Composer 2.0.0.
    web_server_machine_type: str or None, machine type used by the Airflow web
      server
    kms_key: str or None, the user-provided customer-managed encryption key
      resource name
    scheduler_cpu: float or None, CPU allocated to Airflow scheduler. Can be
      specified only in Composer 2.0.0.
    worker_cpu: float or None, CPU allocated to each Airflow worker. Can be
      specified only in Composer 2.0.0.
    web_server_cpu: float or None, CPU allocated to Airflow web server. Can be
      specified only in Composer 2.0.0.
    scheduler_memory_gb: float or None, memory allocated to Airflow scheduler.
      Can be specified only in Composer 2.0.0.
    worker_memory_gb: float or None, memory allocated to each Airflow worker.
      Can be specified only in Composer 2.0.0.
    web_server_memory_gb: float or None, memory allocated to Airflow web server.
      Can be specified only in Composer 2.0.0.
    scheduler_storage_gb: float or None, storage allocated to Airflow scheduler.
      Can be specified only in Composer 2.0.0.
    worker_storage_gb: float or None, storage allocated to each Airflow worker.
      Can be specified only in Composer 2.0.0.
    web_server_storage_gb: float or None, storage allocated to Airflow web
      server. Can be specified only in Composer 2.0.0.
    min_workers: int or None, minimum number of workers in the Environment. Can
      be specified only in Composer 2.0.0.
    max_workers: int or None, maximum number of workers in the Environment. Can
      be specified only in Composer 2.0.0.
    scheduler_count: int or None, number of schedulers in the Environment.
    maintenance_window_start: Datetime or None, the starting time of the
      maintenance window
    maintenance_window_end: Datetime or None, the ending time of the maintenance
      window
    maintenance_window_recurrence: str or None, the recurrence of the
      maintenance window
    enable_master_authorized_networks: bool or None, whether master authorized
      networks should be enabled
    master_authorized_networks: list(str), master authorized networks
    airflow_database_retention_days: Optional[int], the number of retention days
      for airflow database data retention mechanism. Infinite retention will be
      applied in case `0` or no integer is provided.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.
    enable_triggerer: bool or None, enable triggerer in the Environment. Can be
      specified only in Airflow 2.2.x and greater
    triggerer_cpu: float or None, CPU allocated to Airflow triggerer. Can be
      specified only in Airflow 2.2.x and greater
    triggerer_count: int or None, number of Airflow triggerers. Can be specified
      only in Airflow 2.2.x and greater
    triggerer_memory_gb: float or None, memory allocated to Airflow triggerer.
      Can be specified only in Airflow 2.2.x and greater
    enable_scheduled_snapshot_creation: bool or None, whether the automatic
      snapshot creation should be enabled
    snapshot_creation_schedule: str or None, cron expression that specifies when
      snapshots will be created
    snapshot_location: str or None, a Cloud Storage location used to store
      automatically created snapshots
    snapshot_schedule_timezone: str or None, time zone that sets the context to
      interpret snapshot_creation_schedule
    enable_cloud_data_lineage_integration: bool or None, whether Cloud Data
      Lineage integration should be enabled
    disable_cloud_data_lineage_integration: bool or None, whether Cloud Data
      Lineage integration should be disabled
    enable_high_resilience: bool or None, whether high resilience should be
      enabled
    enable_logs_in_cloud_logging_only: bool or None, whether logs in cloud
      logging only should be enabled
    disable_logs_in_cloud_logging_only: bool or None, whether logs in cloud
      logging only should be disabled
    support_web_server_plugins: bool or None, whether to enable/disable the
      support for web server plugins
    dag_processor_cpu: float or None, CPU allocated to Airflow dag processor.
      Can be specified only in Composer 3.
    dag_processor_count: int or None, number of Airflow dag processors. Can be
      specified only in Composer 3.
    dag_processor_memory_gb: float or None, memory allocated to Airflow dag
      processor. Can be specified only in Composer 3.
    dag_processor_storage_gb: float or None, storage allocated to Airflow dag
      processor. Can be specified only in Composer 3.
    composer_internal_ipv4_cidr_block: str or None. The IP range in CIDR
      notation to use internally by Cloud Composer. Can be specified only in
      Composer 3.
    enable_private_builds_only: bool or None, whether to enable the support for
      private only builds.
    disable_private_builds_only: bool or None, whether to disable the support
      for private only builds.
    storage_bucket: str or None. An existing Cloud Storage bucket to be used by
      the environment.
  """

  # TODO(b/154131605): This a type that is an immutable data object. Can't use
  # attrs because it's not part of googlecloudsdk and can't use namedtuple
  # because it's not efficient on python 2 (it generates code, which needs
  # to be parsed and interpretted). Remove this code when we get support
  # for attrs or another dumb data object in gcloud.
  def __init__(
      self,
      node_count=None,
      environment_size=None,
      labels=None,
      location=None,
      machine_type=None,
      network=None,
      subnetwork=None,
      network_attachment=None,
      env_variables=None,
      airflow_config_overrides=None,
      service_account=None,
      oauth_scopes=None,
      tags=None,
      disk_size_gb=None,
      python_version=None,
      image_version=None,
      airflow_executor_type=None,
      use_ip_aliases=None,
      cluster_secondary_range_name=None,
      services_secondary_range_name=None,
      cluster_ipv4_cidr_block=None,
      services_ipv4_cidr_block=None,
      max_pods_per_node=None,
      enable_ip_masq_agent=None,
      private_environment=None,
      private_endpoint=None,
      master_ipv4_cidr=None,
      privately_used_public_ips=None,
      web_server_ipv4_cidr=None,
      cloud_sql_ipv4_cidr=None,
      composer_network_ipv4_cidr=None,
      connection_subnetwork=None,
      connection_type=None,
      web_server_access_control=None,
      cloud_sql_machine_type=None,
      web_server_machine_type=None,
      kms_key=None,
      scheduler_cpu=None,
      worker_cpu=None,
      web_server_cpu=None,
      scheduler_memory_gb=None,
      worker_memory_gb=None,
      web_server_memory_gb=None,
      scheduler_storage_gb=None,
      worker_storage_gb=None,
      web_server_storage_gb=None,
      min_workers=None,
      max_workers=None,
      scheduler_count=None,
      maintenance_window_start=None,
      maintenance_window_end=None,
      maintenance_window_recurrence=None,
      enable_master_authorized_networks=None,
      master_authorized_networks=None,
      airflow_database_retention_days=None,
      release_track=base.ReleaseTrack.GA,
      enable_triggerer=None,
      triggerer_cpu=None,
      triggerer_count=None,
      triggerer_memory_gb=None,
      enable_scheduled_snapshot_creation=None,
      snapshot_creation_schedule=None,
      snapshot_location=None,
      snapshot_schedule_timezone=None,
      enable_cloud_data_lineage_integration=None,
      disable_cloud_data_lineage_integration=None,
      enable_high_resilience=None,
      enable_logs_in_cloud_logging_only=None,
      disable_logs_in_cloud_logging_only=None,
      cloud_sql_preferred_zone=None,
      support_web_server_plugins=None,
      dag_processor_cpu=None,
      dag_processor_count=None,
      dag_processor_memory_gb=None,
      dag_processor_storage_gb=None,
      composer_internal_ipv4_cidr_block=None,
      enable_private_builds_only=None,
      disable_private_builds_only=None,
      storage_bucket=None,
  ):
    self.node_count = node_count
    self.environment_size = environment_size
    self.labels = labels
    self.location = location
    self.machine_type = machine_type
    self.network = network
    self.subnetwork = subnetwork
    self.network_attachment = network_attachment
    self.env_variables = env_variables
    self.airflow_config_overrides = airflow_config_overrides
    self.service_account = service_account
    self.oauth_scopes = oauth_scopes
    self.tags = tags
    self.disk_size_gb = disk_size_gb
    self.python_version = python_version
    self.image_version = image_version
    self.airflow_executor_type = airflow_executor_type
    self.use_ip_aliases = use_ip_aliases
    self.cluster_secondary_range_name = cluster_secondary_range_name
    self.services_secondary_range_name = services_secondary_range_name
    self.cluster_ipv4_cidr_block = cluster_ipv4_cidr_block
    self.services_ipv4_cidr_block = services_ipv4_cidr_block
    self.max_pods_per_node = max_pods_per_node
    self.enable_ip_masq_agent = enable_ip_masq_agent
    self.private_environment = private_environment
    self.private_endpoint = private_endpoint
    self.master_ipv4_cidr = master_ipv4_cidr
    self.privately_used_public_ips = privately_used_public_ips
    self.web_server_ipv4_cidr = web_server_ipv4_cidr
    self.cloud_sql_ipv4_cidr = cloud_sql_ipv4_cidr
    self.composer_network_ipv4_cidr = composer_network_ipv4_cidr
    self.connection_subnetwork = connection_subnetwork
    self.connection_type = connection_type
    self.web_server_access_control = web_server_access_control
    self.cloud_sql_machine_type = cloud_sql_machine_type
    self.web_server_machine_type = web_server_machine_type
    self.kms_key = kms_key
    self.scheduler_cpu = scheduler_cpu
    self.worker_cpu = worker_cpu
    self.web_server_cpu = web_server_cpu
    self.scheduler_memory_gb = scheduler_memory_gb
    self.worker_memory_gb = worker_memory_gb
    self.web_server_memory_gb = web_server_memory_gb
    self.scheduler_storage_gb = scheduler_storage_gb
    self.worker_storage_gb = worker_storage_gb
    self.web_server_storage_gb = web_server_storage_gb
    self.min_workers = min_workers
    self.max_workers = max_workers
    self.scheduler_count = scheduler_count
    self.enable_triggerer = enable_triggerer
    self.triggerer_cpu = triggerer_cpu
    self.triggerer_count = triggerer_count
    self.triggerer_memory_gb = triggerer_memory_gb
    self.maintenance_window_start = maintenance_window_start
    self.maintenance_window_end = maintenance_window_end
    self.maintenance_window_recurrence = maintenance_window_recurrence
    self.enable_master_authorized_networks = enable_master_authorized_networks
    self.master_authorized_networks = master_authorized_networks
    self.airflow_database_retention_days = airflow_database_retention_days
    self.release_track = release_track
    self.enable_scheduled_snapshot_creation = enable_scheduled_snapshot_creation
    self.snapshot_creation_schedule = snapshot_creation_schedule
    self.snapshot_location = snapshot_location
    self.snapshot_schedule_timezone = snapshot_schedule_timezone
    self.enable_cloud_data_lineage_integration = (
        enable_cloud_data_lineage_integration
    )
    self.disable_cloud_data_lineage_integration = (
        disable_cloud_data_lineage_integration
    )
    self.enable_high_resilience = enable_high_resilience
    self.enable_logs_in_cloud_logging_only = enable_logs_in_cloud_logging_only
    self.disable_logs_in_cloud_logging_only = disable_logs_in_cloud_logging_only
    self.cloud_sql_preferred_zone = cloud_sql_preferred_zone
    self.support_web_server_plugins = support_web_server_plugins
    self.dag_processor_cpu = dag_processor_cpu
    self.dag_processor_storage_gb = dag_processor_storage_gb
    self.dag_processor_memory_gb = dag_processor_memory_gb
    self.dag_processor_count = dag_processor_count
    self.composer_internal_ipv4_cidr_block = composer_internal_ipv4_cidr_block
    self.enable_private_builds_only = enable_private_builds_only
    self.disable_private_builds_only = disable_private_builds_only
    self.storage_bucket = storage_bucket


def _CreateNodeConfig(messages, flags):
  """Creates node config from parameters, returns None if config is empty."""
  if not (flags.location or flags.machine_type or flags.network or
          flags.subnetwork or flags.service_account or flags.oauth_scopes or
          flags.tags or flags.disk_size_gb or flags.use_ip_aliases or
          flags.cluster_secondary_range_name or flags.network_attachment or
          flags.services_secondary_range_name or flags.cluster_ipv4_cidr_block
          or flags.services_ipv4_cidr_block or flags.enable_ip_masq_agent or
          flags.composer_internal_ipv4_cidr_block):
    return None

  config = messages.NodeConfig(
      location=flags.location,
      machineType=flags.machine_type,
      network=flags.network,
      subnetwork=flags.subnetwork,
      serviceAccount=flags.service_account,
      diskSizeGb=flags.disk_size_gb)
  if flags.network_attachment:
    config.composerNetworkAttachment = flags.network_attachment
  if flags.composer_internal_ipv4_cidr_block:
    config.composerInternalIpv4CidrBlock = (
        flags.composer_internal_ipv4_cidr_block
    )
  if flags.oauth_scopes:
    config.oauthScopes = sorted([s.strip() for s in flags.oauth_scopes])
  if flags.tags:
    config.tags = sorted([t.strip() for t in flags.tags])
  if (flags.use_ip_aliases or flags.cluster_secondary_range_name or
      flags.services_secondary_range_name or flags.cluster_ipv4_cidr_block or
      flags.services_ipv4_cidr_block):
    config.ipAllocationPolicy = messages.IPAllocationPolicy(
        useIpAliases=flags.use_ip_aliases,
        clusterSecondaryRangeName=flags.cluster_secondary_range_name,
        servicesSecondaryRangeName=flags.services_secondary_range_name,
        clusterIpv4CidrBlock=flags.cluster_ipv4_cidr_block,
        servicesIpv4CidrBlock=flags.services_ipv4_cidr_block,
    )

    if flags.max_pods_per_node:
      config.maxPodsPerNode = flags.max_pods_per_node

  if flags.enable_ip_masq_agent:
    config.enableIpMasqAgent = flags.enable_ip_masq_agent
  return config


def _CreateConfig(messages, flags, is_composer_v1):
  """Creates environment config from parameters, returns None if config is empty."""
  node_config = _CreateNodeConfig(messages, flags)
  if not (node_config or flags.node_count or flags.kms_key or
          flags.image_version or flags.env_variables or
          flags.airflow_config_overrides or flags.python_version or
          flags.airflow_executor_type or flags.maintenance_window_start or
          flags.maintenance_window_end or flags.maintenance_window_recurrence or
          flags.private_environment or flags.web_server_access_control or
          flags.cloud_sql_machine_type or flags.web_server_machine_type or
          flags.scheduler_cpu or flags.worker_cpu or flags.web_server_cpu or
          flags.scheduler_memory_gb or flags.worker_memory_gb or
          flags.web_server_memory_gb or flags.scheduler_storage_gb or
          flags.worker_storage_gb or flags.web_server_storage_gb or
          flags.environment_size or flags.min_workers or flags.max_workers or
          flags.scheduler_count or flags.airflow_database_retention_days or
          flags.triggerer_cpu or flags.triggerer_memory or
          flags.enable_triggerer or flags.enable_scheduled_snapshot_creation or
          flags.snapshot_creation_schedule or flags.snapshot_location or
          flags.snapshot_schedule_timezone or
          flags.enable_cloud_data_lineage_integration or
          flags.disable_cloud_data_lineage_integration):
    return None

  config = messages.EnvironmentConfig()
  if flags.node_count:
    config.nodeCount = flags.node_count
  if node_config:
    config.nodeConfig = node_config
  if flags.kms_key:
    config.encryptionConfig = messages.EncryptionConfig(
        kmsKeyName=flags.kms_key)
  if flags.environment_size:
    if flags.release_track == base.ReleaseTrack.GA:
      config.environmentSize = ENVIRONMENT_SIZE_GA.GetEnumForChoice(
          flags.environment_size)
    elif flags.release_track == base.ReleaseTrack.BETA:
      config.environmentSize = ENVIRONMENT_SIZE_BETA.GetEnumForChoice(
          flags.environment_size)
    elif flags.release_track == base.ReleaseTrack.ALPHA:
      config.environmentSize = ENVIRONMENT_SIZE_ALPHA.GetEnumForChoice(
          flags.environment_size)
  if (
      flags.image_version
      or flags.env_variables
      or flags.airflow_config_overrides
      or flags.python_version
      or flags.airflow_executor_type
      or (flags.scheduler_count and is_composer_v1)
      or flags.enable_cloud_data_lineage_integration
      or flags.disable_cloud_data_lineage_integration
  ):
    config.softwareConfig = messages.SoftwareConfig()
    if flags.image_version:
      config.softwareConfig.imageVersion = flags.image_version
    if flags.env_variables:
      config.softwareConfig.envVariables = api_util.DictToMessage(
          flags.env_variables, messages.SoftwareConfig.EnvVariablesValue)
    if flags.airflow_config_overrides:
      config.softwareConfig.airflowConfigOverrides = api_util.DictToMessage(
          flags.airflow_config_overrides,
          messages.SoftwareConfig.AirflowConfigOverridesValue)
    if flags.python_version:
      config.softwareConfig.pythonVersion = flags.python_version
    if flags.airflow_executor_type:
      config.softwareConfig.airflowExecutorType = ConvertToTypeEnum(
          messages.SoftwareConfig.AirflowExecutorTypeValueValuesEnum,
          flags.airflow_executor_type,
      )
    if flags.support_web_server_plugins is not None:
      if flags.support_web_server_plugins:
        config.softwareConfig.webServerPluginsMode = (
            messages.SoftwareConfig.WebServerPluginsModeValueValuesEnum.PLUGINS_ENABLED
        )
      else:
        config.softwareConfig.webServerPluginsMode = (
            messages.SoftwareConfig.WebServerPluginsModeValueValuesEnum.PLUGINS_DISABLED
        )

    if flags.scheduler_count and is_composer_v1:
      config.softwareConfig.schedulerCount = flags.scheduler_count
    if (
        flags.enable_cloud_data_lineage_integration
        or flags.disable_cloud_data_lineage_integration
    ):
      config.softwareConfig.cloudDataLineageIntegration = (
          messages.CloudDataLineageIntegration(
              enabled=(
                  True if flags.enable_cloud_data_lineage_integration else False
              ),
          )
      )

  if flags.maintenance_window_start:
    assert flags.maintenance_window_end, 'maintenance_window_end is missing'
    assert flags.maintenance_window_recurrence, (
        'maintenance_window_recurrence is missing')
    config.maintenanceWindow = messages.MaintenanceWindow(
        startTime=flags.maintenance_window_start.isoformat(),
        endTime=flags.maintenance_window_end.isoformat(),
        recurrence=flags.maintenance_window_recurrence)
  if flags.airflow_database_retention_days:
    retention_mode = (
        messages.AirflowMetadataRetentionPolicyConfig.RetentionModeValueValuesEnum.RETENTION_MODE_ENABLED
    )
    if flags.airflow_database_retention_days == 0:
      retention_mode = (
          messages.AirflowMetadataRetentionPolicyConfig.RetentionModeValueValuesEnum.RETENTION_MODE_DISABLED
      )
    config.dataRetentionConfig = messages.DataRetentionConfig(
        airflowMetadataRetentionConfig=messages.AirflowMetadataRetentionPolicyConfig(
            retentionDays=flags.airflow_database_retention_days,
            retentionMode=retention_mode,
        )
    )

  if flags.enable_scheduled_snapshot_creation:
    config.recoveryConfig = messages.RecoveryConfig(
        scheduledSnapshotsConfig=messages.ScheduledSnapshotsConfig(
            enabled=flags.enable_scheduled_snapshot_creation,
            snapshotCreationSchedule=flags.snapshot_creation_schedule,
            snapshotLocation=flags.snapshot_location,
            timeZone=flags.snapshot_schedule_timezone))

  if (
      flags.private_environment
      or flags.enable_private_builds_only
      or flags.disable_private_builds_only
  ):
    # Adds a PrivateClusterConfig, if necessary.
    private_cluster_config = None
    networking_config = None
    if flags.private_endpoint or flags.master_ipv4_cidr:
      private_cluster_config = messages.PrivateClusterConfig(
          enablePrivateEndpoint=flags.private_endpoint,
          masterIpv4CidrBlock=flags.master_ipv4_cidr)
    if flags.connection_type:
      if flags.release_track == base.ReleaseTrack.GA:
        connection_type = CONNECTION_TYPE_FLAG_GA.GetEnumForChoice(
            flags.connection_type)
      elif flags.release_track == base.ReleaseTrack.BETA:
        connection_type = CONNECTION_TYPE_FLAG_BETA.GetEnumForChoice(
            flags.connection_type)
      elif flags.release_track == base.ReleaseTrack.ALPHA:
        connection_type = CONNECTION_TYPE_FLAG_ALPHA.GetEnumForChoice(
            flags.connection_type)
      networking_config = messages.NetworkingConfig(
          connectionType=connection_type)

    private_env_config_args = {
        'enablePrivateEnvironment': flags.private_environment,
        'privateClusterConfig': private_cluster_config,
        'networkingConfig': networking_config,
    }

    if flags.web_server_ipv4_cidr is not None:
      private_env_config_args[
          'webServerIpv4CidrBlock'] = flags.web_server_ipv4_cidr
    if flags.cloud_sql_ipv4_cidr is not None:
      private_env_config_args[
          'cloudSqlIpv4CidrBlock'] = flags.cloud_sql_ipv4_cidr
    if flags.composer_network_ipv4_cidr is not None:
      private_env_config_args[
          'cloudComposerNetworkIpv4CidrBlock'] = flags.composer_network_ipv4_cidr
    if flags.privately_used_public_ips is not None:
      private_env_config_args[
          'enablePrivatelyUsedPublicIps'] = flags.privately_used_public_ips
    if flags.connection_subnetwork is not None:
      private_env_config_args[
          'cloudComposerConnectionSubnetwork'] = flags.connection_subnetwork
    if flags.enable_private_builds_only or flags.disable_private_builds_only:
      private_env_config_args['enablePrivateBuildsOnly'] = (
          True if flags.enable_private_builds_only else False
      )
    config.privateEnvironmentConfig = messages.PrivateEnvironmentConfig(
        **private_env_config_args)

  # Builds webServerNetworkAccessControl, if necessary.
  if flags.web_server_access_control is not None:
    config.webServerNetworkAccessControl = BuildWebServerNetworkAccessControl(
        flags.web_server_access_control, flags.release_track)

  if flags.enable_high_resilience:
    config.resilienceMode = (
        messages.EnvironmentConfig.ResilienceModeValueValuesEnum.HIGH_RESILIENCE
    )
  if flags.enable_logs_in_cloud_logging_only:
    task_logs_retention_config = messages.TaskLogsRetentionConfig(
        storageMode=messages.TaskLogsRetentionConfig.StorageModeValueValuesEnum.CLOUD_LOGGING_ONLY
    )
    config.dataRetentionConfig = messages.DataRetentionConfig(
        taskLogsRetentionConfig=task_logs_retention_config
    )
  if flags.disable_logs_in_cloud_logging_only:
    task_logs_retention_config = messages.TaskLogsRetentionConfig(
        storageMode=messages.TaskLogsRetentionConfig.StorageModeValueValuesEnum.CLOUD_LOGGING_AND_CLOUD_STORAGE
    )
    config.dataRetentionConfig = messages.DataRetentionConfig(
        taskLogsRetentionConfig=task_logs_retention_config
    )
  if flags.cloud_sql_machine_type:
    config.databaseConfig = messages.DatabaseConfig(
        machineType=flags.cloud_sql_machine_type)
  if flags.cloud_sql_preferred_zone:
    config.databaseConfig = messages.DatabaseConfig(
        zone=flags.cloud_sql_preferred_zone
    )
  if flags.web_server_machine_type:
    config.webServerConfig = messages.WebServerConfig(
        machineType=flags.web_server_machine_type)

  if flags.enable_master_authorized_networks:
    networks = flags.master_authorized_networks if flags.master_authorized_networks else []
    config.masterAuthorizedNetworksConfig = messages.MasterAuthorizedNetworksConfig(
        enabled=True,
        cidrBlocks=[
            messages.CidrBlock(cidrBlock=network) for network in networks
        ])

  composer_v2_flags = [
      flags.scheduler_cpu,
      flags.worker_cpu,
      flags.web_server_cpu,
      flags.scheduler_memory_gb,
      flags.worker_memory_gb,
      flags.web_server_memory_gb,
      flags.scheduler_storage_gb,
      flags.worker_storage_gb,
      flags.web_server_storage_gb,
      flags.min_workers,
      flags.max_workers,
      flags.triggerer_memory_gb,
      flags.triggerer_cpu,
      flags.enable_triggerer,
      flags.triggerer_count,
      flags.dag_processor_cpu,
      flags.dag_processor_count,
      flags.dag_processor_memory_gb,
      flags.dag_processor_storage_gb,
  ]
  composer_v2_flag_used = any(flag is not None for flag in composer_v2_flags)
  if composer_v2_flag_used or (flags.scheduler_count and not is_composer_v1):
    config.workloadsConfig = _CreateWorkloadConfig(messages, flags)
  return config


def _CreateWorkloadConfig(messages, flags):
  """Creates workload config from parameters."""
  workload_resources = dict(
      scheduler=messages.SchedulerResource(
          cpu=flags.scheduler_cpu,
          memoryGb=flags.scheduler_memory_gb,
          storageGb=flags.scheduler_storage_gb,
          count=flags.scheduler_count),
      webServer=messages.WebServerResource(
          cpu=flags.web_server_cpu,
          memoryGb=flags.web_server_memory_gb,
          storageGb=flags.web_server_storage_gb),
      worker=messages.WorkerResource(
          cpu=flags.worker_cpu,
          memoryGb=flags.worker_memory_gb,
          storageGb=flags.worker_storage_gb,
          minCount=flags.min_workers,
          maxCount=flags.max_workers))
  if (
      flags.enable_triggerer
      or flags.triggerer_cpu
      or flags.triggerer_memory_gb
      or flags.triggerer_count is not None
  ):
    triggerer_count = 1 if flags.enable_triggerer else 0
    if flags.triggerer_count is not None:
      triggerer_count = flags.triggerer_count
    workload_resources['triggerer'] = messages.TriggererResource(
        cpu=flags.triggerer_cpu,
        memoryGb=flags.triggerer_memory_gb,
        count=triggerer_count
    )
  if (
      flags.dag_processor_cpu
      or flags.dag_processor_count is not None
      or flags.dag_processor_memory_gb
      or flags.dag_processor_storage_gb
  ):
    workload_resources['dagProcessor'] = messages.DagProcessorResource(
        cpu=flags.dag_processor_cpu,
        memoryGb=flags.dag_processor_memory_gb,
        storageGb=flags.dag_processor_storage_gb,
        count=flags.dag_processor_count,
    )

  return messages.WorkloadsConfig(**workload_resources)


def Create(environment_ref, flags, is_composer_v1):
  """Calls the Composer Environments.Create method.

  Args:
    environment_ref: Resource, the Composer environment resource to create.
    flags: CreateEnvironmentFlags, the flags provided for environment creation.
    is_composer_v1: boolean representing if creation request is for Composer
      1.*.* image versions.

  Returns:
    Operation: the operation corresponding to the creation of the environment
  """
  messages = api_util.GetMessagesModule(release_track=flags.release_track)
  # Builds environment message and attaches the configuration
  environment = messages.Environment(name=environment_ref.RelativeName())
  environment.config = _CreateConfig(messages, flags, is_composer_v1)

  if flags.labels:
    environment.labels = api_util.DictToMessage(
        flags.labels, messages.Environment.LabelsValue)

  if flags.storage_bucket:
    environment.storageConfig = messages.StorageConfig(
        bucket=flags.storage_bucket
    )

  try:
    return GetService(release_track=flags.release_track).Create(
        api_util.GetMessagesModule(release_track=flags.release_track)
        .ComposerProjectsLocationsEnvironmentsCreateRequest(
            environment=environment,
            parent=environment_ref.Parent().RelativeName()))
  except apitools_exceptions.HttpForbiddenError as e:
    raise exceptions.HttpException(
        e,
        error_format=(
            'Creation operation failed because of lack of proper '
            'permissions. Please, refer to '
            'https://cloud.google.com/composer/docs/how-to/managing/creating '
            'and Composer Creation Troubleshooting pages to resolve this issue.'
        ))


def ConvertToTypeEnum(type_enum, airflow_executor_type):
  """Converts airflow executor type string to enum.

  Args:
    type_enum: AirflowExecutorTypeValueValuesEnum, executor type enum value.
    airflow_executor_type: string, executor type string value.

  Returns:
    AirflowExecutorTypeValueValuesEnum: the executor type enum value.
  """
  return type_enum(airflow_executor_type)


def Delete(environment_ref, release_track=base.ReleaseTrack.GA):
  """Calls the Composer Environments.Delete method.

  Args:
    environment_ref: Resource, the Composer environment resource to delete.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    Operation: the operation corresponding to the deletion of the environment
  """
  return GetService(release_track=release_track).Delete(
      api_util.GetMessagesModule(release_track=release_track)
      .ComposerProjectsLocationsEnvironmentsDeleteRequest(
          name=environment_ref.RelativeName()))


def RestartWebServer(environment_ref, release_track=base.ReleaseTrack.BETA):
  """Calls the Composer Environments.RestartWebServer method.

  Args:
    environment_ref: Resource, the Composer environment resource to restart the
      web server for.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    Operation: the operation corresponding to the restart of the web server
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsRestartWebServerRequest(
      name=environment_ref.RelativeName())
  return GetService(
      release_track=release_track).RestartWebServer(request_message)


def SaveSnapshot(environment_ref,
                 snapshot_location,
                 release_track=base.ReleaseTrack.ALPHA):
  """Calls the Composer Environments.SaveSnapshot method.

  Args:
    environment_ref: Resource, the Composer environment resource to save the
      snapshot for.
    snapshot_location: location to save the snapshot of the environment.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    Operation: the operation corresponding to saving the snapshot.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsSaveSnapshotRequest(
      environment=environment_ref.RelativeName(),
      saveSnapshotRequest=message_module.SaveSnapshotRequest(
          snapshotLocation=snapshot_location))
  return GetService(release_track=release_track).SaveSnapshot(request_message)


def LoadSnapshot(environment_ref,
                 skip_pypi_packages_installation,
                 skip_environment_variables_setting,
                 skip_airflow_overrides_setting,
                 skip_gcs_data_copying,
                 snapshot_path,
                 release_track=base.ReleaseTrack.ALPHA):
  """Calls the Composer Environments.LoadSnapshot method.

  Args:
    environment_ref: Resource, the Composer environment resource to Load the
      snapshot for.
    skip_pypi_packages_installation: skip installing the pypi packages during
      the operation.
    skip_environment_variables_setting: skip setting environment variables
      during the operation.
    skip_airflow_overrides_setting: skip setting Airflow overrides during the
      operation.
    skip_gcs_data_copying: skip copying GCS data during the operation.
    snapshot_path: path of the specific snapshot to load the snapshot.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    Operation: the operation corresponding to loading the snapshot.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsLoadSnapshotRequest(
      environment=environment_ref.RelativeName(),
      loadSnapshotRequest=message_module.LoadSnapshotRequest(
          skipPypiPackagesInstallation=skip_pypi_packages_installation,
          skipEnvironmentVariablesSetting=skip_environment_variables_setting,
          skipAirflowOverridesSetting=skip_airflow_overrides_setting,
          skipGcsDataCopying=skip_gcs_data_copying,
          snapshotPath=snapshot_path))
  return GetService(release_track=release_track).LoadSnapshot(request_message)


def ExecuteAirflowCommand(
    command,
    subcommand,
    parameters,
    environment_ref,
    release_track=base.ReleaseTrack.ALPHA,
):
  """Starts execution of an Airflow CLI command through Composer API.

  Args:
    command: string, the command to execute.
    subcommand: string, the subcommand to execute.
    parameters: string[], optional, additinal parameters for the command.
    environment_ref: Resource, the Composer environment to execute the command.
    release_track: base.ReleaseTrack, the release track of command. Determines
      which Composer client library is used.

  Returns:
    ExecuteAirflowCommandResponse: information about the execution.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsExecuteAirflowCommandRequest(
      environment=environment_ref.RelativeName(),
      executeAirflowCommandRequest=message_module.ExecuteAirflowCommandRequest(
          command=command,
          subcommand=subcommand,
          parameters=parameters,
      ),
  )
  return GetService(release_track=release_track).ExecuteAirflowCommand(
      request_message
  )


def StopAirflowCommand(
    execution_id,
    pod_name,
    pod_namespace,
    force,
    environment_ref,
    release_track=base.ReleaseTrack.ALPHA,
):
  """Stops the execution of an Airflow CLI command.

  Args:
    execution_id: string, the unique ID of execution.
    pod_name: string, the pod the execution is running on.
    pod_namespace: string, the pod's namespace.
    force: boolean, If true, the execution is terminated forcefully (SIGKILL).
      If false, the  execution is stopped gracefully, giving it time for
      cleanup.
    environment_ref: Resource, the Composer environment to stop the command.
    release_track: base.ReleaseTrack, the release track of command. Determines
      which Composer client library is used.

  Returns:
    StopAirflowCommandResponse: information whether stopping the execution was
    successful.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsStopAirflowCommandRequest(
      environment=environment_ref.RelativeName(),
      stopAirflowCommandRequest=message_module.StopAirflowCommandRequest(
          executionId=execution_id,
          pod=pod_name,
          podNamespace=pod_namespace,
          force=force,
      ),
  )
  return GetService(release_track=release_track).StopAirflowCommand(
      request_message
  )


def PollAirflowCommand(
    execution_id,
    pod_name,
    pod_namespace,
    next_line_number,
    environment_ref,
    release_track=base.ReleaseTrack.ALPHA,
):
  """Polls the execution of an Airflow CLI command through Composer API.

  Args:
    execution_id: string, the unique ID of execution.
    pod_name: string, the pod the execution is running on.
    pod_namespace: string, the pod's namespace.
    next_line_number: int, line of the output which should be fetched.
    environment_ref: Resource, the Composer environment to poll the command.
    release_track: base.ReleaseTrack, the release track of command. Determines
      which Composer client library is used.

  Returns:
    PollAirflowCommandResponse: the next output lines from the execution and
    information whether the execution is still running.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsPollAirflowCommandRequest(
      environment=environment_ref.RelativeName(),
      pollAirflowCommandRequest=message_module.PollAirflowCommandRequest(
          executionId=execution_id,
          pod=pod_name,
          podNamespace=pod_namespace,
          nextLineNumber=next_line_number,
      ),
  )
  return GetService(release_track=release_track).PollAirflowCommand(
      request_message
  )


def DatabaseFailover(environment_ref, release_track=base.ReleaseTrack.ALPHA):
  """Triggers the database failover (only for highly resilient environments).

  Args:
    environment_ref: Resource, the Composer environment resource to trigger the
      database failover for.
    release_track: base.ReleaseTrack, the release track of command. Determines
      which Composer client library is used.

  Returns:
    Operation: the operation corresponding to triggering a database failover.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsDatabaseFailoverRequest(
      environment=environment_ref.RelativeName(),
      databaseFailoverRequest=message_module.DatabaseFailoverRequest())
  return GetService(release_track=release_track).DatabaseFailover(
      request_message
  )


def FetchDatabaseProperties(environment_ref,
                            release_track=base.ReleaseTrack.ALPHA):
  """Fetch database properties.

  Args:
    environment_ref: Resource, the Composer environment resource to fetch the
      database properties for.
    release_track: base.ReleaseTrack, the release track of command. Determines
      which Composer client library is used.

  Returns:
    DatabaseProperties: database properties for a given environment.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsFetchDatabasePropertiesRequest(
      environment=environment_ref.RelativeName())
  return GetService(release_track=release_track).FetchDatabaseProperties(
      request_message
  )


def CheckUpgrade(environment_ref,
                 image_version,
                 release_track=base.ReleaseTrack.BETA):
  """Calls the Composer Environments.CheckUpgrade method.

  Args:
    environment_ref: Resource, the Composer environment resource to check
      upgrade for.
    image_version: Image version to upgrade to.
    release_track: base.ReleaseTrack, the release track of command. Determines
      which Composer client library is used.

  Returns:
    Operation: the operation corresponding to the upgrade check
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  request_message = message_module.ComposerProjectsLocationsEnvironmentsCheckUpgradeRequest(
      environment=environment_ref.RelativeName(),
      checkUpgradeRequest=message_module.CheckUpgradeRequest(
          imageVersion=image_version))
  return GetService(release_track=release_track).CheckUpgrade(request_message)


def Get(environment_ref, release_track=base.ReleaseTrack.GA):
  """Calls the Composer Environments.Get method.

  Args:
    environment_ref: Resource, the Composer environment resource to retrieve.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    Environment: the requested environment
  """
  return GetService(release_track=release_track).Get(
      api_util.GetMessagesModule(release_track=release_track)
      .ComposerProjectsLocationsEnvironmentsGetRequest(
          name=environment_ref.RelativeName()))


def List(location_refs,
         page_size,
         limit=None,
         release_track=base.ReleaseTrack.GA):
  """Lists Composer Environments across all locations.

  Uses a hardcoded list of locations, as there is no way to dynamically
  discover the list of supported locations. Support for new locations
  will be aligned with Cloud SDK releases.

  Args:
    location_refs: [core.resources.Resource], a list of resource reference to
      locations in which to list environments.
    page_size: An integer specifying the maximum number of resources to be
      returned in a single list call.
    limit: An integer specifying the maximum number of environments to list.
      None if all available environments should be returned.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    list: a generator over Environments in the locations in `location_refs`
  """
  return api_util.AggregateListResults(
      api_util.GetMessagesModule(release_track=release_track)
      .ComposerProjectsLocationsEnvironmentsListRequest,
      GetService(release_track=release_track),
      location_refs,
      'environments',
      page_size,
      limit=limit)


def Patch(environment_ref,
          environment_patch,
          update_mask,
          release_track=base.ReleaseTrack.GA):
  """Calls the Composer Environments.Update method.

  Args:
    environment_ref: Resource, the Composer environment resource to update.
    environment_patch: The Environment message specifying the patch associated
      with the update_mask.
    update_mask: A field mask defining the patch.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    Operation: the operation corresponding to the environment update
  """
  try:
    return GetService(release_track=release_track).Patch(
        api_util.GetMessagesModule(release_track=release_track)
        .ComposerProjectsLocationsEnvironmentsPatchRequest(
            name=environment_ref.RelativeName(),
            environment=environment_patch,
            updateMask=update_mask))
  except apitools_exceptions.HttpForbiddenError as e:
    raise exceptions.HttpException(
        e,
        error_format=(
            'Update operation failed because of lack of proper '
            'permissions. Please, refer to '
            'https://cloud.google.com/composer/docs/how-to/managing/updating '
            'and Composer Update Troubleshooting pages to resolve this issue.'))


def BuildWebServerNetworkAccessControl(web_server_access_control,
                                       release_track):
  """Builds a WebServerNetworkAccessControl proto given an IP range list.

  If the list is empty, the returned policy is set to ALLOW by default.
  Otherwise, the default policy is DENY with a list of ALLOW rules for each
  of the IP ranges.

  Args:
    web_server_access_control: [{string: string}], list of IP ranges with
      descriptions.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    WebServerNetworkAccessControl: proto to be sent to the API.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  return messages.WebServerNetworkAccessControl(allowedIpRanges=[
      messages.AllowedIpRange(
          value=ip_range['ip_range'], description=ip_range.get('description'))
      for ip_range in web_server_access_control
  ])


def BuildWebServerAllowedIps(allowed_ip_list, allow_all, deny_all):
  """Returns the list of IP ranges that will be sent to the API.

  The resulting IP range list is determined by the options specified in
  environment create or update flags.

  Args:
    allowed_ip_list: [{string: string}], list of IP ranges with descriptions.
    allow_all: bool, True if allow all flag was set.
    deny_all: bool, True if deny all flag was set.

  Returns:
    [{string: string}]: list of IP ranges that will be sent to the API, taking
        into account the values of allow all and deny all flags.
  """
  if deny_all:
    return []
  if allow_all:
    return [{
        'ip_range': '0.0.0.0/0',
        'description': 'Allows access from all IPv4 addresses (default value)',
    }, {
        'ip_range': '::0/0',
        'description': 'Allows access from all IPv6 addresses (default value)',
    }]
  return allowed_ip_list


def DiskSizeBytesToGB(disk_size):
  """Returns a disk size value in GB.

  Args:
    disk_size: int, size in bytes, or None for default value

  Returns:
    int, size in GB
  """
  return disk_size >> 30 if disk_size else disk_size


def MemorySizeBytesToGB(memory_size):
  """Returns a memory size value in GB.

  Args:
    memory_size: int, size in bytes, or None for default value

  Returns:
    float, size in GB rounded to 3 decimal places
  """
  if not memory_size:
    return memory_size
  return round(memory_size / float(1 << 30), 3)
