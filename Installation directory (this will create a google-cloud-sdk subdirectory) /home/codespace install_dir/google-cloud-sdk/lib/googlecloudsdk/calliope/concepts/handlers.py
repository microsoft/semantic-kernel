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
"""Classes for runtime handling of concept arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import util
from googlecloudsdk.core import exceptions
import six


class Error(exceptions.Error):
  """Base class for errors in this module."""


class ParseError(Error):
  """Raised if a concept fails to parse."""

  def __init__(self, presentation_name, message):
    msg = 'Error parsing [{}].\n{}'.format(presentation_name, message)
    super(ParseError, self).__init__(msg)


class RepeatedConceptName(Error):
  """Raised when adding a concept if one with the given name already exists."""

  def __init__(self, concept_name):
    msg = 'Repeated concept name [{}].'.format(concept_name)
    super(RepeatedConceptName, self).__init__(msg)


class RuntimeHandler(object):
  """A handler to hold information about all concept arguments in a command.

  The handler is assigned to 'CONCEPTS' in the argparse namespace and has an
  attribute to match the name of each concept argument in lower snake case.
  """

  def __init__(self):
    # This is set by the ArgumentInterceptor later.
    self.parsed_args = None
    self._arg_name_lookup = {}
    self._all_concepts = []

  def ParsedArgs(self):
    """Basically a lazy property to use during lazy concept parsing."""
    return self.parsed_args

  def AddConcept(self, name, concept_info, required=True):
    """Adds a concept handler for a given concept.

    Args:
      name: str, the name to be used for the presentation spec.
      concept_info: ConceptInfo, the object that holds dependencies of the
        concept.
      required: bool, True if the concept must be parseable, False if not.

    Raises:
      RepeatedConceptName: If the given "name" has already been used with a
        concept.
    """

    class LazyParse(object):
      """Class provided when accessing a concept to lazily parse from args."""

      def __init__(self, parse, arg_getter):
        self.parse = parse
        self.arg_getter = arg_getter

      def Parse(self):
        try:
          return self.parse(self.arg_getter())
        except concepts.InitializationError as e:
          if required:
            raise ParseError(name, six.text_type(e))
          return None

    if hasattr(self, name):
      raise RepeatedConceptName(name)
    setattr(self, name, LazyParse(concept_info.Parse, self.ParsedArgs))
    self._all_concepts.append({
        'name': name,
        'concept_info': concept_info,
        'required': required,
    })
    for _, arg_name in six.iteritems(concept_info.attribute_to_args_map):
      self._arg_name_lookup[util.NormalizeFormat(arg_name)] = concept_info

  def ArgNameToConceptInfo(self, arg_name):
    return self._arg_name_lookup.get(util.NormalizeFormat(arg_name))

  def Reset(self):
    for concept_details in self._all_concepts:
      concept_details['concept_info'].ClearCache()

  def GetValue(self, dest):
    """Returns the value of the argument registered for dest.

    Based on argparse.Namespace.GetValue().

    Args:
      dest: The dest of a registered argument.

    Raises:
      UnknownDestinationException: If no arg is registered for dest.

    Returns:
      The value of the argument registered for dest.
    """
    try:
      return getattr(self, dest)
    except AttributeError:
      raise parser_errors.UnknownDestinationException(
          'No registered concept arg for destination [{}].'.format(dest))
