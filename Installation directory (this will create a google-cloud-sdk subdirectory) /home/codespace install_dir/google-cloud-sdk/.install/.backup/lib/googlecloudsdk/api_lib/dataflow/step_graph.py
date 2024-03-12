# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Code to transform the (cleaned-up) description of a dataflow into Graphviz.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import exceptions
import six


class _Cluster(object):
  """Encapsulation of a single cluster in the final Step-Graph.

  The cluster hierarchy represents pieces of the user_name. A given cluster is
  either a leaf (it contains a single step and no sub-clusters) or a transform
  (it contains no step and one or more sub-clusters).
  """

  def __init__(self, parent, name_in_parent):
    self.__children = {}
    self.__parent = parent
    self.__name_in_parent = name_in_parent
    self.__step = None

  def IsLeaf(self):
    """A leaf cluster contains no sub-clusters.

    Returns:
      True iff this is a leaf cluster.
    """
    return not self.__children

  def IsSingleton(self):
    """A singleton is any cluster that contains a single child.

    Returns:
      True iff this is a singleton cluster.
    """
    return len(self.__children) == 1

  def IsRoot(self):
    """Determine if this cluster is the root.

    Returns:
      True iff this is the root cluster.
    """
    return not self.__parent

  def GetStep(self):
    """Return the step for this cluster.

    Returns:
      The step for this cluster. May be None if this is not a leaf.
    """
    return self.__step

  def SetStep(self, step):
    """Set the step for this cluster.

    Can only be called on leaf nodes that have not yet had their step set.

    Args:
      step: The step that this cluster represents.
    """
    assert not self.__children
    assert not self.__step
    self.__step = step

  def Name(self, relative_to=None):
    """Return the name of this sub-cluster relative to the given ancestor.

    Args:
      relative_to: The ancestor to output the name relative to.

    Returns:
      The string representing the user_name component for this cluster.
    """
    if (not self.__parent) or (self.__parent == relative_to):
      return self.__name_in_parent

    parent_name = self.__parent.Name(relative_to)
    if parent_name:
      return parent_name + '/' + self.__name_in_parent
    else:
      return self.__name_in_parent

  def GetOrAddChild(self, piece_name):
    """Return the cluster representing the given piece_name within this cluster.

    Args:
      piece_name: String representing the piece name of the desired child.
    Returns:
      Cluster representing the child.
    """
    assert not self.__step  # Leaves cannot have steps.
    if piece_name not in self.__children:
      self.__children[piece_name] = _Cluster(self, piece_name)
    return self.__children[piece_name]

  def Children(self):
    """Return the sub-clusters.

    Returns:
      Sorted list of pairs for the children in this cluster.
    """
    return sorted(six.iteritems(self.__children))


def _SplitStep(user_name):
  """Given a user name for a step, split it into the individual pieces.

  Examples:
     _SplitStep('Transform/Step') = ['Transform', 'Step']
     _SplitStep('Read(gs://Foo)/Bar') = ['Read(gs://Foo)', 'Bar']

  Args:
    user_name: The full user_name of the step.
  Returns:
    A list representing the individual pieces of the step name.
  """
  parens = 0
  accum = []
  step_parts = []
  for piece in user_name.split('/'):
    parens += piece.count('(') - piece.count(')')
    accum.append(piece)
    if parens == 0:
      step_parts.append(''.join(accum))
      del accum[:]
    else:
      accum.append('/')

  # If the name contained mismatched parentheses, treat everything after the
  # previous slash as the last step-part.
  if accum:
    step_parts.append(accum)
  return step_parts


def _UnflattenStepsToClusters(steps):
  """Extract a hierarchy from the steps provided.

  The `step graph' is constructed as follows:

    1. Every node has a `name'. This is flat, something like "s1", "s100".
    2. Each node can depend on others. These edges are specified by "name".
    3. Each node can also have a user_name, like "Foo/Bar". This name creates
       a hierarchy of subgraphs (eg., Foo/Bar and Foo/Baz are in the same
       cluster).

  Args:
    steps: A list of steps from the Job message.
  Returns:
    A Cluster representing the root of the step hierarchy.
  """
  root = _Cluster(None, '')
  for step in steps:
    step_path = _SplitStep(step['properties'].get('user_name', step['name']))
    node = root
    for piece in step_path:
      node = node.GetOrAddChild(piece)
    node.SetStep(step)
  return root


def _EscapeGraphvizId(name):
  """Escape a string for use as in Graphviz.

  Args:
    name: The string to escape.

  Returns:
    The `name', with double-quotes escaped, and quotes around it.

  Raises:
    exceptions.UnsupportedNameException: If the name is incompatible with
      Graphviz ID escaping.
  """
  if name.endswith('\\'):
    raise exceptions.UnsupportedNameException(
        'Unsupported name for Graphviz ID escaping: {0!r}'.format(name))
  return '"{0}"'.format(name.replace('"', '\\"'))


_NODE_FORMAT = (
    '{name} [label={user_name}, tooltip={full_name}'
    ', style=filled, fillcolor=white];')


def _YieldGraphvizClusters(cluster, parent=None):
  if cluster.IsLeaf():
    step = cluster.GetStep()
    yield _NODE_FORMAT.format(
        name=_EscapeGraphvizId(step['name']),
        full_name=_EscapeGraphvizId(cluster.Name()),
        user_name=_EscapeGraphvizId(cluster.Name(relative_to=parent)))
  elif cluster.IsSingleton() or cluster.IsRoot():
    for unused_key, subcluster in cluster.Children():
      for line in _YieldGraphvizClusters(subcluster, parent=parent):
        yield line
  else:
    full_name = cluster.Name()
    yield 'subgraph {0} {{'.format(_EscapeGraphvizId('cluster ' + full_name))
    yield 'style=filled;'
    yield 'bgcolor=white;'
    yield 'labeljust=left;'
    yield 'tooltip={0};'.format(_EscapeGraphvizId(full_name))
    yield 'label={0};'.format(_EscapeGraphvizId(cluster.Name(parent)))
    for unused_key, subgroup in cluster.Children():
      for line in _YieldGraphvizClusters(subgroup, parent=cluster):
        yield line
    yield '}'


_EDGE_FORMAT = ('{edge_source} -> {edge_dest} '
                '[taillabel={edge_output}, style={style}];')


def _GraphvizEdge(step_name, output_ref, style='solid'):
  """Returns an edge from the output referred to by output_ref to step_name.

  Args:
    step_name: String identifying the step with the dependency.
    output_ref: Output-reference dictionary to start the edge at.
    style: The style for the edge.

  Returns:
    A string representing the edge in Graphviz format.
  """
  return _EDGE_FORMAT.format(
      edge_source=_EscapeGraphvizId(output_ref['step_name']),
      edge_dest=_EscapeGraphvizId(step_name),
      edge_output=_EscapeGraphvizId(output_ref['output_name']),
      style=style)


def _YieldGraphvizEdges(step):
  """Output Graphviz edges for the given step.

  Args:
    step: Step to write edges for.

  Yields:
    The Graphviz edge lines for the given step.
  """
  step_name = step['name']

  par_input = step['properties'].get('parallel_input', None)
  if par_input:
    yield _GraphvizEdge(step_name, par_input)

  for other_input in step['properties'].get('inputs', []):
    yield _GraphvizEdge(step_name, other_input)

  for side_input in step['properties'].get('non_parallel_inputs', {}).values():
    yield _GraphvizEdge(step_name, side_input, style='dashed')


def YieldGraphviz(steps, graph_name=None):
  """Given a root cluster produce the Graphviz DOT format.

  No attempt is made to produce `pretty' output.

  Args:
    steps: A list of steps from the Job message.
    graph_name: The name of the graph to output.

  Yields:
    The lines representing the step-graph in Graphviz format.
  """
  yield 'strict digraph {graph_name} {{'.format(
      graph_name=_EscapeGraphvizId(graph_name or 'G'))

  # Output the step nodes in the proper clusters.
  root = _UnflattenStepsToClusters(steps)
  for line in _YieldGraphvizClusters(root):
    yield line

  # Output the edges.
  yield ''
  for step in steps:
    for line in _YieldGraphvizEdges(step):
      yield line

  # End the graph.
  yield '}'
