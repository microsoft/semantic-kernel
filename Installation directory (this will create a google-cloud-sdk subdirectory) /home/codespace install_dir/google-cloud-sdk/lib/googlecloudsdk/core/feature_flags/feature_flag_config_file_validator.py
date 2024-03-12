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
"""Validates config file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.feature_flags import config
from googlecloudsdk.core.util import files


SCHEMA_PATH = (
    os.path.join(os.path.dirname(__file__), 'feature_flags_config_schema.yaml'))


class ValidationBaseError(Exception):
  """Base class for validation errors.

  Attributes:
    header: str, description of the error, which may include the
      section/property where there is an error.
    message: str, the error message.
  """

  def __init__(self, header, message):
    self.header = header
    self.message = message
    super(ValidationBaseError, self).__init__(self.message)


class ValidationFailedError(Exception):
  """Validation failed Error."""

  def __init__(self, config_file_path, config_file_errors,
               config_file_property_errors):
    msg_lines = []
    msg_lines.append('Invalid Feature Flag Config File\n[{}]\n'.format(
        config_file_path))
    for error in config_file_errors:
      msg_lines.append('{}: {}'.format(error.header, error.message))

    if config_file_property_errors:
      if config_file_errors:
        msg_lines.append('')
      msg_lines.append('PROPERTY ERRORS:')
    for section_property, errors in sorted(config_file_property_errors.items()):
      msg_lines.append('[{}]'.format(section_property))
      for error in errors:
        msg_lines.append('\t{}: {}'.format(error.header, error.message))

    super(ValidationFailedError, self).__init__('\n'.join(msg_lines))


class InvalidOrderError(ValidationBaseError):
  """Raised when the properties are not in alphabetical order."""

  def __init__(self, properties_list):
    """Instantiates the InvalidOrderError class.

    Args:
      properties_list: str, list of all properties in the config file.
    """
    header = 'ALPHABETICAL_ORDER_ERROR'
    message = ('Properties in the Feature Flag Config File must be in '
               'alphabetical order:\n\t{properties_list}'
               ).format(properties_list=properties_list)
    super(InvalidOrderError, self).__init__(header, message)


class InvalidPropertyError(ValidationBaseError):
  """Raised when a property is not a valid Cloud SDK property."""

  def __init__(self, property_name, reason):
    """Instantiates the InvalidPropertyError class.

    Args:
      property_name: str, name of the property.
      reason: str, reason for the error.
    """
    header = 'INVALID_PROPERTY_ERROR'
    message = '[{}] is not a valid Cloud SDK property. {}'.format(
        property_name, reason)
    super(InvalidPropertyError, self).__init__(header, message)


class InvalidSchemaError(ValidationBaseError):
  """Raised when the config file doesnt satisfy the schema."""

  def __init__(self, invalid_schema_reasons):
    """Instantiates the InvalidSchemaError class.

    Args:
      invalid_schema_reasons: str, list of all reasons why the config file does
        not satisfy the schema.
    """
    header = 'INVALID_SCHEMA_ERROR'
    schema = 'googlecloudsdk/core/feature_flags/feature_flags_config_schema.yaml'
    message = ('Config file does not follow schema at [{}] because:\n{}.'
               ).format(schema, '.\n'.join(invalid_schema_reasons))

    super(InvalidSchemaError, self).__init__(header, message)


class InvalidValueError(ValidationBaseError):
  """Raised when a value does not follow the property's validator."""

  def __init__(self, invalid_values):
    """Instantiates the InvalidValueError class.

    Args:
      invalid_values: str, list of values in the section/property that are
        invalid.
    """
    header = 'INVALID_PROPERTY_VALUES'
    message = ('The following values are invalid according to the property\'s '
               'validator: {}').format(invalid_values)

    super(InvalidValueError, self).__init__(header, message)


class InconsistentValuesError(ValidationBaseError):
  """Raised when the values in a property are not of the same type.

  Attributes:
    header: str, general description of the error.
  """

  def __init__(self, values):
    """Instantiates the InconsistentValuesError class.

    Args:
      values: str, list of values in the property with inconsistent values.
    """
    header = 'INCONSISTENT_PROPERTY_VALUES'
    message = ('Value types are not consistent. '
               'Ensure the values {} are of the same type.').format(values)
    super(InconsistentValuesError, self).__init__(header, message)


def AppendIfNotNone(arr, value):
  if value:
    arr.append(value)


class Validator(object):
  """A class that checks for the validity of the config file.

  Attributes:
    config_file_path: str, the path to the configuration file.
    parsed_yaml: dict, the parsed YAML representation of the configuration file.
  """

  def __init__(self, config_file_path):
    self.config_file_path = config_file_path
    self.parsed_yaml = yaml.load_path(path=config_file_path, round_trip=True)

  def ValidateAlphabeticalOrder(self):
    """Validates whether the properties in the config file are in alphabetical order.

    Returns:
      InvalidOrderError: If the properties in config file are not in
          alphabetical order.
    """
    properties_list = list(self.parsed_yaml.keys())
    if properties_list != sorted(properties_list):
      return InvalidOrderError(properties_list=properties_list)
    return None

  def ValidateConfigFile(self):
    """Validates the config file.

    If the config file has any errors, this method compiles them and then
    returns an easy to read sponge log.

    Raises:
      ValidationFailedError: Error raised when validation fails.
    """
    config_file_errors = []
    if self.parsed_yaml is None:
      return
    if not isinstance(self.parsed_yaml, dict):
      config_file_errors.append(InvalidSchemaError(
          invalid_schema_reasons=['The file content is not in json format']))
      raise ValidationFailedError(self.config_file_path, config_file_errors, {})

    AppendIfNotNone(config_file_errors, self.ValidateAlphabeticalOrder())
    AppendIfNotNone(config_file_errors, self.ValidateSchema())

    config_file_property_errors = {}

    config_file = files.ReadFileContents(self.config_file_path)
    feature_flags_config = config.FeatureFlagsConfig(config_file)
    for section_property in feature_flags_config.properties:
      property_errors = []
      values_list = feature_flags_config.properties[section_property].values

      AppendIfNotNone(property_errors, self.ValidateValueTypes(values_list))
      AppendIfNotNone(property_errors,
                      self.ValidateValues(values_list, section_property))
      if property_errors:
        config_file_property_errors[section_property] = property_errors

    if config_file_errors or config_file_property_errors:
      raise ValidationFailedError(self.config_file_path, config_file_errors,
                                  config_file_property_errors)

  def ValidateSchema(self):
    """Validates the parsed_yaml against the JSON schema at SCHEMA_PATH.

    Returns:
      InvalidSchemaError: If the config file does not match the schema.
    """
    schema_errors = []
    list_of_invalid_schema = yaml_validator.Validator(SCHEMA_PATH).Iterate(
        self.parsed_yaml)
    for error in list_of_invalid_schema:
      schema_errors.append('{}'.format(error))
    if schema_errors:
      return InvalidSchemaError(invalid_schema_reasons=schema_errors)
    return None

  def ValidateValueTypes(self, values_list):
    """Validates the values of each property in the config file.

    This method ensures that the values of each property are of the same type.

    Args:
      values_list: list, list of possible values of the property in the config
          file.

    Returns:
      InconsistentValuesError: If the values are not of the same type.
    """
    if not values_list:
      return None

    first_value_type = type(values_list[0])
    for value in values_list:
      if not isinstance(value, first_value_type):
        return InconsistentValuesError(values=values_list)

    return None

  def ValidateValues(self, values_list, section_property):
    """Validates the values of each property in the config file.

    This method ensures that the possible values of each property satisfy the
    property's validator.

    Args:
      values_list: list, list of possible values of the property in the config
          file.
      section_property: str, name of the property.

    Returns:
      InvalidPropertyError: If the property is not an actual Cloud SDK property.
      InvalidValueError: If the values do not satisfy the property's validator.
    """
    try:
      section_name, property_name = section_property.split('/')
    except ValueError:
      # This is already caught by the schema validator
      return None

    try:
      section_instance = getattr(properties.VALUES, section_name)
    except AttributeError:
      return InvalidPropertyError(
          section_property,
          'Property section [{}] does not exist.'.format(section_name))

    try:
      property_instance = getattr(section_instance, property_name)
    except AttributeError:
      return InvalidPropertyError(
          section_property,
          'Property [{}] is not a property in section [{}].'.format(
              property_name, section_name))

    list_of_invalid_values = []
    for value in values_list:
      try:
        property_instance.Validate(value)
      except properties.InvalidValueError:
        list_of_invalid_values.append(value)

    if list_of_invalid_values:
      return InvalidValueError(invalid_values=list_of_invalid_values)
    return None

