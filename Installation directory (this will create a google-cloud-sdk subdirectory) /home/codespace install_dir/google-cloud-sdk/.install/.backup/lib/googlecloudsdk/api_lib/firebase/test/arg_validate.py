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

"""A shared library to validate 'gcloud test' CLI argument values."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import posixpath
import random
import re
import string
import sys

from googlecloudsdk.api_lib.firebase.test import exceptions as test_exceptions
from googlecloudsdk.api_lib.firebase.test import util as util
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import files
import six


def ValidateArgFromFile(arg_internal_name, arg_value):
  """Do checks/mutations on arg values parsed from YAML which need validation.

  Any arg not appearing in the _FILE_ARG_VALIDATORS dictionary is assumed to be
  a simple string to be validated by the default _ValidateString() function.

  Mutations of the args are done in limited cases to improve ease-of-use.
  This includes:
  1) The YAML parser automatically converts attribute values into numeric types
  where possible. The os-version-ids for Android devices happen to be integers,
  but the Testing service expects them to be strings, so we automatically
  convert them to strings so users don't have to quote each one.
  2) The include: keyword, plus all test args that normally expect lists (e.g.
  device-ids, os-version-ids, locales, orientations...), will also accept a
  single value which is not specified using YAML list notation (e.g not enclosed
  in []). Such single values are automatically converted into a list containing
  one element.

  Args:
    arg_internal_name: the internal form of the arg name.
    arg_value: the argument's value as parsed from the yaml file.

  Returns:
    The validated argument value.

  Raises:
    InvalidArgException: If the arg value is missing or is not valid.
  """
  if arg_value is None:
    raise test_exceptions.InvalidArgException(arg_internal_name,
                                              'no argument value found.')
  if arg_internal_name in _FILE_ARG_VALIDATORS:
    return _FILE_ARG_VALIDATORS[arg_internal_name](arg_internal_name, arg_value)
  return _ValidateString(arg_internal_name, arg_value)


# Constants shared between arg-file validation and CLI flag validation.
POSITIVE_INT_PARSER = arg_parsers.BoundedInt(1, sys.maxsize)
NONNEGATIVE_INT_PARSER = arg_parsers.BoundedInt(0, sys.maxsize)
TIMEOUT_PARSER = arg_parsers.Duration(lower_bound='1m', upper_bound='6h')
TIMEOUT_PARSER_US = arg_parsers.Duration(
    lower_bound='1m', upper_bound='6h', parsed_unit='us')
ORIENTATION_LIST = ['portrait', 'landscape', 'default']
PERMISSIONS_LIST = ['all', 'none']


def ValidateStringList(arg_internal_name, arg_value):
  """Validates an arg whose value should be a list of strings.

  Args:
    arg_internal_name: the internal form of the arg name.
    arg_value: the argument's value parsed from yaml file.

  Returns:
    The validated argument value.

  Raises:
    InvalidArgException: the argument's value is not valid.
  """
  # convert single str to a str list
  if isinstance(arg_value, six.string_types):
    return [arg_value]
  if isinstance(arg_value, int):  # convert single int to a str list
    return [str(arg_value)]
  if isinstance(arg_value, list):
    return [_ValidateString(arg_internal_name, value) for value in arg_value]
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidateString(arg_internal_name, arg_value):
  """Validates an arg whose value should be a simple string."""
  if isinstance(arg_value, six.string_types):
    return arg_value
  if isinstance(arg_value, int):  # convert int->str if str is really expected
    return str(arg_value)
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidateBool(arg_internal_name, arg_value):
  """Validates an argument which should have a boolean value."""
  # Note: the python yaml parser automatically does string->bool conversion for
  # true/True/TRUE/false/False/FALSE and also for variations of on/off/yes/no.
  if isinstance(arg_value, bool):
    return arg_value
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidateDuration(arg_internal_name, arg_value):
  """Validates an argument which should have a Duration value."""
  try:
    if isinstance(arg_value, six.string_types):
      return TIMEOUT_PARSER(arg_value)
    elif isinstance(arg_value, int):
      return TIMEOUT_PARSER(str(arg_value))
  except arg_parsers.ArgumentTypeError as e:
    raise test_exceptions.InvalidArgException(arg_internal_name,
                                              six.text_type(e))
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidateDurationUs(arg_internal_name, arg_value):
  """Validates an argument which should have Duration value in microseconds."""
  try:
    if isinstance(arg_value, six.string_types):
      return TIMEOUT_PARSER_US(arg_value)
    elif isinstance(arg_value, int):
      return TIMEOUT_PARSER_US(str(arg_value))
  except arg_parsers.ArgumentTypeError as e:
    raise test_exceptions.InvalidArgException(arg_internal_name,
                                              six.text_type(e))
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidatePositiveInteger(arg_internal_name, arg_value):
  """Validates an argument which should be an integer > 0."""
  try:
    if isinstance(arg_value, int):
      return POSITIVE_INT_PARSER(str(arg_value))
  except arg_parsers.ArgumentTypeError as e:
    raise test_exceptions.InvalidArgException(arg_internal_name,
                                              six.text_type(e))
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidateNonNegativeInteger(arg_internal_name, arg_value):
  """Validates an argument which should be an integer >= 0."""
  try:
    if isinstance(arg_value, int):
      return NONNEGATIVE_INT_PARSER(str(arg_value))
  except arg_parsers.ArgumentTypeError as e:
    raise test_exceptions.InvalidArgException(arg_internal_name,
                                              six.text_type(e))
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidatePositiveIntList(arg_internal_name, arg_value):
  """Validates an arg whose value should be a list of ints > 0.

  Args:
    arg_internal_name: the internal form of the arg name.
    arg_value: the argument's value parsed from yaml file.

  Returns:
    The validated argument value.

  Raises:
    InvalidArgException: the argument's value is not valid.
  """
  if isinstance(arg_value, int):  # convert single int to an int list
    arg_value = [arg_value]
  if isinstance(arg_value, list):
    return [_ValidatePositiveInteger(arg_internal_name, v) for v in arg_value]
  raise test_exceptions.InvalidArgException(arg_internal_name, arg_value)


def _ValidateOrientationList(arg_internal_name, arg_value):
  """Validates that 'orientations' only contains allowable values."""
  arg_value = ValidateStringList(arg_internal_name, arg_value)
  for orientation in arg_value:
    _ValidateOrientation(orientation)
  if len(arg_value) != len(set(arg_value)):
    raise test_exceptions.InvalidArgException(
        arg_internal_name, 'orientations may not be repeated.')
  return arg_value


def _ValidateOrientation(orientation):
  if orientation not in ORIENTATION_LIST:
    raise test_exceptions.OrientationNotFoundError(orientation)


def _ValidatePermissions(arg_internal_name, arg_value):
  if arg_value not in PERMISSIONS_LIST:
    raise test_exceptions.InvalidArgException(
        arg_internal_name,
        'Invalid permissions specified. Must be either "all" or "none"')
  return arg_value


def _ValidateObbFileList(arg_internal_name, arg_value):
  """Validates that 'obb-files' contains at most 2 entries."""
  arg_value = ValidateStringList(arg_internal_name, arg_value)
  if len(arg_value) > 2:
    raise test_exceptions.InvalidArgException(
        arg_internal_name, 'At most two OBB files may be specified.')
  return arg_value


def _ValidateAdditionalApksList(arg_internal_name, arg_value):
  """Validates that 'additional-apks' contains [1, 100] entries."""
  arg_value = ValidateStringList(arg_internal_name, arg_value)
  if len(arg_value) < 1:
    raise test_exceptions.InvalidArgException(
        arg_internal_name, 'At least 1 additional apk must be specified.')
  if len(arg_value) > 100:
    raise test_exceptions.InvalidArgException(
        arg_internal_name, 'At most 100 additional apks may be specified.')
  return arg_value


def _ValidateAdditionalIpasList(arg_internal_name, arg_value):
  """Validates that 'additional-ipas' contains [1, 100] entries."""
  if len(arg_value) < 1:
    raise test_exceptions.InvalidArgException(
        arg_internal_name, 'At least 1 additional ipa must be specified.')
  if len(arg_value) > 100:
    raise test_exceptions.InvalidArgException(
        arg_internal_name, 'At most 100 additional ipas may be specified.')
  return arg_value


def _ValidateKeyValueStringPairs(arg_internal_name, arg_value):
  """Validates that an argument is a dict of string-type key-value pairs."""
  if isinstance(arg_value, dict):
    new_dict = {}
    # Cannot use dict comprehension since it's not supported in Python 2.6.
    for (key, value) in arg_value.items():
      new_dict[str(key)] = _ValidateString(arg_internal_name, value)
    return new_dict
  else:
    raise test_exceptions.InvalidArgException(arg_internal_name,
                                              'Malformed key-value pairs.')


def _ValidateListOfStringToStringDicts(arg_internal_name, arg_value):
  """Validates that an argument is a list of dicts of key=value string pairs."""
  if not isinstance(arg_value, list):
    raise test_exceptions.InvalidArgException(
        arg_internal_name, 'is not a list of maps of key-value pairs.')
  new_list = []
  for a_dict in arg_value:
    if not isinstance(a_dict, dict):
      raise test_exceptions.InvalidArgException(
          arg_internal_name,
          'Each list item must be a map of key-value string pairs.')
    new_dict = {}
    for (key, value) in a_dict.items():
      new_dict[str(key)] = _ValidateString(key, value)
    new_list.append(new_dict)
  return new_list


# Map of internal arg names to their appropriate validation functions.
# Any arg not appearing in this map is assumed to be a simple string.
_FILE_ARG_VALIDATORS = {
    'additional_apks': _ValidateAdditionalApksList,
    'additional_ipas': _ValidateAdditionalIpasList,
    'async_': _ValidateBool,
    'auto_google_login': _ValidateBool,
    'client_details': _ValidateKeyValueStringPairs,
    'device': _ValidateListOfStringToStringDicts,
    'device_ids': ValidateStringList,
    'directories_to_pull': ValidateStringList,
    'environment_variables': _ValidateKeyValueStringPairs,
    'grant_permissions': _ValidatePermissions,
    'locales': ValidateStringList,
    'orientations': _ValidateOrientationList,
    'obb_files': _ValidateObbFileList,
    'num_flaky_test_attempts': _ValidateNonNegativeInteger,
    'num_uniform_shards': _ValidatePositiveInteger,
    'test_targets_for_shard': ValidateStringList,
    'test_special_entitlements': _ValidateBool,
    'os_version_ids': ValidateStringList,
    'other_files': _ValidateKeyValueStringPairs,
    'performance_metrics': _ValidateBool,
    'record_video': _ValidateBool,
    'resign': _ValidateBool,
    'robo_directives': _ValidateKeyValueStringPairs,
    'scenario_labels': ValidateStringList,
    'scenario_numbers': _ValidatePositiveIntList,
    'test_targets': ValidateStringList,
    'timeout': _ValidateDuration,
    'timeout_us': _ValidateDurationUs,
    'use_orchestrator': _ValidateBool,
}


def InternalArgNameFrom(arg_external_name):
  """Converts a user-visible arg name into its corresponding internal name."""
  if arg_external_name == 'async':
    # The async flag has a special destination in the argparse namespace since
    # 'async' is a reserved keyword as of Python 3.7.
    return 'async_'
  return arg_external_name.replace('-', '_')


# Validation methods below this point are meant to be used on args regardless
# of whether they came from the command-line or an arg-file, while the methods
# above here are only for arg-file args, which bypass the standard validations
# performed by the argparse package (which only works with CLI args).


def ValidateArgsForTestType(args, test_type, type_rules, shared_rules,
                            all_test_args_set):
  """Raise errors if required args are missing or invalid args are present.

  Args:
    args: an argparse.Namespace object which contains attributes for all the
      arguments that were provided to the command invocation (i.e. command
      group and command arguments combined).
    test_type: string containing the type of test to run.
    type_rules: a nested dictionary defining the required and optional args
      per type of test, plus any default values.
    shared_rules: a nested dictionary defining the required and optional args
      shared among all test types, plus any default values.
    all_test_args_set: a set of strings for every gcloud-test argument to use
      for validation.

  Raises:
    InvalidArgException: If an arg doesn't pair with the test type.
    RequiredArgumentException: If a required arg for the test type is missing.
  """
  required_args = type_rules[test_type]['required'] + shared_rules['required']
  optional_args = type_rules[test_type]['optional'] + shared_rules['optional']
  allowable_args_for_type = required_args + optional_args

  # Raise an error if an optional test arg is not allowed with this test_type.
  for arg in all_test_args_set:
    if getattr(args, arg, None) is not None:  # Ignore args equal to None
      if arg not in allowable_args_for_type:
        raise test_exceptions.InvalidArgException(
            arg, 'may not be used with test type [{0}].'.format(test_type))
  # Raise an error if a required test arg is missing or equal to None.
  for arg in required_args:
    if getattr(args, arg, None) is None:
      raise exceptions.RequiredArgumentException(
          '{0}'.format(test_exceptions.ExternalArgNameFrom(arg)),
          'must be specified with test type [{0}].'.format(test_type))


def ValidateResultsBucket(args):
  """Do some basic sanity checks on the format of the results-bucket arg.

  Args:
    args: the argparse.Namespace containing all the args for the command.

  Raises:
    InvalidArgumentException: the bucket name is not valid or includes objects.
  """
  if args.results_bucket is None:
    return
  try:
    bucket_ref = storage_util.BucketReference.FromArgument(args.results_bucket,
                                                           require_prefix=False)
  except Exception as err:
    raise exceptions.InvalidArgumentException('results-bucket',
                                              six.text_type(err))
  args.results_bucket = bucket_ref.bucket


def ValidateResultsDir(args):
  """Sanity checks the results-dir arg and apply a default value if needed.

  Args:
    args: the argparse.Namespace containing all the args for the command.

  Raises:
    InvalidArgumentException: the arg value is not a valid cloud storage name.
  """
  if not args.results_dir:
    args.results_dir = _GenerateUniqueGcsObjectName()
    return

  args.results_dir = args.results_dir.rstrip('/')
  # See https://cloud.google.com/storage/docs/naming#objectnames for details.
  if '\n' in args.results_dir or '\r' in args.results_dir:
    raise exceptions.InvalidArgumentException(
        'results-dir', 'Name may not contain newline or linefeed characters')
  # Leave half of the max GCS object name length of 1024 for the backend to use.
  if len(args.results_dir) > 512:
    raise exceptions.InvalidArgumentException('results-dir', 'Name is too long')


def _GenerateUniqueGcsObjectName():
  """Create a unique GCS object name to hold test results in the results bucket.

  The Testing back-end needs a unique GCS object name within the results bucket
  to prevent race conditions while processing test results. By default, the
  gcloud client uses the current time down to the microsecond in ISO format plus
  a random 4-letter suffix. The format is: "YYYY-MM-DD_hh:mm:ss.ssssss_rrrr".

  Returns:
    A string with the unique GCS object name.
  """
  # In PY2, isoformat() argument 1 needs a char. But in PY3 it needs unicode.
  return '{0}_{1}'.format(
      datetime.datetime.now().isoformat(b'_' if six.PY2 else '_'), ''.join(
          random.sample(string.ascii_letters, 4)))


def ValidateOsVersions(args, catalog_mgr):
  """Validate os-version-ids strings against the TestEnvironmentCatalog.

  Also allow users to alternatively specify OS version strings (e.g. '5.1.x')
  but translate them here to their corresponding version IDs (e.g. '22').
  The final list of validated version IDs is sorted in ascending order.

  Args:
    args: an argparse namespace. All the arguments that were provided to the
      command invocation (i.e. group and command arguments combined).
    catalog_mgr: an AndroidCatalogManager object for working with the Android
      TestEnvironmentCatalog.
  """
  if not args.os_version_ids:
    return
  validated_versions = set()  # Using a set will remove duplicates
  for vers in args.os_version_ids:
    version_id = catalog_mgr.ValidateDimensionAndValue('version', vers)
    validated_versions.add(version_id)
  args.os_version_ids = sorted(validated_versions)


def ValidateXcodeVersion(args, catalog_mgr):
  """Validates an Xcode version string against the TestEnvironmentCatalog."""
  if args.xcode_version:
    catalog_mgr.ValidateXcodeVersion(args.xcode_version)


_OBB_FILE_REGEX = re.compile(
    r'(.*[\\/:])?(main|patch)\.\d+(\.[a-zA-Z]\w*)+\.obb$')


def NormalizeAndValidateObbFileNames(obb_files):
  """Confirm that any OBB file names follow the required Android pattern.

  Also expand local paths with "~"

  Args:
    obb_files: list of obb file references. Each one is either a filename on the
      local FS or a gs:// reference.
  """
  if obb_files:
    obb_files[:] = [
        obb_file if not obb_file or
        obb_file.startswith(storage_util.GSUTIL_BUCKET_PREFIX) else
        files.ExpandHomeDir(obb_file) for obb_file in obb_files
    ]
  for obb_file in (obb_files or []):
    if not _OBB_FILE_REGEX.match(obb_file):
      raise test_exceptions.InvalidArgException(
          'obb_files',
          '[{0}] is not a valid OBB file name, which must have the format: '
          '(main|patch).<versionCode>.<package.name>.obb'.format(obb_file))


def ValidateRoboDirectivesList(args):
  """Validates key-value pairs for 'robo_directives' flag."""
  resource_names = set()
  duplicates = set()
  for key, value in six.iteritems((args.robo_directives or {})):
    (action_type, resource_name) = util.ParseRoboDirectiveKey(key)
    if action_type in ['click', 'ignore'] and value:
      raise test_exceptions.InvalidArgException(
          'robo_directives',
          'Input value not allowed for click or ignore actions: [{0}={1}]'
          .format(key, value))

    # Validate resource_name validity
    if not resource_name:
      raise test_exceptions.InvalidArgException(
          'robo_directives', 'Missing resource_name for key [{0}].'.format(key))

    # Validate resource name uniqueness
    if resource_name in resource_names:
      duplicates.add(resource_name)
    else:
      resource_names.add(resource_name)

  if duplicates:
    raise test_exceptions.InvalidArgException(
        'robo_directives',
        'Duplicate resource names are not allowed: [{0}].'.format(
            ', '.join(duplicates)))


_ENVIRONMENT_VARIABLE_REGEX = re.compile(r'^[a-zA-Z][\w.-]+$')


def ValidateEnvironmentVariablesList(args):
  """Validates key-value pairs for 'environment-variables' flag."""
  for key in (args.environment_variables or []):
    # Check for illegal characters in the key.
    if not _ENVIRONMENT_VARIABLE_REGEX.match(key):
      raise test_exceptions.InvalidArgException(
          'environment_variables',
          'Invalid environment variable [{0}]'.format(key))


_DIRECTORIES_TO_PULL_PATH_REGEX = re.compile(
    r'^/?/(?:sdcard|data/local/tmp)(?:/[\w\-\.\+ /]+)*$')


def NormalizeAndValidateDirectoriesToPullList(dirs):
  """Validate list of file paths for 'directories-to-pull' flag.

  Also collapse paths to remove "." ".." and "//".

  Args:
    dirs: list of directory names to pull from the device.
  """
  if dirs:
    # Expand posix paths (Note: blank entries will fail in the next loop)
    dirs[:] = [posixpath.abspath(path) if path else path for path in dirs]

  for file_path in (dirs or []):
    # Check for correct file path format.
    if not _DIRECTORIES_TO_PULL_PATH_REGEX.match(file_path):
      raise test_exceptions.InvalidArgException(
          'directories_to_pull', 'Invalid path [{0}]'.format(file_path))


_PACKAGE_OR_CLASS_FOLLOWED_BY_COMMA = \
  re.compile(r'.*,(|\s+)(package |class ).*')

_ANY_SPACE_AFTER_COMMA = re.compile(r'.*,(\s+).*')


def ValidateTestTargetsForShard(args):
  """Validates --test-targets-for-shard uses proper delimiter."""
  if not getattr(args, 'test_targets_for_shard', {}):
    return
  for test_target in args.test_targets_for_shard:
    if _PACKAGE_OR_CLASS_FOLLOWED_BY_COMMA.match(test_target):
      raise test_exceptions.InvalidArgException(
          'test_targets_for_shard',
          '[{0}] is not a valid test_targets_for_shard argument. Multiple '
          '"package" and "class" specifications should be separated by '
          'a semicolon instead of a comma.'.format(test_target))
    if _ANY_SPACE_AFTER_COMMA.match(test_target):
      raise test_exceptions.InvalidArgException(
          'test_targets_for_shard',
          '[{0}] is not a valid test_targets_for_shard argument. No white '
          'space is allowed after a comma.'.format(test_target))


def ValidateScenarioNumbers(args):
  """Validates list of game-loop scenario numbers, which must be > 0."""
  if args.type != 'game-loop' or not args.scenario_numbers:
    return
  args.scenario_numbers = [_ValidatePositiveInteger('scenario_numbers', num)
                           for num in args.scenario_numbers]


def ValidateDeviceList(args, catalog_mgr):
  """Validates that --device contains a valid set of dimensions and values."""
  if not args.device:
    return

  for device_spec in args.device:
    for (dim, val) in device_spec.items():
      device_spec[dim] = catalog_mgr.ValidateDimensionAndValue(dim, val)

    # Fill in any missing dimensions with default dimension values
    if 'model' not in device_spec:
      device_spec['model'] = catalog_mgr.GetDefaultModel()
    if 'version' not in device_spec:
      device_spec['version'] = catalog_mgr.GetDefaultVersion()
    if 'locale' not in device_spec:
      device_spec['locale'] = catalog_mgr.GetDefaultLocale()
    if 'orientation' not in device_spec:
      device_spec['orientation'] = catalog_mgr.GetDefaultOrientation()


_IOS_DIRECTORIES_TO_PULL_PATH_REGEX = re.compile(
    r'^(/private/var/mobile/Media.*|[a-zA-Z0-9.-]+:/Documents.*)')


def ValidateIosDirectoriesToPullList(args):
  if not getattr(args, 'directories_to_pull', []):
    return
  for file_path in args.directories_to_pull:
    if not _IOS_DIRECTORIES_TO_PULL_PATH_REGEX.match(file_path):
      raise test_exceptions.InvalidArgException(
          'directories_to_pull', 'Invalid path [{0}]'.format(file_path))
