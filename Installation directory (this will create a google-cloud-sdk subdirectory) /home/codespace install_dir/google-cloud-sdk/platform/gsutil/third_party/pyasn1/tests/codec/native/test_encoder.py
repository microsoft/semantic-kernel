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

from pyasn1.type import namedtype
from pyasn1.type import univ
from pyasn1.codec.native import encoder
from pyasn1.compat.octets import str2octs
from pyasn1.error import PyAsn1Error


class BadAsn1SpecTestCase(BaseTestCase):
    def testBadValueType(self):
        try:
            encoder.encode('not an Asn1Item')

        except PyAsn1Error:
            pass

        else:
            assert 0, 'Invalid value type accepted'


class IntegerEncoderTestCase(BaseTestCase):
    def testPosInt(self):
        assert encoder.encode(univ.Integer(12)) == 12

    def testNegInt(self):
        assert encoder.encode(univ.Integer(-12)) == -12


class BooleanEncoderTestCase(BaseTestCase):
    def testTrue(self):
        assert encoder.encode(univ.Boolean(1)) is True

    def testFalse(self):
        assert encoder.encode(univ.Boolean(0)) is False


class BitStringEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.b = univ.BitString((1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1))

    def testValue(self):
        assert encoder.encode(self.b) == '101010011000101'


class OctetStringEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.o = univ.OctetString('Quick brown fox')

    def testValue(self):
        assert encoder.encode(self.o) == str2octs('Quick brown fox')


class NullEncoderTestCase(BaseTestCase):
    def testNull(self):
        assert encoder.encode(univ.Null('')) is None


class ObjectIdentifierEncoderTestCase(BaseTestCase):
    def testOne(self):
        assert encoder.encode(univ.ObjectIdentifier((1, 3, 6, 0, 12345))) == '1.3.6.0.12345'


class RealEncoderTestCase(BaseTestCase):
    def testChar(self):
        assert encoder.encode(univ.Real((123, 10, 11))) == 1.23e+13

    def testPlusInf(self):
        assert encoder.encode(univ.Real('inf')) == float('inf')

    def testMinusInf(self):
        assert encoder.encode(univ.Real('-inf')) == float('-inf')


class SequenceEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        self.s = univ.Sequence(componentType=namedtype.NamedTypes(
            namedtype.NamedType('place-holder', univ.Null('')),
            namedtype.OptionalNamedType('first-name', univ.OctetString('')),
            namedtype.DefaultedNamedType('age', univ.Integer(33)),
        ))

    def testSimple(self):
        s = self.s.clone()
        s[0] = univ.Null('')
        s[1] = 'abc'
        s[2] = 123
        assert encoder.encode(s) == {'place-holder': None, 'first-name': str2octs('abc'), 'age': 123}


class ChoiceEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        self.s = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('place-holder', univ.Null('')),
                namedtype.NamedType('number', univ.Integer(0)),
                namedtype.NamedType('string', univ.OctetString())
           )
        )

    def testEmpty(self):
        try:
            encoder.encode(self.s)
        except PyAsn1Error:
            pass
        else:
            assert False, 'encoded unset choice'

    def testFilled(self):
        self.s.setComponentByPosition(0, univ.Null(''))
        assert encoder.encode(self.s) == {'place-holder': None}


class AnyEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Any(encoder.encode(univ.OctetString('fox')))

    def testSimple(self):
        assert encoder.encode(self.s) == str2octs('fox')


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
