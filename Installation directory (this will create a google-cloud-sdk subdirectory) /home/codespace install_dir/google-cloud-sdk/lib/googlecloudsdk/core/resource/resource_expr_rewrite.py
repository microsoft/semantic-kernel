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

"""Cloud resource filter expression rewrite backend classes.

These classes are alternate resource_filter.Compile backends that rewrite
expressions instead of evaluating them. To rewrite a filter expression string:

  rewriter = resource_expr_rewrite.Backend()
  frontend_expr, backend_expr = rewriter.Rewrite(filter_expression_string)

It is possible for a rewritten expression to collapse to None. This means that
there is no equivalent server-side expression, i.e., no server-side pruning is
possible.

These rewrites can only prune expressions that will be False client-side.
In this sense a rewrite => None means "the client side will figure it out".
This results in a backend expression that can be applied server-side to prune
the resources passed back to the client-side, where the full filter expression
is applied. The result will be the same whether or not the backend filter is
applied. The only difference would be the number of resources transmitted
from the server back to the client.

None is the value for keys and operators not supported by the backend.
ExprTRUE, ExprAND, ExprOR and ExprNOT do expression rewrites based on None:

  TRUE => None
  None AND x => x
  x AND None => x
  x OR None => None
  None OR x => None
  NOT None => None
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.resource import resource_transform


class _Expr(object):
  """An expression rewrite object that evaluates to the rewritten expression."""

  def __init__(self, expr):
    self.expr = expr

  def Rewrite(self):
    """Returns the server side string rewrite of the filter expression."""
    return self.expr


class _BelieveMe(dict):
  """A symbols dict with nothing that claims everything."""

  def get(self, obj, type=None):  # pylint: disable=redefined-builtin, overridden class expects this prototype
    del obj, type  # unused in get
    return self.get


class BackendBase(object):
  """Cloud resource filter expression rewrite backend base.

  All rewrites default to None. Use this class for target expressions that
  implement a small subset of OnePlatform expressions.

  Attributes:
    frontend_fields: A set of dotted field names supported in the frontend.
    message: The resource proto message object that describes all fields
      available in the backend.
    partial_rewrite: True if the most recent Rewrite() backend_expression is
      a partial rewrite of the original expression. False means that the entire
      original expression was rewritten and that frontend_expression can be
      ignored.
  """

  def __init__(self, frontend_fields=None, message=None):
    self.frontend_fields = frontend_fields
    self.message = message
    self.partial_rewrite = False

  def Rewrite(self, expression, defaults=None):
    """Returns (frontend_expression, backend_expression) for expression.

    There are 3 outcomes:
      (None, backend) -- only need to apply the backend expression
      (frontend, None) -- only need to apply the frontend expression
      (frontend, backend) -- must apply both frontend and backend expressions

    Args:
      expression: The expression string to rewrite.
      defaults: resource_projection_spec.ProjectionSpec defaults.

    Returns:
      Returns (frontend_expression, backend_expression) for expression.
    """
    if defaults and defaults.symbols:
      conditionals = defaults.symbols.get(
          resource_transform.GetTypeDataName('conditionals'))
      if hasattr(conditionals, 'flatten') and conditionals.flatten:
        # If --flatten flag is presented we cannot do serverside filtering.
        return expression, None
    self.partial_rewrite = False
    defaults = resource_projection_spec.ProjectionSpec(defaults=defaults)
    defaults.symbols = _BelieveMe()
    backend_expression = resource_filter.Compile(
        expression, backend=self, defaults=defaults).Rewrite()
    frontend_expression = expression if self.partial_rewrite else None
    if frontend_expression and frontend_expression.isspace():
      frontend_expression = None
    return frontend_expression, backend_expression

  def Expr(self, expr):
    if not expr:
      self.partial_rewrite = True
    return _Expr(expr)

  def RewriteAND(self, unused_left, unused_right):
    """Rewrites <left AND right>."""
    return None

  def RewriteOR(self, unused_left, unused_right):
    """Rewrites <left OR right>."""
    return None

  def RewriteNOT(self, unused_expr):
    """Rewrites <NOT expr>."""
    return None

  def RewriteGlobal(self, unused_call):
    """Rewrites global restriction <call>."""
    return None

  def RewriteOperand(self, unused_operand):
    """Rewrites an operand."""
    return None

  def RewriteTerm(self, unused_key, unused_op, unused_operand,
                  unused_key_type=None):
    """Rewrites <key op operand>."""
    return None

  def Parenthesize(self, expression):
    """Returns expression enclosed in (...) if it contains AND/OR."""
    # Check for unparenthesized AND|OR.
    lex = resource_lex.Lexer(expression)
    while True:
      tok = lex.Token(' ()', balance_parens=True)
      if not tok:
        break
      if tok in ['AND', 'OR']:
        return '({expression})'.format(expression=expression)
    return expression

  def Quote(self, value, always=False):
    """Returns value or value "..." quoted with C-style escapes if needed.

    Args:
      value: The string value to quote if needed.
      always: Always quote non-numeric value if True.

    Returns:
      A string: value or value "..." quoted with C-style escapes if needed or
      requested.
    """
    # First check for numeric constants that are never quoted.
    try:
      return str(int(value))
    except ValueError:
      pass
    try:
      return str(float(value))
    except ValueError:
      pass

    # value is a string.
    chars = []
    enclose = always
    escaped = False
    for c in value:
      if escaped:
        escaped = False
      elif c == '\\':
        chars.append(c)
        chars.append(c)
        escaped = True
        enclose = True
      elif c == '"':
        chars.append('\\')
        enclose = True
      elif c.isspace() or c == "'":
        enclose = True
      chars.append(c)
    string = ''.join(chars)

    return '"{string}"'.format(string=string) if enclose else string

  def QuoteOperand(self, operand, always=False):
    """Returns operand enclosed in "..." if necessary.

    Args:
      operand: A string operand or list of string operands. If a list then each
        list item is quoted.
      always: Always quote if True.

    Returns:
      A string: operand enclosed in "..." if necessary.
    """
    if isinstance(operand, list):
      operands = [self.Quote(x, always=always) for x in operand]
      return '(' + ','.join([x for x in operands if x is not None]) + ')'
    return self.Quote(operand, always=always)

  def Term(self, key, op, operand, transform, args):
    """Returns the rewritten backend term expression.

    Args:
      key: The parsed key.
      op: The operator name.
      operand: The operand.
      transform: The transform object if a transform was specified.
      args: The transform args if a transform was specified.

    Raises:
      UnknownFieldError: If key is not supported on the frontend and backend.

    Returns:
      The rewritten backend term expression.
    """

    # No backend transforms.
    if transform or args:
      return self.Expr(None)

    # Determine the key type if possible.
    key_name = resource_lex.GetKeyName(key)
    if self.message:
      try:
        # key supported in the backend.
        key_type, key = resource_property.GetMessageFieldType(
            key, self.message)
      except KeyError:
        # key not supported in the backend -- check the frontend if possible.
        if (self.frontend_fields is not None and
            not resource_property.LookupField(key, self.frontend_fields)):
          raise resource_exceptions.UnknownFieldError(
              'Unknown field [{}] in expression.'.format(key_name))
        return self.Expr(None)
      else:
        # GetMessageFieldType camelCase/lower_snake_case normalizes key.
        key_name = resource_lex.GetKeyName(key)
    else:
      # Not enough info to determine the key type.
      key_type = None
    return self.Expr(self.RewriteTerm(key_name, op, operand, key_type))

  def ExprTRUE(self):
    return _Expr(None)

  def ExprAND(self, left, right):
    """Returns an AND expression node."""
    if left:
      left = left.Rewrite()
    if right:
      right = right.Rewrite()
    # None AND x => x
    if not left:
      self.partial_rewrite = True
      return self.Expr(right) if right else None
    # x AND None => x
    if not right:
      self.complete = False
      return self.Expr(left)
    return self.Expr(self.RewriteAND(left, right))

  def ExprOR(self, left, right):
    """Returns an OR expression node."""
    if left:
      left = left.Rewrite()
    # None OR x => None
    if not left:
      return self.Expr(None)
    # x OR None => None
    if right:
      right = right.Rewrite()
    if not right:
      return self.Expr(None)
    return self.Expr(self.RewriteOR(left, right))

  def ExprNOT(self, expr):
    if expr:
      expr = expr.Rewrite()
    if not expr:
      return self.Expr(None)
    return self.Expr(self.RewriteNOT(expr))

  def ExprGlobal(self, call):
    return self.Expr(self.RewriteGlobal(call))

  def ExprOperand(self, value):
    return value

  def ExprLT(self, key, operand, transform=None, args=None):
    return self.Term(key, '<', operand, transform, args)

  def ExprLE(self, key, operand, transform=None, args=None):
    return self.Term(key, '<=', operand, transform, args)

  def ExprHAS(self, key, operand, transform=None, args=None):
    return self.Term(key, ':', operand, transform, args)

  def ExprEQ(self, key, operand, transform=None, args=None):
    return self.Term(key, '=', operand, transform, args)

  def ExprNE(self, key, operand, transform=None, args=None):
    return self.Term(key, '!=', operand, transform, args)

  def ExprGE(self, key, operand, transform=None, args=None):
    return self.Term(key, '>=', operand, transform, args)

  def ExprGT(self, key, operand, transform=None, args=None):
    return self.Term(key, '>', operand, transform, args)

  def ExprRE(self, key, operand, transform=None, args=None):
    return self.Term(key, '~', operand, transform, args)

  def ExprNotRE(self, key, operand, transform=None, args=None):
    return self.Term(key, '!~', operand, transform, args)

  def IsRewriter(self):
    return True


class Backend(BackendBase):
  """Rewrites for OnePlatform server side filter expressions.

  This class rewrites client side expressions to OnePlatform server side
  expressions. The only difference is the server side does not support the
  regular expression ~ and !~ operators. Use this class for target expressions
  that implement a large subset of OnePlatform expressions.
  """

  def RewriteAND(self, left, right):
    """Rewrites <left AND right>."""
    return '{left} AND {right}'.format(left=self.Parenthesize(left),
                                       right=self.Parenthesize(right))

  def RewriteOR(self, left, right):
    """Rewrites <left OR right>."""
    return '{left} OR {right}'.format(left=self.Parenthesize(left),
                                      right=self.Parenthesize(right))

  def RewriteNOT(self, expression):
    """Rewrites <NOT expression>."""
    return 'NOT {expression}'.format(expression=self.Parenthesize(expression))

  def RewriteOperand(self, operand):
    """Rewrites an operand."""
    return self.QuoteOperand(operand)

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand>."""
    del key_type  # unused in RewriteTerm
    if op in ['~', '!~']:
      return None
    arg = self.RewriteOperand(operand)
    if arg is None:
      return None
    return '{key}{op}{operand}'.format(key=key, op=op, operand=arg)
