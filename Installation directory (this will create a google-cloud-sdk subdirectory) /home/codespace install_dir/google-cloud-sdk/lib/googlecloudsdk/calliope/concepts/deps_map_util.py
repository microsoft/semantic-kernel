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
"""Utilities for generating and updating fallthrough maps."""

import copy

from googlecloudsdk.calliope.concepts import deps as deps_lib


def AddFlagFallthroughs(
    base_fallthroughs_map, attributes, attribute_to_args_map):
  """Adds flag fallthroughs to fallthrough map.

  Iterates through each attribute and prepends a flag fallthrough.
  This allows resource attributes to be resolved to flag first. For example:

    {'book': [deps.ValueFallthrough('foo')]}

  will update to something like...

    {
        'book': [
            deps.ArgFallthrough('--foo'),
            deps.ValueFallthrough('foo')
        ]
    }

  Args:
    base_fallthroughs_map: {str: [deps._FallthroughBase]}, A map of attribute
      names to fallthroughs
    attributes: list[concepts.Attribute], list of attributes associated
      with the resource
    attribute_to_args_map: {str: str}, A map of attribute names to the names
      of their associated flags.
  """
  for attribute in attributes:
    current_fallthroughs = base_fallthroughs_map.get(attribute.name, [])

    if arg_name := attribute_to_args_map.get(attribute.name):
      arg_fallthrough = deps_lib.ArgFallthrough(arg_name)
    else:
      arg_fallthrough = None

    if arg_fallthrough:
      filtered_fallthroughs = [
          f for f in current_fallthroughs if f != arg_fallthrough]
      fallthroughs = [arg_fallthrough] + filtered_fallthroughs
    else:
      fallthroughs = current_fallthroughs
    base_fallthroughs_map[attribute.name] = fallthroughs


def AddAnchorFallthroughs(
    base_fallthroughs_map, attributes, anchor, collection_info,
    anchor_fallthroughs):
  """Adds fully specified fallthroughs to fallthrough map.

  Iterates through each attribute and prepends a fully specified fallthrough.
  This allows resource attributes to resolve to the fully specified anchor
  value first. For example:

    {'book': [deps.ValueFallthrough('foo')]}

  will udpate to something like...

    {
        'book': [
            deps.FullySpecifiedAnchorFallthrough(anchor_fallthroughs),
            deps.ValueFallthrough('foo')
        ]
    }

  Args:
    base_fallthroughs_map: {str: [deps._FallthroughBase]}, A map of attribute
      names to fallthroughs
    attributes: list[concepts.Attribute], list of attributes associated
      with the resource
    anchor: concepts.Attribute, attribute that the other attributes should
      resolve to if fully specified
    collection_info: the info of the collection to parse the anchor as
    anchor_fallthroughs: list[deps._FallthroughBase], fallthroughs used to
      resolve the anchor value
  """
  for attribute in attributes:
    current_fallthroughs = base_fallthroughs_map.get(attribute.name, [])
    anchor_based_fallthrough = deps_lib.FullySpecifiedAnchorFallthrough(
        anchor_fallthroughs, collection_info, attribute.param_name)

    if attribute != anchor:
      filtered_fallthroughs = [
          f for f in current_fallthroughs if f != anchor_based_fallthrough]
      fallthroughs = [anchor_based_fallthrough] + filtered_fallthroughs
    else:
      fallthroughs = current_fallthroughs
    base_fallthroughs_map[attribute.name] = fallthroughs


def UpdateWithValueFallthrough(
    base_fallthroughs_map, attribute_name, parsed_args):
  """Shortens fallthrough list to a single deps.ValueFallthrough.

  Used to replace the attribute_name entry in a fallthrough map to a
  single ValueFallthrough. For example:

    {'book': [deps.Fallthrough(lambda: 'foo')]}

  will update to something like...

    {'book': [deps.ValueFallthrough('foo')]}

  Args:
    base_fallthroughs_map: {str: [deps._FallthroughBase]}, A map of attribute
      names to fallthroughs we are updating
    attribute_name: str, entry in fallthrough map we are updating
    parsed_args: Namespace | None, used to derive the value for ValueFallthrough
  """
  if not parsed_args:
    return

  attribute_value, attribute_fallthrough = _GetFallthroughAndValue(
      attribute_name, base_fallthroughs_map, parsed_args)

  if attribute_fallthrough:
    _UpdateMapWithValueFallthrough(
        base_fallthroughs_map, attribute_value, attribute_name,
        attribute_fallthrough)


def CreateValueFallthroughMapList(
    base_fallthroughs_map, attribute_name, parsed_args):
  """Generates a list of fallthrough maps for each anchor value in a list.

  For each anchor value, generate a fallthrough map. For example, if user
  provides anchor values ['foo', 'bar'] and a base fallthrough like...

    {'book': [deps.ArgFallthrough('--book')]}

  will generate somehting like...

    [
        {'book': [deps.ValueFallthrough('foo')]},
        {'book': [deps.ValueFallthrough('bar')]}
    ]

  Args:
    base_fallthroughs_map: {str: [deps._FallthroughBase]}, A map of attribute
      names to fallthroughs we are updating
    attribute_name: str, entry in fallthrough map we are updating
    parsed_args: Namespace | None, used to derive the value for ValueFallthrough

  Returns:
    list[{str: deps._FallthroughBase}], a list of fallthrough maps for
    each parsed anchor value
  """
  attribute_values, attribute_fallthrough = _GetFallthroughAndValue(
      attribute_name, base_fallthroughs_map, parsed_args)

  map_list = []
  if not attribute_fallthrough:
    return map_list

  for value in attribute_values:
    new_map = {**base_fallthroughs_map}
    _UpdateMapWithValueFallthrough(
        new_map, value, attribute_name, attribute_fallthrough)
    map_list.append(new_map)
  return map_list


def PluralizeFallthroughs(base_fallthroughs_map, attribute_name):
  """Updates fallthrough map entry to make fallthroughs plural.

  For example:

    {'book': [deps.ArgFallthrough('--foo')]}

  will update to something like...

    {'book': [deps.ArgFallthrough('--foo'), plural=True]}

  Args:
    base_fallthroughs_map: {str: [deps.Fallthrough]}, A map of attribute
      names to fallthroughs we are updating
    attribute_name: str, entry in fallthrough map we are updating
  """
  given_fallthroughs = base_fallthroughs_map.get(attribute_name, [])

  base_fallthroughs_map[attribute_name] = [
      _PluralizeFallthrough(fallthrough)
      for fallthrough in given_fallthroughs
  ]


def _PluralizeFallthrough(fallthrough):
  plural_fallthrough = copy.deepcopy(fallthrough)
  plural_fallthrough.plural = True
  return plural_fallthrough


def _UpdateMapWithValueFallthrough(
    base_fallthroughs_map, value, attribute_name, attribute_fallthrough):
  value_fallthrough = deps_lib.ValueFallthrough(
      value,
      attribute_fallthrough.hint,
      active=attribute_fallthrough.active)
  base_fallthroughs_map[attribute_name] = [value_fallthrough]


def _GetFallthroughAndValue(attribute_name, fallthroughs_map, parsed_args):
  """Derives value and fallthrough used to derives value from map."""
  for possible_fallthrough in fallthroughs_map.get(attribute_name, []):
    try:
      value = possible_fallthrough.GetValue(parsed_args)
      return (value, possible_fallthrough)
    except deps_lib.FallthroughNotFoundError:
      continue
  else:
    return (None, None)


def ValidateFallthroughMap(fallthroughs_map):
  """Validates fallthrough map to ensure fallthrough map is not invalid.

  Fallthrough maps are only invalid if an inactive fallthrough comes before
  an active fallthrough. It could result in an active fallthrough that can
  never be reached.

  Args:
    fallthroughs_map: {str: [deps._FallthroughBase]}, A map of attribute
      names to fallthroughs we are validating

  Returns:
    (bool, str), bool for whether fallthrough map is valid and str for
      the error message
  """

  for attr, fallthroughs in fallthroughs_map.items():
    inactive_fallthrough = None
    for fallthrough in fallthroughs:
      if inactive_fallthrough and fallthrough.active:
        active_str = fallthrough.__class__.__name__
        inactive_str = inactive_fallthrough.__class__.__name__
        msg = (f'Invalid Fallthrough Map: Fallthrough map at [{attr}] contains '
               f'inactive fallthrough [{inactive_str}] before active '
               f'fallthrough [{active_str}]. Fix the order so that active '
               f'fallthrough [{active_str}] is reachable or remove active '
               f'fallthrough [{active_str}].')
        return False, msg

      if not fallthrough.active:
        inactive_fallthrough = fallthrough
    else:
      return True, None
