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

"""Feature flag config file loading and parsing."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import hashlib
import logging
import os
import threading
import time

from googlecloudsdk.core import config
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files as file_utils


class Property:
  """A Python Object that stores the value and weight of Property."""

  def __init__(self, yaml_prop):
    self.values = []
    self.weights = []

    for attribute in yaml_prop:
      if all(key in attribute for key in ('value', 'weight')):
        self.values.append(attribute['value'])
        self.weights.append(attribute['weight'])

_FEATURE_FLAG_CACHE_TIME_SECONDS = 30 * 60  # 30 minutes
_FEATURE_FLAG_YAML_URL = 'https://www.gstatic.com/cloudsdk/feature_flag_config_file.yaml'


def Cache(func):
  """Caches the result of a function."""
  cached_results = {}
  @functools.wraps(func)
  def ReturnCachedOrCallFunc(*args):
    try:
      return cached_results[args]
    except KeyError:
      result = func(*args)
      cached_results[args] = result
      return result
  ReturnCachedOrCallFunc.__wrapped__ = func
  return ReturnCachedOrCallFunc


def IsFeatureFlagsConfigStale(path):
  try:
    return (time.time() - os.path.getmtime(path) >
            _FEATURE_FLAG_CACHE_TIME_SECONDS)
  except OSError:
    return True


_FEATURE_FLAGS_LOCK = threading.RLock()


def FetchFeatureFlagsConfig():
  """Downloads the feature flag config file."""
  # pylint: disable=g-import-not-at-top
  import requests
  from googlecloudsdk.core import requests as core_requests

  try:
    yaml_request = core_requests.GetSession()
    response = yaml_request.get(_FEATURE_FLAG_YAML_URL)
    response.raise_for_status()
    return response.text
  except requests.exceptions.RequestException as e:
    logging.debug('Unable to fetch feature flags config from [%s]: %s',
                  _FEATURE_FLAG_YAML_URL, e)
  return None


@Cache
def GetFeatureFlagsConfig(account_id, project_id):
  """Gets the feature flags config.

  If the feature flags config file does not exist or is stale, download and save
  the feature flags config. Otherwise, read the feature flags config. Errors
  will be logged, but will not interrupt normal operation.

  Args:
    account_id: str, account ID.
    project_id: str, project ID


  Returns:
    A FeatureFlagConfig, or None.
  """
  feature_flags_config_path = config.Paths().feature_flags_config_path

  with _FEATURE_FLAGS_LOCK:
    yaml_data = None
    if IsFeatureFlagsConfigStale(feature_flags_config_path):
      yaml_data = FetchFeatureFlagsConfig()
      try:
        file_utils.WriteFileContents(feature_flags_config_path, yaml_data or '')
      except file_utils.Error as e:
        logging.warning('Unable to write feature flags config [%s]: %s. Please '
                        'ensure that this path is writeable.',
                        feature_flags_config_path, e)
    else:
      try:
        yaml_data = file_utils.ReadFileContents(feature_flags_config_path)
      except file_utils.Error as e:
        logging.warning('Unable to read feature flags config [%s]: %s. Please '
                        'ensure that this path is readable.',
                        feature_flags_config_path, e)

  if yaml_data:
    return FeatureFlagsConfig(yaml_data, account_id, project_id)
  return None


class FeatureFlagsConfig:
  """Stores all Property Objects for a given FeatureFlagsConfig."""

  def __init__(self, feature_flags_config_yaml, account_id=None,
               project_id=None):
    self.user_key = account_id or config.GetCID()
    self.project_id = project_id
    self.properties = _ParseFeatureFlagsConfig(feature_flags_config_yaml)

  def Get(self, prop):
    """Returns the value for the given property."""
    prop_str = str(prop)
    if prop_str not in self.properties:
      return None

    total_weight = sum(self.properties[prop_str].weights)
    if self.project_id:
      hash_str = prop_str + self.project_id
    else:
      hash_str = prop_str + self.user_key
    project_hash = int(
        hashlib.sha256(hash_str.encode('utf-8')).hexdigest(),
        16) % total_weight
    list_of_weights = self.properties[prop_str].weights
    sum_of_weights = 0
    for i in range(len(list_of_weights)):
      sum_of_weights += list_of_weights[i]
      if project_hash < sum_of_weights:
        return self.properties[prop_str].values[i]


def _ParseFeatureFlagsConfig(feature_flags_config_yaml):
  """Converts feature flag config file into a dictionary of Property objects.

  Args:
   feature_flags_config_yaml: str, feature flag config.

  Returns:
   property_dict: A dictionary of Property objects.
  """
  try:
    yaml_dict = yaml.load(feature_flags_config_yaml)
  except yaml.YAMLParseError as e:
    logging.warning('Unable to parse config: %s', e)
    return {}

  property_dict = {}
  for prop in yaml_dict or {}:
    yaml_prop = yaml_dict[prop]
    property_dict[prop] = Property(yaml_prop)
  return property_dict
