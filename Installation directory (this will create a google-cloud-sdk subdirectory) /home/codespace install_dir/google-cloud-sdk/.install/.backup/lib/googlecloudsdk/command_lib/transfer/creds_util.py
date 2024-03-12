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
"""Utils for handing transfer credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

import boto3
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import files

from six.moves import configparser


def _assign_with_error_on_duplicate(key, value, result_dict):
  """Assigns value to results_dict and raises error on duplicate key."""
  if key in result_dict:
    raise KeyError('Duplicate key in file: {}'.format(key))
  result_dict[key] = value


def _extract_keys(keys, search_dict, result_dict):
  """Converts key to multiple cases and attempts to extract from search_dict."""
  for original_key in keys:
    if original_key in search_dict:
      _assign_with_error_on_duplicate(original_key, search_dict[original_key],
                                      result_dict)
    else:
      # Can error if both camel and snake case matches are present.
      # Note: The below conversion utils don't work all the time.
      # For example, they cannot handle kebab-case.
      camel_case_key = resource_property.ConvertToCamelCase(original_key)
      snake_case_key = resource_property.ConvertToSnakeCase(original_key)
      if camel_case_key in search_dict:
        _assign_with_error_on_duplicate(original_key,
                                        search_dict[camel_case_key],
                                        result_dict)
      if snake_case_key in search_dict:
        _assign_with_error_on_duplicate(original_key,
                                        search_dict[snake_case_key],
                                        result_dict)


def get_values_for_keys_from_file(file_path, keys):
  """Reads JSON or INI file and returns dict with values for requested keys.

  JSON file keys should be top level.
  INI file sections will be flattened.

  Args:
    file_path (str): Path of JSON or INI file to read.
    keys (list[str]): Search for these keys to return from file.

  Returns:
    Dict[cred_key: cred_value].

  Raises:
    ValueError: The file was the incorrect format.
    KeyError: Duplicate key found.
  """
  result = {}
  real_path = os.path.realpath(os.path.expanduser(file_path))
  with files.FileReader(real_path) as file_reader:
    try:
      file_dict = json.loads(file_reader.read())
      _extract_keys(keys, file_dict, result)
    except json.JSONDecodeError:
      # More file formats to try before raising error.
      config = configparser.ConfigParser()
      try:
        config.read(real_path)
      except configparser.ParsingError:
        raise ValueError('Source creds file must be JSON or INI format.')
      # Parse all sections of INI file into dict.
      for section in config:
        section_dict = dict(config[section])
        _extract_keys(keys, section_dict, result)

  return result


def get_aws_creds_from_file(file_path):
  """Scans file for AWS credentials keys.

  Key fields prefixed with "aws" take precedence.

  Args:
    file_path (str): Path to creds file.

  Returns:
    Tuple of (access_key_id, secret_access_key).
    Each tuple entry can be a string or None.
  """
  creds_dict = get_values_for_keys_from_file(file_path, [
      'aws_access_key_id', 'aws_secret_access_key', 'access_key_id',
      'secret_access_key', 'role_arn'
  ])
  access_key_id = creds_dict.get('aws_access_key_id',
                                 creds_dict.get('access_key_id', None))
  secret_access_key = creds_dict.get('aws_secret_access_key',
                                     creds_dict.get('secret_access_key', None))
  role_arn = creds_dict.get('role_arn', None)
  return access_key_id, secret_access_key, role_arn


def get_default_aws_creds():
  """Returns creds from common AWS config file paths.

  Currently does not return "role_arn" because there is no way to extract
  this data from a boto3 Session object.

  Returns:
    Tuple of (access_key_id, secret_access_key, role_arn).
    Each tuple entry can be a string or None.
  """
  credentials = boto3.session.Session().get_credentials()
  if credentials:
    return credentials.access_key, credentials.secret_key
  return None, None
