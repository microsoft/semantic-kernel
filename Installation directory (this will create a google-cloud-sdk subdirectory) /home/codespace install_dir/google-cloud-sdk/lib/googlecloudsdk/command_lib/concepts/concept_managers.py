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

"""Classes that manage concepts and dependencies.

For usage examples, see
googlecloudsdk/command_lib/concepts/all_concepts/base.py.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.concepts import base
from googlecloudsdk.command_lib.concepts import dependency_managers
from googlecloudsdk.command_lib.concepts import names

import six


class ConceptManager(object):
  """A manager that contains all concepts (v2) for a given command.

  This object is responsible for registering all concepts, creating arguments
  for the concepts, and creating a RuntimeParser which will be responsible
  for parsing the concepts.

  Attributes:
    concepts: [base.Concept], a list of concepts.
    runtime_parser: RuntimeParser, the runtime parser manager for all concepts.
  """

  def __init__(self):
    self.concepts = []
    self.runtime_parser = None
    self._command_level_fallthroughs = {}

  def AddConcept(self, concept):
    """Add a single concept.

    This method adds a concept to the ConceptManager. It does not immediately
    have any effect on the command's argparse parser.

    Args:
      concept: base.Concept, an instantiated concept.
    """
    self.concepts.append(concept)

  def AddToParser(self, parser):
    """Adds concept arguments and concept RuntimeParser to argparse parser.

    For each concept, the Attribute() method is called, and all resulting
    attributes and attribute groups are translated into arguments for the
    argparse parser.

    Additionally, a concept-specific RuntimeParser is created with all of the
    resulting attributes from the first step. (This will be responsible for
    parsing the concepts.) It is registered to the argparse parser, and will
    appear in the final parsed namespace under CONCEPT_ARGS.

    Args:
      parser: googlecloudsdk.calliope.parser_arguments.ArgumentInterceptor, the
        argparse parser to which to add argparse arguments.
    """
    attributes = [concept.Attribute() for concept in self.concepts]
    self._AddToArgparse(attributes, parser)
    self.runtime_parser = RuntimeParser(attributes)
    parser.add_concepts(self.runtime_parser)

  def _AddToArgparse(self, attributes, parser):
    """Recursively add an arg definition to the parser."""
    for attribute in attributes:
      if isinstance(attribute, base.Attribute):
        parser.add_argument(attribute.arg_name, **attribute.kwargs)
        continue
      group = parser.add_argument_group(attribute.kwargs.pop('help'),
                                        **attribute.kwargs)
      self._AddToArgparse(attribute.attributes, group)


class RuntimeParser(object):
  """An object to manage parsing all concepts via their attributes.

  Once argument parsing is complete and ParseConcepts is called, each parsed
  concept is stored on this runtime parser as an attribute, named after the
  name of that concept.

  Attributes:
    parsed_args: the argparse namespace after arguments have been parsed.
    <CONCEPT_NAME> (the namespace format of each top level concept, such as
      "foo_bar"): the parsed concept corresponding to that name.
  """

  def __init__(self, attributes):
    self.parsed_args = None
    self._attributes = {}
    for attribute in attributes:
      attr_name = names.ConvertToNamespaceName(
          attribute.concept.GetPresentationName())
      if attr_name in self._attributes:
        raise ValueError('Attempting to add two concepts with the same '
                         'presentation name: [{}]'.format(attr_name))
      self._attributes[attr_name] = attribute

  def ParseConcepts(self):
    """Parse all concepts.

    Stores the result of parsing concepts, keyed to the namespace format of
    their presentation name. Afterward, will be accessible as
    args.<LOWER_SNAKE_CASE_NAME>.

    Raises:
      googlecloudsdk.command_lib.concepts.exceptions.Error: if parsing fails.
    """

    # Collect all final parse values in final before assigning back to args
    # because multiple FinalParse calls may use an attr_name multiple times.
    final = {}
    for attr_name, attribute in six.iteritems(self._attributes):
      dependencies = dependency_managers.DependencyNode.FromAttribute(attribute)
      final[attr_name] = FinalParse(dependencies, self.ParsedArgs)

    # Set the final parsed name=value in the args namespace. add_argument(),
    # either called explicitly, or via the concept manager, detects duplicate
    # names and raises an exception before this method is called.
    for name, value in six.iteritems(final):
      setattr(self.parsed_args, name, value)

  def ParsedArgs(self):
    """A lazy property to use during concept parsing.

    Returns:
      googlecloudsdk.calliope.parser_extensions.Namespace: the parsed argparse
        namespace | None, if the parser hasn't been registered to the namespace
        yet.
    """
    return self.parsed_args


def FinalParse(dependencies, arg_getter):
  """Lazy parser stored under args.CONCEPT_ARGS.

  Args:
    dependencies: dependency_managers.DependencyNode, the root of the tree of
      the concept's dependencies.
    arg_getter: Callable, a function that returns the parsed args namespace.

  Raises:
      googlecloudsdk.command_lib.concepts.exceptions.Error: if parsing fails.

  Returns:
    the result of parsing the root concept.
  """
  dependency_manager = dependency_managers.DependencyManager(dependencies)
  parsed_args = arg_getter()
  return dependency_manager.ParseConcept(parsed_args)
