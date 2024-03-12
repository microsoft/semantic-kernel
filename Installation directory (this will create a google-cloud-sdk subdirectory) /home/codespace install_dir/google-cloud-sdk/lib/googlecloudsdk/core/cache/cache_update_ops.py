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

"""Add, replace or delete the cached resource URIs from a single collection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.core.cache import resource_cache

import six


class _TableRows(object):
  """An _UpdateCacheOp._GetTablesFromUris dict entry."""

  def __init__(self, table):
    self.table = table
    self.rows = []


@six.add_metaclass(abc.ABCMeta)
class _UpdateCacheOp(object):
  """The cache update operation base class."""

  def __init__(self, completer):
    self._completer_class = completer

  def Update(self, uris):
    """Applies UpdateRows() to tables that contain the resources uris."""
    try:
      with resource_cache.ResourceCache() as cache:
        completer = self._completer_class(cache=cache)
        tables = {}
        for uri in uris:
          row = completer.StringToRow(uri)
          table = completer.GetTableForRow(row)
          entry = tables.get(table.name)
          if not entry:
            entry = _TableRows(table)
            tables[table.name] = entry
          entry.rows.append(row)
        for table, rows in six.iteritems(tables):
          self.UpdateRows(table, rows)
    except Exception:  # pylint: disable=broad-except
      pass

  @abc.abstractmethod
  def UpdateRows(self, table, rows):
    """Updates table with rows."""
    pass


class AddToCacheOp(_UpdateCacheOp):
  """An AddToCache operation."""

  def UpdateRows(self, table, rows):
    """Adds rows to table."""
    table.AddRows(rows)


class DeleteFromCacheOp(_UpdateCacheOp):
  """A DeleteFromCache operation."""

  def UpdateRows(self, table, rows):
    """Deletes rows from table."""
    table.DeleteRows(rows)


class ReplaceCacheOp(_UpdateCacheOp):
  """A ReplaceCache operation."""

  def UpdateRows(self, table, rows):
    """Replaces table with rows."""
    table.DeleteRows()
    table.AddRows(rows)


class NoCacheUpdater(resource_cache.BaseUpdater):
  """No cache updater."""
