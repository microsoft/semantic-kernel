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

"""A persistent cache implementation using sqlite3.

See the persistent_cache module for a detailed description.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import gc
import os

from googlecloudsdk.core.cache import exceptions
from googlecloudsdk.core.cache import metadata_table
from googlecloudsdk.core.cache import persistent_cache_base
from googlecloudsdk.core.util import files

import six
from six.moves import range  # pylint: disable=redefined-builtin
import sqlite3


def _FieldRef(column):
  """Returns a field reference name.

  Args:
    column: The field column number counting from 0.

  Returns:
    A field reference name.
  """
  return 'f{column}'.format(column=column)


def _Where(row_template=None):
  """Returns a WHERE clause for the row template.

  Column string matching supports * and ? match ops.

  Args:
    row_template: A template row tuple. A column value None means match all
      values for this column. A None value for row means all rows.

  Returns:
    A WHERE clause for the row template or the empty string if there is no none.
  """
  terms = []
  if row_template:
    for index in range(len(row_template)):
      term = row_template[index]
      if term is None:
        continue
      if isinstance(term, six.string_types):
        pattern = term.replace('*', '%').replace('.', '_').replace('"', '""')
        terms.append('{field} LIKE "{pattern}"'.format(
            field=_FieldRef(index), pattern=pattern))
      else:
        terms.append('{field} = {term}'.format(
            field=_FieldRef(index), term=term))
  if not terms:
    return ''
  return  ' WHERE ' + ' AND '.join(terms)


class _Table(persistent_cache_base.Table):
  """A persistent cache table.

  Attributes:
    name: The table name.
    deleted: Table was deleted if True.
    modified: Table modify timestamp.
    timeout: Tables older than timeout are invalid.
    _cache: The parent cache object.
    _fields: The f1,... fields name string.
    _values: The ?,... parameter replacement string for INSERT.
  """

  def __init__(self, cache, name, columns=1, keys=1, timeout=0, modified=0,
               restricted=False):
    self._rows = None
    super(_Table, self).__init__(cache, name, columns=columns, keys=keys,
                                 timeout=timeout, modified=modified,
                                 restricted=restricted)
    if restricted:
      self._cache._restricted.add(name)  # pylint: disable=protected-access
    self._fields = ', '.join([_FieldRef(i) for i in range(columns)])
    self._values = ', '.join(['?'] * columns)
    self.deleted = False
    # pylint: disable=protected-access
    if self._cache._metadata:
      self._cache._tables[name] = self

  def Delete(self):
    """Deletes the table."""
    self.Invalidate()
    self._cache.cursor.execute(
        'DROP TABLE "{table}"'.format(table=self.name))
    # pylint: disable=protected-access
    self._cache._db.commit()
    self._cache._metadata.DeleteRows([(self.name,)])
    self.deleted = True

  def _Commit(self):
    """Commits changed/deleted table data."""
    if self.changed:
      self.changed = False
      # pylint: disable=protected-access
      if self.deleted:
        self.deleted = False
        self._cache._metadata.DeleteRows([(self.name,)])
        del self._cache._tables[self.name]
      else:
        self._cache._metadata.AddRows(
            [metadata_table.Metadata.Row(
                name=self.name,
                columns=self.columns,
                keys=self.keys,
                timeout=self.timeout,
                modified=self.modified,
                restricted=self.restricted,
                version=self._cache.version)])

  def AddRows(self, rows):
    """Adds each row in rows to the table."""
    self._CheckRows(rows)
    self._cache.cursor.executemany(
        'INSERT OR REPLACE INTO "{table}" ({fields}) VALUES ({values})'.
        format(
            table=self.name, fields=self._fields, values=self._values),
        rows)
    self._cache._db.commit()  # pylint: disable=protected-access

  def DeleteRows(self, row_templates=None):
    """Deletes each row in the table matching any of the row_templates."""
    if row_templates:
      self._CheckRowTemplates(row_templates)
      for template in row_templates:
        self._cache.cursor.execute(
            'DELETE FROM "{table}"{where}'.format(
                table=self.name, where=_Where(template)))
    else:
      self._cache.cursor.execute(
          'DELETE FROM "{table}" WHERE 1'.format(table=self.name))
    self._cache._db.commit()  # pylint: disable=protected-access

  def Select(self, row_template=None, ignore_expiration=False):
    """Returns the list of rows that match row_template, None for all."""
    if row_template is not None:
      self._CheckRowTemplates([row_template])
    if not ignore_expiration and not self.restricted and not self.modified:
      raise exceptions.CacheTableExpired(
          '[{}] cache table [{}] has expired.'.format(
              self._cache.name, self.name))
    self._cache.cursor.execute(
        'SELECT {fields} FROM "{table}"{where}'.format(
            fields=self._fields, table=self.name, where=_Where(row_template)))
    return self._cache.cursor.fetchall()


class Cache(metadata_table.CacheUsingMetadataTable):
  """A persistent cache object.

  Attributes:
    cursor: The _db operations cursor.
    name: The db path name. Created/removed by this object. May be a file or
      directory. In this implementation its a file.
    timeout: The default table timeout.
    version: A caller defined version string that must match the version string
      stored when the persistent object was created.
    _db: The db connection.
    _metadata: The metadata restricted _Table.
    _persistent: True if the persistent object has been committed at least once.
    _restricted: The set of restricted table names.
    _start: The cache instance start time.
    _tables: The map of open table objects.
  """

  _EXPECTED_MAGIC = b'SQLite format 3'

  def __init__(self, name, create=True, timeout=None, version=None):
    super(Cache, self).__init__(
        _Table, name, create=create, timeout=timeout, version=version)
    self._persistent = False
    # Check if the db file exists and is an sqlite3 db.
    # Surprise, we have to do the heavy lifting.
    # That stops here.
    try:
      with files.BinaryFileReader(name) as f:
        actual_magic = f.read(len(self._EXPECTED_MAGIC))
        if actual_magic != self._EXPECTED_MAGIC:
          raise exceptions.CacheInvalid(
              '[{}] is not a persistent cache.'.format(self.name))
      self._persistent = True
    except files.MissingFileError:
      if not create:
        raise exceptions.CacheNotFound(
            'Persistent cache [{}] not found.'.format(self.name))
    except files.Error:
      raise exceptions.CacheInvalid(
          '[{}] is not a persistent cache.'.format(self.name))
    self._db = sqlite3.connect(name)
    self.cursor = self._db.cursor()
    self._restricted = set(['__lock__'])
    self._tables = {}
    self._metadata = None
    self._start = persistent_cache_base.Now()
    try:
      self.InitializeMetadata()
    except exceptions.Error:
      # Make sure we clean up any dangling resources.
      self.Close(commit=False)
      raise

  def _DeleteCacheFile(self):
    """Permanently deletes the persistent cache file."""
    try:
      os.remove(self.name)
    except OSError as e:
      if e.errno not in (errno.ENOENT, errno.EISDIR):
        raise

  def Delete(self):
    """Closes and permanently deletes the persistent cache."""
    self.Close(commit=False)
    self._DeleteCacheFile()

  def Commit(self):
    """Commits all operations up to this point."""
    # Update the changed tables.
    for table in [x for x in self._tables.values() if x.changed]:
      table._Commit()  # pylint: disable=protected-access
    if self._metadata.changed:
      self._metadata._Commit()  # pylint: disable=protected-access
    self._db.commit()
    self._persistent = True

  def Close(self, commit=True):
    """Closes the cache, optionally committing any changes.

    Args:
      commit: Commits any changes before closing if True.
    """
    if self._db:
      if commit:
        self.Commit()
      del self.cursor
      self._db.close()
      self._db = None
      gc.collect(2)  # On Windows, connection refs sometimes remain in memory
      # and prevent the db file from being deleted. This gets rid of them.
      self._tables = None
      if not commit and not self._persistent:
        # Need this because sqlite3 creates a filesystem artifact even if there
        # were no commits.
        self._DeleteCacheFile()

  def _ImplementationCreateTable(self, name, columns, keys):
    """sqlite3 implementation specific _CreateTable."""
    field_list = [_FieldRef(i) for i in range(columns)]
    key_list = [_FieldRef(i) for i in range(keys or 1)]
    field_list.append('PRIMARY KEY ({keys})'.format(keys=', '.join(key_list)))
    fields = '({fields})'.format(fields=', '.join(field_list))
    self.cursor.execute(
        'CREATE TABLE IF NOT EXISTS "{name}" {fields}'.format(
            name=name, fields=fields))
