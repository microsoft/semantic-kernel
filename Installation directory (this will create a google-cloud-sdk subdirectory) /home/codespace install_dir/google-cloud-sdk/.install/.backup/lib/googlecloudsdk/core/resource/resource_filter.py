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

"""Cloud resource list filter expression parser.

Left-factorized BNF Grammar:

  expr        : adjterm adjtail            # gcloud: LF has andterm here

  adjtail     : nil
              | expr

  adjterm     : orterm ortail

  ortail      : nil
              | or adjterm

  orterm      : andterm andtail

  andtail     : nil
              | and orterm

  andterm     : term
              | not term

  term        : key operator operand
              | '-'key operator operand
              | function '(' args ')'
              | '(' expr ')'

  key         : member keytail

  keytail     : nil
              | '.' key
              | '.' function '(' args ')'   # gcloud: LF extension

  member      : name
              | name [ integer ]            # gcloud: LF extension
              | name [ ]                    # gcloud: LF extension

  args        : nil
              | arglist

  arglist     | operand arglisttail

  arglisttail : nil
              | ',' arglist

  and       := 'AND'
  not       := 'NOT'
  or        := 'OR'
  operator  := ':' | '=' | '<' | '<=' | '>=' | '>' | '!=' | '~' | '!~'
  function  := < name in symbol table >
  name      := < resource identifier name >
  operand   := < token terminated by <space> |
               '(' operand ... ')' |        # for the : and = operators only
               <EndOfInput> >
  integer   := < positive or negative integer >

Example:
  expression = filter-expression-string
  resources = [JSON-serilaizable-object]

  query = resource_filter.Compile(expression)
  for resource in resources:
    if query.Evaluate(resource):
      ProcessMatchedResource(resource)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_expr
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_property

import six


class _Parser(object):
  """List filter expression parser.

  A filter expression is compiled by passing the expression string to the
  Parser(), which calls the Backend() code generator to produce an Evaluate()
  method. The default resource_expr.Backend() generates a Boolean
  Evaluate(resource) that returns True if resource matches the filter
  expression. Other backends may generate an Evaluate(None) that rewrites the
  filter expression to a different syntax, for example, to convert a filter
  expression to a server-side expression in the server API filtering syntax.

  Attributes:
    _LOGICAL: List of logical operator names.
    _backend: The expression tree generator module.
    _defaults: Resource projection defaults (for default symbols and aliases).
    _lex: The resource_lex.Lexer filter expression lexer.
    _operator: Dictionary of all search term operators.
    _operator_char_1: The first char of all search term operators.
    _operator_char_2: The second char of all search term operators.
    _parenthesize: A LIFO stack of _OP_* sets for each (...) level. Used to
      determine when AND and OR are combined in the same parenthesis group.
  """
  _OP_AND, _OP_OR = six.moves.range(2)

  _LOGICAL = ['AND', 'NOT', 'OR']

  def __init__(self, backend=None, defaults=None):
    self._backend = backend or resource_expr.Backend()
    self._defaults = defaults or resource_projection_spec.ProjectionSpec()
    self._operator_char_1 = ''
    self._operator_char_2 = ''
    self._operator = {
        ':': self._backend.ExprHAS, '=': self._backend.ExprEQ,
        '!=': self._backend.ExprNE, '<': self._backend.ExprLT,
        '<=': self._backend.ExprLE, '>=': self._backend.ExprGE,
        '>': self._backend.ExprGT, '~': self._backend.ExprRE,
        '!~': self._backend.ExprNotRE}
    # Operator names are length 1 or 2. This loop precomputes _operator_char_1
    # and _operator_char_2 for _ParseOperator to determine both valid and
    # invalid operator names.
    for operator in self._operator:
      c = operator[0]
      if c not in self._operator_char_1:
        self._operator_char_1 += c
      if len(operator) < 2:
        continue
      c = operator[1]
      if c not in self._operator_char_2:
        self._operator_char_2 += c
    self._lex = None
    self._parenthesize = [set()]

  def _CheckParenthesization(self, op):
    """Checks that AND and OR do not appear in the same parenthesis group.

    This method is called each time an AND or OR operator is seen in an
    expression. self._parenthesize[] keeps track of AND and OR operators seen in
    the nested parenthesis groups. ExpressionSyntaxError is raised if both AND
    and OR appear in the same parenthesis group. The top expression with no
    parentheses is considered a parenthesis group.

    The One-Platform list filter spec on which this parser is based has an
    unconventional OR higher than AND logical operator precedence. Allowing that
    in the Cloud SDK would lead to user confusion and many bug reports. To avoid
    that and still be true to the spec this method forces expressions containing
    AND and OR combinations to be fully parenthesized so that the desired
    precedence is explicit and unambiguous.

    Args:
      op: self._OP_AND or self._OP_OR.

    Raises:
      ExpressionSyntaxError: AND and OR appear in the same parenthesis group.
    """
    self._parenthesize[-1].add(op)
    if len(self._parenthesize[-1]) > 1:
      raise resource_exceptions.ExpressionSyntaxError(
          'Parenthesis grouping is required when AND and OR are '
          'are combined [{0}].'.format(self._lex.Annotate()))

  def _ParseKey(self):
    """Parses a key with optional trailing transforms.

    Raises:
      ExpressionSyntaxError: Missing term, unknown transform function.

    Returns:
      (key, transform):
        key: The key expression, None means transform is a global restriction.
        transform: A transform call object if not None. If key is None then the
          transform is a global restriction.
    """
    here = self._lex.GetPosition()
    key = self._lex.Key()
    if key and key[0] in self._LOGICAL:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term expected [{0}].'.format(self._lex.Annotate(here)))
    if self._lex.IsCharacter('(', eoi_ok=True):
      func_name = key.pop()
      return key, self._lex.Transform(func_name, 0)
    return key, None

  def _ParseOperator(self):
    """Parses an operator token.

    All operators match the RE [_operator_char_1][_operator_char_2]. Invalid
    operators are 2 character sequences that are not valid operators and
    match the RE [_operator_char_1][_operator_char_1+_operator_char_2].

    Raises:
      ExpressionSyntaxError: The operator spelling is malformed.

    Returns:
      The operator backend expression, None if the next token is not an
      operator.
    """
    if not self._lex.SkipSpace():
      return None
    here = self._lex.GetPosition()
    op = self._lex.IsCharacter(self._operator_char_1)
    if not op:
      return None
    if not self._lex.EndOfInput():
      o2 = self._lex.IsCharacter(self._operator_char_1 + self._operator_char_2)
      if o2:
        op += o2
    if op not in self._operator:
      raise resource_exceptions.ExpressionSyntaxError(
          'Malformed operator [{0}].'.format(self._lex.Annotate(here)))
    self._lex.SkipSpace(token='Term operand')
    return self._operator[op]

  def _ParseTerm(self, must=False):
    """Parses a [-]<key> <operator> <operand> term.

    Args:
      must: Raises ExpressionSyntaxError if must is True and there is no
        expression.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      The new backend expression tree.
    """
    here = self._lex.GetPosition()
    if not self._lex.SkipSpace():
      if must:
        raise resource_exceptions.ExpressionSyntaxError(
            'Term expected [{0}].'.format(self._lex.Annotate(here)))
      return None

    # Check for end of (...) term.
    if self._lex.IsCharacter(')', peek=True):
      # The caller will determine if this ends (...) or is a syntax error.
      return None

    # Check for start of (...) term.
    if self._lex.IsCharacter('('):
      self._parenthesize.append(set())
      tree = self._ParseExpr()
      # Either the next char is ')' or we hit an end of expression syntax error.
      self._lex.IsCharacter(')')
      self._parenthesize.pop()
      return tree

    # Check for term inversion.
    invert = self._lex.IsCharacter('-')

    # Parse the key.
    here = self._lex.GetPosition()
    syntax_error = None
    try:
      key, transform = self._ParseKey()
      restriction = None
    except resource_exceptions.ExpressionSyntaxError as e:
      syntax_error = e
      # An invalid key could be a global restriction.
      self._lex.SetPosition(here)
      restriction = self._lex.Token(resource_lex.OPERATOR_CHARS, space=False)
      transform = None
      key = None

    # Parse the operator.
    here = self._lex.GetPosition()
    operator = self._ParseOperator()
    if not operator:
      if transform and not key:
        # A global restriction function.
        tree = self._backend.ExprGlobal(transform)
      elif transform:
        # key.transform() must be followed by an operator.
        raise resource_exceptions.ExpressionSyntaxError(
            'Operator expected [{0}].'.format(self._lex.Annotate(here)))
      elif restriction in ['AND', 'OR']:
        raise resource_exceptions.ExpressionSyntaxError(
            'Term expected [{0}].'.format(self._lex.Annotate()))
      elif isinstance(syntax_error, resource_exceptions.UnknownTransformError):
        raise syntax_error  # pylint: disable=raising-bad-type, previous line checked for valid type, just sayin
      else:
        # A global restriction on key.
        if not restriction:
          restriction = resource_lex.GetKeyName(key, quote=False)
        pattern = re.compile(re.escape(restriction), re.IGNORECASE)
        name = resource_projection_spec.GLOBAL_RESTRICTION_NAME
        tree = self._backend.ExprGlobal(
            resource_lex.MakeTransform(
                name,
                self._defaults.symbols.get(
                    name,
                    resource_property.EvaluateGlobalRestriction),
                args=[restriction, pattern]))
      if invert:
        tree = self._backend.ExprNOT(tree)
      return tree
    elif syntax_error:
      raise syntax_error  # pylint: disable=raising-bad-type

    # Parse the operand.
    self._lex.SkipSpace(token='Operand')
    here = self._lex.GetPosition()
    if any([self._lex.IsString(x) for x in self._LOGICAL]):
      raise resource_exceptions.ExpressionSyntaxError(
          'Logical operator not expected [{0}].'.format(
              self._lex.Annotate(here)))
    # The '=' and ':' operators accept '('...')' list operands.
    if (operator in (self._backend.ExprEQ, self._backend.ExprHAS) and
        self._lex.IsCharacter('(')):
      # List valued operand.
      operand = [arg for arg in self._lex.Args(separators=' \t\n,')
                 if arg not in self._LOGICAL]
    else:
      operand = self._lex.Token('()')
    if operand is None:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term operand expected [{0}].'.format(self._lex.Annotate(here)))

    # Make an Expr node for the term.
    tree = operator(key=key, operand=self._backend.ExprOperand(operand),
                    transform=transform)
    if invert:
      tree = self._backend.ExprNOT(tree)
    return tree

  def _ParseAndTerm(self, must=False):
    """Parses an andterm term.

    Args:
      must: Raises ExpressionSyntaxError if must is True and there is no
        expression.

    Returns:
      The new backend expression tree.
    """
    if self._lex.IsString('NOT'):
      return self._backend.ExprNOT(self._ParseTerm(must=True))
    return self._ParseTerm(must=must)

  def _ParseAndTail(self, tree):
    """Parses an andtail term.

    Args:
      tree: The backend expression tree.

    Returns:
      The new backend expression tree.
    """
    if self._lex.IsString('AND'):
      self._CheckParenthesization(self._OP_AND)
      tree = self._backend.ExprAND(tree, self._ParseOrTerm(must=True))
    return tree

  def _ParseOrTerm(self, must=False):
    """Parses an orterm term.

    Args:
      must: Raises ExpressionSyntaxError if must is True and there is no
        expression.

    Raises:
      ExpressionSyntaxError: Term expected in expression.

    Returns:
      The new backend expression tree.
    """
    tree = self._ParseAndTerm()
    # In case the backend is a rewriter, the tree from AndTerm can be None if
    # only frontend-only fields are present in this part of the term. We still
    # need to parse the rest of the expression if it exists.
    if tree or self._backend.IsRewriter():
      tree = self._ParseAndTail(tree)
    elif must:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term expected [{0}].'.format(self._lex.Annotate()))
    return tree

  def _ParseOrTail(self, tree):
    """Parses an ortail term.

    Args:
      tree: The backend expression tree.

    Returns:
      The new backend expression tree.
    """
    if self._lex.IsString('OR'):
      self._CheckParenthesization(self._OP_OR)
      tree = self._backend.ExprOR(tree, self._ParseAdjTerm(must=True))
    return tree

  def _ParseAdjTerm(self, must=False):
    """Parses an adjterm term.

    Args:
      must: ExpressionSyntaxError if must is True and there is no expression.

    Raises:
      ExpressionSyntaxError: Term expected in expression.

    Returns:
      The new backend expression tree.
    """
    tree = self._ParseOrTerm()
    if tree:
      tree = self._ParseOrTail(tree)
    elif must:
      raise resource_exceptions.ExpressionSyntaxError(
          'Term expected [{0}].'.format(self._lex.Annotate()))
    return tree

  def _ParseAdjTail(self, tree):
    """Parses an adjtail term.

    Args:
      tree: The backend expression tree.

    Returns:
      The new backend expression tree.
    """
    if (not self._lex.IsString('AND', peek=True) and
        not self._lex.IsString('OR', peek=True) and
        not self._lex.IsCharacter(')', peek=True) and
        not self._lex.EndOfInput()):
      tree = self._backend.ExprAND(tree, self._ParseExpr(must=True))
    return tree

  def _ParseExpr(self, must=False):
    """Parses an expr term.

    Args:
      must: ExpressionSyntaxError if must is True and there is no expression.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      The new backend expression tree.
    """
    tree = self._ParseAdjTerm()
    if tree:
      tree = self._ParseAdjTail(tree)
    elif must and not self._backend.IsRewriter():
      raise resource_exceptions.ExpressionSyntaxError(
          'Term expected [{0}].'.format(self._lex.Annotate()))
    return tree

  def Parse(self, expression):
    """Parses a resource list filter expression.

    This is a hand-rolled recursive descent parser based directly on the
    left-factorized BNF grammar in the file docstring. The parser is not thread
    safe. Each thread should use distinct _Parser objects.

    Args:
      expression: A resource list filter expression string.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      tree: The backend expression tree.
    """
    self._lex = resource_lex.Lexer(expression, defaults=self._defaults)
    tree = self._ParseExpr()
    if not self._lex.EndOfInput():
      raise resource_exceptions.ExpressionSyntaxError(
          'Unexpected tokens [{0}] in expression.'.format(self._lex.Annotate()))
    self._lex = None
    return tree or self._backend.ExprTRUE()


def GetAllKeys(expression):
  """Recursively collects all keys in compiled filter expression."""
  keys = set()
  if expression.contains_key:
    keys.add(tuple(expression.key))
  for _, obj in six.iteritems(vars(expression)):
    if hasattr(obj, 'contains_key'):
      keys |= GetAllKeys(obj)
  return keys


def Compile(expression, defaults=None, backend=None):
  """Compiles a resource list filter expression.

  Args:
    expression: A resource list filter expression string.
    defaults: Resource projection defaults (for default symbols and aliases).
    backend: The backend expression tree generator module, resource_expr
      if None.

  Returns:
    A backend expression tree.

  Example:
    query = resource_filter.Compile(expression)
    for resource in resources:
      if query.Evaluate(resource):
        ProcessMatchedResource(resource)
  """
  return _Parser(defaults=defaults, backend=backend).Parse(expression)
