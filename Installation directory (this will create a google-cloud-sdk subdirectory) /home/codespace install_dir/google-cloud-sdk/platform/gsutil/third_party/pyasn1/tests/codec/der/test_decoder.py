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

from pyasn1.codec.der import decoder
from pyasn1.compat.octets import ints2octs, null
from pyasn1.error import PyAsn1Error


class BitStringDecoderTestCase(BaseTestCase):
    def testShortMode(self):
        assert decoder.decode(
            ints2octs((3, 127, 6) + (170,) * 125 + (128,))
        ) == (((1, 0) * 501), null)

    def testIndefMode(self):
        try:
            decoder.decode(
                ints2octs((35, 128, 3, 2, 0, 169, 3, 2, 1, 138, 0, 0))
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'indefinite length encoding tolerated'

    def testDefModeChunked(self):
        try:
            assert decoder.decode(
                ints2octs((35, 8, 3, 2, 0, 169, 3, 2, 1, 138))
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'chunked encoding tolerated'


class OctetStringDecoderTestCase(BaseTestCase):
    def testShortMode(self):
        assert decoder.decode(
            '\004\017Quick brown fox'.encode()
        ) == ('Quick brown fox'.encode(), ''.encode())

    def testIndefMode(self):
        try:
            decoder.decode(
                ints2octs((36, 128, 4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120, 0, 0))
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'indefinite length encoding tolerated'

    def testChunkedMode(self):
        try:
            decoder.decode(
                ints2octs((36, 23, 4, 2, 81, 117, 4, 2, 105, 99, 4, 2, 107, 32, 4, 2, 98, 114, 4, 2, 111, 119, 4, 1, 110))
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'chunked encoding tolerated'


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
