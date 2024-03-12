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
"""Common flags for some of the SQL commands.

Flags are specified with functions that take in a single argument, the parser,
and add the newly constructed flag to that parser.

Example:

def AddFlagName(parser):
  parser.add_argument(
    '--flag-name',
    ... // Other flag details.
  )
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util import completers

messages = apis.GetMessagesModule('sql', 'v1beta4')
DEFAULT_INSTANCE_DATABASE_VERSION = 'MYSQL_8_0'

_IP_ADDRESS_PART = r'(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})'  # Match decimal 0-255
_CIDR_PREFIX_PART = r'([0-9]|[1-2][0-9]|3[0-2])'  # Match decimal 0-32
# Matches either IPv4 range in CIDR notation or a naked IPv4 address.
_CIDR_REGEX = r'{addr_part}(\.{addr_part}){{3}}(\/{prefix_part})?$'.format(
    addr_part=_IP_ADDRESS_PART, prefix_part=_CIDR_PREFIX_PART
)


class DatabaseCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DatabaseCompleter, self).__init__(
        collection='sql.databases',
        api_version='v1beta4',
        list_command='sql databases list --uri',
        flags=['instance'],
        **kwargs
    )


class InstanceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceCompleter, self).__init__(
        collection='sql.instances',
        list_command='sql instances list --uri',
        **kwargs
    )


class UserCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(UserCompleter, self).__init__(
        collection=None,  # TODO(b/62961917): Should be 'sql.users',
        api_version='v1beta4',
        list_command='sql users list --flatten=name[] --format=disable',
        flags=['instance'],
        **kwargs
    )


class _MajorVersionMatchList(list):

  def __contains__(self, database_version):
    """Check if <database_version> begins with a major_version in <self>."""
    return any(
        database_version.startswith(major_version) for major_version in self
    )


def AddInstance(parser, support_wildcard_instances=False):
  parser.add_argument(
      '--instance',
      '-i',
      required=True,
      completer=InstanceCompleter,
      help='Cloud SQL instance ID.'
      if not support_wildcard_instances
      else 'Cloud SQL instance ID or "-" for all instances.',
  )


def AddOptionalInstance(parser, support_wildcard_instances=False):
  parser.add_argument(
      '--instance',
      '-i',
      required=False,
      completer=InstanceCompleter,
      help='Cloud SQL instance ID.'
      if not support_wildcard_instances
      else 'Cloud SQL instance ID or "-" for all instances.',
  )


def AddInstanceArgument(parser):
  """Add the 'instance' argument to the parser."""
  parser.add_argument(
      'instance', completer=InstanceCompleter, help='Cloud SQL instance ID.'
  )


# The max storage size specified can be the int's max value, and min is 10.
def AddInstanceResizeLimit(parser):
  parser.add_argument(
      '--storage-auto-increase-limit',
      type=arg_parsers.BoundedInt(10, sys.maxsize, unlimited=True),
      help=(
          'Allows you to set a maximum storage capacity, in GB. Automatic'
          ' increases to your capacity will stop once this limit has been'
          ' reached. Default capacity is *unlimited*.'
      ),
  )


def AddUsername(parser):
  parser.add_argument(
      'username', completer=UserCompleter, help='Cloud SQL username.'
  )


def AddHost(parser):
  """Add the '--host' flag to the parser."""
  parser.add_argument(
      '--host',
      help=(
          "Cloud SQL user's hostname expressed as a specific IP address or"
          ' address range. `%` denotes an unrestricted hostname. Applicable'
          ' flag for MySQL instances; ignored for all other engines. Note, if'
          ' you connect to your instance using IP addresses, you must add your'
          ' client IP address as an authorized address, even if your hostname'
          ' is unrestricted. For more information, see [Configure'
          ' IP](https://cloud.google.com/sql/docs/mysql/configure-ip).'
      ),
  )


def AddAvailabilityType(parser, hidden=False):
  """Add the '--availability-type' flag to the parser."""
  availabilty_type_flag = base.ChoiceArgument(
      '--availability-type',
      required=False,
      choices={
          'regional': (
              'Provides high availability and is recommended for '
              'production instances; instance automatically fails over '
              'to another zone within your selected region.'
          ),
          'zonal': 'Provides no failover capability. This is the default.',
      },
      help_str='Specifies level of availability.',
      hidden=hidden,
  )
  availabilty_type_flag.AddToParser(parser)


def AddPassword(parser):
  parser.add_argument('--password', help="Cloud SQL user's password.")


def AddRootPassword(parser, hidden=False):
  """Add the root password field to the parser."""
  parser.add_argument(
      '--root-password',
      required=False,
      help="Root Cloud SQL user's password.",
      hidden=hidden,
  )


def AddPromptForPassword(parser):
  parser.add_argument(
      '--prompt-for-password',
      action='store_true',
      help=(
          "Prompt for the Cloud SQL user's password with character echo "
          'disabled. The password is all typed characters up to but not '
          'including the RETURN or ENTER key.'
      ),
  )


def AddType(parser):
  parser.add_argument(
      '--type',
      help=(
          "Cloud SQL user's type. It determines "
          'the method to authenticate the user during login. '
          'See the list of user types at '
          'https://cloud.google.com/sql/docs/postgres/admin-api/'
          'rest/v1beta4/SqlUserType'
      ),
  )


# Instance create and patch flags


def AddActivationPolicy(parser, hidden=False):
  base.ChoiceArgument(
      '--activation-policy',
      required=False,
      choices=['always', 'never'],
      default=None,
      hidden=hidden,
      help_str=(
          'Activation policy for this instance. This specifies when '
          'the instance should be activated and is applicable only when '
          'the instance state is `RUNNABLE`. The default is `always`. '
          'More information on activation policies can be found here: '
          'https://cloud.google.com/sql/docs/mysql/start-stop-restart-instance#activation_policy'
      ),
  ).AddToParser(parser)


def AddAssignIp(parser, hidden=False):
  parser.add_argument(
      '--assign-ip',
      help=(
          'Assign a public IP address to the instance. This is a public,'
          ' externally available IPv4 address that you can use to connect to'
          ' your instance when properly authorized.'
      ),
      hidden=hidden,
      action=arg_parsers.StoreTrueFalseAction,
  )


def AddEnableGooglePrivatePath(
    parser, show_negated_in_help=False, hidden=False
):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--enable-google-private-path',
      required=False,
      help=(
          'Enable a private path for Google Cloud services. '
          'This flag specifies whether the instance is accessible to '
          'internal Google Cloud services such as BigQuery. '
          'This is only applicable to MySQL and PostgreSQL instances that '
          "don't use public IP. Currently, SQL Server isn't supported."
      ),
      hidden=hidden,
      **kwargs
  )


def AddAuthorizedGAEApps(parser, update=False):
  help_ = (
      'First Generation instances only. List of project IDs for App Engine '
      'applications running in the Standard environment that '
      'can access this instance.'
  )
  if update:
    help_ += (
        '\n\nThe value given for this argument *replaces* the existing list.'
    )
  parser.add_argument(
      '--authorized-gae-apps',
      type=arg_parsers.ArgList(min_length=1),
      metavar='APP',
      required=False,
      help=help_,
  )


def AddAuthorizedNetworks(parser, update=False, hidden=False):
  """Adds the `--authorized-networks` flag."""
  cidr_validator = arg_parsers.RegexpValidator(
      _CIDR_REGEX,
      (
          'Must be specified in CIDR notation, also known as '
          "'slash' notation (e.g. 192.168.100.0/24)."
      ),
  )
  help_ = (
      'The list of external networks that are allowed to connect to '
      'the instance. Specified in CIDR notation, also known as '
      "'slash' notation (e.g. 192.168.100.0/24)."
  )
  if update:
    help_ += (
        '\n\nThe value given for this argument *replaces* the existing list.'
    )
  parser.add_argument(
      '--authorized-networks',
      type=arg_parsers.ArgList(min_length=1, element_type=cidr_validator),
      metavar='NETWORK',
      required=False,
      default=[],
      help=help_,
      hidden=hidden,
  )


def AddBackupStartTime(parser, hidden=False):
  parser.add_argument(
      '--backup-start-time',
      required=False,
      help=(
          'Start time of daily backups, specified in the HH:MM format, in '
          'the UTC timezone.'
      ),
      hidden=hidden,
  )


def AddBackupLocation(parser, allow_empty, hidden=False):
  help_text = (
      'Choose where to store your backups. Backups are stored in the closest '
      'multi-region location to you by default. Only customize if needed.'
  )
  if allow_empty:
    help_text += ' Specify empty string to revert to default.'
  parser.add_argument(
      '--backup-location',
      required=False,
      help=help_text,
      hidden=hidden,
  )


def AddBackup(parser, hidden=False):
  parser.add_argument(
      '--backup',
      required=False,
      action='store_true',
      default=True,
      hidden=hidden,
      help='Enables daily backup.',
  )


def AddSkipFinalBackup(parser):
  parser.add_argument(
      '--skip-final-backup',
      required=False,
      action='store_true',
      default=False,
      hidden=True,
      help=(
          'Skips the final backup to be taken at the time of instance deletion.'
      ),
  )


def AddFinalbackupRetentionDays(parser):
  help_text = (
      'Specifies number of days to retain final backup. The valid range is'
      ' between 1 and 365. Default value is 30 days.'
  )
  parser.add_argument(
      '--final-backup-retention-days',
      type=arg_parsers.BoundedInt(1, 365, unlimited=False),
      required=False,
      help=help_text,
      hidden=True,
      default=30,
  )


def AddFinalbackupDescription(parser):
  parser.add_argument(
      '--final-backup-description',
      required=False,
      hidden=True,
      help='Provides description for the final backup going to be taken.'
  )


def AddFinalBackupExpiryTimeArgument(parser):
  parser.add_argument(
      '--final-backup-expiry-time',
      type=arg_parsers.Datetime.Parse,
      required=False,
      hidden=True,
      help=(
          'Specifies the time at which the final backup will expire. Maximum'
          ' time allowed is 365 days from now. Format: YYYY-MM-DDTHH:MM:SS.'
      ),
  )


# Currently, MAX_BACKUP_RETENTION_COUNT=365, and MIN_BACKUP_RETENTION_COUNT=1.
def AddRetainedBackupsCount(parser, hidden=False):
  help_text = (
      'How many backups to keep. The valid range is between 1 and 365. '
      'Default value is 7 for Enterprise edition instances. For '
      'Enterprise_Plus, default value is 15. Applicable only if --no-backups '
      'is not specified.'
  )
  parser.add_argument(
      '--retained-backups-count',
      type=arg_parsers.BoundedInt(1, 365, unlimited=False),
      help=help_text,
      hidden=hidden,
  )


# Currently, MAX_TRANSACTION_LOG_RETENTION_DAYS=35, and
# MIN_TRANSACTION_LOG_RETENTION_DAYS=1.
def AddRetainedTransactionLogDays(parser, hidden=False):
  help_text = (
      'How many days of transaction logs to keep. The valid range is between '
      '1 and 35. Only use this option when point-in-time recovery is enabled. '
      'If logs are stored on disk, storage size for transaction logs could '
      'increase when the number of days for log retention increases. '
      'For Enterprise, default and max retention values are 7 and 7 '
      'respectively. For Enterprise_Plus, default and max '
      'retention values are 14 and 35.'
  )
  parser.add_argument(
      '--retained-transaction-log-days',
      type=arg_parsers.BoundedInt(1, 35, unlimited=False),
      help=help_text,
      hidden=hidden,
  )


def AddDatabaseFlags(parser, update=False, hidden=False):
  """Adds the `--database-flags` flag."""
  help_ = (
      'Comma-separated list of database flags to set on the '
      'instance. Use an equals sign to separate flag name and value. '
      'Flags without values, like skip_grant_tables, can be written '
      'out without a value after, e.g., `skip_grant_tables=`. Use '
      'on/off for booleans. View the Instance Resource API for allowed '
      'flags. (e.g., `--database-flags max_allowed_packet=55555,'
      'skip_grant_tables=,log_output=1`)'
  )
  if update:
    help_ += (
        '\n\nThe value given for this argument *replaces* the existing list.'
    )
  parser.add_argument(
      '--database-flags',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='FLAG=VALUE',
      required=False,
      help=help_,
      hidden=hidden,
  )


def AddDatabaseVersion(
    parser, restrict_choices=True, hidden=False, support_default_version=True
):
  """Adds `--database-version` to the parser with choices restricted or not."""
  # Section for engine-specific content.
  # This section is auto-generated by //cloud/storage_fe/sql/sync_engines.
  # Do not make manual edits.
  choices = [
      'MYSQL_5_6',
      'MYSQL_5_7',
      'MYSQL_8_0',
      'POSTGRES_9_6',
      'POSTGRES_10',
      'POSTGRES_11',
      'POSTGRES_12',
      'POSTGRES_13',
      'POSTGRES_14',
      'POSTGRES_15',
      'SQLSERVER_2017_EXPRESS',
      'SQLSERVER_2017_WEB',
      'SQLSERVER_2017_STANDARD',
      'SQLSERVER_2017_ENTERPRISE',
      'SQLSERVER_2019_EXPRESS',
      'SQLSERVER_2019_WEB',
      'SQLSERVER_2019_STANDARD',
      'SQLSERVER_2019_ENTERPRISE',
      'SQLSERVER_2022_EXPRESS',
      'SQLSERVER_2022_WEB',
      'SQLSERVER_2022_STANDARD',
      'SQLSERVER_2022_ENTERPRISE',
  ]
  # End of engine-specific content.

  help_text_unspecified_part = (
      DEFAULT_INSTANCE_DATABASE_VERSION + ' is used.'
      if support_default_version
      else 'no changes occur.'
  )
  help_text = (
      'The database engine type and versions. If left unspecified, '
      + help_text_unspecified_part
      + ' See the list of database versions at '
      + 'https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/SqlDatabaseVersion.'
  )

  if restrict_choices:
    help_text += (
        ' Apart from listed major versions, DATABASE_VERSION also accepts'
        ' supported minor versions.'
    )

  parser.add_argument(
      '--database-version',
      required=False,
      default=DEFAULT_INSTANCE_DATABASE_VERSION
      if support_default_version
      else None,
      choices=_MajorVersionMatchList(choices) if restrict_choices else None,
      help=help_text,
      hidden=hidden,
  )


def AddCPU(parser, hidden=False):
  parser.add_argument(
      '--cpu',
      type=int,
      required=False,
      help=(
          'Whole number value indicating how many cores are desired in '
          'the machine. Both --cpu and --memory must be specified if a '
          'custom machine type is desired, and the --tier flag must be '
          'omitted.'
      ),
      hidden=hidden,
  )


def _GetKwargsForBoolFlag(show_negated_in_help):
  if show_negated_in_help:
    return {
        'action': arg_parsers.StoreTrueFalseAction,
    }
  else:
    return {'action': 'store_true', 'default': None}


def AddInstanceCollation(parser, hidden=False):
  parser.add_argument(
      '--collation',
      help=(
          'Cloud SQL server-level collation setting, which specifies '
          'the set of rules for comparing characters in a character set.'
      ),
      hidden=hidden,
  )


def AddEnableBinLog(parser, show_negated_in_help=False, hidden=False):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--enable-bin-log',
      required=False,
      help=(
          'Allows for data recovery from a specific point in time, down to a '
          'fraction of a second. Must have automatic backups enabled to use. '
          'Make sure storage can support at least 7 days of logs.'
      ),
      hidden=hidden,
      **kwargs
  )


def AddEnablePointInTimeRecovery(
    parser, show_negated_in_help=False, hidden=False
):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--enable-point-in-time-recovery',
      required=False,
      help=(
          'Allows for data recovery from a specific point in time, down to a '
          'fraction of a second, via write-ahead logs. Must have automatic '
          'backups enabled to use. Make sure storage can support at least 7 '
          'days of logs.'
      ),
      hidden=hidden,
      **kwargs
  )


def AddExternalMasterGroup(parser):
  """Add flags to the parser for creating an external master and replica."""

  # Group for creating external primary instances.
  external_master_group = parser.add_group(
      required=False,
      help='Options for creating a wrapper for an external data source.',
  )
  external_master_group.add_argument(
      '--source-ip-address',
      required=True,
      type=compute_utils.IPV4Argument,
      help=(
          'Public IP address used to connect to and replicate from '
          'the external data source.'
      ),
  )
  external_master_group.add_argument(
      '--source-port',
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=65535),
      # Default MySQL port number.
      default=3306,
      help=(
          'Port number used to connect to and replicate from the '
          'external data source.'
      ),
  )

  # Group for creating replicas of external primary instances.
  internal_replica_group = parser.add_group(
      required=False,
      help=(
          'Options for creating an internal replica of an external data source.'
      ),
  )
  internal_replica_group.add_argument(
      '--master-username',
      required=True,
      help='Name of the replication user on the external data source.',
  )

  # TODO(b/78648703): Make group required when mutex required status is fixed.
  # For entering the password of the replication user of an external primary.
  master_password_group = internal_replica_group.add_group(
      'Password group.', mutex=True
  )
  master_password_group.add_argument(
      '--master-password',
      help='Password of the replication user on the external data source.',
  )
  master_password_group.add_argument(
      '--prompt-for-master-password',
      action='store_true',
      help=(
          'Prompt for the password of the replication user on the '
          'external data source. The password is all typed characters up '
          'to but not including the RETURN or ENTER key.'
      ),
  )
  internal_replica_group.add_argument(
      '--master-dump-file-path',
      required=True,
      type=storage_util.ObjectReference.FromArgument,
      help=(
          'Path to the MySQL dump file in Google Cloud Storage from '
          'which the seed import is made. The URI is in the form '
          'gs://bucketName/fileName. Compressed gzip files (.gz) are '
          'also supported.'
      ),
  )

  # For specifying SSL certs for connecting to an external primary.
  credential_group = internal_replica_group.add_group(
      'Client and server credentials.', required=False
  )
  credential_group.add_argument(
      '--master-ca-certificate-path',
      required=True,
      help=(
          'Path to a file containing the X.509v3 (RFC5280) PEM encoded '
          "certificate of the CA that signed the external data source's "
          'certificate.'
      ),
  )

  # For specifying client certs for connecting to an external primary.
  client_credential_group = credential_group.add_group(
      'Client credentials.', required=False
  )
  client_credential_group.add_argument(
      '--client-certificate-path',
      required=True,
      help=(
          'Path to a file containing the X.509v3 (RFC5280) PEM encoded '
          'certificate that will be used by the replica to authenticate '
          'against the external data source.'
      ),
  )
  client_credential_group.add_argument(
      '--client-key-path',
      required=True,
      help=(
          'Path to a file containing the unencrypted PKCS#1 or PKCS#8 '
          'PEM encoded private key associated with the '
          'clientCertificate.'
      ),
  )


def AddFailoverFlag(parser, show_negated_in_help=True):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--failover',
      required=False,
      help='Whether the promote operation is a failover.',
      **kwargs
  )


def AddFailoverReplicaName(parser, hidden=False):
  parser.add_argument(
      '--failover-replica-name',
      required=False,
      hidden=hidden,
      help='Also create a failover replica with the specified name.',
  )


def AddFailoverDrReplicaName(parser, hidden=True):
  parser.add_argument(
      '--failover-dr-replica-name',
      required=False,
      hidden=hidden,
      help=(
          'Set a Disaster Recovery (DR) replica with the specified name for '
          'the primary instance. This must be one of the existing cross region '
          'replicas of the primary instance. Flag is only available for MySQL.'
      ),
  )


def AddClearFailoverDrReplicaName(parser, hidden=True):
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--clear-failover-dr-replica-name',
      required=False,
      hidden=hidden,
      help=(
          'Clear the DR replica setting for the primary instance. Flag is only '
          'available for MySQL.'
      ),
      **kwargs
  )


def AddMasterInstanceName(parser, hidden=False):
  parser.add_argument(
      '--master-instance-name',
      required=False,
      hidden=hidden,
      help=(
          'Name of the instance which will act as master in the '
          'replication setup. The newly created instance will be a read '
          'replica of the specified master instance.'
      ),
  )


def AddStorageType(parser, hidden=False):
  parser.add_argument(
      '--storage-type',
      required=False,
      choices=['SSD', 'HDD'],
      default=None,
      hidden=hidden,
      help='The storage type for the instance. The default is SSD.',
  )


def AddReplicaType(parser, hidden=False):
  parser.add_argument(
      '--replica-type',
      choices=['READ', 'FAILOVER'],
      hidden=hidden,
      help='The type of replica to create.',
  )


def AddRequireSsl(parser, hidden=False):
  parser.add_argument(
      '--require-ssl',
      required=False,
      action='store_true',
      default=None,
      hidden=hidden,
      help='Specified if users connecting over IP must use SSL.',
  )


def AddFollowGAEApp(parser):
  parser.add_argument(
      '--follow-gae-app',
      required=False,
      help=(
          'First Generation instances only. The App Engine app '
          'this instance should follow. It must be in the same region as '
          'the instance. WARNING: Instance may be restarted.'
      ),
  )


def AddMaintenanceReleaseChannel(parser, hidden=False):
  base.ChoiceArgument(
      '--maintenance-release-channel',
      choices={
          'week5': (
              'week5 updates release after the production '
              'updates. Use the week5 channel to receive a 5 week '
              'advance notification about the upcoming maintenance, '
              'so you can prepare your application for the release.'
          ),
          'production': (
              'Production updates are stable and recommended '
              'for applications in production.'
          ),
          'preview': (
              'Preview updates release prior to production '
              'updates. You may wish to use the preview channel '
              'for dev/test applications so that you can preview '
              'their compatibility with your application prior '
              'to the production release.'
          ),
      },
      help_str=(
          "Which channel's updates to apply during the maintenance "
          'window. If not specified, Cloud SQL chooses the timing of '
          'updates to your instance.'
      ),
      hidden=hidden,
  ).AddToParser(parser)


def AddMaintenanceWindowDay(parser, hidden=False):
  parser.add_argument(
      '--maintenance-window-day',
      choices=arg_parsers.DayOfWeek.DAYS,
      type=arg_parsers.DayOfWeek.Parse,
      help='Day of week for maintenance window, in UTC time zone.',
      hidden=hidden,
  )


def AddMaintenanceWindowHour(parser, hidden=False):
  parser.add_argument(
      '--maintenance-window-hour',
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=23),
      help='Hour of day for maintenance window, in UTC time zone.',
      hidden=hidden,
  )


def AddDenyMaintenancePeriodStartDate(parser, hidden=False):
  parser.add_argument(
      '--deny-maintenance-period-start-date',
      help=(
          'Date when the deny maintenance period begins, that is'
          " ``2020-11-01''."
      ),
      hidden=hidden,
  )


def AddDenyMaintenancePeriodEndDate(parser, hidden=False):
  parser.add_argument(
      '--deny-maintenance-period-end-date',
      help=(
          "Date when the deny maintenance period ends, that is ``2021-01-10''."
      ),
      hidden=hidden,
  )


def AddDenyMaintenancePeriodTime(parser, hidden=False):
  parser.add_argument(
      '--deny-maintenance-period-time',
      help=(
          'Time when the deny maintenance period starts or ends, that is'
          " ``05:00:00''."
      ),
      hidden=hidden,
  )


def AddInsightsConfigQueryInsightsEnabled(
    parser, show_negated_in_help=False, hidden=False
):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--insights-config-query-insights-enabled',
      required=False,
      help="""Enable query insights feature to provide query and query plan
        analytics.""",
      hidden=hidden,
      **kwargs
  )


def AddInsightsConfigQueryStringLength(parser, hidden=False):
  parser.add_argument(
      '--insights-config-query-string-length',
      required=False,
      type=arg_parsers.BoundedInt(lower_bound=256, upper_bound=4500),
      help="""Query string length in bytes to be stored by the query insights
        feature. Default length is 1024 bytes. Allowed range: 256 to 4500
        bytes.""",
      hidden=hidden,
  )


def AddInsightsConfigRecordApplicationTags(
    parser, show_negated_in_help=False, hidden=False
):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--insights-config-record-application-tags',
      required=False,
      help="""Allow application tags to be recorded by the query insights
        feature.""",
      hidden=hidden,
      **kwargs
  )


def AddInsightsConfigRecordClientAddress(
    parser, show_negated_in_help=False, hidden=False
):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--insights-config-record-client-address',
      required=False,
      help="""Allow the client address to be recorded by the query insights
        feature.""",
      hidden=hidden,
      **kwargs
  )


def AddInsightsConfigQueryPlansPerMinute(parser, hidden=False):
  parser.add_argument(
      '--insights-config-query-plans-per-minute',
      required=False,
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=20),
      help="""Number of query plans to sample every minute.
        Default value is 5. Allowed range: 0 to 20.""",
      hidden=hidden,
  )


def AddMemory(parser, hidden=False):
  parser.add_argument(
      '--memory',
      type=arg_parsers.BinarySize(),
      required=False,
      help=(
          'Whole number value indicating how much memory is desired in '
          'the machine. A size unit should be provided (eg. 3072MiB or '
          '9GiB) - if no units are specified, GiB is assumed. Both --cpu '
          'and --memory must be specified if a custom machine type is '
          'desired, and the --tier flag must be omitted.'
      ),
      hidden=hidden,
  )


def AddNetwork(parser, hidden=False):
  """Adds the `--network` flag to the parser."""
  parser.add_argument(
      '--network',
      help=(
          'Network in the current project that the instance will be part '
          'of. To specify using a network with a shared VPC, use the full '
          "URL of the network. For an example host project, 'testproject', "
          "and shared network, 'testsharednetwork', this would use the "
          'form: '
          '`--network`=`projects/testproject/global/networks/'
          'testsharednetwork`'
      ),
      hidden=hidden,
  )


def AddAllocatedIpRangeName(parser):
  """Adds the `--allocated-ip-range-name` flag to the parser."""
  parser.add_argument(
      '--allocated-ip-range-name',
      required=False,
      help=(
          'The name of the IP range allocated for a Cloud SQL instance with '
          'private network connectivity. For example: '
          "'google-managed-services-default'. If set, the instance IP is "
          'created in the allocated range represented by this name.'
      ),
  )


def AddMaintenanceVersion(parser):
  """Adds the `--maintenance-version` flag to the parser."""
  parser.add_argument(
      '--maintenance-version',
      required=False,
      help='The desired maintenance version of the instance.',
  )


def AddSimulateMaintenanceEvent(parser):
  """Adds the `--simulate-maintenance-event` flag to the parser."""
  parser.add_argument(
      '--simulate-maintenance-event',
      action='store_true',
      required=False,
      help=(
          'Simulate a maintenance event without changing the version. Only'
          ' applicable to instances that support near-zero downtime planned'
          ' maintenance.'
      ),
  )


def AddSqlServerAudit(parser, hidden=False):
  """Adds SQL Server audit related flags to the parser."""
  parser.add_argument(
      '--audit-bucket-path',
      required=False,
      help=(
          'The location, as a Cloud Storage bucket, to which audit files are '
          'uploaded. The URI is in the form gs://bucketName/folderName. Only '
          'available for SQL Server instances.'
      ),
      hidden=hidden,
  )

  parser.add_argument(
      '--audit-retention-interval',
      default=None,
      type=arg_parsers.Duration(upper_bound='7d'),
      required=False,
      help=(
          'The number of days for audit log retention on disk, for example, 3d'
          'for 3 days. Only available for SQL Server instances.'
      ),
      hidden=hidden,
  )

  parser.add_argument(
      '--audit-upload-interval',
      default=None,
      type=arg_parsers.Duration(upper_bound='720m'),
      required=False,
      help=(
          'How often to upload audit logs (audit files), for example, 30m'
          'for 30 minutes. Only available for SQL Server instances.'
      ),
      hidden=hidden,
  )


def AddReplication(parser, hidden=False):
  base.ChoiceArgument(
      '--replication',
      required=False,
      choices=['synchronous', 'asynchronous'],
      default=None,
      help_str=(
          'Type of replication this instance uses. The default is synchronous.'
      ),
      hidden=hidden,
  ).AddToParser(parser)


def AddStorageAutoIncrease(parser, show_negated_in_help=True, hidden=False):
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--storage-auto-increase',
      help=(
          'Storage size can be increased, but it cannot be decreased; '
          'storage increases are permanent for the life of the instance. '
          'With this setting enabled, a spike in storage requirements '
          'can result in permanently increased storage costs for your '
          'instance. However, if an instance runs out of available space, '
          'it can result in the instance going offline, dropping existing '
          'connections. This setting is enabled by default.'
      ),
      hidden=hidden,
      **kwargs
  )


def AddStorageSize(parser, hidden=False):
  parser.add_argument(
      '--storage-size',
      type=arg_parsers.BinarySize(
          lower_bound='10GB',
          upper_bound='65536GB',
          suggested_binary_size_scales=['GB'],
      ),
      help=(
          'Amount of storage allocated to the instance. Must be an integer '
          'number of GB. The default is 10GB. Information on storage '
          'limits can be found here: '
          'https://cloud.google.com/sql/docs/quotas#storage_limits'
      ),
      hidden=hidden,
  )


def AddStorageSizeForStorageShrink(parser):
  parser.add_argument(
      '--storage-size',
      type=arg_parsers.BinarySize(
          lower_bound='10GB',
          upper_bound='65536GB',
          suggested_binary_size_scales=['GB'],
      ),
      required=True,
      help=(
          'The target storage size must be an integer that represents the'
          ' number of GB. For example, --storage-size=10GB'
      ),
  )


def AddTier(parser, is_patch=False, hidden=False):
  """Adds '--tier' flag to the parser."""
  help_text = (
      "Machine type for a shared-core instance e.g. ``db-g1-small''. "
      'For all other instances, instead of using tiers, customize '
      'your instance by specifying its CPU and memory. You can do so '
      'with the `--cpu` and `--memory` flags. Learn more about how '
      'CPU and memory affects pricing: '
      'https://cloud.google.com/sql/pricing.'
  )
  if is_patch:
    help_text += ' WARNING: Instance will be restarted.'

  parser.add_argument(
      '--tier', '-t', required=False, help=help_text, hidden=hidden
  )


def AddEdition(parser, hidden=False):
  """Adds '-edition-' flag to the parser."""
  edition_flag = base.ChoiceArgument(
      '--edition',
      required=False,
      choices=['enterprise', 'enterprise-plus'],
      default=None,
      help_str='Specifies the edition of Cloud SQL instance.',
      hidden=hidden,
  )
  edition_flag.AddToParser(parser)


def AddZone(parser, help_text, hidden=False):
  """Adds the mutually exclusive `--gce-zone` and `--zone` to the parser."""
  zone_group = parser.add_mutually_exclusive_group()
  zone_group.add_argument(
      '--gce-zone',
      required=False,
      action=actions.DeprecationAction(
          '--gce-zone',
          removed=False,
          warn=(
              'Flag `{flag_name}` is deprecated and will be removed by '
              'release 255.0.0. Use `--zone` instead.'
          ),
      ),
      help=help_text,
      hidden=hidden,
  )

  AddZonesPrimarySecondary(zone_group, help_text, hidden=hidden)


def AddZonesPrimarySecondary(parser, help_text, hidden=False):
  """Adds the `--zone` and `--secondary-zone` to the parser."""

  zone_group = parser.add_group(required=False, hidden=hidden)
  zone_group.add_argument(
      '--zone', required=False, help=help_text, hidden=hidden
  )
  zone_group.add_argument(
      '--secondary-zone',
      required=False,
      help=(
          'Preferred secondary Compute Engine zone '
          '(e.g. us-central1-a, us-central1-b, etc.).'
      ),
      hidden=hidden,
  )


def AddRegion(parser, hidden=False, specify_default_region=True):
  parser.add_argument(
      '--region',
      required=False,
      default='us-central' if specify_default_region else None,
      help=(
          'Regional location (e.g. asia-east1, us-east1). See the full '
          'list of regions at '
          'https://cloud.google.com/sql/docs/instance-locations.'
      ),
      hidden=hidden,
  )


# TODO(b/31989340): add remote completion
# TODO(b/73362371): Make specifying a location required.
def AddLocationGroup(parser, hidden=False, specify_default_region=True):
  location_group = parser.add_mutually_exclusive_group(hidden=hidden)
  AddRegion(
      location_group,
      hidden=hidden,
      specify_default_region=specify_default_region,
  )
  AddZone(
      location_group,
      help_text=(
          'Preferred Compute Engine zone (e.g. us-central1-a, '
          'us-central1-b, etc.).'
      ),
      hidden=hidden,
  )


# Database specific flags


def AddDatabaseName(parser):
  parser.add_argument(
      'database', completer=DatabaseCompleter, help='Cloud SQL database name.'
  )


def AddCharset(parser):
  parser.add_argument(
      '--charset',
      help=(
          'Cloud SQL database charset setting, which specifies the set of'
          ' symbols and encodings used to store the data in your database. Each'
          ' database version may support a different set of charsets.'
      ),
  )


def AddCollation(parser, custom_help=None):
  parser.add_argument(
      '--collation',
      help=custom_help
      or 'Cloud SQL database collation setting, which specifies the set of rules for comparing characters in a character set. Each database version may support a different set of collations. For PostgreSQL database versions, this may only be set to the collation of the template database.',
  )


def AddOperationArgument(parser):
  parser.add_argument(
      'operation',
      nargs='+',
      help='An identifier that uniquely identifies the operation.',
  )


# Instance export / import flags.


def AddUriArgument(parser, help_text):
  """Add the 'uri' argument to the parser, with help text help_text."""
  parser.add_argument('uri', help=help_text)


def AddBakImportUriArgument(parser, help_text):
  """Add the 'uri' argument to the parser, with help text help_text."""
  parser.add_argument('uri', help=help_text, nargs='?', default='')


def AddOffloadArgument(parser):
  """Add the 'offload' argument to the parser."""
  parser.add_argument(
      '--offload',
      action='store_true',
      help=(
          'Offload an export to a temporary instance. Doing so reduces strain '
          'on source instances and allows other operations to be performed '
          'while the export is in progress.'
      ),
  )


def AddParallelArgument(parser, operation):
  """Add the 'parallel' argument to the parser."""
  parser.add_argument(
      '--parallel',
      action='store_true',
      help=(
          'Perform a parallel {operation}. This flag is only applicable to'
          ' MySQL and Postgres.'
      ).format(operation=operation),
  )


def AddThreadsArgument(parser, operation):
  """Add the 'threads' argument to the parser."""
  parser.add_argument(
      '--threads',
      type=arg_parsers.BoundedInt(unlimited=True),
      help=(
          'Specifies the number of threads to use for the parallel {operation}.'
          ' If `--parallel` is specified and this flag is not provided, Cloud'
          ' SQL uses a default thread count to optimize performance.'
      ).format(operation=operation),
  )


def AddQuoteArgument(parser):
  """Add the 'quote' argument to the parser."""
  parser.add_argument(
      '--quote',
      help=(
          'Specifies the character that encloses values from columns that have '
          'string data type. The value of this argument has to be a character '
          'in Hex ASCII Code. For example, "22" represents double quotes. '
          'This flag is only available for MySQL and Postgres. If this flag is '
          'not provided, double quotes character will be used as the default '
          'value.'
      ),
  )


def AddEscapeArgument(parser):
  """Add the 'escape' argument to the parser."""
  parser.add_argument(
      '--escape',
      help=(
          'Specifies the character that should appear before a data character '
          'that needs to be escaped. The value of this argument has to be a '
          'character in Hex ASCII Code. For example, "22" represents double '
          'quotes. This flag is only available for MySQL and Postgres. If this '
          'flag is not provided, double quotes character will be used as the '
          'default value.'
      ),
  )


def AddFieldsDelimiterArgument(parser):
  """Add the 'fields-terminated-by' argument to the parser."""
  parser.add_argument(
      '--fields-terminated-by',
      help=(
          'Specifies the character that splits column values. The value of this'
          ' argument has to be a character in Hex ASCII Code. For example, "2C"'
          ' represents a comma. This flag is only available for MySQL and'
          ' Postgres. If this flag is not provided, a comma character will be'
          ' used as the default value.'
      ),
  )


def AddLinesDelimiterArgument(parser):
  """Add the 'lines-terminated-by' argument to the parser."""
  parser.add_argument(
      '--lines-terminated-by',
      help=(
          'Specifies the character that split line records. The value of this '
          'argument has to be a character in Hex ASCII Code. For example, '
          '"0A" represents a new line. This flag is only available for MySQL. '
          'If this flag is not provided, a new line character will be used as '
          'the default value.'
      ),
  )


DEFAULT_DATABASE_IMPORT_HELP_TEXT = (
    'Database to which the import is made. The database needs to be created'
    ' before importing. If not set, it is assumed that the database is'
    ' specified in the file to be imported. If your SQL dump file includes a'
    ' database statement, it will override the database set in this flag.'
)

SQLSERVER_DATABASE_IMPORT_HELP_TEXT = (
    'A new database into which the import is made.'
)


def AddDatabase(parser, help_text, required=False):
  """Add the '--database' and '-d' flags to the parser.

  Args:
    parser: The current argparse parser to add these database flags to.
    help_text: String, specifies the help text for the database flags.
    required: Boolean, specifies whether the database flag is required.
  """
  parser.add_argument('--database', '-d', required=required, help=help_text)


DEFAULT_DATABASE_LIST_EXPORT_HELP_TEXT = (
    'Database(s) from which the export is made. Information on requirements '
    'can be found here: https://cloud.google.com/sql/docs/mysql/admin-api/'
    'v1beta4/instances/export#exportContext.databases'
)

SQLSERVER_DATABASE_LIST_EXPORT_HELP_TEXT = (
    'Database from which the export is made. Information on requirements '
    'can be found here: https://cloud.google.com/sql/docs/sqlserver/admin-api/'
    'v1beta4/instances/export#exportContext.databases'
)


def AddDatabaseList(parser, help_text, required=False):
  """Add the '--database' and '-d' list flags to the parser.

  Args:
    parser: The current argparse parser to add these database flags to.
    help_text: String, specifies the help text for the database flags.
    required: Boolean, specifies whether the database flag is required.
  """
  if required:
    group = parser.add_group(mutex=False, required=True)
    group.add_argument(
        '--database',
        '-d',
        type=arg_parsers.ArgList(min_length=1),
        metavar='DATABASE',
        help=help_text,
    )
  else:
    parser.add_argument(
        '--database',
        '-d',
        type=arg_parsers.ArgList(min_length=1),
        metavar='DATABASE',
        required=False,
        help=help_text,
    )


def AddUser(parser, help_text):
  """Add the '--user' flag to the parser, with help text help_text."""
  parser.add_argument('--user', help=help_text)


def AddEncryptedBakFlags(parser):
  """Add the flags for importing encrypted BAK files.

  Add the --cert-path, --pvk-path, --pvk-password and
  --prompt-for-pvk-password flags to the parser

  Args:
    parser: The current argparse parser to add these database flags to.
  """
  enc_group = parser.add_group(
      mutex=False,
      required=False,
      help='Encryption info to support importing an encrypted .bak file',
  )
  enc_group.add_argument(
      '--cert-path',
      required=True,
      help=(
          'Path to the encryption certificate file in Google Cloud Storage '
          'associated with the BAK file. The URI is in the form '
          '`gs://bucketName/fileName`.'
      ),
  )
  enc_group.add_argument(
      '--pvk-path',
      required=True,
      help=(
          'Path to the encryption private key file in Google Cloud Storage '
          'associated with the BAK file. The URI is in the form '
          '`gs://bucketName/fileName`.'
      ),
  )
  password_group = enc_group.add_group(mutex=True, required=True)
  password_group.add_argument(
      '--pvk-password',
      help='The private key password associated with the BAK file.',
  )
  password_group.add_argument(
      '--prompt-for-pvk-password',
      action='store_true',
      help=(
          'Prompt for the private key password associated with the BAK file '
          'with character echo disabled. The password is all typed characters '
          'up to but not including the RETURN or ENTER key.'
      ),
  )


def AddBakExportStripeCountArgument(parser):
  """Add the 'stripe_count' argument to the parser for striped export."""
  parser.add_argument(
      '--stripe_count',
      type=int,
      default=None,
      help='Specifies the number of stripes to use for SQL Server exports.',
  )


def AddBakExportStripedArgument(parser, show_negated_in_help=True):
  """Add the 'striped' argument to the parser for striped export."""
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--striped',
      required=False,
      help='Whether SQL Server export should be striped.',
      **kwargs
  )


def AddBakExportBakTypeArgument(parser):
  """Add the 'bak-type' argument to the parser for bak import."""
  choices = [
      messages.ExportContext.BakExportOptionsValue.BakTypeValueValuesEnum.FULL.name,
      messages.ExportContext.BakExportOptionsValue.BakTypeValueValuesEnum.DIFF.name,
  ]
  help_text = (
      'Type of bak file that will be exported, FULL or DIFF. SQL Server only.'
  )
  parser.add_argument(
      '--bak-type',
      choices=choices,
      required=False,
      default=messages.ExportContext.BakExportOptionsValue.BakTypeValueValuesEnum.FULL.name,
      help=help_text,
  )


def AddBakExportDifferentialBaseArgument(parser):
  """Add the 'dfferential-base' argument to the parser for export."""
  parser.add_argument(
      '--differential-base',
      required=False,
      default=False,
      action='store_true',
      help=(
          'Whether the bak file export can be used as differential base for'
          ' future differential backup. SQL Server only'
      ),
  )


def AddBakImportStripedArgument(parser, show_negated_in_help=True):
  """Add the 'striped' argument to the parser for striped import."""
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--striped',
      required=False,
      help='Whether SQL Server import should be striped.',
      **kwargs
  )


def AddBakImportNoRecoveryArgument(parser):
  """Add the 'no-recovery' argument to the parser for import with no recovery option."""
  parser.add_argument(
      '--no-recovery',
      required=False,
      default=False,
      action='store_true',
      help=(
          'Whether or not the SQL Server import '
          'is execueted with NORECOVERY keyword.'
      ),
  )


def AddBakImportRecoveryOnlyArgument(parser):
  """Add the 'recovery-only' argument to the parser for bak import."""
  parser.add_argument(
      '--recovery-only',
      required=False,
      default=False,
      action='store_true',
      help=(
          'Whether or not the SQL Server import '
          'skip download and bring database online.'
      ),
  )


def AddBakImportBakTypeArgument(parser):
  """Add the 'bak-type' argument to the parser for bak import."""
  choices = [
      messages.ImportContext.BakImportOptionsValue.BakTypeValueValuesEnum.FULL.name,
      messages.ImportContext.BakImportOptionsValue.BakTypeValueValuesEnum.DIFF.name,
      messages.ImportContext.BakImportOptionsValue.BakTypeValueValuesEnum.TLOG.name,
  ]
  help_text = (
      'Type of bak file that will be imported. Applicable to SQL Server only.'
  )
  parser.add_argument(
      '--bak-type',
      choices=choices,
      required=False,
      default=messages.ImportContext.BakImportOptionsValue.BakTypeValueValuesEnum.FULL.name,
      help=help_text,
  )


def AddBakImportStopAtArgument(parser):
  """Add the 'stop-at' argument to the parser for bak import."""
  parser.add_argument(
      '--stop-at',
      type=arg_parsers.Datetime.Parse,
      required=False,
      help=(
          'Equivalent to SQL Server STOPAT keyword. '
          'Used in transaction log import only. '
          'Transaction log import stop at this timestamp. '
          'Format: YYYY-MM-DDTHH:MM:SS.'
      ),
  )


def AddBakImportStopAtMarkArgument(parser):
  """Add the 'stop-at-mark' argument to the parser for bak import."""
  parser.add_argument(
      '--stop-at-mark',
      required=False,
      help=(
          'Equivalent to SQL Server STOPATMARK keyword. '
          'Used in transaction log import only. '
          'Transaction log import stop at the given mark. '
          'To stop at given LSN, use --stop-at-mark=lsn:xxx. '
      ),
  )


def AddRescheduleType(parser):
  """Add the flag to specify reschedule type.

  Args:
    parser: The current argparse parser to add this to.
  """
  choices = [
      messages.Reschedule.RescheduleTypeValueValuesEnum.IMMEDIATE.name,
      messages.Reschedule.RescheduleTypeValueValuesEnum.NEXT_AVAILABLE_WINDOW.name,
      messages.Reschedule.RescheduleTypeValueValuesEnum.SPECIFIC_TIME.name,
  ]
  help_text = 'The type of reschedule operation to perform.'
  parser.add_argument(
      '--reschedule-type', choices=choices, required=True, help=help_text
  )


def AddScheduleTime(parser):
  """Add the flag for maintenance reschedule schedule time.

  Args:
    parser: The current argparse parser to add this to.
  """
  parser.add_argument(
      '--schedule-time',
      type=arg_parsers.Datetime.Parse,
      help=(
          'When specifying SPECIFIC_TIME, the date and time at which to '
          'schedule the maintenance in ISO 8601 format.'
      ),
  )


def AddBackupRunId(parser):
  """Add the flag for ID of backup run.

  Args:
    parser: The current argparse parser to add this to.
  """
  parser.add_argument(
      'id',
      type=arg_parsers.BoundedInt(lower_bound=1, unlimited=True),
      help=(
          'The ID of the backup run. You can find the ID by running '
          '$ gcloud sql backups list -i {instance}.'
      ),
  )


def AddBackupId(
    parser,
    help_text=(
        'The ID of the backup run. To find the ID, run the following command: '
        '$ gcloud sql backups list -i {instance}.'
    ),
):
  """Add the flag for the ID of the backup run.

  Args:
    parser: The current argparse parser to which to add this.
    help_text: The help text to display.
  """
  parser.add_argument(
      'id',
      help=help_text,
  )


def AddProjectLevelBackupEndpoint(parser):
  """Add the flag to specify requests to route to new backup service end point.

  Args:
    parser: The current argparse parser to add this to.
  """
  parser.add_argument(
      '--project-level',
      hidden=True,
      required=False,
      default=False,
      action='store_true',
      help=(
          "If true, then invoke project level backup endpoint. Use 'Name' as"
          " the value for backup ID. You can find the 'Name' by running $"
          ' gcloud sql backups list --project-level.'
      ),
  )


def AddPasswordPolicyMinLength(parser, hidden=False):
  """Add the flag to specify password policy min length.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  parser.add_argument(
      '--password-policy-min-length',
      type=int,
      required=False,
      default=None,
      help='Minimum number of characters allowed in the password.',
      hidden=hidden,
  )


def AddPasswordPolicyComplexity(parser, hidden=False):
  """Add the flag to specify password policy complexity.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  parser.add_argument(
      '--password-policy-complexity',
      choices={
          'COMPLEXITY_UNSPECIFIED': (
              'The default value if COMPLEXITY_DEFAULT is not specified. It'
              ' implies that complexity check is not enabled.'
          ),
          'COMPLEXITY_DEFAULT': (
              'A combination of lowercase, uppercase, numeric, and'
              ' non-alphanumeric characters.'
          ),
      },
      required=False,
      default=None,
      help=(
          'The complexity of the password. This flag is available only for'
          ' PostgreSQL.'
      ),
      hidden=hidden,
  )


def AddPasswordPolicyReuseInterval(parser, hidden=False):
  """Add the flag to specify password policy reuse interval.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  parser.add_argument(
      '--password-policy-reuse-interval',
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=100),
      required=False,
      default=None,
      help=(
          'Number of previous passwords that cannot be reused. The valid range'
          ' is 0 to 100.'
      ),
      hidden=hidden,
  )


def AddPasswordPolicyDisallowUsernameSubstring(
    parser, show_negated_in_help=True, hidden=False
):
  """Add the flag to specify password policy disallow username as substring.

  Args:
    parser: The current argparse parser to add this to.
    show_negated_in_help: Show nagative action in help.
    hidden: if the field needs to be hidden.
  """
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--password-policy-disallow-username-substring',
      required=False,
      help='Disallow username as a part of the password.',
      hidden=hidden,
      **kwargs
  )


def AddPasswordPolicyPasswordChangeInterval(parser, hidden=False):
  """Add the flag to specify password policy password change interval.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  parser.add_argument(
      '--password-policy-password-change-interval',
      default=None,
      type=arg_parsers.Duration(lower_bound='1s'),
      required=False,
      help="""\
        Minimum interval after which the password can be changed, for example,
        2m for 2 minutes. See <a href="/sdk/gcloud/reference/topic/datetimes">
        $ gcloud topic datetimes</a> for information on duration formats.
        This flag is available only for PostgreSQL.
      """,
      hidden=hidden,
  )


def AddPasswordPolicyEnablePasswordPolicy(
    parser, show_negated_in_help=False, hidden=False
):
  """Add the flag to enable password policy.

  Args:
    parser: The current argparse parser to add this to.
    show_negated_in_help: Show nagative action in help.
    hidden: if the field needs to be hidden.
  """
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--enable-password-policy',
      required=False,
      help="""\
        Enable the password policy, which enforces user password management with
        the policies configured for the instance. This flag is only available for Postgres.
      """,
      hidden=hidden,
      **kwargs
  )


def AddPasswordPolicyClearPasswordPolicy(parser, show_negated_in_help=False):
  """Add the flag to clear password policy.

  Args:
    parser: The current argparse parser to add this to.
    show_negated_in_help: Show nagative action in help.
  """
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--clear-password-policy',
      required=False,
      help=(
          'Clear the existing password policy. This flag is only available for'
          ' Postgres.'
      ),
      **kwargs
  )


def AddPasswordPolicyAllowedFailedAttempts(parser):
  """Add the flag to set number of failed login attempts allowed before a user is locked.

  Args:
    parser: The current argparse parser to add this to.
  """
  parser.add_argument(
      '--password-policy-allowed-failed-attempts',
      type=int,
      required=False,
      default=None,
      help=(
          'Number of failed login attempts allowed before a user is locked out.'
          ' This flag is available only for MySQL.'
      ),
  )


def AddPasswordPolicyPasswordExpirationDuration(parser):
  """Add the flag to specify expiration duration after password is updated.

  Args:
    parser: The current argparse parser to add this to.
  """
  parser.add_argument(
      '--password-policy-password-expiration-duration',
      default=None,
      type=arg_parsers.Duration(lower_bound='1s'),
      required=False,
      help="""\
        Expiration duration after a password is updated, for example,
        2d for 2 days. See `gcloud topic datetimes` for information on
        duration formats. This flag is available only for MySQL.
      """,
  )


def AddPasswordPolicyEnableFailedAttemptsCheck(
    parser, show_negated_in_help=True
):
  """Add the flag to enable the failed login attempts check.

  Args:
    parser: The current argparse parser to add this to.
    show_negated_in_help: Show nagative action in help.
  """
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--password-policy-enable-failed-attempts-check',
      required=False,
      help=(
          'Enables the failed login attempts check if set to true. This flag is'
          ' available only for MySQL.'
      ),
      **kwargs
  )


def AddPasswordPolicyEnablePasswordVerification(
    parser, show_negated_in_help=True
):
  """Add the flag to specify password policy password verification.

  Args:
    parser: The current argparse parser to add this to.
    show_negated_in_help: Show nagative action in help.
  """
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--password-policy-enable-password-verification',
      required=False,
      help=(
          'The current password must be specified when altering the password.'
          ' This flag is available only for MySQL.'
      ),
      **kwargs
  )


def AddUserRetainPassword(parser):
  """Will retain the old password when changing to the new password.

  Args:
    parser: The current argparse parser to add this to.
  """
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--retain-password',
      required=False,
      help=(
          'Retain the old password when changing to the new password. Must set'
          ' password with this flag. This flag is only available for MySQL 8.0.'
      ),
      **kwargs
  )


def AddUserDiscardDualPassword(parser):
  """Will discard the user's secondary password.

  Args:
    parser: The current argparse parser to add this to.
  """
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--discard-dual-password',
      required=False,
      help=(
          "Discard the user's secondary password. Cannot set password and set"
          ' this flag. This flag is only available for MySQL 8.0.'
      ),
      **kwargs
  )


def AddSqlServerTimeZone(parser, hidden=False):
  """Adds the `--time-zone` flag to the parser."""
  parser.add_argument(
      '--time-zone',
      required=False,
      help=(
          'Set a non-default time zone. '
          'Only available for SQL Server instances.'
      ),
      hidden=hidden,
  )


def AddThreadsPerCore(parser, hidden=False):
  """Adds the `--threads-per-core` flag to the parser."""
  parser.add_argument(
      '--threads-per-core',
      type=int,
      required=False,
      help="""\
        The number of threads per core. The value of this flag can be 1 or 2.
        To disable SMT, set this flag to 1. Only available in Cloud SQL for SQL Server instances.
      """,
      hidden=hidden,
  )


def AddShowSqlNetworkArchitecture(parser):
  """Adds the `--show-sql-network-architecture` flag to the parser."""
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--show-sql-network-architecture',
      required=False,
      help="""Show the instance's current SqlNetworkArchitecture backend in addition
        to the default output list. An instance could use either the old or new
        network architecture. The new network architecture offers better
        isolation, reliability, and faster new feature adoption.""",
      **kwargs
  )


INSTANCES_USERLABELS_FORMAT = ':(settings.userLabels:alias=labels:label=LABELS)'

INSTANCES_FORMAT_COLUMNS = [
    'name',
    'databaseVersion',
    'firstof(gceZone,region):label=LOCATION',
    'settings.tier',
    (
        'ip_addresses.filter("type:PRIMARY").*extract(ip_address).flatten()'
        '.yesno(no="-"):label=PRIMARY_ADDRESS'
    ),
    (
        'ip_addresses.filter("type:PRIVATE").*extract(ip_address).flatten()'
        '.yesno(no="-"):label=PRIVATE_ADDRESS'
    ),
    'state:label=STATUS',
]

INSTANCES_FORMAT_COLUMNS_EDITION = [
    'name',
    'databaseVersion',
    'firstof(gceZone,region):label=LOCATION',
    'settings.tier',
    'settings.edition',
    (
        'ip_addresses.filter("type:PRIMARY").*extract(ip_address).flatten()'
        '.yesno(no="-"):label=PRIMARY_ADDRESS'
    ),
    (
        'ip_addresses.filter("type:PRIVATE").*extract(ip_address).flatten()'
        '.yesno(no="-"):label=PRIVATE_ADDRESS'
    ),
    'state:label=STATUS',
]

INSTANCES_FORMAT_COLUMNS_WITH_NETWORK_ARCHITECTURE = [
    'name',
    'databaseVersion',
    'firstof(gceZone,region):label=LOCATION',
    'settings.tier',
    (
        'ip_addresses.filter("type:PRIMARY").*extract(ip_address).flatten()'
        '.yesno(no="-"):label=PRIMARY_ADDRESS'
    ),
    (
        'ip_addresses.filter("type:PRIVATE").*extract(ip_address).flatten()'
        '.yesno(no="-"):label=PRIVATE_ADDRESS'
    ),
    'state:label=STATUS',
    'sqlNetworkArchitecture:label=NETWORK_ARCHITECTURE',
]


def GetInstanceListFormatForNetworkArchitectureUpgrade():
  """Returns the table format for listing instances with current network architecture field."""
  table_format = '{} table({})'.format(
      INSTANCES_USERLABELS_FORMAT,
      ','.join(INSTANCES_FORMAT_COLUMNS_WITH_NETWORK_ARCHITECTURE),
  )

  return table_format


def GetInstanceListFormat():
  """Returns the table format for listing instances."""
  table_format = '{} table({})'.format(
      INSTANCES_USERLABELS_FORMAT, ','.join(INSTANCES_FORMAT_COLUMNS)
  )
  return table_format


def GetInstanceListFormatEdition():
  """Returns the table format for listing instances."""
  table_format = '{} table({})'.format(
      INSTANCES_USERLABELS_FORMAT, ','.join(INSTANCES_FORMAT_COLUMNS_EDITION)
  )
  return table_format


OPERATION_FORMAT = """
  table(
    operation,
    operationType:label=TYPE,
    startTime.iso():label=START,
    endTime.iso():label=END,
    error.errors[0].code.yesno(no="-"):label=ERROR,
    state:label=STATUS
  )
"""

OPERATION_FORMAT_BETA = """
  table(
    name,
    operationType:label=TYPE,
    startTime.iso():label=START,
    endTime.iso():label=END,
    error.errors[0].code.yesno(no="-"):label=ERROR,
    status:label=STATUS
  )
"""

OPERATION_FORMAT_BETA_WITH_INSERT_TIME = """
  table(
    name,
    operationType:label=TYPE,
    insertTime.iso():label=INSERTED_AT,
    startTime.iso():label=START,
    endTime.iso():label=END,
    error.errors[0].code.yesno(no="-"):label=ERROR,
    status:label=STATUS
  )
"""

CLIENT_CERTS_FORMAT = """
  table(
    commonName:label=NAME,
    sha1Fingerprint,
    expirationTime.yesno(no="-"):label=EXPIRATION
  )
"""

SERVER_CA_CERTS_FORMAT = """
  table(
    sha1Fingerprint,
    expirationTime.yesno(no="-"):label=EXPIRATION
  )
"""

TIERS_FORMAT = """
  table(
    tier,
    region.list():label=AVAILABLE_REGIONS,
    RAM.size(),
    DiskQuota.size():label=DISK
  )
"""

TIERS_FORMAT_EDITION = """
  table(
    tier,
    edition,
    region.list():label=AVAILABLE_REGIONS,
    RAM.size(),
    DiskQuota.size():label=DISK
  )
"""


def AddShowEdition(parser):
  """Show the instance or tier edition."""
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--show-edition',
      required=False,
      help='Show the edition field.',
      **kwargs
  )


def AddActiveDirectoryDomain(parser, hidden=False):
  """Adds the '--active-directory-domain' flag to the parser.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  help_text = (
      'Managed Service for Microsoft Active Directory domain this instance is '
      'joined to. Only available for SQL Server instances.'
  )
  parser.add_argument(
      '--active-directory-domain',
      help=help_text,
      hidden=hidden,
  )


def AddDeletionProtection(parser, hidden=False):
  """Adds the '--deletion-protection' flag to the parser for instances patch action.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  help_text = 'Enable deletion protection on a Cloud SQL instance.'
  parser.add_argument(
      '--deletion-protection',
      action=arg_parsers.StoreTrueFalseAction,
      help=help_text,
      hidden=hidden,
  )


def AddConnectorEnforcement(parser, hidden=False):
  """Adds the '--connector-enforcement' flag to the parser.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  help_text = (
      'Cloud SQL Connector enforcement mode. It determines how Cloud SQL '
      'Connectors are used in the connection. See the list of modes '
      '[here](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances#connectorenforcement).'
  )
  parser.add_argument(
      '--connector-enforcement',
      choices={
          'CONNECTOR_ENFORCEMENT_UNSPECIFIED': (
              'The requirement for Cloud SQL connectors is unknown.'
          ),
          'NOT_REQUIRED': 'Does not require Cloud SQL connectors.',
          'REQUIRED': (
              'Requires all connections to use Cloud SQL connectors, '
              'including the Cloud SQL Auth Proxy and Cloud SQL Java, Python, '
              'and Go connectors. Note: This disables all existing authorized '
              'networks.'
          ),
      },
      required=False,
      default=None,
      help=help_text,
      hidden=hidden,
  )


def AddTimeout(
    parser,
    default_max_wait,
    help_text='Time to synchronously wait for the operation to complete, after which the operation continues asynchronously. Ignored if --async flag is specified. By default, set to 3600s. To wait indefinitely, set to *unlimited*.',
    hidden=False,
):
  """Adds --timeout flag."""
  parser.add_argument(
      '--timeout',
      required=False,
      default=default_max_wait,
      help=help_text,
      type=arg_parsers.BoundedInt(lower_bound=0, unlimited=True),
      hidden=hidden,
  )


def AddEnablePrivateServiceConnect(parser, hidden=False):
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--enable-private-service-connect',
      required=False,
      help=(
          'When the flag is set, a Cloud SQL instance will be created with '
          'Private Service Connect enabled.'
      ),
      hidden=hidden,
      **kwargs
  )


def AddAllowedPscProjects(parser, hidden=False):
  parser.add_argument(
      '--allowed-psc-projects',
      type=arg_parsers.ArgList(min_length=1),
      required=False,
      metavar='PROJECT',
      help=(
          'A comma-separated list of projects. Each project in this list might'
          ' be represented by a project number (numeric) or by a project ID'
          ' (alphanumeric). This allows Private Service Connect connections to'
          ' be established from specified consumer projects.'
      ),
      hidden=hidden,
  )


def AddClearAllowedPscProjects(parser):
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--clear-allowed-psc-projects',
      required=False,
      help=(
          'This will clear the project allowlist of Private Service Connect,'
          ' disallowing all projects from creating new Private Service Connect'
          ' bindings to the instance.'
      ),
      **kwargs
  )


def AddRecreateReplicasOnPrimaryCrash(parser, hidden=False):
  """Adds --recreate-replicas-on-primary-crash flag."""
  parser.add_argument(
      '--recreate-replicas-on-primary-crash',
      required=False,
      help=(
          'Allow/Disallow replica recreation when a primary MySQL instance '
          'operating in reduced durability mode crashes. Not recreating the '
          'replicas might lead to data inconsistencies between the primary and '
          'its replicas. This setting is only applicable for MySQL instances '
          'and is enabled by default.'
      ),
      action=arg_parsers.StoreTrueFalseAction,
      hidden=hidden,
  )


def AddUpgradeSqlNetworkArchitecture(parser):
  """Adds --upgrade-sql-network-architecture flag."""
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--upgrade-sql-network-architecture',
      required=False,
      help=(
          """Upgrade from old network architecture to new network architecture. The
       new network architecture offers better isolation, reliability, and faster
       new feature adoption."""
      ),
      **kwargs
  )


def AddCascadableReplica(parser, hidden=False):
  """Adds --cascadable-replica flag."""
  kwargs = _GetKwargsForBoolFlag(False)
  parser.add_argument(
      '--cascadable-replica',
      required=False,
      help=(
          'Specifies whether a SQL Server replica is a cascadable replica. A'
          ' cascadable replica is a SQL Server cross-region replica that'
          ' supports replica(s) under it. This flag only takes effect when the'
          ' `--master-instance-name` flag is set, and the replica under'
          ' creation is in a different region than the primary instance.'
      ),
      hidden=hidden,
      **kwargs
  )


def AddEnableDataCache(parser, show_negated_in_help=False, hidden=False):
  """Adds '--enable-data-cache' flag to the parser."""
  kwargs = _GetKwargsForBoolFlag(show_negated_in_help)
  parser.add_argument(
      '--enable-data-cache',
      required=False,
      help=(
          'Enable use of data cache for accelerated read performance. This flag'
          ' is only available for Enterprise_Plus edition instances.'
      ),
      hidden=hidden,
      **kwargs
  )


def AddReplicationLagMaxSecondsForRecreate(parser):
  """Adds the '--replication-lag-max-seconds-for-recreate' flag to the parser for instances patch action.

  Args:
    parser: The current argparse parser to add this to.
  """
  parser.add_argument(
      '--replication-lag-max-seconds-for-recreate',
      type=arg_parsers.BoundedInt(lower_bound=300, upper_bound=31536000),
      hidden=True,
      action=arg_parsers.StoreOnceAction,
      required=False,
      help=(
          'Set a maximum replication lag for a read replica in'
          'seconds, If the replica lag exceeds the specified value, the read'
          'replica(s) will be recreated. Min value=300 seconds,'
          'Max value=31536000 seconds.'))


def AddSslMode(parser, hidden=False):
  """Adds the '--ssl-mode' flag to the parser.

  Args:
    parser: The current argparse parser to add this to.
    hidden: if the field needs to be hidden.
  """
  help_text = 'Set the SSL mode of the instance.'
  parser.add_argument(
      '--ssl-mode',
      choices={
          'ALLOW_UNENCRYPTED_AND_ENCRYPTED': (
              'Allow non-SSL and SSL connections. For SSL connections, client'
              ' certificate will not be verified.'
          ),
          'ENCRYPTED_ONLY': 'Only allow connections encrypted with SSL/TLS.',
          'TRUSTED_CLIENT_CERTIFICATE_REQUIRED': (
              'Only allow connections encrypted with SSL/TLS and with valid'
              ' client certificates.'
          ),
      },
      required=False,
      default=None,
      help=help_text,
      hidden=hidden,
  )


def AddSqlServerSsrs(parser):
  """Adds SQL Server Reporting Services (SSRS) related flags to the parser."""
  parser.add_argument(
      '--setup-login',
      required=True,
      help=(
          'Existing login in the Cloud SQL for SQL Server instance that is'
          ' used as the setup login for SSRS setup.'
      ),
  )

  parser.add_argument(
      '--service-login',
      required=True,
      help=(
          'Existing login in the Cloud SQL for SQL Server instance that is used'
          ' as the service login for SSRS setup.'
      ),
  )

  parser.add_argument(
      '--report-database',
      required=True,
      help=(
          'Existing or new report database name in the Cloud SQL for SQL Server'
          ' instance that is used for SSRS setup.'
      ),
  )

  parser.add_argument(
      '--duration',
      default=None,
      type=arg_parsers.Duration(lower_bound='1h', upper_bound='12h'),
      required=False,
      help=(
          'Time duration, in hours, that the lease will be active to allow SSRS'
          ' setup. Default lease duration is 5 hours if this flag is not'
          ' specified.'
      ),
  )


def AddEnableGoogleMLIntegration(parser):
  """Adds --enable-google-ml-integration flag."""
  parser.add_argument(
      '--enable-google-ml-integration',
      required=False,
      hidden=True,
      help=(
          'Enable Vertex AI integration for Google Cloud SQL. '
          'Currently, only PostgreSQL is supported.'
      ),
      action=arg_parsers.StoreTrueFalseAction,
  )
