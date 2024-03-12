#!/usr/bin/env python

import unittest

import idna.compat

class IDNACompatTests(unittest.TestCase):

    def testToASCII(self):
        self.assertEqual(idna.compat.ToASCII('\u30c6\u30b9\u30c8.xn--zckzah'), b'xn--zckzah.xn--zckzah')

    def testToUnicode(self):
        self.assertEqual(idna.compat.ToUnicode(b'xn--zckzah.xn--zckzah'), '\u30c6\u30b9\u30c8.\u30c6\u30b9\u30c8')

    def test_nameprep(self):
        self.assertRaises(NotImplementedError, idna.compat.nameprep, "a")

if __name__ == '__main__':
    unittest.main()
