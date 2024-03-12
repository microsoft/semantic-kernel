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
"""Classes to define how concept args are added to argparse.

A PresentationSpec is used to define how a concept spec is presented in an
individual command, such as its help text. ResourcePresentationSpecs are
used for resource specs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import util
from googlecloudsdk.command_lib.util.concepts import info_holders


class PresentationSpec(object):
  """Class that defines how concept arguments are presented in a command.

  Attributes:
    name: str, the name of the main arg for the concept. Can be positional or
      flag style (UPPER_SNAKE_CASE or --lower-train-case).
    concept_spec: googlecloudsdk.calliope.concepts.ConceptSpec, The spec that
      specifies the concept.
    group_help: str, the help text for the entire arg group.
    prefixes: bool, whether to use prefixes before the attribute flags, such as
      `--myresource-project`.
    required: bool, whether the anchor argument should be required. If True, the
      command will fail at argparse time if the anchor argument isn't given.
    plural: bool, True if the resource will be parsed as a list, False
      otherwise.
    group: the parser or subparser for a Calliope command that the resource
      arguments should be added to. If not provided, will be added to the main
      parser.
    attribute_to_args_map: {str: str}, dict of attribute names to names of
      associated arguments.
    hidden: bool, True if the arguments should be hidden.
  """

  def __init__(self,
               name,
               concept_spec,
               group_help,
               prefixes=False,
               required=False,
               flag_name_overrides=None,
               plural=False,
               group=None,
               hidden=False):
    """Initializes a ResourcePresentationSpec.

    Args:
      name: str, the name of the main arg for the concept.
      concept_spec: googlecloudsdk.calliope.concepts.ConceptSpec, The spec that
        specifies the concept.
      group_help: str, the help text for the entire arg group.
      prefixes: bool, whether to use prefixes before the attribute flags, such
        as `--myresource-project`. This will match the "name" (in flag format).
      required: bool, whether the anchor argument should be required.
      flag_name_overrides: {str: str}, dict of attribute names to the desired
        flag name. To remove a flag altogether, use '' as its rename value.
      plural: bool, True if the resource will be parsed as a list, False
        otherwise.
      group: the parser or subparser for a Calliope command that the resource
        arguments should be added to. If not provided, will be added to the main
        parser.
      hidden: bool, True if the arguments should be hidden.
    """
    self.name = name
    self._concept_spec = concept_spec
    self.group_help = group_help
    self.prefixes = prefixes
    self.required = required
    self.plural = plural
    self.group = group
    self._attribute_to_args_map = self._GetAttributeToArgsMap(
        flag_name_overrides)
    self.hidden = hidden

  @property
  def concept_spec(self):
    """The ConceptSpec associated with the PresentationSpec.

    Returns:
      (googlecloudsdk.calliope.concepts.ConceptSpec) the concept spec.
    """
    return self._concept_spec

  @property
  def attribute_to_args_map(self):
    """The map of attribute names to associated args.

    Returns:
      {str: str}, the map.
    """
    return self._attribute_to_args_map

  def _GenerateInfo(self, fallthroughs_map):
    """Generate a ConceptInfo object for the ConceptParser.

    Must be overridden in subclasses.

    Args:
      fallthroughs_map: {str: [googlecloudsdk.calliope.concepts.deps.
        _FallthroughBase]}, dict keyed by attribute name to lists of
        fallthroughs.

    Returns:
      info_holders.ConceptInfo, the ConceptInfo object.
    """
    raise NotImplementedError

  def _GetAttributeToArgsMap(self, flag_name_overrides):
    """Generate a map of attributes to primary arg names.

    Must be overridden in subclasses.

    Args:
      flag_name_overrides: {str: str}, the dict of flags to overridden names.

    Returns:
      {str: str}, dict from attribute names to arg names.
    """
    raise NotImplementedError


class ResourcePresentationSpec(PresentationSpec):
  """Class that specifies how resource arguments are presented in a command."""

  def _ValidateFlagNameOverrides(self, flag_name_overrides):
    if not flag_name_overrides:
      return
    for attribute_name in flag_name_overrides.keys():
      for attribute in self.concept_spec.attributes:
        if attribute.name == attribute_name:
          break
      else:
        raise ValueError(
            'Attempting to override the name for an attribute not present in '
            'the concept: [{}]. Available attributes: [{}]'.format(
                attribute_name,
                ', '.join([attribute.name
                           for attribute in self.concept_spec.attributes])))

  def _GetAttributeToArgsMap(self, flag_name_overrides):
    self._ValidateFlagNameOverrides(flag_name_overrides)
    # Create a rename map for the attributes to their flags.
    attribute_to_args_map = {}
    for i, attribute in enumerate(self._concept_spec.attributes):
      is_anchor = i == len(self._concept_spec.attributes) - 1
      name = self.GetFlagName(
          attribute.name, self.name, flag_name_overrides, self.prefixes,
          is_anchor=is_anchor)
      if name:
        attribute_to_args_map[attribute.name] = name
    return attribute_to_args_map

  @staticmethod
  def GetFlagName(attribute_name, presentation_name, flag_name_overrides=None,
                  prefixes=False, is_anchor=False):
    """Gets the flag name for a given attribute name.

    Returns a flag name for an attribute, adding prefixes as necessary or using
    overrides if an override map is provided.

    Args:
      attribute_name: str, the name of the attribute to base the flag name on.
      presentation_name: str, the anchor argument name of the resource the
        attribute belongs to (e.g. '--foo').
      flag_name_overrides: {str: str}, a dict of attribute names to exact string
        of the flag name to use for the attribute. None if no overrides.
      prefixes: bool, whether to use the resource name as a prefix for the flag.
      is_anchor: bool, True if this it he anchor flag, False otherwise.

    Returns:
      (str) the name of the flag.
    """
    flag_name_overrides = flag_name_overrides or {}
    if attribute_name in flag_name_overrides:
      return flag_name_overrides.get(attribute_name)
    if attribute_name == 'project':
      return ''
    if is_anchor:
      return presentation_name
    prefix = util.PREFIX
    if prefixes:
      if presentation_name.startswith(util.PREFIX):
        prefix += presentation_name[len(util.PREFIX):] + '-'
      else:
        prefix += presentation_name.lower().replace('_', '-') + '-'
    return prefix + attribute_name

  def _GenerateInfo(self, fallthroughs_map):
    """Gets the ResourceInfo object for the ConceptParser.

    Args:
      fallthroughs_map: {str: [googlecloudsdk.calliope.concepts.deps.
        _FallthroughBase]}, dict keyed by attribute name to lists of
        fallthroughs.

    Returns:
      info_holders.ResourceInfo, the ResourceInfo object.
    """
    return info_holders.ResourceInfo(
        self.name,
        self.concept_spec,
        self.group_help,
        self.attribute_to_args_map,
        fallthroughs_map,
        required=self.required,
        plural=self.plural,
        group=self.group,
        hidden=self.hidden)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return False
    return (self.name == other.name and
            self.concept_spec == other.concept_spec and
            self.group_help == other.group_help and
            self.prefixes == other.prefixes and self.plural == other.plural and
            self.required == other.required and self.group == other.group and
            self.hidden == other.hidden)


# Currently no other type of multitype concepts have been implemented.
class MultitypeResourcePresentationSpec(PresentationSpec):
  """A resource-specific presentation spec."""

  def _GetAttributeToArgsMap(self, flag_name_overrides):
    # Create a rename map for the attributes to their flags.
    attribute_to_args_map = {}
    leaf_anchors = [a for a in self._concept_spec.attributes
                    if self._concept_spec.IsLeafAnchor(a)]
    for attribute in self._concept_spec.attributes:
      is_anchor = [attribute] == leaf_anchors
      name = self.GetFlagName(
          attribute.name, self.name, flag_name_overrides=flag_name_overrides,
          prefixes=self.prefixes, is_anchor=is_anchor)
      if name:
        attribute_to_args_map[attribute.name] = name
    return attribute_to_args_map

  @staticmethod
  def GetFlagName(attribute_name, presentation_name, flag_name_overrides=None,
                  prefixes=False, is_anchor=False):
    """Gets the flag name for a given attribute name.

    Returns a flag name for an attribute, adding prefixes as necessary or using
    overrides if an override map is provided.

    Args:
      attribute_name: str, the name of the attribute to base the flag name on.
      presentation_name: str, the anchor argument name of the resource the
        attribute belongs to (e.g. '--foo').
      flag_name_overrides: {str: str}, a dict of attribute names to exact string
        of the flag name to use for the attribute. None if no overrides.
      prefixes: bool, whether to use the resource name as a prefix for the flag.
      is_anchor: bool, True if this is the anchor flag, False otherwise.

    Returns:
      (str) the name of the flag.
    """
    flag_name_overrides = flag_name_overrides or {}
    if attribute_name in flag_name_overrides:
      return flag_name_overrides.get(attribute_name)
    if is_anchor:
      return presentation_name
    if attribute_name == 'project':
      return ''

    if prefixes:
      return util.FlagNameFormat('-'.join([presentation_name, attribute_name]))
    return util.FlagNameFormat(attribute_name)

  def _GenerateInfo(self, fallthroughs_map):
    """Gets the MultitypeResourceInfo object for the ConceptParser.

    Args:
      fallthroughs_map: {str: [googlecloudsdk.calliope.concepts.deps.
        _FallthroughBase]}, dict keyed by attribute name to lists of
        fallthroughs.

    Returns:
      info_holders.MultitypeResourceInfo, the ResourceInfo object.
    """
    return info_holders.MultitypeResourceInfo(
        self.name,
        self.concept_spec,
        self.group_help,
        self.attribute_to_args_map,
        fallthroughs_map,
        required=self.required,
        plural=self.plural,
        group=self.group)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return False
    return (self.name == other.name and
            self.concept_spec == other.concept_spec and
            self.group_help == other.group_help and
            self.prefixes == other.prefixes and self.plural == other.plural and
            self.required == other.required and self.group == other.group and
            self.hidden == other.hidden)
