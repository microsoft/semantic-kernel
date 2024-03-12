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
"""Common methods to display parts of SQL query results."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from functools import partial
from apitools.base.py import encoding
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import text
from sqlparse import lexer
from sqlparse import tokens as T


def _GetAdditionalProperty(properties, property_key, not_found_value='Unknown'):
  """Gets the value for the given key in a list of properties.

  Looks through a list of properties and tries to find the value for the given
  key. If it's not found, not_found_value is returned.

  Args:
    properties: A dictionary of key string, value string pairs.
    property_key: The key string for which we want to get the value.
    not_found_value: The string value to return if the key is not found.

  Returns:
    A string containing the value for the given key, or `not_found_value` if
    the key is not found.
  """
  for prop in properties:
    if prop.key == property_key:
      if hasattr(prop, 'value'):
        return prop.value
      break
  return not_found_value


def _ConvertToTree(plan_nodes):
  """Creates tree of Node objects from the plan_nodes in server response.

  Args:
    plan_nodes (spanner_v1_messages.PlanNode[]): The plan_nodes from the server
      response. Plan nodes are topologically sorted.

  Returns:
    A Node, root of a tree built from `plan_nodes`.
  """
  # plan_nodes is a topologically sorted list, with the root node first.
  return _BuildSubTree(plan_nodes, plan_nodes[0])


def _BuildSubTree(plan_nodes, node):
  """Helper for building the subtree of a query plan node.

  Args:
    plan_nodes (spanner_v1_messages.PlanNode[]): The plan_nodes from the server
      response. Plan nodes are topologically sorted.
    node (spanner_v1_messages.PlanNode): The root node of the subtree to be
      built.

  Returns:
    A Node object.
  """
  children = None
  if node.childLinks:
    children = [_BuildSubTree(plan_nodes, plan_nodes[link.childIndex])
                for link in node.childLinks]
  return Node(node, children)


def _ConvertToStringValue(prop):
  """Converts the prop to a string if it exists.

  Args:
    prop (object_value): The value returned from _GetAdditionalProperty.

  Returns:
    A string value for the given prop, or the `not_found_value` if the prop does
    not exist.
  """
  return getattr(prop, 'string_value', prop)


def _DisplayNumberOfRowsModified(row_count, is_exact_count, out):
  """Prints number of rows modified by a DML statement.

  Args:
    row_count: Either the exact number of rows modified by statement or the
      lower bound of rows modified by a Partitioned DML statement.
    is_exact_count: Boolean stating whether the number is the exact count.
    out: Output stream to which we print.
  """
  if is_exact_count:
    output_str = 'Statement modified {} {}'
  else:
    output_str = 'Statement modified a lower bound of {} {}'

  if row_count == 1:
    out.Print(output_str.format(row_count, 'row'))
  else:
    out.Print(output_str.format(row_count, 'rows'))


def QueryHasDml(sql):
  """Determines if the sql string contains a DML query.

  Args:
    sql (string): The sql string entered by the user.

  Returns:
    A boolean.
  """
  sql = sql.lstrip().lower()
  tokenized = lexer.tokenize(sql)
  for token in list(tokenized):
    has_dml = (
        token == (T.Keyword.DML, 'insert') or
        token == (T.Keyword.DML, 'update') or
        token == (T.Keyword.DML, 'delete'))
    if has_dml:
      return True
  return False


def QueryHasAggregateStats(result):
  """Checks if the given results have aggregate statistics.

  Args:
    result (spanner_v1_messages.ResultSetStats): The stats for a query.

  Returns:
    A boolean indicating whether 'results' contain aggregate statistics.
  """
  return hasattr(
      result, 'stats') and getattr(result.stats, 'queryStats', None) is not None


def DisplayQueryAggregateStats(query_stats, out):
  """Displays the aggregate stats for a Spanner SQL query.

  Looks at the queryStats portion of the query response and prints some of
  the aggregate statistics.

  Args:
    query_stats (spanner_v1_messages.ResultSetStats.QueryStatsValue): The query
      stats taken from the server response to a query.
    out: Output stream to which we print.
  """
  get_prop = partial(_GetAdditionalProperty, query_stats.additionalProperties)
  stats = {
      'total_elapsed_time': _ConvertToStringValue(get_prop('elapsed_time')),
      'cpu_time': _ConvertToStringValue(get_prop('cpu_time')),
      'rows_returned': _ConvertToStringValue(get_prop('rows_returned')),
      'rows_scanned': _ConvertToStringValue(get_prop('rows_scanned')),
      'optimizer_version': _ConvertToStringValue(get_prop('optimizer_version')),
  }
  resource_printer.Print(
      stats,
      'table[box](total_elapsed_time, cpu_time, rows_returned, rows_scanned, optimizer_version)',
      out=out)


def DisplayQueryPlan(result, out):
  """Displays a graphical query plan for a query.

  Args:
    result (spanner_v1_messages.ResultSet): The server response to a query.
    out: Output stream to which we print.
  """
  node_tree_root = _ConvertToTree(result.stats.queryPlan.planNodes)
  node_tree_root.PrettyPrint(out)


def DisplayQueryResults(result, out):
  """Prints the result rows for a query.

  Args:
    result (spanner_v1_messages.ResultSet): The server response to a query.
    out: Output stream to which we print.
  """
  if hasattr(result.stats,
             'rowCountExact') and result.stats.rowCountExact is not None:
    _DisplayNumberOfRowsModified(result.stats.rowCountExact, True, out)

  if hasattr(
      result.stats,
      'rowCountLowerBound') and result.stats.rowCountLowerBound is not None:
    _DisplayNumberOfRowsModified(result.stats.rowCountLowerBound, False, out)

  if result.metadata.rowType.fields:
    # Print "(Unspecified)" for computed columns.
    fields = [
        field.name or '(Unspecified)'
        for field in result.metadata.rowType.fields
    ]

    # Create the format string we pass to the table layout.
    table_format = ','.join('row.slice({0}).join():label="{1}"'.format(i, f)
                            for i, f in enumerate(fields))
    rows = [{
        'row': encoding.MessageToPyValue(row.entry)
    } for row in result.rows]

    # Can't use the PrintText method because we want special formatting.
    resource_printer.Print(rows, 'table({0})'.format(table_format), out=out)


class Node(object):
  """Represents a single node in a Spanner query plan.

  Attributes:
    properties (spanner_v1_messages.PlanNode): The details about a given node
      as returned from the server.
    children: A list of children in the query plan of type Node.
  """

  def __init__(self, properties, children=None):
    self.children = children or []
    self.properties = properties

  def _DisplayKindAndName(self, out, prepend, stub):
    """Prints the kind of the node (SCALAR or RELATIONAL) and its name."""
    kind_and_name = '{}{} {} {}'.format(prepend, stub, self.properties.kind,
                                        self.properties.displayName)
    out.Print(kind_and_name)

  def _GetNestedStatProperty(self, prop_name, nested_prop_name):
    """Gets a nested property name on this object's executionStats.

    Args:
      prop_name: A string of the key name for the outer property on
        executionStats.
      nested_prop_name: A string of the key name of the nested property.

    Returns:
      The string value of the nested property, or None if the outermost
      property or nested property don't exist.
    """
    prop = _GetAdditionalProperty(
        self.properties.executionStats.additionalProperties, prop_name, '')
    if not prop:
      return None

    nested_prop = _GetAdditionalProperty(prop.object_value.properties,
                                         nested_prop_name, '')
    if nested_prop:
      return nested_prop.string_value

    return None

  def _DisplayExecutionStats(self, out, prepend, beneath_stub):
    """Prints the relevant execution statistics for a node.

    More specifically, print out latency information and the number of
    executions. This information only exists when query is run in 'PROFILE'
    mode.

    Args:
      out: Output stream to which we print.
      prepend: String that precedes any information about this node to maintain
        a visible hierarchy.
      beneath_stub: String that preserves the indentation of the vertical lines.
    """
    if not self.properties.executionStats:
      return None

    stat_props = []

    num_executions = self._GetNestedStatProperty('execution_summary',
                                                 'num_executions')
    if num_executions:
      num_executions = int(num_executions)
      executions_str = '{} {}'.format(num_executions,
                                      text.Pluralize(num_executions,
                                                     'execution'))
      stat_props.append(executions_str)

    # Total latency and latency unit are always expected to be present when
    # latency exists. Latency exists when the query is run in PROFILE mode.
    mean_latency = self._GetNestedStatProperty('latency', 'mean')
    total_latency = self._GetNestedStatProperty('latency', 'total')
    unit = self._GetNestedStatProperty('latency', 'unit')
    if mean_latency:
      stat_props.append('{} {} average latency'.format(mean_latency, unit))
    elif total_latency:
      stat_props.append('{} {} total latency'.format(total_latency, unit))

    if stat_props:
      executions_stats_str = '{}{} ({})'.format(prepend, beneath_stub,
                                                ', '.join(stat_props))
      out.Print(executions_stats_str)

  def _DisplayMetadata(self, out, prepend, beneath_stub):
    """Prints the keys and values of the metadata for a node.

    Args:
      out: Output stream to which we print.
      prepend: String that precedes any information about this node to maintain
        a visible hierarchy.
      beneath_stub: String that preserves the indentation of the vertical lines.
    """
    if self.properties.metadata:
      additional_props = []
      # additionalProperties looks like: [key: {value: {string_value: str}}]
      for prop in self.properties.metadata.additionalProperties:
        additional_props.append(
            '{}: {}'.format(prop.key, prop.value.string_value))
      metadata = '{}{} {}'.format(prepend, beneath_stub,
                                  ', '.join(sorted(additional_props)))
      out.Print(metadata)

  def _DisplayShortRepresentation(self, out, prepend, beneath_stub):
    if self.properties.shortRepresentation:
      short_rep = '{}{} {}'.format(
          prepend, beneath_stub,
          self.properties.shortRepresentation.description)
      out.Print(short_rep)

  def _DisplayBreakLine(self, out, prepend, beneath_stub, is_root):
    """Displays an empty line between nodes for visual breathing room.

    Keeps in tact the vertical lines connecting all immediate children of a
    node to each other.

    Args:
      out: Output stream to which we print.
      prepend: String that precedes any information about this node to maintain
        a visible hierarchy.
      beneath_stub: String that preserves the indentation of the vertical lines.
      is_root: Boolean indicating whether this node is the root of the tree.
    """
    above_child = '  ' if is_root else ''
    above_child += '  |' if self.children else ''
    break_line = '{}{}{}'.format(prepend, beneath_stub, above_child)
    # It could be the case the beneath_stub adds spaces but above_child doesn't
    # add an additional vertical line, in which case we want to remove the
    # extra trailing spaces.
    out.Print(break_line.rstrip())

  def PrettyPrint(self, out, prepend=None, is_last=True, is_root=True):
    """Prints a string representation of this node in the tree.

    Args:
      out: Output stream to which we print.
      prepend: String that precedes any information about this node to maintain
        a visible hierarchy.
      is_last: Boolean indicating whether this node is the last child of its
        parent.
      is_root: Boolean indicating whether this node is the root of the tree.
    """
    prepend = prepend or ''
    # The symbol immediately before node kind to indicate that this is a child
    # of its parents. All nodes except the root get one.
    stub = '' if is_root else (r'\-' if is_last else '+-')

    # To list additional properties beneath the name, figure out how they should
    # be indented relative to the name's stub.
    beneath_stub = '' if is_root else ('  ' if is_last else '| ')

    self._DisplayKindAndName(out, prepend, stub)
    self._DisplayExecutionStats(out, prepend, beneath_stub)
    self._DisplayMetadata(out, prepend, beneath_stub)
    self._DisplayShortRepresentation(out, prepend, beneath_stub)
    self._DisplayBreakLine(out, prepend, beneath_stub, is_root)

    for idx, child in enumerate(self.children):
      is_last_child = idx == len(self.children) - 1
      # The amount each subsequent level in the tree is indented.
      indent = '   '
      # Connect all immediate children to each other with a vertical line
      # of '|'. Don't extend this line down past the last child node. It's
      # cleaner.
      child_prepend = prepend + (' ' if is_last else '|') + indent
      child.PrettyPrint(
          out, prepend=child_prepend, is_last=is_last_child, is_root=False)
