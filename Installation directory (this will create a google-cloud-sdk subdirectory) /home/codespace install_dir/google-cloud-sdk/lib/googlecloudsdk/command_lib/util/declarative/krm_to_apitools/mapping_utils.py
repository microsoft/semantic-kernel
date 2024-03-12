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
"""Map Apitools resquest fileds to KCC KRM YAML fields."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import os

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.util import files

import six


_YAML_MAPPING_PLACEHOLDER = '__YAML_PATH__'


class ApitoolsToKrmFieldDescriptor(object):
  """Ecapsulates the mapping from an apitools message field to a YAML path.

  Attributes:
    message_field: string, The field in the apitools message.
    yaml_path: string, Dot ('.') seperated path to the correlated field data in
      the yaml input file.
    submessage_template: {string: ApitoolsToKrmFieldDescriptor}, dict of
      ApitoolsToKrmFieldDescriptors describing the template of the submessage.
      None if this descriptor describes a scalar field.
    repeatable: bool, True if this desriptor is for a repeatable field,
      False otherwise.
  """

  def __init__(self, message_field,
               yaml_field_path,
               submessage_template=None,
               repeatable=False):
    self._message_path = message_field
    self._yaml_path = yaml_field_path
    self._submessage_template = submessage_template
    self._repeatable = repeatable

  @property
  def message_field(self):
    return self._message_path

  @property
  def yaml_path(self):
    return self._yaml_path

  @property
  def submessage_template(self):
    return self._submessage_template

  @property
  def repeatable(self):
    return self._repeatable

  def __str__(self):
    output = collections.OrderedDict()
    output[self._message_path] = self._yaml_path
    output['repeatable'] = self._repeatable
    submessage_template_str_array = []
    if self._submessage_template:
      for descriptor in self._submessage_template.values():
        submessage_template_str_array.append(str(descriptor))
    output['submessage_template'] = submessage_template_str_array or None
    yaml.convert_to_block_text(output)
    return yaml.dump(output, round_trip=True)

  def __eq__(self, other):
    if not isinstance(other, ApitoolsToKrmFieldDescriptor):
      return False
    return (self._message_path == other.message_field and
            self._yaml_path == other.yaml_path and
            self._submessage_template == other.submessage_template and
            self._repeatable == other.repeatable)

  def __hash__(self):
    return hash((self._message_path,
                 self._yaml_path,
                 self._repeatable,
                 self.__str__()))

  @classmethod
  def FromYamlData(cls, msg_field, data):
    """Construct ApitoolsToKrmFieldDescriptor from a string or a dict."""
    msg_field = msg_field.strip()
    if isinstance(data, six.string_types):
      return cls(message_field=msg_field, yaml_field_path=data.strip())
    elif isinstance(data, dict):
      submsg_data = data.get('submessage_template')
      if submsg_data:
        submessage_template = collections.OrderedDict([
            (f, cls.FromYamlData(f, v)) for f, v in six.iteritems(submsg_data)
        ])
      else:
        submessage_template = None
      return cls(
          message_field=msg_field,
          yaml_field_path=data['yaml_path'].strip(),
          repeatable=data.get('repeatable', False),
          submessage_template=submessage_template)
    else:
      raise ValueError('Can not parse ApitoolsToKrmFieldDescriptor '
                       'for [{}] from data: [{}]'.format(msg_field, data))


class ApitoolsToKrmConfigObject(file_parsers.YamlConfigObject):
  """Abstraction for an Apitools to KRM Mapping file object."""

  def __init__(self, content):
    if not isinstance(content, dict):
      raise file_parsers.YamlConfigObjectError(
          'Invalid ApitoolsToKrmFieldDescriptor content')
    self._apitools_request = list(content.keys())[0]
    self._content = content[self._apitools_request]

  @property
  def apitools_request(self):
    return self._apitools_request

  def __str__(self):
    return '{}:\n{}'.format(self.apitools_request,
                            super(ApitoolsToKrmConfigObject, self).__str__())


def GenerateMessageMappingFromList(field_mapping_list):
  """Build message mapping from a list of ApitoolsToKrmFieldDescriptors."""
  return collections.OrderedDict(
      [(x.message_field, x) for x in field_mapping_list])


def GenerateMessageMappingFromFile(input_file):
  """Build apitools to krm mapping from a YAML/JSON File."""
  config_file = file_parsers.YamlConfigFile(ApitoolsToKrmConfigObject,
                                            file_path=input_file)
  config_data = config_file.data[0]
  ValidateMessageMappingFile(config_data.content)
  request_type = config_data.apitools_request
  mapping = collections.OrderedDict()
  for msg_field, value in six.iteritems(config_data):
    mapping[msg_field] = ApitoolsToKrmFieldDescriptor.FromYamlData(msg_field,
                                                                   value)
  return request_type, mapping


class MissingRequiredError(exceptions.Error):
  """Thrown when a required field is missing from input data."""


class InvalidDataError(exceptions.Error):
  """Thrown when mapped fields do not exists in input data."""


def _ParseFieldValue(message_field, value):
  """Parse input value into valid apitools field value."""
  if message_field.variant == messages.Variant.ENUM:
    return message_field.type.lookup_by_name(value)
  else:
    return value


def _MapDictToApiToolsMessage(data, mapping, message):
  """Helper function to do actual KRM to Apitools Mapping."""
  actual_fields = set()
  for field, descriptor in six.iteritems(mapping):
    if file_parsers.FindOrSetItemInDict(data, descriptor.yaml_path):
      actual_fields.add(field)

  if not actual_fields:
    raise InvalidDataError('Input YAML contains no message data')

  output_data = {}
  for field in sorted(message.all_fields(), key=lambda x: x.name):
    if field.name not in actual_fields:  # Skip fields we don't have data for.
      continue
    mapping_descriptor = mapping[field.name]
    value = file_parsers.FindOrSetItemInDict(data, mapping_descriptor.yaml_path)
    # Field is a sub-message, recursively generate it.
    if field.variant == messages.Variant.MESSAGE:
      if field.repeated:
        value = value if yaml.list_like(value) else [value]
        sub_message = []
        for item in value:
          sub_message.append(ParseMessageFromDict(
              item, mapping_descriptor.submessage_template, field.type))
      else:
        sub_message = ParseMessageFromDict(
            value, mapping_descriptor.submessage_template, field.type)
      if sub_message:
        # Only set the sub-message if we have something to put in it.
        output_data[field.name] = sub_message
    # Field is a scalar, just get the value.
    else:
      if field.repeated:  # If it is repeated, may be a repeated object
        if yaml.list_like(value):
          output_data[field.name] = [_ParseFieldValue(field, x) for x in value]
        else:
          output_data[field.name] = [_ParseFieldValue(field, value)]
      else:
        output_data[field.name] = _ParseFieldValue(field, value)
  return message(**output_data)


def GetMappingSchema():
  """Return the mapping YAML schema used to validate mapping files."""
  return (os.path.join(os.path.dirname(__file__),
                       'mappings', 'krm_mapping_schema.yaml'))


def ValidateMessageMappingFile(file_data):
  """Mapping file against krm mapping schema.

  Args:
    file_data: YAMLObject, parsed mapping file data.

  Raises:
    IOError: if schema not found in installed resources.
    ValidationError: if the template doesn't obey the schema.
  """
  validator = yaml_validator.Validator(GetMappingSchema())
  validator.ValidateWithDetailedError(file_data)


def ParseMessageFromDict(data, mapping, message, additional_fields=None):
  """Recursively generates the request message and any sub-messages.

  Args:
      data: {string: string}, A YAML like object containing the message data.
      mapping: {string: ApitoolsToKrmFieldDescriptor}, A mapping from message
        field names to mapping descriptors.
      message: The apitools class for the message.
      additional_fields: {string: object}, Additional fields to set in the
        message that are not mapped from data. Including calculated
        fields and static values.

  Returns:
    The instantiated apitools Message with all fields populated from data.

  Raises:
    InvalidDataError: If mapped fields do not exists in data.
  """

  output_message = _MapDictToApiToolsMessage(data, mapping, message)
  if additional_fields:
    for field_path, value in six.iteritems(additional_fields):
      arg_utils.SetFieldInMessage(output_message, field_path, value)

  return output_message


def BuildMessageFromKrmData(krm_data, field_mappings,
                            collection, request_method,
                            api_version=None, static_fields=None):
  """Build a Apitools message for specified method from KRM Yaml.

  Args:
      krm_data: {string: string}, A YAML like object containing the
        message data.
      field_mappings: {string: ApitoolsToKrmFieldDescriptor}, A mapping from
        message field names to mapping descriptors.
      collection: The resource collection of the requests method. Together with
        request_method, determine the actual message to generate.
      request_method: The api method whose request message we want to generate.
      api_version: Version of the api to retrieve the message type from. If None
        will use default API version.
      static_fields: {string: object}, Additional fields to set in the
        message that are not mapped from data. Including calculated fields
        and static values.

  Returns:
    The instantiated apitools Message with all fields populated from data.
  """
  method = registry.GetMethod(collection, request_method, api_version)
  request_class = method.GetRequestType()
  return ParseMessageFromDict(krm_data,
                              field_mappings,
                              request_class,
                              additional_fields=static_fields)


def _BuildYamlMappingTemplateFromMessage(message_cls):
  """Create a stub Apitools To KRM mapping object from a message object."""
  mapping_object = collections.OrderedDict()
  for field in sorted(message_cls.all_fields(), key=lambda x: x.name):
    if field.variant == messages.Variant.MESSAGE:
      fld_map = collections.OrderedDict()
      fld_map['yaml_path'] = _YAML_MAPPING_PLACEHOLDER
      if field.repeated:
        fld_map['repeatable'] = True
      fld_map['submessage_template'] = _BuildYamlMappingTemplateFromMessage(
          message_cls=field.type)
      mapping_object[field.name] = fld_map
    else:
      if field.repeated:
        fld_map = collections.OrderedDict()
        fld_map['yaml_path'] = _YAML_MAPPING_PLACEHOLDER
        fld_map['repeatable'] = True
        mapping_object[field.name] = fld_map
      else:
        mapping_object[field.name] = _YAML_MAPPING_PLACEHOLDER

  return mapping_object


def GenerateMappingFileTemplate(api_name, message_type, skip_fields=None,
                                file_path=None, api_version=None,
                                known_mappings=None):
  """Create a stub Apitools To KRM mapping file for specified Apitools message.

  Args:
      api_name: string, The api containing the message.
      message_type: string, The message to generate mapping for.
      skip_fields: [string], A list of field paths to exclude from mapping file.
      file_path: string, path of destination file. If None, will write result to
        stdout.
      api_version: Version of the api to retrieve the message type from. If None
        will use default API version.
      known_mappings: {string: object}, Fields to pre-initialize in the mapping.

  Returns:
    The path to the created file or file contents if no path specified.
  Raises:
    InvalidDataError, if api or message are invalid.
  """
  try:
    api_obj = registry.GetAPI(api_name, api_version)
    all_messages = api_obj.GetMessagesModule()
    message = getattr(all_messages, message_type)
    mapping_object = _BuildYamlMappingTemplateFromMessage(message)

    if skip_fields:  # Remove Skipped/Unmapped message fields
      for path in skip_fields:
        file_parsers.DeleteItemInDict(mapping_object, path)

    if known_mappings:
      for path, value in six.iteritems(known_mappings):
        file_parsers.FindOrSetItemInDict(mapping_object, path, set_value=value)

    yaml.convert_to_block_text(mapping_object)
    output = yaml.dump(mapping_object, round_trip=True)

    if file_path:
      files.WriteFileAtomically(file_path, output)
      output = file_path

    return output
  except (AttributeError, registry.Error) as ae:
    raise InvalidDataError('Error retrieving message [{message}] from '
                           'API [{api}/{ver}] :: {error}'.format(
                               message=message_type,
                               api=api_name,
                               ver=api_version or 'default',
                               error=ae))
