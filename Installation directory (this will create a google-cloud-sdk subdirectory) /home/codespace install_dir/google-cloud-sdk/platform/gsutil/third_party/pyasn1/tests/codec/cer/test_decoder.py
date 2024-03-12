#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/pyasn1/license.html
#
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from tests.base import BaseTestCase

from pyasn1.codec.cer import decoder
from pyasn1.compat.octets import ints2octs, str2octs, null
from pyasn1.error import PyAsn1Error


class BooleanDecoderTestCase(BaseTestCase):
    def testTrue(self):
        assert decoder.decode(ints2octs((1, 1, 255))) == (1, null)

    def testFalse(self):
        assert decoder.decode(ints2octs((1, 1, 0))) == (0, null)

    def testEmpty(self):
        try:
            decoder.decode(ints2octs((1, 0)))
        except PyAsn1Error:
            pass

    def testOverflow(self):
        try:
            decoder.decode(ints2octs((1, 2, 0, 0)))
        except PyAsn1Error:
            pass

class BitStringDecoderTestCase(BaseTestCase):
    def testShortMode(self):
        assert decoder.decode(
            ints2octs((3, 3, 6, 170, 128))
        ) == (((1, 0) * 5), null)

    def testLongMode(self):
        assert decoder.decode(
            ints2octs((3, 127, 6) + (170,) * 125 + (128,))
        ) == (((1, 0) * 501), null)

    # TODO: test failures on short chunked and long unchunked substrate samples


class OctetStringDecoderTestCase(BaseTestCase):
    def testShortMode(self):
        assert decoder.decode(
            ints2octs((4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120)),
        ) == (str2octs('Quick brown fox'), null)

    def testLongMode(self):
        assert decoder.decode(
            ints2octs((36, 128, 4, 130, 3, 232) + (81,) * 1000 + (4, 1, 81, 0, 0))
        ) == (str2octs('Q' * 1001), null)

    # TODO: test failures on short chunked and long unchunked substrate samples


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
