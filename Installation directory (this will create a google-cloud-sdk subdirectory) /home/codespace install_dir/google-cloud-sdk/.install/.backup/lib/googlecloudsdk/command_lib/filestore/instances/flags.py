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
"""Flags and helpers for the Cloud Filestore instances commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.filestore import flags
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

INSTANCES_LIST_FORMAT = """\
    table(
      name.basename():label=INSTANCE_NAME:sort=1,
      name.segment(3):label=LOCATION,
      tier,
      fileShares[0].capacityGb:label=CAPACITY_GB,
      fileShares[0].name.yesno(no="N/A"):label=FILE_SHARE_NAME,
      networks[0].ipAddresses[0]:label=IP_ADDRESS,
      state,
      createTime.date()
    )"""

INSTANCES_LIST_FORMAT_BETA = """\
    table(
      name.basename():label=INSTANCE_NAME:sort=1,
      name.segment(3):label=LOCATION,
      tier,
      protocol,
      capacityGb:label=CAPACITY_GB,
      fileShares[0].name.yesno(no="N/A"):label=FILE_SHARE_NAME,
      networks[0].ipAddresses[0]:label=IP_ADDRESS,
      state,
      createTime.date()
    )"""

FILE_SHARE_ARG_SPEC = {
    'name':
        str,
    'capacity':
        arg_parsers.BinarySize(
            default_unit='GB',
            suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB']),
    'nfs-export-options':
        list
}

FILE_TIER_TO_TYPE = {
    'TIER_UNSPECIFIED': 'BASIC',
    'STANDARD': 'BASIC',
    'PREMIUM': 'BASIC',
    'BASIC_HDD': 'BASIC',
    'BASIC_SSD': 'BASIC',
    'ENTERPRISE': 'ENTERPRISE',
    'HIGH_SCALE_SSD': 'HIGH SCALE',
    'ZONAL': 'ZONAL',
    'REGIONAL': 'REGIONAL',
}


def AddAsyncFlag(parser):
  help_text = """Return immediately, without waiting for the operation
  in progress to complete."""
  concepts.ResourceParameterAttributeConfig(name='async', help_text=help_text)
  base.ASYNC_FLAG.AddToParser(parser)


def AddForceArg(parser):
  help_text = """Forces the deletion of an instance and its child resources,
  such as snapshots."""
  parser.add_argument(
      '--force',
      action='store_true',
      help=(help_text))


def AddClearNfsExportOptionsArg(parser):
  help_text = """Clears the NfsExportOptions. Must specify `--file-share`
  flag if --clear-nfs-export-options is specified."""
  parser.add_argument(
      '--clear-nfs-export-options',
      action='store_true',
      required=False,
      help=help_text)


def GetTierType(instance_tier):
  tier_type = dict(FILE_TIER_TO_TYPE)
  return tier_type.get(instance_tier, 'BASIC')


def AddLocationArg(parser):
  parser.add_argument(
      '--location',
      required=False,
      help='Location of the Cloud Filestore instance/operation.')


def AddRegionArg(parser):
  parser.add_argument(
      '--region',
      required=False,
      help='Region of the Cloud Filestore instance.')


def AddDescriptionArg(parser):
  parser.add_argument(
      '--description', help='A description of the Cloud Filestore instance.')


def GetAndValidateKmsKeyName(args):
  """Parse the KMS key resource arg, make sure the key format is correct."""
  kms_ref = args.CONCEPTS.kms_key.Parse()
  if kms_ref:
    return kms_ref.RelativeName()
  # If parsing fails but args were specified, raise error.
  for keyword in ['kms-key', 'kms-keyring',
                  'kms-location', 'kms-project']:
    if getattr(args, keyword.replace('-', '_'), None):
      raise exceptions.InvalidArgumentException(
          '--kms-project --kms-location --kms-keyring --kms-key',
          'Specify fully qualified KMS key ID with --kms-key, or use '
          'combination of --kms-project, --kms-location, --kms-keyring and '
          '--kms-key to specify the key ID in pieces.')
  return None  # user didn't specify KMS key


def AddKmsKeyArg(parser):
  permission_info = '{} must hold permission {}'.format(
      "The 'Filestore Service Agent' service account",
      "'Cloud KMS CryptoKey Encrypter/Decrypter'")
  kms_resource_args.AddKmsKeyResourceArg(
      parser=parser,
      resource='instance',
      permission_info=permission_info,
      required=False)


def GetTierArg(messages):
  """Adds a --tier flag to the given parser.

  Args:
    messages: The messages module.

  Returns:
    the choice arg.
  """
  custom_mappings = {
      'STANDARD': (
          'standard',
          """Standard Filestore instance, An alias for BASIC_HDD.
            Use BASIC_HDD instead whenever possible.""",
      ),
      'PREMIUM': (
          'premium',
          """Premium Filestore instance, An alias for BASIC_SSD.
                  Use BASIC_SSD instead whenever possible.""",
      ),
      'BASIC_HDD': ('basic-hdd', 'Performant NFS storage system using HDD.'),
      'BASIC_SSD': ('basic-ssd', 'Performant NFS storage system using SSD.'),
      'ENTERPRISE': (
          'enterprise',
          """Enterprise instance.
            Use REGIONAL instead whenever possible.""",
      ),
      'HIGH_SCALE_SSD': (
          'high-scale-ssd',
          """High Scale SSD instance, an alias for ZONAL.
            Use ZONAL instead whenever possible.""",
      ),
      'ZONAL': (
          'zonal',
          """Zonal instances offer NFS storage\
            system suitable for high performance computing application\
            requirements. It offers fast performance that scales\
            with capacity and allows you to grow and shrink\
            capacity.""",
      ),
      'REGIONAL': (
          'regional',
          """Regional instances offer the features\
          and availability needed for mission-critical workloads.""",
      ),
  }
  tier_arg = arg_utils.ChoiceEnumMapper(
      '--tier',
      messages.Instance.TierValueValuesEnum,
      help_str="""The service tier for the Cloud Filestore instance.
       For more details, see:
       https://cloud.google.com/filestore/docs/instance-tiers """,
      custom_mappings=custom_mappings,
      default='BASIC_HDD',
  )
  return tier_arg


def GetProtocolArg(messages):
  """Creates a --protocol flag spec for the arg parser.

  Args:
    messages: The messages module.

  Returns:
    The chosen protocol arg.
  """
  protocol_arg = arg_utils.ChoiceEnumMapper(
      '--protocol',
      messages.Instance.ProtocolValueValuesEnum,
      help_str='The service protocol for the Cloud Filestore instance.',
      custom_mappings={
          'NFS_V3': ('nfs-v3', 'NFSv3 protocol.'),
          'NFS_V4_1': ('nfs-v4-1', 'NFSv4.1 protocol.'),
      },
      default='NFS_V3',
  )
  return protocol_arg


def AddConnectManagedActiveDirectoryArg(parser):
  """Adds a --managed-ad flag to the parser.

  Args:
    parser: argparse parser.
  """

  managed_ad_arg_spec = {
      'domain': str,
      'computer': str,
  }

  managed_ad_help = """\
        Managed Active Directory configuration for an instance. Specifies both
        the domain name and a computer name (unique to the domain) to be created
        by the filestore instance.

         domain
            The desired domain full uri. i.e:
            projects/PROJECT/locations/global/domains/DOMAIN

         computer
            The desired active directory computer name to be created by
            the filestore instance when connecting to the domain.
  """

  parser.add_argument(
      '--managed-ad',
      type=arg_parsers.ArgDict(
          spec=managed_ad_arg_spec, required_keys=['domain', 'computer']
      ),
      required=False,
      help=managed_ad_help,
  )


def AddDisconnectManagedActiveDirectoryArg(parser):
  """Adds a --disconnect-managed-ad flag to the parser.

  Args:
    parser: argparse parser.
  """

  disconnnect_managed_ad_help = """\
        Disconnect the instance from Managed Active Directory."""

  parser.add_argument(
      '--disconnect-managed-ad',
      action='store_true',
      required=False,
      help=disconnnect_managed_ad_help)


def AddManagedActiveDirectoryConnectionArgs(parser):
  """Adds a --managed-ad flag to the parser.

  Args:
    parser: argparse parser.
  """

  connection_arg_group = parser.add_mutually_exclusive_group()
  AddConnectManagedActiveDirectoryArg(connection_arg_group)
  AddDisconnectManagedActiveDirectoryArg(connection_arg_group)


def AddNetworkArg(parser):
  """Adds a --network flag to the given parser.

  Args:
    parser: argparse parser.
  """

  network_arg_spec = {
      'name': str,
      'reserved-ip-range': str,
      'connect-mode': str,
  }

  network_help = """\
        Network configuration for a Cloud Filestore instance. Specifying
        `reserved-ip-range` and `connect-mode` is optional.
        *name*::: The name of the Google Compute Engine
        [VPC network](/compute/docs/networks-and-firewalls#networks) to which
        the instance is connected.
        *reserved-ip-range*::: The `reserved-ip-range` can have one of the
        following two types of values: a CIDR range value when using
        DIRECT_PEERING connect mode or an allocated IP address range
        (https://cloud.google.com/compute/docs/ip-addresses/reserve-static-internal-ip-address)
        when using PRIVATE_SERVICE_ACCESS connect mode. When the name of an
        allocated IP address range is specified, it must be one of the ranges
        associated with the private service access connection. When specified as
        a direct CIDR value, it must be a /29 CIDR block for Basic tier or a /24
        CIDR block for High Scale, Zonal, Enterprise or Regional tier in one of the internal IP
        address ranges (https://www.arin.net/knowledge/address_filters.html)
        that identifies the range of IP addresses reserved for this instance.
        For example, 10.0.0.0/29 or 192.168.0.0/24. The range you specify can't
        overlap with either existing subnets or assigned IP address ranges for
        other Cloud Filestore instances in the selected VPC network.
        *connect-mode*::: Network connection mode used by instances.
        CONNECT_MODE must be one of: DIRECT_PEERING or PRIVATE_SERVICE_ACCESS.
  """

  parser.add_argument(
      '--network',
      type=arg_parsers.ArgDict(spec=network_arg_spec, required_keys=['name']),
      required=True,
      help=network_help)


def AddFileShareArg(parser,
                    api_version,
                    include_snapshot_flags=False,
                    include_backup_flags=False,
                    clear_nfs_export_options_required=False,
                    required=True):
  """Adds a --file-share flag to the given parser.

  Args:
    parser: argparse parser.
    api_version: filestore_client api version.
    include_snapshot_flags: bool, whether to include --source-snapshot flags.
    include_backup_flags: bool, whether to include --source-backup flags.
    clear_nfs_export_options_required: bool, whether to include
      --clear-nfs-export-options flags.
    required: bool, passthrough to parser.add_argument.
  """
  alpha_beta_help_text = """
File share configuration for an instance. Specifying both `name` and `capacity`
is required.

*capacity*::: The desired capacity of the volume in GB or TB units. If no capacity
unit is specified, GB is assumed. Acceptable instance capacities for each tier are as follows:
* BASIC_HDD: 1TB-63.9TB in 1GB increments or its multiples.
* BASIC_SSD: 2.5TB-63.9TB in 1GB increments or its multiples.
* HIGH_SCALE_SSD: 10TB-100TB in 2.5TB increments or its multiples.
* ZONAL: 1TB-100TB:
  - 1TB-9.75TB in 256GB increments or its multiples.
  - 10TB-100TB in 2.5TB increments or its multiples.
* ENTERPRISE: 1TB-10TB in 256GB increments or its multiples.
* REGIONAL: 1TB-100TB:
  - 1TB-9.75TB in 256GB increments or its multiples.
  - 10TB-100TB in 2.5TB increments or its multiples.

*name*::: The desired logical name of the volume.

*nfs-export-options*::: The NfsExportOptions for the Cloud Filestore instance file share.
Configuring NfsExportOptions is optional and can only be set using flags-file. Use the `--flags-file`
flag to specify the path to a JSON or YAML configuration file that contains the required NfsExportOptions flags.

*ip-ranges*::: A list of IPv4 addresses or CIDR ranges that are allowed to mount the file share.
IPv4 addresses format: {octet 1}.{octet 2}.{octet 3}.{octet 4}.
CIDR range format: {octet 1}.{octet 2}.{octet 3}.{octet 4}/{mask size}.
Overlapping IP ranges are allowed for all tiers other than BASIC_HDD and
BASIC_SSD. The limit of IP ranges/addresses for each FileShareConfig among all
NfsExportOptions is 64 per instance.

*access-mode*::: The type of access allowed for the specified IP-addresses or CIDR ranges.
READ_ONLY: Allows only read requests on the exported file share.
READ_WRITE: Allows both read and write requests on the exported file share.
The default setting is READ_WRITE.

*squash-mode*::: Enables or disables root squash for the specified
IP addresses or CIDR ranges.
NO_ROOT_SQUASH: Disables root squash to allow root access on the exported file share.
ROOT_SQUASH. Enables root squash to remove root access on the exported file share.
The default setting is NO_ROOT_SQUASH.

*anon_uid*::: An integer that represents the user ID of anonymous users.
Anon_uid may only be set when squash_mode is set to ROOT_SQUASH.
If NO_ROOT_SQUASH is specified, an error will be returned.
The default value is 65534.

*anon_gid*::: An integer that represents the group ID of anonymous groups.
Anon_gid may only be set when squash_mode is set to ROOT_SQUASH.
If NO_ROOT_SQUASH is specified, an error will be returned.
The default value is 65534.

*security-flavors*:: A list of security flavors that are allowed to be used
during mount command in NFSv4.1 filestore instances.
The security flavors supported are:
- SECURITY_FLAVOR_UNSPECIFIED: SecurityFlavor not set. Defaults to AUTH_SYS.
- AUTH_SYS: The user's UNIX user-id and group-ids are passed in the clear.
- KRB5: The end-user authentication is done using Kerberos V5.
- KRB5I: KRB5 plus integrity protection (data packets are tamper proof).
- KRB5P: KRB5I plus privacy protection (data packets are tamper proof and
  encrypted).
"""

  file_share_help = {
      filestore_client.V1_API_VERSION:
          """\
File share configuration for an instance.  Specifying both `name` and `capacity`
is required.

*capacity*::: The desired capacity of the volume in GB or TB units. If no capacity
unit is specified, GB is assumed. Acceptable instance capacities for each tier are as follows:
* BASIC_HDD: 1TB-63.9TB in 1GB increments or its multiples.
* BASIC_SSD: 2.5TB-63.9TB in 1GB increments or its multiples.
* HIGH_SCALE_SSD: 10TB-100TB in 2.5TB increments or its multiples.
* ZONAL: 1TB-100TB:
  - 1TB-9.75TB in 256GB increments or its multiples.
  - 10TB-100TB in 2.5TB increments or its multiples.
* ENTERPRISE: 1TB-10TB in 256GB increments or its multiples.
* REGIONAL: 1TB-100TB:
  - 1TB-9.75TB in 256GB increments or its multiples.
  - 10TB-100TB in 2.5TB increments or its multiples.

*name*::: The desired logical name of the volume.

*nfs-export-options*::: The NfsExportOptions for the Cloud Filestore instance file share.
Configuring NfsExportOptions is optional and can only be set using flags-file. Use the `--flags-file`
flag to specify the path to a JSON or YAML configuration file that contains the required NfsExportOptions flags.

*ip-ranges*::: A list of IPv4 addresses or CIDR ranges that are allowed to mount the file share.
IPv4 addresses format: {octet 1}.{octet 2}.{octet 3}.{octet 4}.
CIDR range format: {octet 1}.{octet 2}.{octet 3}.{octet 4}/{mask size}.
Overlapping IP ranges are allowed for all tiers other than BASIC_HDD and
BASIC_SSD. The limit of IP ranges/addresses for each FileShareConfig among all
NfsExportOptions is 64 per instance.

*access-mode*::: The type of access allowed for the specified IP-addresses or CIDR ranges.
READ_ONLY: Allows only read requests on the exported file share.
READ_WRITE: Allows both read and write requests on the exported file share.
The default setting is READ_WRITE.

*squash-mode*::: Enables or disables root squash for the specified
IP addresses or CIDR ranges.
NO_ROOT_SQUASH: Disables root squash to allow root access on the exported file share.
ROOT_SQUASH. Enables root squash to remove root access on the exported file share.
The default setting is NO_ROOT_SQUASH.

*anon_uid*::: An integer that represents the user ID of anonymous users.
Anon_uid may only be set when squash_mode is set to ROOT_SQUASH.
If NO_ROOT_SQUASH is specified, an error will be returned.
The default value is 65534.

*anon_gid*::: An integer that represents the group ID of anonymous groups.
Anon_gid may only be set when squash_mode is set to ROOT_SQUASH.
If NO_ROOT_SQUASH is specified, an error will be returned.
The default value is 65534.
""",
      filestore_client.ALPHA_API_VERSION: alpha_beta_help_text,
      filestore_client.BETA_API_VERSION: alpha_beta_help_text
  }
  source_snapshot_help = """\

*source-snapshot*::: The name of the snapshot to restore from. Supported for BASIC instances only.

*source-snapshot-region*::: The region of the source snapshot. If
unspecified, it is assumed that the Filestore snapshot is local and
instance-zone will be used.

"""
  source_backup_help = """\

*source-backup*::: The name of the backup to restore from.

*source-backup-region*::: The region of the source backup.

"""

  spec = FILE_SHARE_ARG_SPEC.copy()
  if include_backup_flags:
    spec['source-backup'] = str
    spec['source-backup-region'] = str
  if include_snapshot_flags:
    spec['source-snapshot'] = str
    spec['source-snapshot-region'] = str

  file_share_help = file_share_help[api_version]
  if clear_nfs_export_options_required:
    required = True
    file_share_arg_group = parser.add_argument_group(
        help='Parameters for file-share.'
    )
    AddClearNfsExportOptionsArg(file_share_arg_group)
    file_share_arg_group.add_argument(
        '--file-share',
        type=arg_parsers.ArgDict(spec=spec, required_keys=['name', 'capacity']),
        required=required,
        help=file_share_help
        + (source_snapshot_help if include_snapshot_flags else '')
        + (source_backup_help if include_backup_flags else ''),
    )
  else:
    parser.add_argument(
        '--file-share',
        type=arg_parsers.ArgDict(spec=spec, required_keys=['name', 'capacity']),
        required=required,
        help=file_share_help
        + (source_snapshot_help if include_snapshot_flags else '')
        + (source_backup_help if include_backup_flags else ''),
    )


def AddInstanceCreateArgs(parser, api_version):
  """Add args for creating an instance."""
  concept_parsers.ConceptParser(
      [flags.GetInstancePresentationSpec('The instance to create.')]
  ).AddToParser(parser)
  AddDescriptionArg(parser)
  AddLocationArg(parser)
  AddRegionArg(parser)
  AddAsyncFlag(parser)
  labels_util.AddCreateLabelsFlags(parser)
  AddNetworkArg(parser)
  messages = filestore_client.GetMessages(version=api_version)
  GetTierArg(messages).choice_arg.AddToParser(parser)
  if api_version == filestore_client.BETA_API_VERSION:
    GetProtocolArg(messages).choice_arg.AddToParser(parser)
    AddConnectManagedActiveDirectoryArg(parser)
  AddFileShareArg(
      parser,
      api_version,
      include_snapshot_flags=(
          api_version == filestore_client.ALPHA_API_VERSION),
      include_backup_flags=True)
  if api_version in [filestore_client.BETA_API_VERSION,
                     filestore_client.V1_API_VERSION]:
    AddKmsKeyArg(parser)


def AddInstanceUpdateArgs(parser, api_version):
  """Add args for updating an instance."""
  concept_parsers.ConceptParser([
      flags.GetInstancePresentationSpec('The instance to update.')
  ]).AddToParser(parser)
  AddDescriptionArg(parser)
  AddLocationArg(parser)
  AddRegionArg(parser)
  AddAsyncFlag(parser)
  labels_util.AddUpdateLabelsFlags(parser)
  if api_version == filestore_client.BETA_API_VERSION:
    AddManagedActiveDirectoryConnectionArgs(parser)
  AddFileShareArg(
      parser,
      api_version,
      include_snapshot_flags=(
          api_version == filestore_client.ALPHA_API_VERSION),
      clear_nfs_export_options_required=True,
      required=False)
