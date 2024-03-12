# Copyright 2006 Google LLC.
# All Rights Reserved.
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

"""Higher-level, semantic data types for the datastore. These types
are expected to be set as attributes of Entities.  See "Supported Data Types"
in the API Guide.

Most of these types are based on XML elements from Atom and GData elements
from the atom and gd namespaces. For more information, see:

  http://www.atomenabled.org/developers/syndication/
  https://developers.google.com/gdata/docs/1.0/elements

The namespace schemas are:

  http://www.w3.org/2005/Atom
  http://schemas.google.com/g/2005
"""


# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.


from __future__ import absolute_import


import base64
import calendar
import datetime
import os
import re
import time
from xml.sax import saxutils

from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3 import entity_pb

from googlecloudsdk.third_party.appengine.api import datastore_errors
from googlecloudsdk.third_party.appengine.api import namespace_manager
from googlecloudsdk.third_party.appengine.api import users
from googlecloudsdk.third_party.appengine.datastore import datastore_pb
from googlecloudsdk.third_party.appengine.datastore import datastore_pbs
from googlecloudsdk.third_party.appengine.datastore import entity_v4_pb
from googlecloudsdk.third_party.appengine.datastore import sortable_pb_encoder

from googlecloudsdk.third_party.appengine._internal import six_subset

if datastore_pbs._CLOUD_DATASTORE_ENABLED:
  from googlecloudsdk.third_party.appengine.datastore.datastore_pbs import googledatastore

# Maximum length for string properties, in bytes. If you need to store a
# larger string, use a Text property.
#
# This should be kept in sync with j/c/g/apphosting/datastore/Paths.java,
# apphosting/demos/documentation/templates/apis.html and the
# --max_indexed_property_bytes datastore flag.
_MAX_STRING_LENGTH = 1500

# Maximum length for Link properties, in bytes. If you need to store a larger
# link, use a Text property.
#
# The URL RFCs don't specify a maximum length, so this is somewhat arbitrary:
# it's the well-documented maximum URL length supported by Internet Explorer.
# See http://b/1005416 for discussion.
#
# This should be kept in sync with j/c/g/apphosting/datastore/Paths.java,
# apphosting/demos/documentation/templates/apis.html and the
# --max_atom_link_bytes datastore flag.
_MAX_LINK_PROPERTY_LENGTH = 2083

# Maximum length for raw property strings
# or the --max_raw_property_bytes datastore flag.
_MAX_RAW_PROPERTY_BYTES = 1048487

# The datastore will not allow storing property names that match this.
#
# This must match the corresponding regexps in the datastore server,
# com.google.apphosting.datastore.Paths.RESERVED_NAME, and in other language
# APIs.
RESERVED_PROPERTY_NAME = re.compile('^__.*__$')

# Special properties have values that are determined by something other than a
# normal property value.
#
# Currently, there are two special properties:
#   a) __key__ its value is the entity's primary key.
#   b) __unapplied_log_timestamp_us__ its value is the entity failed commit time
KEY_SPECIAL_PROPERTY = '__key__'
_KEY_SPECIAL_PROPERTY = KEY_SPECIAL_PROPERTY  # Backwards compatibility.
_UNAPPLIED_LOG_TIMESTAMP_SPECIAL_PROPERTY = '__unapplied_log_timestamp_us__'
SCATTER_SPECIAL_PROPERTY = '__scatter__'
_SPECIAL_PROPERTIES = frozenset(
    [KEY_SPECIAL_PROPERTY,
     _UNAPPLIED_LOG_TIMESTAMP_SPECIAL_PROPERTY,
     SCATTER_SPECIAL_PROPERTY])

# Namespace separator is used to decode an "app_id" + "namespace"
# string.
#
# This must match the NAMESPACE_SEPARATOR values in C++ and Java.
# //apphosting/datastore/appid_namespace.h and
# //java/com/google/apphosting/api/NamespaceResources.java
_NAMESPACE_SEPARATOR = '!'

# The id used for the entity representing the empty (default) namespace in
# namespace queries (__namespace__ pseudo-kind).
# This must match the value of EMPTY_NAMESPACE_ID in
# //java/com/google/apphosting/datastore/NamespacePseudoKind.java
_EMPTY_NAMESPACE_ID = 1

# Serialized GD_WHEN integers values are offsets relative to this epoch.
_EPOCH = datetime.datetime.utcfromtimestamp(0)


if six_subset.PY2:
  _PREFERRED_NUM_TYPE = long  # pylint:disable=invalid-name
else:
  _PREFERRED_NUM_TYPE = int  # pylint:disable=invalid-name


# A trivial UTC tzinfo. See the datetime.tzinfo documentation for details. This
# is set on all datetimes returned from the datastore, and used to convert
# datetimes in other timezones to UTC before storing them in the datastore.
class UtcTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(0)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'UTC'
  def __repr__(self): return 'datastore_types.UTC'

UTC = UtcTzinfo()


def typename(obj):
  """Returns the type of obj as a string. More descriptive and specific than
  type(obj), and safe for any object, unlike __class__."""
  if hasattr(obj, '__class__'):
    return getattr(obj, '__class__').__name__
  else:
    return type(obj).__name__


def ValidateString(value,
                   name='unused',
                   exception=datastore_errors.BadValueError,
                   max_len=_MAX_STRING_LENGTH,
                   empty_ok=False):
  """Raises an exception if value is not a valid string or a subclass thereof.

  A string is valid if it's not empty, no more than _MAX_STRING_LENGTH bytes,
  and not a Blob. The exception type can be specified with the exception
  argument; it defaults to BadValueError.

  Args:
    value: the value to validate.
    name: the name of this value; used in the exception message.
    exception: the type of exception to raise.
    max_len: the maximum allowed length, in bytes.
    empty_ok: allow empty value.
  """
  if value is None and empty_ok:
    return
  if not isinstance(value, basestring) or isinstance(value, Blob):
    raise exception('%s should be a string; received %s (a %s):' %
                    (name, value, typename(value)))
  if not value and not empty_ok:
    raise exception('%s must not be empty.' % name)

  if len(value.encode('utf-8')) > max_len:
    raise exception('%s must be under %d bytes.' % (name, max_len))


def ValidateInteger(value,
                   name='unused',
                   exception=datastore_errors.BadValueError,
                   empty_ok=False,
                   zero_ok=False,
                   negative_ok=False):
  """Raises an exception if value is not a valid integer.

  An integer is valid if it's not negative or empty and is an integer
  (either int or long).  The exception type raised can be specified
  with the exception argument; it defaults to BadValueError.

  Args:
    value: the value to validate.
    name: the name of this value; used in the exception message.
    exception: the type of exception to raise.
    empty_ok: allow None value.
    zero_ok: allow zero value.
    negative_ok: allow negative value.
  """
  if value is None and empty_ok:
    return
  if not isinstance(value, six_subset.integer_types):
    raise exception('%s should be an integer; received %s (a %s).' %
                    (name, value, typename(value)))
  if not value and not zero_ok:
    raise exception('%s must not be 0 (zero)' % name)
  if value < 0 and not negative_ok:
    raise exception('%s must not be negative.' % name)

def ResolveAppId(app):
  """Validate app id, providing a default.

  If the argument is None, $APPLICATION_ID is substituted.

  Args:
    app: The app id argument value to be validated.

  Returns:
    The value of app, or the substituted default.  Always a non-empty string.

  Raises:
    BadArgumentError if the value is empty or not a string.
  """
  if app is None:
    app = os.environ.get('APPLICATION_ID', '')
  ValidateString(app, 'app', datastore_errors.BadArgumentError)
  return app


def ResolveNamespace(namespace):
  """Validate app namespace, providing a default.

  If the argument is None, namespace_manager.get_namespace() is substituted.

  Args:
    namespace: The namespace argument value to be validated.

  Returns:
    The value of namespace, or the substituted default. The empty string is used
    to denote the empty namespace.

  Raises:
    BadArgumentError if the value is not a string.
  """
  if namespace is None:
    namespace = namespace_manager.get_namespace()
  else:
    namespace_manager.validate_namespace(
        namespace, datastore_errors.BadArgumentError)
  return namespace


def EncodeAppIdNamespace(app_id, namespace):
  """Concatenates app id and namespace into a single string.

  This method is needed for xml and datastore_file_stub.

  Args:
    app_id: The application id to encode
    namespace: The namespace to encode

  Returns:
    The string encoding for the app_id, namespace pair.
  """
  if not namespace:
    return app_id
  else:
    return app_id + _NAMESPACE_SEPARATOR + namespace


def DecodeAppIdNamespace(app_namespace_str):
  """Decodes app_namespace_str into an (app_id, namespace) pair.

  This method is the reverse of EncodeAppIdNamespace and is needed for
  datastore_file_stub.

  Args:
    app_namespace_str: An encoded app_id, namespace pair created by
      EncodeAppIdNamespace

  Returns:
    (app_id, namespace) pair encoded in app_namespace_str
  """
  sep = app_namespace_str.find(_NAMESPACE_SEPARATOR)
  if sep < 0:
    return (app_namespace_str, '')
  else:
    return (app_namespace_str[0:sep], app_namespace_str[sep + 1:])


def SetNamespace(proto, namespace):
  """Sets the namespace for a protocol buffer or clears the field.

  Args:
    proto: the protocol buffer to update
    namespace: the new namespace (None or an empty string will clear out the
        field).
  """
  if not namespace:
    proto.clear_name_space()
  else:
    proto.set_name_space(namespace)


def PartitionString(value, separator):
  """Equivalent to python2.5 str.partition()
     TODO(user) use str.partition() when python 2.5 is adopted.

  Args:
    value: String to be partitioned
    separator: Separator string
  """
  index = value.find(separator)
  if index == -1:
    return (value, '', value[0:0])
  else:
    return (value[0:index], separator, value[index+len(separator):len(value)])



class Key(object):
  """The primary key for a datastore entity.

  A datastore GUID. A Key instance uniquely identifies an entity across all
  apps, and includes all information necessary to fetch the entity from the
  datastore with Get().

  Key implements __hash__, and key instances are immutable, so Keys may be
  used in sets and as dictionary keys.
  """
  __reference = None

  def __init__(self, encoded=None):
    """Constructor. Creates a Key from a string.

    Args:
      # a base64-encoded primary key, generated by Key.__str__
      encoded: str
    """
    self._str = None
    if encoded is not None:
      if not isinstance(encoded, basestring):
        try:
          repr_encoded = repr(encoded)
        except:
          repr_encoded = "<couldn't encode>"
        raise datastore_errors.BadArgumentError(
          'Key() expects a string; received %s (a %s).' %
          (repr_encoded, typename(encoded)))
      try:
        # add padding back, if necessary
        modulo = len(encoded) % 4
        if modulo != 0:
          encoded += ('=' * (4 - modulo))

        # decode the Reference PB
        # Unicode cannot be base64 decoded directly, hence str().
        #
        # Note: This must be consistent across languages.  If it
        # changes, make sure that similar logic in Java changes as
        # well.  You will also need to update the golden test files.
        self._str = str(encoded)
        encoded_pb = base64.urlsafe_b64decode(self._str)
        self.__reference = entity_pb.Reference(encoded_pb)
        assert self.__reference.IsInitialized()

        # now we have to remove the padding from the cached string
        self._str = self._str.rstrip('=')

      except (AssertionError, TypeError) as e:
        raise datastore_errors.BadKeyError(
          'Invalid string key %s. Details: %s' % (encoded, e))
      except Exception as e:  # pylint:disable=broad-except
        # NOTE(user): ugh. ProtocolBuffer.py and the SWIG-wrapped C module
        # both provide a ProtocolBufferDecodeError, but python considers them
        # different types. 'except ProtocolBufferDecodeError' catches the
        # python one but not the C one. hence this monstrosity.
        # see http://b/1067354.
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
          raise datastore_errors.BadKeyError('Invalid string key %s.' % encoded)
        else:
          raise
    else:
      # empty key
      self.__reference = entity_pb.Reference()

  def to_path(self, _default_id=None, _decode=True, _fail=True):
    """Construct the "path" of this key as a list.

    Returns:
      A list [kind_1, id_or_name_1, ..., kind_n, id_or_name_n] of the key path.

    Raises:
      datastore_errors.BadKeyError if this key does not have a valid path.
    """
    # Private args:
    #   _default_id: if provided, integer id to be applied if a key element
    #     doesn't contain neither id nor name, otherwise raise an
    #     datastore_errors.BadKeyError.
    #   _decode: if True, decode type and name assuming they are utf-8 encoded.
    #   _fail: on invalid utf-8: if True, raise error, if False return s
    def Decode(s):
      if _decode:
        try:
          return s.decode('utf-8')
        except UnicodeDecodeError:
          if _fail:
            raise
      return s

    path = []
    for path_element in self.__reference.path().element_list():
      path.append(Decode(path_element.type()))
      if path_element.has_name():
        path.append(Decode(path_element.name()))
      elif path_element.has_id():
        path.append(path_element.id())
      elif _default_id is not None:
        path.append(_default_id)
      else:
        raise datastore_errors.BadKeyError('Incomplete key found in to_path')
    return path

  @staticmethod
  def from_path(*args, **kwds):
    """Static method to construct a Key out of a "path" (kind, id or name, ...).

    This is useful when an application wants to use just the id or name portion
    of a key in e.g. a URL, where the rest of the URL provides enough context to
    fill in the rest, i.e. the app id (always implicit), the entity kind, and
    possibly an ancestor key. Since ids and names are usually small, they're
    more attractive for use in end-user-visible URLs than the full string
    representation of a key.

    Args:
      kind: the entity kind (a str or unicode instance)
      id_or_name: the id (an int or long) or name (a str or unicode instance)
      parent: optional parent Key; default None.
      namespace: optional namespace to use otherwise namespace_manager's
        default namespace is used.

    Returns:
      A new Key instance whose .kind() and .id() or .name() methods return
      the *last* kind and id or name positional arguments passed.

    Raises:
      BadArgumentError for invalid arguments.
      BadKeyError if the parent key is incomplete.
    """
    # Extract keyword args
    parent = kwds.pop('parent', None)
    # _app is not documented; see datastore.Entity
    app_id = ResolveAppId(kwds.pop('_app', None))

    # Use the parent namespace if parent is specified and
    # namespace is not specified.  This is validated later.
    namespace = kwds.pop('namespace', None)

    # Insist those were the only two keyword args
    if kwds:
      raise datastore_errors.BadArgumentError(
          'Excess keyword arguments ' + repr(kwds))

    # Insist on one or more (kind, id/name) pairs as positional args
    if not args or len(args) % 2:
      raise datastore_errors.BadArgumentError(
          'A non-zero even number of positional arguments is required '
          '(kind, id or name, kind, id or name, ...); received %s' % repr(args))

    # Type-check parent
    if parent is not None:
      if not isinstance(parent, Key):
        raise datastore_errors.BadArgumentError(
            'Expected None or a Key as parent; received %r (a %s).' %
            (parent, typename(parent)))
      if namespace is None:
        namespace = parent.namespace()
      if not parent.has_id_or_name():
        raise datastore_errors.BadKeyError(
            'The parent Key is incomplete.')
      if app_id != parent.app() or namespace != parent.namespace():
        raise datastore_errors.BadArgumentError(
            'The app/namespace arguments (%s/%s) should match '
            'parent.app/namespace() (%s/%s)' %
            (app_id, namespace, parent.app(), parent.namespace()))

    # Go find a namespace if it's not specified and validate namespace.
    namespace = ResolveNamespace(namespace)

    # Construct a Key from the parent and/or the app id
    key = Key()
    ref = key.__reference
    if parent is not None:
      ref.CopyFrom(parent.__reference)
    else:
      ref.set_app(app_id)
      SetNamespace(ref, namespace)

    # Add the (kind, id/name) pairs, while typechecking them
    # TODO(user): Optimize this section
    path = ref.mutable_path()
    for i in xrange(0, len(args), 2):
      kind, id_or_name = args[i:i+2]
      if isinstance(kind, basestring):
        kind = kind.encode('utf-8')
      else:
        raise datastore_errors.BadArgumentError(
            'Expected a string kind as argument %d; received %r (a %s).' %
            (i + 1, kind, typename(kind)))
      elem = path.add_element()
      elem.set_type(kind)
      if isinstance(id_or_name, six_subset.integer_types):
        elem.set_id(id_or_name)
      elif isinstance(id_or_name, basestring):
        ValidateString(id_or_name, 'name')
        elem.set_name(id_or_name.encode('utf-8'))
      else:
        raise datastore_errors.BadArgumentError(
            'Expected an integer id or string name as argument %d; '
            'received %r (a %s).' % (i + 2, id_or_name, typename(id_or_name)))

    # One final check, and we're all set
    assert ref.IsInitialized()
    return key

  def app(self):
    """Returns this entity's app id, a string."""
    if self.__reference.app():
      return self.__reference.app().decode('utf-8')
    else:
      return None

  def namespace(self):
    """Returns this entity's namespace, a string."""
    if self.__reference.has_name_space():
      return self.__reference.name_space().decode('utf-8')
    else:
      return ''  # If None is used as a namespace parameter it is
      # converted to the "current" namespace. Hence
      # we cannot return None.

  def kind(self):
    """Returns this entity's kind, as a string."""
    if self.__reference.path().element_size() > 0:
      encoded = self.__reference.path().element_list()[-1].type()
      return six_subset.text_type(encoded.decode('utf-8'))
    else:
      return None

  def id(self):
    """Returns this entity's id, or None if it doesn't have one."""
    elems = self.__reference.path().element_list()
    if elems and elems[-1].has_id() and elems[-1].id():
      return elems[-1].id()
    else:
      return None

  def name(self):
    """Returns this entity's name, or None if it doesn't have one."""
    elems = self.__reference.path().element_list()
    if elems and elems[-1].has_name() and elems[-1].name():
      return elems[-1].name().decode('utf-8')
    else:
      return None

  def id_or_name(self):
    """Returns this entity's id or name, whichever it has, or None."""
    if self.id() is not None:
      return self.id()
    else:
      # may be None
      return self.name()

  def has_id_or_name(self):
    """Returns True if this entity has an id or name, False otherwise.
    """
    elems = self.__reference.path().element_list()
    if elems:
      e = elems[-1]
      return bool(e.name() or e.id())
    else:
      return False

  def parent(self):
    """Returns this entity's parent, as a Key. If this entity has no parent,
    returns None."""
    if self.__reference.path().element_size() > 1:
      parent = Key()
      parent.__reference.CopyFrom(self.__reference)
      del parent.__reference.path().element_list()[-1]
      return parent
    else:
      return None

  def ToTagUri(self):
    """Returns a tag: URI for this entity for use in XML output.

    Foreign keys for entities may be represented in XML output as tag URIs.
    RFC 4151 describes the tag URI scheme. From http://taguri.org/:

      The tag algorithm lets people mint - create - identifiers that no one
      else using the same algorithm could ever mint. It is simple enough to do
      in your head, and the resulting identifiers can be easy to read, write,
      and remember. The identifiers conform to the URI (URL) Syntax.

    Tag URIs for entities use the app's auth domain and the date that the URI
     is generated. The namespace-specific part is <kind>[<key>].

    For example, here is the tag URI for a Kitten with the key "Fluffy" in the
    catsinsinks app:

      tag:catsinsinks.googleapps.com,2006-08-29:Kitten[Fluffy]

    Raises a BadKeyError if this entity's key is incomplete.
    """
    if not self.has_id_or_name():
      raise datastore_errors.BadKeyError(
        'ToTagUri() called for an entity with an incomplete key.')

    return u'tag:%s.%s,%s:%s[%s]' % (
        #TODO(user): can we somehow "unmangle" this?
        saxutils.escape(EncodeAppIdNamespace(self.app(), self.namespace())),
        os.environ['AUTH_DOMAIN'],
        datetime.date.today().isoformat(),
        saxutils.escape(self.kind()),
        saxutils.escape(str(self)))

  ToXml = ToTagUri

  def entity_group(self):
    """Returns this key's entity group as a Key.

    Note that the returned Key will be incomplete if this Key is for a root
    entity and it is incomplete.
    """
    group = Key._FromPb(self.__reference)
    del group.__reference.path().element_list()[1:]
    return group

  @staticmethod
  def _FromPb(pb):
    """Static factory method. Creates a Key from an entity_pb.Reference.

    Not intended to be used by application developers. Enforced by hiding the
    entity_pb classes.

    Args:
      pb: entity_pb.Reference
    """
    if not isinstance(pb, entity_pb.Reference):
      raise datastore_errors.BadArgumentError(
        'Key constructor takes an entity_pb.Reference; received %s (a %s).' %
        (pb, typename(pb)))

    key = Key()
    key.__reference = entity_pb.Reference()
    key.__reference.CopyFrom(pb)  # defensive copy
    return key

  def _ToPb(self):
    """Converts this Key to its protocol buffer representation.

    Not intended to be used by application developers. Enforced by hiding the
    entity_pb classes.

    Returns:
      # the Reference PB representation of this Key
      entity_pb.Reference
    """
    pb = entity_pb.Reference()
    pb.CopyFrom(self.__reference)

    # strings in the reference should already be UTF-8. check this by
    # attempting to decode them.
    pb.app().decode('utf-8')
    for pathelem in pb.path().element_list():
      pathelem.type().decode('utf-8')

    return pb

  def __str__(self):
    """Encodes this Key as an opaque string.

    Returns a string representation of this key, suitable for use in HTML,
    URLs, and other similar use cases. If the entity's key is incomplete,
    raises a BadKeyError.

    Unfortunately, this string encoding isn't particularly compact, and its
    length varies with the length of the path. If you want a shorter identifier
    and you know the kind and parent (if any) ahead of time, consider using just
    the entity's id or name.

    Returns:
      string
    """
    # Note: This must be consistent across languages.  If it changes,
    # make sure that similar logic in Java changes as well.  You will
    # also need to update the golden test files.
    try:
      if self._str is not None:
        return self._str
    except AttributeError:
      pass
    if (self.has_id_or_name()):
      encoded = base64.urlsafe_b64encode(self.__reference.Encode())
      self._str = encoded.replace('=', '')  # strip padding
    else:
      raise datastore_errors.BadKeyError(
        'Cannot string encode an incomplete key!\n%s' % self.__reference)
    return self._str


  def __repr__(self):
    """Returns an eval()able string representation of this key.

    Returns a Python string of the form 'datastore_types.Key.from_path(...)'
    that can be used to recreate this key.

    Returns:
      string
    """
    args = []
    for elem in self.__reference.path().element_list():
      args.append(repr(elem.type().decode('utf-8')))
      if elem.has_name():
        args.append(repr(elem.name().decode('utf-8')))
      else:
        args.append(repr(elem.id()))  # this will be 0 if there's no id

    args.append('_app=%r' % self.__reference.app().decode('utf-8'))
    if self.__reference.has_name_space():
      args.append('namespace=%r' %
          self.__reference.name_space().decode('utf-8'))
    return u'datastore_types.Key.from_path(%s)' % ', '.join(args)

  def __cmp__(self, other):
    """Returns negative, zero, or positive when comparing two keys.

    TODO(user): for API v2, we should change this to make incomplete keys, ie
    keys without an id or name, not equal to any other keys.

    Args:
      other: Key to compare to.

    Returns:
      Negative if self is less than "other"
      Zero if "other" is equal to self
      Positive if self is greater than "other"
    """
    if not isinstance(other, Key):
      return -2

    self_args = [self.__reference.app(), self.__reference.name_space()]
    self_args += self.to_path(_default_id=0, _decode=False)

    other_args = [other.__reference.app(), other.__reference.name_space()]
    other_args += other.to_path(_default_id=0, _decode=False)

    for self_component, other_component in zip(self_args, other_args):
      comparison = cmp(self_component, other_component)
      if comparison != 0:
        return comparison

    return cmp(len(self_args), len(other_args))

  def __hash__(self):
    """Returns an integer hash of this key.

    Implements Python's hash protocol so that Keys may be used in sets and as
    dictionary keys.

    Returns:
      int
    """
    args = self.to_path(_default_id=0, _fail=False)
    args.append(self.__reference.app())
    return hash(type(args)) ^ hash(tuple(args))


class _OverflowDateTime(_PREFERRED_NUM_TYPE):
  """Container for GD_WHEN values that don't fit into a datetime.datetime.

  This class only exists to safely round-trip GD_WHEN values that are too large
  to fit in a datetime.datetime instance e.g. that were created by Java
  applications. It should not be created directly.
  """
  pass

def _EmptyList(val):
  if val is not None:
    raise datastore_errors.BadValueError('value should be None.')
  return []

def _When(val):
  """Coverts a GD_WHEN value to the appropriate type."""
  try:
    return _EPOCH + datetime.timedelta(microseconds=val)
  except OverflowError:
    return _OverflowDateTime(val)


# These classes subclass built-in POD types, specifically string and long. This
# is a little unsettling, but it works just like you'd expect. See:
#   http://www.python.org/download/releases/2.2.3/descrintro/
#
# Note that __str__ and __unicode__ are equivalent for these classes, but the
# str() built-in coerces __str__()'s return type to string, *not* unicode.
#
# TODO(user): escape CDATA characters in ToXml()s
class Category(six_subset.text_type):
  """A tag, ie a descriptive word or phrase. Entities may be tagged by users,
  and later returned by a queries for that tag. Tags can also be used for
  ranking results (frequency), photo captions, clustering, activity, etc.

  Here's a more in-depth description:  http://www.zeldman.com/daily/0405d.shtml

  This is the Atom "category" element. In XML output, the tag is provided as
  the term attribute. See:
  http://www.atomenabled.org/developers/syndication/#category

  Raises BadValueError if tag is not a string or subtype.
  """
  TERM = 'user-tag'

  def __init__(self, tag):
    super(Category, self).__init__()
    ValidateString(tag, 'tag')

  def ToXml(self):
    return u'<category term="%s" label=%s />' % (Category.TERM,
                                                 saxutils.quoteattr(self))


class Link(six_subset.text_type):
  """A fully qualified URL. Usually http: scheme, but may also be file:, ftp:,
  news:, among others.

  If you have email (mailto:) or instant messaging (aim:, xmpp:) links,
  consider using the Email or IM classes instead.

  This is the Atom "link" element. In XML output, the link is provided as the
  href attribute. See:
  http://www.atomenabled.org/developers/syndication/#link

  Raises BadValueError if link is not a fully qualified, well-formed URL.
  """
  def __init__(self, link):
    super(Link, self).__init__()
    ValidateString(link, 'link', max_len=_MAX_LINK_PROPERTY_LENGTH)

    scheme, domain, path, _, _, _ = six_subset.urlparse_fn(link)
    if (not scheme or (scheme != 'file' and not domain) or
                      (scheme == 'file' and not path)):
      raise datastore_errors.BadValueError('Invalid URL: %s' % link)

  def ToXml(self):
    return u'<link href=%s />' % saxutils.quoteattr(self)


class Email(six_subset.text_type):
  """An RFC2822 email address. Makes no attempt at validation; apart from
  checking MX records, email address validation is a rathole.

  This is the gd:email element. In XML output, the email address is provided as
  the address attribute. See:
  https://developers.google.com/gdata/docs/1.0/elements#gdEmail

  Raises BadValueError if email is not a valid email address.
  """
  def __init__(self, email):
    super(Email, self).__init__()
    ValidateString(email, 'email')

  def ToXml(self):
    return u'<gd:email address=%s />' % saxutils.quoteattr(self)


class GeoPt(object):
  """A geographical point, specified by floating-point latitude and longitude
  coordinates. Often used to integrate with mapping sites like Google Maps.
  May also be used as ICBM coordinates.

  This is the georss:point element. In XML output, the coordinates are
  provided as the lat and lon attributes. See: http://georss.org/

  Serializes to '<lat>,<lon>'. Raises BadValueError if it's passed an invalid
  serialized string, or if lat and lon are not valid floating points in the
  ranges [-90, 90] and [-180, 180], respectively.
  """
  lat = None
  lon = None

  def __init__(self, lat, lon=None):
    if lon is None:
      # serialized. parse out the individual coordinates
      try:
        split = lat.split(',')
        lat, lon = split  # errors if there aren't exactly two
      except (AttributeError, ValueError):
        raise datastore_errors.BadValueError(
          'Expected a "lat,long" formatted string; received %s (a %s).' %
          (lat, typename(lat)))

    try:
      lat = float(lat)
      lon = float(lon)
      if abs(lat) > 90:
        raise datastore_errors.BadValueError(
          'Latitude must be between -90 and 90; received %f' % lat)
      if abs(lon) > 180:
        raise datastore_errors.BadValueError(
          'Longitude must be between -180 and 180; received %f' % lon)
    except (TypeError, ValueError):
      # couldn't convert to float
      raise datastore_errors.BadValueError(
        'Expected floats for lat and long; received %s (a %s) and %s (a %s).' %
        (lat, typename(lat), lon, typename(lon)))

    self.lat = lat
    self.lon = lon

  def __cmp__(self, other):
    if not isinstance(other, GeoPt):
      try:
        other = GeoPt(other)
      except datastore_errors.BadValueError:
        return NotImplemented

    # sort first by latitude, then by longitude
    lat_cmp = cmp(self.lat, other.lat)
    if lat_cmp != 0:
      return lat_cmp
    else:
      return cmp(self.lon, other.lon)

  def __hash__(self):
    """Returns an integer hash of this point.

    Implements Python's hash protocol so that GeoPts may be used in sets and
    as dictionary keys.

    Returns:
      int
    """
    return hash((self.lat, self.lon))

  def __repr__(self):
    """Returns an eval()able string representation of this GeoPt.

    The returned string is of the form 'datastore_types.GeoPt([lat], [lon])'.

    Returns:
      string
    """
    return 'datastore_types.GeoPt(%r, %r)' % (self.lat, self.lon)

  def __unicode__(self):
    return u'%s,%s' % (six_subset.text_type(self.lat),
                       six_subset.text_type(self.lon))

  __str__ = __unicode__

  def ToXml(self):
    return u'<georss:point>%s %s</georss:point>' % (six_subset.text_type(
        self.lat), six_subset.text_type(self.lon))


class IM(object):
  """An instant messaging handle. Includes both an address and its protocol.
  The protocol value is either a standard IM scheme or a URL identifying the
  IM network for the protocol. Possible values include:

    Value                           Description
    sip                             SIP/SIMPLE
    unknown                         Unknown or unspecified
    xmpp                            XMPP/Jabber
    http://aim.com/                 AIM
    http://icq.com/                 ICQ
    http://talk.google.com/         Google Talk
    http://messenger.msn.com/       MSN Messenger
    http://messenger.yahoo.com/     Yahoo Messenger
    http://sametime.com/            Lotus Sametime
    http://gadu-gadu.pl/            Gadu-Gadu

  This is the gd:im element. In XML output, the address and protocol are
  provided as the address and protocol attributes, respectively. See:
  https://developers.google.com/gdata/docs/1.0/elements#gdIm

  Serializes to '<protocol> <address>'. Raises BadValueError if tag is not a
  standard IM scheme or a URL.
  """
  PROTOCOLS = [ 'sip', 'unknown', 'xmpp' ]

  protocol = None
  address = None

  def __init__(self, protocol, address=None):
    if address is None:
      # serialized. parse out the protocol and address
      try:
        split = protocol.split(' ', 1)
        protocol, address = split  # errors if there aren't exactly two
      except (AttributeError, ValueError):
        raise datastore_errors.BadValueError(
          'Expected string of format "protocol address"; received %s' %
          (protocol,))

    ValidateString(address, 'address')
    if protocol not in self.PROTOCOLS:
      # check that it's a valid URL
      Link(protocol)

    self.address = address
    self.protocol = protocol

  def __cmp__(self, other):
    if not isinstance(other, IM):
      try:
        other = IM(other)
      except datastore_errors.BadValueError:
        return NotImplemented

    # sort first by address, then by protocol

    # TODO(user): api v2
    # This is wrong but can't be fixed until we have a new major
    # api version.  The string representation of an IM
    # is protocol followed by address (see __unicode__ below), so the
    # datastore sort order is also going to be protocol followed by address.
    # Unfortunately, apps that are sorting IMs in memory that are relying
    # on this incorrect ordering will break if we change this.  So, we
    # need to wait for a new major api version to make the fix.
    return cmp((self.address, self.protocol),
               (other.address, other.protocol))

  def __repr__(self):
    """Returns an eval()able string representation of this IM.

    The returned string is of the form:

      datastore_types.IM('address', 'protocol')

    Returns:
      string
    """
    return 'datastore_types.IM(%r, %r)' % (self.protocol, self.address)

  def __unicode__(self):
    return u'%s %s' % (self.protocol, self.address)

  __str__ = __unicode__

  def ToXml(self):
    return (u'<gd:im protocol=%s address=%s />' %
            (saxutils.quoteattr(self.protocol),
             saxutils.quoteattr(self.address)))

  def __len__(self):
    return len(six_subset.text_type(self))


class PhoneNumber(six_subset.text_type):
  """A human-readable phone number or address.

  No validation is performed. Phone numbers have many different formats -
  local, long distance, domestic, international, internal extension, TTY,
  VOIP, SMS, and alternative networks like Skype, XFire and Roger Wilco. They
  all have their own numbering and addressing formats.

  This is the gd:phoneNumber element. In XML output, the phone number is
  provided as the text of the element. See:
  https://developers.google.com/gdata/docs/1.0/elements#gdPhoneNumber

  Raises BadValueError if phone is not a string or subtype.
  """
  def __init__(self, phone):
    super(PhoneNumber, self).__init__()
    ValidateString(phone, 'phone')

  def ToXml(self):
    return u'<gd:phoneNumber>%s</gd:phoneNumber>' % saxutils.escape(self)


class PostalAddress(six_subset.text_type):
  """A human-readable mailing address. Again, mailing address formats vary
  widely, so no validation is performed.

  This is the gd:postalAddress element. In XML output, the address is provided
  as the text of the element. See:
  https://developers.google.com/gdata/docs/1.0/elements#gdPostalAddress

  Raises BadValueError if address is not a string or subtype.
  """
  def __init__(self, address):
    super(PostalAddress, self).__init__()
    ValidateString(address, 'address')

  def ToXml(self):
    return u'<gd:postalAddress>%s</gd:postalAddress>' % saxutils.escape(self)


class Rating(_PREFERRED_NUM_TYPE):
  """A user-provided integer rating for a piece of content. Normalized to a
  0-100 scale.

  This is the gd:rating element. In XML output, the address is provided
  as the text of the element. See:
  https://developers.google.com/gdata/docs/1.0/elements#gdRating

  Serializes to the decimal string representation of the rating. Raises
  BadValueError if the rating is not an integer in the range [0, 100].
  """
  MIN = 0
  MAX = 100

  def __init__(self, rating):
    super(Rating, self).__init__()
    if isinstance(rating, float) or isinstance(rating, complex):
      # cowardly refuse to truncate
      raise datastore_errors.BadValueError(
        'Expected int or long; received %s (a %s).' %
        (rating, typename(rating)))

    try:
      if (_PREFERRED_NUM_TYPE(rating) < Rating.MIN
          or _PREFERRED_NUM_TYPE(rating) > Rating.MAX):
        raise datastore_errors.BadValueError()
    except ValueError:
      # couldn't convert to long
      raise datastore_errors.BadValueError(
          'Expected int or long; received %s (a %s).' %
          (rating, typename(rating)))

  def ToXml(self):
    return (u'<gd:rating value="%d" min="%d" max="%d" />' %
            (self, Rating.MIN, Rating.MAX))


class Text(six_subset.text_type):
  """A long string type.

  Strings of any length can be stored in the datastore using this
  type. It behaves identically to the Python unicode type, except for
  the constructor, which only accepts str and unicode arguments.
  """

  def __new__(cls, arg=None, encoding=None):
    """Constructor.

    We only accept unicode and str instances, the latter with encoding.

    Args:
      arg: optional unicode or str instance; default u''
      encoding: optional encoding; disallowed when isinstance(arg, unicode),
                defaults to 'ascii' when isinstance(arg, str);
    """
    if arg is None:
      arg = u''
    if isinstance(arg, six_subset.text_type):
      if encoding is not None:
        raise TypeError('Text() with a unicode argument '
                        'should not specify an encoding')
      return super(Text, cls).__new__(cls, arg)

    if isinstance(arg, six_subset.string_types):
      if encoding is None:
        encoding = 'ascii'
      return super(Text, cls).__new__(cls, arg, encoding)

    raise TypeError('Text() argument should be str or unicode, not %s' %
                    type(arg).__name__)

class _BaseByteType(str):
  """A base class for datastore types that are encoded as bytes.

  This behaves identically to the Python str type, except for the
  constructor, which only accepts str arguments.
  """

  def __new__(cls, arg=None):
    """Constructor.

    We only accept str instances.

    Args:
      arg: optional str instance (default '')
    """
    if arg is None:
      arg = ''
    if isinstance(arg, str):
      return super(_BaseByteType, cls).__new__(cls, arg)

    raise TypeError('%s() argument should be str instance, not %s' %
                    (cls.__name__, type(arg).__name__))

  def ToXml(self):
    """Output bytes as XML.

    Returns:
      Base64 encoded version of itself for safe insertion in to an XML document.
    """
    encoded = base64.urlsafe_b64encode(self)
    return saxutils.escape(encoded)


class Blob(_BaseByteType):
  """A blob type, appropriate for storing binary data of any length.

  This behaves identically to the Python str type, except for the
  constructor, which only accepts str arguments.
  """

  def __init__(self, *args, **kwargs):
    super(Blob, self).__init__(*args, **kwargs)
    self._meaning_uri = None

  @property
  def meaning_uri(self):
    return self._meaning_uri

  @meaning_uri.setter
  def meaning_uri(self, value):
    self._meaning_uri = value


class EmbeddedEntity(_BaseByteType):
  """A proto encoded EntityProto.

  This behaves identically to Blob, except for the
  constructor, which accepts a str or EntityProto argument.

  Can be decoded using datastore.Entity.FromProto(), db.model_from_protobuf() or
  ndb.LocalStructuredProperty.
  """

  def __new__(cls, arg=None):
    """Constructor.

    Args:
      arg: optional str or EntityProto instance (default '')
    """
    if isinstance(arg, entity_pb.EntityProto):
      arg = arg.SerializePartialToString()
    return super(EmbeddedEntity, cls).__new__(cls, arg)


class ByteString(_BaseByteType):
  """A byte-string type, appropriate for storing short amounts of indexed data.

  This behaves identically to Blob, except it's used only for short, indexed
  byte strings.
  """
  pass


class BlobKey(object):

  def __init__(self, blob_key):
    """Constructor.

    Used to convert a string to a BlobKey.  Normally used internally by
    Blobstore API.

    Args:
      blob_key:  Key name of BlobReference that this key belongs to.
    """
    ValidateString(blob_key, 'blob-key', empty_ok=True)
    self.__blob_key = blob_key

  def __str__(self):
    """Convert to string."""
    return self.__blob_key

  def __repr__(self):
    """Returns an eval()able string representation of this key.

    Returns a Python string of the form 'datastore_types.BlobKey(...)'
    that can be used to recreate this key.

    Returns:
      string
    """
    return 'datastore_types.%s(%r)' % (type(self).__name__, self.__blob_key)

  def __cmp__(self, other):
    # Do not want sub-class instances to be considered equal, so does
    # not use 'isinstance'.
    if type(other) is type(self):
      return cmp(str(self), str(other))
    elif isinstance(other, six_subset.string_types):
      return cmp(self.__blob_key, other)
    else:
      return NotImplemented

  def __hash__(self):
    return hash(self.__blob_key)

  def ToXml(self):
    return str(self)


# Maps Python types to their respective Onestore Meanings.
_PROPERTY_MEANINGS = {
  # NOTE(user,user): using meaning to indicate blobs and text is a
  # double-edged sword. if future semantic meanings are text or blobs, they'll
  # need to be special-cased in code. that's not a great design.
  Blob:              entity_pb.Property.BLOB,
  EmbeddedEntity:    entity_pb.Property.ENTITY_PROTO,
  ByteString:        entity_pb.Property.BYTESTRING,
  Text:              entity_pb.Property.TEXT,
  datetime.datetime: entity_pb.Property.GD_WHEN,
  datetime.date:     entity_pb.Property.GD_WHEN,
  datetime.time:     entity_pb.Property.GD_WHEN,
  _OverflowDateTime: entity_pb.Property.GD_WHEN,
  Category:          entity_pb.Property.ATOM_CATEGORY,
  Link:              entity_pb.Property.ATOM_LINK,
  Email:             entity_pb.Property.GD_EMAIL,
  GeoPt:             entity_pb.Property.GEORSS_POINT,
  IM:                entity_pb.Property.GD_IM,
  PhoneNumber:       entity_pb.Property.GD_PHONENUMBER,
  PostalAddress:     entity_pb.Property.GD_POSTALADDRESS,
  Rating:            entity_pb.Property.GD_RATING,
  BlobKey:           entity_pb.Property.BLOBKEY,
}

# Allowed Python types for properties.
_PROPERTY_TYPES = frozenset([
    Blob,
    EmbeddedEntity,
    ByteString,
    bool,
    Category,
    datetime.datetime,
    _OverflowDateTime,
    Email,
    float,
    GeoPt,
    IM,
    int,
    Key,
    Link,
    _PREFERRED_NUM_TYPE,
    PhoneNumber,
    PostalAddress,
    Rating,
    str,
    Text,
    type(None),
    six_subset.text_type,
    users.User,
    BlobKey,
])

# Python types and entity_pb.Property.Meanings for "raw" properties that
# aren't indexed. This is a tuple, instead of a set, so that it can be passed
# directly into isinstance().
_RAW_PROPERTY_TYPES = (Blob, Text, EmbeddedEntity)
_RAW_PROPERTY_MEANINGS = (entity_pb.Property.BLOB, entity_pb.Property.TEXT,
                          entity_pb.Property.ENTITY_PROTO)

# Helper functions for validating property values.
def ValidatePropertyInteger(name, value):
  """Raises an exception if the supplied integer is invalid.

  Args:
    name: Name of the property this is for.
    value: Integer value.

  Raises:
    OverflowError if the value does not fit within a signed int64.
  """
  if not (-0x8000000000000000 <= value <= 0x7fffffffffffffff):
    raise OverflowError('%d is out of bounds for int64' % value)


def ValidateStringLength(name, value, max_len):
  """Raises an exception if the supplied string is too long.

  Args:
    name: Name of the property this is for.
    value: String value.
    max_len: Maximum length the string may be.

  Raises:
    OverflowError if the value is larger than the maximum length.
  """
  # If we receive a unicode string, we assume it will be stored as utf-8.
  if isinstance(value, six_subset.text_type):
    value = value.encode('utf-8')

  if len(value) > max_len:
    raise datastore_errors.BadValueError(
      'Property %s is %d bytes long; it must be %d or less. '
      'Consider Text instead, which can store strings of any length.' %
      (name, len(value), max_len))


def ValidatePropertyString(name, value):
  """Validates the length of an indexed string property.

  Args:
    name: Name of the property this is for.
    value: String value.
  """
  ValidateStringLength(name, value, max_len=_MAX_STRING_LENGTH)


def ValidatePropertyLink(name, value):
  """Validates the length of an indexed Link property.

  Args:
    name: Name of the property this is for.
    value: String value.
  """
  ValidateStringLength(name, value, max_len=_MAX_LINK_PROPERTY_LENGTH)


def ValidatePropertyNothing(name, value):
  """No-op validation function.

  Args:
    name: Name of the property this is for.
    value: Not used.
  """
  pass


def ValidatePropertyKey(name, value):
  """Raises an exception if the supplied datastore.Key instance is invalid.

  Args:
    name: Name of the property this is for.
    value: A datastore.Key instance.

  Raises:
    datastore_errors.BadValueError if the value is invalid.
  """
  if not value.has_id_or_name():
    raise datastore_errors.BadValueError(
        'Incomplete key found for reference property %s.' % name)


# Maps property types to validation functions with the signature:
#
# Args:
#   name: Property name as a string.
#   value: The property value in the Python native type.
_VALIDATE_PROPERTY_VALUES = {
    Blob: ValidatePropertyNothing,
    EmbeddedEntity: ValidatePropertyNothing,
    ByteString: ValidatePropertyNothing,
    bool: ValidatePropertyNothing,
    Category: ValidatePropertyNothing,
    datetime.datetime: ValidatePropertyNothing,
    _OverflowDateTime: ValidatePropertyInteger,
    Email: ValidatePropertyNothing,
    float: ValidatePropertyNothing,
    GeoPt: ValidatePropertyNothing,
    IM: ValidatePropertyNothing,
    int: ValidatePropertyInteger,
    Key: ValidatePropertyKey,
    Link: ValidatePropertyNothing,
    _PREFERRED_NUM_TYPE: ValidatePropertyInteger,
    PhoneNumber: ValidatePropertyNothing,
    PostalAddress: ValidatePropertyNothing,
    Rating: ValidatePropertyInteger,
    str: ValidatePropertyNothing,
    Text: ValidatePropertyNothing,
    type(None): ValidatePropertyNothing,
    six_subset.text_type: ValidatePropertyNothing,
    users.User: ValidatePropertyNothing,
    BlobKey: ValidatePropertyNothing,
}

_PROPERTY_TYPE_TO_INDEX_VALUE_TYPE = {
    six_subset.string_types[0]: str,
    Blob: str,
    EmbeddedEntity: str,
    ByteString: str,
    bool: bool,
    Category: str,
    datetime.datetime: _PREFERRED_NUM_TYPE,
    datetime.date: _PREFERRED_NUM_TYPE,
    datetime.time: _PREFERRED_NUM_TYPE,
    _OverflowDateTime: _PREFERRED_NUM_TYPE,
    Email: str,
    float: float,
    GeoPt: GeoPt,
    IM: str,
    int: _PREFERRED_NUM_TYPE,
    Key: Key,
    Link: str,
    _PREFERRED_NUM_TYPE: _PREFERRED_NUM_TYPE,
    PhoneNumber: str,
    PostalAddress: str,
    Rating: _PREFERRED_NUM_TYPE,
    str: str,
    Text: str,
    type(None): type(None),
    six_subset.text_type: str,
    users.User: users.User,
    BlobKey: str,
}

# Ensure validation doesn't go out of skew with supported types.
assert set(_VALIDATE_PROPERTY_VALUES.keys()) == _PROPERTY_TYPES


def ValidateProperty(name, values, read_only=False):
  """Helper function for validating property values.

  Args:
    name: Name of the property this is for.
    value: Value for the property as a Python native type.
    read_only: deprecated

  Raises:
    BadPropertyError if the property name is invalid. BadValueError if the
    property did not validate correctly or the value was an empty list. Other
    exception types (like OverflowError) if the property value does not meet
    type-specific criteria.
  """
  ValidateString(name, 'property name', datastore_errors.BadPropertyError)

  values_type = type(values)

  # Tuples are not permitted.
  if values_type is tuple:
    raise datastore_errors.BadValueError(
        'May not use tuple property value; property %s is %s.' %
        (name, repr(values)))

  # Normalize to list.
  if values_type is not list:
    values = [values]

  # Check that all values are supported and valid. Treat 8-bit strings (i.e.,
  # str) and unicode strings as equivalent in the list of values.
  try:
    for v in values:
      prop_validator = _VALIDATE_PROPERTY_VALUES.get(v.__class__)
      if prop_validator is None:
        raise datastore_errors.BadValueError(
          'Unsupported type for property %s: %s' % (name, v.__class__))
      prop_validator(name, v)

  except (KeyError, ValueError, TypeError, IndexError, AttributeError) as msg:
    raise datastore_errors.BadValueError(
      'Error type checking values for property %s: %s' % (name, msg))


# For now this is just an alias for the normal property validation function.
# Applications may set it to a useless function if they want the extra
# performance gain of not checking for Datastore corruption on every read.
ValidateReadProperty = ValidateProperty


# Helper functions for packing entity_pb.PropertyValues.
def PackBlob(name, value, pbvalue):
  """Packs a Blob property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A Blob instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.set_stringvalue(value)


def PackString(name, value, pbvalue):
  """Packs a string-typed property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A string, unicode, or string-like value instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.set_stringvalue(six_subset.text_type(value).encode('utf-8'))


def PackDatetime(name, value, pbvalue):
  """Packs a datetime-typed property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A datetime.datetime instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.set_int64value(DatetimeToTimestamp(value))


def DatetimeToTimestamp(value):
  """Converts a datetime.datetime to microseconds since the epoch, as a float.
  Args:
    value: datetime.datetime

  Returns: value as a long
  """
  if value.tzinfo:
    # this is an "aware" datetime with an explicit timezone. convert to UTC.
    value = value.astimezone(UTC)
  return _PREFERRED_NUM_TYPE(
      calendar.timegm(value.timetuple()) * 1000000) + value.microsecond


def PackGeoPt(name, value, pbvalue):
  """Packs a GeoPt property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A GeoPt instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.mutable_pointvalue().set_x(value.lat)
  pbvalue.mutable_pointvalue().set_y(value.lon)


def PackUser(name, value, pbvalue):
  """Packs a User property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A users.User instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.mutable_uservalue().set_email(value.email().encode('utf-8'))
  pbvalue.mutable_uservalue().set_auth_domain(
      value.auth_domain().encode('utf-8'))
  pbvalue.mutable_uservalue().set_gaiaid(0)

  # Code in production currently ignores the obfuscated_gaiaid. As does the
  # datastore_filestub as of OCL 17091779. However, this would be useful
  # if we add a permission for datastore_types to trust the user-provided ID.
  if value.user_id() is not None:
    pbvalue.mutable_uservalue().set_obfuscated_gaiaid(
        value.user_id().encode('utf-8'))

  if value.federated_identity() is not None:
    pbvalue.mutable_uservalue().set_federated_identity(
        value.federated_identity().encode('utf-8'))

  if value.federated_provider() is not None:
    pbvalue.mutable_uservalue().set_federated_provider(
        value.federated_provider().encode('utf-8'))


def PackKey(name, value, pbvalue):
  """Packs a reference property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A Key instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  ref = value._Key__reference
  pbvalue.mutable_referencevalue().set_app(ref.app())
  SetNamespace(pbvalue.mutable_referencevalue(), ref.name_space())
  for elem in ref.path().element_list():
    pbvalue.mutable_referencevalue().add_pathelement().CopyFrom(elem)


def PackBool(name, value, pbvalue):
  """Packs a boolean property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A boolean instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.set_booleanvalue(value)


def PackInteger(name, value, pbvalue):
  """Packs an integer property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: An int or long instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.set_int64value(value)


def PackFloat(name, value, pbvalue):
  """Packs a float property into a entity_pb.PropertyValue.

  Args:
    name: The name of the property as a string.
    value: A float instance.
    pbvalue: The entity_pb.PropertyValue to pack this value into.
  """
  pbvalue.set_doublevalue(value)


# Maps property types to functions with the signature:
#
# Args:
#   value: The Python value to pack into the PropertyValue.
#   pbvalue: A mutable entity_pb.PropertyValue.
_PACK_PROPERTY_VALUES = {
    Blob: PackBlob,
    EmbeddedEntity: PackBlob,
    ByteString: PackBlob,
    bool: PackBool,
    Category: PackString,
    datetime.datetime: PackDatetime,
    _OverflowDateTime: PackInteger,
    Email: PackString,
    float: PackFloat,
    GeoPt: PackGeoPt,
    IM: PackString,
    int: PackInteger,
    Key: PackKey,
    Link: PackString,
    _PREFERRED_NUM_TYPE: PackInteger,
    PhoneNumber: PackString,
    PostalAddress: PackString,
    Rating: PackInteger,
    str: PackString,
    Text: PackString,
    type(None): lambda name, value, pbvalue: None,
    six_subset.text_type: PackString,
    users.User: PackUser,
    BlobKey: PackString,
}

# Ensure packing doesn't go out of skew with supported types.
assert set(_PACK_PROPERTY_VALUES.keys()) == _PROPERTY_TYPES


def ToPropertyPb(name, values):
  """Creates type-specific entity_pb.PropertyValues.

  Determines the type and meaning of the PropertyValue based on the Python
  type of the input value(s).

  NOTE: This function does not validate anything!

  Args:
    name: string or unicode; the property name
    values: The values for this property, either a single one or a list of them.
      All values must be a supported type. Lists of values must all be of the
      same type.

  Returns:
    A list of entity_pb.Property instances.
  """
  encoded_name = name.encode('utf-8')

  values_type = type(values)
  if values_type is list and len(values) == 0:
    # Empty list
    pb = entity_pb.Property()
    pb.set_meaning(entity_pb.Property.EMPTY_LIST)
    pb.set_name(encoded_name)
    pb.set_multiple(False)
    pb.mutable_value()
    return pb
  elif values_type is list:
    multiple = True
  else:
    multiple = False
    values = [values]

  pbs = []
  for v in values:
    pb = entity_pb.Property()
    pb.set_name(encoded_name)
    pb.set_multiple(multiple)

    meaning = _PROPERTY_MEANINGS.get(v.__class__)
    if meaning is not None:
      pb.set_meaning(meaning)

    if hasattr(v, 'meaning_uri') and v.meaning_uri:
      pb.set_meaning_uri(v.meaning_uri)

    pack_prop = _PACK_PROPERTY_VALUES[v.__class__]
    pbvalue = pack_prop(name, v, pb.mutable_value())
    pbs.append(pb)

  if multiple:
    return pbs
  else:
    return pbs[0]


def FromReferenceProperty(value):
  """Converts a reference PropertyValue to a Key.

  Args:
    value: entity_pb.PropertyValue

  Returns:
    Key

  Raises:
    BadValueError if the value is not a PropertyValue.
  """
  assert isinstance(value, entity_pb.PropertyValue)
  assert value.has_referencevalue()
  ref = value.referencevalue()

  key = Key()
  key_ref = key._Key__reference
  key_ref.set_app(ref.app())
  SetNamespace(key_ref, ref.name_space())

  for pathelem in ref.pathelement_list():
    key_ref.mutable_path().add_element().CopyFrom(pathelem)

  return key


# Maps onestore meanings and property PB types to lambda functions that create
# native python values. the value field is passed into the lambda function.
#
# If it's a string property, the value is UTF-8 decoded and converted to a
# unicode string beforehand. If it's a point, a 2-tuple is passed in. If it's
# a user, the email is passed in. If it's a reference, the entire
# ReferenceProperty is passed in.
_PROPERTY_CONVERSIONS = {
  entity_pb.Property.GD_WHEN:           _When,
  entity_pb.Property.ATOM_CATEGORY:     Category,
  entity_pb.Property.ATOM_LINK:         Link,
  entity_pb.Property.GD_EMAIL:          Email,
  entity_pb.Property.GD_IM:             IM,
  entity_pb.Property.GD_PHONENUMBER:    PhoneNumber,
  entity_pb.Property.GD_POSTALADDRESS:  PostalAddress,
  entity_pb.Property.GD_RATING:         Rating,
  entity_pb.Property.BLOB:              Blob,
  entity_pb.Property.ENTITY_PROTO:      EmbeddedEntity,
  entity_pb.Property.BYTESTRING:        ByteString,
  entity_pb.Property.TEXT:              Text,
  entity_pb.Property.BLOBKEY:           BlobKey,
  entity_pb.Property.EMPTY_LIST:        _EmptyList,
}


_NON_UTF8_MEANINGS = frozenset((entity_pb.Property.BLOB,
                                entity_pb.Property.ENTITY_PROTO,
                                entity_pb.Property.BYTESTRING,
                                entity_pb.Property.INDEX_VALUE))


def FromPropertyPb(pb):
  """Converts a property PB to a python value.

  Args:
    pb: entity_pb.Property

  Returns:
    # return type is determined by the type of the argument
    string, int, bool, double, users.User, or one of the atom or gd types
  """
  # This method is performance critical. Some key optimizations:
  # 1. use unicode(s, 'utf-8') rather than s.decode('utf-8') to avoid a codec
  #    registry lookup on every conversion (see http://b/5588971).
  pbval = pb.value()
  meaning = pb.meaning()

  if pbval.has_stringvalue():
    value = pbval.stringvalue()
    if not pb.has_meaning() or meaning not in _NON_UTF8_MEANINGS:
      value = six_subset.text_type(value, 'utf-8')
  elif pbval.has_int64value():
    # convert for consistency. the user could have set the field to either an
    # int or a long. (if it's coming from the datastore, it's always a long.)
    value = _PREFERRED_NUM_TYPE(pbval.int64value())
  elif pbval.has_booleanvalue():
    # the booleanvalue field is an int32, so booleanvalue() returns an int,
    # hence the conversion.
    value = bool(pbval.booleanvalue())
  elif pbval.has_doublevalue():
    value = pbval.doublevalue()
  elif pbval.has_referencevalue():
    value = FromReferenceProperty(pbval)
  elif pbval.has_pointvalue():
    value = GeoPt(pbval.pointvalue().x(), pbval.pointvalue().y())
  elif pbval.has_uservalue():
    email = six_subset.text_type(pbval.uservalue().email(), 'utf-8')
    auth_domain = six_subset.text_type(pbval.uservalue().auth_domain(), 'utf-8')
    obfuscated_gaiaid = pbval.uservalue().obfuscated_gaiaid().decode('utf-8')
    obfuscated_gaiaid = six_subset.text_type(
        pbval.uservalue().obfuscated_gaiaid(), 'utf-8')

    federated_identity = None
    if pbval.uservalue().has_federated_identity():
      federated_identity = six_subset.text_type(
          pbval.uservalue().federated_identity(), 'utf-8')

    # For outbound delivery we will not be as strict as inbound, allowing users
    # to fetch user properties which may otherwise be considered as corrupt.
    value = users.User(email=email,
                       _auth_domain=auth_domain,
                       _user_id=obfuscated_gaiaid,
                       federated_identity=federated_identity,
                       _strict_mode=False)
  else:
    value = None

  try:
    if pb.has_meaning() and meaning in _PROPERTY_CONVERSIONS:
      conversion = _PROPERTY_CONVERSIONS[meaning]
      value = conversion(value)
      if (meaning == entity_pb.Property.BLOB
          and pb.has_meaning_uri()):
        value.meaning_uri = pb.meaning_uri()
  except (KeyError, ValueError, IndexError, TypeError, AttributeError) as msg:
    raise datastore_errors.BadValueError(
      'Error converting pb: %s\nException was: %s' % (pb, msg))

  return value


def RestoreFromIndexValue(index_value, data_type):
  """Restores a index value to the correct datastore type.

  Projection queries return property values direclty from a datastore index.
  These values are the native datastore values, one of str, bool, long, float,
  GeoPt, Key or User. This function restores the original value when the
  original type is known.

  This function returns the value type returned when decoding a normal entity,
  not necessarily of type data_type. For example, data_type=int returns a
  long instance.

  Args:
    index_value: The value returned by FromPropertyPb for the projected
      property.
    data_type: The type of the value originally given to ToPropertyPb

  Returns:
    The restored property value.

  Raises:
    datastore_errors.BadValueError if the value cannot be restored.
  """
  raw_type = _PROPERTY_TYPE_TO_INDEX_VALUE_TYPE.get(data_type)
  if raw_type is None:
    raise datastore_errors.BadValueError(
        'Unsupported data type (%r)' % data_type)

  if index_value is None:
    return index_value

  # NOTE(user): The dev server returns whatever the user passed in, so
  # we cannot rely on the type being exactly one of the index value types.
  if not isinstance(index_value, raw_type):
    raise datastore_errors.BadValueError(
        'Unsupported converstion. Expected %r got %r' %
        (type(index_value), raw_type))

  meaning = _PROPERTY_MEANINGS.get(data_type)

  # Handling utf-8 decoding explicitly
  if isinstance(index_value, str) and meaning not in _NON_UTF8_MEANINGS:
    index_value = six_subset.text_type(index_value, 'utf-8')

  # Performing additional conversions
  conv = _PROPERTY_CONVERSIONS.get(meaning)
  if not conv:
    return index_value  # No converstion needed.

  try:
    value = conv(index_value)
  except (KeyError, ValueError, IndexError, TypeError, AttributeError) as msg:
    raise datastore_errors.BadValueError(
      'Error converting value: %r\nException was: %s' % (index_value, msg))
  return value


def PropertyTypeName(value):
  """Returns the name of the type of the given property value, as a string.

  Raises BadValueError if the value is not a valid property type.

  Args:
    value: any valid property value

  Returns:
    string
  """
  if value.__class__ in _PROPERTY_MEANINGS:
    meaning = _PROPERTY_MEANINGS[value.__class__]
    name = entity_pb.Property._Meaning_NAMES[meaning]
    return name.lower().replace('_', ':')
  elif isinstance(value, basestring):
    return 'string'
  elif isinstance(value, users.User):
    return 'user'
  elif isinstance(value, _PREFERRED_NUM_TYPE):
    return 'int'
  elif value is None:
    return 'null'
  else:
    return typename(value).lower()

# Mapping from property type names to type classes.
_PROPERTY_TYPE_STRINGS = {
    'string': six_subset.text_type,
    'bool': bool,
    'int': _PREFERRED_NUM_TYPE,
    'null': type(None),
    'float': float,
    'key': Key,
    'blob': Blob,
    'entity:proto': EmbeddedEntity,
    'bytestring': ByteString,
    'text': Text,
    'user': users.User,
    'atom:category': Category,
    'atom:link': Link,
    'gd:email': Email,
    'gd:when': datetime.datetime,
    'georss:point': GeoPt,
    'gd:im': IM,
    'gd:phonenumber': PhoneNumber,
    'gd:postaladdress': PostalAddress,
    'gd:rating': Rating,
    'blobkey': BlobKey,
}


def FromPropertyTypeName(type_name):
  """Returns the python type given a type name.

  Args:
    type_name: A string representation of a datastore type name.

  Returns:
    A python type.
  """
  return _PROPERTY_TYPE_STRINGS[type_name]


def PropertyValueFromString(type_,
                            value_string,
                            _auth_domain=None):
  """Returns an instance of a property value given a type and string value.

  The reverse of this method is just str() and type() of the python value.

  Note that this does *not* support non-UTC offsets in ISO 8601-formatted
  datetime strings, e.g. the -08:00 suffix in '2002-12-25 00:00:00-08:00'.
  It only supports -00:00 and +00:00 suffixes, which are UTC.

  Args:
    type_: A python class.
    value_string: A string representation of the value of the property.

  Returns:
    An instance of 'type'.

  Raises:
    ValueError if type_ is datetime and value_string has a timezone offset.
  """
  if type_ == datetime.datetime:
    value_string = value_string.strip()
    # check for timezone offset
    if value_string[-6] in ('+', '-'):
      if value_string[-5:] == '00:00':
        value_string = value_string[:-6]
      else:
        # TODO(user,user): support time zone offsets
        raise ValueError('Non-UTC offsets in datetimes are not supported.')

    # extract microseconds
    split = value_string.split('.')
    iso_date = split[0]
    microseconds = 0
    if len(split) > 1:
      microseconds = int(split[1])

    # This is the default iso format. str() of a datetime object will return a
    # string in this format.
    time_struct = time.strptime(iso_date, '%Y-%m-%d %H:%M:%S')[0:6]
    value = datetime.datetime(*(time_struct + (microseconds,)))
    return value
  elif type_ == Rating:
    # TODO(user): Remove special case for Rating.
    return Rating(int(value_string))
  elif type_ == bool:
    return value_string == 'True'
  elif type_ == users.User:
    return users.User(value_string, _auth_domain)
  elif type_ == type(None):
    return None
  return type_(value_string)


def ReferenceToKeyValue(key, id_resolver=None):
  """Converts a key into a comparable hashable "key" value.

  Args:
    key: The entity_pb.Reference or googledatastore.Key from which to construct
        the key value.
    id_resolver: An optional datastore_pbs.IdResolver. Only necessary for
        googledatastore.Key values.
  Returns:
    A comparable and hashable representation of the given key that is
    compatible with one derived from a key property value.
  """
  if (datastore_pbs._CLOUD_DATASTORE_ENABLED
      and isinstance(key, googledatastore.Key)):
    v1_key = key
    key = entity_pb.Reference()
    datastore_pbs.get_entity_converter(id_resolver).v1_to_v3_reference(v1_key,
                                                                       key)
  elif isinstance(key, entity_v4_pb.Key):
    v4_key = key
    key = entity_pb.Reference()
    datastore_pbs.get_entity_converter().v4_to_v3_reference(v4_key, key)

  if isinstance(key, entity_pb.Reference):
    element_list = key.path().element_list()
  elif isinstance(key, entity_pb.PropertyValue_ReferenceValue):
    element_list = key.pathelement_list()
  else:
    raise datastore_errors.BadArgumentError(
        "key arg expected to be entity_pb.Reference or googledatastore.Key (%r)"
        % (key,))

  result = [entity_pb.PropertyValue.kReferenceValueGroup,
            key.app(), key.name_space()]
  for element in element_list:
    result.append(element.type())
    if element.has_name():
      result.append(element.name())
    else:
      result.append(element.id())
  return tuple(result)


def PropertyValueToKeyValue(prop_value):
  """Converts a entity_pb.PropertyValue into a comparable hashable "key" value.

  The values produces by this function mimic the native ording of the datastore
  and uniquely identify the given PropertyValue.

  Args:
    prop_value: The entity_pb.PropertyValue from which to construct the
      key value.

  Returns:
    A comparable and hashable representation of the given property value.
  """
  if not isinstance(prop_value, entity_pb.PropertyValue):
    raise datastore_errors.BadArgumentError(
        'prop_value arg expected to be entity_pb.PropertyValue (%r)' %
        (prop_value,))

  # NOTE(user): These values must be constructed in a way that mimics the
  # order of the datastore which orders protos first by tag id then value.
  if prop_value.has_stringvalue():
    return (entity_pb.PropertyValue.kstringValue, prop_value.stringvalue())
  if prop_value.has_int64value():
    return (entity_pb.PropertyValue.kint64Value, prop_value.int64value())
  if prop_value.has_booleanvalue():
    return (entity_pb.PropertyValue.kbooleanValue, prop_value.booleanvalue())
  if prop_value.has_doublevalue():
    # The datastore makes -0.0 < 0.0
    encoder = sortable_pb_encoder.Encoder()
    encoder.putDouble(prop_value.doublevalue())
    return (entity_pb.PropertyValue.kdoubleValue, tuple(encoder.buf))
  if prop_value.has_pointvalue():
    return (entity_pb.PropertyValue.kPointValueGroup,
            prop_value.pointvalue().x(), prop_value.pointvalue().y())
  if prop_value.has_referencevalue():
    return ReferenceToKeyValue(prop_value.referencevalue())
  if prop_value.has_uservalue():
    result = []
    uservalue = prop_value.uservalue()
    if uservalue.has_email():
      result.append((entity_pb.PropertyValue.kUserValueemail,
                     uservalue.email()))
    if uservalue.has_auth_domain():
      result.append((entity_pb.PropertyValue.kUserValueauth_domain,
                     uservalue.auth_domain()))
    if uservalue.has_nickname():
      result.append((entity_pb.PropertyValue.kUserValuenickname,
                     uservalue.nickname()))
    if uservalue.has_gaiaid():
      result.append((entity_pb.PropertyValue.kUserValuegaiaid,
                     uservalue.gaiaid()))
    if uservalue.has_obfuscated_gaiaid():
      result.append((entity_pb.PropertyValue.kUserValueobfuscated_gaiaid,
                     uservalue.obfuscated_gaiaid()))
    if uservalue.has_federated_identity():
      result.append((entity_pb.PropertyValue.kUserValuefederated_identity,
                     uservalue.federated_identity()))
    if uservalue.has_federated_provider():
      result.append((entity_pb.PropertyValue.kUserValuefederated_provider,
                     uservalue.federated_provider()))
    result.sort()
    return (entity_pb.PropertyValue.kUserValueGroup, tuple(result))
  return ()  # null comes before everything


def GetPropertyValueTag(value_pb):
  """Returns the tag constant associated with the given entity_pb.PropertyValue.
  """
  if value_pb.has_booleanvalue():
    return entity_pb.PropertyValue.kbooleanValue
  elif value_pb.has_doublevalue():
    return entity_pb.PropertyValue.kdoubleValue
  elif value_pb.has_int64value():
    return entity_pb.PropertyValue.kint64Value
  elif value_pb.has_pointvalue():
    return entity_pb.PropertyValue.kPointValueGroup
  elif value_pb.has_referencevalue():
    return entity_pb.PropertyValue.kReferenceValueGroup
  elif value_pb.has_stringvalue():
    return entity_pb.PropertyValue.kstringValue
  elif value_pb.has_uservalue():
    return entity_pb.PropertyValue.kUserValueGroup
  else:
    return 0
