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
"""Common utility functions for Composer environment patch commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log
import six


def _ConstructAirflowDatabaseRetentionDaysPatch(airflow_database_retention_days,
                                                release_track):
  """Constructs an environment patch for Airflow Database Retention feature.

  Args:
    airflow_database_retention_days: int or None, the number of retention days
      for airflow database data retention mechanism
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig()
  retention_mode = (
      messages.AirflowMetadataRetentionPolicyConfig.RetentionModeValueValuesEnum.RETENTION_MODE_ENABLED
  )
  if airflow_database_retention_days == 0:
    retention_mode = (
        messages.AirflowMetadataRetentionPolicyConfig.RetentionModeValueValuesEnum.RETENTION_MODE_DISABLED
    )
  config.dataRetentionConfig = messages.DataRetentionConfig(
      airflowMetadataRetentionConfig=messages.AirflowMetadataRetentionPolicyConfig(
          retentionDays=airflow_database_retention_days,
          retentionMode=retention_mode,
      )
  )
  return (
      'config.data_retention_configuration.airflow_metadata_retention_config',
      messages.Environment(config=config),
  )


def Patch(env_resource,
          field_mask,
          patch,
          is_async,
          release_track=base.ReleaseTrack.GA):
  """Patches an Environment, optionally waiting for the operation to complete.

  This function is intended to perform the common work of an Environment
  patching command's Run method. That is, calling the patch API method and
  waiting for the result or immediately returning the Operation.

  Args:
    env_resource: googlecloudsdk.core.resources.Resource, Resource representing
      the Environment to be patched
    field_mask: str, a field mask string containing comma-separated paths to be
      patched
    patch: Environment, a patch Environment containing updated values to apply
    is_async: bool, whether or not to perform the patch asynchronously
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    an Operation corresponding to the Patch call if `is_async` is True;
    otherwise None is returned after the operation is complete

  Raises:
    command_util.Error: if `is_async` is False and the operation encounters
    an error
  """
  operation = environments_api_util.Patch(
      env_resource, patch, field_mask, release_track=release_track)
  details = 'with operation [{0}]'.format(operation.name)
  if is_async:
    log.UpdatedResource(
        env_resource.RelativeName(),
        kind='environment',
        is_async=True,
        details=details)
    return operation

  try:
    operations_api_util.WaitForOperation(
        operation,
        'Waiting for [{}] to be updated with [{}]'.format(
            env_resource.RelativeName(), operation.name),
        release_track=release_track)
  except command_util.Error as e:
    raise command_util.Error('Error updating [{}]: {}'.format(
        env_resource.RelativeName(), six.text_type(e)))


def ConstructPatch(
    is_composer_v1,
    env_ref=None,
    node_count=None,
    update_pypi_packages_from_file=None,
    clear_pypi_packages=None,
    remove_pypi_packages=None,
    update_pypi_packages=None,
    clear_labels=None,
    remove_labels=None,
    update_labels=None,
    clear_airflow_configs=None,
    remove_airflow_configs=None,
    update_airflow_configs=None,
    clear_env_variables=None,
    remove_env_variables=None,
    update_env_variables=None,
    update_image_version=None,
    update_web_server_access_control=None,
    cloud_sql_machine_type=None,
    web_server_machine_type=None,
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
    clear_maintenance_window=None,
    maintenance_window_start=None,
    maintenance_window_end=None,
    maintenance_window_recurrence=None,
    environment_size=None,
    master_authorized_networks_enabled=None,
    master_authorized_networks=None,
    airflow_database_retention_days=None,
    release_track=base.ReleaseTrack.GA,
    triggerer_cpu=None,
    triggerer_memory_gb=None,
    triggerer_count=None,
    enable_scheduled_snapshot_creation=None,
    snapshot_location=None,
    snapshot_schedule_timezone=None,
    snapshot_creation_schedule=None,
    cloud_data_lineage_integration_enabled=None,
    support_web_server_plugins=None,
    support_private_builds_only=None,
    dag_processor_cpu=None,
    dag_processor_count=None,
    dag_processor_memory_gb=None,
    dag_processor_storage_gb=None,
    disable_vpc_connectivity=None,
    network=None,
    subnetwork=None,
    network_attachment=None,
    workload_updated=None,
    enable_private_environment=None,
    disable_private_environment=None,
    enable_high_resilience=None,
    enable_logs_in_cloud_logging_only=None,
):
  """Constructs an environment patch.

  Args:
    is_composer_v1: boolean representing if patch request is for Composer 1.*.*
      Environment.
    env_ref: resource argument, Environment resource argument for environment
      being updated.
    node_count: int, the desired node count
    update_pypi_packages_from_file: str, path to local requirements file
      containing desired pypi dependencies.
    clear_pypi_packages: bool, whether to uninstall all PyPI packages.
    remove_pypi_packages: iterable(string), Iterable of PyPI packages to
      uninstall.
    update_pypi_packages: {string: string}, dict mapping PyPI package name to
      extras and version specifier.
    clear_labels: bool, whether to clear the labels dictionary.
    remove_labels: iterable(string), Iterable of label names to remove.
    update_labels: {string: string}, dict of label names and values to set.
    clear_airflow_configs: bool, whether to clear the Airflow configs
      dictionary.
    remove_airflow_configs: iterable(string), Iterable of Airflow config
      property names to remove.
    update_airflow_configs: {string: string}, dict of Airflow config property
      names and values to set.
    clear_env_variables: bool, whether to clear the environment variables
      dictionary.
    remove_env_variables: iterable(string), Iterable of environment variables to
      remove.
    update_env_variables: {string: string}, dict of environment variable names
      and values to set.
    update_image_version: string, image version to use for environment upgrade
    update_web_server_access_control: [{string: string}], Webserver access
      control to set
    cloud_sql_machine_type: str or None, Cloud SQL machine type used by the
      Airflow database.
    web_server_machine_type: str or None, machine type used by the Airflow web
      server
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
    max_workers: int or None, maximumn number of workers in the Environment. Can
      be specified only in Composer 2.0.0.
    scheduler_count: int or None, number of schedulers in the Environment. Can
      be specified only in Composer 2.0.0.
    clear_maintenance_window: bool or None, specifies if maintenance window
      options should be cleared.
    maintenance_window_start: Datetime or None, a starting date of the
      maintenance window.
    maintenance_window_end: Datetime or None, an ending date of the maintenance
      window.
    maintenance_window_recurrence: str or None, recurrence RRULE for the
      maintenance window.
    environment_size: str or None, one of small, medium and large.
    master_authorized_networks_enabled: bool or None, whether the feature should
      be enabled
    master_authorized_networks: iterable(string) or None, iterable of master
      authorized networks.
    airflow_database_retention_days: Optional[int], the number of retention days
      for airflow database data retention mechanism. Infinite retention will be
      applied in case `0` or no integer is provided.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.
    triggerer_cpu: float or None, CPU allocated to Airflow triggerer. Can be
      specified only in Airflow 2.2.x and greater.
    triggerer_memory_gb: float or None, memory allocated to Airflow triggerer.
      Can be specified only in Airflow 2.2.x and greater.
    triggerer_count: int or None, number of triggerers in the Environment. Can
      be specified only in Airflow 2.2.x and greater
    enable_scheduled_snapshot_creation: bool, whether the automatic snapshot
      creation should be enabled
    snapshot_location: str, a Cloud Storage location used to store automatically
      created snapshots
    snapshot_schedule_timezone: str, time zone that sets the context to
      interpret snapshot_creation_schedule.
    snapshot_creation_schedule: str, cron expression that specifies when
      snapshots will be created
    cloud_data_lineage_integration_enabled: bool or None, whether the feature
      should be enabled
    support_web_server_plugins: bool or None, whether to enable/disable the
      support for web server plugins
    support_private_builds_only: bool or None, whether to enable/disable the
      support for private only builds
    dag_processor_cpu: float or None, CPU allocated to Airflow dag processor.
      Can be specified only in Composer 3.
    dag_processor_count: int or None, number of Airflow dag processors. Can be
      specified only in Composer 3.
    dag_processor_memory_gb: float or None, memory allocated to Airflow dag
      processor. Can be specified only in Composer 3.
    dag_processor_storage_gb: float or None, storage allocated to Airflow dag
      processor. Can be specified only in Composer 3.
    disable_vpc_connectivity: bool or None, defines whether to disable
      connectivity with a user's VPC network. Can be specified only in Composer
      3.
    network: str or None, the Compute Engine network to which to connect the
      environment specified as relative resource name. Can be specified only in
      Composer 3.
    subnetwork: str or None, the Compute Engine subnetwork to which to connect
      the environment specified as relative resource name. Can be specified only
      in Composer 3.
    network_attachment: str or None, the Compute Engine network attachment that
      is used as PSC Network entry point.
    workload_updated: bool or None, verify if workload config has been updated
    enable_private_environment: bool or None, defines whether the internet
      access is disabled from Composer components. Can be specified only in
      Composer 3.
    disable_private_environment: bool or None, defines whether the internet
      access is enabled from Composer components. Can be specified only in
      Composer 3.
    enable_high_resilience: bool or None, defines whether high resilience should
      be enabled for given environment. Can be specified only in Composer 2.
    enable_logs_in_cloud_logging_only: bool or None, defines whether logs in
      cloud logging only feature should be enabled for given environment. Can be
      specified only in composer 2.

  Returns:
    (str, Environment), the field mask and environment to use for update.

  Raises:
    command_util.Error: if no update type is specified
  """
  if node_count:
    return _ConstructNodeCountPatch(node_count, release_track=release_track)
  if environment_size:
    return _ConstructEnvironmentSizePatch(
        environment_size, release_track=release_track)
  if update_pypi_packages_from_file:
    return _ConstructPyPiPackagesPatch(
        True, [],
        command_util.ParseRequirementsFile(update_pypi_packages_from_file),
        release_track=release_track)
  if clear_pypi_packages or remove_pypi_packages or update_pypi_packages:
    return _ConstructPyPiPackagesPatch(
        clear_pypi_packages,
        remove_pypi_packages,
        update_pypi_packages,
        release_track=release_track)
  if enable_private_environment or disable_private_environment:
    return _ConstructPrivateEnvironmentPatch(
        enable_private_environment,
        release_track=release_track)
  if clear_labels or remove_labels or update_labels:
    return _ConstructLabelsPatch(
        clear_labels, remove_labels, update_labels, release_track=release_track)
  if (clear_airflow_configs or remove_airflow_configs or
      update_airflow_configs):
    return _ConstructAirflowConfigsPatch(
        clear_airflow_configs,
        remove_airflow_configs,
        update_airflow_configs,
        release_track=release_track)
  if clear_env_variables or remove_env_variables or update_env_variables:
    return _ConstructEnvVariablesPatch(
        env_ref,
        clear_env_variables,
        remove_env_variables,
        update_env_variables,
        release_track=release_track)
  if update_image_version:
    return _ConstructImageVersionPatch(
        update_image_version, release_track=release_track)
  if update_web_server_access_control is not None:
    return _ConstructWebServerAccessControlPatch(
        update_web_server_access_control, release_track=release_track)
  if cloud_sql_machine_type:
    return _ConstructCloudSqlMachineTypePatch(
        cloud_sql_machine_type, release_track=release_track)
  if web_server_machine_type:
    return _ConstructWebServerMachineTypePatch(
        web_server_machine_type, release_track=release_track)
  if master_authorized_networks_enabled is not None:
    return _ConstructMasterAuthorizedNetworksTypePatch(
        master_authorized_networks_enabled, master_authorized_networks,
        release_track)
  if enable_scheduled_snapshot_creation is not None:
    return _ConstructScheduledSnapshotPatch(enable_scheduled_snapshot_creation,
                                            snapshot_creation_schedule,
                                            snapshot_location,
                                            snapshot_schedule_timezone,
                                            release_track)

  if support_private_builds_only is not None:
    return _ConstructPrivateBuildsOnlyPatch(
        support_private_builds_only, release_track
    )

  if support_web_server_plugins is not None:
    return _ConstructWebServerPluginsModePatch(
        support_web_server_plugins, release_track
    )
  if (
      disable_vpc_connectivity is not None
      or network
      or subnetwork
      or network_attachment
  ):
    return _ConstructVpcConnectivityPatch(
        disable_vpc_connectivity,
        network,
        subnetwork,
        network_attachment,
        release_track,
    )
  if airflow_database_retention_days is not None:
    return _ConstructAirflowDatabaseRetentionDaysPatch(
        airflow_database_retention_days, release_track)
  if is_composer_v1 and scheduler_count:
    return _ConstructSoftwareConfigurationSchedulerCountPatch(
        scheduler_count=scheduler_count, release_track=release_track)
  if workload_updated:
    if is_composer_v1:
      raise command_util.Error(
          'You cannot use Workloads Config flags introduced in Composer 2.X'
          ' when updating Composer 1.X environments.')
    else:
      return _ConstructAutoscalingPatch(
          scheduler_cpu=scheduler_cpu,
          worker_cpu=worker_cpu,
          web_server_cpu=web_server_cpu,
          scheduler_memory_gb=scheduler_memory_gb,
          worker_memory_gb=worker_memory_gb,
          web_server_memory_gb=web_server_memory_gb,
          scheduler_storage_gb=scheduler_storage_gb,
          worker_storage_gb=worker_storage_gb,
          web_server_storage_gb=web_server_storage_gb,
          worker_min_count=min_workers,
          worker_max_count=max_workers,
          scheduler_count=scheduler_count,
          release_track=release_track,
          triggerer_cpu=triggerer_cpu,
          triggerer_memory_gb=triggerer_memory_gb,
          triggerer_count=triggerer_count,
          dag_processor_cpu=dag_processor_cpu,
          dag_processor_memory_gb=dag_processor_memory_gb,
          dag_processor_count=dag_processor_count,
          dag_processor_storage_gb=dag_processor_storage_gb,
      )
  if (
      maintenance_window_start
      and maintenance_window_end
      and maintenance_window_recurrence
      or clear_maintenance_window
  ):
    return _ConstructMaintenanceWindowPatch(
        maintenance_window_start,
        maintenance_window_end,
        maintenance_window_recurrence,
        clear_maintenance_window,
        release_track=release_track,
    )
  if cloud_data_lineage_integration_enabled is not None:
    return _ConstructSoftwareConfigurationCloudDataLineageIntegrationPatch(
        cloud_data_lineage_integration_enabled, release_track
    )
  if enable_high_resilience is not None:
    return _ConstructHighResiliencePatch(
        enable_high_resilience, release_track
    )
  if enable_logs_in_cloud_logging_only is not None:
    return _ConstructLogsInCloudLoggingOnlyPatch(
        enable_logs_in_cloud_logging_only, release_track
    )
  raise command_util.Error(
      'Cannot update Environment with no update type specified.'
  )


def _ConstructPrivateEnvironmentPatch(
    enable_private_environment,
    release_track=base.ReleaseTrack.GA,
):
  """Constructs an environment patch for private environment.

  Args:
    enable_private_environment: bool or None, defines whether the internet
      access is disabled from Composer components. Can be specified only in
      Composer 3.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  private_environment_config = messages.PrivateEnvironmentConfig()
  config = messages.EnvironmentConfig(
      privateEnvironmentConfig=private_environment_config
  )
  update_mask = 'config.private_environment_config.enable_private_environment'
  private_environment_config.enablePrivateEnvironment = bool(
      enable_private_environment
  )

  return (
      update_mask,
      messages.Environment(config=config),
  )


def _ConstructPrivateBuildsOnlyPatch(
    support_private_builds_only,
    release_track=base.ReleaseTrack.GA,
):
  """Constructs an environment patch to enable/disable private builds only.

  Args:
    support_private_builds_only: bool or None, defines whether the internet
      access is disabled during builds. Can be specified only in
      Composer 3.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  private_environment_config = messages.PrivateEnvironmentConfig()
  config = messages.EnvironmentConfig(
      privateEnvironmentConfig=private_environment_config
  )
  update_mask = 'config.private_environment_config.enable_private_builds_only'
  private_environment_config.enablePrivateBuildsOnly = bool(
      support_private_builds_only
  )

  return (
      update_mask,
      messages.Environment(config=config),
  )


def _ConstructVpcConnectivityPatch(
    disable_vpc_connectivity,
    network,
    subnetwork,
    network_attachment,
    release_track=base.ReleaseTrack.GA,
):
  """Constructs an environment patch for vpc connectivity.

  Used only in Composer 3.

  Args:
    disable_vpc_connectivity: bool or None, defines whether to disable
      connectivity with a user's VPC network.
    network: str or None, the Compute Engine network to which to connect the
      environment specified as relative resource name.
    subnetwork: str or None, the Compute Engine subnetwork to which to connect
      the environment specified as relative resource name.
    network_attachment: str or None, the Compute Engine network attachment that
      is used as PSC Network entry point.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  node_config = messages.NodeConfig()
  config = messages.EnvironmentConfig(nodeConfig=node_config)
  update_mask = None
  if disable_vpc_connectivity:
    update_mask = 'config.node_config.network,config.node_config.subnetwork'
  elif network_attachment:
    update_mask = 'config.node_config.network_attachment'
    node_config.composerNetworkAttachment = network_attachment
  elif network and subnetwork:
    update_mask = 'config.node_config.network,config.node_config.subnetwork'
    node_config.network = network
    node_config.subnetwork = subnetwork
  return (
      update_mask,
      messages.Environment(config=config),
  )


def _ConstructNodeCountPatch(node_count, release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for node count.

  Args:
    node_count: int, the desired node count
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig(nodeCount=node_count)
  return 'config.node_count', messages.Environment(config=config)


def _ConstructEnvironmentSizePatch(environment_size,
                                   release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for environment size.

  Args:
    environment_size: str, the desired environment size.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig(environmentSize=environment_size)
  return 'config.environment_size', messages.Environment(config=config)


def _ConstructPyPiPackagesPatch(clear_pypi_packages,
                                remove_pypi_packages,
                                update_pypi_packages,
                                release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for partially updating PyPI packages.

  Args:
    clear_pypi_packages: bool, whether to clear the PyPI packages dictionary.
    remove_pypi_packages: iterable(string), Iterable of PyPI package names to
      remove.
    update_pypi_packages: {string: string}, dict mapping PyPI package name to
      optional extras and version specifier.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  env_cls = messages.Environment
  pypi_packages_cls = (messages.SoftwareConfig.PypiPackagesValue)
  entry_cls = pypi_packages_cls.AdditionalProperty

  def _BuildEnv(entries):
    software_config = messages.SoftwareConfig(
        pypiPackages=pypi_packages_cls(additionalProperties=entries))
    config = messages.EnvironmentConfig(softwareConfig=software_config)
    return env_cls(config=config)

  return command_util.BuildPartialUpdate(
      clear_pypi_packages, remove_pypi_packages, update_pypi_packages,
      'config.software_config.pypi_packages', entry_cls, _BuildEnv)


def _ConstructLabelsPatch(clear_labels,
                          remove_labels,
                          update_labels,
                          release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for updating labels.

  Args:
    clear_labels: bool, whether to clear the labels dictionary.
    remove_labels: iterable(string), Iterable of label names to remove.
    update_labels: {string: string}, dict of label names and values to set.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  env_cls = messages.Environment
  entry_cls = env_cls.LabelsValue.AdditionalProperty

  def _BuildEnv(entries):
    return env_cls(labels=env_cls.LabelsValue(additionalProperties=entries))

  return command_util.BuildPartialUpdate(clear_labels, remove_labels,
                                         update_labels, 'labels', entry_cls,
                                         _BuildEnv)


def _ConstructAirflowConfigsPatch(clear_airflow_configs,
                                  remove_airflow_configs,
                                  update_airflow_configs,
                                  release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for updating Airflow configs.

  Args:
    clear_airflow_configs: bool, whether to clear the Airflow configs
      dictionary.
    remove_airflow_configs: iterable(string), Iterable of Airflow config
      property names to remove.
    update_airflow_configs: {string: string}, dict of Airflow config property
      names and values to set.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  env_cls = messages.Environment
  airflow_config_overrides_cls = (
      messages.SoftwareConfig.AirflowConfigOverridesValue)
  entry_cls = airflow_config_overrides_cls.AdditionalProperty

  def _BuildEnv(entries):
    software_config = messages.SoftwareConfig(
        airflowConfigOverrides=airflow_config_overrides_cls(
            additionalProperties=entries))
    config = messages.EnvironmentConfig(softwareConfig=software_config)
    return env_cls(config=config)

  return command_util.BuildPartialUpdate(
      clear_airflow_configs, remove_airflow_configs, update_airflow_configs,
      'config.software_config.airflow_config_overrides', entry_cls, _BuildEnv)


def _ConstructEnvVariablesPatch(env_ref,
                                clear_env_variables,
                                remove_env_variables,
                                update_env_variables,
                                release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for updating environment variables.

  Note that environment variable updates do not support partial update masks
  unlike other map updates due to comments in (b/78298321). For this reason, we
  need to retrieve the Environment, apply an update on EnvVariable dictionary,
  and patch the entire dictionary. The potential race condition here
  (environment variables being updated between when we retrieve them and when we
  send patch request)is not a concern since environment variable updates take
  5 mins to complete, and environments cannot be updated while already in the
  updating state.

  Args:
    env_ref: resource argument, Environment resource argument for environment
      being updated.
    clear_env_variables: bool, whether to clear the environment variables
      dictionary.
    remove_env_variables: iterable(string), Iterable of environment variable
      names to remove.
    update_env_variables: {string: string}, dict of environment variable names
      and values to set.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  env_obj = environments_api_util.Get(env_ref, release_track=release_track)
  initial_env_var_value = env_obj.config.softwareConfig.envVariables
  initial_env_var_list = (
      initial_env_var_value.additionalProperties
      if initial_env_var_value else [])

  messages = api_util.GetMessagesModule(release_track=release_track)
  env_cls = messages.Environment
  env_variables_cls = messages.SoftwareConfig.EnvVariablesValue
  entry_cls = env_variables_cls.AdditionalProperty

  def _BuildEnv(entries):
    software_config = messages.SoftwareConfig(
        envVariables=env_variables_cls(additionalProperties=entries))
    config = messages.EnvironmentConfig(softwareConfig=software_config)
    return env_cls(config=config)

  return ('config.software_config.env_variables',
          command_util.BuildFullMapUpdate(clear_env_variables,
                                          remove_env_variables,
                                          update_env_variables,
                                          initial_env_var_list, entry_cls,
                                          _BuildEnv))


def _ConstructScheduledSnapshotPatch(enable_scheduled_snapshot_creation,
                                     snapshot_creation_schedule,
                                     snapshot_location,
                                     snapshot_schedule_timezone,
                                     release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for environment image version.

  Args:
    enable_scheduled_snapshot_creation: bool, whether the automatic snapshot
      creation should be enabled
    snapshot_creation_schedule: str, cron expression that specifies when
      snapshots will be created
    snapshot_location: str, a Cloud Storage location used to store automatically
      created snapshots
    snapshot_schedule_timezone: str, time zone that sets the context to
      interpret snapshot_creation_schedule.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig(
      recoveryConfig=messages.RecoveryConfig(
          scheduledSnapshotsConfig=messages.ScheduledSnapshotsConfig(
              enabled=enable_scheduled_snapshot_creation,
              snapshotCreationSchedule=snapshot_creation_schedule,
              snapshotLocation=snapshot_location,
              timeZone=snapshot_schedule_timezone)))

  return 'config.recovery_config.scheduled_snapshots_config', messages.Environment(
      config=config)


def _ConstructWebServerPluginsModePatch(
    support_web_server_plugins, release_track=base.ReleaseTrack.GA
):
  """Constructs an environment patch for web server plugins mode patch.

  Args:
    support_web_server_plugins: bool, defines if plugins are enabled or not.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  software_config = messages.SoftwareConfig()

  if support_web_server_plugins:
    software_config.webServerPluginsMode = (
        messages.SoftwareConfig.WebServerPluginsModeValueValuesEnum.PLUGINS_ENABLED
    )
  else:
    software_config.webServerPluginsMode = (
        messages.SoftwareConfig.WebServerPluginsModeValueValuesEnum.PLUGINS_DISABLED
    )

  config = messages.EnvironmentConfig(softwareConfig=software_config)

  return 'config.software_config.web_server_plugins_mode', messages.Environment(
      config=config)


def _ConstructImageVersionPatch(update_image_version,
                                release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for environment image version.

  Args:
    update_image_version: string, the target image version.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  software_config = messages.SoftwareConfig(imageVersion=update_image_version)
  config = messages.EnvironmentConfig(softwareConfig=software_config)

  return 'config.software_config.image_version', messages.Environment(
      config=config)


def _ConstructWebServerAccessControlPatch(web_server_access_control,
                                          release_track):
  """Constructs an environment patch for web server network access control.

  Args:
    web_server_access_control: [{string: string}], the target list of IP ranges.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig(
      webServerNetworkAccessControl=environments_api_util
      .BuildWebServerNetworkAccessControl(web_server_access_control,
                                          release_track))
  return 'config.web_server_network_access_control', messages.Environment(
      config=config)


def _ConstructCloudSqlMachineTypePatch(cloud_sql_machine_type, release_track):
  """Constructs an environment patch for Cloud SQL machine type.

  Args:
    cloud_sql_machine_type: str or None, Cloud SQL machine type used by the
      Airflow database.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig(
      databaseConfig=messages.DatabaseConfig(
          machineType=cloud_sql_machine_type))
  return 'config.database_config.machine_type', messages.Environment(
      config=config)


def _ConstructWebServerMachineTypePatch(web_server_machine_type, release_track):
  """Constructs an environment patch for Airflow web server machine type.

  Args:
    web_server_machine_type: str or None, machine type used by the Airflow web
      server.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig(
      webServerConfig=messages.WebServerConfig(
          machineType=web_server_machine_type))
  return 'config.web_server_config.machine_type', messages.Environment(
      config=config)


def _ConstructMasterAuthorizedNetworksTypePatch(enabled, networks,
                                                release_track):
  """Constructs an environment patch for Master authorized networks feature.

  Args:
    enabled: bool, whether master authorized networks should be enabled.
    networks: Iterable(string), master authorized networks.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  config = messages.EnvironmentConfig()
  networks = [] if networks is None else networks
  config.masterAuthorizedNetworksConfig = messages.MasterAuthorizedNetworksConfig(
      enabled=enabled,
      cidrBlocks=[
          messages.CidrBlock(cidrBlock=network) for network in networks
      ])
  return 'config.master_authorized_networks_config', messages.Environment(
      config=config)


def _ConstructAutoscalingPatch(scheduler_cpu, worker_cpu, web_server_cpu,
                               scheduler_memory_gb, worker_memory_gb,
                               web_server_memory_gb, scheduler_storage_gb,
                               worker_storage_gb, web_server_storage_gb,
                               worker_min_count, worker_max_count,
                               scheduler_count, release_track, triggerer_cpu,
                               triggerer_memory_gb, triggerer_count,
                               dag_processor_cpu, dag_processor_memory_gb,
                               dag_processor_count, dag_processor_storage_gb):
  """Constructs an environment patch for Airflow web server machine type.

  Args:
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
    worker_min_count: int or None, minimum number of workers in the Environment.
      Can be specified only in Composer 2.0.0.
    worker_max_count: int or None, maximumn number of workers in the
      Environment. Can be specified only in Composer 2.0.0.
    scheduler_count: int or None, number of schedulers in the Environment. Can
      be specified only in Composer 2.0.0.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.
    triggerer_cpu: float or None, CPU allocated to Airflow triggerer. Can be
      specified only in Airflow 2.2.x and greater.
    triggerer_memory_gb: float or None, memory allocated to Airflow triggerer.
      Can be specified only in Airflow 2.2.x and greater.
    triggerer_count: int or None, number of triggerers in the Environment. Can
      be specified only in Airflow 2.2.x and greater
    dag_processor_cpu: float or None, CPU allocated to Airflow dag processor.
      Can be specified only in Composer 3.
    dag_processor_count: int or None, number of Airflow dag processors. Can be
      specified only in Composer 3.
    dag_processor_memory_gb: float or None, memory allocated to Airflow dag
      processor. Can be specified only in Composer 3.
    dag_processor_storage_gb: float or None, storage allocated to Airflow dag
      processor. Can be specified only in Composer 3.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)

  workload_resources = dict(
      scheduler=messages.SchedulerResource(
          cpu=scheduler_cpu,
          memoryGb=scheduler_memory_gb,
          storageGb=scheduler_storage_gb,
          count=scheduler_count),
      webServer=messages.WebServerResource(
          cpu=web_server_cpu,
          memoryGb=web_server_memory_gb,
          storageGb=web_server_storage_gb),
      worker=messages.WorkerResource(
          cpu=worker_cpu,
          memoryGb=worker_memory_gb,
          storageGb=worker_storage_gb,
          minCount=worker_min_count,
          maxCount=worker_max_count))
  if (triggerer_count is not None or
      triggerer_cpu or
      triggerer_memory_gb):
    workload_resources['triggerer'] = messages.TriggererResource(
        cpu=triggerer_cpu, memoryGb=triggerer_memory_gb, count=triggerer_count
    )
  if release_track != base.ReleaseTrack.GA:
    if dag_processor_count is not None:
      workload_resources['dagProcessor'] = messages.DagProcessorResource(
          cpu=dag_processor_cpu,
          memoryGb=dag_processor_memory_gb,
          storageGb=dag_processor_storage_gb,
          count=dag_processor_count,
      )

  config = messages.EnvironmentConfig(
      workloadsConfig=messages.WorkloadsConfig(**workload_resources))
  return 'config.workloads_config', messages.Environment(config=config)


def _ConstructMaintenanceWindowPatch(maintenance_window_start,
                                     maintenance_window_end,
                                     maintenance_window_recurrence,
                                     clear_maintenance_window,
                                     release_track=base.ReleaseTrack.GA):
  """Constructs an environment patch for updating maintenance window.

  Args:
    maintenance_window_start: Datetime or None, a starting date of the
      maintenance window.
    maintenance_window_end: Datetime or None, an ending date of the maintenance
      window.
    maintenance_window_recurrence: str or None, recurrence RRULE for the
      maintenance window.
    clear_maintenance_window: bool or None, specifies if maintenance window
      options should be cleared.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)

  if clear_maintenance_window:
    return 'config.maintenance_window', messages.Environment()

  window_value = messages.MaintenanceWindow(
      startTime=maintenance_window_start.isoformat(),
      endTime=maintenance_window_end.isoformat(),
      recurrence=maintenance_window_recurrence)
  config = messages.EnvironmentConfig(maintenanceWindow=window_value)

  return 'config.maintenance_window', messages.Environment(config=config)


def _ConstructSoftwareConfigurationSchedulerCountPatch(
    scheduler_count, release_track=base.ReleaseTrack.GA):
  """Constructs a patch for updating scheduler count for Composer 1.*.*.

  Args:
    scheduler_count: number of schedulers.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Composer client library will be used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)

  return 'config.software_config.scheduler_count', messages.Environment(
      config=messages.EnvironmentConfig(
          softwareConfig=messages.SoftwareConfig(
              schedulerCount=scheduler_count)))


def _ConstructSoftwareConfigurationCloudDataLineageIntegrationPatch(
    enabled, release_track):
  """Constructs a patch for updating Cloud Data Lineage integration config.

  Args:
    enabled: bool, whether Cloud Data Lineage integration should be enabled.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)

  return 'config.software_config.cloud_data_lineage_integration', messages.Environment(
      config=messages.EnvironmentConfig(
          softwareConfig=messages.SoftwareConfig(
              cloudDataLineageIntegration=messages.CloudDataLineageIntegration(
                  enabled=enabled))))


def _ConstructHighResiliencePatch(
    enabled, release_track):
  """Constructs a patch for updating high resilience.

  Args:
    enabled: bool, whether High resilience should be enabled.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  if not enabled:
    return 'config.resilience_mode', messages.Environment(
        config=messages.EnvironmentConfig()
    )
  return 'config.resilience_mode', messages.Environment(
      config=messages.EnvironmentConfig(
          resilienceMode=(
              messages.EnvironmentConfig.ResilienceModeValueValuesEnum.HIGH_RESILIENCE
          )
      )
  )


def _ConstructLogsInCloudLoggingOnlyPatch(enabled, release_track):
  """Constructs a patch for updating logs in cloud logging only feature.

  Args:
    enabled: bool, whether logs in cloud logging onlyshould be enabled.
    release_track: base.ReleaseTrack, the release track of command. It dictates
      which Composer client library is used.

  Returns:
    (str, Environment), the field mask and environment to use for update.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)
  if enabled:
    task_logs_retention_config = messages.TaskLogsRetentionConfig(
        storageMode=messages.TaskLogsRetentionConfig.StorageModeValueValuesEnum.CLOUD_LOGGING_ONLY
    )
  else:
    task_logs_retention_config = messages.TaskLogsRetentionConfig(
        storageMode=messages.TaskLogsRetentionConfig.StorageModeValueValuesEnum.CLOUD_LOGGING_AND_CLOUD_STORAGE
    )
  data_retention_config = messages.DataRetentionConfig(
      taskLogsRetentionConfig=task_logs_retention_config
  )
  config = messages.EnvironmentConfig(dataRetentionConfig=data_retention_config)
  return (
      'config.data_retention_config.task_logs_retention_config.storage_mode',
      messages.Environment(config=config),
  )
