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

"""A persistent cache implementation using files.

See the persistent_cache module for a detailed description.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import fnmatch
import json
import os

from googlecloudsdk.core.cache import exceptions
from googlecloudsdk.core.cache import metadata_table
from googlecloudsdk.core.cache import persistent_cache_base
from googlecloudsdk.core.util import files

import six
from six.moves import range  # pylint: disable=redefined-builtin


class _Table(persistent_cache_base.Table):
  """A persistent cache table.

  Attributes:
    name: The table name.
    deleted: Table was deleted if True.
    restricted: Table is restricted if True.
    modified: Table modify timestamp.
    timeout: Tables older than timeout are invalid.
    _cache: The parent cache object.
    _rows: The list of rows in the table.
  """

  def __init__(self, cache, name, columns=1, keys=1, timeout=0, modified=0,
               restricted=False):
    self._rows = None
    super(_Table, self).__init__(cache, name, columns=columns, keys=keys,
                                 timeout=timeout, modified=modified,
                                 restricted=restricted)
    if restricted:
      self._cache._restricted.add(name)  # pylint: disable=protected-access
    self.deleted = False
    try:
      contents = files.ReadFileContents(
          os.path.join(self._cache.name, self.EncodeName(name)))
    except files.MissingFileError:
      contents = None
      self.changed = True
    except files.Error:
      raise

    if contents:
      self._rows = [tuple(r) for r in json.loads(contents)]
    else:
      self._rows = []
    # pylint: disable=protected-access
    if self._cache._metadata:
      self._cache._tables[name] = self

  def Delete(self):
    """Deletes the table."""
    self.Invalidate()
    self.DeleteRows()
    # pylint: disable=protected-access
    self._cache._metadata.DeleteRows([(self.name,)])
    self.deleted = True

  def _Commit(self):
    """Commits changed/deleted table data to the table file."""
    if self.changed:
      self.changed = False
      path = os.path.join(self._cache.name, self.EncodeName(self.name))
      # pylint: disable=protected-access
      if self.deleted:
        self.deleted = False
        self._cache._metadata.DeleteRows([(self.name,)])
        del self._cache._tables[self.name]
        try:
          os.remove(path)
        except OSError as e:
          # The deleted table might have never been committed.
          if e.errno != errno.ENOENT:
            raise
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
        files.WriteFileContents(path, json.dumps(self._rows))

  def _RowEqual(self, a, b):
    """Returns True if rows a and b have the same key."""
    return a[:self.keys] == b[:self.keys]

  def _RowMatch(self, row_template, row):
    """Returns True if row_template matches row."""
    if row_template:
      for i in range(len(row_template)):
        if row_template[i] is not None:
          if (isinstance(row_template[i], six.string_types) and
              isinstance(row[i], six.string_types)):
            if not fnmatch.fnmatch(row[i], row_template[i]):
              return False
          elif row_template[i] != row[i]:
            return False
    return True

  def _AnyRowMatch(self, row_templates, row):
    """Returns True if any template in row_templates matches row."""
    for row_template in row_templates:
      if self._RowMatch(row_template, row):
        return True
    return False

  def AddRows(self, rows):
    """Adds each row in rows to the table."""
    self._CheckRows(rows)
    self.changed = True
    rows = sorted(self._rows + list(rows), key=lambda x: x[:self.keys])
    self._rows = []
    i = 0
    while i < len(rows):
      # Skip over dup keys, keep the last, which is a new entry thanks to the
      # stable sort above.
      while i < len(rows) - 1 and self._RowEqual(rows[i], rows[i + 1]):
        i += 1
      self._rows.append(rows[i])
      i += 1

  def DeleteRows(self, row_templates=None):
    """Deletes each row in the table matching any of the row_templates."""
    self.changed = True
    if row_templates:
      self._CheckRowTemplates(row_templates)
      keep = []
      for row in self._rows:
        if not self._AnyRowMatch(row_templates, row):
          keep.append(row)
      self._rows = keep
    else:
      self._rows = []

  def Select(self, row_template=None, ignore_expiration=False):
    """Returns the list of rows that match row_template, None for all."""
    if row_template is not None:
      self._CheckRowTemplates([row_template])
    if not ignore_expiration and not self.restricted and not self.modified:
      raise exceptions.CacheTableExpired(
          '[{}] cache table [{}] has expired.'.format(
              self._cache.name, self.name))
    matched = []
    for row in self._rows:
      if row and self._RowMatch(row_template, row):
        matched.append(row)
    return matched


class Cache(metadata_table.CacheUsingMetadataTable):
  """A persistent cache object.

  Attributes:
    name: The db path name. Created/removed by this object. May be a file or
      directory. In this implementation its a file.
    timeout: The default table timeout.
    version: A caller defined version string that must match the version string
      stored when the persistent object was created.
    _lock: The cache lock object. None if no files have been committed yet.
    _lock_path: The cache lock meta file.
    _metadata: The metadata restricted _Table.
    _persistent: True if the persistent object has been committed at least once.
    _restricted: The set of restricted table names.
    _start: The cache instance start time.
    _tables: The map of open table objects.
  """

  def __init__(self, name, create=True, timeout=None, version=None):
    super(Cache, self).__init__(
        _Table, name, create=create, timeout=timeout, version=version)
    lock_name = '__lock__'
    self._restricted = set([lock_name])
    self._tables = {}
    self._metadata = None
    self._start = persistent_cache_base.Now()
    self._lock_path = os.path.join(self.name, lock_name)
    self._lock = None
    self._persistent = False
    if not os.path.exists(self.name):
      if not create:
        raise exceptions.CacheNotFound(
            'Persistent cache [{}] not found.'.format(self.name))
    elif not os.path.exists(self._lock_path):
      raise exceptions.CacheInvalid(
          '[{}] is not a persistent cache.'.format(self.name))
    else:
      # self.name exists and is a directory, and self._lock_path exists.
      self._persistent = True
      self._lock = files.FileLock(self._lock_path, timeout_secs=2)
      self._lock.Lock()
    try:
      self.InitializeMetadata()
    except exceptions.Error:
      # Make sure we clean up any dangling resources.
      self.Close(commit=False)
      raise

  def Delete(self):
    """Permanently deletes the persistent cache."""
    self.Close(commit=False)
    if self._persistent:
      files.RmTree(self.name)
      self._persistent = False

  def Commit(self):
    """Commits all operations up to this point."""
    if not self._lock:
      os.mkdir(self.name, 0o700)
      self._persistent = True
      self._lock = files.FileLock(self._lock_path, timeout_secs=2)
      self._lock.Lock()
    # Update the changed tables.
    for table in list([x for x in self._tables.values() if x.changed]):
      table._Commit()  # pylint: disable=protected-access
    if self._metadata.changed:
      self._metadata._Commit()  # pylint: disable=protected-access

  def Close(self, commit=True):
    """Closes the cache, optionally committing any changes.

    Args:
      commit: Commits any changes before closing if True.
    """
    if commit:
      self.Commit()
    if self._lock:
      self._lock.Unlock()
      self._lock = None
    self._metadata = None
    self._tables = None
