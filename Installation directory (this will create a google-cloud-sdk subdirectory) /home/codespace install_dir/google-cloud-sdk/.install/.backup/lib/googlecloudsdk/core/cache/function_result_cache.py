# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for caching the result of function calls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools


class FakeLruCache:
  """Doesn't actually cache but supports LRU interface in Python 2."""

  def __init__(self, function):
    self._function = function

  def cache_clear(self):
    """Exposes this function of actual LRU to avoid missing attribute errors."""
    pass

  def __call__(self, *args, **kwargs):
    return self._function(*args, **kwargs)


def lru(maxsize=128):
  """Returns cached result if function was run with same args before.

  Wraps functools.lru_cache, so it's not referenced at import in Python 2 and
  unsupported Python 3 distributions.

  Args:
    maxsize (int|None): From Python functools docs: "...saves up to the maxsize
      most recent calls... If maxsize is set to None, the LRU feature is
      disabled and the cache can grow without bound."

  Returns:
    Wrapped functools.lru_cache.
  """

  def _wrapper(function):
    if getattr(functools, 'lru_cache', None):
      return functools.lru_cache(maxsize=maxsize)(function)
    return FakeLruCache(function)

  return _wrapper
