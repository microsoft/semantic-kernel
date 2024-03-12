# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Low level reading and writing of property files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files

import six
from six.moves import configparser


class Error(exceptions.Error):
  """Exceptions for the properties_file module."""


class PropertiesParseError(Error):
  """An exception to be raised when a properties file is invalid."""


class PropertiesFile(object):
  """A class for loading and parsing property files."""

  def __init__(self, paths):
    """Creates a new PropertiesFile and load from the given paths.

    Args:
      paths: [str], List of files to load properties from, in order.
    """
    self._properties = {}

    for properties_path in paths:
      if properties_path:
        # Skip any paths that are None.
        self.__Load(properties_path)

  def __Load(self, properties_path):
    """Loads properties from the given file.

    Overwrites anything already known.

    Args:
      properties_path: str, Path to the file containing properties info.
    """
    parsed_config = configparser.ConfigParser()
    try:
      parsed_config.read(properties_path)
    except configparser.ParsingError as e:
      raise PropertiesParseError(str(e))

    for section in parsed_config.sections():
      if section not in self._properties:
        self._properties[section] = {}
      self._properties[section].update(dict(parsed_config.items(section)))

  def Get(self, section, name):
    """Gets the value of the given property.

    Args:
      section: str, The section name of the property to get.
      name: str, The name of the property to get.

    Returns:
      str, The value for the given section and property, or None if it is not
        set.
    """
    try:
      return self._properties[section][name]
    except KeyError:
      return None

  def AllProperties(self):
    """Returns a dictionary of properties in the file."""
    return dict(self._properties)


def PersistProperty(file_path, section, name, value):
  """Persists a value for a given property to a specific property file.

  Args:
    file_path: str, The path to the property file to update.
    section: str, The section name of the property to set.
    name: str, The name of the property to set.
    value: str, The value to set for the given property, or None to unset it.
  """
  parsed_config = configparser.ConfigParser()
  parsed_config.read(file_path)

  if not parsed_config.has_section(section):
    if value is None:
      return
    parsed_config.add_section(section)

  if value is None:
    parsed_config.remove_option(section, name)
  else:
    parsed_config.set(section, name, six.text_type(value))

  properties_dir, unused_name = os.path.split(file_path)
  files.MakeDir(properties_dir)

  # They changed the interface for configparser. On Python 2 it operates with
  # byte strings, on Python 3 it operaters with text strings.
  writer = files.BinaryFileWriter if six.PY2 else files.FileWriter
  with writer(file_path) as fp:
    parsed_config.write(fp)
