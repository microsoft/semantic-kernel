# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Classes to define multitype concept specs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.calliope.concepts import deps_map_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


class Error(exceptions.Error):
  """Base class for errors in this module."""


class ConfigurationError(Error):
  """Raised if the spec is misconfigured."""


class ConflictingTypesError(Error):
  """Raised if there are multiple or no possible types for the spec."""

  def __init__(
      self, name, concept_specs, specified_attributes, fallthroughs_map):
    attributes = _GetAttrStr(specified_attributes)
    directions = _GetDirections(name, fallthroughs_map, concept_specs)
    message = (f'Failed to determine type of [{name}] resource. '
               f'You specified attributes [{attributes}].\n{directions}')
    super(ConflictingTypesError, self).__init__(message)


class InitializationError(concepts.InitializationError):
  """Raised if a spec fails to initialize."""

  def __init__(
      self, name, concept_specs, specified_attributes, fallthroughs_map):
    attributes = _GetAttrStr(specified_attributes)
    directions = _GetDirections(name, fallthroughs_map, concept_specs)
    super(InitializationError, self).__init__(
        (f'[{name}] resource missing required data. '
         f'You specified attributes [{attributes}].\n{directions}'))


class MultitypeResourceSpec(concepts.ConceptSpec):
  """A concept spec that can have multiple possible types.

  Creating a multitype concept spec requires a name and a list of
  concept specs. For example, to create a spec out of two other specs, a
  project_foo_spec and an organization_foo_spec:

    proj_org_foo_spec = MultitypeResourceSpec(
        'projorgfoo', project_foo_spec, organization_foo_spec)

  The command should parse the concept in the same way as always, obtaining a
  TypedConceptResult:

    result = args.CONCEPTS.proj_org_foo.Parse()

  To check the type of the result and use it, the user might do:

    if result.concept_type == type(result.concept_type).PROJFOO:
      _HandleProjectResource(result.result)
    else:
     _HandleOrgResource(result.result)

  Attributes:
    name: str, the name of the concept
    plural_name: str, the pluralized name. Will be pluralized by default rules
      if not given in cases where the resource is referred to in the plural.
    attributes: [concepts._Attribute], a list of attributes of the concept.
    type_enum: enum.Enum, an Enum class representing the available types.
  """

  def __init__(self, name, *concept_specs, **kwargs):
    self._name = name
    self._plural_name = kwargs.get('plural_name', None)
    self._allow_inactive = kwargs.get('allow_inactive', False)
    self._concept_specs = concept_specs
    self._attributes = []
    self._attribute_to_types_map = {}
    self.disable_auto_completers = True

    self._name_to_concepts = {}
    final_names = []
    for concept_spec in self._concept_specs:
      name = self._GetUniqueNameForSpec(concept_spec, final_names)
      final_names.append(name)
      self._name_to_concepts[name] = concept_spec

    self.type_enum = enum.Enum('Type', final_names)

    attr_map = {}
    for spec in self._concept_specs:
      for i, attribute in enumerate(spec.attributes):
        attr_name = attribute.name
        if attr_name in attr_map and attribute != attr_map[attr_name][1]:
          raise ConfigurationError(
              'Multiple non-equivalent attributes found with name '
              f'[{attribute.name}]')
        attr_map[attr_name] = (i, attribute)

        self._attribute_to_types_map.setdefault(attr_name, []).append(
            (self.type_enum[self._ConceptToName(spec)]))

    attr_list = sorted(list(attr_map.values()), key=lambda x: x[0])
    self._attributes = [attr[1] for attr in attr_list]
    self._anchor = self._GetAnchor()

  @property
  def name(self):
    return self._name

  @property
  def attributes(self):
    return self._attributes

  @property
  def anchor(self):
    return self._anchor

  def _GetAnchor(self):
    leaf_anchors = set(
        attr for attr in self.attributes if self.IsLeafAnchor(attr))
    if len(leaf_anchors) != 1:
      anchor_names = ', '.join([attr.name for attr in leaf_anchors])
      raise ConfigurationError(
          'Could not find single achor value for multitype resource. '
          f'Resource {self.name} has multiple leaf anchors: [{anchor_names}].')
    return leaf_anchors.pop()

  def IsAnchor(self, attribute):
    """Returns True if attribute is an anchor in at least one concept."""
    return any(attribute == spec.anchor for spec in self._concept_specs)

  def IsLeafAnchor(self, attribute):
    """Returns True if attribute is an anchor in at least one concept.

    Attribute can only be a leaf anchor if it is an anchor for at least
    one concept AND not an attribute in any other resource.

    Args:
      attribute: concepts.Attribute, attribute we are checking

    Returns:
      bool, whether attribute is a leaf anchor
    """
    if not self.IsAnchor(attribute):
      return False
    # Not a leaf if it's a non-anchor attribute in at least one spec.
    if any(attribute in spec.attributes and attribute.name != spec.anchor.name
           for spec in self._concept_specs):
      return False
    return True

  def Pluralize(self, attribute, plural=False):
    return plural and self.IsLeafAnchor(attribute)

  def Initialize(self, full_fallthroughs_map, parsed_args=None):
    """Generates a parsed resource based on fallthroughs and user input.

    Determines which attributes are actively specified (i.e. on the command
    line) in order to determine which type of concept is being specified by the
    user. The rules are:
      1) If *exactly one* concept spec can be initialized using ALL explicilty
         specified attributes, return it.
      2) If *exactly one* concept spec can be initialized using ALL explicilty
         specified attributes and some non-active attributes, return it.
      3) If more than one concept spec can be initialized using ALL
         explicitly specified attributes, prompt user or emit
         ConflictingTypesError
      4) If no concept specs can be initialized, emit IntitializationError

    Args:
      full_fallthroughs_map: {str: [deps_lib._FallthroughBase]}, a dict of
        finalized fallthroughs for the resource.
      parsed_args: the argparse namespace.

    Returns:
      A TypedConceptResult that stores the type of the parsed concept and the
        raw parsed concept (such as a resource reference).

    Raises:
      InitializationError: if the concept's attributes are underspecified and
        cannot be initialized from data.
      ConflictingTypesError: if more than one possible type exists.
    """
    active_fallthroughs_map = {
        attr: [f for f in fallthroughs if f.active]
        for attr, fallthroughs in full_fallthroughs_map.items()
    }
    actively_specified = self._GetSpecifiedAttributes(
        active_fallthroughs_map, parsed_args=parsed_args)

    # (1) Try to determine if one resource can be parsed from actively
    # specified attributes. No extra attributes can be actively specifed.
    actively_specified_resources = self._FilterTypesByAttribute(
        actively_specified,
        self._GetParsedResources(active_fallthroughs_map, parsed_args))
    if len(actively_specified_resources) == 1:
      return actively_specified_resources[0]

    # (2) Determine if any resource can be parsed from active and inactive
    # fallthroughs. No extra attributes can be actively specified.
    all_specified = self._GetSpecifiedAttributes(
        full_fallthroughs_map, parsed_args=parsed_args)
    parsed_resources = self._GetParsedResources(
        full_fallthroughs_map, parsed_args)
    if not parsed_resources:
      raise InitializationError(
          self.name, self._concept_specs, all_specified,
          full_fallthroughs_map)

    # Only filter out types that have too many actively specified attributes
    specified_resources = self._FilterTypesByAttribute(
        actively_specified, parsed_resources)
    if len(specified_resources) == 1:
      return specified_resources[0]
    else:
      return self._PromptOrErrorConflictingTypes(
          all_specified, full_fallthroughs_map, parsed_resources)

  def Parse(self, attribute_to_args_map, base_fallthroughs_map,
            parsed_args=None, plural=False, allow_empty=False):
    """Lazy parsing function for resource.

    Generates resource based off of the parsed_args (user provided
    arguments) and specified fallthrough behavior.

    Args:
      attribute_to_args_map: {str: str}, A map of attribute names to the names
        of their associated flags.
      base_fallthroughs_map: {str: [deps_lib.Fallthrough]} A map of attribute
        names to non-argument fallthroughs, including command-level
        fallthroughs.
      parsed_args: the parsed Namespace.
      plural: bool, True if multiple resources can be parsed, False otherwise.
      allow_empty: bool, True if resource parsing is allowed to return no
        resource, otherwise False.

    Returns:
      A TypedConceptResult or a list of TypedConceptResult objects containing
        the parsed resource or resources.

    Raises:
      ValueError: if fallthrough map contains invalid fallthrough order.
    """
    if base_fallthroughs_map:
      valid, msg = deps_map_util.ValidateFallthroughMap(base_fallthroughs_map)
      if not valid:
        raise ValueError(msg)

    if not plural:
      return self._ParseFromValue(
          attribute_to_args_map, base_fallthroughs_map,
          parsed_args, allow_empty)
    else:
      return self._ParseFromPluralValue(
          attribute_to_args_map, base_fallthroughs_map, parsed_args,
          allow_empty)

  def BuildFullFallthroughsMap(
      self, attribute_to_args_map, base_fallthroughs_map, parsed_args=None):
    """Generate fallthrough map that is used to resolve resource params.

    Used as source of truth for how each attribute is resolved. It is also used
    to generate help text for both plural and singular resources.
    Fallthroughs are a list of objects that, when called, try different ways of
    resolving a resource attribute (see googlecloudsdk.calliope.concepts.
    deps_lib._Fallthrough). This method builds a map from the name of each
    attribute to its list of fallthroughs.

    For each attribute, adds default flag fallthroughs and fully specified
    anchor fallthroughs.

    Args:
      attribute_to_args_map: {str: str}, A map of attribute names to the names
        of their associated flags.
      base_fallthroughs_map: {str: [deps.Fallthrough]}, A map of attribute
        names to non-argument fallthroughs, including command-level
        fallthroughs.
      parsed_args: Namespace | None, user's CLI input

    Returns:
      {str: [deps.Fallthrough]}, a map from attribute name to all its
      fallthroughs.
    """

    # For each concept, add a flag, value, or fully specified fallthrough.
    # deps_map_util automatically removes duplicated fallthroughs from
    # lower down the in the fallthrough list. For example, for attribute
    # location, if location is in more than one concept spec, it
    # will still only have one `--location` flag fallthrough in its
    # fallthrough list.
    fallthroughs_map = {**base_fallthroughs_map}

    # Add flag and value fallthroughs first
    for resource_spec in self._concept_specs:
      deps_map_util.AddFlagFallthroughs(
          fallthroughs_map, resource_spec.attributes, attribute_to_args_map)
      deps_map_util.UpdateWithValueFallthrough(
          fallthroughs_map, resource_spec.anchor.name, parsed_args)

    # Add fully specified fallthroughs to non-anchor params
    map_without_anchors = {**fallthroughs_map}
    for resource_spec in self._concept_specs:
      deps_map_util.AddAnchorFallthroughs(
          fallthroughs_map, resource_spec.attributes, resource_spec.anchor,
          resource_spec.collection_info,
          map_without_anchors.get(resource_spec.anchor.name, []))

    return fallthroughs_map

  def _BuildFullFallthroughsMapList(
      self, anchor, attribute_to_args_map, base_fallthroughs_map,
      parsed_args=None):
    """Builds fallthrough map for each anchor value specified in a list.

    For each anchor value parsed, create a falthrough map to derive the rest
    of the resource params. For each attribute, adds flag fallthroughs
    and fully specified anchor fallthroughs. For each attribute,
    adds default flag fallthroughs and fully specified anchor fallthroughs.

    Args:
      anchor: attributes.Anchor, the anchor attribute we are parsing
      attribute_to_args_map: {str: str}, A map of attribute names to the names
        of their associated flags.
      base_fallthroughs_map: FallthroughsMap, A map of attribute names to
        non-argument fallthroughs, including command-level fallthroughs.
      parsed_args: Namespace, used to parse the anchor value and derive
        fully specified fallthroughs.

    Returns:
      list[FallthroughsMap], fallthrough map for each anchor value
    """
    fallthroughs_map = {**base_fallthroughs_map}
    deps_map_util.AddFlagFallthroughs(
        fallthroughs_map, self.attributes, attribute_to_args_map)
    deps_map_util.PluralizeFallthroughs(fallthroughs_map, anchor.name)

    map_list = deps_map_util.CreateValueFallthroughMapList(
        fallthroughs_map, anchor.name, parsed_args)

    for full_map in map_list:
      for spec in self._concept_specs:
        if spec.anchor.name != anchor.name:
          continue
        deps_map_util.AddAnchorFallthroughs(
            full_map, spec.attributes, spec.anchor, spec.collection_info,
            full_map.get(spec.anchor.name, []))

    return map_list

  def _ParseFromValue(
      self, attribute_to_args_map, base_fallthroughs_map,
      parsed_args, allow_empty=False):
    """Parses a singular resource from user input."""
    fallthroughs_map = self.BuildFullFallthroughsMap(
        attribute_to_args_map, base_fallthroughs_map, parsed_args)
    try:
      return self.Initialize(fallthroughs_map, parsed_args=parsed_args)
    except InitializationError:
      if allow_empty:
        return TypedConceptResult(None, None)
      raise

  def _ParseFromPluralValue(
      self, attribute_to_args_map, base_fallthroughs_map,
      parsed_args, allow_empty=False):
    """Parses a list of resources from user input."""
    results = []
    for attribute in self.attributes:
      if self.IsLeafAnchor(attribute):
        results += self._ParseFromPluralLeaf(
            attribute_to_args_map, base_fallthroughs_map, attribute,
            parsed_args=parsed_args)
    if results:
      return results

    # If no resources were found from the "leaf" anchors, then we are looking
    # for a single parent resource (whose anchor is a non-"leaf" anchor).
    parent = self._ParseFromValue(
        attribute_to_args_map, base_fallthroughs_map, parsed_args,
        allow_empty=allow_empty)
    if parent.result is not None:
      return [parent]
    else:
      return []

  def _ParseFromPluralLeaf(
      self, attribute_to_args_map, base_fallthroughs_map, anchor, parsed_args):
    """Helper for parsing a list of results using a single anchor value."""
    parsed_resources = []
    map_list = self._BuildFullFallthroughsMapList(
        anchor, attribute_to_args_map, base_fallthroughs_map, parsed_args)
    for fallthroughs_map in map_list:
      resource = self.Initialize(
          fallthroughs_map, parsed_args=parsed_args)
      if resource.result is not None:
        parsed_resources.append(resource)

    return parsed_resources

  def _GetParsedResources(self, fallthroughs_map, parsed_args):
    """Helper method to get the parsed resources using actively specified args.
    """
    types = []
    for concept_type in self.type_enum:
      try:
        concept_spec = self._name_to_concepts[concept_type.name]
        parsed_resource = concept_spec.Initialize(
            fallthroughs_map, parsed_args=parsed_args)
        types.append(TypedConceptResult(parsed_resource, concept_type))
      except concepts.InitializationError:
        continue
    return types

  def _ConceptToName(self, concept_spec):
    """Helper to get the type enum name for a concept spec."""
    for name, spec in self._name_to_concepts.items():
      if spec == concept_spec:
        return name
    else:
      return None

  def _GetSpecifiedAttributes(self, fallthroughs_map, parsed_args=None):
    """Get a list of attributes that are actively specified in runtime."""
    specified = []
    for attribute in self.attributes:
      try:
        value = deps_lib.Get(
            attribute.name, fallthroughs_map, parsed_args=parsed_args)
      except deps_lib.AttributeNotFoundError:
        continue
      if value is not None:
        specified.append(attribute)
    return specified

  def _FilterTypesByAttribute(self, attribute_info, concept_result):
    """Fitlers out types that do not contain actively specified attribute."""
    possible_types = []
    for candidate in concept_result:
      for attribute in attribute_info:
        if candidate.concept_type not in self._attribute_to_types_map.get(
            attribute.name, []):
          break
      else:
        possible_types.append(candidate)
    return possible_types

  def _GetUniqueNameForSpec(self, resource_spec, final_names):
    """Overrides this functionality from generic multitype concept specs."""
    del final_names
    # If all resources have different names, use their names.
    resource_names = [spec.name for spec in self._concept_specs]
    if len(set(resource_names)) == len(resource_names):
      return resource_spec.name
    # Otherwise, use the collection name.
    other_collection_names = [
        spec.collection for spec in self._concept_specs]
    other_collection_names.pop(self._concept_specs.index(resource_spec))
    if any(resource_spec.collection == n for n in other_collection_names):
      raise ValueError('Attempting to create a multitype spec with duplicate '
                       'collections. Collection name: [{}]'.format(
                           resource_spec.collection))
    else:
      return resource_spec.collection

  def _PromptOrErrorConflictingTypes(
      self, specified_attributes, full_fallthroughs_map, parsed_resources):
    """If one or more type is parsed, send prompt for user to confirm.

    If user is unable to confirm resource type, raise ConflictingTypesError

    Args:
      specified_attributes: list[Attribute], list of explicitly specified
        resource attributes
      full_fallthroughs_map: {str: [deps_lib._FallthroughBase]}, a dict of
        finalized fallthroughs for the resource.
      parsed_resources: list[TypedConceptResult], list of parsed resources

    Returns:
      concepts.Resource, resource user elects to specify

    Raises:
      ConflictingTypesError: if user is not able to specify preferred resource.
    """
    if not console_io.CanPrompt():
      raise ConflictingTypesError(
          self.name, self._concept_specs, specified_attributes,
          full_fallthroughs_map)

    guess_list = [guess.result.RelativeName() for guess in parsed_resources]
    attr_str = _GetAttrStr(specified_attributes)

    try:
      selected_index = console_io.PromptChoice(
          guess_list,
          message=(f'Failed determine type of [{self.name}] resource. '
                   f'You specified attributes [{attr_str}].\n'
                   'Did you mean to specify one of the following resources?'),
          prompt_string=('Please enter your numeric choice. Defaults to'),
          cancel_option=True,
          default=len(guess_list))  # default to cancel option
    except console_io.OperationCancelledError:
      raise ConflictingTypesError(
          self.name, self._concept_specs, specified_attributes,
          full_fallthroughs_map)

    return parsed_resources[selected_index]


class TypedConceptResult(object):
  """A small wrapper to hold the results of parsing a multityped concept."""

  def __init__(self, result, concept_type):
    """Initializes.

    Args:
      result: the parsed concept, such as a resource reference.
      concept_type: the enum value of the type of the result.
    """
    self.result = result
    self.concept_type = concept_type


def _GetAttrStr(attributes):
  """Helper to format a list of attributes into a string."""
  return ', '.join([attr.name for attr in attributes])


def _GetDirections(name, full_fallthroughs_map, concept_specs):
  """Aggregates directions on how to specify each type of resource."""
  directions = []
  for spec in concept_specs:
    attribute_directions = _GetAttributeDirections(
        spec.attributes, full_fallthroughs_map)
    directions.append(
        f'\nTo specify [{name}] as type {spec.collection}, specify only '
        f'the following attributes.')
    directions.append(attribute_directions)

  return '\n\n'.join(directions)


def _GetAttributeDirections(attributes, full_fallthroughs_map):
  """Aggregates directions on how to set resource attribute."""
  directions = []
  for i, attribute in enumerate(attributes):
    fallthroughs = full_fallthroughs_map.get(attribute.name, [])
    tab = ' ' * 4

    to_specify = (f'{i + 1}. To provide [{attribute.name}] attribute, do one '
                  'of the following:')
    hints = (f'\n{tab}- {hint}' for hint in deps_lib.GetHints(fallthroughs))
    directions.append(to_specify + ''.join(hints))

  return '\n\n'.join(directions)
