import unittest

import cachetools

from . import CacheTestMixin


class CacheTest(unittest.TestCase, CacheTestMixin):

    Cache = cachetools.Cache
