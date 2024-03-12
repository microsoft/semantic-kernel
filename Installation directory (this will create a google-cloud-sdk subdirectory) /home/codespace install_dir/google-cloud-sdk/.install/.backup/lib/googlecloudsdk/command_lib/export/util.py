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

"""Common utilities for the gcloud export/import commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json
import os
import re
import textwrap

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.py import encoding as api_encoding
from apitools.base.py import encoding_helper
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.util import encoding


def AddExportFlags(parser, schema_path=None):
  """Add common export flags to the arg parser.

  Args:
    parser: The argparse parser object.
    schema_path: The resource instance schema file path if there is one.
  """

  help_text = """Path to a YAML file where the configuration will be exported.
          Alternatively, you may omit this flag to write to standard output."""
  if schema_path is not None:
    help_text += """ For a schema describing the export/import format, see:
          {}.
      """.format(schema_path)
  parser.add_argument(
      '--destination',
      help=textwrap.dedent(help_text),
      # Allow writing to stdout.
      required=False)


def AddImportFlags(parser, schema_path=None):
  """Add common import flags to the arg parser.

  Args:
    parser: The argparse parser object.
    schema_path: The resource instance schema file path if there is one.
  """

  help_text = """Path to a YAML file containing configuration export data.
          Alternatively, you may omit this flag to read from standard input."""
  if schema_path is not None:
    help_text += """For a schema describing the export/import format, see:
          {}.
      """.format(schema_path)
    if '$CLOUDSDKROOT' in schema_path:
      help_text += """

      Note: $CLOUDSDKROOT represents the Google Cloud CLI's installation directory.
      """

  parser.add_argument(
      '--source',
      help=textwrap.dedent(help_text),
      # Allow reading from stdin.
      required=False)


def GetSchemaPath(api_name, api_version='v1', message_name=None,
                  for_help=False):
  """Returns the schema installation path.

  $CLOUDSDKROOT/lib/googlecloudsdk/schemas/
    {api}/{api_version}/{message_name}.yaml

  Args:
    api_name: The api name.
    api_version: The API version string.
    message_name: The UpperCamelCase message name.
    for_help: Replaces the actual Cloud SDK installation root dir with
      $CLOUDSDKROOT.
  """
  path = os.path.join(
      os.path.dirname(os.path.dirname(os.path.dirname(
          encoding.Decode(__file__)))),
      'schemas',
      api_name,
      api_version,
      '{}.yaml'.format(message_name),
  )
  if for_help:
    rel_path_index = path.rfind(os.path.sep + 'googlecloudsdk' + os.path.sep)
    if rel_path_index < 0:
      return path
    path = os.path.join('$CLOUDSDKROOT', 'lib', path[rel_path_index + 1:])
  return path


def ValidateYAML(parsed_yaml, schema_path):
  """Validates YAML against JSON schema.

  Args:
    parsed_yaml: YAML to validate
    schema_path: JSON schema file path.

  Raises:
    IOError: if schema not found in installed resources.
    files.Error: if schema file not found.
    ValidationError: if the template doesn't obey the schema.
    SchemaError: if the schema is invalid.
  """
  yaml_validator.Validator(schema_path).Validate(parsed_yaml)


def _ParseProperties(error_message):
  """Parses disallowed properties from an error message.

  Args:
    error_message: The error message to parse.

  Returns:
    A list of property names.

  A sample error message might look like this:

  Additional properties are not allowed ('id', 'createTime', 'updateTime',
  'name' were unexpected)

  """
  return list(
      property.strip('\'') for property in re.findall("'[^']*'", error_message))


def _ClearFields(fields, path_deque, py_dict):
  """Clear the given fields in a dict at a given path.

  Args:
    fields: A list of fields to clear
    path_deque: A deque containing path segments
    py_dict: A nested dict from which to clear the fields
  """
  tmp_dict = py_dict
  for elem in path_deque:
    tmp_dict = tmp_dict[elem]
  for field in fields:
    if field in tmp_dict:
      del tmp_dict[field]


def _IsDisallowedPropertiesError(error):
  """Checks if an error is due to properties that were not in the schema.

  Args:
    error: A ValidationError

  Returns:
    Whether the error was due to disallowed properties
  """
  prop_validator = 'additionalProperties'
  prop_message = 'Additional properties are not allowed'
  return error.validator == prop_validator and prop_message in error.message


def _FilterYAML(parsed_yaml, schema_path):
  """Filter out fields from the yaml that are not in the schema.

  Args:
    parsed_yaml: yaml to filter
    schema_path: Path to schema.
  """
  has_warnings = False
  for error in yaml_validator.Validator(schema_path).Iterate(parsed_yaml):
    # There are other types of errors (for example, missing a required field),
    # but these are the only ones we expect to see on export and the only ones
    # we want to act on. There is no way to distinguish disallowed fields from
    # unrecognized fields. If we attempt to export an unrecognized value for a
    # recognized field (this will happen whenever we add a new enum value), or
    # if we attempt to export a resource that is missing a required field, we
    # will log the errors as warnings and the exported data will not be able to
    # be imported via the import command until the import command is updated.
    if _IsDisallowedPropertiesError(error):
      fields_to_remove = _ParseProperties(error.message)
      _ClearFields(fields_to_remove, error.path, parsed_yaml)
    else:
      log.warning(error.message)
      has_warnings = True
    if has_warnings:
      log.warning('The import command may need to be updated to handle '
                  'the export data.')


def Import(message_type, stream, schema_path=None):
  """Reads YAML from a stream as a message.

  Args:
    message_type: Type of message to load YAML into.
    stream: Input stream or buffer containing the YAML.
    schema_path: JSON schema file path. None for no YAML validation.

  Raises:
    ParseError: if yaml could not be parsed as the given message type.

  Returns:
    message_type object.
  """
  parsed_yaml = yaml.load(stream)
  if schema_path:
    # If a schema is provided, validate against it.
    yaml_validator.Validator(schema_path).Validate(parsed_yaml)
  try:
    message = api_encoding.PyValueToMessage(message_type, parsed_yaml)
  except Exception as e:
    raise exceptions.ParseError('Cannot parse YAML: [{0}]'.format(e))
  return message


# pylint: disable=protected-access
# TODO(b/177577343)
# This is a terrible hack to fix an apitools issue that makes all registered
# codecs global, which breaks our presubmits. This will be removed once
# declarative workflows deprecate our current import/export tooling.
class _ProtoJsonApiTools(encoding_helper._ProtoJsonApiTools):
  """JSON encoder used by apitools clients."""
  _INSTANCE = None

  @classmethod
  def Get(cls):
    if cls._INSTANCE is None:
      cls._INSTANCE = cls()
    return cls._INSTANCE

  def encode_message(self, message):
    if isinstance(message, messages.FieldList):
      return '[%s]' % (', '.join(self.encode_message(x) for x in message))

    # pylint: disable=unidiomatic-typecheck
    if type(message) in encoding_helper._CUSTOM_MESSAGE_CODECS:
      return encoding_helper._CUSTOM_MESSAGE_CODECS[type(message)].encoder(
          message)

    message = _EncodeUnknownFields(message)
    result = super(encoding_helper._ProtoJsonApiTools,
                   self).encode_message(message)
    result = _EncodeCustomFieldNames(message, result)
    return json.dumps(json.loads(result), sort_keys=True)

  def encode_field(self, field, value):
    for encoder in _GetFieldCodecs(field, 'encoder'):
      result = encoder(field, value)
      value = result.value
      if result.complete:
        return value
    if isinstance(field, messages.EnumField):
      if field.repeated:
        remapped_value = [
            encoding_helper.GetCustomJsonEnumMapping(
                field.type, python_name=e.name) or e.name for e in value
        ]
      else:
        remapped_value = encoding_helper.GetCustomJsonEnumMapping(
            field.type, python_name=value.name)
      if remapped_value:
        return remapped_value
    if (isinstance(field, messages.MessageField) and
        not isinstance(field, message_types.DateTimeField)):
      value = json.loads(self.encode_message(value))
    return super(encoding_helper._ProtoJsonApiTools,
                 self).encode_field(field, value)


def RegisterCustomFieldTypeCodecs(field_type_codecs):
  """Registers custom field codec for int64s."""
  def _EncodeInt64Field(unused_field, value):
    int_value = api_encoding.CodecResult(value=value, complete=True)
    return int_value

  def _DecodeInt64Field(unused_field, value):
    # Don't need to do anything special, they're decoded just fine
    return api_encoding.CodecResult(value=value, complete=True)

  field_type_codecs[messages.IntegerField] = encoding_helper._Codec(
      encoder=_EncodeInt64Field, decoder=_DecodeInt64Field)
  return field_type_codecs


def _GetFieldCodecs(field, attr):
  custom_field_codecs = copy.deepcopy(encoding_helper._CUSTOM_FIELD_CODECS)
  field_type_codecs = RegisterCustomFieldTypeCodecs(
      copy.deepcopy(encoding_helper._FIELD_TYPE_CODECS))

  result = [
      getattr(custom_field_codecs.get(field), attr, None),
      getattr(field_type_codecs.get(type(field)), attr, None),
  ]
  return [x for x in result if x is not None]


def _EncodeUnknownFields(message):
  """Remap unknown fields in message out of message.source."""
  source = encoding_helper._UNRECOGNIZED_FIELD_MAPPINGS.get(type(message))
  if source is None:
    return message
  # CopyProtoMessage uses _ProtoJsonApiTools, which uses this message. Use
  # the vanilla protojson-based copy function to avoid infinite recursion.
  result = encoding_helper._CopyProtoMessageVanillaProtoJson(message)
  pairs_field = message.field_by_name(source)
  if not isinstance(pairs_field, messages.MessageField):
    raise exceptions.InvalidUserInputError('Invalid pairs field %s' %
                                           pairs_field)
  pairs_type = pairs_field.message_type
  value_field = pairs_type.field_by_name('value')
  value_variant = value_field.variant
  pairs = getattr(message, source)
  codec = _ProtoJsonApiTools.Get()
  for pair in pairs:
    encoded_value = codec.encode_field(value_field, pair.value)
    result.set_unrecognized_field(pair.key, encoded_value, value_variant)
  setattr(result, source, [])
  return result


def _EncodeCustomFieldNames(message, encoded_value):
  field_remappings = list(
      encoding_helper._JSON_FIELD_MAPPINGS.get(type(message), {}).items())
  if field_remappings:
    decoded_value = json.loads(encoded_value)
    for python_name, json_name in field_remappings:
      if python_name in encoded_value:
        decoded_value[json_name] = decoded_value.pop(python_name)
    encoded_value = json.dumps(decoded_value)
  return encoded_value


def Export(message, stream=None, schema_path=None):
  """Writes a message as YAML to a stream.

  Args:
    message: Message to write.
    stream: Output stream, None for writing to a string and returning it.
    schema_path: JSON schema file path. If None then all message fields are
      written, otherwise only fields in the schema are written.

  Returns:
    Returns the return value of yaml.dump(). If stream is None then the return
    value is the YAML data as a string.
  """

  result = _ProtoJsonApiTools.Get().encode_message(message)
  message_dict = json.loads(
      encoding_helper._IncludeFields(result, message, None))
  if schema_path:
    _FilterYAML(message_dict, schema_path)
  return yaml.dump(message_dict, stream=stream)
