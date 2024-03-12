import unittest

import cachetools.func


class DecoratorTestMixin:
    def decorator(self, maxsize, **kwargs):
        return self.DECORATOR(maxsize, **kwargs)

    def test_decorator(self):
        cached = self.decorator(maxsize=2)(lambda n: n)
        self.assertEqual(cached.cache_parameters(), {"maxsize": 2, "typed": False})
        self.assertEqual(cached.cache_info(), (0, 0, 2, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 1, 2, 1))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (1, 1, 2, 1))
        self.assertEqual(cached(1.0), 1.0)
        self.assertEqual(cached.cache_info(), (2, 1, 2, 1))

    def test_decorator_clear(self):
        cached = self.decorator(maxsize=2)(lambda n: n)
        self.assertEqual(cached.cache_parameters(), {"maxsize": 2, "typed": False})
        self.assertEqual(cached.cache_info(), (0, 0, 2, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 1, 2, 1))
        cached.cache_clear()
        self.assertEqual(cached.cache_info(), (0, 0, 2, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 1, 2, 1))

    def test_decorator_nocache(self):
        cached = self.decorator(maxsize=0)(lambda n: n)
        self.assertEqual(cached.cache_parameters(), {"maxsize": 0, "typed": False})
        self.assertEqual(cached.cache_info(), (0, 0, 0, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 1, 0, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 2, 0, 0))
        self.assertEqual(cached(1.0), 1.0)
        self.assertEqual(cached.cache_info(), (0, 3, 0, 0))

    def test_decorator_unbound(self):
        cached = self.decorator(maxsize=None)(lambda n: n)
        self.assertEqual(cached.cache_parameters(), {"maxsize": None, "typed": False})
        self.assertEqual(cached.cache_info(), (0, 0, None, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 1, None, 1))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (1, 1, None, 1))
        self.assertEqual(cached(1.0), 1.0)
        self.assertEqual(cached.cache_info(), (2, 1, None, 1))

    def test_decorator_typed(self):
        cached = self.decorator(maxsize=2, typed=True)(lambda n: n)
        self.assertEqual(cached.cache_parameters(), {"maxsize": 2, "typed": True})
        self.assertEqual(cached.cache_info(), (0, 0, 2, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 1, 2, 1))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (1, 1, 2, 1))
        self.assertEqual(cached(1.0), 1.0)
        self.assertEqual(cached.cache_info(), (1, 2, 2, 2))
        self.assertEqual(cached(1.0), 1.0)
        self.assertEqual(cached.cache_info(), (2, 2, 2, 2))

    def test_decorator_user_function(self):
        cached = self.decorator(lambda n: n)
        self.assertEqual(cached.cache_parameters(), {"maxsize": 128, "typed": False})
        self.assertEqual(cached.cache_info(), (0, 0, 128, 0))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (0, 1, 128, 1))
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached.cache_info(), (1, 1, 128, 1))
        self.assertEqual(cached(1.0), 1.0)
        self.assertEqual(cached.cache_info(), (2, 1, 128, 1))

    def test_decorator_needs_rlock(self):
        cached = self.decorator(lambda n: n)

        class RecursiveEquals:
            def __init__(self, use_cache):
                self._use_cache = use_cache

            def __hash__(self):
                return hash(self._use_cache)

            def __eq__(self, other):
                if self._use_cache:
                    # This call will happen while the cache-lock is held,
                    # requiring a reentrant lock to avoid deadlock.
                    cached(self)
                return self._use_cache == other._use_cache

        # Prime the cache.
        cached(RecursiveEquals(False))
        cached(RecursiveEquals(True))
        # Then do a call which will cause a deadlock with a non-reentrant lock.
        self.assertEqual(cached(RecursiveEquals(True)), RecursiveEquals(True))


class FIFODecoratorTest(unittest.TestCase, DecoratorTestMixin):

    DECORATOR = staticmethod(cachetools.func.fifo_cache)


class LFUDecoratorTest(unittest.TestCase, DecoratorTestMixin):

    DECORATOR = staticmethod(cachetools.func.lfu_cache)


class LRUDecoratorTest(unittest.TestCase, DecoratorTestMixin):

    DECORATOR = staticmethod(cachetools.func.lru_cache)


class MRUDecoratorTest(unittest.TestCase, DecoratorTestMixin):

    DECORATOR = staticmethod(cachetools.func.mru_cache)


class RRDecoratorTest(unittest.TestCase, DecoratorTestMixin):

    DECORATOR = staticmethod(cachetools.func.rr_cache)


class TTLDecoratorTest(unittest.TestCase, DecoratorTestMixin):

    DECORATOR = staticmethod(cachetools.func.ttl_cache)
