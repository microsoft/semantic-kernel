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

"""Help search filter rewrite.

Converts Cloud SDK filter expressions to nested terms prefixed by AND and OR
operators.

Usage:

  from googlecloudsdk.command_lib.search_help import filter_rewrite

  _, terms = filter_rewrite.SearchTerms().Rewrite(expression_string)

Examples:

    "a b OR c" =>
    [
      "AND",
      {
        "a": null
      },
      [
        "OR",
        {
          "b": null
        },
        {
          "c": null
        }
      ]
    ]

    "flag:a release:alpha" =>
    [
      "AND",
      {
        "a": "flag"
      },
      {
        "alpha": "release"
      }
    ]
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.resource import resource_expr_rewrite


class Error(exceptions.Error):
  """Exceptions for this module."""


class OperatorNotSupportedError(Error):
  """Operator not supported."""


class SearchTerms(resource_expr_rewrite.Backend):
  """A resource filter backend that produces help search terms."""

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand>."""
    del key_type  # unused in RewriteTerm
    if op != ':':
      raise OperatorNotSupportedError(
          'The [{}] operator is not supported.'.format(op))
    return [{operand: key}]

  def RewriteGlobal(self, call):
    """Rewrites global restriction <call>."""
    return [{call.term: None}]

  @staticmethod
  def _SimplifyLogical(op, left, right):
    """Simplifies the binary logical operator subexpression 'left op right'.

    Adjacent nested terms with the same 'AND' or 'OR' binary logical operator
    are flattened.

    For example,
      ['AND', {'a': None}, ['AND', {'b': None}, {'c', None}]]
    simplifies to
      ['AND', {'a': None}, {'b': None}, {'c', None}]

    Args:
      op: The subexpression binary op, either 'AND' or 'OR'.
      left: The left expression. Could be a term, 'AND' or 'OR' subexpression.
      right: The right expression. Could be a term, 'AND' or 'OR' subexpression.

    Returns:
      The simplified binary logical operator subexpression.
    """
    inv = 'AND' if op == 'OR' else 'OR'
    if left[0] == op:
      if right[0] == inv:
        return left + [right]
      if right[0] == op:
        right = right[1:]
      return left + right
    if left[0] == inv:
      if right[0] in [op, inv]:
        return [op, left, right]
      return [op, left] + right
    if right[0] == inv:
      return [op] + left + [right]
    if right[0] == op:
      right = right[1:]
    return [op] + left + right

  def RewriteAND(self, left, right):
    """Rewrites <left AND right>."""
    return self._SimplifyLogical('AND', left, right)

  def RewriteOR(self, left, right):
    """Rewrites <left OR right>."""
    return self._SimplifyLogical('OR', left, right)

  def RewriteNOT(self, expression):
    """Rewrites <NOT expression>."""
    raise OperatorNotSupportedError(
        'The [{}] operator is not supported.'.format('NOT'))
