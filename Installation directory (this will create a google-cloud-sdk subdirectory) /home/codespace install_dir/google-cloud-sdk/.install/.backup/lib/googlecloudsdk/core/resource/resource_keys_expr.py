# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Cloud resource filter expression referenced key backend."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Backend(object):
  """Cloud resource filter expression referenced key backend.

  This is a backend for resource_filter.Parser(). The generated "evaluator" is a
  parsed resource expression tree with branching factor 2 for binary operator
  nodes, 1 for NOT and function nodes, and 0 for TRUE nodes. Evaluation starts
  with expression_tree_root.Evaluate(obj) which recursively evaluates child
  nodes. The Evaluate() method generates the list of parsed keys referenced by
  the expression.

  For a complete backend expression evaluator see core.resource.resource_expr.

  Attributes:
    keys: The set of parsed keys referenced by the expression.
  """

  def __init__(self, supported_key=None):  # pylint: disable=unused-argument
    self.keys = []

  # The remaining methods return an initialized class object.

  def ExprTRUE(self):
    return None

  def ExprAND(self, left, right):
    return _ExprLogical(self, left, right)

  def ExprOR(self, left, right):
    return _ExprLogical(self, left, right)

  def ExprNOT(self, expr):
    return _ExprNOT(self, expr)

  def ExprGlobal(self, unused_func, unused_args):
    return None

  def ExprOperand(self, unused_value):
    return None

  def ExprLT(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprLE(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprHAS(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprEQ(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprNE(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprGE(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprGT(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprRE(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def ExprNotRE(self, key, operand, transform=None, args=None):
    return _ExprOperator(self, key, operand, transform, args)

  def IsRewriter(self):
    return False


# _Expr* class instantiations are done by the Backend.Expr* methods.


class _Expr(object):
  """Expression base class."""

  def __init__(self, backend):
    self.backend = backend

  def Evaluate(self, unused_obj):
    """Returns the set of parsed keys referenced by the exptression.

    Args:
     unused_ obj: The current resource object.

    Returns:
      Returns the set of parsed keys referenced by the exptression.
    """
    return self.backend.keys


class _ExprLogical(_Expr):
  """Base logical operator node.

  Attributes:
    left: Left Expr operand.
    right: Right Expr operand.
  """

  def __init__(self, backend, left, right):
    super(_ExprLogical, self).__init__(backend)
    self._left = left
    self._right = right

  def Evaluate(self, obj):
    self._left.Evaluate(obj)
    self._right.Evaluate(obj)
    return self.backend.keys


class _ExprNOT(_Expr):
  """NOT node."""

  def __init__(self, backend, expr):
    super(_ExprNOT, self).__init__(backend)
    self._expr = expr

  def Evaluate(self, obj):
    self._expr.Evaluate(obj)
    return self.backend.keys


class _ExprOperator(_Expr):
  """Base term (<key operator operand>) node."""

  def __init__(self, backend, key, unused_operand, unused_transform,
               unused_args):
    super(_ExprOperator, self).__init__(backend)
    if key not in self.backend.keys:
      self.backend.keys.append(key)
