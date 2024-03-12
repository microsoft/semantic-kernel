# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utils for camel case/snake case conversions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import metrics
import six

_DEFAULT_API_NAME = 'datastream'
CAMEL_CASE_CONVERSION_EVENT = _DEFAULT_API_NAME + '_camel_case_conversion'


def ConvertYamlToCamelCase(yaml_dict):
  """Recursively goes through the dictionary obj and replaces keys with the convert function.

  taken from:
  https://stackoverflow.com/questions/11700705/how-to-recursively-replace-character-in-keys-of-a-nested-dictionary.

  Args:
    yaml_dict: dict of loaded yaml

  Returns:
    A converted dict with camelCase keys
  """
  # NOMUTANTS -- not necessary here.
  if isinstance(yaml_dict, (str, int, float)):
    return yaml_dict
  if isinstance(yaml_dict, dict):
    new = yaml_dict.__class__()
    for k, v in yaml_dict.items():
      new[SnakeToCamelCase(k)] = ConvertYamlToCamelCase(v)
  elif isinstance(yaml_dict, (list, set, tuple)):
    new = yaml_dict.__class__(ConvertYamlToCamelCase(v) for v in yaml_dict)
  else:
    return yaml_dict
  return new


def SnakeToCamelCase(value):
  """Convert value from snake_case to camelCase."""
  # If it's not snake_case format
  if not re.match(r'[a-zA-Z]+_[a-zA-Z]+', value):
    return value

  # Remove unnecessary characters from beginning of line.
  string = re.sub(r'^[\-_\.]', '', six.text_type(value.lower()))
  if not string:
    return string

  # Record snake to camel case conversion (for tracking purposes)
  metrics.CustomTimedEvent(CAMEL_CASE_CONVERSION_EVENT)

  # convert first character to lower and replace characters
  # after '_' to upppercase.
  return string[0].lower() + re.sub(
      r'[\-_\.\s]([a-z])', lambda matched: matched.group(1).upper(), string[1:]
  )
