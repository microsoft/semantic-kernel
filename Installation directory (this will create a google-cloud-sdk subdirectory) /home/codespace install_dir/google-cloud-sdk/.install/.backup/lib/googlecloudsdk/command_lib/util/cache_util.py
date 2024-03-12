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

"""Common utilities for using the persistent cache."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools

from googlecloudsdk.core import resources
from googlecloudsdk.core.cache import exceptions as cache_exceptions


def CacheResource(table_prefix, timeout_sec=604800):
  """Decorator to cache the result of a function.

  The decorated function must return a resource.

  The returned function will take three arguments:
    cache: a Cache object.
    key: str, the key for the function call in the cache.
    args: tuple (optional), the arguments to pass to the original function. If
      not specified, key will be used.

  >>> @CacheResource('sums')
  ... def Add(value1, value2):
  ...   print 'adding...'
  ...   value = value1 + value2
  ...   return resources.REGISTRY.Parse(str(value), collection='...')
  >>> with cache_util.GetCache('resource://') as cache:
  ...   print Add(cache, '1+4', (1, 4))
  ...   print Add(cache, '1+4', (1, 4))
  adding...
  http://example.googleapis.com/v1/foos/5
  http://example.googleapis.com/v1/foos/5

  Args:
    table_prefix: str, a prefix for the names of the tables in the cache to use
      for these results
    timeout_sec: int, the time (in seconds) for which a table is valid

  Returns:
    function, a function that decorates with the appropriate behavior.
  """
  def Wrapper(func):
    """Wraps a function and caches its result."""
    @functools.wraps(func)
    def GetFromCache(cache, key, args=None):
      table_name = '{}:{}'.format(table_prefix, key)
      table = cache.Table(table_name, columns=1, timeout=timeout_sec)
      try:
        result = table.Select()
      except cache_exceptions.CacheTableExpired:
        args = args if args is not None else (key,)
        ref = func(*args)
        table.AddRows([(ref.SelfLink(),)])
        table.Validate()
        return ref
      else:
        url = result[0][0]
        return resources.REGISTRY.ParseURL(url)

    return GetFromCache
  return Wrapper
