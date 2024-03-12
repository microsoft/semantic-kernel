# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the connection profiles cloudsql related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


_IP_ADDRESS_PART = r'(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})'  # Match decimal 0-255
_CIDR_PREFIX_PART = r'([0-9]|[1-2][0-9]|3[0-2])'  # Match decimal 0-32
# Matches either IPv4 range in CIDR notation or a naked IPv4 address.
_CIDR_REGEX = r'{addr_part}(\.{addr_part}){{3}}(\/{prefix_part})?$'.format(
    addr_part=_IP_ADDRESS_PART, prefix_part=_CIDR_PREFIX_PART)


def AddDatabaseVersionFlag(parser, support_minor_version):
  """Adds a --database-version flag to the given parser."""
  help_text = """\
    Database engine type and version.
    """
  choices = [
      'MYSQL_5_7',
      'MYSQL_5_6',
      'MYSQL_8_0',
      'MYSQL_8_0_18',
      'MYSQL_8_0_26',
      'MYSQL_8_0_27',
      'MYSQL_8_0_28',
      'MYSQL_8_0_30',
      'MYSQL_8_0_31',
      'MYSQL_8_0_32',
      'MYSQL_8_0_33',
      'MYSQL_8_0_34',
      'MYSQL_8_0_35',
      'MYSQL_8_0_36',
      'POSTGRES_9_6',
      'POSTGRES_10',
      'POSTGRES_11',
      'POSTGRES_12',
      'POSTGRES_13',
      'POSTGRES_14',
      'POSTGRES_15',
  ]
  if not support_minor_version:
    choices = [
        'MYSQL_5_7',
        'MYSQL_5_6',
        'MYSQL_8_0',
        'POSTGRES_9_6',
        'POSTGRES_10',
        'POSTGRES_11',
        'POSTGRES_12',
        'POSTGRES_13',
        'POSTGRES_14',
        'POSTGRES_15',
    ]

  parser.add_argument(
      '--database-version', help=help_text, choices=choices, required=True)


def AddUserLabelsFlag(parser):
  """Adds a --user-labels flag to the given parser."""
  help_text = """\
    The resource labels for a Cloud SQL instance to use to annotate any related
    underlying resources such as Compute Engine VMs. An object containing a list
    of "key": "value" pairs.
    """
  parser.add_argument(
      '--user-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text)


def AddTierFlag(parser):
  """Adds a --tier flag to the given parser."""
  help_text = """\
    Tier (or machine type) for this instance, for example: ``db-n1-standard-1''
    (MySQL instances) or ``db-custom-1-3840'' (PostgreSQL instances). For more
    information, see
    [Cloud SQL Instance Settings](https://cloud.google.com/sql/docs/mysql/instance-settings).
    """
  parser.add_argument('--tier', help=help_text, required=True)


def AddEditionFlag(parser):
  """Adds a --edition flag to the given parser."""
  edition_flag = base.ChoiceArgument(
      '--edition',
      required=False,
      choices={
          'enterprise': (
              'Enterprise is the standard option for smaller instances.'
          ),
          'enterprise-plus': (
              'Enterprise plus option recommended for cpu-intensive workloads. '
              'Offers access to premium features and capabilities.'
          ),
      },
      default=None,
      help_str='Specifies edition.',
  )
  edition_flag.AddToParser(parser)


def AddStorageAutoResizeLimitFlag(parser):
  """Adds a --storage-auto-resize-limit flag to the given parser."""
  help_text = """\
    Maximum size to which storage capacity can be automatically increased. The
    default value is 0, which specifies that there is no limit.
    """
  parser.add_argument('--storage-auto-resize-limit', type=int, help=help_text)


def AddActivationPolicylag(parser):
  """Adds a --activation-policy flag to the given parser."""
  help_text = """\
    Activation policy specifies when the instance is activated; it is
    applicable only when the instance state is 'RUNNABLE'. Valid values:

    ALWAYS: The instance is on, and remains so even in the absence of
    connection requests.

    NEVER: The instance is off; it is not activated, even if a connection
    request arrives.
    """
  choices = ['ALWAYS', 'NEVER']
  parser.add_argument('--activation-policy', help=help_text, choices=choices)


def AddEnableIpv4Flag(parser):
  """Adds a --enable-ip-v4 flag to the given parser."""
  help_text = 'Whether the instance should be assigned an IPv4 address or not.'
  parser.add_argument(
      '--enable-ip-v4',
      help=help_text,
      action='store_true',
      dest='enable_ip_v4',
      default=True)


def AddPrivateNetworkFlag(parser):
  """Adds a --private-network flag to the given parser."""
  help_text = """\
    Resource link for the VPC network from which the Cloud SQL instance is
    accessible for private IP. For example,
    /projects/myProject/global/networks/default. This setting can be updated,
    but it cannot be removed after it is set.
    """
  parser.add_argument('--private-network', help=help_text)


def AddRequireSslFlag(parser):
  """Adds a --require-ssl flag to the given parser."""
  help_text = 'Whether SSL connections over IP should be enforced or not.'
  parser.add_argument(
      '--require-ssl',
      help=help_text,
      action='store_true',
      dest='require_ssl',
      default=False)


def AddAuthorizedNetworksFlag(parser):
  """Adds a `--authorized-networks` flag."""
  cidr_validator = arg_parsers.RegexpValidator(
      _CIDR_REGEX, ('Must be specified in CIDR notation, also known as '
                    '\'slash\' notation (e.g. 192.168.100.0/24).'))
  help_text = """\
    List of external networks that are allowed to connect to the instance.
    Specify values in CIDR notation, also known as 'slash' notation
    (e.g.192.168.100.0/24).
    """
  parser.add_argument(
      '--authorized-networks',
      type=arg_parsers.ArgList(min_length=1, element_type=cidr_validator),
      metavar='NETWORK',
      default=[],
      help=help_text)


def AddAutoStorageIncreaseFlag(parser):
  """Adds a --auto-storage-increase flag to the given parser."""
  help_text = """\
    If you enable this setting, Cloud SQL checks your available storage every
    30 seconds. If the available storage falls below a threshold size, Cloud
    SQL automatically adds additional storage capacity. If the available
    storage repeatedly falls below the threshold size, Cloud SQL continues to
    add storage until it reaches the maximum of 64 TB. Default: ON.
    """
  parser.add_argument(
      '--auto-storage-increase',
      help=help_text,
      action='store_true',
      dest='auto_storage_increase',
      default=True)


def AddDatabaseFlagsFlag(parser):
  """Adds a --database-flags flag to the given parser."""
  help_text = """\
    Comma-separated list of database flags to set on the instance. Use an equals
    sign to separate the flag name and value. Flags without values, like
    skip_grant_tables, can be written out without a value, e.g.,
    `skip_grant_tables=`. Use on/off values for booleans. View the Instance
    Resource API for allowed flags. (e.g., `--database-flags max_allowed_packet=55555
    skip_grant_tables=,log_output=1`).
  """
  parser.add_argument(
      '--database-flags',
      type=arg_parsers.ArgDict(),
      metavar='FLAG=VALUE',
      help=help_text)


def AddDataDiskTypeFlag(parser):
  """Adds a --data-disk-type flag to the given parser."""
  help_text = 'Type of storage.'
  choices = ['PD_SSD', 'PD_HDD']
  parser.add_argument('--data-disk-type', help=help_text, choices=choices)


def AddDataDiskSizeFlag(parser):
  """Adds a --data-disk-size flag to the given parser."""
  help_text = """\
    Storage capacity available to the database, in GB. The minimum (and
    default) size is 10GB.
  """
  parser.add_argument('--data-disk-size', type=int, help=help_text)


def AddAvailabilityTypeFlag(parser):
  """Adds a --availability-type flag to the given parser."""
  help_text = 'Cloud SQL availability type.'
  choices = ['REGIONAL', 'ZONAL']
  parser.add_argument('--availability-type', help=help_text, choices=choices)


def AddZoneFlag(parser):
  """Adds a --zone flag to the given parser."""
  help_text = """\
    Google Cloud Platform zone where your Cloud SQL database instance is
    located.
  """
  parser.add_argument('--zone', help=help_text)


def AddSecondaryZoneFlag(parser):
  """Adds a --secondary-zone flag to the given parser."""
  help_text = """\
    Google Cloud Platform zone where the failover Cloud SQL database
    instance is located. Used when the Cloud SQL database availability type
    is REGIONAL (i.e. multiple zones / highly available).
  """
  parser.add_argument('--secondary-zone', help=help_text)


def AddAllocatedIpRangeFlag(parser):
  """Adds a --allocated-ip-range flag to the given parser."""
  help_text = """\
    The name of the allocated IP range for the private IP Cloud SQL instance.
    This name refers to an already allocated IP range.
    If set, the instance IP will be created in the allocated range.
  """
  parser.add_argument('--allocated-ip-range', help=help_text)


def AddRootPassword(parser):
  """Add the root password field to the parser."""
  parser.add_argument(
      '--root-password',
      required=False,
      help="Root Cloud SQL user's password.")


def AddEnableDataCacheFlag(parser):
  """Adds a --enable-data-cache flag to the given parser."""
  parser.add_argument(
      '--enable-data-cache',
      hidden=True,
      required=False,
      action='store_true',
      dest='enable_data_cache',
      help=(
          'Enable use of data cache for accelerated read performance. This flag'
          ' is only available for Enterprise Plus edition instances.'
      )
  )
