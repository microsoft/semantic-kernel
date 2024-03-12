# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""The Cloud SDK persistent cache abstract base classes.

A persistent cache is a long-lived object that contains cache data and metadata.
Cache data is organized into zero or more named tables. Table data is an
unordered list of row tuples of fixed length. Column value types within a row
are fixed and may be one of string (basestring or unicode), floating point, or
integer.

    +-----------------------+
    | persistent cache      |
    | +-------------------+ |
    | | table             | |
    | | (key,...,col,...) | |
    | |        ...        | |
    | +-------------------+ |
    |          ...          |
    +-----------------------+

A persistent cache is implemented as a Cache object that contains Table objects.
Each table has a timeout and last modified time attribute. Read access on a
table that has expired is an error. The rows in a table have a fixed number of
columns specified by the columns attribute. The keys attribute is the count of
columns in a table row, left to right, that forms the primary key. The primary
key is used to differentiate rows. Adding a row that already exists is not an
error. The row is simply replaced by the new data.

A Table object can be restricted and hidden from cache users. These tables
must be instantiated when the Cache object is instantiated, before the first
user access to the cache. This allows a cache implementation layer to have
tables that are hidden from the layers above it.

The table select and delete methods match against a row template. A template may
have fewer columns than the number of columns in the table. Omitted template
columns or columns with value None match all values for that column. '*' and '?'
matching operators are supported for string columns. It is not an error to
select or delete a row that does not exist.

HINTS for IMPLEMENTERS

By default the Cache and Table constructors create the objects if they don't
exist. The create=False kwarg disables this and raises an exception if the
object does not exist. In addition, the Select ignore_expiration=True kwarg
disables expiry check. These can be used by meta commands/functions to view
and debug cache data without modifying the underlying persistent data.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import time

from googlecloudsdk.core.cache import exceptions

import six
import six.moves.urllib.parse


def Now():
  """Returns the current time in seconds since the epoch."""
  return time.time()


@six.add_metaclass(abc.ABCMeta)
class Table(object):
  """A persistent cache table object.

  This object should only be instantiated by a Cache object.

  The AddRows and DeleteRows methods operate on lists of rows rather than a
  single row. This accomodates sqlite3 (and possibly other implementation
  layers) that batch rows ops. Restricting to a single row would rule out
  batching.

  Attributes:
    cache: The parent cache object.
    changed: Table data or metadata changed if True.
    name: The table name.
    modified: Table modify Now() (time.time()) value. 0 for expired tables.
    restricted: True if Table is restricted.
    timeout: A float number of seconds. Tables older than (modified+timeout)
      are invalid. 0 means no timeout.
  """

  def __init__(self, cache, name, columns=1, keys=1, timeout=0, modified=0,
               restricted=False):
    self._cache = cache
    self.name = name
    self.restricted = restricted
    self.modified = modified
    self.changed = False
    self.timeout = timeout or 0
    self.columns = columns
    self.keys = keys
    # Determine is the table has expired once at initialization time. We expect
    # callers to keep cache or table objects open for a few seconds at most.
    # Given that it doesn't make sense to do a few operations in that window
    # only to have the last one expire.
    if timeout and modified and (modified + timeout) < Now():
      self.Invalidate()

  @property
  def is_expired(self):
    """True if the table data has expired.

    Expired tables have a self.modified value of 0. Expiry is currently
    computed once when the table object is instantiated. This property shields
    callers from that implementation detail.

    Returns:
      True if the table data has expired.
    """
    return not self.modified

  @classmethod
  def EncodeName(cls, name):
    r"""Returns name encoded for file system path compatibility.

    A table name may be a file name. alnum and '_.-' are not encoded.

    Args:
      name: The cache name string to encode.

    Raises:
      CacheTableNameInvalid: For invalid table names.

    Returns:
      Name encoded for portability.
    """
    if not name:
      raise exceptions.CacheTableNameInvalid(
          'Cache table name [{}] is invalid.'.format(name))
    return six.moves.urllib.parse.quote(name, '!@+,')

  def _CheckRows(self, rows):
    """Raise an exception if the size of any row in rows is invalid.

    Each row size must be equal to the number of columns in the table.

    Args:
      rows: The list of rows to check.

    Raises:
      CacheTableRowSizeInvalid: If any row has an invalid size.
    """
    for row in rows:
      if len(row) != self.columns:
        raise exceptions.CacheTableRowSizeInvalid(
            'Cache table [{}] row size [{}] is invalid. Must be {}.'.format(
                self.name, len(row), self.columns))

  def _CheckRowTemplates(self, rows):
    """Raise an exception if the size of any row template in rows is invalid.

    Each row template must have at least 1 column and no more than the number
    of columns in the table.

    Args:
      rows: The list of rows to check.

    Raises:
      CacheTableRowSizeInvalid: If any row template size is invalid.
    """
    for row in rows:
      if not 1 <= len(row) <= self.columns:
        if self.columns == 1:
          limits = '1'
        else:
          limits = '>= 1 and <= {}'.format(self.columns)
        raise exceptions.CacheTableRowSizeInvalid(
            'Cache table [{}] row size [{}] is invalid. Must be {}.'.format(
                self.name, len(row), limits))

  def Invalidate(self):
    """Invalidates the table by marking it expired."""
    self.changed = True
    self.modified = 0

  def Validate(self, timeout=None):
    """Validates the table and resets the TTL."""
    if timeout is not None:
      self.timeout = timeout or 0
    self.modified = Now()
    self.changed = True

  @abc.abstractmethod
  def Delete(self):
    """Deletes the table."""
    pass

  @abc.abstractmethod
  def AddRows(self, rows):
    """Adds each row in rows to the table. Existing rows are overwritten.

    The number of columns in each row must be equal to the number of columns
    in the table.

    Args:
      rows: A list of rows to add. Existing rows are overwritten.
    """
    pass

  @abc.abstractmethod
  def DeleteRows(self, row_templates=None):
    """Deletes each row in the table matching any of the row_templates.

    Args:
      row_templates: A list of row templates. See Select() below for a detailed
        description of templates. None deletes all rows and is allowed for
        expired tables.
    """
    pass

  @abc.abstractmethod
  def Select(self, row_template=None, ignore_expiration=False):
    """Returns the list of rows that match row_template.

    Args:
      row_template: A row template. The number of columns in the template must
        not exceed the number of columns in the table. An omitted column or
        column with value None matches all values for the column. A None value
        for row_template matches all rows. Each string column may contain these
        wildcard characters:
          * - match zero or more characters
          ? - match any character
      ignore_expiration: Disable table expiration checks if True.

    Raises:
      CacheTableExpired: If the table has expired.

    Returns:
      The list of rows that match row_template.
    """
    pass


@six.add_metaclass(abc.ABCMeta)
class Cache(object):
  r"""A persistent cache object.

  This class is also a context manager. Changes are automaticaly committed if
  the context exits with no exceptions. For example:

    with CacheImplementation('my-cache-name') as c:
      ...

  Attributes:
    name: The persistent cache name. Created/removed by this object. Internally
      encoded by Cache.EncodeName().
    timeout: The default table timeout in seconds. 0 for no timeout.
    version: A caller defined version string that must match the version string
      stored when the persistent object was created.
  """

  def __init__(self, name, create=True, timeout=None, version=None):
    self.name = Cache.EncodeName(name)
    del create  # Unused in __init__. Subclass constructors may use this.
    self.timeout = timeout
    self.version = version

  def __enter__(self):
    return self

  def __exit__(self, typ, value, traceback):
    self.Close(commit=typ is None)

  @classmethod
  def EncodeName(cls, name):
    r"""Returns name encoded for filesystem portability.

    A cache name may be a file path. The part after the rightmost of
    ('/', '\\') is encoded with Table.EncodeName().

    Args:
      name: The cache name string to encode.

    Raises:
      CacheNameInvalid: For invalid cache names.

    Returns:
      Name encoded for filesystem portability.
    """
    basename_index = max(name.rfind('/'), name.rfind('\\')) + 1
    if not name[basename_index:]:
      raise exceptions.CacheNameInvalid(
          'Cache name [{}] is invalid.'.format(name))
    return name[:basename_index] + Table.EncodeName(name[basename_index:])

  @abc.abstractmethod
  def Delete(self):
    """Permanently deletes the cache."""
    pass

  def Invalidate(self):
    """Invalidates the cache by invalidating all of its tables."""
    for name in self.Select():
      self.Table(name).Invalidate()

  @abc.abstractmethod
  def Commit(self):
    """Commits all changes up to this point."""
    pass

  @abc.abstractmethod
  def Close(self, commit=True):
    """Closes the cache, optionally committing any changes.

    Args:
      commit: Commits any changes before closing if True.
    """
    pass

  @abc.abstractmethod
  def Table(self, name, create=True, columns=1, keys=1, timeout=None):
    """Returns the Table object for existing table name.

    Args:
      name: The table name.
      create: If True creates the table if it does not exist.
      columns: The number of columns in the table. Must be >= 1.
      keys: The number of columns, starting from 0, that form the primary
        row key. Must be 1 <= keys <= columns. The primary key is used to
        differentiate rows in the AddRows and DeleteRows methods.
      timeout: The table timeout in seconds, 0 for no timeout.

    Raises:
      CacheTableNameInvalid: name is not a valid table name.
      CacheTableNotFound: If the table does not exist.

    Returns:
      A Table object for name.
    """
    pass

  @abc.abstractmethod
  def Select(self, name=None):
    """Returns the list of table names matching name.

    Args:
      name: The table name pattern to match, None for all tables. The pattern
        may contain these wildcard characters:
          * - match zero or more characters
          ? - match any character
    """
    pass
