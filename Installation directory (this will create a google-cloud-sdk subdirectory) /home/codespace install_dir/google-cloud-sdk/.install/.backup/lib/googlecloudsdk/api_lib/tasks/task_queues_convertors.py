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

"""Functions to convert attribute formats between Task Queue and Cloud Tasks.

Functions defined here are used to migrate away from soon to be deprecated
admin-console-hr superapp. Instead we will be using Cloud Tasks APIs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from googlecloudsdk.command_lib.tasks import constants

import six


def ConvertStringToCamelCase(string):
  """Takes a 'snake_case' string and converts it to 'camelCase'.

  Args:
    string: The string we want to convert.

  Returns:
    The converted string. Some examples are below:
      min_backoff => minBackoff
      max_retry_duration => maxRetryDuration
  """
  if not hasattr(ConvertStringToCamelCase, 'processed_strings'):
    ConvertStringToCamelCase.processed_strings = {}
  if string in ConvertStringToCamelCase.processed_strings:
    return ConvertStringToCamelCase.processed_strings[string]
  attributes = string.split('_')
  for index, attribute in enumerate(attributes):
    if index == 0:
      continue
    attributes[index] = attribute.capitalize()
  camel_case_string = ''.join(attributes)
  ConvertStringToCamelCase.processed_strings[string] = camel_case_string
  return camel_case_string


def ConvertRate(value):
  """Converts the time based rate into its integer value in seconds.

  This function converts the input float values into its seconds equivalent.
  For example,
    '100/s' => 100.0
    '60/m' => 1.0

  Args:
    value: The string value we want to convert.

  Returns:
    A float value representing the rate on a per second basis
  """
  float_value, unit = float(value[:-2]), value[-1]
  return round(float_value / constants.TIME_IN_SECONDS[unit], 9)


def CheckAndConvertStringToFloatIfApplicable(string):
  """Converts the input into a float if possible.

  This function converts the input float values into its seconds equivalent if
  the string has any relevant time units. For example,
    '2m' => 120.0
    '1h' => 3600.0
    '8s' => 8.0
    'apples' => 'apples'

  Args:
    string: The string we want to convert.

  Returns:
    The input itself if it is not possible to convert it to a float value,
    the converted float value otherwise.
  """
  if not isinstance(string, six.string_types):
    return string
  if re.match(r'^(\d+(\.\d+)?|\.\d+)[smhd]$', string):
    return float(string[:-1]) * constants.TIME_IN_SECONDS[string[-1]]
  try:
    return_value = float(string)
  except ValueError:
    return_value = string
  return return_value


def ConvertBackoffSeconds(value):
  """Converts min/max backoff values to the format CT expects.

  Args:
    value: A float value representing time in seconds.

  Returns:
    The string representing the time with 's' appended at the end.
  """
  if value is None:
    return None
  return '{}s'.format(round(value, 8))


def ConvertTarget(value):
  """Converts target to that format that Cloud Tasks APIs expect.

  Args:
    value: A string representing the service or version_dot_service.

  Returns:
    An ordered dict with parsed values for service and target if it exists.

  Raises:
    ValueError: If the input provided for target is not in the format expected.
  """
  targets = value.split('.')
  if len(targets) == 1:
    return collections.OrderedDict({'service': targets[0]})
  elif len(targets) == 2:
    return collections.OrderedDict(
        {'service': targets[1], 'version': targets[0]})
  raise ValueError('Unsupported value received for target {}'.format(value))


def ConvertTaskAgeLimit(value):
  """Converts task age limit values to the format CT expects.

  Args:
    value: A string value representing the task age limit. For example, '2.5m',
      '1h', '8s', etc.

  Returns:
    The string representing the time to the nearest second with 's' appended
    at the end.
  """
  time_in_seconds = float(value[:-1]) * constants.TIME_IN_SECONDS[value[-1]]
  return '{}s'.format(int(time_in_seconds))
