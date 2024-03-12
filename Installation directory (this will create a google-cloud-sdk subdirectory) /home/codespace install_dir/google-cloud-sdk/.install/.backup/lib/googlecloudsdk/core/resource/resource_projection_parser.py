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

"""A class for parsing a resource projection expression."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import re

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_transform

import six


class Parser(object):
  """Resource projection expression parser.

  A projection is an expression string that contains a list of resource keys
  with optional attributes. This class parses a projection expression into
  resource key attributes and a tree data structure that is used by a projector.

  A projector is a method that takes a JSON-serializable object and a
  projection as input and produces a new JSON-serializable object containing
  only the values corresponding to the keys in the projection. Optional
  projection key attributes may transform the values in the resulting
  JSON-serializable object.

  In the Cloud SDK projection attributes are used for output formatting.

  A default or empty projection expression still produces a projector that
  converts a resource to a JSON-serializable object.

  Attributes:
    __key_attributes_only: Parse projection key list for attributes only.
    _projection: The resource_projection_spec.ProjectionSpec to parse into.
    _root: The projection _Tree tree root node.
    _snake_headings: Dict used to disambiguate key attribute labels.
    _snake_re: Compiled re for converting key names to angry snake case.
  """

  _BOOLEAN_ATTRIBUTES = ['optional', 'reverse']
  _OPTIONAL_BOOLEAN_ATTRIBUTES = ['wrap']

  def __init__(self, defaults=None, symbols=None, aliases=None, compiler=None):
    """Constructor.

    Args:
      defaults: resource_projection_spec.ProjectionSpec defaults.
      symbols: Transform function symbol table dict indexed by function name.
      aliases: Resource key alias dictionary.
      compiler: The projection compiler method for nested projections.
    """
    self.__key_attributes_only = False
    self._projection = resource_projection_spec.ProjectionSpec(
        defaults=defaults, symbols=symbols, aliases=aliases, compiler=compiler)
    self._snake_headings = {}
    self._snake_re = None

  class _Tree(object):
    """Defines a Projection tree node.

    Attributes:
      tree: Projection _Tree node indexed by key path.
      attribute: Key _Attribute.
    """

    def __init__(self, attribute):
      self.tree = {}
      self.attribute = attribute

  class _Attribute(object):
    """Defines a projection key attribute.

    Attribute semantics, except transform, are caller defined.  e.g., the table
    formatter uses the label attribute for the column heading for the key.

    Attributes:
      align: The column alignment name: left, center, or right.
      flag: The projection algorithm flag, one of DEFAULT, INNER, PROJECT.
      hidden: Attribute is projected but not displayed.
      label: A string associated with each projection key.
      optional: Column data is optional if True.
      order: The column sort order, None if not ordered. Lower values have
        higher sort precedence.
      reverse: Reverse column sort if True.
      skip_reorder: Don't reorder this attribute in the next _Reorder().
      subformat: Sub-format string.
      transform: obj = func(obj,...) function applied during projection.
      width: Fixed column width.
      wrap: Column can be wrapped if True.
    """

    def __init__(self, flag):
      self.align = resource_projection_spec.ALIGN_DEFAULT
      self.flag = flag
      self.hidden = False
      self.label = None
      self.optional = None
      self.order = None
      self.reverse = None
      self.skip_reorder = False
      self.subformat = None
      self.transform = None
      self.width = None
      self.wrap = None

    def __str__(self):
      option = []
      if self.hidden:
        option.append('hidden')
      if self.optional:
        option.append('optional')
      if self.reverse:
        option.append('reverse')
      if self.subformat:
        option.append('subformat')
      if option:
        options = ', [{0}]'.format('|'.join(option))
      else:
        options = ''
      return ('({flag}, {order}, {label}, {align}, {active}, {wrap},'
              ' {transform}{options})'.format(
                  flag=self.flag,
                  order=('UNORDERED'
                         if self.order is None else six.text_type(self.order)),
                  label=(self.label if self.label is None else "'" +
                         self.label + "'"),
                  align=self.align,
                  active=self.transform.active if self.transform else None,
                  wrap=self.wrap,
                  transform=self.transform,
                  options=options))

  def _AngrySnakeCase(self, key):
    """Returns an ANGRY_SNAKE_CASE string representation of a parsed key.

    For key input [A, B, C] the headings [C, C_B, C_B_A] are generated. The
    first heading not in self._snake_headings is added to self._snake_headings
    and returned.

    Args:
        key: A parsed resource key and/or list of strings.

    Returns:
      The ANGRY_SNAKE_CASE string representation of key, adding components
        from right to left to disambiguate from previous ANGRY_SNAKE_CASE
        strings.
    """
    if self._snake_re is None:
      self._snake_re = re.compile('((?<=[a-z0-9])[A-Z]+|(?!^)[A-Z](?=[a-z]))')
    label = ''
    for index in reversed(key):
      if isinstance(index, six.string_types):
        key_snake = self._snake_re.sub(r'_\1', index).upper()
        if label:
          label = key_snake + '_' + label
        else:
          label = key_snake
        if label not in self._snake_headings:
          self._snake_headings[label] = 1
          break
    return label

  def _AddKey(self, key, attribute_add):
    """Propagates default attribute values and adds key to the projection.

    Args:
      key: The parsed key to add.
      attribute_add: Parsed _Attribute to add.
    """
    projection = self._root

    # Add or update the inner nodes.
    for name in key[:-1]:
      tree = projection.tree
      if name in tree:
        attribute = tree[name].attribute
        if attribute.flag != self._projection.PROJECT:
          attribute.flag = self._projection.INNER
      else:
        tree[name] = self._Tree(self._Attribute(self._projection.INNER))
      projection = tree[name]

    # Add or update the terminal node.
    tree = projection.tree
    name = key[-1] if key else ''
    name_in_tree = name in tree
    # key == [] => . or a function on the entire object.
    if name_in_tree:
      # Already added.
      attribute = tree[name].attribute
      if (not self.__key_attributes_only and
          any([col for col in self._projection.Columns() if col.key == key])):
        # A duplicate column. A projection can only have one attribute object
        # per key. The first <key, attribute> pair added to the current set of
        # columns remains in the projection. Projection columns may have
        # duplicate keys (e.g., table columns with the same key but different
        # transforms). The attribute copy, with attribute_add merged in, is
        # added to the projection columns but not the projection tree.
        attribute = copy.copy(attribute)
      if not self.__key_attributes_only or not attribute.order:
        # Only an attributes_only attribute with explicit :sort=N can be hidden.
        attribute.hidden = False
    elif isinstance(name, six.integer_types) and None in tree:
      # New projection for explicit name using slice defaults.
      tree[name] = copy.deepcopy(tree[None])
      attribute = tree[name].attribute
    else:
      # New projection.
      attribute = attribute_add
      if self.__key_attributes_only and attribute.order:
        attribute.hidden = True
      if key or attribute.transform:
        tree[name] = self._Tree(attribute)

    # Propagate non-default values from attribute_add to attribute.
    if attribute_add.order is not None:
      attribute.order = attribute_add.order
      if self.__key_attributes_only:
        self.__key_order_offset += 1
        attribute.skip_reorder = True
    if attribute_add.label is not None:
      attribute.label = attribute_add.label
    elif attribute.label is None:
      attribute.label = self._AngrySnakeCase(key)
    if attribute_add.align != resource_projection_spec.ALIGN_DEFAULT:
      attribute.align = attribute_add.align
    if attribute_add.optional is not None:
      attribute.optional = attribute_add.optional
    elif attribute.optional is None:
      attribute.optional = False
    if attribute_add.reverse is not None:
      attribute.reverse = attribute_add.reverse
    elif attribute.reverse is None:
      attribute.reverse = False
    if attribute_add.transform:
      attribute.transform = attribute_add.transform
    if attribute_add.subformat:
      attribute.subformat = attribute_add.subformat
    if attribute_add.width is not None:
      attribute.width = attribute_add.width
    elif attribute.width is None:
      attribute.width = False
    if attribute_add.wrap is not None:
      attribute.wrap = attribute_add.wrap
    elif attribute.wrap is None:
      attribute.wrap = False
    self._projection.AddAlias(attribute.label, key, attribute)

    if not self.__key_attributes_only or attribute.hidden:
      # This key is in the projection.
      attribute.flag = self._projection.PROJECT
      self._projection.AddKey(key, attribute)
    elif not name_in_tree:
      # This is a new attributes only key.
      attribute.flag = self._projection.DEFAULT

  def _Reorder(self):
    """Recursively adds self.__key_order_offset to non-zero attribute order.

    This slides established attribute.order out of the way so new
    attribute.order in projection composition take precedence.
    """

    def _AddOffsetToOrder(tree):
      """Adds self.__key_order_offset to unmarked attribute.order.

      A DFS search that visits each attribute once. The search clears
      skip_reorder attributes marked skip_reorder, otherwise it adds
      self.__key_order_offset to attribute.order.

      Args:
        tree: The attribute subtree to reorder.
      """
      for node in tree.values():
        if node.attribute.order:
          if node.attribute.skip_reorder:
            node.attribute.skip_reorder = False
          else:
            node.attribute.order += self.__key_order_offset
        _AddOffsetToOrder(node.tree)

    if self.__key_order_offset:
      _AddOffsetToOrder(self._root.tree)
      self.__key_order_offset = 0

  def _ParseKeyAttributes(self, key, attribute):
    """Parses one or more key attributes and adds them to attribute.

    The initial ':' has been consumed by the caller.

    Args:
      key: The parsed key name of the attributes.
      attribute: Add the parsed transform to this resource_projector._Attribute.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    while True:
      name = self._lex.Token('=:,)', space=False)
      here = self._lex.GetPosition()
      if self._lex.IsCharacter('=', eoi_ok=True):
        boolean_value = False
        value = self._lex.Token(':,)', space=False, convert=True)
      else:
        boolean_value = True
        if name.startswith('no-'):
          name = name[3:]
          value = False
        else:
          value = True
      if name in self._BOOLEAN_ATTRIBUTES:
        if not boolean_value:
          # A Boolean attribute with a non-Boolean value.
          raise resource_exceptions.ExpressionSyntaxError(
              'value not expected [{0}].'.format(self._lex.Annotate(here)))
      elif boolean_value and name not in self._OPTIONAL_BOOLEAN_ATTRIBUTES:
        # A non-Boolean attribute without a value or a no- prefix.
        raise resource_exceptions.ExpressionSyntaxError(
            'value expected [{0}].'.format(self._lex.Annotate(here)))
      if name == 'alias':
        if not value:
          raise resource_exceptions.ExpressionSyntaxError(
              'Cannot unset alias [{0}].'.format(self._lex.Annotate(here)))
        self._projection.AddAlias(value, key, attribute)
      elif name == 'align':
        if value not in resource_projection_spec.ALIGNMENTS:
          raise resource_exceptions.ExpressionSyntaxError(
              'Unknown alignment [{0}].'.format(self._lex.Annotate(here)))
        attribute.align = value
      elif name == 'format':
        attribute.subformat = value or ''
      elif name == 'label':
        attribute.label = value or ''
      elif name == 'optional':
        attribute.optional = value
      elif name == 'reverse':
        attribute.reverse = value
      elif name == 'sort':
        attribute.order = value
      elif name == 'width':
        attribute.width = value
      elif name == 'wrap':
        attribute.wrap = value
      else:
        raise resource_exceptions.ExpressionSyntaxError(
            'Unknown key attribute [{0}].'.format(self._lex.Annotate(here)))
      if not self._lex.IsCharacter(':'):
        break

  def _ParseKey(self):
    """Parses a key and optional attributes from the expression.

    The parsed key is appended to the ordered list of keys via _AddKey().
    Transform functions and key attributes are also handled here.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    key, attribute = self._lex.KeyWithAttribute()
    if self._lex.IsCharacter('(', eoi_ok=True):
      add_transform = self._lex.Transform(key.pop(), self._projection.active)
    else:
      add_transform = None
    if (not self.__key_attributes_only and
        attribute) or (self.__key_attributes_only and attribute and not key):
      # When a key is repeated in the format expression, we want to duplicate
      # the attribute and add transfrom to the key, as the previous behaviour
      # was. However _AddKey is also processed for attribute only keys; in this
      # case, we want to reference the same attribute if the attribute is
      # referenced by its label.
      attribute = copy.copy(attribute)
    else:
      attribute = self._Attribute(self._projection.PROJECT)
    if not attribute.transform:
      attribute.transform = add_transform
    elif add_transform:
      # Compose the alias attribute.transform with add_transforms.
      attribute.transform._transforms.extend(add_transform._transforms)  # pylint: disable=protected-access
    self._lex.SkipSpace()
    if self._lex.IsCharacter(':'):
      self._ParseKeyAttributes(key, attribute)
    if attribute.transform and attribute.transform.conditional:
      # Parse and evaluate if() transform conditional expression,
      conditionals = self._projection.symbols.get(
          resource_transform.GetTypeDataName('conditionals'))

      def EvalGlobalRestriction(unused_obj, restriction, unused_pattern):
        return getattr(conditionals, restriction, None)

      defaults = resource_projection_spec.ProjectionSpec(
          symbols={resource_projection_spec.GLOBAL_RESTRICTION_NAME:
                   EvalGlobalRestriction})
      if not resource_filter.Compile(
          attribute.transform.conditional,
          defaults=defaults).Evaluate(conditionals):
        return
    if attribute.label is None and not key and attribute.transform:
      attribute.label = self._AngrySnakeCase(
          [attribute.transform.name] +
          attribute.transform._transforms[0].args)  # pylint: disable=protected-access
    self._AddKey(key, attribute)

  def _ParseKeys(self):
    """Parses a comma separated list of keys.

    The initial '(' has already been consumed by the caller.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    if self._lex.IsCharacter(')'):
      # An empty projection is OK.
      return
    while True:
      self._ParseKey()
      self._lex.SkipSpace()
      if self._lex.IsCharacter(')'):
        break
      if not self._lex.IsCharacter(','):
        raise resource_exceptions.ExpressionSyntaxError(
            'Expected ) in projection expression [{0}].'.format(
                self._lex.Annotate()))

  def _ParseAttributes(self):
    """Parses a comma separated [no-]name[=value] projection attribute list.

    The initial '[' has already been consumed by the caller.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    while True:
      name = self._lex.Token('=,])', space=False)
      if name:
        if self._lex.IsCharacter('='):
          value = self._lex.Token(',])', space=False, convert=True)
        else:
          value = 1
        if isinstance(value, six.string_types):
          value = value.replace('\\n', '\n').replace('\\t', '\t')
        self._projection.AddAttribute(name, value)
        if name.startswith('no-'):
          self._projection.DelAttribute(name[3:])
        else:
          self._projection.DelAttribute('no-' + name)
      if self._lex.IsCharacter(']'):
        break
      if not self._lex.IsCharacter(','):
        raise resource_exceptions.ExpressionSyntaxError(
            'Expected ] in attribute list [{0}].'.format(self._lex.Annotate()))

  def Parse(self, expression=None):
    """Parse a projection expression.

    An empty projection is OK.

    Args:
      expression: The resource projection expression string.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      A ProjectionSpec for the expression.
    """
    self._root = self._projection.GetRoot()
    if not self._root:
      self._root = self._Tree(self._Attribute(self._projection.DEFAULT))
      self._projection.SetRoot(self._root)
    self._projection.SetEmpty(
        self._Tree(self._Attribute(self._projection.PROJECT)))
    if expression:
      self._lex = resource_lex.Lexer(expression, self._projection)
      defaults = False
      self.__key_attributes_only = False
      while self._lex.SkipSpace():
        if self._lex.IsCharacter('('):
          if not self.__key_attributes_only:
            defaults = False
            self._projection.Defaults()
          self._ParseKeys()
          if self.__key_attributes_only:
            self.__key_attributes_only = False
            self._Reorder()
        elif self._lex.IsCharacter('['):
          self._ParseAttributes()
        elif self._lex.IsCharacter(':'):
          self.__key_attributes_only = True
          self.__key_order_offset = 0
        else:
          here = self._lex.GetPosition()
          name = self._lex.Token(':([')
          if not name.isalpha():
            raise resource_exceptions.ExpressionSyntaxError(
                'Name expected [{0}].'.format(self._lex.Annotate(here)))
          self._projection.SetName(name)
          defaults = True
      self._lex = None
      if defaults:
        self._projection.Defaults()
    return self._projection


def Parse(expression='', defaults=None, symbols=None, aliases=None,
          compiler=None):
  """Parses a resource projector expression.

  Args:
    expression: The resource projection expression string.
    defaults: resource_projection_spec.ProjectionSpec defaults.
    symbols: Transform function symbol table dict indexed by function name.
    aliases: Resource key alias dictionary.
    compiler: The projection compiler method for nested projections.

  Returns:
    A ProjectionSpec for the expression.
  """
  return Parser(defaults=defaults, symbols=symbols, aliases=aliases,
                compiler=compiler).Parse(expression)
