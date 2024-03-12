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

r"""Resource expression lexer.

This class is used to parse resource keys, quoted tokens, and operator strings
and characters from resource filter and projection expression strings. Tokens
are defined by isspace() and caller specified per-token terminator characters.
" or ' quotes are supported, with these literal escapes: \\ => \, \' => ',
\" => ", and \<any-other-character> => \<any-other-character>.

Typical resource usage:

  # Initialize a lexer with the expression string.
  lex = resource_lex.Lexer(expression_string)
  # isspace() separated tokens. lex.SkipSpace() returns False at end of input.
  while lex.SkipSpace():
    # Save the expression string position for syntax error annotation.
    here = lex.GetPosition()
    # The next token must be a key.
    key = lex.Key()
    if not key:
      if lex.EndOfInput():
        # End of input is OK here.
        break
      # There were some characters in the input that did not form a valid key.
      raise resource_exceptions.ExpressionSyntaxError(
          'key expected [{0}].'.format(lex.Annotate(here)))
    # Check if the key is a function call.
    if lex.IsCharacter('('):
      # Collect the actual args and convert numeric args to float or int.
      args = lex.Args(convert=True)
    else:
      args = None
    # Skip an isspace() characters. End of input will fail with an
    # 'Operator expected [...]' resource_exceptions.ExpressionSyntaxError.
    lex.SkipSpace(token='Operator')
    # The next token must be one of these operators ...
    operator = lex.IsCharacter('+-*/&|')
    if not operator:
      # ... one of the operator names.
      if lex.IsString('AND'):
        operator = '&'
      elif lex.IsString('OR'):
        operator = '|'
      else:
        raise resource_exceptions.ExpressionSyntaxError(
            'Operator expected [{0}].'.format(lex.Annotate()))
    # The next token must be an operand. Convert to float or int if possible.
    # lex.Token() by default eats leading isspace().
    operand = lex.Token(convert=True)
    if not operand:
      raise resource_exceptions.ExpressionSyntaxErrorSyntaxError(
          'Operand expected [{0}].'.format(lex.Annotate()))
    # Process the key, args, operator and operand.
    Process(key, args, operator, operand)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import re

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.resource import resource_transform

import six
from six.moves import map  # pylint: disable=redefined-builtin
from six.moves import range  # pylint: disable=redefined-builtin


# Resource keys cannot contain unquoted operator characters.
OPERATOR_CHARS = ':=!<>~()'

# Reserved operator characters. Resource keys cannot contain unquoted reverved
# operator characters. This prevents key/operator clashes in expressions.
_RESERVED_OPERATOR_CHARS = OPERATOR_CHARS + '[].{},+*/%&|^#;?'


class _TransformCall(object):
  """A key transform function call with actual args.

  Attributes:
    name: The transform function name.
    func: The transform function.
    active: The parent projection active level. A transform is active if
      transform.active is None or equal to the caller active level.
    map_transform: If r is a list then apply the transform to each list item
      up to map_transform times. map_transform>1 handles nested lists.
    args: List of function call actual arg strings.
    kwargs: List of function call actual keyword arg strings.
  """

  def __init__(self, name, func, active=0, map_transform=0, args=None,
               kwargs=None):
    self.name = name
    self.func = func
    self.active = active
    self.map_transform = map_transform
    self.args = args or []
    self.kwargs = kwargs or {}

  def __str__(self):
    args = ['<projecton>' if isinstance(
        arg, resource_projection_spec.ProjectionSpec) else arg
            for arg in self.args]
    if self.map_transform > 1:
      prefix = 'map({0}).'.format(self.map_transform)
    elif self.map_transform == 1:
      prefix = 'map().'
    else:
      prefix = ''
    return '{0}{1}({2})'.format(prefix, self.name, ','.join(args))

  def __deepcopy__(self, memo):
    # This avoids recursive ProjectionSpec transforms that deepcopy chokes on.
    return copy.copy(self)


class _Transform(object):
  """An object that contains an ordered list of _TransformCall objects.

  Attributes:
    _conditional: The resource_filter expression string for the if() transform.
    _transforms: The list of _TransformCall objects.
  """

  def __init__(self):
    self._conditional = None
    self._transforms = []

  def __str__(self):
    return '[{0}]'.format('.'.join(map(str, self._transforms)))

  # TODO(b/38445579): Add explicit unit tests for these properties.
  @property
  def active(self):
    """The transform active level or None if always active."""
    return self._transforms[0].active if self._transforms else None

  @property
  def conditional(self):
    """The if() transform conditional expression string."""
    return self._conditional

  @property
  def global_restriction(self):
    """The global restriction string or None if not a global restriction.

    Terms in a fiter expression are sometimes called "restrictions" because
    they restrict or constrain values.  A regular restriction is of the form
    "attribute<op>operand".  A "global restriction" is a term that has no
    attribute or <op>.  It is a bare string that is matched against every
    attribute value in the resource object being filtered.  The global
    restriction matches if any of those values contains the string using case
    insensitive string match.

    Returns:
      The global restriction string or None if not a global restriction.
    """
    if (len(self._transforms) != 1 or
        (self._transforms[0].name !=
         resource_projection_spec.GLOBAL_RESTRICTION_NAME)):
      return None
    return self._transforms[0].args[0]

  @property
  def name(self):
    """The name of the last transform."""
    return self._transforms[-1].name if self._transforms else ''

  @property
  def term(self):
    """The first global restriction term."""
    return self._transforms[0].args[0] if self._transforms else ''

  def IsActive(self, active):
    """Returns True if the Transform active level is None or active."""
    return self._transforms and self.active in (None, active)

  def Add(self, transform):
    """Adds a transform to the list."""
    self._transforms.append(transform)

  def SetConditional(self, expr):
    """Sets the conditional expression string."""
    self._conditional = expr

  def Evaluate(self, obj, original_object=None):
    """Apply the list of transforms to obj and return the transformed value."""
    for transform in self._transforms:
      # If the transform key is 'uri', uri transform function is expecting
      # an object not a dict
      if transform.name == 'uri' and original_object is not None:
        obj = original_object
      if transform.map_transform and resource_property.IsListLike(obj):
        # A transform mapped on a list - transform each list item.
        # map_transform > 1 for nested lists. For example:
        #   abc[].def[].ghi[].map(3)
        # iterates over the items in ghi[] for all abc[] and def[].
        items = obj
        for _ in range(transform.map_transform - 1):
          nested = []
          try:
            # Stop if items is not a list.
            for item in items:
              nested.extend(item)
          except TypeError:
            break
          items = nested
        obj = []
        for item in items:
          obj.append(transform.func(item, *transform.args, **transform.kwargs))
      elif obj or not transform.map_transform:
        obj = transform.func(obj, *transform.args, **transform.kwargs)
    return obj


def MakeTransform(func_name, func, args=None, kwargs=None):
  """Returns a transform call object for func(*args, **kwargs).

  Args:
    func_name: The function name.
    func: The function object.
    args: The actual call args.
    kwargs: The actual call kwargs.

  Returns:
    A transform call object for func(obj, *args, **kwargs).
  """
  calls = _Transform()
  calls.Add(_TransformCall(func_name, func, args=args, kwargs=kwargs))
  return calls


class Lexer(object):
  """Resource expression lexer.

  This lexer handles simple and compound tokens. Compound tokens returned by
  Key() and Args() below are not strictly lexical items (i.e., they are parsed
  against simple grammars), but treating them as tokens here simplifies the
  resource expression parsers that use this class and avoids code replication.

  Attributes:
    _ESCAPE: The quote escape character.
    _QUOTES: The quote characters.
    _defaults: ProjectionSpec object for aliases and symbols defaults.
    _expr: The expression string.
    _position: The index of the next character in _expr to parse.
  """
  _ESCAPE = '\\'
  _QUOTES = '\'"'

  def __init__(self, expression, defaults=None):
    """Initializes a resource lexer.

    Args:
      expression: The expression string.
      defaults: ProjectionSpec object for aliases and symbols defaults.
    """
    self._expr = expression or ''
    self._position = 0
    self._defaults = defaults or resource_projection_spec.ProjectionSpec()

  def EndOfInput(self, position=None):
    """Checks if the current expression string position is at the end of input.

    Args:
      position: Checks position instead of the current expression position.

    Returns:
      True if the expression string position is at the end of input.
    """
    if position is None:
      position = self._position
    return position >= len(self._expr)

  def GetPosition(self):
    """Returns the current expression position.

    Returns:
      The current expression position.
    """
    return self._position

  def SetPosition(self, position):
    """Sets the current expression position.

    Args:
      position: Sets the current position to position. Position should be 0 or a
        previous value returned by GetPosition().
    """
    self._position = position

  def Annotate(self, position=None):
    """Returns the expression string annotated for syntax error messages.

    The current position is marked by '*HERE*' for visual effect.

    Args:
      position: Uses position instead of the current expression position.

    Returns:
      The expression string with current position annotated.
    """
    here = position if position is not None else self._position
    cursor = '*HERE*'  # For visual effect only.
    if here > 0 and not self._expr[here - 1].isspace():
      cursor = ' ' + cursor
    if here < len(self._expr) and not self._expr[here].isspace():
      cursor += ' '
    return '{0}{1}{2}'.format(self._expr[0:here], cursor, self._expr[here:])

  def SkipSpace(self, token=None, terminators=''):
    """Skips spaces in the expression string.

    Args:
      token: The expected next token description string, None if end of input is
        OK. This string is used in the exception message. It is not used to
        validate the type of the next token.
      terminators: Space characters in this string will not be skipped.

    Raises:
      ExpressionSyntaxError: End of input reached after skipping and a token is
        expected.

    Returns:
      True if the expression is not at end of input.
    """
    while not self.EndOfInput():
      c = self._expr[self._position]
      if not c.isspace() or c in terminators:
        return True
      self._position += 1
    if token:
      raise resource_exceptions.ExpressionSyntaxError(
          '{0} expected [{1}].'.format(token, self.Annotate()))
    return False

  def IsCharacter(self, characters, peek=False, eoi_ok=False):
    """Checks if the next character is in characters and consumes it if it is.

    Args:
      characters: A set of characters to check for. It may be a string, tuple,
        list or set.
      peek: Does not consume a matching character if True.
      eoi_ok: True if end of input is OK. Returns None if at end of input.

    Raises:
      ExpressionSyntaxError: End of input reached and peek and eoi_ok are False.

    Returns:
      The matching character or None if no match.
    """
    if self.EndOfInput():
      if peek or eoi_ok:
        return None
      raise resource_exceptions.ExpressionSyntaxError(
          'More tokens expected [{0}].'.format(self.Annotate()))
    c = self._expr[self._position]
    if c not in characters:
      return None
    if not peek:
      self._position += 1
    return c

  def IsString(self, name, peek=False):
    """Skips leading space and checks if the next token is name.

    One of space, '(', or end of input terminates the next token.

    Args:
      name: The token name to check.
      peek: Does not consume the string on match if True.

    Returns:
      True if the next space or ( separated token is name.
    """
    if not self.SkipSpace():
      return False
    i = self.GetPosition()
    if not self._expr[i:].startswith(name):
      return False
    i += len(name)
    if self.EndOfInput(i) or self._expr[i].isspace() or self._expr[i] == '(':
      if not peek:
        self.SetPosition(i)
      return True
    return False

  def Token(self, terminators='', balance_parens=False, space=True,
            convert=False):
    """Parses a possibly quoted token from the current expression position.

    The quote characters are in _QUOTES. The _ESCAPE character can prefix
    an _ESCAPE or _QUOTE character to treat it as a normal character. If
    _ESCAPE is at end of input, or is followed by any other character, then it
    is treated as a normal character.

    Quotes may be adjacent ("foo"" & ""bar" => "foo & bar") and they may appear
    mid token (foo" & "bar => "foo & bar").

    Args:
      terminators: A set of characters that terminate the token. isspace()
        characters always terminate the token. It may be a string, tuple, list
        or set. Terminator characters are not consumed.
      balance_parens: True if (...) must be balanced.
      space: True if space characters should be skipped after the token. Space
        characters are always skipped before the token.
      convert: Converts unquoted numeric string tokens to numbers if True.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      None if there is no token, the token string if convert is False or the
      token is quoted, otherwise the converted float / int / string value of
      the token.
    """
    quote = None  # The current quote character, None if not in quote.
    quoted = False  # True if the token is constructed from quoted parts.
    token = None  # The token char list, None for no token, [] for empty token.
    paren_count = 0
    i = self.GetPosition()
    while not self.EndOfInput(i):
      c = self._expr[i]
      if c == self._ESCAPE and not self.EndOfInput(i + 1):
        # Only _ESCAPE, the current quote or _QUOTES are escaped.
        c = self._expr[i + 1]
        if token is None:
          token = []
        if (c != self._ESCAPE and c != quote and
            (quote or c not in self._QUOTES)):
          token.append(self._ESCAPE)
        token.append(c)
        i += 1
      elif c == quote:
        # The end of the current quote.
        quote = None
      elif not quote and c in self._QUOTES:
        # The start of a new quote.
        quote = c
        quoted = True
        if token is None:
          token = []
      elif not quote and c.isspace() and token is None:
        pass
      elif not quote and balance_parens and c in '()':
        if c == '(':
          paren_count += 1
        else:
          if c in terminators and not paren_count:
            break
          paren_count -= 1
        # Append c to the token string.
        if token is None:
          token = []
        token.append(c)
      elif not quote and not paren_count and c in terminators:
        # Only unquoted terminators terminate the token.
        break
      elif quote or not c.isspace() or token is not None and balance_parens:
        # Append c to the token string.
        if token is None:
          token = []
        token.append(c)
      elif token is not None:
        # A space after any token characters is a terminator.
        break
      i += 1
    if quote:
      raise resource_exceptions.ExpressionSyntaxError(
          'Unterminated [{0}] quote [{1}].'.format(quote, self.Annotate()))
    self.SetPosition(i)
    if space:
      self.SkipSpace(terminators=terminators)
    if token is not None:
      # Convert the list of token chars to a string.
      token = ''.join(token)
    if convert and token and not quoted:
      # Only unquoted tokens are converted.
      try:
        return int(token)
      except ValueError:
        try:
          return float(token)
        except ValueError:
          pass
    return token

  def Args(self, convert=False, separators=','):
    """Parses a separators-separated, )-terminated arg list.

    The initial '(' has already been consumed by the caller. The arg list may
    be empty. Otherwise the first ',' must be preceded by a non-empty argument,
    and every ',' must be followed by a non-empty argument.

    Args:
      convert: Converts unquoted numeric string args to numbers if True.
      separators: A string of argument separator characters.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      [...]: The arg list.
    """
    required = False  # True if there must be another argument token.
    args = []
    terminators = separators + ')'  # The closing ')' also terminates an arg.
    while True:
      here = self.GetPosition()
      arg = self.Token(terminators, balance_parens=True, convert=convert)
      end = self.IsCharacter(')')
      if end:
        sep = end
      else:
        sep = self.IsCharacter(separators, eoi_ok=True)
        if not sep:
          # This branch "cannot happen". End of input, separators and
          # terminators have already been handled. Retained to guard against
          # future ingenuity.
          here = self.GetPosition()
          raise resource_exceptions.ExpressionSyntaxError(
              'Closing ) expected in argument list [{0}].'.format(
                  self.Annotate(here)))
      if arg is not None:
        # No empty args with space separators.
        if arg or not sep.isspace():
          args.append(arg)
      elif required or not end:
        raise resource_exceptions.ExpressionSyntaxError(
            'Argument expected [{0}].'.format(self.Annotate(here)))
      if end:
        break
      required = not sep.isspace()
    return args

  def _CheckMapShorthand(self):
    """Checks for N '*' chars shorthand for .map(N)."""
    map_level = 0
    while self.IsCharacter('*'):
      map_level += 1
    if not map_level:
      return
    # We have map_level '*'s. Do a simple text substitution on the input
    # expression and let the lexer/parser handle map().
    self._expr = '{}map({}).{}'.format(
        self._expr[:self._position - map_level],
        map_level,
        self._expr[self._position:])
    # Adjust the cursor to the beginning of the '*' chars just consumed.
    self._position -= map_level

  def KeyWithAttribute(self):
    """Parses a resource key from the expression.

    A resource key is a '.' separated list of names with optional [] slice or
    [NUMBER] array indices. Names containing _RESERVED_OPERATOR_CHARS must be
    quoted. For example, "k.e.y".value has two name components, 'k.e.y' and
    'value'.

    A parsed key is encoded as an ordered list of tokens, where each token may
    be:

      KEY VALUE   PARSED VALUE  DESCRIPTION
      ---------   ------------  -----------
      name        string        A dotted name list element.
      [NUMBER]    NUMBER        An array index.
      []          None          An array slice.

    For example, the key 'abc.def[123].ghi[].jkl' parses to this encoded list:
      ['abc', 'def', 123, 'ghi', None, 'jkl']

    Raises:
      ExpressionKeyError: The expression has a key syntax error.

    Returns:
      (key, attribute) The parsed key and attribute. attribute is the alias
        attribute if there was an alias expansion, None otherwise.
    """
    key = []
    attribute = None
    while not self.EndOfInput():
      self._CheckMapShorthand()
      here = self.GetPosition()
      name = self.Token(_RESERVED_OPERATOR_CHARS, space=False)
      if name:
        is_function = self.IsCharacter('(', peek=True, eoi_ok=True)
        if not key and not is_function and name in self._defaults.aliases:
          k, attribute = self._defaults.aliases[name]
          key.extend(k)
        else:
          key.append(name)
      elif not self.IsCharacter('[', peek=True):
        # A single . is a valid key that names the top level resource.
        if (not key and
            self.IsCharacter('.') and
            not self.IsCharacter('.', peek=True, eoi_ok=True) and (
                self.EndOfInput() or self.IsCharacter(
                    _RESERVED_OPERATOR_CHARS, peek=True, eoi_ok=True))):
          break
        raise resource_exceptions.ExpressionSyntaxError(
            'Non-empty key name expected [{0}].'.format(self.Annotate(here)))
      if self.EndOfInput():
        break
      if self.IsCharacter(']'):
        raise resource_exceptions.ExpressionSyntaxError(
            'Unmatched ] in key [{0}].'.format(self.Annotate(here)))
      while self.IsCharacter('[', eoi_ok=True):
        # [] slice or [NUMBER] array index.
        index = self.Token(']', convert=True)
        self.IsCharacter(']')
        key.append(index)
      if not self.IsCharacter('.', eoi_ok=True):
        break
      if self.EndOfInput():
        # Dangling '.' is not allowed.
        raise resource_exceptions.ExpressionSyntaxError(
            'Non-empty key name expected [{0}].'.format(self.Annotate()))
    return key, attribute

  def Key(self):
    """Parses a resource key from the expression and returns the parsed key."""
    key, _ = self.KeyWithAttribute()
    return key

  def _ParseSynthesize(self, args):
    """Parses the synthesize() transform args and returns a new transform.

    The args are a list of tuples. Each tuple is a schema that defines the
    synthesis of one resource list item. Each schema item is an attribute
    that defines the synthesis of one synthesized_resource attribute from
    an original_resource attribute.

    There are three kinds of attributes:

      name:literal
        The value for the name attribute in the synthesized resource is the
        literal value.
      name=key
        The value for the name attribute in the synthesized_resource is the
        value of key in the original_resource.
      key:
        All the attributes of the value of key in the original_resource are
        added to the attributes in the synthesized_resource.

    Args:
      args: The original synthesize transform args.

    Returns:
      A synthesize transform function that uses the schema from the parsed
      args.

    Example:
      This returns a list of two resource items:
        synthesize((name:up, upInfo), (name:down, downInfo))
      If upInfo and downInfo serialize to
        {"foo": 1, "bar": "yes"}
      and
        {"foo": 0, "bar": "no"}
      then the synthesized resource list is
        [{"name": "up", "foo": 1, "bar": "yes"},
        {"name": "down", "foo": 0, "bar": "no"}]
      which could be displayed by a nested table using
        synthesize(...):format="table(name, foo, bar)"
    """
    schemas = []
    for arg in args:
      lex = Lexer(arg)
      if not lex.IsCharacter('('):
        raise resource_exceptions.ExpressionSyntaxError(
            '(...) args expected in synthesizer() transform')
      schema = []
      for attr in lex.Args():
        if ':' in attr:
          name, literal = attr.split(':', 1)
          key = None
        elif '=' in attr:
          name, value = attr.split('=', 1)
          key = Lexer(value).Key()
          literal = None
        else:
          key = Lexer(attr).Key()
          name = None
          literal = None
        schema.append((name, key, literal))
      schemas.append(schema)

    def _Synthesize(r):
      """Synthesize a new resource list from the original resource r.

      Args:
        r: The original resource.

      Returns:
        The synthesized resource list.
      """
      synthesized_resource_list = []
      for schema in schemas:
        synthesized_resource = {}
        for attr in schema:
          name, key, literal = attr
          value = resource_property.Get(r, key, None) if key else literal
          if name:
            synthesized_resource[name] = value
          elif isinstance(value, dict):
            synthesized_resource.update(value)
        synthesized_resource_list.append(synthesized_resource)
      return synthesized_resource_list

    return _Synthesize

  def _ParseTransform(self, func_name, active=0, map_transform=None):
    """Parses a transform function call.

    The initial '(' has already been consumed by the caller.

    Args:
      func_name: The transform function name.
      active: The transform active level or None if always active.
      map_transform: Apply the transform to each resource list item this many
        times.

    Returns:
      A _TransformCall object. The caller appends these to a list that is used
      to apply the transform functions.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    here = self.GetPosition()
    func = self._defaults.symbols.get(func_name)
    if not func:
      raise resource_exceptions.UnknownTransformError(
          'Unknown transform function {0} [{1}].'.format(
              func_name, self.Annotate(here)))
    args = []
    kwargs = {}
    doc = getattr(func, '__doc__', None)
    if doc and resource_projection_spec.PROJECTION_ARG_DOC in doc:
      # The second transform arg is the caller projection.
      args.append(self._defaults)
    if getattr(func, '__defaults__', None):
      # Separate the args from the kwargs.
      for arg in self.Args():
        name, sep, val = arg.partition('=')
        if sep:
          kwargs[name] = val
        else:
          args.append(arg)
    else:
      # No kwargs.
      args += self.Args()
    return _TransformCall(func_name, func, active=active,
                          map_transform=map_transform, args=args, kwargs=kwargs)

  def Transform(self, func_name, active=0):
    """Parses one or more transform calls and returns a _Transform call object.

    The initial '(' has already been consumed by the caller.

    Args:
      func_name: The name of the first transform function.
      active: The transform active level, None for always active.

    Returns:
      The _Transform object containing the ordered list of transform calls.
    """
    here = self.GetPosition()
    calls = _Transform()
    map_transform = 0
    while True:
      transform = self._ParseTransform(func_name, active=active,
                                       map_transform=map_transform)
      if transform.func == resource_transform.TransformAlways:
        active = None  # Always active.
        func_name = None
      elif transform.func == resource_transform.TransformMap:
        map_transform = int(transform.args[0]) if transform.args else 1
        func_name = None
      elif transform.func == resource_transform.TransformIf:
        if len(transform.args) != 1:
          raise resource_exceptions.ExpressionSyntaxError(
              'Conditional filter expression expected [{0}].'.format(
                  self.Annotate(here)))
        calls.SetConditional(transform.args[0])
      elif transform.func == resource_transform.TransformSynthesize:
        transform.func = self._ParseSynthesize(transform.args)
        transform.args = []
        transform.kwargs = {}
        calls.Add(transform)
      else:
        # always() applies to all transforms for key.
        # map() applies to the next transform.
        map_transform = 0
        calls.Add(transform)
      if not self.IsCharacter('.', eoi_ok=True):
        break
      call = self.Key()
      here = self.GetPosition()
      if not self.IsCharacter('('):
        raise resource_exceptions.ExpressionSyntaxError(
            'Transform function expected [{0}].'.format(
                self.Annotate(here)))
      if len(call) != 1:
        raise resource_exceptions.UnknownTransformError(
            'Unknown transform function {0} [{1}].'.format(
                '.'.join(call), self.Annotate(here)))
      func_name = call.pop()
    return calls


def ParseKey(name):
  """Returns a parsed key for the dotted resource name string.

  This is an encapsulation of Lexer.Key(). That docstring has the input/output
  details for this function.

  Args:
    name: A resource name string that may contain dotted components and
      multi-value indices.

  Raises:
    ExpressionSyntaxError: If there are unexpected tokens after the key name.

  Returns:
    A parsed key for he dotted resource name string.
  """
  lex = Lexer(name)
  key = lex.Key()
  if not lex.EndOfInput():
    raise resource_exceptions.ExpressionSyntaxError(
        'Unexpected tokens [{0}] in key.'.format(lex.Annotate()))
  return key


def GetKeyName(key, quote=True, omit_indices=False):
  """Returns the string representation for a parsed key.

  This is the inverse of Lexer.Key(). That docstring has the input/output
  details for this function.

  Args:
    key: A parsed key, which is an ordered list of key names/indices. Each
      element in the list may be one of:
        str - A resource property name. This could be a class attribute name or
          a dict index.
        int - A list index. Selects one member is the list. Negative indices
          count from the end of the list, starting with -1 for the last element
          in the list. An out of bounds index is not an error; it produces the
          value None.
        None - A list slice. Selects all members of a list or dict like object.
          A slice of an empty dict or list is an empty dict or list.
    quote: "..." the key name if it contains non-alphanum characters.
    omit_indices: Omit [...] indices if True.

  Returns:
    The string representation of the parsed key.
  """
  parts = []
  for part in key:
    if part is None:
      if omit_indices:
        continue
      part = '[]'
      if parts:
        parts[-1] += part
        continue
    elif isinstance(part, six.integer_types):
      if omit_indices:
        continue
      part = '[{part}]'.format(part=part)
      if parts:
        parts[-1] += part
        continue
    elif quote and re.search(r'[^-@\w]', part):
      part = part.replace('\\', '\\\\')
      part = part.replace('"', '\\"')
      part = '"{part}"'.format(part=part)
    parts.append(part)
  return '.'.join(parts) if parts else '.'
