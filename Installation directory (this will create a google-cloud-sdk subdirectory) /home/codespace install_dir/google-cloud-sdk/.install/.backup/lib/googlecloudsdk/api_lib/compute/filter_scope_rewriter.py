# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Filter rewrite that determines the equivalent set restriction operands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_expr_rewrite

import six


class FilterScopeRewriter(resource_expr_rewrite.Backend):
  """Resource filter expression rewriter backend.

  This rewriter returns the equivalent set of operands for a set of keys in a
  filter expression. If there are no key restrictions or the key restrictions
  are optional (a term in a top level OR) then None is returned, otherwise the
  specific set of operand literals for the combined restrictions is returned.
  """

  def Rewrite(self, expression, defaults=None, keys=None):
    """Returns (None, specific set of required operands or None).

    Args:
      expression: The filter expression string.
      defaults: The filter/format/projection defaults.
      keys: The set of keys to collect the restriction operands for.

    Returns:
      A (None, operands) tuple where operands is the set of required operands
      or None. The tuple return value matches the base rewriter signature i.e.
      (frontend_rewrite, backend_rewrite) former always being None in this case.
    """
    self._keys = keys or {}
    _, operands = super(FilterScopeRewriter, self).Rewrite(
        expression, defaults=defaults)
    if isinstance(operands, six.string_types):
      operands = set([operands])
    return None, operands

  def RewriteNOT(self, expr):
    """Punt on negation. Only the caller knows the operand universe."""
    return None

  def RewriteOR(self, left, right):
    """OR keeps all operands in play."""
    return None

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites restrictions for keys in self._keys.

    Args:
      key: The dotted resource name.
      op: The operator name.
      operand: The operand string value.
      key_type: The type of key, None if not known.

    Returns:
      A specific set of operands or None.
    """
    if key not in self._keys or op != '=':
      return None
    return operand
