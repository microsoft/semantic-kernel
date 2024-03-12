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

"""Helpers for parsing Binary Authorization resource files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

import enum
from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
import six


class ResourceFileReadError(exceptions.Error):
  """Indicates a resource file could not be read."""


class ResourceFileTypeError(exceptions.Error):
  """Indicates a resource file was of an unsupported type."""


class ResourceFileParseError(exceptions.Error):
  """Indicates a resource file could not be parsed."""


class ResourceFileType(enum.Enum):
  UNKNOWN = 0
  JSON = 1
  YAML = 2


def GetResourceFileType(file_name):
  _, ext = os.path.splitext(file_name)
  if ext == '.json':
    return ResourceFileType.JSON
  elif ext in ('.yaml', '.yml'):
    return ResourceFileType.YAML
  else:
    return ResourceFileType.UNKNOWN


def LoadResourceFile(input_fname):
  """Load an input resource file in either JSON or YAML format.

  Args:
    input_fname: The name of the file to convert to parse.

  Returns:
    The Python object resulting from the decode.

  Raises:
    ResourceFileReadError: An error occurred attempting to read the input file.
    ResourceFileTypeError: The input file was an unsupported type.
    ResourceFileParseError: A parse error occurred.
  """
  try:
    input_text = files.ReadFileContents(input_fname)
  except files.Error as e:
    raise ResourceFileReadError(six.text_type(e))

  file_type = GetResourceFileType(input_fname)
  if file_type == ResourceFileType.JSON:
    try:
      return json.loads(input_text)
    except ValueError as e:
      raise ResourceFileParseError('Error in resource file JSON: ' +
                                   six.text_type(e))
  elif file_type == ResourceFileType.YAML:
    try:
      return yaml.load(input_text)
    except yaml.YAMLParseError as e:
      raise ResourceFileParseError('Error in resource file YAML: ' +
                                   six.text_type(e))
  else:  # file_type == ResourceFileType.UNKNOWN
    raise ResourceFileTypeError(
        'Input file [{}] not of type YAML or JSON'.format(input_fname))
