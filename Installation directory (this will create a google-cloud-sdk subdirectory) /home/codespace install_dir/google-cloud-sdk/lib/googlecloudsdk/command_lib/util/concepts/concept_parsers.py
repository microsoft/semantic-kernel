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
"""ConceptParsers manage the adding of all concept arguments to argparse parser.

The ConceptParser is created with a list of all resources needed for the
command, and they should be added all at once during calliope's Args method.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.calliope.concepts import util
from googlecloudsdk.command_lib.util.concepts import presentation_specs

import six


class ConceptParser(object):
  """Class that handles adding concept specs to argparse."""

  def __init__(self, specs, command_level_fallthroughs=None):
    """Initializes a concept holder.

    Args:
      specs: [presentation_specs.PresentationSpec], a list of the
        specs for concepts to be added to the parser.
      command_level_fallthroughs: {str: str}, a map of attributes to argument
        fallthroughs for those attributes. The format of the key should be FOO.a
        (the resource presentation name is "FOO" and the attribute name is "a").
        The format of the value should either be "BAR.b" (where the argument
        depended upon is the main argument generated for attribute "b" of
        the resource presentation spec that is named "BAR"), or "--baz", where
        "--baz" is a non-resource argument that is added separately to the
        parser.

    Raises:
      ValueError: if two presentation specs have the same name or two specs
        contain positional arguments.
    """
    self._specs = {}
    self._all_args = []
    for spec in specs:
      self._AddSpec(spec)
    self._command_level_fallthroughs = self._ValidateAndFormatFallthroughsMap(
        command_level_fallthroughs or {})

  @classmethod
  def ForResource(cls, name, resource_spec, group_help, required=False,
                  hidden=False, flag_name_overrides=None,
                  plural=False, prefixes=False,
                  group=None, command_level_fallthroughs=None):
    """Constructs a ConceptParser for a single resource argument.

    Automatically sets prefixes to False.

    Args:
      name: str, the name of the main arg for the resource.
      resource_spec: googlecloudsdk.calliope.concepts.ResourceSpec, The spec
        that specifies the resource.
      group_help: str, the help text for the entire arg group.
      required: bool, whether the main argument should be required for the
        command.
      hidden: bool, whether or not the resource is hidden.
      flag_name_overrides: {str: str}, dict of attribute names to the desired
        flag name. To remove a flag altogether, use '' as its rename value.
      plural: bool, True if the resource will be parsed as a list, False
        otherwise.
      prefixes: bool, True if flag names will be prefixed with the resource
        name, False otherwise. Should be False for all typical use cases.
      group: the parser or subparser for a Calliope command that the resource
        arguments should be added to. If not provided, will be added to the main
        parser.
      command_level_fallthroughs: a map of attribute names to lists of command-
        specific fallthroughs. These will be prioritized over the default
        fallthroughs for the attribute.

    Returns:
      (googlecloudsdk.calliope.concepts.concept_parsers.ConceptParser) The fully
        initialized ConceptParser.
    """
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        name,
        resource_spec,
        group_help,
        required=required,
        flag_name_overrides=flag_name_overrides or {},
        plural=plural,
        prefixes=prefixes,
        group=group,
        hidden=hidden)
    fallthroughs_map = {}
    UpdateFallthroughsMap(fallthroughs_map, name, command_level_fallthroughs)
    for attribute_name, fallthroughs in six.iteritems(
        command_level_fallthroughs or {}):
      key = '{}.{}'.format(presentation_spec.name, attribute_name)
      fallthroughs_map[key] = fallthroughs
    return cls([presentation_spec], fallthroughs_map)

  def _ArgNameMatches(self, name, other_name):
    """Checks if two argument names match in the namespace.

    RESOURCE_ARG and --resource-arg will match with each other, as well as exact
    matches.

    Args:
      name: the first argument name.
      other_name: the second argument name.

    Returns:
      (bool) True if the names match.
    """
    if util.NormalizeFormat(name) == util.NormalizeFormat(other_name):
      return True
    return False

  def _AddSpec(self, presentation_spec):
    """Adds a given presentation spec to the concept holder's spec registry.

    Args:
      presentation_spec: PresentationSpec, the spec to be added.

    Raises:
      ValueError: if two presentation specs have the same name, if two
        presentation specs are both positional, or if two args are going to
        overlap.
    """
    # Check for duplicate spec names.
    for spec_name in self._specs:
      if self._ArgNameMatches(spec_name, presentation_spec.name):
        raise ValueError('Attempted to add two concepts with the same name: '
                         '[{}, {}]'.format(spec_name, presentation_spec.name))
      if (util.IsPositional(spec_name) and
          util.IsPositional(presentation_spec.name)):
        raise ValueError('Attempted to add multiple concepts with positional '
                         'arguments: [{}, {}]'.format(spec_name,
                                                      presentation_spec.name))

    # Also check for duplicate argument names.
    for a, arg_name in six.iteritems(presentation_spec.attribute_to_args_map):
      del a  # Unused.
      name = util.NormalizeFormat(arg_name)
      if name in self._all_args:
        raise ValueError('Attempted to add a duplicate argument name: [{}]'
                         .format(arg_name))
      self._all_args.append(name)

    self._specs[presentation_spec.name] = presentation_spec

  def _ValidateAndFormatFallthroughsMap(self, command_level_fallthroughs):
    """Validate formatting of fallthroughs and build map keyed to spec name."""
    spec_map = {}
    for key, fallthroughs_list in six.iteritems(command_level_fallthroughs):
      keys = key.split('.')
      if len(keys) != 2:
        raise ValueError('invalid fallthrough key: [{}]. Must be in format '
                         '"FOO.a" where FOO is the presentation spec name and '
                         'a is the attribute name.'.format(key))
      spec_name, attribute_name = keys
      self._ValidateSpecAndAttributeExist('key', spec_name, attribute_name)
      for fallthrough_string in fallthroughs_list:
        values = fallthrough_string.split('.')
        if len(values) not in [1, 2]:
          raise ValueError('invalid fallthrough value: [{}]. Must be in the '
                           'form BAR.b or --baz'.format(fallthrough_string))
        if len(values) == 2:
          value_spec_name, value_attribute_name = values
          self._ValidateSpecAndAttributeExist('value',
                                              value_spec_name,
                                              value_attribute_name)
      spec_map.setdefault(spec_name, {})[attribute_name] = fallthroughs_list
    return spec_map

  def _ValidateSpecAndAttributeExist(self, location, spec_name, attribute_name):
    """Raises if a formatted string refers to non-existent spec or attribute."""
    if spec_name not in self.specs:
      raise ValueError('invalid fallthrough {}: [{}]. Spec name is not '
                       'present in the presentation specs. Available names: '
                       '[{}]'.format(
                           location,
                           '{}.{}'.format(spec_name, attribute_name),
                           ', '.join(sorted(list(self.specs.keys())))))
    spec = self.specs.get(spec_name)
    if attribute_name not in [
        attribute.name for attribute in spec.concept_spec.attributes]:
      raise ValueError('invalid fallthrough {}: [{}]. spec named [{}] has no '
                       'attribute named [{}]'.format(
                           location,
                           '{}.{}'.format(spec_name, attribute_name),
                           spec_name,
                           attribute_name))

  @property
  def specs(self):
    return self._specs

  def AddToParser(self, parser):
    """Adds attribute args for all presentation specs to argparse.

    Args:
      parser: the parser for a Calliope command.
    """
    runtime_handler = parser.data.concept_handler
    if not runtime_handler:
      runtime_handler = handlers.RuntimeHandler()
      parser.add_concepts(runtime_handler)
    for spec_name, spec in six.iteritems(self._specs):
      concept_info = self.GetInfo(spec_name)
      concept_info.AddToParser(parser)
      runtime_handler.AddConcept(
          util.NormalizeFormat(spec_name),
          concept_info,
          required=spec.required)

  def GetExampleArgString(self):
    """Returns a command line example arg string for the concept."""
    examples = []
    for spec_name in self._specs:
      info = self.GetInfo(spec_name)
      args = info.GetExampleArgList()
      if args:
        examples.extend(args)

    def _PositionalsFirst(arg):
      prefix = 'Z' if arg.startswith('--') else 'A'
      return prefix + arg

    return ' '.join(sorted(examples, key=_PositionalsFirst))

  def _MakeFallthrough(self, fallthrough_string):
    """Make an ArgFallthrough from a formatted string."""
    values = fallthrough_string.split('.')
    if len(values) == 1:
      arg_name = values
      return deps.ArgFallthrough(values[0])
    elif len(values) == 2:
      spec_name, attribute_name = values
      spec = self.specs.get(spec_name)
      arg_name = spec.attribute_to_args_map.get(attribute_name, None)
      if not arg_name:
        raise ValueError(
            'Invalid fallthrough value [{}]: No argument associated with '
            'attribute [{}] in concept argument named [{}]'.format(
                fallthrough_string,
                attribute_name,
                spec_name))
      return deps.ArgFallthrough(arg_name)
    else:
      # Defensive only, should be validated earlier
      raise ValueError('bad fallthrough string [{}]'.format(fallthrough_string))

  def GetInfo(self, presentation_spec_name):
    """Build ConceptInfo object for the spec with the given name."""
    if presentation_spec_name not in self.specs:
      raise ValueError('Presentation spec with name [{}] has not been added '
                       'to the concept parser, cannot generate info.'.format(
                           presentation_spec_name))
    presentation_spec = self.specs[presentation_spec_name]
    fallthroughs_map = {}
    for attribute in presentation_spec.concept_spec.attributes:
      fallthrough_strings = self._command_level_fallthroughs.get(
          presentation_spec.name, {}).get(attribute.name, [])
      fallthroughs = [self._MakeFallthrough(fallthrough_string)
                      for fallthrough_string in fallthrough_strings]
      fallthroughs_map[attribute.name] = fallthroughs + attribute.fallthroughs

    return presentation_spec._GenerateInfo(fallthroughs_map)  # pylint: disable=protected-access


def UpdateFallthroughsMap(fallthroughs_map, resource_arg_name,
                          command_level_fallthroughs):
  """Helper to add a single resource's command level fallthroughs."""
  for attribute_name, fallthroughs in six.iteritems(
      command_level_fallthroughs or {}):
    key = '{}.{}'.format(resource_arg_name, attribute_name)
    fallthroughs_map[key] = fallthroughs
