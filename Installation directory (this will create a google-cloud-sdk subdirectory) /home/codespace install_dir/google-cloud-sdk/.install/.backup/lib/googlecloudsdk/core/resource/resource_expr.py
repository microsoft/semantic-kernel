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

"""Cloud resource list filter expression evaluator backend."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import re
import unicodedata

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import times

import six


def _ReCompile(pattern, flags=0):
  """Returns a compiled RE pattern.

  Args:
    pattern: The RE pattern string.
    flags: Optional RE flags.

  Raises:
    ExpressionSyntaxError: RE pattern error.

  Returns:
    The compiled RE.
  """
  try:
    return re.compile(pattern, flags)
  except re.error as e:
    raise resource_exceptions.ExpressionSyntaxError(
        'Filter expression RE pattern [{}]: {}'.format(pattern, e))


def _Stringize(value):
  """Returns the unicode string representation for value."""
  if value is None:
    return 'null'
  if not isinstance(value, six.string_types):
    value = repr(value)
  return six.text_type(encoding.Decode(value))


def NormalizeForSearch(value, html=False):
  """Returns lowercase unicode NFKD form with accents stripped.

  Args:
    value: The value to be normalized.
    html: If True the value is HTML text and HTML tags are converted to spaces.

  Returns:
    The normalized unicode representation of value suitable for cloud search
    matching.
  """
  # Stringize and convert to lower case.
  text = _Stringize(value).lower()
  # Strip HTML tags if needed.
  if html:
    text = re.sub('<[^>]*>', '', text)
  # Convert to NFKD normal form with accents stripped.
  return ''.join([c for c in unicodedata.normalize('NFKD', text)
                  if not unicodedata.combining(c)])


def _MatchOneWordInText(backend, key, op, warned_attribute, value, pattern):
  """Returns True if value word matches pattern.

  Args:
    backend: The parser backend object.
    key: The parsed expression key.
    op: The expression operator string.
    warned_attribute: Deprecation warning Boolean attribute name.
    value: The value to be matched by pattern.
    pattern: An (operand, standard_regex, deprecated_regex) tuple.

  Raises:
    ValueError: To catch codebase reliance on deprecated usage.

  Returns:
    True if pattern matches value.

  Examples:
    See surface/topic/filters.py for a table of example matches.
  """
  operand, standard_regex, deprecated_regex = pattern
  if isinstance(value, float):
    try:
      if value == float(operand):
        return True
    except ValueError:
      pass
    if value == 0 and operand.lower() == 'false':
      return True
    if value == 1 and operand.lower() == 'true':
      return True
    # Stringize float with trailing .0's stripped.
    text = re.sub(r'\.0*$', '', _Stringize(value))
  elif value == operand:
    return True
  elif value is None:
    if operand in ('', None):
      return True
    if operand == '*' and op == ':':
      return False
    text = 'null'
  else:
    text = NormalizeForSearch(value, html=True)

  # Phase 1: return deprecated_matched and warn if different from matched.
  # Phase 2: return matched and warn if different from deprecated_matched.
  # Phase 3: drop deprecated logic.

  matched = bool(standard_regex.search(text))
  if not deprecated_regex:
    return matched

  deprecated_matched = bool(deprecated_regex.search(text))

  # For compute's region and zone keys we also want to exact match segment(-1).
  # We do this because exact match filter fields for zone and region are used to
  # determine which zonal/regional endpoints to scope the request to.

  if len(key) == 1 and key[0] in ['zone', 'region']:
    deprecated_matched |= bool(deprecated_regex.search(text.split('/')[-1]))

  if (matched != deprecated_matched and warned_attribute and
      not getattr(backend, warned_attribute, False)):
    setattr(backend, warned_attribute, True)
    old_match = 'matches' if deprecated_matched else 'does not match'
    new_match = 'will match' if matched else 'will not match'
    log.warning('--filter : operator evaluation is changing for '
                'consistency across Google APIs.  {key}{op}{operand} currently '
                '{old_match} but {new_match} in the near future.  Run '
                '`gcloud topic filters` for details.'.format(
                    key=resource_lex.GetKeyName(key),
                    op=op,
                    operand=operand,
                    old_match=old_match,
                    new_match=new_match))
  return deprecated_matched


def _WordMatch(backend, key, op, warned_attribute, value, pattern):
  """Applies _MatchOneWordInText to determine if value matches pattern.

  Both value and operand can be lists.

  Args:
    backend: The parser backend object.
    key: The parsed expression key.
    op: The expression operator string.
    warned_attribute: Deprecation warning Boolean attribute name.
    value: The key value or list of values.
    pattern: Pattern value or list of values.

  Returns:
    True if the value (or any element in value if it is a list) matches pattern
    (or any element in operand if it is a list).
  """
  if isinstance(value, dict):
    # Don't check deprecated diffs on dicts. It adds instability to the UX and
    # test assertions. Checking dict keys may be deprecated in the unified
    # filter spec anyway, so it's not terrible to disable the checks for dicts.
    warned_attribute = None
    values = []
    if value:
      values.extend(six.iterkeys(value))
      values.extend(six.itervalues(value))
  elif isinstance(value, (list, tuple)):
    values = value
  else:
    values = [value]
  if isinstance(pattern, (list, tuple)):
    patterns = pattern
  else:
    patterns = {pattern}
  for v in values:
    for p in patterns:
      if _MatchOneWordInText(backend, key, op, warned_attribute, v, p):
        return True
  return False


class Backend(object):
  """Cloud resource list filter expression evaluator backend.

  This is a backend for resource_filter.Parser(). The generated "evaluator" is a
  parsed resource expression tree with branching factor 2 for binary operator
  nodes, 1 for NOT and function nodes, and 0 for TRUE nodes. Evaluation for a
  resource object starts with expression_tree_root.Evaluate(obj) which
  recursively evaluates child nodes. The logic operators use left-right shortcut
  pruning, so an evaluation may not visit every node in the expression tree.
  """

  # The remaining methods return an initialized class object.

  def ExprTRUE(self):
    return _ExprTRUE(self)

  def ExprAND(self, left, right):
    return _ExprAND(self, left, right)

  def ExprOR(self, left, right):
    return _ExprOR(self, left, right)

  def ExprNOT(self, expr):
    return _ExprNOT(self, expr)

  def ExprGlobal(self, call):
    return _ExprGlobal(self, call)

  def ExprOperand(self, value):
    return _ExprOperand(self, value)

  def ExprLT(self, key, operand, transform=None):
    return _ExprLT(self, key, operand, transform)

  def ExprLE(self, key, operand, transform=None):
    return _ExprLE(self, key, operand, transform)

  def ExprHAS(self, key, operand, transform=None):
    """Case insensitive membership node.

    This is the pre-compile Expr for the ':' operator. It compiles into an
    _ExprHAS node for prefix*suffix matching.

    The * operator splits the operand into prefix and suffix matching strings.

    Args:
      key: Resource object key (list of str, int and/or None values).
      operand: The term ExprOperand operand.
      transform: Optional key value transform calls.

    Returns:
      _ExprHAS.
    """
    return _ExprHAS(self, key, operand, transform)

  def ExprEQ(self, key, operand, transform=None):
    """Case sensitive EQ node.

    Args:
      key: Resource object key (list of str, int and/or None values).
      operand: The term ExprOperand operand.
      transform: Optional key value transform calls.

    Returns:
      _ExprEQ.
    """
    return _ExprEQ(self, key, operand, transform)

  def ExprNE(self, key, operand, transform=None):
    return _ExprNE(self, key, operand, transform)

  def ExprGE(self, key, operand, transform=None):
    return _ExprGE(self, key, operand, transform)

  def ExprGT(self, key, operand, transform=None):
    return _ExprGT(self, key, operand, transform)

  def ExprRE(self, key, operand, transform=None):
    return _ExprRE(self, key, operand, transform)

  def ExprNotRE(self, key, operand, transform=None):
    return _ExprNotRE(self, key, operand, transform)

  def IsRewriter(self):
    return False


# _Expr* class instantiations are done by the Backend.Expr* methods.


@six.add_metaclass(abc.ABCMeta)
class _Expr(object):
  """Expression base class."""

  def __init__(self, backend):
    self.backend = backend

  @abc.abstractmethod
  def Evaluate(self, obj):
    """Returns the value of the subexpression applied to obj.

    Args:
      obj: The current resource object.

    Returns:
      True if the subexpression matches obj, False if it doesn't match, or
      None if the subexpression is not supported.
    """
    pass

  @property
  def contains_key(self):
    return False


class _ExprTRUE(_Expr):
  """TRUE node.

  Always evaluates True.
  """

  def Evaluate(self, unused_obj):
    return True


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


class _ExprAND(_ExprLogical):
  """AND node.

  AND with left-to-right shortcut pruning.
  """

  def Evaluate(self, obj):
    if not self._left.Evaluate(obj):
      return False
    if not self._right.Evaluate(obj):
      return False
    return True


class _ExprOR(_ExprLogical):
  """OR node.

  OR with left-to-right shortcut pruning.
  """

  def Evaluate(self, obj):
    if self._left.Evaluate(obj):
      return True
    if self._right.Evaluate(obj):
      return True
    return False


class _ExprNOT(_Expr):
  """NOT node."""

  def __init__(self, backend, expr):
    super(_ExprNOT, self).__init__(backend)
    self._expr = expr

  def Evaluate(self, obj):
    return not self._expr.Evaluate(obj)


class _ExprGlobal(_Expr):
  """Global restriction function call node.

  Attributes:
    _call: The function call object.
  """

  def __init__(self, backend, call):
    super(_ExprGlobal, self).__init__(backend)
    self._call = call

  def Evaluate(self, obj):
    return self._call.Evaluate(obj)


class _ExprOperand(object):
  """Operand node.

  Converts an expession value token string to internal string and/or numeric
  values. If an operand has a numeric value then the actual key values are
  converted to numbers at Evaluate() time if possible for Apply(); if the
  conversion fails then the key and operand string values are passed to Apply().

  Attributes:
    list_value: A list of operands.
    numeric_value: The int or float number, or None if the token string does not
      convert to a number.
    string_value: The token string.
  """

  _NUMERIC_CONSTANTS = {
      'false': 0,
      'true': 1,
  }

  def __init__(self, backend, value, normalize=None):
    self.backend = backend
    self.list_value = None
    self.numeric_constant = False
    self.numeric_value = None
    self.string_value = None
    self.Initialize(value, normalize=normalize)

  def Initialize(self, value, normalize=None):
    """Initializes an operand string_value and numeric_value from value.

    Args:
      value: The operand expression string value.
      normalize: Optional normalization function.
    """
    if isinstance(value, list):
      self.list_value = []
      for val in value:
        self.list_value.append(
            _ExprOperand(self.backend, val, normalize=normalize))
    elif value and normalize:
      self.string_value = normalize(value)
    elif isinstance(value, six.string_types):
      self.string_value = value
      try:
        self.numeric_value = self._NUMERIC_CONSTANTS[value.lower()]
        self.numeric_constant = True
      except KeyError:
        try:
          self.numeric_value = int(value)
        except ValueError:
          try:
            self.numeric_value = float(value)
          except ValueError:
            pass
    else:
      self.string_value = _Stringize(value)
      self.numeric_value = value


@six.add_metaclass(abc.ABCMeta)
class _ExprOperator(_Expr):
  """Base term (<key operator operand>) node.

  ExprOperator subclasses must define the function Apply(self, value, operand)
  that returns the result of <value> <op> <operand>.

  Attributes:
    _key: Resource object key (list of str, int and/or None values).
    _normalize: The resource value normalization function.
    _operand: The term ExprOperand operand.
    _transform: Optional key value transform calls.
    key : Property decorator for the resource object key.
  """

  _TIME_TYPES = (
      times.datetime.date,
      times.datetime.time,
      times.datetime.timedelta,
      times.datetime.tzinfo,
  )

  def __init__(self, backend, key, operand, transform):
    super(_ExprOperator, self).__init__(backend)
    self._key = key
    self._operand = operand
    self._transform = transform
    if transform:
      self._normalize = lambda x: x
    else:
      self._normalize = self.InitializeNormalization

  def InitializeNormalization(self, value):
    """Checks the first non-empty resource value to see if it can be normalized.

    This method is called at most once on the first non-empty resource value.
    After that a new normalization method is set for the remainder of the
    resource values.

    Resource values are most likely well defined protobuf string encodings. The
    RE patterns match against those.

    Args:
      value: A resource value to normalize.

    Returns:
      The normalized value.
    """
    self._normalize = lambda x: x

    # Check for datetime. Dates may have trailing timzone indicators. We don't
    # match them but ParseDateTime will handle them.
    if re.match(r'\d\d\d\d-\d\d-\d\d[ T]\d\d:\d\d:\d\d', value):
      try:
        value = times.ParseDateTime(value)
        # Make sure the value and operand times are both tz aware or tz naive.
        # Otherwise datetime comparisons will fail.
        tzinfo = times.LOCAL if value.tzinfo else None
        self._operand.Initialize(
            self._operand.list_value or self._operand.string_value,
            normalize=lambda x: times.ParseDateTime(x, tzinfo=tzinfo))
        self._normalize = times.ParseDateTime
      except ValueError:
        pass

    # More type checks go here.

    return value

  @property
  def contains_key(self):
    return True

  @property
  def key(self):
    return self._key

  def Evaluate(self, obj):
    """Evaluate a term node.

    Args:
      obj: The resource object to evaluate.
    Returns:
      The value of the operator applied to the key value and operand.
    """
    value = resource_property.Get(obj, self._key)
    if self._transform:
      value = self._transform.Evaluate(value)
    # Arbitrary choice: value == []  =>  values = [[]]
    if value and isinstance(value, (list, tuple)):
      resource_values = value
    else:
      resource_values = [value]
    values = []
    for value in resource_values:
      if value:
        try:
          value = self._normalize(value)
        except (TypeError, ValueError):
          pass
      values.append(value)

    if self._operand.list_value:
      operands = self._operand.list_value
    else:
      operands = [self._operand]

    # Check for any match in all value X operand combinations.
    for value in values:
      for operand in operands:
        # Each try/except attempts a different combination of value/operand
        # numeric and string conversions.

        if operand.numeric_value is not None:
          try:
            if self.Apply(float(value), operand.numeric_value):
              return True
            if not operand.numeric_constant:
              continue
          except (TypeError, ValueError):
            pass

        if not value and isinstance(operand.string_value, self._TIME_TYPES):
          continue

        try:
          if self.Apply(value, operand.string_value):
            return True
        except (AttributeError, ValueError):
          pass
        except TypeError:
          if (
              value is not None
              and not isinstance(value, (six.string_types, dict, list))
              and self.Apply(_Stringize(value), operand.string_value)
          ):
            return True
          if (
              six.PY3
              and value is None
              and self.Apply('', operand.string_value)
          ):
            return True

    return False

  @abc.abstractmethod
  def Apply(self, value, operand):
    """Returns the value of applying a <value> <operator> <operand> term.

    Args:
      value: The term key value.
      operand: The term operand value.

    Returns:
      The Boolean value of applying a <value> <operator> <operand> term.
    """
    pass


class _ExprLT(_ExprOperator):
  """LT node."""

  def Apply(self, value, operand):
    return value < operand


class _ExprLE(_ExprOperator):
  """LE node."""

  def Apply(self, value, operand):
    return value <= operand


class _ExprWordMatchBase(_ExprOperator):
  """{ HAS EQ NE } word match base class."""

  def __init__(self, backend, key, operand, transform, op=None,
               warned_attribute=None):
    super(_ExprWordMatchBase, self).__init__(backend, key, operand, transform)
    self._op = op
    # Should be private but it will go away soon and this avoids pylints.
    self._warned_attribute = warned_attribute
    self._patterns = []
    if self._operand.list_value is not None:
      for operand in self._operand.list_value:
        if operand.string_value is not None:
          operand.string_value = operand.string_value
          self._AddPattern(operand.string_value)
    elif self._operand.string_value is not None:
      operand.string_value = operand.string_value
      self._AddPattern(self._operand.string_value)

  @abc.abstractmethod
  def _AddPattern(self, pattern):
    """Adds a word match pattern to self._patterns."""
    pass

  def Apply(self, value, operand):
    """Checks if value word matches operand ignoring case differences.

    Args:
      value: The number, string, dict or list object value.
      operand: Non-pattern operand for equality check. The ':' HAS operator
        operand can be a prefix*suffix pattern or a literal value. Literal
        values are first checked by the _Equals method to handle numeric
        constant matching. String literals and patterns are then matched by the
        _Has method.

    Returns:
      True if value HAS matches operand (or any value in operand if it is a
      list) ignoring case differences.
    """
    return _WordMatch(self.backend, self._key, self._op, self._warned_attribute,
                      value, self._patterns)


class _ExprHAS(_ExprWordMatchBase):
  """HAS word match node."""

  def __init__(self, backend, key, operand, transform):
    super(_ExprHAS, self).__init__(backend, key, operand, transform, op=':',
                                   warned_attribute='_deprecated_has_warned')

  def _AddPattern(self, pattern):
    """Adds a HAS match pattern to self._patterns.

    A pattern is a word that optionally contains one trailing * that matches
    0 or more characters.

    This method re-implements both the original and the OnePlatform : using REs.
    It was tested against the original tests with no failures.  This cleaned up
    the code (really!) and made it easier to reason about the two
    implementations.

    Args:
      pattern: A string containing at most one trailing *.

    Raises:
      resource_exceptions.ExpressionSyntaxError if the pattern contains more
        than one leading or trailing * glob character.
    """
    if pattern == '*':
      standard_pattern = '.'
      deprecated_pattern = None
    else:
      head = '\\b'
      glob = ''
      tail = '\\b'
      normalized_pattern = NormalizeForSearch(pattern)
      parts = normalized_pattern.split('*')
      if len(parts) > 2:
        raise resource_exceptions.ExpressionSyntaxError(
            'At most one * expected in : patterns [{}].'.format(pattern))

      # Construct the standard RE pattern.
      if normalized_pattern.endswith('*'):
        normalized_pattern = normalized_pattern[:-1]
        tail = ''
      word = re.escape(normalized_pattern)
      standard_pattern = head + word + tail

      # Construct the deprecated RE pattern.
      if len(parts) == 1:
        parts.append('')
      elif pattern.startswith('*'):
        head = ''
      elif pattern.endswith('*'):
        tail = ''
      else:
        glob = '.*'
      left = re.escape(parts[0]) if parts[0] else ''
      right = re.escape(parts[1]) if parts[1] else ''
      if head and tail:
        if glob:
          deprecated_pattern = '^' + left + glob + right + '$'
        else:
          deprecated_pattern = left + glob + right
      elif head:
        deprecated_pattern = '^' +  left + glob + right
      elif tail:
        deprecated_pattern = left + glob + right + '$'
      else:
        deprecated_pattern = None

    reflags = re.IGNORECASE|re.MULTILINE|re.UNICODE
    standard_regex = _ReCompile(standard_pattern, reflags)
    if deprecated_pattern:
      deprecated_regex = _ReCompile(deprecated_pattern, reflags)
    else:
      deprecated_regex = None
    self._patterns.append((pattern, standard_regex, deprecated_regex))


class _ExprEQ(_ExprWordMatchBase):
  """EQ word match node."""

  def __init__(self, backend, key, operand, transform, op=None):
    super(_ExprEQ, self).__init__(backend, key, operand, transform,
                                  op=op or '=',
                                  warned_attribute='_deprecated_eq_warned')

  def _AddPattern(self, pattern):
    """Adds an EQ match pattern to self._patterns.

    A pattern is a word.

    This method re-implements both the original and the OnePlatform = using REs.
    It was tested against the original tests with no failures.  This cleaned up
    the code (really!) and made it easier to reason about the two
    implementations.

    Args:
      pattern: A string containing a word to match.
    """
    normalized_pattern = NormalizeForSearch(pattern)
    word = re.escape(normalized_pattern)

    # Construct the standard RE pattern.
    standard_pattern = '\\b' + word + '\\b'

    # Construct the deprecated RE pattern.
    deprecated_pattern = '^' + word + '$'

    reflags = re.IGNORECASE|re.MULTILINE|re.UNICODE
    standard_regex = _ReCompile(standard_pattern, reflags)
    deprecated_regex = _ReCompile(deprecated_pattern, reflags)
    self._patterns.append((pattern, standard_regex, deprecated_regex))


class _ExprNE(_ExprEQ):
  """NE node."""

  def __init__(self, backend, key, operand, transform):
    super(_ExprNE, self).__init__(backend, key, operand, transform, op='!=')

  def Apply(self, value, operand):
    return not super(_ExprNE, self).Apply(value, operand)


class _ExprGE(_ExprOperator):
  """GE node."""

  def Apply(self, value, operand):
    return value >= operand


class _ExprGT(_ExprOperator):
  """GT node."""

  def Apply(self, value, operand):
    return value > operand


class _ExprRE(_ExprOperator):
  """Unanchored RE match node."""

  def __init__(self, backend, key, operand, transform):
    super(_ExprRE, self).__init__(backend, key, operand, transform)
    self.pattern = _ReCompile(self._operand.string_value)

  def Apply(self, value, unused_operand):
    if not isinstance(value, six.string_types):
      # This exception is caught by Evaluate().
      raise TypeError('RE match subject value must be a string.')
    return self.pattern.search(value) is not None


class _ExprNotRE(_ExprOperator):
  """Unanchored RE not match node."""

  def __init__(self, backend, key, operand, transform):
    super(_ExprNotRE, self).__init__(backend, key, operand, transform)
    self.pattern = _ReCompile(self._operand.string_value)

  def Apply(self, value, unused_operand):
    if not isinstance(value, six.string_types):
      # This exception is caught by Evaluate().
      raise TypeError('RE match subject value must be a string.')
    return self.pattern.search(value) is None
