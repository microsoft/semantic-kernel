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

"""A persistent cache metadata table implementation layer.

Used by persistent cache implementations that maintain a metadata table to keep
track of cache tables.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.core.cache import exceptions
from googlecloudsdk.core.cache import persistent_cache_base

import six


class Metadata(object):
  """Metadata table row container.

  This object encapsulates the persistent metadata table row layout.

  Attributes:
    name: The table name.
    columns: The number of columns in the table. Must be >= 1.
    keys: The number of columns, starting from 0, that form the primary
      row key. Must be 1 <= keys <= columns. The primary key is used to
      differentiate rows in the AddRows and DeleteRows methods.
    timeout: A float number of seconds. Tables older than (modified+timeout)
      are invalid. 0 means no timeout.
    modified: Table modify Now() (time.time()) value. 0 for expired tables.
    restricted: True if Table is restricted.
    version: A caller defined version string that must match the version string
      stored when the persistent object was created. '' for all but the
      metadata table itself.
  """

  COLUMNS = 7

  def __init__(self, row):
    """Constructs a metadata container from a row."""
    (self.name, self.columns, self.keys, self.timeout, self.modified,
     restricted, self.version) = row
    self.restricted = bool(restricted)

  @classmethod
  def Row(cls, name=None, columns=None, keys=None, timeout=None,
          modified=None, restricted=None, version=None):
    """Constructs and returns a metadata table row from the args."""
    if restricted is not None:
      restricted = int(restricted)
    return (name, columns, keys, timeout, modified, restricted, version)


@six.add_metaclass(abc.ABCMeta)
class CacheUsingMetadataTable(persistent_cache_base.Cache):
  """A persistent cache metadata table implementation layer.

  Attributes:
    _metadata: A table containing a row for each table.
    _table_class: The cache Table class.
    _restricted: The set of restricted table names.
    _tables: The map of open table objects.
  """

  def __init__(self, table, name, create=True, timeout=0, version=None):
    super(CacheUsingMetadataTable, self).__init__(
        name, create=create, timeout=timeout, version=version)
    self._metadata = None
    self._table_class = table
    self._restricted = None
    self._tables = None

  @abc.abstractmethod
  def Delete(self):
    pass

  @abc.abstractmethod
  def Commit(self):
    pass

  @abc.abstractmethod
  def Close(self, commit=True):
    pass

  def _ImplementationCreateTable(self, name, columns, keys):
    """Implementation layer _CreateTable.

    The cache implementation object can override this method to do
    implementation specific table initialization.

    Args:
      name: The table name.
      columns: The number of columns in each row.
      keys: The number of columns, left to right, that are primary keys. 0 for
        all columns.
    """
    pass

  def _CreateTable(self, name, restricted, columns, keys, timeout):
    """Creates and returns a table object for name.

    NOTE: This code is conditioned on self._metadata. If self._metadata is None
    then we are initializing/updating the metadata table. The table name is
    relaxed, in particular '_' is allowed in the table name. This avoids user
    table name conflicts. Finally, self._metadata is set and the metadata
    table row is updated to reflect any changes in the default timeout.

    Args:
      name: The table name.
      restricted: Return a restricted table object.
      columns: The number of columns in each row.
      keys: The number of columns, left to right, that are primary keys. 0 for
        all columns.
      timeout: The number of seconds after last modification when the table
        becomes invalid. 0 for no timeout.

    Raises:
      CacheTableNameInvalid: If name is invalid.

    Returns:
      A table object for name.
    """
    if columns is None:
      columns = 1
    if columns < 1:
      raise exceptions.CacheTableColumnsInvalid(
          '[{}] table [{}] column count [{}] must be >= 1.'.format(
              self.name, name, columns))
    if keys is None:
      keys = columns
    if keys < 1 or keys > columns:
      raise exceptions.CacheTableKeysInvalid(
          '[{}] table [{}] primary key count [{}] must be >= 1 and <= {}.'
          .format(self.name, name, keys, columns))
    if timeout is None:
      timeout = self.timeout
    self._ImplementationCreateTable(name, columns, keys)
    table = self._table_class(self,
                              name=name,
                              columns=columns,
                              keys=keys,
                              timeout=timeout,
                              modified=0,
                              restricted=restricted)
    if self._metadata:
      version = None
    else:
      # Initializing the metadata table -- get its Table object.
      self._metadata = table
      table.Validate()
      rows = table.Select(Metadata.Row(name=name))
      row = rows[0] if rows else None
      if row:
        metadata = Metadata(row)
        if self.version is None:
          self.version = metadata.version or ''
        elif self.version != metadata.version:
          raise exceptions.CacheVersionMismatch(
              '[{}] cache version [{}] does not match [{}].'.format(
                  self.name, metadata.version, self.version),
              metadata.version, self.version)
        if self.timeout is None:
          self.timeout = metadata.timeout
      table.modified = 0
      version = self.version
    self._metadata.AddRows([Metadata.Row(
        name=table.name,
        columns=table.columns,
        keys=table.keys,
        timeout=table.timeout,
        modified=table.modified,
        restricted=table.restricted,
        version=version)])
    return table

  def Table(self, name, create=True, restricted=False, columns=None, keys=None,
            timeout=None):
    """Returns the Table object for existing table name.

    Args:
      name: The table name.
      create: If True creates the table if it does not exist.
      restricted: Return a restricted table object.
      columns: The number of columns in each row.
      keys: The number of columns, left to right, that are primary keys. 0 for
        all columns.
      timeout: The number of seconds after last modification when the table
        becomes invalid. 0 for no timeout. If None then the default cache
        timeout is assumed.

    Raises:
      CacheTableNameInvalid: name is not a valid table name.
      CacheTableNotFound: If the table does not exist.

    Returns:
      A Table object for name.
    """
    if name in self._restricted:
      raise exceptions.CacheTableRestricted(
          '[{}] cache table [{}] is restricted.'.format(self.name, name))
    table = self._tables.get(name, None)
    if table:
      if not table.deleted:
        if columns is not None and columns != table.columns:
          raise exceptions.CacheTableColumnsInvalid(
              '[{}] cache table [{}] columns [{}] does not match existing {}.'
              .format(self.name, name, columns, table.columns))
        if keys is not None and keys != table.keys:
          raise exceptions.CacheTableKeysInvalid(
              '[{}] cache table [{}] keys [{}] does not match existing {}.'
              .format(self.name, name, keys, table.keys))
        return table
      if not create:
        raise exceptions.CacheTableNotFound(
            '[{}] cache table [{}] not found.'.format(self.name, name))
    if self._metadata:
      rows = self._metadata.Select(Metadata.Row(name=name))
      row = rows[0] if rows else None
      if row:
        metadata = Metadata(row)
        return self._table_class(self,
                                 name=metadata.name,
                                 columns=metadata.columns,
                                 keys=metadata.keys,
                                 timeout=metadata.timeout,
                                 modified=metadata.modified,
                                 restricted=metadata.restricted)
    if not create:
      raise exceptions.CacheTableNotFound(
          '[{}] cache table [{}] not found.'.format(self.name, name))
    return self._CreateTable(name, restricted, columns, keys, timeout)

  def InitializeMetadata(self):
    """Initializes the metadata table and self._metadata."""
    self.Table('__metadata__', restricted=True, columns=Metadata.COLUMNS,
               keys=1, timeout=0)

  def Select(self, name=None):
    """Returns the list of unrestricted table names matching name.

    Args:
      name: The table name pattern. None for all unrestricted tables. May
        contain the * and ? pattern match characters.

    Returns:
      The list of unrestricted table names matching name.
    """
    rows = self._metadata.Select(Metadata.Row(name=name, restricted=False))
    return [Metadata(row).name for row in rows]
