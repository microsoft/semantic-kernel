# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Helpers for loading YAML data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import pkg_resources

_RESOURCE_FILE_NAME = 'resources.yaml'
_RESOURCE_FILE_PREFIX = 'googlecloudsdk.command_lib.'
_RESOURCE_PATH_PATTERN = r'^(?P<surface_name>\S+)\.(?P<resource_name>\w+)$'


class Error(exceptions.Error):
  """Base class for errors in this module."""


class InvalidResourcePathError(Error):
  """Raised when a resources.yaml is not found by the given resource_path."""


class YAMLData(object):
  """A general data holder object for data parsed from a YAML file."""

  def __init__(self, data):
    self._data = data

  def GetData(self):
    return self._data


class ResourceYAMLData(YAMLData):
  """A data holder object for data parsed from a resources.yaml file."""

  @classmethod
  def FromPath(cls, resource_path):
    """Constructs a ResourceYAMLData from a standard resource_path.

    Args:
      resource_path: string, the dotted path of the resources.yaml file, e.g.
        iot.device or compute.instance.

    Returns:
      A ResourceYAMLData object.

    Raises:
      InvalidResourcePathError: invalid resource_path string.
    """
    match = re.search(_RESOURCE_PATH_PATTERN, resource_path)
    if not match:
      raise InvalidResourcePathError(
          'Invalid resource_path: [{}].'.format(resource_path))
    surface_name = match.group('surface_name')
    resource_name = match.group('resource_name')
    # Gets the directory name of the targeted YAML file.
    # Example: googlecloudsdk.command_lib.iot.
    dir_name = _RESOURCE_FILE_PREFIX + surface_name + '.'
    resource_file = pkg_resources.GetResource(dir_name, _RESOURCE_FILE_NAME)
    # Loads the data from YAML file.
    resource_data = yaml.load(resource_file)[resource_name]
    return cls(resource_data)

  def GetArgName(self):
    return self._data.get('name', None)
