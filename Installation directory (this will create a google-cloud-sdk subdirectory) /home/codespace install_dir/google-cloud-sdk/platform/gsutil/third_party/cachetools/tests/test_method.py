import operator
import unittest

from cachetools import LRUCache, cachedmethod, keys


class Cached:
    def __init__(self, cache, count=0):
        self.cache = cache
        self.count = count

    @cachedmethod(operator.attrgetter("cache"))
    def get(self, value):
        count = self.count
        self.count += 1
        return count

    @cachedmethod(operator.attrgetter("cache"), key=keys.typedkey)
    def get_typed(self, value):
        count = self.count
        self.count += 1
        return count


class Locked:
    def __init__(self, cache):
        self.cache = cache
        self.count = 0

    @cachedmethod(operator.attrgetter("cache"), lock=lambda self: self)
    def get(self, value):
        return self.count

    def __enter__(self):
        self.count += 1

    def __exit__(self, *exc):
        pass


class Unhashable:
    def __init__(self, cache):
        self.cache = cache

    @cachedmethod(operator.attrgetter("cache"))
    def get_default(self, value):
        return value

    @cachedmethod(operator.attrgetter("cache"), key=keys.hashkey)
    def get_hashkey(self, value):
        return value

    # https://github.com/tkem/cachetools/issues/107
    def __hash__(self):
        raise TypeError("unhashable type")


class CachedMethodTest(unittest.TestCase):
    def test_dict(self):
        cached = Cached({})

        self.assertEqual(cached.get(0), 0)
        self.assertEqual(cached.get(1), 1)
        self.assertEqual(cached.get(1), 1)
        self.assertEqual(cached.get(1.0), 1)
        self.assertEqual(cached.get(1.0), 1)

        cached.cache.clear()
        self.assertEqual(cached.get(1), 2)

    def test_typed_dict(self):
        cached = Cached(LRUCache(maxsize=2))

        self.assertEqual(cached.get_typed(0), 0)
        self.assertEqual(cached.get_typed(1), 1)
        self.assertEqual(cached.get_typed(1), 1)
        self.assertEqual(cached.get_typed(1.0), 2)
        self.assertEqual(cached.get_typed(1.0), 2)
        self.assertEqual(cached.get_typed(0.0), 3)
        self.assertEqual(cached.get_typed(0), 4)

    def test_lru(self):
        cached = Cached(LRUCache(maxsize=2))

        self.assertEqual(cached.get(0), 0)
        self.assertEqual(cached.get(1), 1)
        self.assertEqual(cached.get(1), 1)
        self.assertEqual(cached.get(1.0), 1)
        self.assertEqual(cached.get(1.0), 1)

        cached.cache.clear()
        self.assertEqual(cached.get(1), 2)

    def test_typed_lru(self):
        cached = Cached(LRUCache(maxsize=2))

        self.assertEqual(cached.get_typed(0), 0)
        self.assertEqual(cached.get_typed(1), 1)
        self.assertEqual(cached.get_typed(1), 1)
        self.assertEqual(cached.get_typed(1.0), 2)
        self.assertEqual(cached.get_typed(1.0), 2)
        self.assertEqual(cached.get_typed(0.0), 3)
        self.assertEqual(cached.get_typed(0), 4)

    def test_nospace(self):
        cached = Cached(LRUCache(maxsize=0))

        self.assertEqual(cached.get(0), 0)
        self.assertEqual(cached.get(1), 1)
        self.assertEqual(cached.get(1), 2)
        self.assertEqual(cached.get(1.0), 3)
        self.assertEqual(cached.get(1.0), 4)

    def test_nocache(self):
        cached = Cached(None)

        self.assertEqual(cached.get(0), 0)
        self.assertEqual(cached.get(1), 1)
        self.assertEqual(cached.get(1), 2)
        self.assertEqual(cached.get(1.0), 3)
        self.assertEqual(cached.get(1.0), 4)

    def test_weakref(self):
        import weakref
        import fractions
        import gc

        # in Python 3.4, `int` does not support weak references even
        # when subclassed, but Fraction apparently does...
        class Int(fractions.Fraction):
            def __add__(self, other):
                return Int(fractions.Fraction.__add__(self, other))

        cached = Cached(weakref.WeakValueDictionary(), count=Int(0))

        self.assertEqual(cached.get(0), 0)
        gc.collect()
        self.assertEqual(cached.get(0), 1)

        ref = cached.get(1)
        self.assertEqual(ref, 2)
        self.assertEqual(cached.get(1), 2)
        self.assertEqual(cached.get(1.0), 2)

        ref = cached.get_typed(1)
        self.assertEqual(ref, 3)
        self.assertEqual(cached.get_typed(1), 3)
        self.assertEqual(cached.get_typed(1.0), 4)

        cached.cache.clear()
        self.assertEqual(cached.get(1), 5)

    def test_locked_dict(self):
        cached = Locked({})

        self.assertEqual(cached.get(0), 1)
        self.assertEqual(cached.get(1), 3)
        self.assertEqual(cached.get(1), 3)
        self.assertEqual(cached.get(1.0), 3)
        self.assertEqual(cached.get(2.0), 7)

    def test_locked_nocache(self):
        cached = Locked(None)

        self.assertEqual(cached.get(0), 0)
        self.assertEqual(cached.get(1), 0)
        self.assertEqual(cached.get(1), 0)
        self.assertEqual(cached.get(1.0), 0)
        self.assertEqual(cached.get(1.0), 0)

    def test_locked_nospace(self):
        cached = Locked(LRUCache(maxsize=0))

        self.assertEqual(cached.get(0), 1)
        self.assertEqual(cached.get(1), 3)
        self.assertEqual(cached.get(1), 5)
        self.assertEqual(cached.get(1.0), 7)
        self.assertEqual(cached.get(1.0), 9)

    def test_unhashable(self):
        cached = Unhashable(LRUCache(maxsize=0))

        self.assertEqual(cached.get_default(0), 0)
        self.assertEqual(cached.get_default(1), 1)

        with self.assertRaises(TypeError):
            cached.get_hashkey(0)
