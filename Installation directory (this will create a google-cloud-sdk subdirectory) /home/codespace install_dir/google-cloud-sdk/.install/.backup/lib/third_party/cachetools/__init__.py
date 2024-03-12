"""Extensible memoizing collections and decorators."""

from __future__ import absolute_import

import functools

from . import keys
from .cache import Cache
from .lfu import LFUCache
from .lru import LRUCache
from .rr import RRCache
from .ttl import TTLCache

__all__ = ('Cache', 'LFUCache', 'LRUCache', 'RRCache', 'TTLCache', 'cached',
           'cachedmethod')

__version__ = '3.1.1'

if hasattr(functools.update_wrapper(lambda f: f(), lambda: 42), '__wrapped__'):
  _update_wrapper = functools.update_wrapper
else:

  def _update_wrapper(wrapper, wrapped):
    functools.update_wrapper(wrapper, wrapped)
    wrapper.__wrapped__ = wrapped
    return wrapper


def cached(cache, key=keys.hashkey, lock=None):
  """Decorator to wrap a function with a memoizing callable that saves

    results in a cache.

    """

  def decorator(func):
    if cache is None:

      def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    elif lock is None:

      def wrapper(*args, **kwargs):
        k = key(*args, **kwargs)
        try:
          return cache[k]
        except KeyError:
          pass  # key not found
        v = func(*args, **kwargs)
        try:
          cache[k] = v
        except ValueError:
          pass  # value too large
        return v
    else:

      def wrapper(*args, **kwargs):
        k = key(*args, **kwargs)
        try:
          with lock:
            return cache[k]
        except KeyError:
          pass  # key not found
        v = func(*args, **kwargs)
        try:
          with lock:
            cache[k] = v
        except ValueError:
          pass  # value too large
        return v

    return _update_wrapper(wrapper, func)

  return decorator


def cachedmethod(cache, key=keys.hashkey, lock=None):
  """Decorator to wrap a class or instance method with a memoizing

    callable that saves results in a cache.

    """

  def decorator(method):
    if lock is None:

      def wrapper(self, *args, **kwargs):
        c = cache(self)
        if c is None:
          return method(self, *args, **kwargs)
        k = key(*args, **kwargs)
        try:
          return c[k]
        except KeyError:
          pass  # key not found
        v = method(self, *args, **kwargs)
        try:
          c[k] = v
        except ValueError:
          pass  # value too large
        return v
    else:

      def wrapper(self, *args, **kwargs):
        c = cache(self)
        if c is None:
          return method(self, *args, **kwargs)
        k = key(*args, **kwargs)
        try:
          with lock(self):
            return c[k]
        except KeyError:
          pass  # key not found
        v = method(self, *args, **kwargs)
        try:
          with lock(self):
            c[k] = v
        except ValueError:
          pass  # value too large
        return v

    return _update_wrapper(wrapper, method)

  return decorator
