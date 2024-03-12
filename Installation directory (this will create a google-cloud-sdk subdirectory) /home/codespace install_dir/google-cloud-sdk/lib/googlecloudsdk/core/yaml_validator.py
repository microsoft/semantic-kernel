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

"""JSON schema YAML validator module.

Usage:

  # Get a validator for the JSON schema in the file schema_path.
  validator = yaml_validator.Validator(schema_path)
  # Validate parsed YAML data.
  validator.Validate(parsed_yaml_data)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import pkg_resources

import jsonschema


class Error(exceptions.Error):
  """Errors for this module."""


class InvalidSchemaError(Error):
  """JSON schema is invalid."""


class InvalidSchemaVersionError(Error):
  """JSON schema version is invalid."""


class RefError(Error):
  """Ref error -- YAML $ref path not found."""


class ValidationError(Error):
  """Validation error -- YAML data does not match the schema.

  Attributes:
      message: A user-readable error message describing the validation error.
  """

  def __init__(self, error):
    super(ValidationError, self).__init__(error)
    self.message = error.message


class Validator(object):
  """JSON schema validator."""

  def __init__(self, schema_path):
    """"Initilaizes the schema and validator for schema_path.

    The validator resolves references to all other schemas in the directory
    of schema_path.

    Yes, it's really this ugly defining a validator with a resolver to
    pkg_resources resources.

    Raises:
      IOError: if schema not found in installed resources.
      files.Error: if schema file not found.
      SchemaError: if the schema is invalid.

    Args:
      schema_path: JSON schema file path.

    Returns:
      The schema to validate and the validator.
    """
    schema_dir = os.path.dirname(schema_path)

    class RefResolver(jsonschema.RefResolver):
      """$ref: resolver that consults pkg_resources."""

      @staticmethod
      def resolve_remote(ref):
        """pkg_resources $ref override -- schema_dir closure needed here."""
        path = os.path.join(schema_dir, ref)
        data = pkg_resources.GetResourceFromFile(path)
        try:
          schema = yaml.load(data)
        except Exception as e:  # pylint: disable=broad-except, avoid crash
          raise InvalidSchemaError(e)
        self.ValidateSchemaVersion(schema, path)
        return schema

    try:
      schema = yaml.load(pkg_resources.GetResourceFromFile(schema_path))
    except Exception as e:  # pylint: disable=broad-except, avoid crash
      raise InvalidSchemaError(e)
    self.ValidateSchemaVersion(schema, schema_path)
    resolver = RefResolver.from_schema(schema)
    self._validator = jsonschema.validators.validator_for(schema)(
        schema, resolver=resolver)
    self._validate = self._validator.validate

  def ValidateSchemaVersion(self, schema, path):
    """Validates the parsed_yaml JSON schema version."""
    try:
      version = schema.get('$schema')
    except AttributeError:
      version = None
    if (not version or
        not version.startswith('http://json-schema.org/') or
        not version.endswith('/schema#')):
      raise InvalidSchemaVersionError(
          'Schema [{}] version [{}] is invalid. Expected "$schema: '
          'http://json-schema.org/*/schema#".'.format(path, version))

  def Validate(self, parsed_yaml):
    """Validates parsed_yaml against JSON schema.

    Args:
      parsed_yaml: YAML to validate

    Raises:
      ValidationError: if the template doesn't obey the schema.
    """
    try:
      self._validate(parsed_yaml)
    except jsonschema.RefResolutionError as e:
      raise RefError(e)
    except jsonschema.ValidationError as e:
      raise ValidationError(e)

  def ValidateWithDetailedError(self, parsed_yaml):
    """Validates parsed_yaml against JSON schema.

    Provides details of validation failure in the returned error message.
    Args:
      parsed_yaml: YAML to validate

    Raises:
      ValidationError: if the template doesn't obey the schema.
    """
    try:
      self._validate(parsed_yaml)
    except jsonschema.RefResolutionError as e:
      raise RefError(e)
    except jsonschema.exceptions.ValidationError as ve:
      msg = io.StringIO()
      msg.write('ERROR: Schema validation failed: {}\n\n'.format(ve))

      if ve.cause:
        additional_exception = 'Root Exception: {}'.format(ve.cause)
      else:
        additional_exception = ''

      root_error = ve.context[-1] if ve.context else None
      if root_error:
        error_path = ''.join(
            ('[{}]'.format(elem) for elem in root_error.absolute_path))
      else:
        error_path = ''

      msg.write('Additional Details:\n'
                'Error Message: {msg}\n\n'
                'Failing Validation Schema: {schema}\n\n'
                'Failing Element: {instance}\n\n'
                'Failing Element Path: {path}\n\n'
                '{additional_cause}\n'.format(
                    msg=root_error.message if root_error else None,
                    instance=root_error.instance if root_error else None,
                    schema=root_error.schema if root_error else None,
                    path=error_path,
                    additional_cause=additional_exception))
      ve.message = msg.getvalue()
      raise ValidationError(ve)

  def Iterate(self, parsed_yaml):
    """Validates parsed_yaml against JSON schema and returns all errors.

    Args:
      parsed_yaml: YAML to validate

    Raises:
      ValidationError: if the template doesn't obey the schema.

    Returns:
      A list of all errors, empty if no validation errors.
    """
    return self._validator.iter_errors(parsed_yaml)
