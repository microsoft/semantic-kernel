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
"""Classes for runtime handling of concept arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.calliope.concepts import util
from googlecloudsdk.command_lib.util.concepts import completers
from googlecloudsdk.core.util import text
import six
from six.moves import filter  # pylint: disable=redefined-builtin


ANCHOR_HELP = ('ID of the {resource} or fully qualified identifier for the '
               '{resource}.')

PLURAL_ANCHOR_HELP = ('IDs of the {resource} or fully qualified identifiers '
                      'for the {resource}.')


class ConceptInfo(six.with_metaclass(abc.ABCMeta, object)):
  """Holds information for a concept argument.

  The ConceptInfo object is responsible for holding information about the
  dependencies of a concept, and building a Deps object when it is time for
  lazy parsing of the concept.

  Attributes:
    concept_spec: The concept spec underlying the concept handler.
    attribute_to_args_map: A map of attributes to the names of their associated
      flags.
    fallthroughs_map: A map of attributes to non-argument fallthroughs.
  """

  @property
  def concept_spec(self):
    """The concept spec associated with this info class."""
    raise NotImplementedError

  @property
  def fallthroughs_map(self):
    """A map of attribute names to non-primary fallthroughs."""
    raise NotImplementedError

  @abc.abstractmethod
  def GetHints(self, attribute_name):
    """Get a list of string hints for how to specify a concept's attribute.

    Args:
      attribute_name: str, the name of the attribute to get hints for.

    Returns:
      [str], a list of string hints.
    """

  def GetGroupHelp(self):
    """Get the group help for the group defined by the presentation spec.

    Must be overridden in subclasses.

    Returns:
      (str) the help text.
    """
    raise NotImplementedError

  def GetAttributeArgs(self):
    """Generate args to add to the argument group.

    Must be overridden in subclasses.

    Yields:
      (calliope.base.Argument), all arguments corresponding to concept
        attributes.
    """
    raise NotImplementedError

  def AddToParser(self, parser):
    """Adds all attribute args for the concept to argparse.

    Must be overridden in subclasses.

    Args:
      parser: the parser for the Calliope command.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def Parse(self, parsed_args=None):
    """Lazy parsing function to parse concept.

    Args:
      parsed_args: the argparse namespace from the runtime handler.

    Returns:
      the parsed concept.
    """

  def ClearCache(self):
    """Clear cache if it exists. Override where needed."""
    pass


class ResourceInfo(ConceptInfo):
  """Holds information for a resource argument."""

  def __init__(self,
               presentation_name,
               concept_spec,
               group_help,
               attribute_to_args_map,
               fallthroughs_map,
               required=False,
               plural=False,
               group=None,
               hidden=False):
    """Initializes the ResourceInfo.

    Args:
      presentation_name: str, the name of the anchor argument of the
        presentation spec.
      concept_spec: googlecloudsdk.calliope.concepts.ConceptSpec, The underlying
        concept spec.
      group_help: str, the group help for the argument group.
      attribute_to_args_map: {str: str}, A map of attribute names to the names
        of their associated flags.
      fallthroughs_map: {str: [deps_lib.Fallthrough]} A map of attribute names
        to non-argument fallthroughs.
      required: bool, False if resource parsing is allowed to return no
        resource, otherwise True.
      plural: bool, True if multiple resources can be parsed, False otherwise.
      group: an argparse argument group parser to which the resource arg group
        should be added, if any.
      hidden: bool, True, if the resource should be hidden.
    """
    super(ResourceInfo, self).__init__()
    self.presentation_name = presentation_name
    self._concept_spec = concept_spec
    self._fallthroughs_map = fallthroughs_map
    self.attribute_to_args_map = attribute_to_args_map
    self.plural = plural
    self.group_help = group_help
    self.allow_empty = not required
    self.group = group
    self.hidden = hidden

    self._result = None
    self._result_computed = False
    self.sentinel = 0

  @property
  def concept_spec(self):
    return self._concept_spec

  @property
  def resource_spec(self):
    return self.concept_spec

  @property
  def fallthroughs_map(self):
    return self._fallthroughs_map

  @property
  def title(self):
    """The title of the arg group for the spec, in all caps with spaces."""
    name = self.concept_spec.name
    name = name[0].upper() + name[1:]
    return name.replace('_', ' ').replace('-', ' ')

  def _IsAnchor(self, attribute):
    return self.concept_spec.IsAnchor(attribute)

  def BuildFullFallthroughsMap(self):
    return self.concept_spec.BuildFullFallthroughsMap(
        self.attribute_to_args_map,
        self.fallthroughs_map)

  def GetHints(self, attribute_name):
    """Gets a list of string hints for how to set an attribute.

    Given the attribute name, gets a list of hints corresponding to the
    attribute's fallthroughs.

    Args:
      attribute_name: str, the name of the attribute.

    Returns:
      A list of hints for its fallthroughs, including its primary arg if any.
    """
    fallthroughs = self.BuildFullFallthroughsMap().get(attribute_name, [])
    return deps_lib.GetHints(fallthroughs)

  def GetGroupHelp(self):
    """Build group help for the argument group."""
    if len(list(filter(bool, list(self.attribute_to_args_map.values())))) == 1:
      generic_help = 'This represents a Cloud resource.'
    else:
      generic_help = ('The arguments in this group can be used to specify the '
                      'attributes of this resource.')
    description = ['{} resource - {} {}'.format(
        self.title,
        self.group_help,
        generic_help)]
    skip_flags = [
        attribute.name for attribute in self.resource_spec.attributes
        if not self.attribute_to_args_map.get(attribute.name)]
    if skip_flags:
      description.append('(NOTE) Some attributes are not given arguments in '
                         'this group but can be set in other ways.')
      for attr_name in skip_flags:
        hints = [
            '\n* {}'.format(hint) for hint in self.GetHints(attr_name)]
        if not hints:
          # This may be an error, but existence of fallthroughs should not be
          # enforced here.
          continue
        hint = '\n\nTo set the `{}` attribute:{}.'.format(
            attr_name, ';'.join(hints)
        )
        description.append(hint)
    return ' '.join(description)

  @property
  def args_required(self):
    """True if the resource is required and any arguments have no fallthroughs.

    If fallthroughs can ever be configured in the ResourceInfo object,
    a more robust solution will be needed, e.g. a GetFallthroughsForAttribute
    method.

    Returns:
      bool, whether the argument group should be required.
    """
    if self.allow_empty:
      return False
    anchor = self.resource_spec.anchor
    if (self.attribute_to_args_map.get(anchor.name, None)
        and not self.fallthroughs_map.get(anchor.name, [])):
      return True
    return False

  def _GetHelpTextForAttribute(self, attribute):
    """Helper to get the help text for the attribute arg."""
    if self._IsAnchor(attribute):
      help_text = ANCHOR_HELP if not self.plural else PLURAL_ANCHOR_HELP
    else:
      help_text = attribute.help_text

    expansion_name = text.Pluralize(
        2 if self.plural else 1,
        self.resource_spec.name,
        plural=getattr(self.resource_spec, 'plural_name', None))
    hints = [
        '\n* {}'.format(hint) for hint in self.GetHints(attribute.name)]
    if hints:
      hint = '\n\nTo set the `{}` attribute:{}.'.format(
          attribute.name, ';'.join(hints)
      )
      help_text += hint
    return help_text.format(resource=expansion_name)

  def _IsRequiredArg(self, attribute):
    # An argument cannot be required if it's hidden
    return not self.hidden and (
        self._IsAnchor(attribute) and
        not self.fallthroughs_map.get(attribute.name, []))

  def _IsPluralArg(self, attribute):
    return self._IsAnchor(attribute) and self.plural

  def _KwargsForAttribute(self, name, attribute):
    """Constructs the kwargs for adding an attribute to argparse."""
    # Argument is modal if it's the anchor, unless there are fallthroughs.
    # If fallthroughs can ever be configured in the ResourceInfo object,
    # a more robust solution will be needed, e.g. a GetFallthroughsForAttribute
    # method.
    required = self._IsRequiredArg(attribute)
    final_help_text = self._GetHelpTextForAttribute(attribute)
    plural = self._IsPluralArg(attribute)
    if attribute.completer:
      completer = attribute.completer
    elif not self.resource_spec.disable_auto_completers:
      completer = completers.CompleterForAttribute(
          self.resource_spec,
          attribute.name)
    else:
      completer = None
    kwargs_dict = {
        'help': final_help_text,
        'type': attribute.value_type,
        'completer': completer,
        'hidden': self.hidden
    }
    if util.IsPositional(name):
      if plural and required:
        kwargs_dict.update({'nargs': '+'})
      # The following should not usually happen because anchor args are
      # required.
      elif plural and not required:
        kwargs_dict.update({'nargs': '*'})
      elif not required:
        kwargs_dict.update({'nargs': '?'})
    else:
      kwargs_dict.update({'metavar': util.MetavarFormat(name)})
      if required:
        kwargs_dict.update({'required': True})
      if plural:
        kwargs_dict.update({'type': arg_parsers.ArgList()})
    return kwargs_dict

  def _GetAttributeArg(self, attribute):
    """Creates argument for a specific attribute."""
    name = self.attribute_to_args_map.get(attribute.name, None)
    # Return None for any false value.
    if not name:
      return None
    return base.Argument(
        name,
        **self._KwargsForAttribute(name, attribute))

  def GetAttributeArgs(self):
    """Generate args to add to the argument group."""
    args = []
    for attribute in self.resource_spec.attributes:
      arg = self._GetAttributeArg(attribute)
      if arg:
        args.append(arg)

    return args

  def AddToParser(self, parser):
    """Adds all attributes of the concept to argparse.

    Creates a group to hold all the attributes and adds an argument for each
    attribute. If the presentation spec is required, then the anchor attribute
    argument will be required.

    Args:
      parser: the parser for the Calliope command.
    """
    args = self.GetAttributeArgs()
    if not args:
      # Don't create the group if there are not going to be any args generated.
      return
    # If this spec is supposed to be added to a subgroup, that overrides the
    # provided parser.
    parser = self.group or parser

    hidden = any(x.IsHidden() for x in args)

    resource_group = parser.add_group(
        help=self.GetGroupHelp(), required=self.args_required, hidden=hidden)
    for arg in args:
      arg.AddToParser(resource_group)

  def GetExampleArgList(self):
    """Returns a list of command line example arg strings for the concept."""
    args = self.GetAttributeArgs()
    examples = []
    for arg in args:
      if arg.name.startswith('--'):
        example = '{}=my-{}'.format(arg.name, arg.name[2:])
      else:
        example = 'my-{}'.format(arg.name.lower())
      examples.append(example)
    return examples

  def Parse(self, parsed_args=None):
    """Lazy, cached parsing function for resource.

    Args:
      parsed_args: the parsed Namespace.

    Returns:
      the initialized resource or a list of initialized resources if the
        resource argument was pluralized.
    """
    if not self._result_computed:
      result = self.concept_spec.Parse(self.attribute_to_args_map,
                                       self.fallthroughs_map,
                                       parsed_args=parsed_args,
                                       plural=self.plural,
                                       allow_empty=self.allow_empty)
      self._result_computed = True
      self._result = result
    return self._result

  def ClearCache(self):
    self._result = None
    self._result_computed = False


class MultitypeResourceInfo(ResourceInfo):
  """ResourceInfo object specifically for multitype resources."""

  def _IsAnchor(self, attribute):
    """Returns true if the attribute is an anchor."""
    return self.concept_spec.IsAnchor(attribute)

  def _GetAnchors(self):
    return [a for a in self.concept_spec.attributes if self._IsAnchor(a)]

  def _IsRequiredArg(self, attribute):
    """Returns True if the attribute arg should be required."""
    anchors = self._GetAnchors()
    return anchors == [attribute] and not self.fallthroughs_map.get(
        attribute.name, [])

  def _IsPluralArg(self, attribute):
    return self.concept_spec.Pluralize(attribute, plural=self.plural)

  @property
  def args_required(self):
    """True if resource is required & has a single anchor with no fallthroughs.

    Returns:
      bool, whether the argument group should be required.
    """
    if self.allow_empty:
      return False

    anchors = self._GetAnchors()
    if len(anchors) != 1:
      return False
    anchor = anchors[0]
    if self.fallthroughs_map.get(anchor.name, []):
      return False
    # There's only one anchor and it's got no fallthroughs.
    return True

  def GetGroupHelp(self):
    base_text = super(MultitypeResourceInfo, self).GetGroupHelp()
    all_types = [
        type_.name for type_ in self.concept_spec.type_enum]  # pylint: disable=protected-access
    return base_text + (' This resource can be one of the following types: '
                        '[{}].'.format(', '.join(all_types)))

  def _GetHelpTextForAttribute(self, attribute):
    base_text = super(MultitypeResourceInfo, self)._GetHelpTextForAttribute(
        attribute)
    # pylint: disable=protected-access
    relevant_types = sorted([
        type_.name for type_ in self.concept_spec._attribute_to_types_map.get(
            attribute.name)])
    # Don't add anything extra if this attribute is used in all types.
    all_types = [
        type_.name for type_ in self.concept_spec.type_enum]
    if len(set(relevant_types)) == len(all_types):
      return base_text
    # pylint: disable=protected-access
    return base_text + (
        ' Must be specified for resource of type {}.'
        .format(' or '.join(['[{}]'.format(t) for t in relevant_types])))
