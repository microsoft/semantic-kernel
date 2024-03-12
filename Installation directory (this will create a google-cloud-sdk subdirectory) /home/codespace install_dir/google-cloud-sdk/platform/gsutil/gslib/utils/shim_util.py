# -*- coding: utf-8 -*-
# Copyright 2021 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helper for shim used to translate gsutil command to gcloud storage."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import collections
import enum
import os
import re
import subprocess

from boto import config
from gslib import exception
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.utils import boto_util
from gslib.utils import constants
from gslib.utils import system_util


class HIDDEN_SHIM_MODE(enum.Enum):
  NO_FALLBACK = 'no_fallback'
  DRY_RUN = 'dry_run'
  NONE = 'none'


class RepeatFlagType(enum.Enum):
  LIST = 0
  DICT = 1


DECRYPTION_KEY_REGEX = re.compile(r'^decryption_key([1-9]$|[1-9][0-9]$|100$)')

# Required for headers translation and boto config translation.
COMMANDS_SUPPORTING_ALL_HEADERS = frozenset(['cp', 'mv', 'rsync', 'setmeta'])
ENCRYPTION_SUPPORTED_COMMANDS = COMMANDS_SUPPORTING_ALL_HEADERS | frozenset(
    ['ls', 'rewrite', 'stat', 'cat', 'compose'])
PRECONDITONS_ONLY_SUPPORTED_COMMANDS = frozenset(
    ['compose', 'rewrite', 'rm', 'retention'])
DATA_TRANSFER_HEADERS = frozenset([
    'cache-control',
    'content-disposition',
    'content-encoding',
    'content-md5',
    'content-language',
    'content-type',
    'custom-time',
])
PRECONDITIONS_HEADERS = frozenset([
    'x-goog-generation-match', 'x-goog-if-generation-match',
    'x-goog-metageneration-match', 'x-goog-if-metageneration-match'
])

# The format for _BOTO_CONFIG_MAP is as follows:
# {
#   'Boto section name': {
#     'boto field name': 'correspnding env variable name in Cloud SDK'
#   }
# }
_BOTO_CONFIG_MAP = {
    'Credentials': {
        'aws_access_key_id':
            'AWS_ACCESS_KEY_ID',
        'aws_secret_access_key':
            'AWS_SECRET_ACCESS_KEY',
        'gs_access_key_id':
            'CLOUDSDK_STORAGE_GS_XML_ACCESS_KEY_ID',
        'gs_secret_access_key':
            'CLOUDSDK_STORAGE_GS_XML_SECRET_ACCESS_KEY',
        'use_client_certificate':
            'CLOUDSDK_CONTEXT_AWARE_USE_CLIENT_CERTIFICATE',
    },
    'Boto': {
        'proxy': 'CLOUDSDK_PROXY_ADDRESS',
        'proxy_type': 'CLOUDSDK_PROXY_TYPE',
        'proxy_port': 'CLOUDSDK_PROXY_PORT',
        'proxy_user': 'CLOUDSDK_PROXY_USERNAME',
        'proxy_pass': 'CLOUDSDK_PROXY_PASSWORD',
        'proxy_rdns': 'CLOUDSDK_PROXY_RDNS',
        'http_socket_timeout': 'CLOUDSDK_CORE_HTTP_TIMEOUT',
        'ca_certificates_file': 'CLOUDSDK_CORE_CUSTOM_CA_CERTS_FILE',
        'max_retry_delay': 'CLOUDSDK_STORAGE_BASE_RETRY_DELAY',
        'num_retries': 'CLOUDSDK_STORAGE_MAX_RETRIES',
    },
    'GSUtil': {
        'check_hashes':
            'CLOUDSDK_STORAGE_CHECK_HASHES',
        'default_project_id':
            'CLOUDSDK_CORE_PROJECT',
        'disable_analytics_prompt':
            'CLOUDSDK_CORE_DISABLE_USAGE_REPORTING',
        'use_magicfile':
            'CLOUDSDK_STORAGE_USE_MAGICFILE',
        'parallel_composite_upload_threshold':
            'CLOUDSDK_STORAGE_PARALLEL_COMPOSITE_UPLOAD_THRESHOLD',
        'resumable_threshold':
            'CLOUDSDK_STORAGE_RESUMABLE_THRESHOLD',
        'rsync_buffer_lines':
            'CLOUDSDK_STORAGE_RSYNC_LIST_CHUNK_SIZE',
    },
    'OAuth2': {
        'client_id': 'CLOUDSDK_AUTH_CLIENT_ID',
        'client_secret': 'CLOUDSDK_AUTH_CLIENT_SECRET',
        'provider_authorization_uri': 'CLOUDSDK_AUTH_AUTH_HOST',
        'provider_token_uri': 'CLOUDSDK_AUTH_TOKEN_HOST',
    },
}

_REQUIRED_BOTO_CONFIG_NOT_YET_SUPPORTED = frozenset(
    # TOTO(b/214245419) Remove this once STET is support and add equivalent
    # mapping above.
    ['stet_binary_path', 'stet_config_path'])


def get_flag_from_header(raw_header_key, header_value, unset=False):
  """Returns the gcloud storage flag for the given gsutil header.

  Args:
    raw_header_key: The header key.
    header_value: The header value
    unset: If True, the equivalent clear/remove flag is returned instead of the
      setter flag. This only applies to setmeta.

  Returns:
    A string representing the equivalent gcloud storage flag and value, if
      translation is possible, else returns None.

  Examples:
    >> get_flag_from_header('Cache-Control', 'val')
    --cache-control=val

    >> get_flag_from_header('x-goog-meta-foo', 'val')
    --update-custom-metadata=foo=val

    >> get_flag_from_header('x-goog-meta-foo', 'val', unset=True)
    --remove-custom-metadata=foo

  """
  lowercase_header_key = raw_header_key.lower()
  if lowercase_header_key in PRECONDITIONS_HEADERS:
    providerless_flag = raw_header_key[len('x-goog-'):]
    if not providerless_flag.startswith('if-'):
      flag_name = 'if-' + providerless_flag
    else:
      flag_name = providerless_flag
  elif lowercase_header_key in DATA_TRANSFER_HEADERS:
    flag_name = lowercase_header_key
  else:
    flag_name = None

  if flag_name is not None:
    if unset:
      if lowercase_header_key in PRECONDITIONS_HEADERS or lowercase_header_key == 'content-md5':
        # Precondition headers and content-md5 cannot be cleared.
        return None
      else:
        return '--clear-' + flag_name
    return '--{}={}'.format(flag_name, header_value)

  for header_prefix in ('x-goog-meta-', 'x-amz-meta-'):
    if lowercase_header_key.startswith(header_prefix):
      # Preserving raw header keys to avoid forcing lowercase on custom data.
      metadata_key = raw_header_key[len(header_prefix):]
      if unset:
        return '--remove-custom-metadata=' + metadata_key
      else:
        return '--update-custom-metadata={}={}'.format(metadata_key,
                                                       header_value)

  return None


def get_format_flag_caret():
  if system_util.IS_WINDOWS:
    return '^^^^'
  return '^'


def get_format_flag_newline():
  if system_util.IS_WINDOWS:
    return '^\\^n'
  return '\n'


class GcloudStorageFlag(object):

  def __init__(self,
               gcloud_flag,
               repeat_type=None,
               supports_output_translation=False):
    """Initializes GcloudStorageFlag.

    Args:
      gcloud_flag (str|dict): The name of the gcloud flag or a dictionary for
        when the gcloud flag depends on a gsutil value.
        gsutil "--pap off" -> gcloud "--no-public-access-prevention"
      repeat_type (RepeatFlagType|None): Gsutil sometimes handles list
        and dictionary inputs by accepting a flag multiple times.
      support_output_translation (bool): If True, this flag in gcloud storage
        supports printing gsutil formatted output.
    """
    self.gcloud_flag = gcloud_flag
    self.repeat_type = repeat_type
    self.supports_output_translation = supports_output_translation


class GcloudStorageMap(object):
  """Mapping to translate gsutil command to its gcloud storage equivalent."""

  def __init__(self,
               gcloud_command,
               flag_map,
               supports_output_translation=False):
    """Intalizes GcloudStorageMap.

    Args:
      gcloud_command (dict|str): The corresponding name of the command to be
        called in gcloud. If this command supports sub-commands, then this
        field must be a dict of sub-command-name:GcloudStorageMap pairs.
      flag_map (dict): A dict of str to GcloudStorageFlag. Mapping of gsutil
        flags to their equivalent gcloud storage flag names.
      supports_output_translation (bool): Indicates if the corresponding
        gcloud storage command supports the printing gsutil formatted output.
    """
    self.gcloud_command = gcloud_command
    self.flag_map = flag_map
    self.supports_output_translation = supports_output_translation


def _get_gcloud_binary_path(cloudsdk_root):
  return os.path.join(cloudsdk_root, 'bin',
                      'gcloud.cmd' if system_util.IS_WINDOWS else 'gcloud')


def _get_validated_gcloud_binary_path():
  # GCLOUD_BINARY_PATH is used for testing purpose only.
  # It helps to run the parity_check.py script directly without having
  # to build gcloud.
  gcloud_binary_path = os.environ.get('GCLOUD_BINARY_PATH')
  if gcloud_binary_path:
    return gcloud_binary_path

  cloudsdk_root = os.environ.get('CLOUDSDK_ROOT_DIR')
  if cloudsdk_root is None:
    raise exception.GcloudStorageTranslationError(
        'Requested to use "gcloud storage" but the gcloud binary path cannot'
        ' be found. This might happen if you attempt to use gsutil that was'
        ' not installed via Cloud SDK. You can manually set the'
        ' `CLOUDSDK_ROOT_DIR` environment variable to point to the'
        ' google-cloud-sdk installation directory to resolve the issue.'
        ' Alternatively, you can set `use_gcloud_storage=False` to disable'
        ' running the command using gcloud storage.')
  return _get_gcloud_binary_path(cloudsdk_root)


def _get_gcs_json_endpoint_from_boto_config(config):
  gs_json_host = config.get('Credentials', 'gs_json_host')
  if gs_json_host:
    gs_json_port = config.get('Credentials', 'gs_json_port')
    port = ':' + gs_json_port if gs_json_port else ''
    json_api_version = config.get('Credentials', 'json_api_version', 'v1')
    return 'https://{}{}/storage/{}'.format(gs_json_host, port,
                                            json_api_version)
  return None


def _get_s3_endpoint_from_boto_config(config):
  s3_host = config.get('Credentials', 's3_host')
  if s3_host:
    s3_port = config.get('Credentials', 's3_port')
    port = ':' + s3_port if s3_port else ''
    return 'https://{}{}'.format(s3_host, port)
  return None


def _convert_args_to_gcloud_values(args, gcloud_storage_map):
  gcloud_args = []
  repeat_flag_data = collections.defaultdict(list)
  i = 0
  while i < len(args):
    if args[i] not in gcloud_storage_map.flag_map:
      # Add raw value (positional args and flag values for non-repeated flags).
      gcloud_args.append(args[i])
      i += 1
      continue

    gcloud_flag_object = gcloud_storage_map.flag_map[args[i]]
    if not gcloud_flag_object:
      # Flag asked to be skipped over.
      i += 1
    elif gcloud_flag_object.repeat_type:
      # Capture "v1" and "v2" in ["-k", "v1", "-k", "v2"].
      repeat_flag_data[gcloud_flag_object].append(args[i + 1])
      i += 2
    elif isinstance(gcloud_flag_object.gcloud_flag, str):
      # Simple translation.
      # gsutil: "-x" -> gcloud: "-y"
      gcloud_args.append(gcloud_flag_object.gcloud_flag)
      i += 1
    else:  # isinstance(gcloud_flag_object.gcloud_flag, dict)
      # gsutil: "--pap on" -> gcloud: "--pap"
      # gsutil: "--pap off" -> gcloud: "--no-pap"
      if args[i + 1] not in gcloud_flag_object.gcloud_flag:
        raise ValueError(
            'Flag value not in translation map for "{}": {}'.format(
                args[i], args[i + 1]))
      translated_flag_and_value = gcloud_flag_object.gcloud_flag[args[i + 1]]
      if translated_flag_and_value:
        gcloud_args.append(translated_flag_and_value)
      i += 2

  for gcloud_flag_object, values in repeat_flag_data.items():
    if gcloud_flag_object.repeat_type is RepeatFlagType.LIST:
      # gsutil: "-k v1 -k v2" -> gcloud: "-k=v1,v2"
      condensed_flag_values = ','.join(values)
    elif gcloud_flag_object.repeat_type is RepeatFlagType.DICT:
      # gcloud: "-d k1:v1 -d k2:v2" -> gcloud: "-d=k1=v1,k2=v2"
      condensed_flag_values = ','.join(
          ['{}={}'.format(*s.split(':', 1)) for s in values])
    else:
      raise ValueError('Shim cannot handle repeat flag type: {}'.format(
          repeat_flag_data.repeat_type))
    gcloud_args.append('{}={}'.format(gcloud_flag_object.gcloud_flag,
                                      condensed_flag_values))

  return gcloud_args


class GcloudStorageCommandMixin(object):
  """Provides gcloud storage translation functionality.

  The command.Command class must inherit this class in order to support
  converting the gsutil command to it's gcloud storage equivalent.
  """
  # Mapping for translating gsutil command to gcloud storage.
  gcloud_storage_map = None

  def __init__(self):
    self._translated_gcloud_storage_command = None
    self._translated_env_variables = None

  def _get_gcloud_storage_args(self, sub_opts, gsutil_args, gcloud_storage_map):
    if gcloud_storage_map is None:
      raise exception.GcloudStorageTranslationError(
          'Command "{}" cannot be translated to gcloud storage because the'
          ' translation mapping is missing.'.format(self.command_name))
    args = []
    if isinstance(gcloud_storage_map.gcloud_command, list):
      args.extend(gcloud_storage_map.gcloud_command)
    elif isinstance(gcloud_storage_map.gcloud_command, dict):
      # If a command has sub-commands, e.g gsutil pap set, gsutil pap get.
      # All the flags mapping must be present in the subcommand's map
      # because gsutil does not have command specific flags
      # if sub-commands are present.
      if gcloud_storage_map.flag_map:
        raise ValueError(
            'Flags mapping should not be present at the top-level command if '
            'a sub-command is used. Command: {}.'.format(self.command_name))
      sub_command = gsutil_args[0]
      sub_opts, parsed_args = self.ParseSubOpts(
          args=gsutil_args[1:], should_update_sub_opts_and_args=False)
      return self._get_gcloud_storage_args(
          sub_opts, parsed_args,
          gcloud_storage_map.gcloud_command.get(sub_command))
    else:
      raise ValueError('Incorrect mapping found for "{}" command'.format(
          self.command_name))

    if sub_opts:
      for option, value in sub_opts:
        if option not in gcloud_storage_map.flag_map:
          raise exception.GcloudStorageTranslationError(
              'Command option "{}" cannot be translated to'
              ' gcloud storage'.format(option))
        else:
          args.append(option)
          if value != '':
            # Empty string represents that the user did not passed in a value
            # for the flag.
            args.append(value)

    return _convert_args_to_gcloud_values(args + gsutil_args,
                                          gcloud_storage_map)

  def _translate_top_level_flags(self):
    """Translates gsutil's top level flags.

    Gsutil specifies the headers (-h) and boto config (-o) as top level flags
    as well, but we handle those separately.

    Returns:
      A tuple. The first item is a list of top level flags that can be appended
        to the gcloud storage command. The second item is a dict of environment
        variables that can be set for the gcloud storage command execution.
    """
    top_level_flags = []
    env_variables = {
        'CLOUDSDK_METRICS_ENVIRONMENT': 'gsutil_shim',
        'CLOUDSDK_STORAGE_RUN_BY_GSUTIL_SHIM': 'True'
    }
    if self.debug >= 3:
      top_level_flags.extend(['--verbosity', 'debug'])
    if self.debug == 4:
      top_level_flags.append('--log-http')
    if self.quiet_mode:
      top_level_flags.append('--no-user-output-enabled')
    if self.user_project:
      top_level_flags.append('--billing-project=' + self.user_project)
    if self.trace_token:
      top_level_flags.append('--trace-token=' + self.trace_token)
    if constants.IMPERSONATE_SERVICE_ACCOUNT:
      top_level_flags.append('--impersonate-service-account=' +
                             constants.IMPERSONATE_SERVICE_ACCOUNT)
    # TODO(b/208294509) Add --perf-trace-token translation.
    should_use_rsync_override = self.command_name == 'rsync' and not (
        config.get('GSUtil', 'parallel_process_count') == '1' and
        config.get('GSUtil', 'thread_process_count') == '1')
    if not (self.parallel_operations or should_use_rsync_override):
      # TODO(b/208301084) Set the --sequential flag instead.
      env_variables['CLOUDSDK_STORAGE_THREAD_COUNT'] = '1'
      env_variables['CLOUDSDK_STORAGE_PROCESS_COUNT'] = '1'
    return top_level_flags, env_variables

  def _translate_headers(self, headers=None, unset=False):
    """Translates gsutil headers to equivalent gcloud storage flags.

    Args:
      headers (dict|None): If absent, extracts headers from command instance.
      unset (bool): Yield metadata clear flags instead of setter flags.

    Returns:
      List[str]: Translated flags for gcloud.

    Raises:
      GcloudStorageTranslationError: Could not translate flag.
    """
    flags = []
    # Accept custom headers or extract headers dict from Command class.
    headers_to_translate = headers if headers is not None else self.headers
    additional_headers = []
    for raw_header_key, header_value in headers_to_translate.items():
      lowercase_header_key = raw_header_key.lower()
      if lowercase_header_key == 'x-goog-api-version':
        # Gsutil adds this header. We don't have to translate it for gcloud.
        continue
      flag = get_flag_from_header(raw_header_key, header_value, unset=unset)
      if self.command_name in COMMANDS_SUPPORTING_ALL_HEADERS:
        if flag:
          flags.append(flag)
      elif (self.command_name in PRECONDITONS_ONLY_SUPPORTED_COMMANDS and
            lowercase_header_key in PRECONDITIONS_HEADERS):
        flags.append(flag)
      if not flag:
        self.logger.warn('Header {}:{} cannot be translated to a gcloud storage'
                         ' equivalent flag. It is being treated as an arbitrary'
                         ' request header.'.format(raw_header_key,
                                                   header_value))
        additional_headers.append('{}={}'.format(raw_header_key, header_value))
    if additional_headers:
      flags.append('--additional-headers=' + ','.join(additional_headers))
    return flags

  def _translate_boto_config(self):
    """Translates boto config options to gcloud storage properties.

    Returns:
      A tuple where first element is a list of flags and the second element is
      a dict representing the env variables that can be set to set the
      gcloud storage properties.
    """
    flags = []
    env_vars = {}
    # Handle gs_json_host and gs_json_port.
    gcs_json_endpoint = _get_gcs_json_endpoint_from_boto_config(config)
    if gcs_json_endpoint:
      env_vars['CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE'] = gcs_json_endpoint
    # Handle s3_host and s3_port.
    s3_endpoint = _get_s3_endpoint_from_boto_config(config)
    if s3_endpoint:
      env_vars['CLOUDSDK_STORAGE_S3_ENDPOINT_URL'] = s3_endpoint

    decryption_keys = []
    for section_name, section in config.items():
      for key, value in section.items():
        if (key == 'encryption_key' and
            self.command_name in ENCRYPTION_SUPPORTED_COMMANDS):
          flags.append('--encryption-key=' + value)
        # Boto config can have decryption keys in the form of
        # decryption_key1..100.
        elif (DECRYPTION_KEY_REGEX.match(key) and
              self.command_name in ENCRYPTION_SUPPORTED_COMMANDS):
          decryption_keys.append(value)
        elif (key == 'content_language' and
              self.command_name in COMMANDS_SUPPORTING_ALL_HEADERS):
          flags.append('--content-language=' + value)
        elif key in _REQUIRED_BOTO_CONFIG_NOT_YET_SUPPORTED:
          self.logger.error('The boto config field {}:{} cannot be translated'
                            ' to gcloud storage equivalent.'.format(
                                section_name, key))
        elif key == 'https_validate_certificates' and not value:
          env_vars['CLOUDSDK_AUTH_DISABLE_SSL_VALIDATION'] = True
        # Skip mapping GS HMAC auth keys if gsutil wouldn't use them.
        elif (key in ('gs_access_key_id', 'gs_secret_access_key') and
              not boto_util.UsingGsHmac()):
          self.logger.debug('The boto config field {}:{} skipped translation'
                            ' to the gcloud storage equivalent as it would'
                            ' have been unused in gsutil.'.format(
                                section_name, key))
        else:
          env_var = _BOTO_CONFIG_MAP.get(section_name, {}).get(key, None)
          if env_var is not None:
            env_vars[env_var] = value
    if decryption_keys:
      flags.append('--decryption-keys=' + ','.join(decryption_keys))
    return flags, env_vars

  def get_gcloud_storage_args(self, gcloud_storage_map=None):
    """Translates the gsutil command flags to gcloud storage flags.

    It uses the command_spec.gcloud_storage_map field that provides the
    translation mapping for all the flags.

    Args:
      gcloud_storage_map (GcloudStorageMap|None): Command surface may pass a
        custom translation map instead of using the default class constant.
        Useful for when translations change based on conditional logic.


    Returns:
      A list of all the options and arguments that can be used with the
        equivalent gcloud storage command.
    Raises:
      GcloudStorageTranslationError: If a flag or command cannot be translated.
      ValueError: If there is any issue with the mapping provided by
        GcloudStorageMap.
    """
    return self._get_gcloud_storage_args(
        self.sub_opts, self.args, gcloud_storage_map or self.gcloud_storage_map)

  def _print_gcloud_storage_command_info(self,
                                         gcloud_command,
                                         env_variables,
                                         dry_run=False):
    logger_func = self.logger.info if dry_run else self.logger.debug
    logger_func('Gcloud Storage Command: {}'.format(' '.join(gcloud_command)))
    if env_variables:
      logger_func('Environment variables for Gcloud Storage:')
      for k, v in env_variables.items():
        logger_func('%s=%s', k, v)

  def _get_full_gcloud_storage_execution_information(self, args):
    top_level_flags, env_variables = self._translate_top_level_flags()
    header_flags = self._translate_headers()

    flags_from_boto, env_vars_from_boto = self._translate_boto_config()
    env_variables.update(env_vars_from_boto)

    gcloud_binary_path = _get_validated_gcloud_binary_path()
    gcloud_storage_command = ([gcloud_binary_path] + args + top_level_flags +
                              header_flags + flags_from_boto)
    return env_variables, gcloud_storage_command

  def translate_to_gcloud_storage_if_requested(self):
    """Translates the gsutil command to gcloud storage equivalent.

    The translated commands get stored at
    self._translated_gcloud_storage_command.
    This command also translate the boto config, which gets stored as a dict
    at self._translated_env_variables

    Returns:
      True if the command was successfully translated, else False.
    """
    if self.command_name == 'version' or self.command_name == 'test':
      # Running any command in debug mode will lead to calling gsutil version
      # command. We don't want to translate the version command as this
      # should always reflect the version that gsutil is using.

      # We don't want to run any translation for the "test" command.
      return False
    use_gcloud_storage = config.getbool('GSUtil', 'use_gcloud_storage', False)
    try:
      hidden_shim_mode = HIDDEN_SHIM_MODE(
          config.get('GSUtil', 'hidden_shim_mode', 'none'))
    except ValueError:
      raise exception.CommandException(
          'Invalid option specified for'
          ' GSUtil:hidden_shim_mode config setting. Should be one of: {}'.
          format(' | '.join([x.value for x in HIDDEN_SHIM_MODE])))
    if use_gcloud_storage:
      try:
        env_variables, gcloud_storage_command = self._get_full_gcloud_storage_execution_information(
            self.get_gcloud_storage_args())
        if hidden_shim_mode == HIDDEN_SHIM_MODE.DRY_RUN:
          self._print_gcloud_storage_command_info(gcloud_storage_command,
                                                  env_variables,
                                                  dry_run=True)
        elif not os.environ.get('CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL'):
          raise exception.GcloudStorageTranslationError(
              'Requested to use "gcloud storage" but gsutil is not using the'
              ' same credentials as gcloud.'
              ' You can make gsutil use the same credentials by running:\n'
              '{} config set pass_credentials_to_gsutil True'.format(
                  _get_validated_gcloud_binary_path()))
        elif (boto_util.UsingGsHmac() and
              ApiSelector.XML not in self.command_spec.gs_api_support):
          raise CommandException(
              'Requested to use "gcloud storage" with Cloud Storage XML API'
              ' HMAC credentials but the "{}" command can only be used'
              ' with the Cloud Storage JSON API.'.format(self.command_name))
        else:
          self._print_gcloud_storage_command_info(gcloud_storage_command,
                                                  env_variables)
          self._translated_gcloud_storage_command = gcloud_storage_command
          self._translated_env_variables = env_variables
          return True
      except exception.GcloudStorageTranslationError as e:
        # Raise error if no_fallback mode has been requested. This mode
        # should only be used for debuggling and testing purposes.
        if hidden_shim_mode == HIDDEN_SHIM_MODE.NO_FALLBACK:
          raise exception.CommandException(e)
        # For all other cases, we want to run gsutil.
        self.logger.error(
            'Cannot translate gsutil command to gcloud storage.'
            ' Going to run gsutil command. Error: %s', e)
    return False

  def _get_shim_command_environment_variables(self):
    subprocess_envs = os.environ.copy()
    subprocess_envs.update(self._translated_env_variables)
    return subprocess_envs

  def run_gcloud_storage(self):
    process = subprocess.run(self._translated_gcloud_storage_command,
                             env=self._get_shim_command_environment_variables())
    return process.returncode
