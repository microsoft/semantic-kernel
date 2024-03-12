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
"""Reducer functions to generate instance props from prior state and flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import datetime

from googlecloudsdk.api_lib.sql import api_util as common_api_util
from googlecloudsdk.api_lib.sql import constants
from googlecloudsdk.api_lib.sql import exceptions as sql_exceptions
from googlecloudsdk.api_lib.sql import instances as api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
import six


def ActiveDirectoryConfig(sql_messages, domain=None):
  """Generates the Active Directory configuration for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    domain: string, the Active Directory domain value.

  Returns:
    sql_messages.SqlActiveDirectoryConfig object.
  """
  config = sql_messages.SqlActiveDirectoryConfig(domain=domain)
  return config


def SqlServerAuditConfig(sql_messages,
                         bucket=None,
                         retention_interval=None,
                         upload_interval=None):
  """Generates the Audit configuration for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    bucket: string, the GCS bucket name.
    retention_interval: duration, how long to keep generated audit files.
    upload_interval: duration, how often to upload generated audit files.

  Returns:
    sql_messages.SqlServerAuditConfig object.
  """

  if bucket is None and retention_interval is None and upload_interval is None:
    return None

  config = sql_messages.SqlServerAuditConfig()
  if bucket is not None:
    config.bucket = bucket
  if retention_interval is not None:
    config.retentionInterval = six.text_type(retention_interval) + 's'
  if upload_interval is not None:
    config.uploadInterval = six.text_type(upload_interval) + 's'

  return config


def BackupConfiguration(sql_messages,
                        instance=None,
                        backup_enabled=None,
                        backup_location=None,
                        backup_start_time=None,
                        enable_bin_log=None,
                        enable_point_in_time_recovery=None,
                        retained_backups_count=None,
                        retained_transaction_log_days=None):
  """Generates the backup configuration for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    instance: sql_messages.DatabaseInstance, the original instance, if the
      previous state is needed.
    backup_enabled: boolean, True if backup should be enabled.
    backup_location: string, location where to store backups by default.
    backup_start_time: string, start time of backup specified in 24-hour format.
    enable_bin_log: boolean, True if binary logging should be enabled.
    enable_point_in_time_recovery: boolean, True if point-in-time recovery
      (using write-ahead log archiving) should be enabled.
    retained_backups_count: int, how many backups to keep stored.
    retained_transaction_log_days: int, how many days of transaction logs to
      keep stored.

  Returns:
    sql_messages.BackupConfiguration object, or None

  Raises:
    ToolException: Bad combination of arguments.
  """
  should_generate_config = any([
      backup_location is not None,
      backup_start_time,
      enable_bin_log is not None,
      enable_point_in_time_recovery is not None,
      retained_backups_count is not None,
      retained_transaction_log_days is not None,
      not backup_enabled,
  ])

  if not should_generate_config:
    return None

  if not instance or not instance.settings.backupConfiguration:
    backup_config = sql_messages.BackupConfiguration(
        kind='sql#backupConfiguration',
        startTime='00:00',
        enabled=backup_enabled)
  else:
    backup_config = instance.settings.backupConfiguration

  if backup_location is not None:
    backup_config.location = backup_location
    backup_config.enabled = True
  if backup_start_time:
    backup_config.startTime = backup_start_time
    backup_config.enabled = True

  if retained_backups_count is not None:
    backup_retention_settings = (
        backup_config.backupRetentionSettings or
        sql_messages.BackupRetentionSettings())
    backup_retention_settings.retentionUnit = sql_messages.BackupRetentionSettings.RetentionUnitValueValuesEnum.COUNT
    backup_retention_settings.retainedBackups = retained_backups_count

    backup_config.backupRetentionSettings = backup_retention_settings
    backup_config.enabled = True

  if retained_transaction_log_days is not None:
    backup_config.transactionLogRetentionDays = retained_transaction_log_days
    backup_config.enabled = True

  if not backup_enabled:
    if (backup_location is not None or backup_start_time or
        retained_backups_count is not None or
        retained_transaction_log_days is not None):
      raise sql_exceptions.ArgumentError(
          'Argument --no-backup not allowed with --backup-location, '
          '--backup-start-time, --retained-backups-count, or '
          '--retained-transaction-log-days')
    backup_config.enabled = False

  if enable_bin_log is not None:
    backup_config.binaryLogEnabled = enable_bin_log

  if enable_point_in_time_recovery is not None:
    backup_config.pointInTimeRecoveryEnabled = enable_point_in_time_recovery
    if backup_config.replicationLogArchivingEnabled is not None:
      backup_config.replicationLogArchivingEnabled = (
          enable_point_in_time_recovery
      )

  # retainedTransactionLogDays is only valid when we have transaction logs,
  # i.e, have binlog or pitr.
  if (retained_transaction_log_days and not backup_config.binaryLogEnabled and
      not backup_config.pointInTimeRecoveryEnabled):
    raise sql_exceptions.ArgumentError(
        'Argument --retained-transaction-log-days only valid when '
        'transaction logs are enabled. To enable transaction logs, use '
        '--enable-bin-log for MySQL, and use --enable-point-in-time-recovery '
        'for Postgres.')

  return backup_config


def DatabaseFlags(sql_messages,
                  settings=None,
                  database_flags=None,
                  clear_database_flags=False):
  """Generates the database flags for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    settings: sql_messages.Settings, the original settings, if the previous
      state is needed.
    database_flags: dict of flags.
    clear_database_flags: boolean, True if flags should be cleared.

  Returns:
    list of sql_messages.DatabaseFlags objects
  """
  updated_flags = []
  if database_flags:
    for (name, value) in sorted(database_flags.items()):
      updated_flags.append(sql_messages.DatabaseFlags(name=name, value=value))
  elif clear_database_flags:
    updated_flags = []
  elif settings:
    updated_flags = settings.databaseFlags

  return updated_flags


def MaintenanceWindow(sql_messages,
                      instance,
                      maintenance_release_channel=None,
                      maintenance_window_day=None,
                      maintenance_window_hour=None):
  """Generates the maintenance window for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    instance: sql_messages.DatabaseInstance, The original instance, if it might
      be needed to generate the maintenance window.
    maintenance_release_channel: string, which channel's updates to apply.
    maintenance_window_day: string, maintenance window day of week.
    maintenance_window_hour: int, maintenance window hour of day.

  Returns:
    sql_messages.MaintenanceWindow or None

  Raises:
    argparse.ArgumentError: no maintenance window specified.
  """
  channel = maintenance_release_channel
  day = maintenance_window_day
  hour = maintenance_window_hour
  if not any([channel, day, hour]):
    return None

  maintenance_window = sql_messages.MaintenanceWindow(
      kind='sql#maintenanceWindow')

  # If there's no existing maintenance window,
  # both or neither of day and hour must be set.
  if (not instance or not instance.settings or
      not instance.settings.maintenanceWindow):
    if ((day is None and hour is not None) or
        (hour is None and day is not None)):
      raise argparse.ArgumentError(
          None, 'There is currently no maintenance window on the instance. '
          'To add one, specify values for both day, and hour.')

  if channel:
    # Map UI name to API name.
    names = {
        'week5':
            sql_messages.MaintenanceWindow.UpdateTrackValueValuesEnum.week5,
        'production':
            sql_messages.MaintenanceWindow.UpdateTrackValueValuesEnum.stable,
        'preview':
            sql_messages.MaintenanceWindow.UpdateTrackValueValuesEnum.canary
    }
    maintenance_window.updateTrack = names[channel]
  if day:
    # Map day name to number.
    day_num = arg_parsers.DayOfWeek.DAYS.index(day)
    if day_num == 0:
      day_num = 7
    maintenance_window.day = day_num
  if hour is not None:  # must execute on hour = 0
    maintenance_window.hour = hour
  return maintenance_window


def DenyMaintenancePeriod(sql_messages,
                          instance,
                          deny_maintenance_period_start_date=None,
                          deny_maintenance_period_end_date=None,
                          deny_maintenance_period_time='00:00:00'):
  """Generates the deny maintenance period for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    instance: sql_messages.DatabaseInstance, The original instance, if it might
      be needed to generate the deny maintenance period.
    deny_maintenance_period_start_date: date, Date when the deny maintenance
      period begins, i.e., 2020-11-01.
    deny_maintenance_period_end_date: date, Date when the deny maintenance
      period ends, i.e., 2021-01-10.
    deny_maintenance_period_time: Time when the deny maintenance period
      starts/ends, i.e., 05:00:00.

  Returns:
    sql_messages.DenyMaintenancePeriod or None

  Raises:
    argparse.ArgumentError: invalid deny maintenance period specified.
  """
  old_deny_maintenance_period = None
  if (instance and instance.settings and
      instance.settings.denyMaintenancePeriods and
      instance.settings.denyMaintenancePeriods[0]):
    old_deny_maintenance_period = instance.settings.denyMaintenancePeriods[0]

  deny_maintenance_period = sql_messages.DenyMaintenancePeriod()

  if old_deny_maintenance_period:
    # if there is deny maintenance period specified for the instance
    deny_maintenance_period = old_deny_maintenance_period
    if deny_maintenance_period_start_date:
      ValidateDate(deny_maintenance_period_start_date)
      deny_maintenance_period.startDate = deny_maintenance_period_start_date

    if deny_maintenance_period_end_date:
      ValidateDate(deny_maintenance_period_end_date)
      deny_maintenance_period.endDate = deny_maintenance_period_end_date

    if deny_maintenance_period_time:
      ValidTime(deny_maintenance_period_time)
      deny_maintenance_period.time = deny_maintenance_period_time
  else:
    if not (deny_maintenance_period_start_date and
            deny_maintenance_period_end_date):
      raise argparse.ArgumentError(
          None, 'There is no deny maintenance period on the instance.'
          ' To add one, specify values for both start date and end date.')
    ValidateDate(deny_maintenance_period_start_date)
    deny_maintenance_period.startDate = deny_maintenance_period_start_date

    ValidateDate(deny_maintenance_period_end_date)
    deny_maintenance_period.endDate = deny_maintenance_period_end_date

    if deny_maintenance_period_time:
      ValidTime(deny_maintenance_period_time)
      deny_maintenance_period.time = deny_maintenance_period_time

  return deny_maintenance_period


def ValidTime(s):
  try:
    datetime.datetime.strptime(s, '%H:%M:%S')
  except ValueError:
    raise argparse.ArgumentError(
        None, 'Invalid time value. The format should be HH:mm:SS.')


def ValidateDate(s):
  try:
    return datetime.datetime.strptime(s, '%Y-%m-%d')
  except ValueError:
    try:
      return datetime.datetime.strptime(s, '%m-%d')
    except ValueError:
      raise argparse.ArgumentError(
          None, 'Invalid date value. The format should be yyyy-mm-dd or mm-dd.')


def InsightsConfig(sql_messages,
                   insights_config_query_insights_enabled=None,
                   insights_config_query_string_length=None,
                   insights_config_record_application_tags=None,
                   insights_config_record_client_address=None,
                   insights_config_query_plans_per_minute=None):
  """Generates the insights config for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    insights_config_query_insights_enabled: boolean, True if query insights
      should be enabled.
    insights_config_query_string_length: number, length of the query string to
      be stored.
    insights_config_record_application_tags: boolean, True if application tags
      should be recorded.
    insights_config_record_client_address: boolean, True if client address
      should be recorded.
    insights_config_query_plans_per_minute: number, number of query plans to
      sample every minute.

  Returns:
    sql_messages.InsightsConfig or None
  """

  should_generate_config = any([
      insights_config_query_insights_enabled is not None,
      insights_config_query_string_length is not None,
      insights_config_record_application_tags is not None,
      insights_config_record_client_address is not None,
      insights_config_query_plans_per_minute is not None,
  ])
  if not should_generate_config:
    return None

  # Config exists, generate insights config.
  insights_config = sql_messages.InsightsConfig()
  if insights_config_query_insights_enabled is not None:
    insights_config.queryInsightsEnabled = (
        insights_config_query_insights_enabled)
  if insights_config_query_string_length is not None:
    insights_config.queryStringLength = insights_config_query_string_length
  if insights_config_record_application_tags is not None:
    insights_config.recordApplicationTags = (
        insights_config_record_application_tags)
  if insights_config_record_client_address is not None:
    insights_config.recordClientAddress = insights_config_record_client_address
  if insights_config_query_plans_per_minute is not None:
    insights_config.queryPlansPerMinute = insights_config_query_plans_per_minute

  return insights_config


def _CustomMachineTypeString(cpu, memory_mib):
  """Creates a custom machine type from the CPU and memory specs.

  Args:
    cpu: the number of cpu desired for the custom machine type
    memory_mib: the amount of ram desired in MiB for the custom machine type
      instance

  Returns:
    The custom machine type name for the 'instance create' call
  """
  machine_type = 'db-custom-{0}-{1}'.format(cpu, memory_mib)
  return machine_type


def MachineType(instance=None, tier=None, memory=None, cpu=None):
  """Generates the machine type for the instance.

  Adapted from compute.

  Args:
    instance: sql_messages.DatabaseInstance, The original instance, if it might
      be needed to generate the machine type.
    tier: string, the v1 or v2 tier.
    memory: string, the amount of memory.
    cpu: int, the number of CPUs.

  Returns:
    A string representing the URL naming a machine-type.

  Raises:
    exceptions.RequiredArgumentException when only one of the two custom
        machine type flags are used, or when none of the flags are used.
    exceptions.InvalidArgumentException when both the tier and
        custom machine type flags are used to generate a new instance.
  """

  # Setting the machine type.
  machine_type = None
  if tier:
    machine_type = tier

  # Setting the specs for the custom machine.
  if cpu or memory:
    if not cpu:
      raise exceptions.RequiredArgumentException(
          '--cpu', 'Both [--cpu] and [--memory] must be '
          'set to create a custom machine type instance.')
    if not memory:
      raise exceptions.RequiredArgumentException(
          '--memory', 'Both [--cpu] and [--memory] must '
          'be set to create a custom machine type instance.')
    if tier:
      raise exceptions.InvalidArgumentException(
          '--tier', 'Cannot set both [--tier] and '
          '[--cpu]/[--memory] for the same instance.')
    custom_type_string = _CustomMachineTypeString(
        cpu,
        # Converting from B to MiB.
        memory // (2**20))

    # Updating the machine type that is set for the URIs.
    machine_type = custom_type_string

  # Reverting to default if creating instance and no flags are set.
  if not machine_type and not instance:
    machine_type = constants.DEFAULT_MACHINE_TYPE

  return machine_type


def OnPremisesConfiguration(sql_messages, source_ip_address, source_port):
  """Generates the external primary configuration for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    source_ip_address: string, the IP address of the external data source.
    source_port: number, the port number of the external data source.

  Returns:
    sql_messages.OnPremisesConfiguration object.
  """
  return sql_messages.OnPremisesConfiguration(
      kind='sql#onPremisesConfiguration',
      hostPort='{0}:{1}'.format(source_ip_address, source_port))


def PrivateNetworkUrl(network):
  """Generates the self-link of the instance's private network.

  Args:
    network: The ID of the network.

  Returns:
    string, the URL of the network.
  """
  client = common_api_util.SqlClient(common_api_util.API_VERSION_DEFAULT)
  network_ref = client.resource_parser.Parse(
      network,
      params={
          'project': properties.VALUES.core.project.GetOrFail,
      },
      collection='compute.networks')
  return network_ref.SelfLink()


def ReplicaConfiguration(sql_messages,
                         primary_username,
                         primary_password,
                         primary_dump_file_path,
                         primary_ca_certificate_path=None,
                         client_certificate_path=None,
                         client_key_path=None):
  """Generates the config for an external primary replica.

  Args:
    sql_messages: module, The messages module that should be used.
    primary_username: The username for connecting to the external instance.
    primary_password: The password for connecting to the external instance.
    primary_dump_file_path: ObjectReference, a wrapper for the URI of the Cloud
      Storage path containing the dumpfile to seed the replica with.
    primary_ca_certificate_path: The path to the CA certificate PEM file.
    client_certificate_path: The path to the client certificate PEM file.
    client_key_path: The path to the client private key PEM file.

  Returns:
    sql_messages.MySqlReplicaConfiguration object.
  """
  mysql_replica_configuration = sql_messages.MySqlReplicaConfiguration(
      kind='sql#mysqlReplicaConfiguration',
      username=primary_username,
      password=primary_password,
      dumpFilePath=primary_dump_file_path.ToUrl())
  if primary_ca_certificate_path:
    mysql_replica_configuration.caCertificate = files.ReadFileContents(
        primary_ca_certificate_path)
  if client_certificate_path:
    mysql_replica_configuration.clientCertificate = files.ReadFileContents(
        client_certificate_path)
  if client_key_path:
    mysql_replica_configuration.clientKey = files.ReadFileContents(
        client_key_path)
  return sql_messages.ReplicaConfiguration(
      kind='sql#demoteMasterMysqlReplicaConfiguration',
      mysqlReplicaConfiguration=mysql_replica_configuration)


def Region(specified_region, gce_zone, secondary_zone=None):
  """Generates the region string for the instance.

  Args:
    specified_region: string, the GCE region to create the instance in.
    gce_zone: string, the GCE zone to create the instance in.
    secondary_zone: string, the GCE zone to create the standby instance in.

  Returns:
    string, the region to create the instance in.
  """
  if gce_zone and secondary_zone:
    region_from_zone = api_util.GetRegionFromZone(gce_zone)
    region_from_secondary_zone = api_util.GetRegionFromZone(secondary_zone)
    if region_from_zone != region_from_secondary_zone:
      raise exceptions.ConflictingArgumentsException(
          'Zones in arguments --zone and --secondary-zone '
          'belong to different regions.')
  if gce_zone:
    derived_region = api_util.GetRegionFromZone(gce_zone)
    return derived_region
  return specified_region


def _ParseComplexity(sql_messages, complexity):
  if complexity:
    return sql_messages.PasswordValidationPolicy.ComplexityValueValuesEnum.lookup_by_name(
        complexity.upper())
  return None


def PasswordPolicy(
    sql_messages,
    password_policy_min_length=None,
    password_policy_complexity=None,
    password_policy_reuse_interval=None,
    password_policy_disallow_username_substring=None,
    password_policy_password_change_interval=None,
    enable_password_policy=None,
    clear_password_policy=None,
):
  """Generates or clears password policy for the instance.

  Args:
    sql_messages: module, The messages module that should be used.
    password_policy_min_length: int, Minimum number of characters allowed.
    password_policy_complexity: string, The complexity of the password.
    password_policy_reuse_interval: int, Number of previous passwords that
      cannot be reused.
    password_policy_disallow_username_substring: boolean, True if disallow
      username as a part of the password.
    password_policy_password_change_interval: duration, Minimum interval at
      which password can be changed.
    enable_password_policy: boolean, True if password validation policy is
      enabled.
    clear_password_policy: boolean, True if clear existing password policy.

  Returns:
    sql_messages.PasswordValidationPolicy or None
  """
  should_generate_policy = any([
      password_policy_min_length is not None,
      password_policy_complexity is not None,
      password_policy_reuse_interval is not None,
      password_policy_disallow_username_substring is not None,
      password_policy_password_change_interval is not None,
      enable_password_policy is not None,
  ])
  if not should_generate_policy or clear_password_policy:
    return None

  # Config exists, generate password policy.
  password_policy = sql_messages.PasswordValidationPolicy()

  if password_policy_min_length is not None:
    password_policy.minLength = password_policy_min_length
  if password_policy_complexity is not None:
    password_policy.complexity = _ParseComplexity(sql_messages,
                                                  password_policy_complexity)
  if password_policy_reuse_interval is not None:
    password_policy.reuseInterval = password_policy_reuse_interval
  if password_policy_disallow_username_substring is not None:
    password_policy.disallowUsernameSubstring = password_policy_disallow_username_substring
  if password_policy_password_change_interval is not None:
    password_policy.passwordChangeInterval = str(
        password_policy_password_change_interval) + 's'
  if enable_password_policy is not None:
    password_policy.enablePasswordPolicy = enable_password_policy

  return password_policy
