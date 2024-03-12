import unittest

from cachetools import MRUCache

from . import CacheTestMixin


class MRUCacheTest(unittest.TestCase, CacheTestMixin):

    Cache = MRUCache

    def test_evict__writes_only(self):
        cache = MRUCache(maxsize=2)

        cache[1] = 1
        cache[2] = 2
        cache[3] = 3  # Evicts 1 because nothing's been used yet

        assert len(cache) == 2
        assert 1 not in cache, "Wrong key was evicted. Should have been '1'."
        assert 2 in cache
        assert 3 in cache

    def test_evict__with_access(self):
        cache = MRUCache(maxsize=2)

        cache[1] = 1
        cache[2] = 2
        cache[1]
        cache[2]
        cache[3] = 3  # Evicts 2
        assert 2 not in cache, "Wrong key was evicted. Should have been '2'."
        assert 1 in cache
        assert 3 in cache

    def test_evict__with_delete(self):
        cache = MRUCache(maxsize=2)

        cache[1] = 1
        cache[2] = 2
        del cache[2]
        cache[3] = 3  # Doesn't evict anything because we just deleted 2

        assert 2 not in cache
        assert 1 in cache

        cache[4] = 4  # Should evict 1 as we just accessed it with __contains__
        assert 1 not in cache
        assert 3 in cache
        assert 4 in cache
