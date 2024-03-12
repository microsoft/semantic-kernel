# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Cloud Datacatalog tags client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import times

import six

VERSION = 'v1'


class InvalidTagError(exceptions.Error):
  """Error if a schema is improperly specified."""


class InvalidTagFileError(exceptions.Error):
  """Error if a tag file is not valid JSON or YAML."""


class TagsClient(object):
  """Cloud Datacatalog tags client."""

  def __init__(self):
    self.client = util.GetClientInstance(VERSION)
    self.messages = util.GetMessagesModule(VERSION)
    self.template_service = self.client.projects_locations_tagTemplates

  def ParseCreateTagArgsIntoRequest(self, args, request):
    """Parses tag-templates create args into the request."""
    tag_template_ref = args.CONCEPTS.tag_template.Parse()
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1Tag.template',
        tag_template_ref.RelativeName())
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1Tag.fields',
        self._ProcessTagFromFile(tag_template_ref, args.tag_file))
    return request

  def ParseUpdateTagArgsIntoRequest(self, args, request):
    """Parses tag-templates update args into the request."""
    tag_template_ref = args.CONCEPTS.tag_template.Parse()
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1Tag.template',
        tag_template_ref.RelativeName())
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1Tag.fields',
        self._ProcessTagFromFile(tag_template_ref, args.tag_file))
    return request

  def _ProcessTagFromFile(self, tag_template_ref, tag_file):
    """Processes a tag file into the request."""
    try:
      tag = yaml.load_path(tag_file)
      if not isinstance(tag, dict):
        raise InvalidTagFileError('Error parsing tag file: [invalid format]')
    except yaml.YAMLParseError as e:
      raise InvalidTagFileError(
          'Error parsing tag file: [{}]'.format(e))

    tag_template = self.template_service.Get(
        self.messages.DatacatalogProjectsLocationsTagTemplatesGetRequest(
            name=tag_template_ref.RelativeName(),
        )
    )
    field_to_field_type = {}
    for additional_property in tag_template.fields.additionalProperties:
      message_type = additional_property.value.type
      field_to_field_type[additional_property.key] = (
          self._GetFieldType(message_type))

    additional_properties = []
    for field_id, field_value in six.iteritems(tag):
      if field_id not in field_to_field_type:
        raise InvalidTagError(
            'Error parsing tag file: [{}] is not a valid field.'
            .format(field_id))
      additional_properties.append(
          self.messages.GoogleCloudDatacatalogV1Tag.FieldsValue
          .AdditionalProperty(
              key=field_id,
              value=self._MakeTagField(field_to_field_type[field_id],
                                       field_value),
          )
      )

    return self.messages.GoogleCloudDatacatalogV1Tag.FieldsValue(
        additionalProperties=additional_properties,
    )

  def _GetFieldType(self, message_type):
    """Get a field type from a type."""
    primitive_type_enum = (
        self.messages.GoogleCloudDatacatalogV1FieldType
        .PrimitiveTypeValueValuesEnum
    )
    primitive_types = {
        primitive_type_enum.DOUBLE: 'double',
        primitive_type_enum.STRING: 'string',
        primitive_type_enum.BOOL: 'bool',
        primitive_type_enum.TIMESTAMP: 'timestamp',
    }
    if message_type.primitiveType:
      if message_type.primitiveType in primitive_types:
        return primitive_types[message_type.primitiveType]
    elif message_type.enumType:
      return 'enum'

    raise ValueError('Unknown field type in message {}'.format(message_type))

  def _MakeTagField(self, field_type, field_value):
    """Create a tag field."""
    value = self.messages.GoogleCloudDatacatalogV1TagField()
    if field_type == 'double':
      value.doubleValue = field_value
    elif field_type == 'string':
      value.stringValue = field_value
    elif field_type == 'bool':
      value.boolValue = field_value
    elif field_type == 'timestamp':
      try:
        value.timestampValue = times.FormatDateTime(
            times.ParseDateTime(field_value))
      except times.Error as e:
        raise InvalidTagError('Invalid timestamp value: {} [{}]'.format(
            e, field_value))
    elif field_type == 'enum':
      value.enumValue = (
          self.messages.GoogleCloudDatacatalogV1TagFieldEnumValue(
              displayName=field_value,
          ))
    else:
      raise ValueError('Unknown field type: [{}]'.format(field_type))
    return value
