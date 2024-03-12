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
"""Abstract base class for concepts.

This base class cannot be used as a concept on its own but must be subclassed,
and the methods Attribute(), GetPresentationName(), and Parse() must be
implemented.

Example usage:

class IntConcept(Concept):

  def __init__(self, **kwargs):
    super(IntConcept, self).__init__(name='int', **kwargs)

  def Attribute(self):
    return Attribute(concept=self,
                     fallthroughs=self.fallthroughs,
                     help=self.BuildHelpText(),
                     required=self.required,
                     hidden=self.hidden,
                     completer=self.completer,
                     metavar=self.metavar)

  def GetPresentationName(self):
    return googlecloudsdk.command_lib.concepts.names.FlagNameFormat(
        self.name)

  def BuildHelpText(self):
    super(IntConcept, self).BuildHelpText() + ' Must be an int.'

  def Parse(self, dependencies):
    try:
      return int(dependencies.value)
    except ValueError:
      raise googlecloudsdk.command_lib.concepts.exceptions.Error(
          'Could not parse int concept; you provided [{}]'
          .format(dependencies.value))

* Note for Concept Implementers *
When implementing a new concept that produces a single argument, you can
subclass googlecloudsdk.command_lib.concepts.all_concepts.SimpleArg in order to
take advantage of general functionality, such as creating a simple presentation
name based on whether concept.positional is True, determining whether the
produced attribute is required, raising an exception if no value is found and
the concept is required, and storing fallthroughs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import six


class Concept(six.with_metaclass(abc.ABCMeta, object)):
  """Abstract base class for concept args.

  Attributes:
    name: str, the name of the concept. Used to determine
      the argument or group name of the concept.
    key: str, the name by which the parsed concept is stored in the dependency
      view. If not given, is the same as the concept's name. Generally,
      this should only be set and used by containing concepts when parsing
      from a DependencyView object. End users of concepts do not need to
      use it.
    help_text: str, the help text to be displayed for this concept.
    required: bool, whether the concept must be provided by the end user. If
      False, it's acceptable to have an empty result; otherwise, an empty
      result will raise an error.
    hidden: bool, whether the associated argument or group should be hidden.
  """

  def __init__(self, name, key=None, help_text='', required=False,
               hidden=False):
    self.name = name
    self.help_text = help_text
    self.required = required
    self.hidden = hidden
    self.key = key or self.name

  @abc.abstractmethod
  def Attribute(self):
    """Returns an Attribute object representing the attributes.

    Must be defined in subclasses.

    Returns:
      Attribute | AttributeGroup, the attribute or group.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def GetPresentationName(self):
    """Returns the main name for the concept."""
    raise NotImplementedError

  def BuildHelpText(self):
    """Builds and returns the help text.

    Returns:
      str, the help text for the concept.
    """
    return self.help_text

  def Marshal(self):
    """Returns the list of concepts that this concept marshals."""
    return None

  @abc.abstractmethod
  def Parse(self, dependencies):
    """Parses the concept.

    Args:
      dependencies: a DependenciesView object.

    Returns:
      the parsed concept.

    Raises:
      googlecloudsdk.command_lib.concepts.exceptions.Error, if parsing fails.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def IsArgRequired(self):
    """Returns whether this concept is required to be specified by argparse."""
    return False

  def MakeArgKwargs(self):
    """Returns argparse kwargs shared between all concept types."""
    return {
        'help': self.BuildHelpText(),
        'required': self.IsArgRequired(),
        'hidden': self.hidden,
    }


class Attribute(object):
  """An attribute that gets transformed to an argument.

  Attributes:
    concept: Concept, the underlying concept.
    key: str, the name by which the Attribute is looked up in the dependency
      view.
    fallthroughs: [deps.Fallthrough], the list of fallthroughs for the concept.
    kwargs: {str: any}, other metadata describing the attribute. Available
      keys include: required (bool), hidden (bool), help (str), completer,
      default, nargs.  **Note: This is currently used essentially as a
      passthrough to the argparse library.
  """

  def __init__(self, concept=None, fallthroughs=None, **kwargs):
    self.concept = concept
    self.fallthroughs = fallthroughs or []
    self.kwargs = kwargs

  @property
  def arg_name(self):
    """A string property representing the final argument name."""
    return self.concept.GetPresentationName()


class AttributeGroup(object):
  """Represents an object that gets transformed to an argument group.

  Attributes:
    concept: Concept, the underlying concept.
    key: str, the name by which the Attribute is looked up in the dependency
      view.
    attributes: [Attribute | AttributeGroup], the list of attributes or
      attribute groups contained in this attribute group.
    kwargs: {str: any}, other metadata describing the attribute. Available
      keys include: required (bool), mutex (bool), hidden (bool), help (str).
      **Note: This is currently used essentially as a passthrough to the
      argparse library.
  """

  def __init__(self, concept=None, attributes=None, **kwargs):
    self.concept = concept
    self.key = concept.key
    self.attributes = attributes or []
    self.kwargs = kwargs
