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
"""Command that updates scalar properties of an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import environment_patch_util as patch_util
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """\
        To update the Cloud Composer environment named ``env-1'' to have 8
        Airflow workers, and not have the ``production'' label, run:

          $ {command} env-1 --node-count=8 --remove-labels=production
      """
}

_INVALID_OPTION_FOR_V2_ERROR_MSG = """\
Cannot specify --{opt} with Composer 2.X or greater.
"""

_INVALID_OPTION_FOR_V1_ERROR_MSG = """\
Cannot specify --{opt} with Composer 1.X.
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update properties of a Cloud Composer environment."""

  detailed_help = DETAILED_HELP
  _support_autoscaling = True
  _support_composer3flags = False
  _support_maintenance_window = True
  _support_environment_size = True

  @staticmethod
  def Args(parser, release_track=base.ReleaseTrack.GA):
    resource_args.AddEnvironmentResourceArg(parser, 'to update')
    base.ASYNC_FLAG.AddToParser(parser)

    Update.update_type_group = parser.add_mutually_exclusive_group(
        required=True, help='The update type.')
    flags.AddNodeCountUpdateFlagToGroup(Update.update_type_group)
    flags.AddPypiUpdateFlagsToGroup(Update.update_type_group)
    flags.AddEnvVariableUpdateFlagsToGroup(Update.update_type_group)
    flags.AddAirflowConfigUpdateFlagsToGroup(Update.update_type_group)
    flags.AddLabelsUpdateFlagsToGroup(Update.update_type_group)
    web_server_group = Update.update_type_group.add_mutually_exclusive_group()
    flags.UPDATE_WEB_SERVER_ALLOW_IP.AddToParser(web_server_group)
    flags.WEB_SERVER_ALLOW_ALL.AddToParser(web_server_group)
    flags.WEB_SERVER_DENY_ALL.AddToParser(web_server_group)
    flags.ENABLE_HIGH_RESILIENCE.AddToParser(Update.update_type_group)
    flags.DISABLE_HIGH_RESILIENCE.AddToParser(Update.update_type_group)
    flags.ENABLE_LOGS_IN_CLOUD_LOGGING_ONLY.AddToParser(
        Update.update_type_group
    )
    flags.DISABLE_LOGS_IN_CLOUD_LOGGING_ONLY.AddToParser(
        Update.update_type_group
    )
    flags.CLOUD_SQL_MACHINE_TYPE.AddToParser(Update.update_type_group)
    flags.WEB_SERVER_MACHINE_TYPE.AddToParser(Update.update_type_group)

    flags.AddAutoscalingUpdateFlagsToGroup(Update.update_type_group,
                                           release_track)
    flags.AddMasterAuthorizedNetworksUpdateFlagsToGroup(
        Update.update_type_group)

    flags.AIRFLOW_DATABASE_RETENTION_DAYS.AddToParser(
        Update.update_type_group.add_argument_group(hidden=True)
    )

    flags.AddScheduledSnapshotFlagsToGroup(Update.update_type_group)

    flags.AddMaintenanceWindowFlagsUpdateGroup(Update.update_type_group)
    flags.AddCloudDataLineageIntegrationUpdateFlagsToGroup(
        Update.update_type_group)

  def _ConstructPatch(self, env_ref, args, support_environment_upgrades=False):
    env_obj = environments_api_util.Get(
        env_ref, release_track=self.ReleaseTrack())
    is_composer_v1 = image_versions_command_util.IsImageVersionStringComposerV1(
        env_obj.config.softwareConfig.imageVersion)

    params = dict(
        is_composer_v1=is_composer_v1,
        env_ref=env_ref,
        node_count=args.node_count,
        update_pypi_packages_from_file=args.update_pypi_packages_from_file,
        clear_pypi_packages=args.clear_pypi_packages,
        remove_pypi_packages=args.remove_pypi_packages,
        update_pypi_packages=dict(
            command_util.SplitRequirementSpecifier(r)
            for r in args.update_pypi_package),
        clear_labels=args.clear_labels,
        remove_labels=args.remove_labels,
        update_labels=args.update_labels,
        clear_airflow_configs=args.clear_airflow_configs,
        remove_airflow_configs=args.remove_airflow_configs,
        update_airflow_configs=args.update_airflow_configs,
        clear_env_variables=args.clear_env_variables,
        remove_env_variables=args.remove_env_variables,
        update_env_variables=args.update_env_variables,
        release_track=self.ReleaseTrack(),
    )

    if support_environment_upgrades:
      params['update_image_version'] = self._getImageVersion(
          args, env_ref, env_obj
      )
    params['update_web_server_access_control'] = (
        environments_api_util.BuildWebServerAllowedIps(
            args.update_web_server_allow_ip,
            args.web_server_allow_all,
            args.web_server_deny_all,
        )
    )

    if args.cloud_sql_machine_type and not is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='cloud-sql-machine-type')
      )
    if args.web_server_machine_type and not is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='web-server-machine-type')
      )
    params['cloud_sql_machine_type'] = args.cloud_sql_machine_type
    params['web_server_machine_type'] = args.web_server_machine_type

    if self._support_environment_size:
      if args.environment_size and is_composer_v1:
        raise command_util.InvalidUserInputError(
            _INVALID_OPTION_FOR_V1_ERROR_MSG.format(opt='environment-size')
        )
      if self.ReleaseTrack() == base.ReleaseTrack.GA:
        params['environment_size'] = flags.ENVIRONMENT_SIZE_GA.GetEnumForChoice(
            args.environment_size
        )
      elif self.ReleaseTrack() == base.ReleaseTrack.BETA:
        params['environment_size'] = (
            flags.ENVIRONMENT_SIZE_BETA.GetEnumForChoice(args.environment_size)
        )
      elif self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
        params['environment_size'] = (
            flags.ENVIRONMENT_SIZE_ALPHA.GetEnumForChoice(args.environment_size)
        )
    if self._support_autoscaling:
      if (
          args.scheduler_cpu
          or args.worker_cpu
          or args.web_server_cpu
          or args.scheduler_memory
          or args.worker_memory
          or args.web_server_memory
          or args.scheduler_storage
          or args.worker_storage
          or args.web_server_storage
          or args.min_workers
          or args.max_workers
          or (
              args.enable_triggerer
              or args.disable_triggerer
              or args.triggerer_count is not None
              or args.triggerer_cpu
              or args.triggerer_memory
          )
      ):
        params['workload_updated'] = True
        if is_composer_v1:
          raise command_util.InvalidUserInputError(
              'Workloads Config flags introduced in Composer 2.X'
              ' cannot be used when updating Composer 1.X environments.'
          )
      if env_obj.config.workloadsConfig:
        if env_obj.config.workloadsConfig.scheduler:
          params['scheduler_cpu'] = env_obj.config.workloadsConfig.scheduler.cpu
          params['scheduler_memory_gb'] = (
              env_obj.config.workloadsConfig.scheduler.memoryGb
          )
          params['scheduler_storage_gb'] = (
              env_obj.config.workloadsConfig.scheduler.storageGb
          )
          params['scheduler_count'] = (
              env_obj.config.workloadsConfig.scheduler.count
          )
        if env_obj.config.workloadsConfig.worker:
          params['worker_cpu'] = env_obj.config.workloadsConfig.worker.cpu

          params['worker_memory_gb'] = (
              env_obj.config.workloadsConfig.worker.memoryGb
          )
          params['worker_storage_gb'] = (
              env_obj.config.workloadsConfig.worker.storageGb
          )
          params['min_workers'] = env_obj.config.workloadsConfig.worker.minCount
          params['max_workers'] = env_obj.config.workloadsConfig.worker.maxCount
        if env_obj.config.workloadsConfig.webServer:
          params['web_server_cpu'] = (
              env_obj.config.workloadsConfig.webServer.cpu
          )
          params['web_server_memory_gb'] = (
              env_obj.config.workloadsConfig.webServer.memoryGb
          )
          params['web_server_storage_gb'] = (
              env_obj.config.workloadsConfig.webServer.storageGb
          )
      if args.scheduler_count is not None:
        params['scheduler_count'] = args.scheduler_count
        if not is_composer_v1:
          params['workload_updated'] = True
      if args.scheduler_cpu is not None:
        params['scheduler_cpu'] = args.scheduler_cpu
      if args.worker_cpu is not None:
        params['worker_cpu'] = args.worker_cpu
      if args.web_server_cpu is not None:
        params['web_server_cpu'] = args.web_server_cpu
      if args.scheduler_memory is not None:
        params['scheduler_memory_gb'] = (
            environments_api_util.MemorySizeBytesToGB(args.scheduler_memory)
        )
      if args.worker_memory is not None:
        params['worker_memory_gb'] = environments_api_util.MemorySizeBytesToGB(
            args.worker_memory
        )
      if args.web_server_memory is not None:
        params['web_server_memory_gb'] = (
            environments_api_util.MemorySizeBytesToGB(args.web_server_memory)
        )
      if args.scheduler_storage is not None:
        params['scheduler_storage_gb'] = (
            environments_api_util.MemorySizeBytesToGB(args.scheduler_storage)
        )
      if args.worker_storage is not None:
        params['worker_storage_gb'] = environments_api_util.MemorySizeBytesToGB(
            args.worker_storage
        )
      if args.web_server_storage is not None:
        params['web_server_storage_gb'] = (
            environments_api_util.MemorySizeBytesToGB(args.web_server_storage)
        )
      if args.min_workers:
        params['min_workers'] = args.min_workers
      if args.max_workers:
        params['max_workers'] = args.max_workers

    self._addScheduledSnapshotFields(params, args, is_composer_v1)
    self._addTriggererFields(params, args, env_obj)

    if self._support_maintenance_window:
      params['clear_maintenance_window'] = args.clear_maintenance_window
      params['maintenance_window_start'] = args.maintenance_window_start
      params['maintenance_window_end'] = args.maintenance_window_end
      params[
          'maintenance_window_recurrence'] = args.maintenance_window_recurrence
    params['airflow_database_retention_days'] = (
        args.airflow_database_retention_days
    )
    if args.enable_master_authorized_networks and args.disable_master_authorized_networks:
      raise command_util.InvalidUserInputError(
          'Cannot specify --enable-master-authorized-networks with --disable-master-authorized-networks'
      )
    if args.disable_master_authorized_networks and args.master_authorized_networks:
      raise command_util.InvalidUserInputError(
          'Cannot specify --disable-master-authorized-networks with --master-authorized-networks'
      )
    if args.enable_master_authorized_networks is None and args.master_authorized_networks:
      raise command_util.InvalidUserInputError(
          'Cannot specify --master-authorized-networks without --enable-master-authorized-networks'
      )
    if args.enable_master_authorized_networks or args.disable_master_authorized_networks:
      params[
          'master_authorized_networks_enabled'] = True if args.enable_master_authorized_networks else False
    command_util.ValidateMasterAuthorizedNetworks(
        args.master_authorized_networks)
    params['master_authorized_networks'] = args.master_authorized_networks

    if args.enable_high_resilience or args.disable_high_resilience:
      if is_composer_v1:
        raise command_util.InvalidUserInputError(
            _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
                opt='enable_high_resilience'
                if args.enable_high_resilience
                else 'disable_high_resilience'
            )
        )
      params['enable_high_resilience'] = bool(args.enable_high_resilience)

    if (
        args.enable_logs_in_cloud_logging_only
        or args.disable_logs_in_cloud_logging_only
    ):
      if is_composer_v1:
        raise command_util.InvalidUserInputError(
            _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
                opt='enable_logs_in_cloud_logging_only'
                if args.enable_logs_in_cloud_logging_only
                else 'disable_logs_in_cloud_logging_only'
            )
        )
      params['enable_logs_in_cloud_logging_only'] = bool(
          args.enable_logs_in_cloud_logging_only
      )

    if (
        args.enable_cloud_data_lineage_integration
        or args.disable_cloud_data_lineage_integration
    ):
      if is_composer_v1:
        raise command_util.InvalidUserInputError(
            _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
                opt='enable-cloud-data-lineage-integration'
                if args.enable_cloud_data_lineage_integration
                else 'disable-cloud-data-lineage-integration'
            )
        )
      params['cloud_data_lineage_integration_enabled'] = bool(
          args.enable_cloud_data_lineage_integration
      )

    if self._support_composer3flags:
      self._addComposer3Fields(params, args, env_obj)
    return patch_util.ConstructPatch(**params)

  def _getImageVersion(self, args, env_ref, env_obj):
    if (
        args.airflow_version or args.image_version
    ) and image_versions_command_util.IsDefaultImageVersion(args.image_version):
      message = image_versions_command_util.BuildDefaultComposerVersionWarning(
          args.image_version, args.airflow_version
      )
      log.warning(message)

    if args.airflow_version:
      args.image_version = (
          image_versions_command_util.ImageVersionFromAirflowVersion(
              args.airflow_version, env_obj.config.softwareConfig.imageVersion
          )
      )
    # Checks validity of image_version upgrade request.
    if args.image_version:
      upgrade_validation = (
          image_versions_command_util.IsValidImageVersionUpgrade(
              env_obj.config.softwareConfig.imageVersion, args.image_version
          )
      )
      if not upgrade_validation.upgrade_valid:
        raise command_util.InvalidUserInputError(upgrade_validation.error)
    return args.image_version

  def _addComposer3Fields(self, params, args, env_obj):
    is_composer3 = image_versions_command_util.IsVersionComposer3Compatible(
        env_obj.config.softwareConfig.imageVersion
    )

    possible_args = {
        'support-web-server-plugins': args.support_web_server_plugins,
        'enable-private-builds-only': args.enable_private_builds_only,
        'disable-private-builds-only': args.disable_private_builds_only,
        'dag-processor-cpu': args.dag_processor_cpu,
        'dag-processor-memory': args.dag_processor_memory,
        'dag-processor-count': args.dag_processor_count,
        'dag-processor-storage': args.dag_processor_storage,
        'disable-vpc-connectivity': args.disable_vpc_connectivity,
        'enable-private-environment': args.enable_private_environment,
        'disable-private-environment': args.disable_private_environment,
        'network': args.network,
        'subnetwork': args.subnetwork,
        'clear-maintenance-window': args.clear_maintenance_window,
    }
    for k, v in possible_args.items():
      if v is not None and not is_composer3:
        raise command_util.InvalidUserInputError(
            flags.COMPOSER3_IS_REQUIRED_MSG.format(
                opt=k,
                composer_version=flags.MIN_COMPOSER3_VERSION,
            )
        )

    if (
        args.dag_processor_count is not None
        or args.dag_processor_cpu
        or args.dag_processor_memory
        or args.dag_processor_storage
    ):
      params['workload_updated'] = True

    dag_processor_count = None
    dag_processor_cpu = None
    dag_processor_memory_gb = None
    dag_processor_storage_gb = None

    if (
        env_obj.config.workloadsConfig
        and env_obj.config.workloadsConfig.dagProcessor
    ):
      dag_processor_resource = env_obj.config.workloadsConfig.dagProcessor
      dag_processor_count = dag_processor_resource.count
      dag_processor_cpu = dag_processor_resource.cpu
      dag_processor_memory_gb = dag_processor_resource.memoryGb
      dag_processor_storage_gb = dag_processor_resource.storageGb

    if args.dag_processor_count is not None:
      dag_processor_count = args.dag_processor_count
    if args.dag_processor_cpu:
      dag_processor_cpu = args.dag_processor_cpu
    if args.dag_processor_memory:
      dag_processor_memory_gb = environments_api_util.MemorySizeBytesToGB(
          args.dag_processor_memory
      )
    if args.dag_processor_storage:
      dag_processor_storage_gb = environments_api_util.MemorySizeBytesToGB(
          args.dag_processor_storage
      )

    if args.support_web_server_plugins is not None:
      params['support_web_server_plugins'] = args.support_web_server_plugins
    if args.enable_private_builds_only or args.disable_private_builds_only:
      params['support_private_builds_only'] = (
          True if args.enable_private_builds_only else False
      )
    if args.enable_private_environment is not None:
      params['enable_private_environment'] = args.enable_private_environment
    if args.disable_private_environment is not None:
      params['disable_private_environment'] = args.disable_private_environment
    params['dag_processor_count'] = dag_processor_count
    params['dag_processor_cpu'] = dag_processor_cpu
    params['dag_processor_memory_gb'] = dag_processor_memory_gb
    params['dag_processor_storage_gb'] = dag_processor_storage_gb
    if args.disable_vpc_connectivity:
      params['disable_vpc_connectivity'] = True
    if args.network_attachment:
      params['network_attachment'] = args.network_attachment
    if args.network:
      params['network'] = args.network
    if args.subnetwork:
      params['subnetwork'] = args.subnetwork

  # TODO(b/245909413): Update Composer version
  def _addScheduledSnapshotFields(self, params, args, is_composer_v1):
    if (args.disable_scheduled_snapshot_creation or
        args.enable_scheduled_snapshot_creation) and is_composer_v1:
      raise command_util.InvalidUserInputError(
          'Scheduled Snapshots flags introduced in Composer 2.X'
          ' cannot be used when creating Composer 1 environments.')

    if args.disable_scheduled_snapshot_creation:
      params['enable_scheduled_snapshot_creation'] = False
    if args.enable_scheduled_snapshot_creation:
      params['enable_scheduled_snapshot_creation'] = True
      params['snapshot_location'] = args.snapshot_location
      params['snapshot_schedule_timezone'] = args.snapshot_schedule_timezone
      params['snapshot_creation_schedule'] = args.snapshot_creation_schedule

  def _addTriggererFields(self, params, args, env_obj):
    triggerer_supported = image_versions_command_util.IsVersionTriggererCompatible(
        env_obj.config.softwareConfig.imageVersion)
    triggerer_count = None
    triggerer_cpu = None
    triggerer_memory_gb = None
    if (env_obj.config.workloadsConfig and
        env_obj.config.workloadsConfig.triggerer and
        env_obj.config.workloadsConfig.triggerer.count != 0):
      triggerer_count = env_obj.config.workloadsConfig.triggerer.count
      triggerer_memory_gb = env_obj.config.workloadsConfig.triggerer.memoryGb
      triggerer_cpu = env_obj.config.workloadsConfig.triggerer.cpu
    if args.disable_triggerer or args.enable_triggerer:
      triggerer_count = 1 if args.enable_triggerer else 0
    if args.triggerer_count is not None:
      triggerer_count = args.triggerer_count
    if args.triggerer_cpu:
      triggerer_cpu = args.triggerer_cpu
    if args.triggerer_memory:
      triggerer_memory_gb = environments_api_util.MemorySizeBytesToGB(
          args.triggerer_memory)
    possible_args = {
        'triggerer-count': args.enable_triggerer,
        'triggerer-cpu': args.triggerer_cpu,
        'triggerer-memory': args.triggerer_memory
    }
    for k, v in possible_args.items():
      if v and not triggerer_supported:
        raise command_util.InvalidUserInputError(
            flags.INVALID_OPTION_FOR_MIN_IMAGE_VERSION_ERROR_MSG.format(
                opt=k,
                composer_version=flags.MIN_TRIGGERER_COMPOSER_VERSION,
                airflow_version=flags.MIN_TRIGGERER_AIRFLOW_VERSION))
    if not triggerer_count:
      if args.triggerer_cpu:
        raise command_util.InvalidUserInputError(
            'Cannot specify --triggerer-cpu without enabled triggerer')
      if args.triggerer_memory:
        raise command_util.InvalidUserInputError(
            'Cannot specify --triggerer-memory without enabled triggerer')
    if triggerer_count == 1 and not (triggerer_memory_gb and triggerer_cpu):
      raise command_util.InvalidUserInputError(
          'Cannot enable triggerer without providing triggerer memory and cpu.')
    params['triggerer_count'] = triggerer_count
    if triggerer_count:
      params['triggerer_cpu'] = triggerer_cpu
      params['triggerer_memory_gb'] = triggerer_memory_gb

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    field_mask, patch = self._ConstructPatch(env_ref, args)
    return patch_util.Patch(
        env_ref,
        field_mask,
        patch,
        args.async_,
        release_track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update properties of a Cloud Composer environment."""

  _support_autoscaling = True
  _support_composer3flags = True
  _support_maintenance_window = True
  _support_environment_size = True

  @staticmethod
  def AlphaAndBetaArgs(parser, release_track=base.ReleaseTrack.BETA):
    """Arguments available only in both alpha and beta."""
    Update.Args(parser, release_track=release_track)

    # Environment upgrade arguments
    UpdateBeta.support_environment_upgrades = True
    flags.AddEnvUpgradeFlagsToGroup(Update.update_type_group)
    flags.AddComposer3FlagsToGroup(Update.update_type_group)

  @staticmethod
  def Args(parser):
    """Arguments available only in beta, not in alpha."""
    UpdateBeta.AlphaAndBetaArgs(parser, base.ReleaseTrack.BETA)

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()

    # Checks validity of update_web_server_allow_ip
    if (self.ReleaseTrack() == base.ReleaseTrack.BETA and
        args.update_web_server_allow_ip):
      flags.ValidateIpRanges(
          [acl['ip_range'] for acl in args.update_web_server_allow_ip])

    field_mask, patch = self._ConstructPatch(
        env_ref, args, UpdateBeta.support_environment_upgrades)

    return patch_util.Patch(
        env_ref,
        field_mask,
        patch,
        args.async_,
        release_track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update properties of a Cloud Composer environment."""

  _support_autoscaling = True

  @staticmethod
  def Args(parser):
    UpdateBeta.AlphaAndBetaArgs(parser, base.ReleaseTrack.ALPHA)
