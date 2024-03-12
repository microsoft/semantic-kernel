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
"""Cloud Datacatalog tag templates client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.data_catalog import util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils


class TagTemplatesClient(object):
  """Cloud Datacatalog tag templates client."""

  def __init__(self):
    self.client = util.GetClientInstance()
    self.messages = util.GetMessagesModule()
    self.service = self.client.projects_locations_tagTemplates

  def ParseCreateTagTemplateArgsIntoRequest(self, args, request):
    """Parses tag-templates create args into the request."""
    fields = []
    for field in args.field:
      fields.append(self._ParseField(field))
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1beta1TagTemplate.fields',
        self.messages
        .GoogleCloudDatacatalogV1beta1TagTemplate.FieldsValue(
            additionalProperties=fields,
        ))
    return request

  def ParseCreateTagTemplateFieldArgsIntoRequest(self, args, request):
    """Parses tag-templates fields create args into the request."""
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1beta1TagTemplateField.type',
        self._ParseFieldType(args.type))
    return request

  def ParseUpdateTagTemplateFieldArgsIntoRequest(self, args, request):
    """Parses tag-templates fields update args into the request."""
    enum_values = []
    if args.IsSpecified('enum_values'):
      for value in args.enum_values:
        enum_values.append(self._MakeEnumValue(value))
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1beta1TagTemplateField.type',
        self.messages.GoogleCloudDatacatalogV1beta1FieldType(
            enumType=(
                self.messages.GoogleCloudDatacatalogV1beta1FieldTypeEnumType(
                    allowedValues=enum_values,
                )
            )
        ))
    return request

  def _ParseField(self, field):
    """Parses a field."""
    key = field['id']
    value = (
        self.messages
        .GoogleCloudDatacatalogV1beta1TagTemplateField(
            displayName=field.get('display-name', None),
            type=self._ParseFieldType(field['type']),
            isRequired=field.get('required', False),
        )
    )
    return (
        self.messages
        .GoogleCloudDatacatalogV1beta1TagTemplate.FieldsValue
        .AdditionalProperty(
            key=key,
            value=value)
    )

  def _ParseFieldType(self, field_type):
    """Parses a field type."""
    primitive_field_type_enum = (
        self.messages.GoogleCloudDatacatalogV1beta1FieldType
        .PrimitiveTypeValueValuesEnum
    )
    valid_primitive_type_mapping = {
        'double': primitive_field_type_enum.DOUBLE,
        'string': primitive_field_type_enum.STRING,
        'bool': primitive_field_type_enum.BOOL,
        'timestamp': primitive_field_type_enum.TIMESTAMP,
    }
    if field_type in valid_primitive_type_mapping:
      return self.messages.GoogleCloudDatacatalogV1beta1FieldType(
          primitiveType=valid_primitive_type_mapping[field_type],
      )
    else:
      enum_values = self._ParseEnumValues(field_type)
      if enum_values:
        return self.messages.GoogleCloudDatacatalogV1beta1FieldType(
            enumType=(
                self.messages.GoogleCloudDatacatalogV1beta1FieldTypeEnumType(
                    allowedValues=enum_values,
                )
            )
        )

    raise exceptions.InvalidArgumentException(
        '--field', field_type)

  def _ParseEnumValues(self, raw_enum_values):
    """Parses a raw enum value (e.g. 'enum(A|B|C)).

    Args:
      raw_enum_values: User-supplied definition of an enum

    Returns:
      DataCatalog FieldTypeEnumTypeEnumValue or none if a valid enum type wasn't
      not provided.
    """
    match = re.search(r'enum\((.*)\)', raw_enum_values, re.IGNORECASE)
    if not match:
      return None

    enum_values = []
    for enum in match.group(1).split('|'):
      enum_values.append(self._MakeEnumValue(enum))
    return enum_values

  def _MakeEnumValue(self, enum):
    """Make an enum value."""
    return (
        self.messages
        .GoogleCloudDatacatalogV1beta1FieldTypeEnumTypeEnumValue(
            displayName=enum,
        )
    )
