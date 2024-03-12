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

"""Exceptions for the Cloud SDK persistent cache module."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Error(Exception):
  """Base for all persistent cache exceptions."""


class CacheVersionMismatch(Error):
  """Cache version mismatch."""

  def __init__(self, message, actual, requested):
    super(CacheVersionMismatch, self).__init__(message)
    self.actual = actual
    self.requested = requested


class CacheInvalid(Error):
  """Cach object is invalid."""


class CacheNameInvalid(Error):
  """Name is not a valid cache name."""


class CacheNotFound(Error):
  """Cache not found."""


class CacheTableDeleted(Error):
  """Cache table deleted."""


class CacheTableExpired(Error):
  """Cache table expired."""


class CacheTableRestricted(Error):
  """Cache table is restricted."""


class CacheTableNameInvalid(Error):
  """Cache table invalid table name."""


class CacheTableColumnsInvalid(Error):
  """Cache table columns invalid."""


class CacheTableKeysInvalid(Error):
  """Cache table keys invalid."""


class CacheTableNotFound(Error):
  """Cache table not found."""


class CacheTableRowSizeInvalid(Error):
  """Cache table row has incorrect size."""
