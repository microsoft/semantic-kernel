import unittest

import cachetools.keys


class CacheKeysTest(unittest.TestCase):
    def test_hashkey(self, key=cachetools.keys.hashkey):
        self.assertEqual(key(), key())
        self.assertEqual(hash(key()), hash(key()))
        self.assertEqual(key(1, 2, 3), key(1, 2, 3))
        self.assertEqual(hash(key(1, 2, 3)), hash(key(1, 2, 3)))
        self.assertEqual(key(1, 2, 3, x=0), key(1, 2, 3, x=0))
        self.assertEqual(hash(key(1, 2, 3, x=0)), hash(key(1, 2, 3, x=0)))
        self.assertNotEqual(key(1, 2, 3), key(3, 2, 1))
        self.assertNotEqual(key(1, 2, 3), key(1, 2, 3, x=None))
        self.assertNotEqual(key(1, 2, 3, x=0), key(1, 2, 3, x=None))
        self.assertNotEqual(key(1, 2, 3, x=0), key(1, 2, 3, y=0))
        with self.assertRaises(TypeError):
            hash(key({}))
        # untyped keys compare equal
        self.assertEqual(key(1, 2, 3), key(1.0, 2.0, 3.0))
        self.assertEqual(hash(key(1, 2, 3)), hash(key(1.0, 2.0, 3.0)))

    def test_typedkey(self, key=cachetools.keys.typedkey):
        self.assertEqual(key(), key())
        self.assertEqual(hash(key()), hash(key()))
        self.assertEqual(key(1, 2, 3), key(1, 2, 3))
        self.assertEqual(hash(key(1, 2, 3)), hash(key(1, 2, 3)))
        self.assertEqual(key(1, 2, 3, x=0), key(1, 2, 3, x=0))
        self.assertEqual(hash(key(1, 2, 3, x=0)), hash(key(1, 2, 3, x=0)))
        self.assertNotEqual(key(1, 2, 3), key(3, 2, 1))
        self.assertNotEqual(key(1, 2, 3), key(1, 2, 3, x=None))
        self.assertNotEqual(key(1, 2, 3, x=0), key(1, 2, 3, x=None))
        self.assertNotEqual(key(1, 2, 3, x=0), key(1, 2, 3, y=0))
        with self.assertRaises(TypeError):
            hash(key({}))
        # typed keys compare unequal
        self.assertNotEqual(key(1, 2, 3), key(1.0, 2.0, 3.0))

    def test_addkeys(self, key=cachetools.keys.hashkey):
        self.assertIsInstance(key(), tuple)
        self.assertIsInstance(key(1, 2, 3) + key(4, 5, 6), type(key()))
        self.assertIsInstance(key(1, 2, 3) + (4, 5, 6), type(key()))
        self.assertIsInstance((1, 2, 3) + key(4, 5, 6), type(key()))

    def test_pickle(self, key=cachetools.keys.hashkey):
        import pickle

        for k in [key(), key("abc"), key("abc", 123), key("abc", q="abc")]:
            # white-box test: assert cached hash value is not pickled
            self.assertEqual(len(k.__dict__), 0)
            h = hash(k)
            self.assertEqual(len(k.__dict__), 1)
            pickled = pickle.loads(pickle.dumps(k))
            self.assertEqual(len(pickled.__dict__), 0)
            self.assertEqual(k, pickled)
            self.assertEqual(h, hash(pickled))
