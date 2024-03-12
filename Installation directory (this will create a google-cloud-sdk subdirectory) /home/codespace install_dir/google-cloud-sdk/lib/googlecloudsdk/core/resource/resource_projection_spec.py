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

"""A class that creates resource projection specification."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import sys


# A transform function name to evaluate global restrictions. A parsed function
# name cannot contain a '.', so this name will not conflict with any valid
# transform name.
GLOBAL_RESTRICTION_NAME = 'global.restriction'

PROJECTION_ARG_DOC = ' projection: The parent ProjectionSpec.'

ALIGN_DEFAULT = 'left'
ALIGNMENTS = {'left': lambda s, w: s.ljust(w),
              'center': lambda s, w: s.center(w),
              'right': lambda s, w: s.rjust(w)}


def CombineDefaults(defaults):
  """Combines a list of defaults into a new defaults object.

  Args:
    defaults: An ordered list of ProjectionSpec objects to combine. alias and
      symbol names from higher index objects in the list take precedence.

  Returns:
    A new ProjectionSpec object that is a combination of the objects in the
    defaults list.
  """
  aliases = {}
  symbols = {}
  for default in defaults:
    if not default:
      continue
    if default.symbols:
      symbols.update(default.symbols)
    if default.aliases:
      aliases.update(default.aliases)
  return ProjectionSpec(symbols=symbols, aliases=aliases)


class ProjectionSpec(object):
  """Creates a resource projection specification.

  A resource projection is an expression string that contains a list of resource
  keys with optional attributes. A projector is a method that takes a projection
  specification and a resource object as input and produces a new
  JSON-serializable object containing only the values corresponding to the keys
  in the projection specification.

  Optional projection key attributes may transform the values in the output
  JSON-serializable object. Cloud SDK projection attributes are used for output
  formatting.

  A default or empty projection expression still produces a projector that
  converts a resource to a JSON-serializable object.

  This class is used by the resource projection expression parser to create a
  resource projection specification from a projection expression string.

  Attributes:
    aliases: Resource key alias dictionary.
    _active: The transform active level. Incremented each time Defaults() is
      called. Used to determine active transforms.
    attributes: Projection attributes dict indexed by attribute name.
    _columns: A list of (key,_Attribute) tuples used to project a resource to
      a list of columns.
    _compiler: The projection compiler method for nested projections.
    _empty: An empty projection _Tree used by Projector().
    _name: The projection name from the expression string.
    _tree: The projection _Tree root, used by
      resource_projector.Evaluate() to efficiently project each resource.
    symbols: Default and caller-defined transform function dict indexed by
      function name.
  """

  DEFAULT = 0  # _Attribute default node flag.
  INNER = 1  # _Attribute inner node flag.
  PROJECT = 2  # _Attribute project node flag.

  class _Column(object):
    """Column key and transform attribute for self._columns.

    Attributes:
      key: The column key.
      attribute: The column key _Attribute.
    """

    def __init__(self, key, attribute):
      self.key = key
      self.attribute = attribute

  def __init__(self, defaults=None, symbols=None, aliases=None, compiler=None):
    """Initializes a projection.

    Args:
      defaults: A list of resource_projection_spec.ProjectionSpec defaults.
      symbols: Transform function symbol table dict indexed by function name.
      aliases: Resource key alias dictionary.
      compiler: The projection compiler method for nested projections.
    """
    self.aliases = aliases or {}
    self.attributes = {}
    self._columns = []
    self._compiler = compiler
    self._empty = None
    self._name = None
    self._snake_headings = {}
    self._snake_re = None
    if defaults:
      self._active = defaults.active
      self._tree = copy.deepcopy(defaults.GetRoot())
      self.Defaults()
      self.symbols = copy.deepcopy(symbols) if symbols else {}
      if defaults.symbols:
        self.symbols.update(defaults.symbols)
      if defaults.aliases:
        self.aliases.update(defaults.aliases)
    else:
      self._active = 0
      self._tree = None
      self.symbols = symbols or {}

  @property
  def active(self):
    """Gets the transform active level."""
    return self._active

  @property
  def compiler(self):
    """Returns the projection compiler method for nested projections."""
    return self._compiler

  def _Defaults(self, projection):
    """Defaults() helper -- converts a projection to a default projection.

    Args:
      projection: A node in the original projection _Tree.
    """
    projection.attribute.flag = self.DEFAULT
    for node in projection.tree.values():
      self._Defaults(node)

  def _Print(self, projection, out, level):
    """Print() helper -- prints projection node p and its children.

    Sorted by projection tree level for diff stability.

    Args:
      projection: A _Tree node in the original projection.
      out: The output stream.
      level: The nesting level counting from 1 at the root.
    """
    for key in sorted(projection.tree):
      out.write('{indent} {key} : {attribute}\n'.format(
          indent='  ' * level,
          key=key,
          attribute=projection.tree[key].attribute))
      self._Print(projection.tree[key], out, level + 1)

  def AddAttribute(self, name, value):
    """Adds name=value to the attributes.

    Args:
      name: The attribute name.
      value: The attribute value
    """
    self.attributes[name] = value

  def DelAttribute(self, name):
    """Deletes name from the attributes if it is in the attributes.

    Args:
      name: The attribute name.
    """
    if name in self.attributes:
      del self.attributes[name]

  def AddAlias(self, name, key, attribute):
    """Adds name as an alias for key and attribute to the projection.

    Args:
      name: The short (no dots) alias name for key.
      key: The parsed key to add.
      attribute: The attribute for key.
    """
    self.aliases[name] = (key, attribute)

  def AddKey(self, key, attribute):
    """Adds key and attribute to the projection.

    Args:
      key: The parsed key to add.
      attribute: Parsed _Attribute to add.
    """
    self._columns.append(self._Column(key, attribute))

  def SetName(self, name):
    """Sets the projection name.

    The projection name is the rightmost of the names in the expression.

    Args:
      name: The projection name.
    """
    if self._name:
      # Reset the name-specific attributes.
      self.attributes = {}
    self._name = name

  def GetRoot(self):
    """Returns the projection root node.

    Returns:
      The resource_projector_parser._Tree root node.
    """
    return self._tree

  def SetRoot(self, root):
    """Sets the projection root node.

    Args:
      root: The resource_projector_parser._Tree root node.
    """
    self._tree = root

  def GetEmpty(self):
    """Returns the projector resource_projector_parser._Tree empty node.

    Returns:
      The projector resource_projector_parser._Tree empty node.
    """
    return self._empty

  def SetEmpty(self, node):
    """Sets the projector resource_projector_parser._Tree empty node.

    The empty node is used by to apply [] empty slice projections.

    Args:
      node: The projector resource_projector_parser._Tree empty node.
    """
    self._empty = node

  def Columns(self):
    """Returns the projection columns.

    Returns:
      The columns in the projection, None if the entire resource is projected.
    """
    return self._columns

  def ColumnCount(self):
    """Returns the number of columns in the projection.

    Returns:
      The number of columns in the projection, 0 if the entire resource is
        projected.
    """
    return len(self._columns)

  def Defaults(self):
    """Converts the projection to a default projection.

    A default projection provides defaults for attribute values and function
    symbols. An explicit non-default projection value always overrides the
    corresponding default value.
    """
    if self._tree:
      self._Defaults(self._tree)
    self._columns = []
    self._active += 1

  def Aliases(self):
    """Returns the short key name alias dictionary.

    This dictionary maps short (no dots) names to parsed keys.

    Returns:
      The short key name alias dictionary.
    """
    return self.aliases

  def Attributes(self):
    """Returns the projection _Attribute dictionary.

    Returns:
      The projection _Attribute dictionary.
    """
    return self.attributes

  def Alignments(self):
    """Returns the projection column justfication list.

    Returns:
      The ordered list of alignment functions, where each function is one of
        ljust [default], center, or rjust.
    """
    return [ALIGNMENTS[col.attribute.align] for col in self._columns]

  def Labels(self):
    """Returns the ordered list of projection labels.

    Returns:
      The ordered list of projection label strings, None if all labels are
        empty.
    """
    labels = [col.attribute.label or '' for col in self._columns]
    return labels if any(labels) else None

  def Name(self):
    """Returns the projection name.

    The projection name is the rightmost of the names in the expression.

    Returns:
      The projection name, None if none was specified.
    """
    return self._name

  def Order(self):
    """Returns the projection sort key order suitable for use by sorted().

    Example:
      projection = resource_projector.Compile('...')
      order = projection.Order()
      if order:
        rows = sorted(rows, key=itemgetter(*order))

    Returns:
      The list of (sort-key-index, reverse), [] if projection is None
      or if all sort order indices in the projection are None (unordered).
    """
    ordering = []
    for i, col in enumerate(self._columns):
      if col.attribute.order or col.attribute.reverse:
        ordering.append(
            (col.attribute.order or sys.maxsize, i, col.attribute.reverse))
    return [(i, reverse) for _, i, reverse in sorted(ordering)]

  def Print(self, out=sys.stdout):
    """Prints the projection with indented nesting.

    Args:
      out: The output stream, sys.stdout if None.
    """
    if self._tree:
      self._Print(self._tree, out, 1)

  def Tree(self):
    """Returns the projection tree root.

    Returns:
      The projection tree root.
    """
    return self._tree
