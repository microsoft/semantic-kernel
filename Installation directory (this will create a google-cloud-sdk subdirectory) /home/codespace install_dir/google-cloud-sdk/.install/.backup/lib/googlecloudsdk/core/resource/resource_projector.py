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

"""A class for projecting and transforming JSON-serializable objects.

From the Cloud SDK doc "DD: gcloud resource projection algorithm":

  Algorithm

  The algorithm represents a resource R and projection P as trees. P is used
  to color the nodes of R (with the colors {0, 1, 2, 3}) as follows:

  1. Initialize the nodes in R to (id, 0, identity).
  2. Do a DFS on P. Let p be the projection subtree and r be the resource
     subtree at each level. Let f be a flag value at each level, and initialize
     f to the flag value of the root node of P.
     2.1. For each id i in p that is also in r, set r[i].flag |= p[i].flag | f,
          and r[i].transform = p[i].transform if  r[i].transform != identity and
          p[i].transform != identity.
     2.2. If p contains a slice then repeat step 2.1 with i = slice.
     2.3. If r[i].flag is 0 then prune the search at this node, otherwise
     2.4. descend to the next level with r = r[i], p = p[i], and f = r[i].flag.
  3. At the end of the search the nodes of R will be colored with the values
     {0, 1, 2, 3}. The projected keys are the set of the longest paths from the
     root of R ending with a flag value >= 2.

  Remarks

  If the initial value of f is PROJECT or PROJECT* (2 or 3) then all keys in R
  are projected. Non-leaf keys may be projected in this model, resulting in dict
  or list values instead of scalars.

Example usage:

  projector = resource_projector.Compile(expression)
  for resource in resources:
    obj = projector.Evaluate(resource)
    OperateOnProjectedResource(obj)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import json

from apitools.base.protorpclite import messages as protorpc_message
from apitools.base.py import encoding as protorpc_encoding

from googlecloudsdk.core.resource import resource_projection_parser
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import encoding

import six
from six.moves import range  # pylint: disable=redefined-builtin

if six.PY3:
  import proto  # pylint: disable=g-import-not-at-top


def MakeSerializable(resource):
  """Returns resource or a JSON-serializable copy of resource.

  Args:
    resource: The resource object.

  Returns:
    The original resource if it is a primitive type object, otherwise a
    JSON-serializable copy of resource.
  """
  return Compile().Evaluate(resource)


class Projector(object):
  """Projects a resource using a ProjectionSpec.

  A projector is a method that takes an object and a projection as input and
  produces a new JSON-serializable object containing only the values
  corresponding to the keys in the projection. Optional projection key
  attributes may transform the values in the resulting JSON-serializable object.

  Attributes:
    _projection: The projection object.
    _been_here_done_that: A set of the current object id()'s being projected.
      Used to catch recursive objects like datetime.datetime.max.
    _by_columns: True if Projector projects to a list of columns.
    _columns: self._projection.Columns() column attributes.
    _ignore_default_transforms: Ignore default projection transforms if True.
    _retain_none_values: Retain dict entries with None values.
    _transforms_enabled_attribute: The projection.Attributes()
      transforms_enabled setting.
    _transforms_enabled: Projection attribute transforms enabled if True,
      disabled if False, or set by each Evaluate().
  """

  def __init__(self, projection, by_columns=False,
               ignore_default_transforms=False, retain_none_values=False):
    """Constructor.

    Args:
      projection: A ProjectionSpec (parsed resource projection expression).
      by_columns: Project to a list of columns if True.
      ignore_default_transforms: Ignore default projection transforms if True.
      retain_none_values: project dict entries with None values.
    """
    self._projection = projection
    self._by_columns = by_columns
    self._columns = self._projection.Columns()
    self._ignore_default_transforms = ignore_default_transforms
    self._retain_none_values = retain_none_values
    self._been_here_done_that = set()
    attributes = projection.Attributes()
    if 'transforms' in attributes:
      self._transforms_enabled_attribute = True
    elif 'no-transforms' in attributes:
      self._transforms_enabled_attribute = False
    else:
      self._transforms_enabled_attribute = None
    self._json_decode = 'json-decode' in attributes

  def _TransformIsEnabled(self, transform):
    """Returns True if transform is enabled.

    Args:
      transform: The resource_projection_parser._Transform object.

    Returns:
      True if the transform is enabled, False if not.
    """
    if self._transforms_enabled is not None:
      return self._transforms_enabled
    return transform.active in (None, self._projection.active)

  def _ProjectAttribute(self, obj, projection, flag):
    """Applies projection.attribute.transform in projection if any to obj.

    Args:
      obj: An object.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.

    Returns:
      The transformed obj if there was a transform, otherwise the original obj.
    """
    if flag < self._projection.PROJECT:
      # Unprojected values are skipped.
      return None
    if (projection and projection.attribute and projection.attribute.transform
        and self._TransformIsEnabled(projection.attribute.transform)):
      # Transformed values end the DFS on this branch of the tree.
      return projection.attribute.transform.Evaluate(obj)
    # leaf=True makes sure we don't get back here with the same obj.
    return self._Project(obj, projection, flag, leaf=True)

  def _ProjectClass(self, obj, projection, flag):
    """Converts class object to a dict.

    Private and callable attributes are omitted in the dict.

    Args:
      obj: The class object to convert.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.

    Returns:
      The dict representing the class object.
    """
    r = {}
    exclude = set()
    if isinstance(obj, datetime.datetime):
      # The datetime.tzinfo object does not serialize, so we save the original
      # string representation, which by default has enough information to
      # reconstruct tzinfo.
      r['datetime'] = six.text_type(obj)
      # Exclude tzinfo and the default recursive attributes that really should
      # be external constants anyway.
      exclude.update(('max', 'min', 'resolution', 'tzinfo'))
    else:
      try:
        # Exclude static isupper class attributes.
        exclude.update([a for a in dir(obj.__class__) if a.isupper()])
      except AttributeError:
        pass
    for attr in dir(obj):
      if attr.startswith('_'):
        # Omit private attributes.
        continue
      if attr in exclude:
        # Omit excluded attributes.
        continue
      try:
        value = getattr(obj, attr)
      except:  # pylint: disable=bare-except, forgive property method errors.
        continue
      if hasattr(value, '__call__'):
        # Omit callable attributes.
        continue
      f = flag
      if attr in projection.tree:
        child_projection = projection.tree[attr]
        f |= child_projection.attribute.flag
        if f < self._projection.INNER:
          # This branch of the tree is dead.
          continue
        # This branch of the tree is still alive. self._Project() returns
        # None if there are no actual PROJECT hits below.
        r[attr] = self._Project(value, child_projection, f)
      else:
        r[attr] = self._ProjectAttribute(value, self._projection.GetEmpty(), f)
    return r

  def _ProjectDict(self, obj, projection, flag):
    """Projects a dictionary object.

    Args:
      obj: A dict.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.

    Returns:
      The projected obj.
    """
    if not obj:
      return obj
    res = {}
    try:
      six.iteritems(obj)
    except ValueError:
      return None
    for key, val in six.iteritems(obj):
      f = flag
      if key in projection.tree:
        child_projection = projection.tree[key]
        f |= child_projection.attribute.flag
        if f < self._projection.INNER:
          # This branch of the tree is dead.
          continue
        # This branch of the tree is still alive. self._Project() returns
        # None if there are no actual PROJECT hits below.
        val = self._Project(val, child_projection, f)
      else:
        val = self._ProjectAttribute(val, self._projection.GetEmpty(), f)
      if (val is not None or self._retain_none_values or
          f >= self._projection.PROJECT and self._columns):
        # Explicit projection paths always show none values.
        try:
          res[encoding.Decode(key)] = val
        except UnicodeError:
          res[key] = val
    return res or None

  def _ProjectList(self, obj, projection, flag):
    """Projects a list, tuple or set object.

    Args:
      obj: A list, tuple or set.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.

    Returns:
      The projected obj.
    """
    if obj is None:
      return None
    if not obj:
      return []

    # No iterators or generators beyond this point.
    try:
      _ = len(obj)
      try:
        _ = obj[0]
      except TypeError:
        # Convert a set like object to an ordered list.
        obj = sorted(obj)
    except TypeError:
      try:
        obj = list(obj)
      except TypeError:
        return None

    # Determine the explicit indices or slice.
    # If there is a slice index then every index is projected.
    indices = set([])
    sliced = None
    if not projection.tree:
      # With no projection tree its all or nothing.
      if flag < self._projection.PROJECT:
        return None
    else:
      # Glean indices from the projection tree.
      for index in projection.tree:
        if index is None:
          if (flag >= self._projection.PROJECT or
              projection.tree[index].attribute.flag):
            sliced = projection.tree[index]
        elif (isinstance(index, six.integer_types) and
              index in range(-len(obj), len(obj))):
          indices.add(index)

    # Everything below a PROJECT node is projected.
    if flag >= self._projection.PROJECT and not sliced:
      sliced = self._projection.GetEmpty()

    # If there are no indices to match then nothing is projected.
    if not indices and not sliced:
      return None

    # Keep track of the max index projected.
    maxindex = -1
    if sliced:
      # A slice covers all indices.
      res = [None] * (len(obj))
    else:
      # Otherwise the result only includes the largest explict index.
      res = [None] * (max(x + len(obj) if x < 0 else x for x in indices) + 1)
    for index in range(len(obj)) if sliced else indices:
      val = obj[index]

      # Can't project something from nothing.
      if val is None:
        continue

      # Determine the child node projection.
      f = flag
      if index in projection.tree:
        # Explicit index in projection overrides slice.
        child_projection = projection.tree[index]
        if sliced:
          # Except the slice flag still counts.
          f |= sliced.attribute.flag
      else:
        # slice provides defaults for indices that are not explicit.
        child_projection = sliced

      # Now determine the value.
      if child_projection:
        f |= child_projection.attribute.flag
        if f >= self._projection.INNER:
          # This branch of the tree is still alive. self._Project() returns
          # None if there are no actual PROJECT hits below.
          val = self._Project(val, child_projection, f)
        else:
          val = None

      # Don't record empty projections.
      if val is None:
        continue
      # Record the highest index so the rest can be stripped.
      if index < 0:
        index += len(obj)
      if maxindex < index:
        maxindex = index
      res[index] = val

    # If nothing was projected return None instead of a list of all None items.
    if maxindex < 0:
      return None

    # Some non-None elements. slice strips trailing None elements.
    return res[0:maxindex + 1] if sliced else res

  def _Project(self, obj, projection, flag, leaf=False):
    """Evaluate() helper function.

    This function takes a resource obj and a preprocessed projection. obj
    is a dense subtree of the resource schema (some keys values may be missing)
    and projection is a sparse, possibly improper, subtree of the resource
    schema. Improper in that it may contain paths that do not exist in the
    resource schema or object. _Project() traverses both trees simultaneously,
    guided by the projection tree. When a projection tree path reaches an
    non-existent obj tree path the projection tree traversal is pruned. When a
    projection tree path terminates with an existing obj tree path, that obj
    tree value is projected and the obj tree traversal is pruned.

    Since resources can be sparse a projection can reference values not present
    in a particular resource. Because of this the code is lenient on out of
    bound conditions that would normally be errors.

    Args:
      obj: An object.
      projection: Projection _Tree node.
      flag: A bitmask of DEFAULT, INNER, PROJECT.
      leaf: Do not call _ProjectAttribute() if True.

    Returns:
      An object containing only the key:values selected by projection, or obj if
      the projection is None or empty.
    """
    objid = id(obj)
    if objid in self._been_here_done_that:
      return None
    elif obj is None:
      pass
    elif isinstance(obj, six.text_type) or isinstance(obj, six.binary_type):
      # Don't use six.string_types because bytes are not considered a string
      # on Python 3.
      if isinstance(obj, six.binary_type):
        # If it's bytes, first decode it, then continue.
        obj = encoding.Decode(obj)
      # Check for {" because valid compact JSON keys are always "..." quoted.
      if (self._json_decode and (
          obj.startswith('{"') and obj.endswith('}') or
          obj.startswith('[') and obj.endswith(']'))):
        try:
          return self._Project(json.loads(obj), projection, flag, leaf=leaf)
        except ValueError:
          # OK if it's not JSON.
          pass
    elif (isinstance(obj, (bool, float, complex)) or
          isinstance(obj, six.integer_types)):
      # primitive data type
      pass
    elif isinstance(obj, bytearray):
      # bytearray copied to disassociate from original obj.
      obj = encoding.Decode(bytes(obj))
    elif isinstance(obj, protorpc_message.Enum):
      # protorpc enum
      obj = obj.name
    else:
      self._been_here_done_that.add(objid)
      from cloudsdk.google.protobuf import message as protobuf_message  # pylint: disable=g-import-not-at-top
      if isinstance(obj, protorpc_message.Message):
        # protorpc message
        obj = protorpc_encoding.MessageToDict(obj)
      elif isinstance(obj, protobuf_message.Message):
        # protobuf message
        from cloudsdk.google.protobuf import json_format as protobuf_encoding  # pylint: disable=g-import-not-at-top
        obj = protobuf_encoding.MessageToDict(obj)
      elif six.PY3 and isinstance(obj, proto.Message):
        # proto message
        obj = obj.__class__.to_dict(obj)
      elif not hasattr(obj, '__iter__') or hasattr(obj, '_fields'):
        # class object or collections.namedtuple() (via the _fields test).
        obj = self._ProjectClass(obj, projection, flag)
      if (projection and projection.attribute and
          projection.attribute.transform and
          self._TransformIsEnabled(projection.attribute.transform)):
        # Transformed nodes prune here.
        obj = projection.attribute.transform.Evaluate(obj)
      elif ((flag >= self._projection.PROJECT or projection and projection.tree)
            and hasattr(obj, '__iter__')):
        if hasattr(obj, 'items'):
          try:
            obj = self._ProjectDict(obj, projection, flag)
          except (IOError, TypeError):
            obj = None
        else:
          try:
            obj = self._ProjectList(obj, projection, flag)
          except (IOError, TypeError):
            obj = None
      self._been_here_done_that.discard(objid)
      return obj
    # _ProjectAttribute() may apply transforms functions on obj, even if it is
    # None. For example, a tranform that returns 'FAILED' for None values.
    return obj if leaf else self._ProjectAttribute(obj, projection, flag)

  def SetByColumns(self, enable):
    """Sets the projection to list-of-columns mode.

    Args:
      enable: Enables projection to a list-of-columns if True.
    """
    self._by_columns = enable

  def SetIgnoreDefaultTransforms(self, enable):
    """Sets the ignore default transforms mode.

    Args:
      enable: Disable default projection transforms if True.
    """
    self._ignore_default_transforms = enable

  def SetRetainNoneValues(self, enable):
    """Sets the projection to retain-none-values mode.

    Args:
      enable: Enables projection to a retain-none-values if True.
    """
    self._retain_none_values = enable

  def Evaluate(self, obj):
    """Serializes/projects/transforms obj.

    A default or empty projection expression simply converts a resource object
    to a JSON-serializable copy of the object.

    Args:
      obj: An object.

    Returns:
      A JSON-serializeable object containing only the key values selected by
        the projection. The return value is a deep copy of the object: changes
        to the input object do not affect the JSON-serializable copy.
    """
    self._transforms_enabled = self._transforms_enabled_attribute
    if not self._by_columns or not self._columns:
      if self._columns:
        self._retain_none_values = False
        flag = self._projection.DEFAULT
      else:
        flag = self._projection.PROJECT
      if hasattr(obj, 'MakeSerializable'):
        obj = obj.MakeSerializable()
      return self._Project(obj, self._projection.Tree(), flag)
    obj_serialized = self._Project(
        obj, self._projection.GetEmpty(), self._projection.PROJECT
    )
    if self._transforms_enabled_attribute is None:
      # By-column formats enable transforms by default.
      self._transforms_enabled = not self._ignore_default_transforms
    columns = []
    for column in self._columns:
      val = (
          resource_property.Get(obj_serialized, column.key)
          if column.key
          else obj_serialized
      )
      if column.attribute.transform and self._TransformIsEnabled(
          column.attribute.transform
      ):
        val = column.attribute.transform.Evaluate(val, obj)
      columns.append(val)
    return columns

  def Projection(self):
    """Returns the ProjectionSpec object for the projector.

    Returns:
      The ProjectionSpec object for the projector.
    """
    return self._projection


def Compile(expression='', defaults=None, symbols=None, by_columns=False,
            retain_none_values=False):
  """Compiles a resource projection expression.

  Args:
    expression: The resource projection string.
    defaults: resource_projection_spec.ProjectionSpec defaults.
    symbols: Transform function symbol table dict indexed by function name.
    by_columns: Project to a list of columns if True.
    retain_none_values: Retain dict entries with None values.

  Returns:
    A Projector containing the compiled expression ready for Evaluate().
  """
  projection = resource_projection_parser.Parse(
      expression, defaults=defaults, symbols=symbols, compiler=Compile)
  return Projector(projection, by_columns=by_columns,
                   retain_none_values=retain_none_values)


class IdentityProjector(Projector):
  """A no-op resource projector that preserves the original object."""

  def __init__(self):
    super(IdentityProjector, self).__init__(resource_projection_parser.Parse())

  def Evaluate(self, obj):
    return obj
