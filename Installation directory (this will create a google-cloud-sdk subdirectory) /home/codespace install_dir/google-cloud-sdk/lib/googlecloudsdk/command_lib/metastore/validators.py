# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Resource parsing helpers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from typing import Any

from googlecloudsdk.calliope import exceptions

STRING_MAX_LENGTH = 1000
METASTORE_TYPE_DICT = {
    'dpms': 'DATAPROC_METASTORE',
    'dataplex': 'DATAPLEX',
    'bigquery': 'BIGQUERY',
}
METASTORE_RESOURCE_PATH_DICT = {'dpms': 'services', 'dataplex': 'lakes'}


def ValidatePort(port):
  """Python hook to validate that the port is between 1024 and 65535, inclusive."""
  if port < 1024 or port > 65535:
    raise exceptions.BadArgumentException(
        '--port', 'Port ({0}) is not in the range [1025, 65535].'.format(port)
    )
  return port


def ValidateScalingFactor(scaling_factor):
  """Python hook to validate the scaling factor."""
  if scaling_factor < 0.1 or scaling_factor > 6:
    raise exceptions.BadArgumentException(
        '--scaling-factor',
        'Scaling factor ({0}) is not in the range [0.1, 6.0].'.format(
            scaling_factor
        ),
    )
  elif scaling_factor < 1 and scaling_factor * 10 % 1 != 0:
    raise exceptions.BadArgumentException(
        '--scaling-factor',
        'Scaling factor less than 1.0 ({0}) should be a'
        ' multiple of 0.1 (e.g. (0.1, 0.2, 0.3))'.format(scaling_factor),
    )
  elif scaling_factor >= 1 and scaling_factor % 1.0 != 0:
    raise exceptions.BadArgumentException(
        '--scaling-factor',
        'Scaling greater than 1.0 ({0}) should be a multiple'
        ' of 1.0 (e.g. (1.0, 2.0, 3.0))'.format(scaling_factor),
    )
  return scaling_factor


def ValidateGcsUri(arg_name):
  """Validates the gcs uri is formatted correctly."""

  def Process(gcs_uri):
    if not gcs_uri.startswith('gs://'):
      raise exceptions.BadArgumentException(
          arg_name, 'Expected URI {0} to start with `gs://`.'.format(gcs_uri)
      )
    return gcs_uri

  return Process


def ValidateKerberosPrincipal(kerberos_principal):
  pattern = re.compile(r'^(.+)/(.+)@(.+)$')
  if not pattern.match(kerberos_principal):
    raise exceptions.BadArgumentException(
        '--kerberos-principal',
        'Kerberos Principal {0} does not match ReGeX {1}.'.format(
            kerberos_principal, pattern
        ),
    )
  return kerberos_principal


def ValidateHourOfDay(hour):
  """Validates that the hour falls between 0 and 23, inclusive."""
  if hour < 0 or hour > 23:
    raise exceptions.BadArgumentException(
        '--maintenance-window-hour-of-day',
        'Hour of day ({0}) is not in [0, 23].'.format(hour),
    )
  return hour


def ValidateStringField(arg_name):
  """Validates that the string field is not longer than STRING_MAX_LENGTH, to avoid abuse issues."""
  if len(arg_name) > STRING_MAX_LENGTH:
    raise exceptions.BadArgumentException(
        arg_name,
        'The string field can not be longer than {0} characters.'.format(
            STRING_MAX_LENGTH
        ),
    )
  return arg_name


def ValidateServiceMutexConfig(unused_ref, unused_args, req):
  """Validates that the mutual exclusive configurations of Dataproc Metastore service are not set at the same time.

  Args:
    req: A request with `service` field.

  Returns:
    A request without service mutex configuration conflicts.
  Raises:
    BadArgumentException: when mutual exclusive configurations of service are
    set at the same time.
  """
  if (
      req.service.encryptionConfig
      and req.service.encryptionConfig.kmsKey
      and req.service.metadataIntegration.dataCatalogConfig.enabled
  ):
    raise exceptions.BadArgumentException(
        '--data-catalog-sync',
        'Data Catalog synchronization cannot be used in conjunction with'
        ' customer-managed encryption keys.',
    )

  return ValidateServiceMutexConfigForV1(unused_ref, unused_args, req)


def ValidateServiceMutexConfigForV1(unused_ref, unused_args, req):
  """Validates exclusively for V1 fields that the mutual exclusive configurations of Dataproc Metastore service are not set at the same time.

  Args:
    req: A request with `service` field.

  Returns:
    A request without service mutex configuration conflicts.
  Raises:
    BadArgumentException: when mutual exclusive configurations of service are
    set at the same time.
  """
  if (
      req.service.hiveMetastoreConfig
      and req.service.hiveMetastoreConfig.kerberosConfig
      and req.service.hiveMetastoreConfig.kerberosConfig.principal
      and _IsNetworkConfigPresentInService(req.service)
  ):
    raise exceptions.BadArgumentException(
        '--kerberos-principal',
        'Kerberos configuration cannot be used in conjunction with'
        ' --network-config-from-file or --consumer-subnetworks.',
    )
  if (
      req.service.encryptionConfig
      and req.service.encryptionConfig.kmsKey
      and req.service.metadataIntegration.dataCatalogConfig.enabled
  ):
    raise exceptions.BadArgumentException(
        '--data-catalog-sync',
        'Data Catalog synchronization cannot be used in conjunction with'
        ' customer-managed encryption keys.',
    )
  return req


def ValidateScheduledBackupConfigs(unused_ref, args, req):
  """Validates that the cron_schedule and backup_location are set when the scheduled backup is enabled.

  Args:
    unused_ref: A resource ref to the parsed metastore service resource.
    args: The parsed args namespace from CLI.
    req: A request with `service` field.

  Returns:
    A request with service scheduled backups configurations required.
  Raises:
    BadArgumentException: when cron_schedule and backup_location are not set
    when the scheduled backup is enabled.
  """

  args_set = set(args.GetSpecifiedArgNames())
  if (
      req.service.scheduledBackup.enabled
      and '--scheduled-backup-cron' not in args_set
  ):
    raise exceptions.BadArgumentException(
        '--scheduled-backup-cron',
        '--scheduled-backup-cron must be set when the scheduled backup is'
        ' enabled.',
    )
  if (
      req.service.scheduledBackup.enabled
      and '--scheduled-backup-location' not in args_set
  ):
    raise exceptions.BadArgumentException(
        '--scheduled-backup-location',
        '--scheduled-backup-location must be set when the scheduled backup is'
        ' enabled.',
    )
  return req


def _IsNetworkConfigPresentInService(service):
  return service.networkConfig and service.networkConfig.consumers


def ValidateClearBackends(unused_ref, args, update_federation_req):
  """Validate if users run update federation command with --clear-backends arg only.

  Args:
    unused_ref: A resource ref to the parsed Federation resource.
    args: The parsed args namespace from CLI.
    update_federation_req: The request for the API call.

  Returns:
    String request
  Raises:
    BadArgumentException: When users run update federation command with
    --clear-backends arg only.
  """

  args_set = set(args.GetSpecifiedArgNames())
  if '--clear-backends' in args_set and '--update-backends' not in args_set:
    raise exceptions.BadArgumentException(
        '--clear-backends',
        '--clear-backends must be used with --update-backends',
    )
  return update_federation_req


def _IsZeroOrPositiveNumber(string):
  if string.isdigit():
    return int(string) >= 0
  return False


def _GetMetastoreTypeFromDict(dictionary):
  return '|'.join(value for key, value in dictionary.items())


def _GenerateShortOrLongBackendNames(metastore_type_and_name):
  """Validate and process the format of short and long names for backends.

  Args:
    metastore_type_and_name: Metastore type and name.

  Returns:
    String backend name.

  Raises:
    BadArgumentException: When the input backend(s) are invalid
  """

  if metastore_type_and_name[0].lower() == 'bigquery':
    long_name_regex = r'^projects\/.*[^\/]'
  else:
    long_name_regex = (
        r'^projects\/.*[^\/]\/locations\/.[^\/]*\/('
        + _GetMetastoreTypeFromDict(METASTORE_RESOURCE_PATH_DICT)
        + r')\/.[^\/]*$'
    )
  if '/' in metastore_type_and_name[1]:
    if re.search(long_name_regex, metastore_type_and_name[1]):
      return metastore_type_and_name[1]
    else:
      raise exceptions.BadArgumentException(
          '--backends', 'Invalid backends format'
      )
  else:
    if metastore_type_and_name[0].lower() == 'bigquery':
      return 'projects/' + metastore_type_and_name[1]
    else:
      return (
          '{0}/'
          + METASTORE_RESOURCE_PATH_DICT[metastore_type_and_name[0]]
          + '/'
          + metastore_type_and_name[1]
      )


def ValidateBackendsAndReturnMetastoreDict(backends):
  """Validate backends argument if it has correct format, metastore type and the keys are positive number and not duplicated.

  In addition, parsing the backends to backend metastore dict

  Args:
    backends: A string is passed by user in format
      <key>=<metastore_type>:<name>,... For example:
      1=dpms:dpms1,2=dataplex:lake1

  Returns:
    Backend metastore dict
  Raises:
    BadArgumentException: When the input backends is invalid or duplicated keys
  """
  backend_dict = {}

  if not backends:
    raise exceptions.BadArgumentException('--backends', 'Cannot be empty')
  backend = backends.split(',')
  for data in backend:
    rank_and_metastore = data.split('=')
    if len(rank_and_metastore) != 2:
      raise exceptions.BadArgumentException(
          '--backends', 'Invalid backends format'
      )
    key = rank_and_metastore[0]
    if not _IsZeroOrPositiveNumber(key):
      raise exceptions.BadArgumentException(
          '--backends',
          'Invalid backends format or key of backend is less than 0',
      )
    value = rank_and_metastore[1]
    metastore_type_and_name = value.split(':')
    if len(metastore_type_and_name) != 2:
      raise exceptions.BadArgumentException(
          '--backends', 'Invalid backends format'
      )
    if key in backend_dict:
      raise exceptions.BadArgumentException(
          '--backends', 'Duplicated keys of backends'
      )
    if metastore_type_and_name[0] not in METASTORE_TYPE_DICT.keys():
      raise exceptions.BadArgumentException(
          '--backends', 'Invalid backends type'
      )
    generated_name = _GenerateShortOrLongBackendNames(metastore_type_and_name)
    backend_metastores_dict = {
        'name': generated_name,
        'metastoreType': METASTORE_TYPE_DICT[metastore_type_and_name[0]],
    }
    backend_dict[key] = backend_metastores_dict
  return backend_dict


def ParseBackendsIntoRequest(job_ref, request):
  """Generate the long backend name of Dataproc Metastore federation requests.

  Args:
    job_ref: A resource ref to the parsed Federation resource.
    request: The request for the API call.

  Returns:
    Modified request for the API call.
  """

  for prop in request.federation.backendMetastores.additionalProperties:
    prop.value.name = prop.value.name.format(job_ref.Parent().RelativeName())
  return request
