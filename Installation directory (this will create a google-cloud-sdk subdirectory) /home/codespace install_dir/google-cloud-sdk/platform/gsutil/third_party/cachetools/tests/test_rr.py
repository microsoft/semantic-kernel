import unittest

from cachetools import RRCache

from . import CacheTestMixin


class RRCacheTest(unittest.TestCase, CacheTestMixin):

    Cache = RRCache

    def test_rr(self):
        cache = RRCache(maxsize=2, choice=min)
        self.assertEqual(min, cache.choice)

        cache[1] = 1
        cache[2] = 2
        cache[3] = 3

        self.assertEqual(2, len(cache))
        self.assertEqual(2, cache[2])
        self.assertEqual(3, cache[3])
        self.assertNotIn(1, cache)

        cache[0] = 0
        self.assertEqual(2, len(cache))
        self.assertEqual(0, cache[0])
        self.assertEqual(3, cache[3])
        self.assertNotIn(2, cache)

        cache[4] = 4
        self.assertEqual(2, len(cache))
        self.assertEqual(3, cache[3])
        self.assertEqual(4, cache[4])
        self.assertNotIn(0, cache)
