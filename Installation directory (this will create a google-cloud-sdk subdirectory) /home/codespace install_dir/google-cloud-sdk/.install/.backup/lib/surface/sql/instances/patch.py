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
"""Updates the settings of a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.protorpclite import messages
from apitools.base.py import encoding

from googlecloudsdk.api_lib.sql import api_util as common_api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import instances as api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import instances as command_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class _Result(object):
  """Run() method result object."""

  def __init__(self, new, old):
    self.new = new
    self.old = old


def _PrintAndConfirmWarningMessage(args, database_version):
  """Print and confirm warning indicating the effect of applying the patch."""
  continue_msg = None

  insights_query_length_changed = (
      'insights_config_query_string_length' in args and
      args.insights_config_query_string_length is not None)
  if any([
      args.tier,
      args.enable_database_replication is not None,
      args.active_directory_domain is not None,
      insights_query_length_changed,
  ]):
    continue_msg = ('WARNING: This patch modifies a value that requires '
                    'your instance to be restarted. Submitting this patch '
                    'will immediately restart your instance if it\'s running.')
  elif any([args.database_flags, args.clear_database_flags]):
    database_type_fragment = 'mysql'
    if api_util.InstancesV1Beta4.IsPostgresDatabaseVersion(database_version):
      database_type_fragment = 'postgres'
    elif api_util.InstancesV1Beta4.IsSqlServerDatabaseVersion(database_version):
      database_type_fragment = 'sqlserver'
    flag_docs_url = 'https://cloud.google.com/sql/docs/{}/flags'.format(
        database_type_fragment)
    if args.database_flags is not None and any([
        'sync_binlog' in args.database_flags,
        'innodb_flush_log_at_trx_commit' in args.database_flags,
    ]):
      log.warning(
          'Changing innodb_flush_log_at_trx_commit '
          'or sync_binlog may cause data loss. Check {}'
          ' for more details.'.format(flag_docs_url)
      )
    continue_msg = (
        'WARNING: This patch modifies database flag values, which may require '
        'your instance to be restarted. Check the list of supported flags - '
        '{} - to see if your instance will be restarted when this patch '
        'is submitted.'.format(flag_docs_url))
  else:
    if any([args.follow_gae_app, args.gce_zone]):
      continue_msg = ('WARNING: This patch modifies the zone your instance '
                      'is set to run in, which may require it to be moved. '
                      'Submitting this patch will restart your instance '
                      'if it is running in a different zone.')

  if continue_msg and not console_io.PromptContinue(continue_msg):
    raise exceptions.CancelledError('canceled by the user.')


def WithoutKind(message, inline=False):
  result = message if inline else copy.deepcopy(message)
  for field in result.all_fields():
    if field.name == 'kind':
      result.kind = None
    elif isinstance(field, messages.MessageField):
      value = getattr(result, field.name)
      if value is not None:
        if isinstance(value, list):
          setattr(result, field.name,
                  [WithoutKind(item, True) for item in value])
        else:
          setattr(result, field.name, WithoutKind(value, True))
  return result


def _GetConfirmedClearedFields(args, patch_instance, original_instance):
  """Clear fields according to args and confirm with user."""
  cleared_fields = []

  if args.clear_gae_apps:
    cleared_fields.append('settings.authorizedGaeApplications')
  if args.clear_authorized_networks:
    cleared_fields.append('settings.ipConfiguration.authorizedNetworks')
  if args.clear_database_flags:
    cleared_fields.append('settings.databaseFlags')
  if args.remove_deny_maintenance_period:
    cleared_fields.append('settings.denyMaintenancePeriods')
  if args.clear_password_policy:
    cleared_fields.append('settings.passwordValidationPolicy')
  if args.IsKnownAndSpecified('clear_allowed_psc_projects'):
    cleared_fields.append(
        'settings.ipConfiguration.pscConfig.allowedConsumerProjects')

  log.status.write(
      'The following message will be used for the patch API method.\n')
  log.status.write(
      encoding.MessageToJson(
          WithoutKind(patch_instance), include_fields=cleared_fields) + '\n')

  _PrintAndConfirmWarningMessage(args, original_instance.databaseVersion)

  return cleared_fields


def AddBaseArgs(parser):
  """Adds base args and flags to the parser."""
  # TODO(b/35705305): move common flags to command_lib.sql.flags
  flags.AddActivationPolicy(parser)
  flags.AddActiveDirectoryDomain(parser)
  flags.AddAssignIp(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  gae_apps_group = parser.add_mutually_exclusive_group()
  flags.AddAuthorizedGAEApps(gae_apps_group, update=True)
  gae_apps_group.add_argument(
      '--clear-gae-apps',
      required=False,
      action='store_true',
      help=('Specified to clear the list of App Engine apps that can access '
            'this instance.'))
  networks_group = parser.add_mutually_exclusive_group()
  flags.AddAuthorizedNetworks(networks_group, update=True)
  networks_group.add_argument(
      '--clear-authorized-networks',
      required=False,
      action='store_true',
      help=('Clear the list of external networks that are allowed to connect '
            'to the instance.'))
  flags.AddAvailabilityType(parser)

  backups_group = parser.add_mutually_exclusive_group()

  backups_enabled_group = backups_group.add_group()
  flags.AddBackupStartTime(backups_enabled_group)
  flags.AddBackupLocation(backups_enabled_group, allow_empty=True)
  flags.AddRetainedBackupsCount(backups_enabled_group)
  flags.AddRetainedTransactionLogDays(backups_enabled_group)

  backups_group.add_argument(
      '--no-backup',
      required=False,
      action='store_true',
      help='Specified if daily backup should be disabled.')

  database_flags_group = parser.add_mutually_exclusive_group()
  flags.AddDatabaseFlags(database_flags_group)
  database_flags_group.add_argument(
      '--clear-database-flags',
      required=False,
      action='store_true',
      help=('Clear the database flags set on the instance. '
            'WARNING: Instance will be restarted.'))
  flags.AddCPU(parser)
  parser.add_argument(
      '--diff',
      action='store_true',
      help='Show what changed as a result of the update.')
  flags.AddEnableBinLog(parser, show_negated_in_help=True)
  parser.add_argument(
      '--enable-database-replication',
      action=arg_parsers.StoreTrueFalseAction,
      help=('Enable database replication. Applicable only for read replica '
            'instance(s). WARNING: Instance will be restarted.'))
  parser.add_argument(
      '--follow-gae-app',
      required=False,
      help=('First Generation instances only. The App Engine app '
            'this instance should follow. It must be in the same region as '
            'the instance. WARNING: Instance may be restarted.'))
  parser.add_argument(
      'instance',
      completer=flags.InstanceCompleter,
      help='Cloud SQL instance ID.')
  flags.AddMaintenanceReleaseChannel(parser)
  parser.add_argument(
      '--maintenance-window-any',
      action='store_true',
      help='Removes the user-specified maintenance window.')
  flags.AddMaintenanceWindowDay(parser)
  flags.AddMaintenanceWindowHour(parser)
  flags.AddDenyMaintenancePeriodStartDate(parser)
  flags.AddDenyMaintenancePeriodEndDate(parser)
  flags.AddDenyMaintenancePeriodTime(parser)
  parser.add_argument(
      '--remove-deny-maintenance-period',
      action='store_true',
      help='Removes the user-specified deny maintenance period.')
  flags.AddInsightsConfigQueryInsightsEnabled(parser, show_negated_in_help=True)
  flags.AddInsightsConfigQueryStringLength(parser)
  flags.AddInsightsConfigRecordApplicationTags(
      parser, show_negated_in_help=True)
  flags.AddInsightsConfigRecordClientAddress(parser, show_negated_in_help=True)
  flags.AddInsightsConfigQueryPlansPerMinute(parser)
  flags.AddMemory(parser)
  flags.AddPasswordPolicyMinLength(parser)
  flags.AddPasswordPolicyComplexity(parser)
  flags.AddPasswordPolicyReuseInterval(parser)
  flags.AddPasswordPolicyDisallowUsernameSubstring(parser)
  flags.AddPasswordPolicyPasswordChangeInterval(parser)
  flags.AddPasswordPolicyEnablePasswordPolicy(parser)
  flags.AddPasswordPolicyClearPasswordPolicy(parser)
  parser.add_argument(
      '--pricing-plan',
      '-p',
      required=False,
      choices=['PER_USE', 'PACKAGE'],
      help=('First Generation instances only. The pricing plan for this '
            'instance.'))
  flags.AddReplication(parser)
  parser.add_argument(
      '--require-ssl',
      action=arg_parsers.StoreTrueFalseAction,
      help=('mysqld should default to \'REQUIRE X509\' for users connecting '
            'over IP.'))
  flags.AddStorageAutoIncrease(parser)
  flags.AddStorageSize(parser)
  flags.AddTier(parser, is_patch=True)
  flags.AddEdition(parser)
  flags.AddEnablePointInTimeRecovery(parser)
  flags.AddNetwork(parser)
  flags.AddMaintenanceVersion(parser)
  flags.AddSqlServerAudit(parser)
  flags.AddDeletionProtection(parser)
  flags.AddConnectorEnforcement(parser)
  flags.AddEnableGooglePrivatePath(parser, show_negated_in_help=True)
  flags.AddThreadsPerCore(parser)
  flags.AddEnableDataCache(parser, show_negated_in_help=False)
  flags.AddRecreateReplicasOnPrimaryCrash(parser)
  psc_update_group = parser.add_mutually_exclusive_group()
  flags.AddAllowedPscProjects(psc_update_group)
  flags.AddClearAllowedPscProjects(psc_update_group)
  flags.AddSslMode(parser)
  flags.AddUpgradeSqlNetworkArchitecture(parser)
  flags.AddSimulateMaintenanceEvent(parser)


def AddBetaArgs(parser):
  """Adds beta args and flags to the parser."""
  flags.AddInstanceResizeLimit(parser)
  flags.AddAllocatedIpRangeName(parser)
  labels_util.AddUpdateLabelsFlags(parser, enable_clear=True)
  flags.AddReplicationLagMaxSecondsForRecreate(parser)
  flags.AddEnableGoogleMLIntegration(parser)
  flags.AddFailoverDrReplicaName(parser)
  flags.AddClearFailoverDrReplicaName(parser)


def AddAlphaArgs(unused_parser):
  """Adds alpha args and flags to the parser."""
  pass


def RunBasePatchCommand(args, release_track):
  """Updates settings of a Cloud SQL instance using the patch api method.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    release_track: base.ReleaseTrack, the release track that this was run under.

  Returns:
    A dict object representing the operations resource describing the patch
    operation if the patch was successful.
  Raises:
    CancelledError: The user chose not to continue.
  """
  if args.diff and not args.IsSpecified('format'):
    args.format = 'diff(old, new)'

  client = common_api_util.SqlClient(common_api_util.API_VERSION_DEFAULT)
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  validate.ValidateInstanceName(args.instance)
  validate.ValidateInstanceLocation(args)
  instance_ref = client.resource_parser.Parse(
      args.instance,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances')

  # If the flag to simulate a maintenance event is supplied along with other
  # flags thrown an error.
  if args.IsSpecified(
      'simulate_maintenance_event'
  ):
    for key in args.GetSpecifiedArgsDict():
      # positional argument does not have a flag argument
      if key == 'instance':
        continue
      if key == 'simulate_maintenance_event':
        continue
      if not args.GetFlagArgument(key).is_global:
        raise exceptions.ArgumentError(
            '`--simulate-maintenance-event` cannot be specified with other'
            ' arguments excluding gCloud wide flags'
        )

  if args.IsSpecified('no_backup'):
    if args.IsSpecified('enable_bin_log'):
      raise exceptions.ArgumentError(
          '`--enable-bin-log` cannot be specified when --no-backup is '
          'specified')
    elif args.IsSpecified('enable_point_in_time_recovery'):
      raise exceptions.ArgumentError(
          '`--enable-point-in-time-recovery` cannot be specified when '
          '--no-backup is specified')

  # beta only
  if args.IsKnownAndSpecified('failover_dr_replica_name'):
    if args.IsKnownAndSpecified('clear_failover_dr_replica_name'):
      raise exceptions.ArgumentError(
          '`--failover-dr-replica-name` cannot be specified when '
          '--clear-failover-dr-replica-name is specified')

  # If --authorized-networks is used, confirm that the user knows the networks
  # will get overwritten.
  if args.authorized_networks:
    api_util.InstancesV1Beta4.PrintAndConfirmAuthorizedNetworksOverwrite()

  original_instance_resource = sql_client.instances.Get(
      sql_messages.SqlInstancesGetRequest(
          project=instance_ref.project, instance=instance_ref.instance))

  patch_instance = command_util.InstancesV1Beta4.ConstructPatchInstanceFromArgs(
      sql_messages,
      args,
      original=original_instance_resource,
      release_track=release_track)
  patch_instance.project = instance_ref.project
  patch_instance.name = instance_ref.instance

  cleared_fields = _GetConfirmedClearedFields(args, patch_instance,
                                              original_instance_resource)
  # beta only
  if args.maintenance_window_any:
    cleared_fields.append('settings.maintenanceWindow')

  # beta only
  if args.IsKnownAndSpecified('clear_failover_dr_replica_name'):
    cleared_fields.append('replicationCluster')

  with sql_client.IncludeFields(cleared_fields):
    result_operation = sql_client.instances.Patch(
        sql_messages.SqlInstancesPatchRequest(
            databaseInstance=patch_instance,
            project=instance_ref.project,
            instance=instance_ref.instance))

  operation_ref = client.resource_parser.Create(
      'sql.operations',
      operation=result_operation.name,
      project=instance_ref.project)

  if args.async_:
    return sql_client.operations.Get(
        sql_messages.SqlOperationsGetRequest(
            project=operation_ref.project, operation=operation_ref.operation))

  operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                'Patching Cloud SQL instance')

  log.UpdatedResource(instance_ref)

  changed_instance_resource = sql_client.instances.Get(
      sql_messages.SqlInstancesGetRequest(
          project=instance_ref.project, instance=instance_ref.instance))
  return _Result(changed_instance_resource, original_instance_resource)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Patch(base.UpdateCommand):
  """Updates the settings of a Cloud SQL instance."""

  def Run(self, args):
    return RunBasePatchCommand(args, self.ReleaseTrack())

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    AddBaseArgs(parser)
    flags.AddZone(
        parser,
        help_text=('Preferred Compute Engine zone (e.g. us-central1-a, '
                   'us-central1-b, etc.). WARNING: Instance may be restarted.'))
    flags.AddDatabaseVersion(parser, support_default_version=False)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class PatchBeta(base.UpdateCommand):
  """Updates the settings of a Cloud SQL instance."""

  def Run(self, args):
    return RunBasePatchCommand(args, self.ReleaseTrack())

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    AddBaseArgs(parser)
    flags.AddZone(
        parser,
        help_text=('Preferred Compute Engine zone (e.g. us-central1-a, '
                   'us-central1-b, etc.). WARNING: Instance may be restarted.'))
    AddBetaArgs(parser)
    flags.AddDatabaseVersion(
        parser,
        restrict_choices=False,
        support_default_version=False)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class PatchAlpha(base.UpdateCommand):
  """Updates the settings of a Cloud SQL instance."""

  def Run(self, args):
    return RunBasePatchCommand(args, self.ReleaseTrack())

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    AddBaseArgs(parser)
    flags.AddZone(
        parser,
        help_text=('Preferred Compute Engine zone (e.g. us-central1-a, '
                   'us-central1-b, etc.). WARNING: Instance may be restarted.'))
    AddBetaArgs(parser)
    AddAlphaArgs(parser)
    flags.AddDatabaseVersion(
        parser,
        restrict_choices=False,
        support_default_version=False)
