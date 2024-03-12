# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Utilities for creating/parsing update resource argument groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import util as format_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import update_args
from googlecloudsdk.command_lib.util.apis import yaml_command_schema_util as util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import resources


# TODO(b/280653078) The UX is still under review. These utilities are
# liable to change and should not be used in new surface yet.

# TODO(b/283949482): Place this file in util/args and replace the duplicate
# logic in the util files.


def _GetRelativeNameField(arg_data):
  """Gets message field where the resource's relative name is mapped."""
  api_fields = [
      key
      for key, value in arg_data.resource_method_params.items()
      if util.REL_NAME_FORMAT_KEY in value
  ]
  if not api_fields:
    return None

  return api_fields[0]


def _GetAllSharedAttributes(arg_data, shared_resource_args):
  """Gets a list of all shared resource attributes."""
  if not shared_resource_args:
    ignored_attributes = set()
  else:
    ignored_attributes = set(shared_resource_args)

  # iterate through all attributes except the anchor
  for a in arg_data.attribute_names[:-1]:
    if a in arg_data.removed_flags or concepts.IGNORED_FIELDS.get(a):
      continue
    ignored_attributes.add(a)

  return list(ignored_attributes)


def _GetResourceArgGenerator(
    arg_data, resource_collection, shared_resource_args):
  """Gets a function to generate a resource arg."""
  ignored_attributes = _GetAllSharedAttributes(arg_data, shared_resource_args)
  def ArgGen(name, group_help):
    group_help += '\n\n'
    if arg_data.group_help:
      group_help += arg_data.group_help

    return arg_data.GenerateResourceArg(
        resource_collection, name, ignored_attributes, group_help=group_help)
  return ArgGen


class UpdateResourceArgumentGenerator(update_args.UpdateArgumentGenerator):
  """Update flag generator for resource args."""

  @classmethod
  def FromArgData(
      cls, arg_data, resource_collection, is_list_method=False,
      shared_resource_args=None
  ):
    if arg_data.repeated:
      gen_cls = UpdateListResourceArgumentGenerator
    else:
      gen_cls = UpdateDefaultResourceArgumentGenerator

    arg_name = arg_data.GetAnchorArgName(resource_collection, is_list_method)
    is_primary = arg_data.IsPrimaryResource(resource_collection)
    if is_primary:
      raise util.InvalidSchemaError(
          '{} is a primary resource. Primary resources are required and '
          'cannot be listed as clearable.'.format(arg_name)
      )

    api_field = _GetRelativeNameField(arg_data)
    if not api_field:
      raise util.InvalidSchemaError(
          '{} does not specify the message field where the relative name is '
          'mapped in resource_method_params. Message field name is needed '
          'in order add update args. Please update '
          'resource_method_params.'.format(arg_name)
      )

    return gen_cls(
        arg_name=arg_name,
        arg_gen=_GetResourceArgGenerator(
            arg_data, resource_collection, shared_resource_args),
        api_field=api_field,
        repeated=arg_data.repeated,
        collection=arg_data.collection,
        is_primary=is_primary,
        attribute_flags=arg_utils.GetAttributeFlags(
            arg_data, arg_name, resource_collection, shared_resource_args),
    )

  def __init__(
      self,
      arg_name,
      arg_gen=None,
      is_hidden=False,
      api_field=None,
      repeated=False,
      collection=None,
      is_primary=None,
      attribute_flags=None,
  ):
    super(UpdateResourceArgumentGenerator, self).__init__()
    self.arg_name = format_util.NormalizeFormat(arg_name)
    self.arg_gen = arg_gen
    self.is_hidden = is_hidden
    self.api_field = api_field
    self.repeated = repeated
    self.collection = collection
    self.is_primary = is_primary
    self.attribute_flags = attribute_flags

  def _CreateResourceFlag(self, flag_prefix=None, group_help=None):
    flag_name = arg_utils.GetFlagName(
        self.arg_name, flag_prefix=flag_prefix and flag_prefix.value)
    return self.arg_gen(flag_name, group_help=group_help)

  def _RelativeName(self, value):
    return resources.REGISTRY.ParseRelativeName(
        value, self.collection.full_name)

  def GetArgFromNamespace(self, namespace, arg):
    """Retrieves namespace value associated with flag.

    Args:
      namespace: The parsed command line argument namespace.
      arg: base.Argument|concept_parsers.ConceptParser|None, used to get
        namespace value

    Returns:
      value parsed from namespace
    """
    if isinstance(arg, base.Argument):
      return arg_utils.GetFromNamespace(namespace, arg.name)

    if isinstance(arg, concept_parsers.ConceptParser):
      all_anchors = list(arg.specs.keys())
      if len(all_anchors) != 1:
        raise ValueError(
            'ConceptParser must contain exactly one spec for clearable '
            'but found specs {}. {} cannot parse the namespace value if more '
            'than or less than one spec is added to the '
            'ConceptParser.'.format(all_anchors, type(self).__name__))
      name = all_anchors[0]
      value = arg_utils.GetFromNamespace(namespace.CONCEPTS, name)
      if value:
        value = value.Parse()
      return value

    return None

  def GetFieldValueFromMessage(self, existing_message):
    value = arg_utils.GetFieldValueFromMessage(existing_message, self.api_field)
    if not value:
      return None

    if isinstance(value, list):
      return [self._RelativeName(v) for v in value]
    return self._RelativeName(value)

  def Generate(self):
    return super(UpdateResourceArgumentGenerator, self).Generate(
        self.attribute_flags)


class UpdateDefaultResourceArgumentGenerator(UpdateResourceArgumentGenerator):
  """Update flag generator for resource args."""

  @property
  def _empty_value(self):
    return None

  @property
  def set_arg(self):
    return self._CreateResourceFlag(
        group_help='Set {} to new value.'.format(self.arg_name))

  @property
  def clear_arg(self):
    return self._CreateFlag(
        self.arg_name,
        flag_prefix=update_args.Prefix.CLEAR,
        action='store_true',
        help_text='Clear {} value and set to {}.'.format(
            self.arg_name, self._GetTextFormatOfEmptyValue(self._empty_value)),
    )

  def ApplySetFlag(self, output, set_val):
    if set_val:
      return set_val
    return output

  def ApplyClearFlag(self, output, clear_flag):
    if clear_flag:
      return self._empty_value
    return output


class UpdateListResourceArgumentGenerator(UpdateResourceArgumentGenerator):
  """Update flag generator for list resource args."""

  @property
  def _empty_value(self):
    return []

  @property
  def set_arg(self):
    return self._CreateResourceFlag(
        group_help='Set {} to new value.'.format(self.arg_name))

  @property
  def clear_arg(self):
    return self._CreateFlag(
        self.arg_name,
        flag_prefix=update_args.Prefix.CLEAR,
        action='store_true',
        help_text='Clear {} value and set to {}.'.format(
            self.arg_name, self._GetTextFormatOfEmptyValue(self._empty_value)),
    )

  @property
  def update_arg(self):
    return self._CreateResourceFlag(
        flag_prefix=update_args.Prefix.ADD,
        group_help='Add new value to {} list.'.format(self.arg_name))

  @property
  def remove_arg(self):
    return self._CreateResourceFlag(
        flag_prefix=update_args.Prefix.REMOVE,
        group_help='Remove value from {} list.'.format(self.arg_name))

  def ApplySetFlag(self, output, set_val):
    if set_val:
      return set_val
    return output

  def ApplyClearFlag(self, output, clear_flag):
    if clear_flag:
      return self._empty_value
    return output

  def ApplyRemoveFlag(self, existing_val, remove_val):
    value = existing_val or self._empty_value
    if remove_val:
      return [x for x in value if x not in remove_val]
    else:
      return value

  def ApplyUpdateFlag(self, existing_val, update_val):
    value = existing_val or self._empty_value
    if update_val:
      return existing_val + [x for x in update_val if x not in value]
    else:
      return value

