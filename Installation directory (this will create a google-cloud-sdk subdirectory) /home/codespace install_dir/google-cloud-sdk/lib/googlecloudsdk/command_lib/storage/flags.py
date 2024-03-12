# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Generic flags that apply to multiple commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


REQUIRED_INVENTORY_REPORTS_METADATA_FIELDS = ('project', 'bucket', 'name')
OPTIONAL_INVENTORY_REPORTS_METADATA_FIELDS = (
    'location', 'size', 'timeCreated', 'timeDeleted',
    'updated', 'storageClass', 'etag', 'retentionExpirationTime', 'crc32c',
    'md5Hash', 'generation', 'metageneration', 'contentType',
    'contentEncoding', 'timeStorageClassUpdated')
ALL_INVENTORY_REPORTS_METADATA_FIELDS = (
    REQUIRED_INVENTORY_REPORTS_METADATA_FIELDS +
    OPTIONAL_INVENTORY_REPORTS_METADATA_FIELDS)


class ReplicationStrategy(enum.Enum):
  """Enum class for specifying the replication setting."""
  DEFAULT = 'DEFAULT'
  ASYNC_TURBO = 'ASYNC_TURBO'


class RetentionMode(enum.Enum):
  """Enum class for specifying the retention mode."""
  LOCKED = 'Locked'
  UNLOCKED = 'Unlocked'


def get_object_state_from_flags(flag_args):
  """Returns object version to query based on user flags."""
  if getattr(flag_args, 'soft_deleted', False):
    return cloud_api.ObjectState.SOFT_DELETED
  if getattr(flag_args, 'all_versions', False):
    return cloud_api.ObjectState.LIVE_AND_NONCURRENT
  return cloud_api.ObjectState.LIVE


def add_additional_headers_flag(parser):
  """Adds a flag that allows users to specify arbitrary headers in API calls."""
  parser.add_argument(
      '--additional-headers',
      action=actions.StoreProperty(
          properties.VALUES.storage.additional_headers),
      metavar='HEADER=VALUE',
      help='Includes arbitrary headers in storage API calls.'
      ' Accepts a comma separated list of key=value pairs, e.g.'
      ' `header1=value1,header2=value2`.')


def add_autoclass_flags(parser):
  """Adds flags required for modifying Autoclass feature."""
  autoclass_group = parser.add_group(category='AUTOCLASS')
  autoclass_group.add_argument(
      '--enable-autoclass',
      action=arg_parsers.StoreTrueFalseAction,
      help='The Autoclass feature automatically selects the best storage class'
      ' for objects based on access patterns.')
  autoclass_group.add_argument(
      '--autoclass-terminal-storage-class',
      help='The storage class that objects in the bucket eventually'
      ' transition to if they are not read for a certain length of time.'
      ' Only valid if Autoclass is enabled.')


def add_fetch_encrypted_object_hashes_flag(parser, is_list=True):
  """Adds flag to commands that need object hashes."""
  if is_list:
    help_text = (
        'API requests to the LIST endpoint do not fetch the hashes for'
        ' encrypted objects by default. If this flag is set, a GET request'
        ' is sent for each encrypted object in order to fetch hashes. This'
        ' can significantly increase the cost of the command.')
  else:
    help_text = (
        'If the initial GET request returns an object encrypted with a'
        ' customer-supplied encryption key, the hash fields will be null.'
        ' If the matching decryption key is present on the system, this flag'
        ' retries the GET request with the key.')
  parser.add_argument(
      '--fetch-encrypted-object-hashes', action='store_true', help=help_text)


def add_predefined_acl_flag(parser):
  """Adds predefined ACL flag shared for both buckets and objects."""
  parser.add_argument(
      '-a',
      '--predefined-acl',
      '--canned-acl',
      help=(
          'Applies predefined, or "canned," ACLs to a resource. See'
          ' docs for a list of predefined ACL constants:'
          ' https://cloud.google.com'
          '/storage/docs/access-control/lists#predefined-acl'
      ),
  )


def add_preserve_acl_flag(parser, hidden=False):
  """Adds preserve ACL flag."""
  parser.add_argument(
      '--preserve-acl',
      '-p',
      action=arg_parsers.StoreTrueFalseAction,
      hidden=hidden,
      help=(
          'Preserves ACLs when copying in the cloud. This option is Cloud'
          ' Storage-only, and you need OWNER access to all copied objects. If'
          ' all objects in the destination bucket should have the same ACL, you'
          ' can also set a default object ACL on that bucket instead of using'
          ' this flag.\nPreserving ACLs is the default behavior for updating'
          ' existing objects.'
      ),
  )


def add_acl_modifier_flags(parser):
  """Adds flags common among commands that modify ACLs."""
  add_predefined_acl_flag(parser)
  parser.add_argument(
      '--acl-file',
      help=(
          'Path to a local JSON or YAML formatted file containing a valid'
          ' policy. See the'
          ' [ObjectAccessControls resource](https://cloud.google.com/storage'
          '/docs/json_api/v1/objectAccessControls) for a representation of'
          ' JSON formatted files. The output of'
          ' `gcloud storage [buckets|objects] describe`'
          ' `--format="multi(acl:format=json)"` is a valid file and can be'
          ' edited for more fine-grained control.'
      ),
  )
  parser.add_argument(
      '--add-acl-grant',
      action='append',
      metavar='ACL_GRANT',
      type=arg_parsers.ArgDict(),
      help=(
          'Key-value pairs mirroring the JSON accepted by your cloud provider.'
          ' For example, for Cloud Storage,'
          '`--add-acl-grant=entity=user-tim@gmail.com,role=OWNER`'
      ),
  )
  parser.add_argument(
      '--remove-acl-grant',
      action='append',
      help=(
          'Key-value pairs mirroring the JSON accepted by your cloud provider.'
          ' For example, for Cloud Storage, `--remove-acl-grant=ENTITY`,'
          ' where `ENTITY` has a valid ACL entity format,'
          ' such as `user-tim@gmail.com`,'
          ' `group-admins`, `allUsers`, etc.'
      ),
  )


def add_precondition_flags(parser):
  """Add flags indicating a precondition for an operation to happen."""
  preconditions_group = parser.add_group(
      category='PRECONDITION',
  )
  preconditions_group.add_argument(
      '--if-generation-match',
      metavar='GENERATION',
      help='Execute only if the generation matches the generation of the'
      ' requested object.')
  preconditions_group.add_argument(
      '--if-metageneration-match',
      metavar='METAGENERATION',
      help='Execute only if the metageneration matches the metageneration of'
      ' the requested object.')


def add_object_metadata_flags(parser, allow_patch=False):
  """Add flags that allow setting object metadata."""
  metadata_group = parser.add_group(category='OBJECT METADATA')
  metadata_group.add_argument(
      '--cache-control',
      help='How caches should handle requests and responses.')
  metadata_group.add_argument(
      '--content-disposition',
      help='How content should be displayed.')
  metadata_group.add_argument(
      '--content-encoding', help='How content is encoded (e.g. ``gzip\'\').')
  metadata_group.add_argument(
      '--content-language',
      help='Content\'s language (e.g. ``en\'\' signifies "English").')
  metadata_group.add_argument(
      '--content-type',
      help='Type of data contained in the object (e.g. ``text/html\'\').')
  metadata_group.add_argument(
      '--custom-time',
      type=arg_parsers.Datetime.Parse,
      help='Custom time for Cloud Storage objects in RFC 3339 format.')

  # TODO(b/238631069): Refactor to make use of command_lib/util/args/map_util.py
  custom_metadata_group = metadata_group.add_mutually_exclusive_group()
  custom_metadata_group.add_argument(
      '--custom-metadata',
      metavar='CUSTOM_METADATA_KEYS_AND_VALUES',
      type=arg_parsers.ArgDict(),
      help=(
          'Sets custom metadata on objects. When used with `--preserve-posix`,'
          ' POSIX attributes are also stored in custom metadata.'))

  custom_metadata_group.add_argument(
      '--clear-custom-metadata',
      action='store_true',
      help=(
          'Clears all custom metadata on objects. When used with'
          ' `--preserve-posix`, POSIX attributes will still be stored in custom'
          ' metadata.'))

  update_custom_metadata_group = custom_metadata_group.add_group(
      help=(
          'Flags that preserve unspecified existing metadata cannot be used'
          ' with `--custom-metadata` or `--clear-custom-metadata`, but can be'
          ' specified together:'))
  update_custom_metadata_group.add_argument(
      '--update-custom-metadata',
      metavar='CUSTOM_METADATA_KEYS_AND_VALUES',
      type=arg_parsers.ArgDict(),
      help=(
          'Adds or sets individual custom metadata key value pairs on objects.'
          ' Existing custom metadata not specified with this flag is not'
          ' changed. This flag can be used with `--remove-custom-metadata`.'
          ' When keys overlap with those provided by `--preserve-posix`, values'
          ' specified by this flag are used.'))
  update_custom_metadata_group.add_argument(
      '--remove-custom-metadata',
      metavar='METADATA_KEYS',
      type=arg_parsers.ArgList(),
      help=(
          'Removes individual custom metadata keys from objects. This flag can'
          ' be used with `--update-custom-metadata`. When used with'
          ' `--preserve-posix`, POSIX attributes specified by this flag are not'
          ' preserved.'))

  if allow_patch:
    metadata_group.add_argument(
        '--clear-cache-control',
        action='store_true',
        help='Clears object cache control.')
    metadata_group.add_argument(
        '--clear-content-disposition',
        action='store_true',
        help='Clears object content disposition.')
    metadata_group.add_argument(
        '--clear-content-encoding',
        action='store_true',
        help='Clears content encoding.')
    metadata_group.add_argument(
        '--clear-content-language',
        action='store_true',
        help='Clears object content language.')
    metadata_group.add_argument(
        '--clear-content-type',
        action='store_true',
        help='Clears object content type.')
    metadata_group.add_argument(
        '--clear-custom-time',
        action='store_true',
        help='Clears object custom time.')


def add_encryption_flags(parser,
                         allow_patch=False,
                         command_only_reads_data=False,
                         hidden=False):
  """Adds flags for encryption and decryption keys.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Parser passed to surface.
    allow_patch (bool): Adds flags relevant for update operations if true.
    command_only_reads_data (bool): Should be set to true if a command only
        reads data from storage providers (e.g. cat, ls) and false for commands
        that also write data (e.g. cp, rewrite). Hides flags that pertain to
        write operations for read-only commands.
    hidden (bool): Hides encryption flags if true.
  """
  encryption_group = parser.add_group(category='ENCRYPTION', hidden=hidden)
  encryption_group.add_argument(
      '--encryption-key',
      # Flag is hidden for read-only commands and not omitted for parity
      # reasons: gsutil allows supplying decryption keys through the encryption
      # key boto config option, so keeping encryption flags for read-only
      # commands eases translation.
      hidden=hidden or command_only_reads_data,
      help=(
          'The encryption key to use for encrypting target objects. The'
          ' specified encryption key can be a customer-supplied encryption key'
          ' (An RFC 4648 section 4 base64-encoded AES256 string), or a'
          ' customer-managed encryption key of the form `projects/{project}/'
          'locations/{location}/keyRings/{key-ring}/cryptoKeys/{crypto-key}`.'
          ' The specified key also acts as a decryption key, which is useful'
          ' when copying or moving encrypted data to a new location. Using this'
          ' flag in an `objects update` command triggers a rewrite of target'
          ' objects.'
      ),
  )
  encryption_group.add_argument(
      '--decryption-keys',
      type=arg_parsers.ArgList(),
      metavar='DECRYPTION_KEY',
      hidden=hidden,
      help=('A comma-separated list of customer-supplied encryption keys'
            ' (RFC 4648 section 4 base64-encoded AES256 strings) that will'
            ' be used to decrypt Cloud Storage objects. Data encrypted'
            ' with a customer-managed encryption key (CMEK) is decrypted'
            ' automatically, so CMEKs do not need to be listed here.'))
  if allow_patch:
    encryption_group.add_argument(
        '--clear-encryption-key',
        action='store_true',
        hidden=hidden or command_only_reads_data,
        help='Clears the encryption key associated with an object. Using this'
             ' flag triggers a rewrite of affected objects, which are then'
             ' encrypted using the default encryption key set on the bucket,'
             ' if one exists, or else with a Google-managed encryption key.')


def add_continue_on_error_flag(parser):
  """Adds flag to indicate error should be skipped instead of being raised."""
  parser.add_argument(
      '-c',
      '--continue-on-error',
      action='store_true',
      help='If any operations are unsuccessful, the command will exit with'
      ' a non-zero exit status after completing the remaining operations.'
      ' This flag takes effect only in sequential execution mode (i.e.'
      ' processor and thread count are set to 1). Parallelism is default.')


def _get_optional_help_text(require_create_flags, flag_name):
  """Returns a text to be added for create command's help text."""
  optional_text_map = {
      'destination': ' Defaults to <SOURCE_BUCKET_URL>/inventory_reports/.',
      'metadata_fields': ' Defaults to all fields being included.',
      'start_date': ' Defaults to tomorrow.',
      'end_date': ' Defaults to one year from --schedule-starts value.',
      'frequency': ' Defaults to DAILY.'
  }
  return optional_text_map[flag_name] if require_create_flags else ''


class ArgListWithRequiredFieldsCheck(arg_parsers.ArgList):
  """ArgList that raises errror if required fields are not present."""

  def __call__(self, arg_value):
    arglist = super(ArgListWithRequiredFieldsCheck, self).__call__(arg_value)
    missing_required_fields = (
        set(REQUIRED_INVENTORY_REPORTS_METADATA_FIELDS) - set(arglist))
    if missing_required_fields:
      raise arg_parsers.ArgumentTypeError(
          'Fields {} are REQUIRED.'.format(
              ','.join(sorted(missing_required_fields))))
    return arglist


def add_inventory_reports_metadata_fields_flag(parser,
                                               require_create_flags=False):
  """Adds the metadata-fields flag."""
  parser.add_argument(
      '--metadata-fields',
      metavar='METADATA_FIELDS',
      default=(list(ALL_INVENTORY_REPORTS_METADATA_FIELDS)
               if require_create_flags else None),
      type=ArgListWithRequiredFieldsCheck(
          choices=ALL_INVENTORY_REPORTS_METADATA_FIELDS),
      help=(
          'The metadata fields to be included in the inventory '
          'report. The fields: "{}" are REQUIRED. '.format(
              ', '.join(REQUIRED_INVENTORY_REPORTS_METADATA_FIELDS)) +
          _get_optional_help_text(require_create_flags, 'metadata_fields')))


def add_inventory_reports_flags(parser, require_create_flags=False):
  """Adds the flags for the inventory reports create and update commands.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Parser passed to surface.
    require_create_flags (bool): True if create flags should be required.
  """
  report_format_settings = parser.add_group(
      mutex=True,
      help='Report format configuration. Any combination of '
      'CSV flags is valid as long as the Parquet flag is not present.')
  report_format_settings.add_argument(
      '--parquet',
      action='store_true',
      help='Generate reports in parquet format.')
  csv_format_settings = report_format_settings.add_group(
      help='Flags for setting CSV format options.')
  csv_format_settings.add_argument(
      '--csv-separator',
      choices=[r'\n', r'\r\n'],
      type=str,
      metavar='SEPARATOR',
      help='Sets the character used to separate the records in the inventory '
            'report CSV file. For example, ``\\n``')
  csv_format_settings.add_argument(
      '--csv-delimiter',
      type=str,
      metavar='DELIMITER',
      help='Sets the delimiter that separates the fields in the inventory '
            'report CSV file. For example, ``,``')
  csv_format_settings.add_argument(
      '--csv-header',
      action=arg_parsers.StoreTrueFalseAction,
      help='Indicates whether or not headers are included in the inventory '
            'report CSV file. Default is None.')
  parser.add_argument(
      '--destination',
      type=str,
      metavar='DESTINATION_URL',
      help=('Sets the URL of the destination bucket and path where generated '
            'reports are stored.' +
            _get_optional_help_text(require_create_flags, 'destination')))
  parser.add_argument(
      '--display-name',
      type=str,
      help='Sets the editable name of the report configuration.')
  parser.add_argument(
      '--schedule-starts',
      type=arg_parsers.Day.Parse,
      metavar='START_DATE',
      help=('Sets the date you want to start generating inventory reports. '
            'For example, 2022-01-30. Should be tomorrow or later based'
            ' on UTC timezone.' +
            _get_optional_help_text(require_create_flags, 'start_date')))
  parser.add_argument(
      '--schedule-repeats',
      choices=['daily', 'weekly'],
      metavar='FREQUENCY',
      default='daily' if require_create_flags else None,
      type=str,
      help=('Sets how often the inventory report configuration will run.' +
            _get_optional_help_text(require_create_flags, 'frequency')))
  parser.add_argument(
      '--schedule-repeats-until',
      type=arg_parsers.Day.Parse,
      metavar='END_DATE',
      help=(
          'Sets date after which you want to stop generating inventory reports.'
          ' For example, 2022-03-30.'
          + _get_optional_help_text(require_create_flags, 'end_date')))
  if require_create_flags:
    add_inventory_reports_metadata_fields_flag(parser, require_create_flags)


def add_dataset_config_location_flag(parser, is_required=True):
  """Adds the location flag for the dataset-config commands.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Parser passed to surface.
    is_required (bool): True if location flag is a required field.
  """
  parser.add_argument(
      '--location',
      type=str,
      required=is_required,
      help='Provide location of the dataset config.',
  )


def add_dataset_config_create_update_flags(parser, is_update=False):
  """Adds the flags for the dataset-config create and update commands.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Parser passed to surface.
    is_update (bool): True if flags are for the dataset-configs update command.
  """
  parser.add_argument(
      '--retention-period-days',
      type=int,
      metavar='RETENTION_DAYS',
      required=not is_update,
      help='Provide retention period for the config.',
  )
  parser.add_argument(
      '--description',
      type=str,
      help='Description for dataset config.',
  )


def add_raw_display_flag(parser):
  parser.add_argument(
      '--raw',
      action='store_true',
      help=(
          'Shows metadata in the format returned by the API instead of'
          ' standardizing it.'
      ),
  )


def add_admission_policy_flag(parser):
  parser.add_argument(
      '--admission-policy',
      choices=['ADMIT_ON_FIRST_MISS', 'ADMIT_ON_SECOND_MISS'],
      help=(
          'The cache admission policy decides for each cache miss, whether to'
          ' insert the missed block or not.'
      ),
  )


def add_read_paths_from_stdin_flag(
    parser, help_text='Read the list of URLs from stdin.'
):
  parser.add_argument(
      '--read-paths-from-stdin', '-I', action='store_true', help=help_text
  )


def add_per_object_retention_flags(parser, is_update=False):
  """Adds the flags for object retention lock.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Parser passed to surface.
    is_update (bool): True if flags are for the objects update command.
  """
  retention_group = parser.add_group(
      category='RETENTION',
  )
  if is_update:
    subject = 'object'
    retention_group.add_argument(
        '--clear-retention',
        action='store_true',
        help=(
            'Clears object retention settings and unlocks the configuration.'
            ' Requires --override-unlocked-retention flag as confirmation.'
        ),
    )
    retention_group.add_argument(
        '--override-unlocked-retention',
        action='store_true',
        help=(
            'Needed for certain retention configuration modifications, such as'
            ' clearing retention settings and reducing retention time.'
            ' Note that locked configurations cannot be edited even'
            ' with this flag.'
        ),
    )
    override_note = (
        ' Requires --override-unlocked-retention flag to shorten'
        ' the retain-until time in unlocked configurations.'
    )
  else:
    subject = 'destination object'
    override_note = ''

  retention_group.add_argument(
      '--retention-mode',
      choices=sorted([option.value for option in RetentionMode]),
      help=(
          'Sets the {} retention mode to either "Locked" or "Unlocked". When'
          ' retention mode is "Locked", the retain until time can only be'
          ' increased.'.format(subject)
      ),
  )
  retention_group.add_argument(
      '--retain-until',
      type=arg_parsers.Datetime.Parse,
      help=(
          'Ensures the {} is retained until the specified time in RFC 3339'
          ' format.'.format(subject)
          + override_note
      ),
      metavar='DATETIME',
  )


def add_soft_deleted_flag(parser):
  """Adds flag for only displaying soft-deleted objects."""
  parser.add_argument(
      '--soft-deleted',
      action='store_true',
      help=(
          'Displays soft-deleted objects only. Excludes live and noncurrent'
          ' objects.'
      ),
  )


def add_soft_delete_flags(parser):
  """Adds flags related to soft delete feature."""
  add_soft_deleted_flag(parser)
  parser.add_argument(
      '--exhaustive',
      action='store_true',
      help=(
          'For features like soft delete, the API may return an empty list.'
          ' If present, continue querying. This may incur costs from repeated'
          ' LIST calls and may not return any additional objects.'
      ),
  )
  parser.add_argument(
      '--next-page-token',
      help='Page token for resuming LIST calls.',
  )


def add_enable_per_object_retention_flag(parser):
  """Adds flag for enabling object retention for buckets."""
  parser.add_argument(
      '--enable-per-object-retention',
      action='store_true',
      help=(
          'Enables each object in the bucket to have its own retention'
          ' settings, which prevents deletion until stored for a specific'
          ' length of time.'
      ),
  )


def _get_storage_uri(resource):
  storage_url = resource['storage_url']
  if storage_url.startswith('gs://'):
    uri = resources.REGISTRY.Parse(storage_url).SelfLink()
    universe_domain_property = properties.VALUES.core.universe_domain
    if universe_domain_property.IsExplicitlySet():
      uri = uri.replace(universe_domain_property.default,
                        universe_domain_property.Get())
    return uri
  return storage_url


def add_uri_support_to_list_commands(parser):
  parser.display_info.AddUriFunc(_get_storage_uri)


def add_recovery_point_objective_flag(parser):
  """Adds the recovery point objective flag for buckets commands.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Parser passed to surface.
  """
  parser.add_argument(
      '--recovery-point-objective',
      '--rpo',
      choices=sorted([option.value for option in ReplicationStrategy]),
      metavar='SETTING',
      type=str,
      help=('Sets the [recovery point objective](https://cloud.google.com'
            '/architecture/dr-scenarios-planning-guide#basics_of_dr_planning)'
            ' of a bucket. This flag can only be used with multi-region and'
            ' dual-region buckets. `DEFAULT` option is valid for multi-region'
            ' and dual-regions buckets. `ASYNC_TURBO` option is only valid for'
            ' dual-region buckets. If unspecified when the bucket is created,'
            ' it defaults to `DEFAULT` for dual-region and multi-region'
            ' buckets. For more information, see'
            ' [replication in Cloud Storage](https://cloud.google.com/storage'
            '/docs/availability-durability#cross-region-redundancy).'))


def check_if_use_gsutil_style(args):
  """Check if format output using gsutil style.

  Args:
    args (object): User input arguments.

  Returns:
    use_gsutil_style (bool): True if format with gsutil style.
  """
  if args.format:
    if args.format != 'gsutil':
      raise errors.Error(
          'The only valid format value for ls and du is "gsutil" (e.g.'
          ' "--format=gsutil"). See other flags and commands for additional'
          ' formatting options.'
      )
    use_gsutil_style = True
    # Prevents validation errors in resource_printer.py.
    args.format = None
  else:
    use_gsutil_style = properties.VALUES.storage.run_by_gsutil_shim.GetBool()
  return use_gsutil_style
