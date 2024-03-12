v5.0.0 (2021-12-21)
===================

- Require Python 3.7 or later (breaking change).

- Remove deprecated submodules (breaking change).

  The ``cache``, ``fifo``, ``lfu``, ``lru``, ``mru``, ``rr`` and
  ``ttl`` submodules have been deleted.  Therefore, statements like

  ``from cachetools.ttl import TTLCache``

  will no longer work. Use

  ``from cachetools import TTLCache``

  instead.

- Pass ``self`` to ``@cachedmethod`` key function (breaking change).

  The ``key`` function passed to the ``@cachedmethod`` decorator is
  now called as ``key(self, *args, **kwargs)``.

  The default key function has been changed to ignore its first
  argument, so this should only affect applications using custom key
  functions with the ``@cachedmethod`` decorator.

- Change exact time of expiration in ``TTLCache`` (breaking change).

  ``TTLCache`` items now get expired if their expiration time is less
  than *or equal to* ``timer()``.  For applications using the default
  ``timer()``, this should be barely noticable, but it may affect the
  use of custom timers with larger tick intervals.  Note that this
  also implies that a ``TTLCache`` with ``ttl=0`` can no longer hold
  any items, since they will expire immediately.

- Change ``Cache.__repr__()`` format (breaking change).

  String representations of cache instances now use a more compact and
  efficient format, e.g.

  ``LRUCache({1: 1, 2: 2}, maxsize=10, currsize=2)``

- Add TLRU cache implementation.

- Documentation improvements.


v4.2.4 (2021-09-30)
===================

- Add submodule shims for backward compatibility.


v4.2.3 (2021-09-29)
===================

- Add documentation and tests for using ``TTLCache`` with
  ``datetime``.

- Link to typeshed typing stubs.

- Flatten package file hierarchy.


v4.2.2 (2021-04-27)
===================

- Update build environment.

- Remove Python 2 remnants.

- Format code with Black.


v4.2.1 (2021-01-24)
===================

- Handle ``__missing__()`` not storing cache items.

- Clean up ``__missing__()`` example.


v4.2.0 (2020-12-10)
===================

- Add FIFO cache implementation.

- Add MRU cache implementation.

- Improve behavior of decorators in case of race conditions.

- Improve documentation regarding mutability of caches values and use
  of key functions with decorators.

- Officially support Python 3.9.


v4.1.1 (2020-06-28)
===================

- Improve ``popitem()`` exception context handling.

- Replace ``float('inf')`` with ``math.inf``.

- Improve "envkey" documentation example.


v4.1.0 (2020-04-08)
===================

- Support ``user_function`` with ``cachetools.func`` decorators
  (Python 3.8 compatibility).

- Support ``cache_parameters()`` with ``cachetools.func`` decorators
  (Python 3.9 compatibility).


v4.0.0 (2019-12-15)
===================

- Require Python 3.5 or later.


v3.1.1 (2019-05-23)
===================

- Document how to use shared caches with ``@cachedmethod``.

- Fix pickling/unpickling of cache keys


v3.1.0 (2019-01-29)
===================

- Fix Python 3.8 compatibility issue.

- Use ``time.monotonic`` as default timer if available.

- Improve documentation regarding thread safety.


v3.0.0 (2018-11-04)
===================

- Officially support Python 3.7.

- Drop Python 3.3 support (breaking change).

- Remove ``missing`` cache constructor parameter (breaking change).

- Remove ``self`` from ``@cachedmethod`` key arguments (breaking
  change).

- Add support for ``maxsize=None`` in ``cachetools.func`` decorators.


v2.1.0 (2018-05-12)
===================

- Deprecate ``missing`` cache constructor parameter.

- Handle overridden ``getsizeof()`` method in subclasses.

- Fix Python 2.7 ``RRCache`` pickling issues.

- Various documentation improvements.


v2.0.1 (2017-08-11)
===================

- Officially support Python 3.6.

- Move documentation to RTD.

- Documentation: Update import paths for key functions (courtesy of
  slavkoja).


v2.0.0 (2016-10-03)
===================

- Drop Python 3.2 support (breaking change).

- Drop support for deprecated features (breaking change).

- Move key functions to separate package (breaking change).

- Accept non-integer ``maxsize`` in ``Cache.__repr__()``.


v1.1.6 (2016-04-01)
===================

- Reimplement ``LRUCache`` and ``TTLCache`` using
  ``collections.OrderedDict``.  Note that this will break pickle
  compatibility with previous versions.

- Fix ``TTLCache`` not calling ``__missing__()`` of derived classes.

- Handle ``ValueError`` in ``Cache.__missing__()`` for consistency
  with caching decorators.

- Improve how ``TTLCache`` handles expired items.

- Use ``Counter.most_common()`` for ``LFUCache.popitem()``.


v1.1.5 (2015-10-25)
===================

- Refactor ``Cache`` base class.  Note that this will break pickle
  compatibility with previous versions.

- Clean up ``LRUCache`` and ``TTLCache`` implementations.


v1.1.4 (2015-10-24)
===================

- Refactor ``LRUCache`` and ``TTLCache`` implementations.  Note that
  this will break pickle compatibility with previous versions.

- Document pending removal of deprecated features.

- Minor documentation improvements.


v1.1.3 (2015-09-15)
===================

- Fix pickle tests.


v1.1.2 (2015-09-15)
===================

- Fix pickling of large ``LRUCache`` and ``TTLCache`` instances.


v1.1.1 (2015-09-07)
===================

- Improve key functions.

- Improve documentation.

- Improve unit test coverage.


v1.1.0 (2015-08-28)
===================

- Add ``@cached`` function decorator.

- Add ``hashkey`` and ``typedkey`` fuctions.

- Add `key` and `lock` arguments to ``@cachedmethod``.

- Set ``__wrapped__`` attributes for Python versions < 3.2.

- Move ``functools`` compatible decorators to ``cachetools.func``.

- Deprecate ``@cachedmethod`` `typed` argument.

- Deprecate `cache` attribute for ``@cachedmethod`` wrappers.

- Deprecate `getsizeof` and `lock` arguments for `cachetools.func`
  decorator.


v1.0.3 (2015-06-26)
===================

- Clear cache statistics when calling ``clear_cache()``.


v1.0.2 (2015-06-18)
===================

- Allow simple cache instances to be pickled.

- Refactor ``Cache.getsizeof`` and ``Cache.missing`` default
  implementation.


v1.0.1 (2015-06-06)
===================

- Code cleanup for improved PEP 8 conformance.

- Add documentation and unit tests for using ``@cachedmethod`` with
  generic mutable mappings.

- Improve documentation.


v1.0.0 (2014-12-19)
===================

- Provide ``RRCache.choice`` property.

- Improve documentation.


v0.8.2 (2014-12-15)
===================

- Use a ``NestedTimer`` for ``TTLCache``.


v0.8.1 (2014-12-07)
===================

- Deprecate ``Cache.getsize()``.


v0.8.0 (2014-12-03)
===================

- Ignore ``ValueError`` raised on cache insertion in decorators.

- Add ``Cache.getsize()``.

- Add ``Cache.__missing__()``.

- Feature freeze for `v1.0`.


v0.7.1 (2014-11-22)
===================

- Fix `MANIFEST.in`.


v0.7.0 (2014-11-12)
===================

- Deprecate ``TTLCache.ExpiredError``.

- Add `choice` argument to ``RRCache`` constructor.

- Refactor ``LFUCache``, ``LRUCache`` and ``TTLCache``.

- Use custom ``NullContext`` implementation for unsynchronized
  function decorators.


v0.6.0 (2014-10-13)
===================

- Raise ``TTLCache.ExpiredError`` for expired ``TTLCache`` items.

- Support unsynchronized function decorators.

- Allow ``@cachedmethod.cache()`` to return None


v0.5.1 (2014-09-25)
===================

- No formatting of ``KeyError`` arguments.

- Update ``README.rst``.


v0.5.0 (2014-09-23)
===================

- Do not delete expired items in TTLCache.__getitem__().

- Add ``@ttl_cache`` function decorator.

- Fix public ``getsizeof()`` usage.


v0.4.0 (2014-06-16)
===================

- Add ``TTLCache``.

- Add ``Cache`` base class.

- Remove ``@cachedmethod`` `lock` parameter.


v0.3.1 (2014-05-07)
===================

- Add proper locking for ``cache_clear()`` and ``cache_info()``.

- Report `size` in ``cache_info()``.


v0.3.0 (2014-05-06)
===================

- Remove ``@cache`` decorator.

- Add ``size``, ``getsizeof`` members.

- Add ``@cachedmethod`` decorator.


v0.2.0 (2014-04-02)
===================

- Add ``@cache`` decorator.

- Update documentation.


v0.1.0 (2014-03-27)
===================

- Initial release.
