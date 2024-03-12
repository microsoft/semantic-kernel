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

"""Classes that manage concepts and dependencies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools

from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.command_lib.concepts import base
from googlecloudsdk.command_lib.concepts import exceptions
from googlecloudsdk.command_lib.concepts import names

import six


def GetPresentationNames(nodes):
  return (child.GetPresentationName() for child in nodes)


class DependencyManager(object):
  """Holds dependency info for a single overall concept and creates views.

  Attributes:
    node: the DependencyNode at the root of the dependency tree for this
      concept.
  """

  def __init__(self, node):
    self.node = node

  def ParseConcept(self, parsed_args):
    """Parse the concept recursively by building the dependencies in a DFS.

    Args are formatted in the same way as usage_text.py:GetArgsUsage, except
    concepts in a concept group are not sorted. Concepts are displayed in the
    order they were added to the group.

    Args:
      parsed_args: the raw parsed argparse namespace.

    Raises:
      googlecloudsdk.command_lib.concepts.exceptions.Error: if parsing fails.

    Returns:
      the parsed top-level concept.
    """

    def _ParseConcept(node):
      """Recursive parsing."""
      if not node.is_group:
        fallthroughs = []
        if node.arg_name:
          fallthroughs.append(deps_lib.ArgFallthrough(node.arg_name))
        fallthroughs += node.fallthroughs
        return node.concept.Parse(
            DependencyViewFromValue(
                functools.partial(
                    deps_lib.GetFromFallthroughs, fallthroughs, parsed_args),
                marshalled_dependencies=node.dependencies))

      # TODO(b/120132521) Replace and eliminate argparse extensions
      also_optional = []  # The optional concepts that were not specified.
      have_optional = []  # The specified optional (not required) concepts.
      have_required = []  # The specified required concepts.
      need_required = []  # The required concepts that must be specified.
      namespace = {}
      for name, child in six.iteritems(node.dependencies):
        result = None
        try:
          result = _ParseConcept(child)
          if result:
            if child.concept.required:
              have_required.append(child.concept)
            else:
              have_optional.append(child.concept)
          else:
            also_optional.append(child.concept)
        except exceptions.MissingRequiredArgumentError:
          need_required.append(child.concept)
        namespace[name] = result

      if need_required:
        missing = ' '.join(GetPresentationNames(need_required))
        if have_optional or have_required:
          specified_parts = []
          if have_required:
            specified_parts.append(' '.join(
                GetPresentationNames(have_required)))
          if have_required and have_optional:
            specified_parts.append(':')
          if have_optional:
            specified_parts.append(' '.join(
                GetPresentationNames(have_optional)))

          specified = ' '.join(specified_parts)
          if have_required and have_optional:
            if node.concept.required:
              specified = '({})'.format(specified)
            else:
              specified = '[{}]'.format(specified)
          raise exceptions.ModalGroupError(
              node.concept.GetPresentationName(), specified, missing)

      count = len(have_required) + len(have_optional)
      if node.concept.mutex:
        specified = ' | '.join(
            GetPresentationNames(node.concept.concepts))
        if node.concept.required:
          specified = '({specified})'.format(specified=specified)
          if count != 1:
            raise exceptions.RequiredMutexGroupError(
                node.concept.GetPresentationName(), specified)
        else:
          if count > 1:
            raise exceptions.OptionalMutexGroupError(
                node.concept.GetPresentationName(), specified)

      return node.concept.Parse(DependencyView(namespace))

    return _ParseConcept(self.node)


class DependencyView(object):
  """Simple namespace used by concept.Parse for concept groups."""

  def __init__(self, values_dict):
    for key, value in six.iteritems(values_dict):
      setattr(self, names.ConvertToNamespaceName(key), value)


class DependencyViewFromValue(object):
  """Simple namespace for single value."""

  def __init__(self, value_getter, marshalled_dependencies=None):
    self._value_getter = value_getter
    self._marshalled_dependencies = marshalled_dependencies

  @property
  def value(self):
    """Lazy value getter.

    Returns:
      the value of the attribute, from its fallthroughs.

    Raises:
      deps_lib.AttributeNotFoundError: if the value cannot be found.
    """
    try:
      return self._value_getter()
    except TypeError:
      return self._value_getter

  @property
  def marshalled_dependencies(self):
    """Returns the marshalled dependencies or None if not marshalled."""
    return self._marshalled_dependencies


class DependencyNode(object):
  """A node of a dependency tree.

  Attributes:
    name: the name that will be used to look up the dependency from higher
      in the tree. Corresponds to the "key" of the attribute.
    concept: the concept of the attribute.
    dependencies: {str: DependencyNode}, a map from dependency names to
      sub-dependency trees.
    arg_name: str, the argument name of the attribute.
    fallthroughs: [deps_lib._Fallthrough], the list of fallthroughs for the
      dependency.
    marshalled: [base.Concept], the list of concepts marshalled by concept.
      The marshalled dependencies are generated here, but concept handles the
      parsing.
  """

  def __init__(self, name, is_group, concept=None, dependencies=None,
               arg_name=None, fallthroughs=None):
    self.name = name
    self.is_group = is_group
    self.concept = concept
    self.dependencies = dependencies
    self.arg_name = arg_name
    self.fallthroughs = fallthroughs or []

  @classmethod
  def FromAttribute(cls, attribute):
    """Builds the dependency tree from the attribute."""
    kwargs = {
        'concept': attribute.concept,
    }
    marshal = attribute.concept.Marshal()
    if marshal:
      attributes = [concept.Attribute() for concept in marshal]
    elif not isinstance(attribute, base.Attribute):
      attributes = attribute.attributes
    else:
      attributes = None
    if isinstance(attribute, base.Attribute) and (marshal or not attributes):
      kwargs['arg_name'] = attribute.arg_name
      kwargs['fallthroughs'] = attribute.fallthroughs
    if attributes:
      kwargs['dependencies'] = {a.concept.key: DependencyNode.FromAttribute(a)
                                for a in attributes}
    return DependencyNode(attribute.concept.key,
                          not isinstance(attribute, base.Attribute), **kwargs)
