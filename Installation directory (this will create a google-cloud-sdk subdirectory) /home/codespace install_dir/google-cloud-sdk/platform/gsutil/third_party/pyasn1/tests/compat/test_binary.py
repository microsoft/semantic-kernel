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

from pyasn1.compat import binary


class BinaryTestCase(BaseTestCase):

    def test_bin_zero(self):
        assert '0b0' == binary.bin(0)


    def test_bin_noarg(self):
        try:
            binary.bin()

        except TypeError:
            pass

        except:
            assert 0, 'bin() tolerates no arguments'


    def test_bin_allones(self):
        assert '0b1111111111111111111111111111111111111111111111111111111111111111' == binary.bin(0xffffffffffffffff)


    def test_bin_allzeros(self):
        assert '0b0' == binary.bin(0x0000000)



    def test_bin_pos(self):
        assert '0b1000000010000000100000001' == binary.bin(0x01010101)


    def test_bin_neg(self):
        assert '-0b1000000010000000100000001' == binary.bin(-0x01010101)


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
