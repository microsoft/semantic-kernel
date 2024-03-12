#
# Copyright 2010 Google LLC. All Rights Reserved.
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

"""Asynchronous datastore API.

This is designed to be the lowest-level API to be used by all Python
datastore client libraries.
"""

# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

from __future__ import absolute_import
from __future__ import unicode_literals


# This defines the names that will be seen by "from ... import *".
__all__ = ['AbstractAdapter',
           'BaseConfiguration',
           'BaseConnection',
           'ConfigOption',
           'Configuration',
           'Connection',
           'IdentityAdapter',
           'MultiRpc',
           'TransactionalConnection',
           'TransactionMode',
           'TransactionOptions',
          ]

# TODO(user): Consider implementing __eq__ for all immutable classes.

# Python imports.
import collections
import copy
import functools
import logging
import os

from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3 import entity_pb
from googlecloudsdk.third_party.appengine._internal import six_subset

# App Engine imports.
from googlecloudsdk.third_party.appengine.api import api_base_pb
from googlecloudsdk.third_party.appengine.api import apiproxy_rpc
from googlecloudsdk.third_party.appengine.api import apiproxy_stub_map
# TODO(user): Move the stuff we need from _errors and and _types here?
from googlecloudsdk.third_party.appengine.api import datastore_errors
from googlecloudsdk.third_party.appengine.api import datastore_types
from googlecloudsdk.third_party.appengine.datastore import datastore_pb
from googlecloudsdk.third_party.appengine.datastore import datastore_pbs
from googlecloudsdk.third_party.appengine.runtime import apiproxy_errors

_CLOUD_DATASTORE_ENABLED = datastore_pbs._CLOUD_DATASTORE_ENABLED  # pylint: disable=protected-access
if _CLOUD_DATASTORE_ENABLED:
  from googlecloudsdk.third_party.appengine.datastore.datastore_pbs import googledatastore

# Constants and globals.

# The maximum number of ids that can be allocated at a time
_MAX_ID_BATCH_SIZE = 1000 * 1000 * 1000

# API versions (also the name of the corresponding service).
_DATASTORE_V3 = 'datastore_v3'
_CLOUD_DATASTORE_V1 = 'cloud_datastore_v1'


# TODO(user): Move this to some kind of utility module.
def _positional(max_pos_args):
  """A decorator to declare that only the first N arguments may be positional.

  Note that for methods, n includes 'self'.
  """
  def positional_decorator(wrapped):
    @functools.wraps(wrapped)
    def positional_wrapper(*args, **kwds):
      if len(args) > max_pos_args:
        plural_s = ''
        if max_pos_args != 1:
          plural_s = 's'
        raise TypeError(
          '%s() takes at most %d positional argument%s (%d given)' %
          (wrapped.__name__, max_pos_args, plural_s, len(args)))
      return wrapped(*args, **kwds)
    return positional_wrapper
  return positional_decorator


def _GetDatastoreType(app=None):
  """Tries to get the datastore type for the given app.

  This function is only guaranteed to return something other than
  UNKNOWN_DATASTORE when running in production and querying the current app.
  """
  current_app = datastore_types.ResolveAppId(None)
  if app not in (current_app, None):
    return BaseConnection.UNKNOWN_DATASTORE
  return BaseConnection.HIGH_REPLICATION_DATASTORE


class AbstractAdapter(object):
  """Abstract interface between protobufs and user-level classes.

  This class defines conversions between the protobuf classes defined
  in entity_pb.py on the one hand, and the corresponding user-level
  classes (which are defined by higher-level API libraries such as
  datastore.py or db.py) on the other hand.

  The premise is that the code in this module is agnostic about the
  user-level classes used to represent keys and entities, while at the
  same time provinging APIs that accept or return such user-level
  classes.

  Higher-level libraries must subclass this abstract class and pass an
  instance of the subclass to the Connection they want to use.

  These methods may raise datastore_errors.Error for bad inputs.
  """
  # Defaults in case subclasses don't call init.
  _entity_converter = datastore_pbs.get_entity_converter()
  _query_converter = datastore_pbs._QueryConverter(_entity_converter)

  def __init__(self, id_resolver=None):
    if id_resolver:
      self._entity_converter = datastore_pbs.get_entity_converter(
          id_resolver)
      self._query_converter = datastore_pbs._QueryConverter(
          self._entity_converter)

  def get_entity_converter(self):
    return self._entity_converter

  def get_query_converter(self):
    return self._query_converter

  def pb_to_key(self, pb):
    """Turn an entity_pb.Reference into a user-level key."""
    raise NotImplementedError

  def pb_v1_to_key(self, pb):
    """Turn an googledatastore.Key into a user-level key."""
    v3_ref = entity_pb.Reference()
    self._entity_converter.v1_to_v3_reference(pb, v3_ref)
    return self.pb_to_key(v3_ref)

  def pb_to_entity(self, pb):
    """Turn an entity_pb.EntityProto into a user-level entity."""
    raise NotImplementedError

  def pb_v1_to_entity(self, pb, is_projection):
    """Turn an googledatastore.Entity into a user-level entity."""
    v3_entity = entity_pb.EntityProto()
    self._entity_converter.v1_to_v3_entity(pb, v3_entity, is_projection)
    return self.pb_to_entity(v3_entity)

  def pb_v1_to_query_result(self, pb, query_options):
    """Turn an googledatastore.Entity into a user-level query result."""
    if query_options.keys_only:
      return self.pb_v1_to_key(pb.key)
    else:
      return self.pb_v1_to_entity(pb, bool(query_options.projection))

  def pb_to_index(self, pb):
    """Turn an entity_pb.CompositeIndex into a user-level Index
    representation."""
    raise NotImplementedError

  def pb_to_query_result(self, pb, query_options):
    """Turn an entity_pb.EntityProto into a user-level query result."""
    if query_options.keys_only:
      return self.pb_to_key(pb.key())
    else:
      return self.pb_to_entity(pb)

  def key_to_pb(self, key):
    """Turn a user-level key into an entity_pb.Reference."""
    raise NotImplementedError

  def key_to_pb_v1(self, key):
    """Turn a user-level key into an googledatastore.Key."""
    v3_ref = self.key_to_pb(key)
    v1_key = googledatastore.Key()
    self._entity_converter.v3_to_v1_key(v3_ref, v1_key)
    return v1_key

  def entity_to_pb(self, entity):
    """Turn a user-level entity into an entity_pb.EntityProto."""
    raise NotImplementedError

  def entity_to_pb_v1(self, entity):
    """Turn a user-level entity into an googledatastore.Key."""
    v3_entity = self.entity_to_pb(entity)
    v1_entity = googledatastore.Entity()
    self._entity_converter.v3_to_v1_entity(v3_entity, v1_entity)
    return v1_entity

  def new_key_pb(self):
    """Create a new, empty entity_pb.Reference."""
    return entity_pb.Reference()

  def new_entity_pb(self):
    """Create a new, empty entity_pb.EntityProto."""
    return entity_pb.EntityProto()


class IdentityAdapter(AbstractAdapter):
  """A concrete adapter that implements the identity mapping.

  This is used as the default when a Connection is created without
  specifying an adapter; that's primarily for testing.
  """

  def __init__(self, id_resolver=None):
    super(IdentityAdapter, self).__init__(id_resolver)

  def pb_to_key(self, pb):
    return pb

  def pb_to_entity(self, pb):
    return pb

  def key_to_pb(self, key):
    return key

  def entity_to_pb(self, entity):
    return entity

  def pb_to_index(self, pb):
    return pb


class ConfigOption(object):
  """A descriptor for a Configuration option.

  This class is used to create a configuration option on a class that inherits
  from BaseConfiguration. A validator function decorated with this class will
  be converted to a read-only descriptor and BaseConfiguration will implement
  constructor and merging logic for that configuration option. A validator
  function takes a single non-None value to validate and either throws
  an exception or returns that value (or an equivalent value). A validator is
  called once at construction time, but only if a non-None value for the
  configuration option is specified the constructor's keyword arguments.
  """

  def __init__(self, validator):
    self.validator = validator

  def __get__(self, obj, objtype):
    if obj is None:   # Descriptor called on class.
      return self
    return obj._values.get(self.validator.__name__, None)

  def __set__(self, obj, value):
    raise AttributeError('Configuration options are immutable (%s)' %
                         (self.validator.__name__,))

  def __call__(self, *args):
    """Gets the first non-None value for this option from the given args.

    Args:
      *arg: Any number of configuration objects or None values.

    Returns:
      The first value for this ConfigOption found in the given configuration
    objects or None.

    Raises:
      datastore_errors.BadArgumentError if a given in object is not a
    configuration object.
    """
    name = self.validator.__name__
    for config in args:
      # apiproxy_stub_map.UserRPC is included for legacy support
      if isinstance(config, (type(None), apiproxy_stub_map.UserRPC)):
        pass
      elif not isinstance(config, BaseConfiguration):
        raise datastore_errors.BadArgumentError(
            'invalid config argument (%r)' % (config,))
      elif name in config._values and self is config._options[name]:
        return config._values[name]
    return None


class _ConfigurationMetaClass(type):
  """The metaclass for all Configuration types.

  This class is needed to store a class specific list of all ConfigOptions in
  cls._options, and insert a __slots__ variable into the class dict before the
  class is created to impose immutability.
  """

  def __new__(metaclass, classname, bases, classDict):
    if classname == '_MergedConfiguration':
      # Special-cased, so it can be a subclass of BaseConfiguration
      return type.__new__(metaclass, classname, bases, classDict)

    # Use 'object in bases' as a crutch to distinguish BaseConfiguration
    # from its subclasses.
    if object in bases:
      classDict['__slots__'] = ['_values']  # making class immutable
    else:
      classDict['__slots__'] = []  # it already has a _values slot
    cls = type.__new__(metaclass, classname, bases, classDict)
    if object not in bases:
      options = {}
      for c in reversed(cls.__mro__):
        if '_options' in c.__dict__:
          options.update(c.__dict__['_options'])
      cls._options = options  # Each cls gets its own copy of fields.
      for option, value in cls.__dict__.items():
        if isinstance(value, ConfigOption):
          if option in cls._options:  # pylint: disable=protected-access
            raise TypeError('%s cannot be overridden (%s)' %
                            (option, cls.__name__))
          cls._options[option] = value
          value._cls = cls
    return cls

  # TODO(user): define __instancecheck__ once we have a released 2.7 environment


class BaseConfiguration(six_subset.with_metaclass(_ConfigurationMetaClass,
                                                  object)):
  """A base class for a configuration object.

  Subclasses should provide validation functions for every configuration option
  they accept. Any public function decorated with ConfigOption is assumed to be
  a validation function for an option of the same name. All validation functions
  take a single non-None value to validate and must throw an exception or return
  the value to store.

  This class forces subclasses to be immutable and exposes a read-only
  property for every accepted configuration option. Configuration options set by
  passing keyword arguments to the constructor. The constructor and merge
  function are designed to avoid creating redundant copies and may return
  the configuration objects passed to them if appropriate.

  Setting an option to None is the same as not specifying the option except in
  the case where the 'config' argument is given. In this case the value on
  'config' of the same name is ignored. Options that are not specified will
  return 'None' when accessed.
  """
  _options = {}  # Maps option name to ConfigOption objects

  def __new__(cls, config=None, **kwargs):
    """Immutable constructor.

    If 'config' is non-None all configuration options will default to the value
    it contains unless the configuration option is explicitly set to 'None' in
    the keyword arguments. If 'config' is None then all configuration options
    default to None.

    Args:
      config: Optional base configuration providing default values for
        parameters not specified in the keyword arguments.
      **kwargs: Configuration options to store on this object.

    Returns:
      Either a new Configuration object or (if it would be equivalent)
      the config argument unchanged, but never None.
    """
    if config is None:
      pass
    elif isinstance(config, BaseConfiguration):
      if cls is config.__class__ and config.__is_stronger(**kwargs):
        # Shortcut: return the config argument unchanged.
        return config

      for key, value in config._values.items():  # pylint: disable=protected-access
        # Only grab options we know about
        if issubclass(cls, config._options[key]._cls):
          kwargs.setdefault(key, value)
    else:
      raise datastore_errors.BadArgumentError(
          'config argument should be Configuration (%r)' % (config,))

    obj = super(BaseConfiguration, cls).__new__(cls)
    obj._values = {}
    for key, value in kwargs.items():
      if value is not None:
        try:
          config_option = obj._options[key]
        except KeyError as err:
          raise TypeError('Unknown configuration option (%s)' % err)
        value = config_option.validator(value)
        if value is not None:
          obj._values[key] = value
    return obj

  def __eq__(self, other):
    if self is other:
      return True
    if not isinstance(other, BaseConfiguration):
      return NotImplemented
    return self._options == other._options and self._values == other._values

  def __ne__(self, other):
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return equal
    return not equal

  def __hash__(self):
    return (hash(frozenset(self._values.items())) ^
            hash(frozenset(self._options.items())))

  def __repr__(self):
    args = []
    for key_value in sorted(self._values.items()):
      args.append('%s=%r' % key_value)
    return '%s(%s)' % (self.__class__.__name__, ', '.join(args))

  def __is_stronger(self, **kwargs):
    """Internal helper to ask whether a configuration is stronger than another.

    A configuration is stronger when it contains every name/value pair in
    kwargs.

    Example: a configuration with:
      (deadline=5, on_configuration=None, read_policy=EVENTUAL_CONSISTENCY)
    is stronger than:
      (deadline=5, on_configuration=None)
    but not stronger than:
      (deadline=5, on_configuration=None, read_policy=None)
    or
      (deadline=10, on_configuration=None, read_policy=None).

    More formally:
      - Any value is stronger than an unset value;
      - Any value is stronger than itself.

    Returns:
      True if each of the self attributes is stronger than the
    corresponding argument.
    """
    for key, value in kwargs.items():
      if key not in self._values or value != self._values[key]:
        return False
    return True

  @classmethod
  def is_configuration(cls, obj):
    """True if configuration obj handles all options of this class.

    Use this method rather than isinstance(obj, cls) to test if a
    configuration object handles the options of cls (is_configuration
    is handled specially for results of merge which may handle the options
    of unrelated configuration classes).

    Args:
      obj: the object to test.
    """
    return isinstance(obj, BaseConfiguration) and obj._is_configuration(cls)

  def _is_configuration(self, cls):
    return isinstance(self, cls)

  def merge(self, config):
    """Merge two configurations.

    The configuration given as an argument (if any) takes priority;
    defaults are filled in from the current configuration.

    Args:
      config: Configuration providing overrides, or None (but cannot
        be omitted).

    Returns:
      Either a new configuration object or (if it would be equivalent)
      self or the config argument unchanged, but never None.

    Raises:
      BadArgumentError if self or config are of configurations classes
      with conflicting options (i.e. the same option name defined in
      two different configuration classes).
    """
    if config is None or config is self:
      # Nothing to do.
      return self

    # Optimizations to avoid _MergedConfiguration when possible,
    # for backwards compatibility of code that uses isinstance.
    if not (isinstance(config, _MergedConfiguration) or
            isinstance(self, _MergedConfiguration)):

      # Return config if for every value self has, config has a value
      # that would override it.
      if isinstance(config, self.__class__):
        for key in self._values:
          if key not in config._values:
            break
        else:
          return config
      if isinstance(self, config.__class__):
        if  self.__is_stronger(**config._values):
          return self

      # Return an instance of a configuration class if possible
      def _quick_merge(obj):
        obj._values = self._values.copy()
        obj._values.update(config._values)
        return obj

      if isinstance(config, self.__class__):
        return _quick_merge(type(config)())
      if isinstance(self, config.__class__):
        return _quick_merge(type(self)())

    # Helper class merges configurations with config taking priority.
    return _MergedConfiguration(config, self)

  def __getstate__(self):
    return {'_values': self._values}

  def __setstate__(self, state):
    # Re-validate values in case validation changed as logic elsewhere assumes
    # validation passed.
    obj = self.__class__(**state['_values'])
    self._values = obj._values


class _MergedConfiguration(BaseConfiguration):
  """Helper class to handle merges of configurations.

  Instances of _MergedConfiguration are in some sense "subclasses" of the
  argument configurations, i.e.:
  - they handle exactly the configuration options of the argument configurations
  - the value of these options is taken in priority order from the arguments
  - isinstance is true on this configuration if it is true on any of the
    argument configurations
  This class raises an exception if two argument configurations have an option
  with the same name but coming from a different configuration class.
  """
  __slots__ = ['_values', '_configs', '_options', '_classes']

  def __new__(cls, *configs):
    obj = super(BaseConfiguration, cls).__new__(cls)
    obj._configs = configs

    # Find out which options we handle and raise an error on name clashes
    obj._options = {}
    for config in configs:
      for name, option in config._options.items():  # pylint: disable=protected-access
        if name in obj._options:
          if option is not obj._options[name]:
            error = ("merge conflict on '%s' from '%s' and '%s'" %
                     (name, option._cls.__name__,
                      obj._options[name]._cls.__name__))
            raise datastore_errors.BadArgumentError(error)
        obj._options[name] = option

    obj._values = {}
    for config in reversed(configs):
      for name, value in config._values.items():  # pylint: disable=protected-access
        obj._values[name] = value

    return obj

  def __repr__(self):
    return '%s%r' % (self.__class__.__name__, tuple(self._configs))

  def _is_configuration(self, cls):
    for config in self._configs:
      if config._is_configuration(cls):
        return True
    return False

  def __getattr__(self, name):
    if name in self._options:
      if name in self._values:
        return self._values[name]
      else:
        return None
    raise AttributeError("Configuration has no attribute '%s'" % (name,))

  def __getstate__(self):
    return {'_configs': self._configs}

  def __setstate__(self, state):
    # Using constructor to build the correct state.
    obj = _MergedConfiguration(*state['_configs'])
    self._values = obj._values
    self._configs = obj._configs
    self._options = obj._options


class Configuration(BaseConfiguration):
  """Configuration parameters for datastore RPCs.

  This class reserves the right to define configuration options of any name
  except those that start with 'user_'. External subclasses should only define
  function or variables with names that start with in 'user_'.

  The options defined on this class include generic RPC parameters (deadline)
  but also datastore-specific parameters (on_completion and read_policy).

  Options are set by passing keyword arguments to the constructor corresponding
  to the configuration options defined below.
  """

  # Flags to determine read policy and related constants.
  STRONG_CONSISTENCY = 0
  """A read consistency that will return up to date results."""

  EVENTUAL_CONSISTENCY = 1
  """A read consistency that allows requests to return possibly stale results.

  This read_policy tends to be faster and less prone to unavailability/timeouts.
  May return transactionally inconsistent results in rare cases.
  """

  APPLY_ALL_JOBS_CONSISTENCY = 2  # forces READ_CURRENT for 1.0.1 shards
  """A read consistency that aggressively tries to find write jobs to apply.

  Use of this read policy is strongly discouraged.

  This read_policy tends to be more costly and is only useful in a few specific
  cases. It is equivalent to splitting a request by entity group and wrapping
  each batch in a separate transaction. Cannot be used with non-ancestor
  queries.
  """


  ALL_READ_POLICIES = frozenset((STRONG_CONSISTENCY,
                                 EVENTUAL_CONSISTENCY,
                                 APPLY_ALL_JOBS_CONSISTENCY,
                                 ))

  # Accessors.  These are read-only attributes.

  @ConfigOption
  def deadline(value):
    """The deadline for any RPC issued.

    If unset the system default will be used which is typically 5 seconds.

    Raises:
      BadArgumentError if value is not a number or is less than zero.
    """
    if not isinstance(value, six_subset.integer_types + (float,)):
      raise datastore_errors.BadArgumentError(
        'deadline argument should be int/long/float (%r)' % (value,))
    if value <= 0:
      raise datastore_errors.BadArgumentError(
        'deadline argument should be > 0 (%r)' % (value,))
    return value

  @ConfigOption
  def on_completion(value):
    """A callback that is invoked when any RPC completes.

    If specified, it will be called with a UserRPC object as argument when an
    RPC completes.

    NOTE: There is a subtle but important difference between
    UserRPC.callback and Configuration.on_completion: on_completion is
    called with the RPC object as its first argument, where callback is
    called without arguments.  (Because a Configuration's on_completion
    function can be used with many UserRPC objects, it would be awkward
    if it was called without passing the specific RPC.)
    """
    # NOTE: There is no on_completion validation.  Passing something
    # inappropriate will raise an exception when it is called.
    return value

  @ConfigOption
  def read_policy(value):
    """The read policy to use for any relevent RPC.

    if unset STRONG_CONSISTENCY will be used.

    Raises:
      BadArgumentError if value is not a known read policy.
    """
    if value not in Configuration.ALL_READ_POLICIES:
      raise datastore_errors.BadArgumentError(
        'read_policy argument invalid (%r)' % (value,))
    return value

  @ConfigOption
  def force_writes(value):
    """If a write request should succeed even if the app is read-only.

    This only applies to user controlled read-only periods.
    """
    if not isinstance(value, bool):
      raise datastore_errors.BadArgumentError(
        'force_writes argument invalid (%r)' % (value,))
    return value

  @ConfigOption
  def max_entity_groups_per_rpc(value):
    """The maximum number of entity groups that can be represented in one rpc.

    For a non-transactional operation that involves more entity groups than the
    maximum, the operation will be performed by executing multiple, asynchronous
    rpcs to the datastore, each of which has no more entity groups represented
    than the maximum.  So, if a put() operation has 8 entity groups and the
    maximum is 3, we will send 3 rpcs, 2 with 3 entity groups and 1 with 2
    entity groups.  This is a performance optimization - in many cases
    multiple, small, concurrent rpcs will finish faster than a single large
    rpc.  The optimal value for this property will be application-specific, so
    experimentation is encouraged.
    """
    if not (isinstance(value, six_subset.integer_types) and value > 0):
      raise datastore_errors.BadArgumentError(
          'max_entity_groups_per_rpc should be a positive integer')
    return value

  @ConfigOption
  def max_allocate_ids_keys(value):
    """The maximum number of keys in a v1 AllocateIds rpc."""
    if not (isinstance(value, six_subset.integer_types) and value > 0):
      raise datastore_errors.BadArgumentError(
          'max_allocate_ids_keys should be a positive integer')
    return value

  @ConfigOption
  def max_rpc_bytes(value):
    """The maximum serialized size of a Get/Put/Delete without batching."""
    if not (isinstance(value, six_subset.integer_types) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_rpc_bytes should be a positive integer')
    return value

  @ConfigOption
  def max_get_keys(value):
    """The maximum number of keys in a Get without batching."""
    if not (isinstance(value, six_subset.integer_types) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_get_keys should be a positive integer')
    return value

  @ConfigOption
  def max_put_entities(value):
    """The maximum number of entities in a Put without batching."""
    if not (isinstance(value, six_subset.integer_types) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_put_entities should be a positive integer')
    return value

  @ConfigOption
  def max_delete_keys(value):
    """The maximum number of keys in a Delete without batching."""
    if not (isinstance(value, six_subset.integer_types) and value > 0):
      raise datastore_errors.BadArgumentError(
        'max_delete_keys should be a positive integer')
    return value


# Some Cloud Datastore calls are noops. We install a fake stub to handle them.
_NOOP_SERVICE = 'cloud_datastore_noop'


class _NoopRPC(apiproxy_rpc.RPC):
  """An RPC implementation that does not modify the response object."""

  def __init__(self):
    super(_NoopRPC, self).__init__()

  def _WaitImpl(self):
    return True

  def _MakeCallImpl(self):
    self._state = apiproxy_rpc.RPC.FINISHING


class _NoopRPCStub(object):
  """An RPC stub which always creates a NoopRPC."""

  def CreateRPC(self):  # pylint: disable=invalid-name
    return _NoopRPC()


class MultiRpc(object):
  """A wrapper around multiple UserRPC objects.

  This provides an API similar to that of UserRPC, but wraps multiple
  RPCs such that e.g. .wait() blocks until all wrapped RPCs are
  complete, and .get_result() returns the combined results from all
  wrapped RPCs.

  Class methods:
    flatten(rpcs): Expand a list of UserRPCs and MultiRpcs
      into a list of UserRPCs.
    wait_any(rpcs): Call UserRPC.wait_any(flatten(rpcs)).
    wait_all(rpcs): Call UserRPC.wait_all(flatten(rpcs)).

  Instance methods:
    wait(): Wait for all RPCs.
    check_success(): Wait and then check success for all RPCs.
    get_result(): Wait for all, check successes, then merge
      all results.

  Instance attributes:
    rpcs: The list of wrapped RPCs (returns a copy).
    state: The combined state of all RPCs.
  """

  def __init__(self, rpcs, extra_hook=None):
    """Constructor.

    Args:
      rpcs: A list of UserRPC and MultiRpc objects; it is flattened
        before being stored.
      extra_hook: Optional function to be applied to the final result
        or list of results.
    """
    self.__rpcs = self.flatten(rpcs)
    self.__extra_hook = extra_hook

  @property
  def rpcs(self):
    """Get a flattened list containing the RPCs wrapped.

    This returns a copy to prevent users from modifying the state.
    """
    return list(self.__rpcs)

  @property
  def state(self):
    """Get the combined state of the wrapped RPCs.

    This mimics the UserRPC.state property.  If all wrapped RPCs have
    the same state, that state is returned; otherwise, RUNNING is
    returned (which here really means 'neither fish nor flesh').
    """
    lo = apiproxy_rpc.RPC.FINISHING
    hi = apiproxy_rpc.RPC.IDLE
    for rpc in self.__rpcs:
      lo = min(lo, rpc.state)
      hi = max(hi, rpc.state)
    if lo == hi:
      return lo
    return apiproxy_rpc.RPC.RUNNING

  def wait(self):
    """Wait for all wrapped RPCs to finish.

    This mimics the UserRPC.wait() method.
    """
    apiproxy_stub_map.UserRPC.wait_all(self.__rpcs)

  def check_success(self):
    """Check success of all wrapped RPCs, failing if any of the failed.

    This mimics the UserRPC.check_success() method.

    NOTE: This first waits for all wrapped RPCs to finish before
    checking the success of any of them.  This makes debugging easier.
    """
    self.wait()
    for rpc in self.__rpcs:
      rpc.check_success()

  def get_result(self):
    """Return the combined results of all wrapped RPCs.

    This mimics the UserRPC.get_results() method.  Multiple results
    are combined using the following rules:

    1. If there are no wrapped RPCs, an empty list is returned.

    2. If exactly one RPC is wrapped, its result is returned.

    3. If more than one RPC is wrapped, the result is always a list,
       which is constructed from the wrapped results as follows:

       a. A wrapped result equal to None is ignored;

       b. A wrapped result that is a list (but not any other type of
          sequence!) has its elements added to the result list.

       c. Any other wrapped result is appended to the result list.

    After all results are combined, if __extra_hook is set, it is
    called with the combined results and its return value becomes the
    final result.

    NOTE: This first waits for all wrapped RPCs to finish, and then
    checks all their success.  This makes debugging easier.
    """
    # TODO(user): This is a temporary fix. Sub-RPCs are currently wrapping
    # exceptions in get_result() (through the extra_hook) instead of
    # check_success() so calling check_success() will expose the raw exception.
    # Functionality should be added to easily wrap exceptions thrown in
    # check_success.
    #
    # Check all successes before getting any result.
    # self.check_success()

    # Special-case a single RPC: always return its exact result.
    if len(self.__rpcs) == 1:
      results = self.__rpcs[0].get_result()
    else:
      results = []
      # NOTE: This merging of results is heuristic: Lists are
      # concatenated, other values joined into a list, None is skipped.
      for rpc in self.__rpcs:
        result = rpc.get_result()
        if isinstance(result, list):
          results.extend(result)
        elif result is not None:
          results.append(result)
    if self.__extra_hook is not None:
      results = self.__extra_hook(results)
    return results

  @classmethod
  def flatten(cls, rpcs):
    """Return a list of UserRPCs, expanding MultiRpcs in the argument list.

    For example: given 4 UserRPCs rpc1 through rpc4,
    flatten(rpc1, MultiRpc([rpc2, rpc3], rpc4)
    returns [rpc1, rpc2, rpc3, rpc4].

    Args:
      rpcs: A list of UserRPC and MultiRpc objects.

    Returns:
      A list of UserRPC objects.
    """
    flat = []
    for rpc in rpcs:
      if isinstance(rpc, MultiRpc):
        # NOTE: Because MultiRpc calls flatten() on its arguments,
        # there is no need to recursively flatten rpc.__rpcs -- it is
        # guaranteed to be already flat.
        flat.extend(rpc.__rpcs)
      else:
        if not isinstance(rpc, apiproxy_stub_map.UserRPC):
          raise datastore_errors.BadArgumentError(
            'Expected a list of UserRPC object (%r)' % (rpc,))
        flat.append(rpc)
    return flat

  @classmethod
  def wait_any(cls, rpcs):
    """Wait until one of the RPCs passed in is finished.

    This mimics UserRPC.wait_any().

    Args:
      rpcs: A list of UserRPC and MultiRpc objects.

    Returns:
      A UserRPC object or None.
    """
    return apiproxy_stub_map.UserRPC.wait_any(cls.flatten(rpcs))

  @classmethod
  def wait_all(cls, rpcs):
    """Wait until all RPCs passed in are finished.

    This mimics UserRPC.wait_all().

    Args:
      rpcs: A list of UserRPC and MultiRpc objects.
    """
    apiproxy_stub_map.UserRPC.wait_all(cls.flatten(rpcs))


class TransactionMode(object):
  """The mode of a Datastore transaction.

  Specifying the mode of the transaction can help to improve throughput, as it
  provides additional information about the intent (or lack of intent, in the
  case of a read only transaction) to perform a write as part of the
  transaction.
  """
  UNKNOWN = 0  #  Unknown transaction mode.
  READ_ONLY = 1  #  Transaction is used for both read and write oeprations.
  READ_WRITE = 2  #  Transaction is used only for read operations.


class BaseConnection(object):
  """Datastore connection base class.

  NOTE: Do not instantiate this class; use Connection or
  TransactionalConnection instead.

  This is not a traditional database connection -- with App Engine, in
  the end the connection is always implicit in the process state.
  There is also no intent to be compatible with PEP 249 (Python's
  Database-API).  But it is a useful abstraction to have an explicit
  object that manages the database interaction, and especially
  transactions.  Other settings related to the App Engine datastore
  are also stored here (e.g. the RPC timeout).

  A similar class in the Java API to the App Engine datastore is
  DatastoreServiceConfig (but in Java, transaction state is always
  held by the current thread).

  To use transactions, call connection.new_transaction().  This
  returns a new connection (an instance of the TransactionalConnection
  subclass) which you should use for all operations in the
  transaction.

  This model supports multiple unrelated concurrent transactions (but
  not nested transactions as this concept is commonly understood in
  the relational database world).

  When the transaction is done, call .commit() or .rollback() on the
  transactional connection.  If .commit() returns False, the
  transaction failed and none of your operations made it to the
  datastore; if it returns True, all your operations were committed.
  The transactional connection cannot be used once .commit() or
  .rollback() is called.

  Transactions are created lazily.  The first operation that requires
  a transaction handle will issue the low-level BeginTransaction
  request and wait for it to return.

  Transactions keep track of the entity group.  All operations within
  a transaction must use the same entity group.  An entity group
  (currently) comprises an app id, a namespace, and a top-level key (a
  kind and an id or name).  The first operation performed determines
  the entity group.  There is some special-casing when the first
  operation is a put() of an entity with an incomplete key; in this case
  the entity group is determined after the operation returns.

  NOTE: the datastore stubs in the dev_appserver currently support
  only a single concurrent transaction.  Specifically, the (old) file
  stub locks up if an attempt is made to start a new transaction while
  a transaction is already in use, whereas the sqlite stub fails an
  assertion.
  """

  UNKNOWN_DATASTORE = 0
  PRIMARY_STANDBY_DATASTORE = 1
  HIGH_REPLICATION_DATASTORE = 2

  __SUPPORTED_VERSIONS = frozenset((_DATASTORE_V3,
                                    _CLOUD_DATASTORE_V1))

  @_positional(1)
  def __init__(self, adapter=None, config=None, _api_version=_DATASTORE_V3):
    """Constructor.

    All arguments should be specified as keyword arguments.

    Args:
      adapter: Optional AbstractAdapter subclass instance;
        default IdentityAdapter.
      config: Optional Configuration object.
    """
    if adapter is None:
      adapter = IdentityAdapter()
    if not isinstance(adapter, AbstractAdapter):
      raise datastore_errors.BadArgumentError(
          'invalid adapter argument (%r)' % (adapter,))
    self.__adapter = adapter

    if config is None:
      config = Configuration()
    elif not Configuration.is_configuration(config):
      raise datastore_errors.BadArgumentError(
          'invalid config argument (%r)' % (config,))
    self.__config = config

    if _api_version not in self.__SUPPORTED_VERSIONS:
      raise datastore_errors.BadArgumentError(
          'unsupported API version (%s)' % (_api_version,))
    if _api_version == _CLOUD_DATASTORE_V1:
      if not _CLOUD_DATASTORE_ENABLED:
        raise datastore_errors.BadArgumentError(
            datastore_pbs.MISSING_CLOUD_DATASTORE_MESSAGE)
      # Install the noop service for some Cloud Datastore calls to use.
      apiproxy_stub_map.apiproxy.ReplaceStub(_NOOP_SERVICE, _NoopRPCStub())

    self._api_version = _api_version

    self.__pending_rpcs = set()

  # Accessors.  These are read-only attributes.

  @property
  def adapter(self):
    """The adapter used by this connection."""
    return self.__adapter

  @property
  def config(self):
    """The default configuration used by this connection."""
    return self.__config

  # TODO(user): We don't need to track pending RPCs for
  # non-transactional connections.
  def _add_pending(self, rpc):
    """Add an RPC object to the list of pending RPCs.

    The argument must be a UserRPC object, not a MultiRpc object.
    """
    assert not isinstance(rpc, MultiRpc)
    self.__pending_rpcs.add(rpc)

  def _remove_pending(self, rpc):
    """Remove an RPC object from the list of pending RPCs.

    If the argument is a MultiRpc object, the wrapped RPCs are removed
    from the list of pending RPCs.
    """
    if isinstance(rpc, MultiRpc):
      # Remove the wrapped RPCs, not the wrapping RPC.
      # NOTE: Avoid the rpcs property since it copies the list.
      for wrapped_rpc in rpc._MultiRpc__rpcs:
        self._remove_pending(wrapped_rpc)
    else:
      try:
        self.__pending_rpcs.remove(rpc)
      except KeyError:
        # Catching the exception is faster than first checking if it
        # is there (since that's another linear search).
        pass

  def is_pending(self, rpc):
    """Check whether an RPC object is currently pending.

    Note that 'pending' in this context refers to an RPC associated
    with this connection for which _remove_pending() hasn't been
    called yet; normally this is called by check_rpc_success() which
    itself is called by the various result hooks.  A pending RPC may
    be in the RUNNING or FINISHING state.

    If the argument is a MultiRpc object, this returns true if at least
    one of its wrapped RPCs is pending.
    """
    if isinstance(rpc, MultiRpc):
      for wrapped_rpc in rpc._MultiRpc__rpcs:
        if self.is_pending(wrapped_rpc):
          return True
      return False
    else:
      return rpc in self.__pending_rpcs

  def get_pending_rpcs(self):
    """Return (a copy of) the list of currently pending RPCs."""
    return set(self.__pending_rpcs)  # Make a copy to be on the safe side.

  def get_datastore_type(self, app=None):
    """Tries to get the datastore type for the given app.

    This function is only guaranteed to return something other than
    UNKNOWN_DATASTORE when running in production and querying the current app.
    """
    return _GetDatastoreType(app)

  def wait_for_all_pending_rpcs(self):
    """Wait for all currently pending RPCs to complete."""
    while self.__pending_rpcs:
      try:
        rpc = apiproxy_stub_map.UserRPC.wait_any(self.__pending_rpcs)
      except Exception:
        # Most likely the callback raised an exception.  Ignore it.
        # (Subtle: if it's still in the pending list it will come back
        # and then we'll likely take the other path.)
        # Log traceback at INFO level.
        logging.info('wait_for_all_pending_rpcs(): exception in wait_any()',
                     exc_info=True)
        continue
      if rpc is None:
        logging.debug('wait_any() returned None')
        continue
      assert rpc.state == apiproxy_rpc.RPC.FINISHING
      if rpc in self.__pending_rpcs:
        # Waiting for it did not remove it from the set.  This means
        # that either it didn't have a callback or the callback didn't
        # call self.check_rpc_success().  Call that now so that the
        # post-call hooks are called.  Note that this will not the
        # callback since it has already been called by wait_any().
        # Again, we ignore exceptions.
        try:
          self.check_rpc_success(rpc)
        except Exception:
          # Log traceback at INFO level.
          logging.info('wait_for_all_pending_rpcs(): '
                       'exception in check_rpc_success()',
                       exc_info=True)

  # TransactionalConnection overrides the following; their base class
  # implementations are no-ops.  For docstrings, see TransactionalConnection.

  def _create_rpc(self, config=None, service_name=None):
    """Create an RPC object using the configuration parameters.

    Internal only.

    Args:
      config: Optional Configuration object.
      service_name: Optional datastore service name.

    Returns:
      A new UserRPC object with the designated settings.

    NOTES:

    (1) The RPC object returned can only be used to make a single call
        (for details see apiproxy_stub_map.UserRPC).

    (2) To make a call, use one of the specific methods on the
        Connection object, such as conn.put(entities).  This sends the
        call to the server but does not wait.  To wait for the call to
        finish and get the result, call rpc.get_result().
    """
    deadline = Configuration.deadline(config, self.__config)
    on_completion = Configuration.on_completion(config, self.__config)
    callback = None
    if service_name is None:
      # NOTE(user): This is a best-effort attempt to support the
      # "hidden feature" in which an RPC may be passed to some methods in place
      # of a Configuration object. It will fail in cases where a particular
      # operation uses a different service than the connection uses in general
      # (e.g. allocate_ids() always uses datastore_v3, even on a v1 connection).
      service_name = self._api_version
    if on_completion is not None:
      # Create an intermediate closure because on_completion must be called
      # with an RPC argument whereas callback is called without arguments.
      def callback():
        return on_completion(rpc)
    rpc = apiproxy_stub_map.UserRPC(service_name, deadline, callback)
    return rpc

  # Backwards compatible alias. # TODO(user): Remove. http://b/11856478.
  create_rpc = _create_rpc

  def _set_request_read_policy(self, request, config=None):
    """Set the read policy on a request.

    This takes the read policy from the config argument or the
    configuration's default configuration, and sets the request's read
    options.

    Args:
      request: A read request protobuf.
      config: Optional Configuration object.

    Returns:
      True if the read policy specifies a read current request, False if it
        specifies an eventually consistent request, None if it does
        not specify a read consistency.
    """
    # Hidden feature: config may be a UserRPC object to use.
    if isinstance(config, apiproxy_stub_map.UserRPC):
      read_policy = getattr(config, 'read_policy', None)
    else:
      read_policy = Configuration.read_policy(config)

    # Compute the combined read_policy value.
    if read_policy is None:
      read_policy = self.__config.read_policy

    if hasattr(request, 'set_failover_ms') and hasattr(request, 'strong'):
      # It's a v3 read request.
      if read_policy == Configuration.APPLY_ALL_JOBS_CONSISTENCY:
        request.set_strong(True)
        return True
      elif read_policy == Configuration.EVENTUAL_CONSISTENCY:
        request.set_strong(False)  # let 4.1 shard use READ_CONSISTENT
        # It doesn't actually matter what value we set here;
        # datastore_client.cc will set its own deadline.  All that
        # matters is that we set a value.
        request.set_failover_ms(-1)
        return False
      else:
        return None
    elif hasattr(request, 'read_options'):
      # It's a v1 read request.
      # NOTE(user): Configuration.APPLY_ALL_JOBS_CONSISTENCY is
      # intentionally ignored for v1.
      if read_policy == Configuration.EVENTUAL_CONSISTENCY:
        request.read_options.read_consistency = (
            googledatastore.ReadOptions.EVENTUAL)
        return False
      else:
        return None
    else:
      raise datastore_errors.BadRequestError(
          'read_policy is only supported on read operations.')

  def _set_request_transaction(self, request):
    """Set the current transaction on a request.

    NOTE: This version of the method does nothing.  The version
    overridden by TransactionalConnection is the real thing.

    Args:
      request: A protobuf with a transaction field.

    Returns:
      An object representing a transaction or None.
    """
    return None

  def _make_rpc_call(self, config, method, request, response,
                     get_result_hook=None, user_data=None,
                     service_name=None):
    """Make an RPC call.

    Internal only.

    Except for the added config argument, this is a thin wrapper
    around UserRPC.make_call().

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      method: The method name.
      request: The request protocol buffer.
      response: The response protocol buffer.
      get_result_hook: Optional get-result hook function.  If not None,
        this must be a function with exactly one argument, the RPC
        object (self).  Its return value is returned from get_result().
      user_data: Optional additional arbitrary data for the get-result
        hook function.  This can be accessed as rpc.user_data.  The
        type of this value is up to the service module.

    Returns:
      The UserRPC object used for the call.
    """
    # Hidden feature: config may be a UserRPC object to use, and then
    # that object is returned.
    if isinstance(config, apiproxy_stub_map.UserRPC):
      rpc = config  # "We already got one."
    else:
      rpc = self._create_rpc(config, service_name)
    rpc.make_call(six_subset.ensure_binary(method), request, response,
                  get_result_hook, user_data)
    self._add_pending(rpc)
    return rpc

  # Backwards compatible alias. # TODO(user): Remove. http://b/11856478.
  make_rpc_call = _make_rpc_call

  def check_rpc_success(self, rpc):
    """Check for RPC success and translate exceptions.

    This wraps rpc.check_success() and should be called instead of that.

    This also removes the RPC from the list of pending RPCs, once it
    has completed.

    Args:
      rpc: A UserRPC or MultiRpc object.

    Raises:
      Nothing if the call succeeded; various datastore_errors.Error
      subclasses if ApplicationError was raised by rpc.check_success().
    """
    try:
      rpc.wait()
    finally:
      # If wait() raised an exception, it's likely a DeadlineExceededError,
      # and then we're better off removing it than keeping it.
      self._remove_pending(rpc)
    try:
      rpc.check_success()
    except apiproxy_errors.ApplicationError as err:
      raise _ToDatastoreError(err)

  # Basic operations: Get, Put, Delete.

  # Default limits for batching.  These can be overridden using the
  # corresponding Configuration options.
  MAX_RPC_BYTES = 1024 * 1024
  MAX_GET_KEYS = 1000
  MAX_PUT_ENTITIES = 500
  MAX_DELETE_KEYS = 500
  MAX_ALLOCATE_IDS_KEYS = 500
  # By default, client-side batching kicks in for all ops with more than 10
  # entity groups.
  DEFAULT_MAX_ENTITY_GROUPS_PER_RPC = 10
  # NOTE(user): Keep these in sync with similar constants in
  # com.google.appengine.tools.development.ApiProxyLocalImpl and

  def __get_max_entity_groups_per_rpc(self, config):
    """Internal helper: figures out max_entity_groups_per_rpc for the config."""
    return Configuration.max_entity_groups_per_rpc(
        config, self.__config) or self.DEFAULT_MAX_ENTITY_GROUPS_PER_RPC

  def _extract_entity_group(self, value):
    """Internal helper: extracts the entity group from a key or entity.

    Supports both v3 and v1 protobufs.

    Args:
      value: an entity_pb.{Reference, EntityProto} or
          googledatastore.{Key, Entity}.

    Returns:
      A tuple consisting of:
        - kind
        - name, id, or ('new', unique id)
    """
    if _CLOUD_DATASTORE_ENABLED and isinstance(value, googledatastore.Entity):
      value = value.key
    if isinstance(value, entity_pb.EntityProto):
      value = value.key()
    if _CLOUD_DATASTORE_ENABLED and isinstance(value, googledatastore.Key):
      elem = value.path[0]
      elem_id = elem.id
      elem_name = elem.name
      kind = elem.kind
    else:
      elem = value.path().element(0)
      kind = elem.type()
      elem_id = elem.id()
      elem_name = elem.name()
    # We use a tuple when elem has neither id nor name to avoid collisions
    # between elem.id() and id(elem).
    return (kind, elem_id or elem_name or ('new', id(elem)))

  def _map_and_group(self, values, map_fn, group_fn):
    """Internal helper: map values to keys and group by key. Here key is any
    object derived from an input value by map_fn, and which can be grouped
    by group_fn.

    Args:
      values: The values to be grouped by applying get_group(to_ref(value)).
      map_fn: a function that maps a value to a key to be grouped.
      group_fn: a function that groups the keys output by map_fn.

    Returns:
      A list where each element is a list of (key, index) pairs.  Here
      index is the location of the value from which the key was derived in
      the original list.
    """
    indexed_key_groups = collections.defaultdict(list)
    for index, value in enumerate(values):
      key = map_fn(value)
      indexed_key_groups[group_fn(key)].append((key, index))
    return list(indexed_key_groups.values())

  def __create_result_index_pairs(self, indexes):
    """Internal helper: build a function that ties an index with each result.

    Args:
      indexes: A list of integers.  A value x at location y in the list means
        that the result at location y in the result list needs to be at location
        x in the list of results returned to the user.
    """
    def create_result_index_pairs(results):
      return list(zip(results, indexes))
    return create_result_index_pairs

  def __sort_result_index_pairs(self, extra_hook):
    """Builds a function that sorts the indexed results.

    Args:
      extra_hook: A function that the returned function will apply to its result
        before returning.

    Returns:
      A function that takes a list of results and reorders them to match the
      order in which the input values associated with each results were
      originally provided.
    """

    def sort_result_index_pairs(result_index_pairs):
      results = [None] * len(result_index_pairs)
      for result, index in result_index_pairs:
        results[index] = result
      if extra_hook is not None:
        results = extra_hook(results)
      return results
    return sort_result_index_pairs

  def _generate_pb_lists(self, grouped_values, base_size, max_count,
                         max_groups, config):
    """Internal helper: repeatedly yield a list of 2 elements.

    Args:
      grouped_values: A list of lists.  The inner lists consist of objects
        grouped by e.g. entity group or id sequence.

      base_size: An integer representing the base size of an rpc.  Used for
        splitting operations across multiple RPCs due to size limitations.

      max_count: An integer representing the maximum number of objects we can
        send in an rpc.  Used for splitting operations across multiple RPCs.

      max_groups: An integer representing the maximum number of groups we can
        have represented in an rpc.  Can be None, in which case no constraint.

      config: The config object, defining max rpc size in bytes.

    Yields:
      Repeatedly yields 2 element tuples.  The first element is a list of
      protobufs to send in one batch.  The second element is a list containing
      the original location of those protobufs (expressed as an index) in the
      input.
    """
    max_size = (Configuration.max_rpc_bytes(config, self.__config) or
                self.MAX_RPC_BYTES)
    pbs = []
    pb_indexes = []
    size = base_size
    num_groups = 0
    for indexed_pbs in grouped_values:
      num_groups += 1
      if max_groups is not None and num_groups > max_groups:
        yield (pbs, pb_indexes)
        pbs = []
        pb_indexes = []
        size = base_size
        num_groups = 1
      for indexed_pb in indexed_pbs:
        (pb, index) = indexed_pb
        # Extra 5 bytes come from:
        # - 1 byte determined by looking at source of GetRequest.ByteSize().
        # - 4 bytes from inspecting code for pb.lengthString(), which is not
        #   available in proto2. 4 bytes is an upper bound for pb sizes
        #   up to 100MB.
        incr_size = pb.ByteSize() + 5
        # The test on the yield checks for several conditions:
        # - no batching if config is really a UserRPC object;
        # - avoid yielding empty batches;
        # - a batch can fill up based on count or serialized size.
        if (not isinstance(config, apiproxy_stub_map.UserRPC) and
            (len(pbs) >= max_count or (pbs and size + incr_size > max_size))):
          yield (pbs, pb_indexes)
          pbs = []
          pb_indexes = []
          size = base_size
          num_groups = 1
        pbs.append(pb)
        pb_indexes.append(index)
        size += incr_size
    yield (pbs, pb_indexes)  # Last batch.

  def __force(self, req):
    """Configure a request to force mutations."""
    if isinstance(req, (datastore_pb.PutRequest,
                        datastore_pb.TouchRequest,
                        datastore_pb.DeleteRequest)):
      req.set_force(True)

  def get(self, keys):
    """Synchronous Get operation.

    Args:
      keys: An iterable of user-level key objects.

    Returns:
      A list of user-level entity objects and None values, corresponding
      1:1 to the argument keys.  A None means there is no entity for the
      corresponding key.
    """
    return self.async_get(None, keys).get_result()

  def async_get(self, config, keys, extra_hook=None):
    """Asynchronous Get operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      keys: An iterable of user-level key objects.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

    Returns:
      A MultiRpc object.
    """
    # This function is a closure over self and config
    def make_get_call(base_req, pbs, extra_hook=None):
      req = copy.deepcopy(base_req)
      if self._api_version == _CLOUD_DATASTORE_V1:
        method = 'Lookup'
        req.keys.extend(pbs)
        resp = googledatastore.LookupResponse()
      else:
        method = 'Get'
        req.key_list().extend(pbs)
        resp = datastore_pb.GetResponse()
      # Note that we embed both the config and an optional user supplied hook in
      # the RPC's user_data.
      #
      # We also pass along the pbs (keys) that were requested.  In theory, we
      # should be able to simply retrieve these from the req object later, but
      # some users may be doing fancy things like intercepting these calls and
      # altering the request/response.
      user_data = config, pbs, extra_hook
      return self._make_rpc_call(config, method, req, resp,
                                 get_result_hook=self.__get_hook,
                                 user_data=user_data,
                                 service_name=self._api_version)

    if self._api_version == _CLOUD_DATASTORE_V1:
      base_req = googledatastore.LookupRequest()
      key_to_pb = self.__adapter.key_to_pb_v1
    else:
      base_req = datastore_pb.GetRequest()
      base_req.set_allow_deferred(True)
      key_to_pb = self.__adapter.key_to_pb
    is_read_current = self._set_request_read_policy(base_req, config)
    txn = self._set_request_transaction(base_req)

    # Special case for legacy support and single value
    if isinstance(config, apiproxy_stub_map.UserRPC) or len(keys) <= 1:
      pbs = [key_to_pb(key) for key in keys]
      return make_get_call(base_req, pbs, extra_hook)

    max_count = (Configuration.max_get_keys(config, self.__config) or
                 self.MAX_GET_KEYS)

    indexed_keys_by_entity_group = self._map_and_group(
        keys, key_to_pb, self._extract_entity_group)

    if is_read_current is None:
      is_read_current = (self.get_datastore_type() ==
                         BaseConnection.HIGH_REPLICATION_DATASTORE)
    # Entity group based client-side batch splitting is only useful when
    # performing a strong or consistent read. However, if we have a transaction
    # then all RPCs go to the same task so entity group client-side batching
    # won't have any impact.
    if is_read_current and txn is None:
      max_egs_per_rpc = self.__get_max_entity_groups_per_rpc(config)
    else:
      max_egs_per_rpc = None

    # Iterator yielding lists of entity protobufs, each
    # list representing one batch.
    pbsgen = self._generate_pb_lists(indexed_keys_by_entity_group,
                                     base_req.ByteSize(), max_count,
                                     max_egs_per_rpc, config)

    rpcs = []
    for pbs, indexes in pbsgen:
      rpcs.append(make_get_call(base_req, pbs,
                                self.__create_result_index_pairs(indexes)))
    return MultiRpc(rpcs, self.__sort_result_index_pairs(extra_hook))

  def __get_hook(self, rpc):
    """Internal method used as get_result_hook for Get operation."""
    self.check_rpc_success(rpc)

    # get_async stores the config, the requested keys, and an extra_hook on the
    # rpc's user_data field.
    config, keys_from_request, extra_hook = rpc.user_data

    if self._api_version == _DATASTORE_V3 and rpc.response.in_order():
      # The response is in the same order as the request.  This also implies
      # that there are no deferred results.
      entities = []
      for entity_result in rpc.response.entity_list():
        if entity_result.has_entity():
          entity = self.__adapter.pb_to_entity(entity_result.entity())
        else:
          entity = None
        entities.append(entity)
    else:
      # The response is not in order.  Start accumulating the results in a dict.
      current_get_response = rpc.response
      result_dict = {}
      self.__add_get_response_entities_to_dict(current_get_response,
                                               result_dict)

      # Issue additional (synchronous) RPCs until there are no more deferred
      # keys.
      deferred_req = copy.deepcopy(rpc.request)
      if self._api_version == _CLOUD_DATASTORE_V1:
        method = 'Lookup'
        deferred_resp = googledatastore.LookupResponse()
        while current_get_response.deferred:
          deferred_req.ClearField('keys')
          deferred_req.keys.extend(current_get_response.deferred)
          deferred_resp.Clear()
          deferred_rpc = self._make_rpc_call(config, method,
                                             deferred_req, deferred_resp,
                                             service_name=self._api_version)
          deferred_rpc.get_result()
          current_get_response = deferred_rpc.response

          # Add the resulting Entities to the result_dict.
          self.__add_get_response_entities_to_dict(current_get_response,
                                                   result_dict)
      else:
        method = 'Get'
        deferred_resp = datastore_pb.GetResponse()
        while current_get_response.deferred_list():
          deferred_req.clear_key()
          deferred_req.key_list().extend(current_get_response.deferred_list())
          deferred_resp.Clear()
          deferred_rpc = self._make_rpc_call(config, method,
                                             deferred_req, deferred_resp,
                                             service_name=self._api_version)
          deferred_rpc.get_result()
          current_get_response = deferred_rpc.response

          # Add the resulting Entities to the result_dict.
          self.__add_get_response_entities_to_dict(current_get_response,
                                                   result_dict)

      # Pull the results out of the dictionary in the order of the request keys.
      # Defaults to None for entries not in the dictionary.
      entities = [result_dict.get(datastore_types.ReferenceToKeyValue(pb))
                  for pb in keys_from_request]

    # Now we have all of the requested entities in the correct order.  Apply the
    # extra_hook function if it exists.
    if extra_hook is not None:
      entities = extra_hook(entities)

    return entities

  def __add_get_response_entities_to_dict(self, get_response, result_dict):
    """Converts entities from the get response and adds them to the dict.

    The Key for the dict will be calculated via
    datastore_types.ReferenceToKeyValue.  There will be no entry for entities
    that were not found.

    Args:
      get_response: A datastore_pb.GetResponse or
          googledatastore.LookupResponse.
      result_dict: The dict to add results to.
    """
    if (_CLOUD_DATASTORE_ENABLED
        and isinstance(get_response, googledatastore.LookupResponse)):
      for result in get_response.found:
        v1_key = result.entity.key
        entity = self.__adapter.pb_v1_to_entity(result.entity, False)
        result_dict[datastore_types.ReferenceToKeyValue(v1_key)] = entity
    else:
      for entity_result in get_response.entity_list():
        # Exclude missing entities from dict.
        if entity_result.has_entity():
          # Note that we take the protopuf Reference from the response and
          # create a hashable key from it.
          #
          # TODO(user): Check on remote api issues with getting key here
          reference_pb = entity_result.entity().key()
          hashable_key = datastore_types.ReferenceToKeyValue(reference_pb)
          entity = self.__adapter.pb_to_entity(entity_result.entity())
          result_dict[hashable_key] = entity

  def get_indexes(self):
    """Synchronous get indexes operation.

    Returns:
      user-level indexes representation
    """
    return self.async_get_indexes(None).get_result()

  def async_get_indexes(self, config, extra_hook=None, _app=None):
    """Asynchronous get indexes operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      extra_hook: Optional function to be called once the RPC has completed.

    Returns:
      A MultiRpc object.
    """
    req = datastore_pb.GetIndicesRequest()
    req.set_app_id(datastore_types.ResolveAppId(_app))
    resp = datastore_pb.CompositeIndices()
    return self._make_rpc_call(config, 'GetIndices', req, resp,
                               get_result_hook=self.__get_indexes_hook,
                               user_data=extra_hook,
                               service_name=_DATASTORE_V3)

  def __get_indexes_hook(self, rpc):
    """Internal method used as get_result_hook for Get operation."""
    self.check_rpc_success(rpc)
    indexes = [self.__adapter.pb_to_index(index)
               for index in rpc.response.index_list()]
    if rpc.user_data:
      indexes = rpc.user_data(indexes)
    return indexes

  def put(self, entities):
    """Synchronous Put operation.

    Args:
      entities: An iterable of user-level entity objects.

    Returns:
      A list of user-level key objects, corresponding 1:1 to the
      argument entities.

    NOTE: If any of the entities has an incomplete key, this will
    *not* patch up those entities with the complete key.
    """
    return self.async_put(None, entities).get_result()

  def async_put(self, config, entities, extra_hook=None):
    """Asynchronous Put operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      entities: An iterable of user-level entity objects.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

     Returns:
      A MultiRpc object.

    NOTE: If any of the entities has an incomplete key, this will
    *not* patch up those entities with the complete key.
    """
    # This function is a closure over self and config
    def make_put_call(base_req, pbs, user_data=None):
      req = copy.deepcopy(base_req)
      if self._api_version == _CLOUD_DATASTORE_V1:
        for entity in pbs:
          mutation = req.mutations.add()
          mutation.upsert.CopyFrom(entity)
        method = 'Commit'
        resp = googledatastore.CommitResponse()
      else:
        req.entity_list().extend(pbs)
        method = 'Put'
        resp = datastore_pb.PutResponse()
      user_data = pbs, user_data
      return self._make_rpc_call(config, method, req, resp,
                                 get_result_hook=self.__put_hook,
                                 user_data=user_data,
                                 service_name=self._api_version)

    # See elaborate comments about batching in async_get().
    if self._api_version == _CLOUD_DATASTORE_V1:
      base_req = googledatastore.CommitRequest()
      base_req.mode = googledatastore.CommitRequest.NON_TRANSACTIONAL
      entity_to_pb = self.__adapter.entity_to_pb_v1
    else:
      base_req = datastore_pb.PutRequest()
      entity_to_pb = self.__adapter.entity_to_pb
    self._set_request_transaction(base_req)
    if Configuration.force_writes(config, self.__config):
      self.__force(base_req)

    # Special case for legacy support and single value.
    if isinstance(config, apiproxy_stub_map.UserRPC) or len(entities) <= 1:
      pbs = [entity_to_pb(entity) for entity in entities]
      return make_put_call(base_req, pbs, extra_hook)

    max_count = (Configuration.max_put_entities(config, self.__config) or
                 self.MAX_PUT_ENTITIES)
    if ((self._api_version == _CLOUD_DATASTORE_V1 and
         not base_req.transaction) or
        not base_req.has_transaction()):
      max_egs_per_rpc = self.__get_max_entity_groups_per_rpc(config)
    else:
      max_egs_per_rpc = None

    indexed_entities_by_entity_group = self._map_and_group(
        entities, entity_to_pb, self._extract_entity_group)

    # Iterator yielding lists of key protobufs, each list representing
    # one batch.
    pbsgen = self._generate_pb_lists(indexed_entities_by_entity_group,
                                     base_req.ByteSize(), max_count,
                                     max_egs_per_rpc, config)

    rpcs = []
    for pbs, indexes in pbsgen:
      rpcs.append(make_put_call(base_req, pbs,
                                self.__create_result_index_pairs(indexes)))
    return MultiRpc(rpcs, self.__sort_result_index_pairs(extra_hook))

  def __put_hook(self, rpc):
    """Internal method used as get_result_hook for Put operation."""
    self.check_rpc_success(rpc)
    entities_from_request, extra_hook = rpc.user_data

    if (_CLOUD_DATASTORE_ENABLED
        and isinstance(rpc.response, googledatastore.CommitResponse)):
      keys = []
      i = 0
      for entity in entities_from_request:
        if datastore_pbs.is_complete_v1_key(entity.key):
          keys.append(entity.key)
        else:
          keys.append(rpc.response.mutation_results[i].key)
          i += 1
      keys = [self.__adapter.pb_v1_to_key(key) for key in keys]
    else:
      keys = [self.__adapter.pb_to_key(key) for key in rpc.response.key_list()]

    # NOTE: We don't patch up the keys of entities that were written
    # with an incomplete key here; that's up to the extra_hook.
    if extra_hook is not None:
      keys = extra_hook(keys)
    return keys

  def delete(self, keys):
    """Synchronous Delete operation.

    Args:
      keys: An iterable of user-level key objects.

    Returns:
      None.
    """
    return self.async_delete(None, keys).get_result()

  def async_delete(self, config, keys, extra_hook=None):
    """Asynchronous Delete operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      keys: An iterable of user-level key objects.
      extra_hook: Optional function to be called once the RPC has completed.

    Returns:
      A MultiRpc object.
    """
    # This function is a closure over self and config
    def make_delete_call(base_req, pbs, user_data=None):
      req = copy.deepcopy(base_req)
      if self._api_version == _CLOUD_DATASTORE_V1:
        for pb in pbs:
          mutation = req.mutations.add()
          mutation.delete.CopyFrom(pb)
        method = 'Commit'
        resp = googledatastore.CommitResponse()
      else:
        req.key_list().extend(pbs)
        method = 'Delete'
        resp = datastore_pb.DeleteResponse()
      return self._make_rpc_call(config, method, req, resp,
                                 get_result_hook=self.__delete_hook,
                                 user_data=user_data,
                                 service_name=self._api_version)

    # See elaborate comments about batching in async_get().
    if self._api_version == _CLOUD_DATASTORE_V1:
      base_req = googledatastore.CommitRequest()
      base_req.mode = googledatastore.CommitRequest.NON_TRANSACTIONAL
      key_to_pb = self.__adapter.key_to_pb_v1
    else:
      base_req = datastore_pb.DeleteRequest()
      key_to_pb = self.__adapter.key_to_pb
    self._set_request_transaction(base_req)
    if Configuration.force_writes(config, self.__config):
      self.__force(base_req)

    # Special case for legacy support and single value.
    if isinstance(config, apiproxy_stub_map.UserRPC) or len(keys) <= 1:
      pbs = [key_to_pb(key) for key in keys]
      return make_delete_call(base_req, pbs, extra_hook)

    max_count = (Configuration.max_delete_keys(config, self.__config) or
                 self.MAX_DELETE_KEYS)
    if ((self._api_version == _CLOUD_DATASTORE_V1 and
         not base_req.transaction) or
        not base_req.has_transaction()):
      max_egs_per_rpc = self.__get_max_entity_groups_per_rpc(config)
    else:
      max_egs_per_rpc = None

    indexed_keys_by_entity_group = self._map_and_group(
        keys, key_to_pb, self._extract_entity_group)

    # Iterator yielding lists of key protobufs, each list representing
    # one batch.
    pbsgen = self._generate_pb_lists(indexed_keys_by_entity_group,
                                     base_req.ByteSize(), max_count,
                                     max_egs_per_rpc, config)

    rpcs = []
    for pbs, _ in pbsgen:
      rpcs.append(make_delete_call(base_req, pbs))
    return MultiRpc(rpcs, extra_hook)

  def __delete_hook(self, rpc):
    """Internal method used as get_result_hook for Delete operation."""
    self.check_rpc_success(rpc)
    if rpc.user_data is not None:
      # Call it with None to match MultiRpc.
      rpc.user_data(None)

  # BeginTransaction operation.

  def begin_transaction(self,
                        app,
                        previous_transaction=None,
                        mode=TransactionMode.UNKNOWN):
    """Synchronous BeginTransaction operation.

    NOTE: In most cases the new_transaction() method is preferred,
    since that returns a TransactionalConnection object which will
    begin the transaction lazily.

    Args:
      app: Application ID.
      previous_transaction: The transaction to reset.
      mode: The transaction mode.

    Returns:
      An object representing a transaction or None.
    """
    return (self.async_begin_transaction(None, app, previous_transaction, mode)
            .get_result())

  def async_begin_transaction(self,
                              config,
                              app,
                              previous_transaction=None,
                              mode=TransactionMode.UNKNOWN):
    """Asynchronous BeginTransaction operation.

    Args:
      config: A configuration object or None.  Defaults are taken from
        the connection's default configuration.
      app: Application ID.
      previous_transaction: The transaction to reset.
      mode: The transaction mode.

    Returns:
      A MultiRpc object.
    """
    if not isinstance(app, six_subset.string_types) or not app:
      raise datastore_errors.BadArgumentError(
          'begin_transaction requires an application id argument (%r)' % (app,))

    if previous_transaction is not None and mode == TransactionMode.READ_ONLY:
      raise datastore_errors.BadArgumentError(
          'begin_transaction requires mode != READ_ONLY when '
          'previous_transaction is not None'
      )

    if self._api_version == _CLOUD_DATASTORE_V1:
      req = googledatastore.BeginTransactionRequest()
      resp = googledatastore.BeginTransactionResponse()

      # upgrade mode to READ_WRITE for retries
      if previous_transaction is not None:
        mode = TransactionMode.READ_WRITE

      if mode == TransactionMode.UNKNOWN:
        pass
      elif mode == TransactionMode.READ_ONLY:
        req.transaction_options.read_only.SetInParent()
      elif mode == TransactionMode.READ_WRITE:
        if previous_transaction is not None:
          (req.transaction_options.read_write
           .previous_transaction) = previous_transaction
        else:
          req.transaction_options.read_write.SetInParent()
    else:
      req = datastore_pb.BeginTransactionRequest()
      req.set_app(app)
      if (TransactionOptions.xg(config, self.__config)):
        req.set_allow_multiple_eg(True)

      if mode == TransactionMode.UNKNOWN:
        pass
      elif mode == TransactionMode.READ_ONLY:
        req.set_mode(datastore_pb.BeginTransactionRequest.READ_ONLY)
      elif mode == TransactionMode.READ_WRITE:
        req.set_mode(datastore_pb.BeginTransactionRequest.READ_WRITE)

      if previous_transaction is not None:
        req.mutable_previous_transaction().CopyFrom(previous_transaction)
      resp = datastore_pb.Transaction()

    return self._make_rpc_call(config, 'BeginTransaction', req, resp,
                               get_result_hook=self.__begin_transaction_hook,
                               service_name=self._api_version)

  def __begin_transaction_hook(self, rpc):
    """Internal method used as get_result_hook for BeginTransaction."""
    self.check_rpc_success(rpc)
    if self._api_version == _CLOUD_DATASTORE_V1:
      return rpc.response.transaction
    else:
      return rpc.response


class Connection(BaseConnection):
  """Transaction-less connection class.

  This contains those operations that are not allowed on transactional
  connections.  (Currently only allocate_ids and reserve_key_ids.)
  """

  @_positional(1)
  def __init__(self, adapter=None, config=None, _api_version=_DATASTORE_V3):
    """Constructor.

    All arguments should be specified as keyword arguments.

    Args:
      adapter: Optional AbstractAdapter subclass instance;
        default IdentityAdapter.
      config: Optional Configuration object.
    """
    super(Connection, self).__init__(adapter=adapter, config=config,
                                     _api_version=_api_version)
    self.__adapter = self.adapter  # Copy to new private variable.
    self.__config = self.config  # Copy to new private variable.

  # Pseudo-operation to create a new TransactionalConnection.

  def new_transaction(self, config=None, previous_transaction=None,
                      mode=TransactionMode.UNKNOWN):
    """Create a new transactional connection based on this one.

    This is different from, and usually preferred over, the
    begin_transaction() method; new_transaction() returns a new
    TransactionalConnection object.

    Args:
      config: A configuration object for the new connection, merged
        with this connection's config.
      previous_transaction: The transaction being reset.
      mode: The transaction mode.
    """
    config = self.__config.merge(config)
    return TransactionalConnection(adapter=self.__adapter, config=config,
                                   _api_version=self._api_version,
                                   previous_transaction=previous_transaction,
                                   mode=mode)

  # AllocateIds operation.

  def allocate_ids(self, key, size=None, max=None):
    """Synchronous AllocateIds operation.

    Exactly one of size and max must be specified.

    Args:
      key: A user-level key object.
      size: Optional number of IDs to allocate.
      max: Optional maximum ID to allocate.

    Returns:
      A pair (start, end) giving the (inclusive) range of IDs allocation.
    """
    return self.async_allocate_ids(None, key, size, max).get_result()

  def async_allocate_ids(self, config, key, size=None, max=None,
                         extra_hook=None):
    """Asynchronous AllocateIds operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      key: A user-level key object.
      size: Optional number of IDs to allocate.
      max: Optional maximum ID to allocate.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

    Returns:
      A MultiRpc object.
    """
    if size is not None:
      if max is not None:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate ids using both size and max')
      if not isinstance(size, six_subset.integer_types):
        raise datastore_errors.BadArgumentError('Invalid size (%r)' % (size,))
      if size > _MAX_ID_BATCH_SIZE:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate more than %s ids at a time; received %s'
          % (_MAX_ID_BATCH_SIZE, size))
      if size <= 0:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate less than 1 id; received %s' % size)
    if max is not None:
      if not isinstance(max, six_subset.integer_types):
        raise datastore_errors.BadArgumentError('Invalid max (%r)' % (max,))
      if max < 0:
        raise datastore_errors.BadArgumentError(
          'Cannot allocate a range with a max less than 0 id; received %s' %
          size)
    req = datastore_pb.AllocateIdsRequest()
    req.mutable_model_key().CopyFrom(self.__adapter.key_to_pb(key))
    if size is not None:
      req.set_size(size)
    if max is not None:
      req.set_max(max)
    resp = datastore_pb.AllocateIdsResponse()
    rpc = self._make_rpc_call(config, 'AllocateIds', req, resp,
                              get_result_hook=self.__allocate_ids_hook,
                              user_data=extra_hook,
                              service_name=_DATASTORE_V3)
    return rpc

  def __allocate_ids_hook(self, rpc):
    """Internal method used as get_result_hook for AllocateIds."""
    self.check_rpc_success(rpc)
    pair = rpc.response.start(), rpc.response.end()  # Inclusive range.
    if rpc.user_data is not None:
      pair = rpc.user_data(pair)
    return pair

  # AllocateIds operation with keys to reserve for restore/load/copy.

  def _reserve_keys(self, keys):
    """Synchronous AllocateIds operation to reserve the given keys.

    Sends one or more v3 AllocateIds rpcs with keys to reserve.
    Reserved keys must be complete and must have valid ids.

    Args:
      keys: Iterable of user-level keys.
    """
    self._async_reserve_keys(None, keys).get_result()

  def _async_reserve_keys(self, config, keys, extra_hook=None):
    """Asynchronous AllocateIds operation to reserve the given keys.

    Sends one or more v3 AllocateIds rpcs with keys to reserve.
    Reserved keys must be complete and must have valid ids.

    Args:
      config: A Configuration object or None to use Connection default.
      keys: Iterable of user-level keys.
      extra_hook: Optional function to be called on rpc result.

    Returns:
      None, or the result of user-supplied extra_hook.
    """
    def to_id_key(key):
      if key.path().element_size() == 1:
        return 'root_idkey'
      else:
        return self._extract_entity_group(key)

    keys_by_idkey = self._map_and_group(keys, self.__adapter.key_to_pb,
                                        to_id_key)
    max_count = (Configuration.max_allocate_ids_keys(config, self.__config) or
                 self.MAX_ALLOCATE_IDS_KEYS)

    rpcs = []
    pbsgen = self._generate_pb_lists(keys_by_idkey, 0, max_count, None, config)
    for pbs, _ in pbsgen:
      req = datastore_pb.AllocateIdsRequest()
      req.reserve_list().extend(pbs)
      resp = datastore_pb.AllocateIdsResponse()
      rpcs.append(self._make_rpc_call(config, 'AllocateIds', req, resp,
                                      get_result_hook=self.__reserve_keys_hook,
                                      user_data=extra_hook,
                                      service_name=_DATASTORE_V3))
    return MultiRpc(rpcs)

  def __reserve_keys_hook(self, rpc):
    """Internal get_result_hook for _reserve_keys."""
    self.check_rpc_success(rpc)
    if rpc.user_data is not None:
      return rpc.user_data(rpc.response)


class TransactionOptions(Configuration):
  """An immutable class that contains options for a transaction."""

  NESTED = 1
  """Create a nested transaction under an existing one."""

  MANDATORY = 2
  """Always propagate an existing transaction, throw an exception if there is
  no existing transaction."""

  ALLOWED = 3
  """If there is an existing transaction propagate it."""

  INDEPENDENT = 4
  """Always use a new transaction, pausing any existing transactions."""

  _PROPAGATION = frozenset((NESTED, MANDATORY, ALLOWED, INDEPENDENT))

  @ConfigOption
  def propagation(value):
    """How existing transactions should be handled.

    One of NESTED, MANDATORY, ALLOWED, INDEPENDENT. The interpertation of
    these types is up to higher level run-in-transaction implementations.

    WARNING: Using anything other than NESTED for the propagation flag
    can have strange consequences.  When using ALLOWED or MANDATORY, if
    an exception is raised, the transaction is likely not safe to
    commit.  When using INDEPENDENT it is not generally safe to return
    values read to the caller (as they were not read in the caller's
    transaction).

    Raises: datastore_errors.BadArgumentError if value is not reconized.
    """
    if value not in TransactionOptions._PROPAGATION:
      raise datastore_errors.BadArgumentError('Unknown propagation value (%r)' %
                                              (value,))
    return value

  @ConfigOption
  def xg(value):
    """Whether to allow cross-group transactions.

    Raises: datastore_errors.BadArgumentError if value is not a bool.
    """
    if not isinstance(value, bool):
      raise datastore_errors.BadArgumentError(
          'xg argument should be bool (%r)' % (value,))
    return value

  @ConfigOption
  def retries(value):
    """How many retries to attempt on the transaction.

    The exact retry logic is implemented in higher level run-in-transaction
    implementations.

    Raises: datastore_errors.BadArgumentError if value is not an integer or
      is not greater than zero.
    """
    datastore_types.ValidateInteger(value,
                                    'retries',
                                    datastore_errors.BadArgumentError,
                                    zero_ok=True)
    return value

  @ConfigOption
  def app(value):
    """The application in which to perform the transaction.

    Raises: datastore_errors.BadArgumentError if value is not a string
      or is the empty string.
    """
    datastore_types.ValidateString(value,
                                   'app',
                                   datastore_errors.BadArgumentError)
    return value


class TransactionalConnection(BaseConnection):
  """A connection specific to one transaction.

  It is possible to pass the transaction and entity group to the
  constructor, but typically the transaction is lazily created by
  _get_transaction() when the first operation is started.
  """

  # Transaction states
  OPEN = 0  # Initial state.
  COMMIT_IN_FLIGHT = 1  # A commit has started but not finished.
  FAILED = 2  # Commit attempt failed.
  CLOSED = 3  # Commit succeeded or rollback initiated.

  @_positional(1)
  def __init__(self,
               adapter=None, config=None, transaction=None, entity_group=None,
               _api_version=_DATASTORE_V3, previous_transaction=None,
               mode=TransactionMode.UNKNOWN):
    """Constructor.

    All arguments should be specified as keyword arguments.

    Args:
      adapter: Optional AbstractAdapter subclass instance;
        default IdentityAdapter.
      config: Optional Configuration object.
      transaction: Optional datastore_db.Transaction object.
      entity_group: Deprecated, do not use.
      previous_transaction: Optional datastore_db.Transaction object
        representing the transaction being reset.
      mode: Optional datastore_db.TransactionMode representing the transaction
        mode.

    Raises:
      datastore_errors.BadArgumentError: If previous_transaction and transaction
        are both set.
    """
    super(TransactionalConnection, self).__init__(adapter=adapter,
                                                  config=config,
                                                  _api_version=_api_version)

    self._state = TransactionalConnection.OPEN

    if previous_transaction is not None and transaction is not None:
      raise datastore_errors.BadArgumentError(
          'Only one of transaction and previous_transaction should be set')

    self.__adapter = self.adapter  # Copy to new private variable.
    self.__config = self.config  # Copy to new private variable.
    if transaction is None:
      app = TransactionOptions.app(self.config)
      app = datastore_types.ResolveAppId(TransactionOptions.app(self.config))
      self.__transaction_rpc = self.async_begin_transaction(
          None, app, previous_transaction, mode)
    else:
      if self._api_version == _CLOUD_DATASTORE_V1:
        txn_class = six_subset.binary_type
      else:
        txn_class = datastore_pb.Transaction
      if not isinstance(transaction, txn_class):
        raise datastore_errors.BadArgumentError(
            'Invalid transaction (%r)' % transaction)
      self.__transaction = transaction
      self.__transaction_rpc = None

    # Pending v1 transactional mutations.
    self.__pending_v1_upserts = {}
    self.__pending_v1_deletes = {}

  @property
  def finished(self):
    return self._state != TransactionalConnection.OPEN

  @property
  def transaction(self):
    """The current transaction. None when state == FINISHED."""
    if self.__transaction_rpc is not None:
      self.__transaction = self.__transaction_rpc.get_result()
      self.__transaction_rpc = None
    return self.__transaction

  def _set_request_transaction(self, request):
    """Set the current transaction on a request.

    This accesses the transaction property.  The transaction object
    returned is both set as the transaction field on the request
    object and returned.

    Args:
      request: A protobuf with a transaction field.

    Returns:
      An object representing a transaction or None.

    Raises:
      ValueError: if called with a non-Cloud Datastore request when using
          Cloud Datastore.
    """
    if self.finished:
      raise datastore_errors.BadRequestError(
          'Cannot start a new operation in a finished transaction.')
    transaction = self.transaction
    if self._api_version == _CLOUD_DATASTORE_V1:
      if isinstance(request, (googledatastore.CommitRequest,
                              googledatastore.RollbackRequest)):
        request.transaction = transaction
      elif isinstance(request, (googledatastore.LookupRequest,
                                googledatastore.RunQueryRequest)):
        request.read_options.transaction = transaction
      else:
        # We need to make sure we are not trying to set the transaction on an
        # unknown request. This is most likely the TaskQueue API. Once there is
        # an external version of that API, we should populate the transaction
        # accordingly.
        raise ValueError('Cannot use Cloud Datastore V1 transactions with %s.' %
                         type(request))
      request.read_options.transaction = transaction
    else:
      request.mutable_transaction().CopyFrom(transaction)
    return transaction

  # Put operation.

  def async_put(self, config, entities, extra_hook=None):
    """Transactional asynchronous Put operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      entities: An iterable of user-level entity objects.
      extra_hook: Optional function to be called on the result once the
        RPC has completed.

     Returns:
      A MultiRpc object.

    NOTE: If any of the entities has an incomplete key, this will
    *not* patch up those entities with the complete key.
    """
    if self._api_version != _CLOUD_DATASTORE_V1:
      # v3 async_put() supports transactional and non-transactional calls.
      return super(TransactionalConnection, self).async_put(
          config, entities, extra_hook)

    v1_entities = [self.adapter.entity_to_pb_v1(entity)
                   for entity in entities]

    # Allocate the IDs now and cache the puts until commit() is called.
    v1_req = googledatastore.AllocateIdsRequest()
    for v1_entity in v1_entities:
      if not datastore_pbs.is_complete_v1_key(v1_entity.key):
        v1_req.keys.add().CopyFrom(v1_entity.key)

    user_data = v1_entities, extra_hook

    service_name = _CLOUD_DATASTORE_V1
    if not v1_req.keys:
      # We don't need to do any work. Create a fake RPC.
      service_name = _NOOP_SERVICE
    return self._make_rpc_call(config, 'AllocateIds', v1_req,
                               googledatastore.AllocateIdsResponse(),
                               get_result_hook=self.__v1_put_allocate_ids_hook,
                               user_data=user_data,
                               service_name=service_name)

  def __v1_put_allocate_ids_hook(self, rpc):
    """Internal method used as get_result_hook for AllocateIds call."""
    self.check_rpc_success(rpc)
    v1_resp = rpc.response
    return self.__v1_build_put_result(list(v1_resp.keys),
                                      rpc.user_data)

  def __v1_build_put_result(self, v1_allocated_keys, user_data):
    """Internal method that builds the result of a put operation.

    Converts the results from a v1 AllocateIds operation to a list of user-level
    key objects.

    Args:
      v1_allocated_keys: a list of googledatastore.Keys that have been allocated
      user_data: a tuple consisting of:
        - a list of googledatastore.Entity objects
        - an optional extra_hook
    """
    v1_entities, extra_hook = user_data
    keys = []
    idx = 0
    for v1_entity in v1_entities:
      # Copy the entity because (1) we need to put the allocated key in it
      # without affecting the user-level Key object and (2) subsequent
      # local edits to the user-level Entity object should not affect the
      # mutation (unless put() is called again). This defensive copy is only
      # actually needed if the adapter does not return a new object when
      # converting (e.g. IdentityAdapter or an adapter that returns proxies).
      v1_entity = copy.deepcopy(v1_entity)
      if not datastore_pbs.is_complete_v1_key(v1_entity.key):
        v1_entity.key.CopyFrom(v1_allocated_keys[idx])
        idx += 1
      hashable_key = datastore_types.ReferenceToKeyValue(v1_entity.key)
      # Cancel any pending deletes for this entity.
      self.__pending_v1_deletes.pop(hashable_key, None)
      # TODO(user): Track size, count, number of entity groups, and raise
      # an error if limits are exceeded.
      self.__pending_v1_upserts[hashable_key] = v1_entity
      keys.append(self.adapter.pb_v1_to_key(copy.deepcopy(v1_entity.key)))
    # NOTE: We don't patch up the keys of entities that were written
    # with an incomplete key here; that's up to the extra_hook.
    if extra_hook:
      keys = extra_hook(keys)
    return keys

  # Delete operation.

  def async_delete(self, config, keys, extra_hook=None):
    """Transactional asynchronous Delete operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.
      keys: An iterable of user-level key objects.
      extra_hook: Optional function to be called once the RPC has completed.

    Returns:
      A MultiRpc object.
    """
    if self._api_version != _CLOUD_DATASTORE_V1:
      # v3 async_delete() supports transactional and non-transactional calls.
      return super(TransactionalConnection, self).async_delete(config,
                                                               keys,
                                                               extra_hook)

    v1_keys = [self.__adapter.key_to_pb_v1(key) for key in keys]

    for key in v1_keys:
      hashable_key = datastore_types.ReferenceToKeyValue(key)
      # Cancel any pending upserts for this entity.
      self.__pending_v1_upserts.pop(hashable_key, None)
      # TODO(user): Track size, count, number of entity groups, and raise
      # an error if limits are exceeded.
      self.__pending_v1_deletes[hashable_key] = key

    # No need to execute an RPC, but we're still obligated to return one, so
    # we use the NOOP service.
    return self._make_rpc_call(config, 'Commit', None,
                               googledatastore.CommitResponse(),
                               get_result_hook=self.__v1_delete_hook,
                               user_data=extra_hook,
                               service_name=_NOOP_SERVICE)

  def __v1_delete_hook(self, rpc):
    extra_hook = rpc.user_data
    if extra_hook:
      extra_hook(None)

  # Commit operation.

  def commit(self):
    """Synchronous Commit operation.

    Returns:
      True if the transaction was successfully committed.  False if
      the backend reported a concurrent transaction error.
    """
    # TODO(user): Without this create_rpc() call,
    # testTransactionRetries() (in datastore_unittest.py) fails.  Why?
    rpc = self._create_rpc(service_name=self._api_version)
    rpc = self.async_commit(rpc)
    if rpc is None:
      return True
    return rpc.get_result()

  def async_commit(self, config):
    """Asynchronous Commit operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.

    Returns:
      A MultiRpc object.
    """
    self.wait_for_all_pending_rpcs()

    if self._state != TransactionalConnection.OPEN:
      raise datastore_errors.BadRequestError('Transaction is already finished.')
    self._state = TransactionalConnection.COMMIT_IN_FLIGHT

    transaction = self.transaction
    if transaction is None:
      self._state = TransactionalConnection.CLOSED
      return None  # Neither True nor False.

    if self._api_version == _CLOUD_DATASTORE_V1:
      req = googledatastore.CommitRequest()
      req.transaction = transaction
      if Configuration.force_writes(config, self.__config):
        self.__force(req)

      # Move all pending mutations into the request.
      for entity in self.__pending_v1_upserts.values():
        mutation = req.mutations.add()
        mutation.upsert.CopyFrom(entity)
      for key in self.__pending_v1_deletes.values():
        mutation = req.mutations.add()
        mutation.delete.CopyFrom(key)
      # Transactional connections cannot be reused, but clear the cached
      # mutations anyway out of an abundance of caution.
      self.__pending_v1_upserts.clear()
      self.__pending_v1_deletes.clear()

      resp = googledatastore.CommitResponse()
    else:
      req = transaction
      resp = datastore_pb.CommitResponse()

    return self._make_rpc_call(config, 'Commit', req, resp,
                               get_result_hook=self.__commit_hook,
                               service_name=self._api_version)

  def __commit_hook(self, rpc):
    """Internal method used as get_result_hook for Commit."""
    try:
      rpc.check_success()
      self._state = TransactionalConnection.CLOSED
      self.__transaction = None
    except apiproxy_errors.ApplicationError as err:
      self._state = TransactionalConnection.FAILED
      if err.application_error == datastore_pb.Error.CONCURRENT_TRANSACTION:
        return False
      else:
        raise _ToDatastoreError(err)
    else:
      return True

  # Rollback operation.

  def rollback(self):
    """Synchronous Rollback operation."""
    rpc = self.async_rollback(None)
    if rpc is None:
      return None
    return rpc.get_result()

  def async_rollback(self, config):
    """Asynchronous Rollback operation.

    Args:
      config: A Configuration object or None.  Defaults are taken from
        the connection's default configuration.

     Returns:
      A MultiRpc object.
    """
    self.wait_for_all_pending_rpcs()

    if not (self._state == TransactionalConnection.OPEN
            or self._state == TransactionalConnection.FAILED):
      raise datastore_errors.BadRequestError(
          'Cannot rollback transaction that is neither OPEN or FAILED state.')

    transaction = self.transaction
    if transaction is None:
      return None

    self._state = TransactionalConnection.CLOSED
    self.__transaction = None

    if self._api_version == _CLOUD_DATASTORE_V1:
      req = googledatastore.RollbackRequest()
      req.transaction = transaction
      resp = googledatastore.RollbackResponse()
    else:
      req = transaction
      resp = api_base_pb.VoidProto()

    return self._make_rpc_call(config, 'Rollback', req, resp,
                               get_result_hook=self.__rollback_hook,
                               service_name=self._api_version)

  def __rollback_hook(self, rpc):
    """Internal method used as get_result_hook for Rollback."""
    self.check_rpc_success(rpc)


_DATASTORE_APP_ID_ENV = 'DATASTORE_APP_ID'
_DATASTORE_PROJECT_ID_ENV = 'DATASTORE_PROJECT_ID'
_DATASTORE_ADDITIONAL_APP_IDS_ENV = 'DATASTORE_ADDITIONAL_APP_IDS'
_DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV = 'DATASTORE_USE_PROJECT_ID_AS_APP_ID'


# pylint: disable=protected-access,invalid-name
def _CreateDefaultConnection(connection_fn, **kwargs):
  """Creates a new connection to Datastore.

  Uses environment variables to determine if the connection should be made
  to Cloud Datastore v1 or to Datastore's private App Engine API.
  If DATASTORE_PROJECT_ID exists, connect to Cloud Datastore v1. In this case,
  either DATASTORE_APP_ID or DATASTORE_USE_PROJECT_ID_AS_APP_ID must be set to
  indicate what the environment's application should be.

  Args:
    connection_fn: The function to use to create the connection.
    **kwargs: Addition arguments to pass to the connection_fn.

  Raises:
    ValueError: If DATASTORE_PROJECT_ID is set but DATASTORE_APP_ID or
       DATASTORE_USE_PROJECT_ID_AS_APP_ID is not. If DATASTORE_APP_ID doesn't
       resolve to DATASTORE_PROJECT_ID. If DATASTORE_APP_ID doesn't match
       an existing APPLICATION_ID.

  Returns:
    the connection object returned from connection_fn.
  """
  datastore_app_id = os.environ.get(_DATASTORE_APP_ID_ENV, None)
  datastore_project_id = os.environ.get(_DATASTORE_PROJECT_ID_ENV, None)
  if datastore_app_id or datastore_project_id:
    # We will create a Cloud Datastore context.
    app_id_override = bool(os.environ.get(
        _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV, False))
    if not datastore_app_id and not app_id_override:
      raise ValueError('Could not determine app id. To use project id (%s) '
                       'instead, set %s=true. This will affect the '
                       'serialized form of entities and should not be used '
                       'if serialized entities will be shared between '
                       'code running on App Engine and code running off '
                       'App Engine. Alternatively, set %s=<app id>.'
                       % (datastore_project_id,
                          _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV,
                          _DATASTORE_APP_ID_ENV))
    elif datastore_app_id:
      if app_id_override:
        raise ValueError('App id was provided (%s) but %s was set to true. '
                         'Please unset either %s or %s.' %
                         (datastore_app_id,
                          _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV,
                          _DATASTORE_APP_ID_ENV,
                          _DATASTORE_USE_PROJECT_ID_AS_APP_ID_ENV))
      elif datastore_project_id:
        # Project id and app id provided, make sure they are the same.
        id_resolver = datastore_pbs.IdResolver([datastore_app_id])
        if (datastore_project_id !=
            id_resolver.resolve_project_id(datastore_app_id)):
          raise ValueError('App id "%s" does not match project id "%s".'
                           % (datastore_app_id, datastore_project_id))

    datastore_app_id = datastore_app_id or datastore_project_id
    additional_app_str = os.environ.get(_DATASTORE_ADDITIONAL_APP_IDS_ENV, '')
    additional_apps = (app.strip() for app in additional_app_str.split(','))
    return _CreateCloudDatastoreConnection(connection_fn,
                                           datastore_app_id,
                                           additional_apps,
                                           kwargs)
  return connection_fn(**kwargs)


# pylint: disable=protected-access,invalid-name
def _CreateCloudDatastoreConnection(connection_fn,
                                    app_id,
                                    external_app_ids,
                                    kwargs):
  """Creates a new context to connect to a remote Cloud Datastore instance.

  This should only be used outside of Google App Engine.

  Args:
    connection_fn: A connection function which accepts both an _api_version
      and an _id_resolver argument.
    app_id: The application id to connect to. This differs from the project
      id as it may have an additional prefix, e.g. "s~" or "e~".
    external_app_ids: A list of apps that may be referenced by data in your
      application. For example, if you are connected to s~my-app and store keys
      for s~my-other-app, you should include s~my-other-app in the external_apps
      list.
    kwargs: The additional kwargs to pass to the connection_fn.

  Raises:
    ValueError: if the app_id provided doesn't match the current environment's
        APPLICATION_ID.

  Returns:
    An ndb.Context that can connect to a Remote Cloud Datastore. You can use
    this context by passing it to ndb.set_context.
  """
  # Late import to avoid circular deps.
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.third_party.appengine.datastore import cloud_datastore_v1_remote_stub

  if not datastore_pbs._CLOUD_DATASTORE_ENABLED:
    raise datastore_errors.BadArgumentError(
        datastore_pbs.MISSING_CLOUD_DATASTORE_MESSAGE)

  current_app_id = os.environ.get('APPLICATION_ID', None)
  if current_app_id and current_app_id != app_id:
    # TODO(user): We should support this so users can connect to different
    # applications.
    raise ValueError('Cannot create a Cloud Datastore context that connects '
                     'to an application (%s) that differs from the application '
                     'already connected to (%s).' % (app_id, current_app_id))
  os.environ['APPLICATION_ID'] = app_id

  id_resolver = datastore_pbs.IdResolver((app_id,) + tuple(external_app_ids))
  project_id = id_resolver.resolve_project_id(app_id)
  endpoint = googledatastore.helper.get_project_endpoint_from_env(project_id)
  datastore = googledatastore.Datastore(
      project_endpoint=endpoint,
      credentials=googledatastore.helper.get_credentials_from_env())
  kwargs['_api_version'] = _CLOUD_DATASTORE_V1
  kwargs['_id_resolver'] = id_resolver
  conn = connection_fn(**kwargs)

  # If necessary, install the stubs
  # pylint: disable=bare-except
  try:
    stub = cloud_datastore_v1_remote_stub.CloudDatastoreV1RemoteStub(datastore)
    apiproxy_stub_map.apiproxy.RegisterStub(_CLOUD_DATASTORE_V1,
                                            stub)
  except:
    pass  # The stub is already installed.
  # TODO(user): Ensure the current stub is connected to the right project.

  # Install a memcache and taskqueue stub which throws on everything.
  try:
    apiproxy_stub_map.apiproxy.RegisterStub('memcache', _ThrowingStub())
  except:
    pass  # The stub is already installed.
  try:
    apiproxy_stub_map.apiproxy.RegisterStub('taskqueue', _ThrowingStub())
  except:
    pass  # The stub is already installed.

  return conn


class _ThrowingStub(object):
  """A Stub implementation which always throws a NotImplementedError."""

  # pylint: disable=invalid-name
  def MakeSyncCall(self, service, call, request, response):
    raise NotImplementedError('In order to use %s.%s you must '
                              'install the Remote API.' % (service, call))

  # pylint: disable=invalid-name
  def CreateRPC(self):
    return apiproxy_rpc.RPC(stub=self)


# TODO(user): Consider moving these to datastore_errors.py.
# TODO(user): Write unittests for these?


def _ToDatastoreError(err):
  """Converts an apiproxy.ApplicationError to an error in datastore_errors.

  Args:
    err: An apiproxy.ApplicationError object.

  Returns:
    An instance of a subclass of datastore_errors.Error.
  """
  return _DatastoreExceptionFromErrorCodeAndDetail(err.application_error,
                                                   err.error_detail)


_DATASTORE_EXCEPTION_CLASSES = {
    datastore_pb.Error.BAD_REQUEST: datastore_errors.BadRequestError,
    datastore_pb.Error.CONCURRENT_TRANSACTION: datastore_errors.TransactionFailedError,
    datastore_pb.Error.INTERNAL_ERROR: datastore_errors.InternalError,
    datastore_pb.Error.NEED_INDEX: datastore_errors.NeedIndexError,
    datastore_pb.Error.TIMEOUT: datastore_errors.Timeout,
    datastore_pb.Error.BIGTABLE_ERROR: datastore_errors.Timeout,
    datastore_pb.Error.COMMITTED_BUT_STILL_APPLYING: datastore_errors.CommittedButStillApplying,
    datastore_pb.Error.CAPABILITY_DISABLED: apiproxy_errors.CapabilityDisabledError,
    datastore_pb.Error.RESOURCE_EXHAUSTED: apiproxy_errors.OverQuotaError,
}

_CLOUD_DATASTORE_EXCEPTION_CLASSES = {}

if _CLOUD_DATASTORE_ENABLED:
  _CLOUD_DATASTORE_EXCEPTION_CLASSES = {
      googledatastore.code_pb2.INVALID_ARGUMENT: datastore_errors.BadRequestError,
      googledatastore.code_pb2.ABORTED: datastore_errors.TransactionFailedError,
      googledatastore.code_pb2.FAILED_PRECONDITION:
          # Could also indicate SAFE_TIME_TOO_OLD.
          datastore_errors.NeedIndexError,
      googledatastore.code_pb2.DEADLINE_EXCEEDED: datastore_errors.Timeout,
      googledatastore.code_pb2.PERMISSION_DENIED: datastore_errors.BadRequestError,
      googledatastore.code_pb2.UNAVAILABLE: apiproxy_errors.RPCFailedError,
      googledatastore.code_pb2.RESOURCE_EXHAUSTED: apiproxy_errors.OverQuotaError,
      googledatastore.code_pb2.INTERNAL:
          # Could also indicate COMMITTED_BUT_STILL_APPLYING
          datastore_errors.InternalError,
  }


def _DatastoreExceptionFromErrorCodeAndDetail(error, detail):
  """Converts a datastore_pb.Error into a datastore_errors.Error.

  Args:
    error: A member of the datastore_pb.Error enumeration.
    detail: A string providing extra details about the error.

  Returns:
    An instance of a subclass of datastore_errors.Error.
  """
  exception_class = _DATASTORE_EXCEPTION_CLASSES.get(error,
                                                     datastore_errors.Error)

  if detail is None:
    return exception_class()
  else:
    return exception_class(detail)


def _DatastoreExceptionFromCanonicalErrorCodeAndDetail(error, detail):
  """Converts a canonical error code into a datastore_errors.Error.

  Args:
    error: A canonical error code from google.rpc.code.
    detail: A string providing extra details about the error.

  Returns:
    An instance of a subclass of datastore_errors.Error.
  """
  exception_class = _CLOUD_DATASTORE_EXCEPTION_CLASSES.get(
      error, datastore_errors.InternalError)

  if detail is None:
    return exception_class()
  else:
    return exception_class(detail)
