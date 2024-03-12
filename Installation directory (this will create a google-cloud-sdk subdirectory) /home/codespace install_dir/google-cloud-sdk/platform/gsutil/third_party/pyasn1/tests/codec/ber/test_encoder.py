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

from pyasn1.type import tag
from pyasn1.type import namedtype
from pyasn1.type import opentype
from pyasn1.type import univ
from pyasn1.type import char
from pyasn1.codec.ber import encoder
from pyasn1.compat.octets import ints2octs
from pyasn1.error import PyAsn1Error


class LargeTagEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        self.o = univ.Integer().subtype(
            value=1, explicitTag=tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 0xdeadbeaf)
        )

    def testEncoder(self):
        assert encoder.encode(self.o) == ints2octs((127, 141, 245, 182, 253, 47, 3, 2, 1, 1))


class IntegerEncoderTestCase(BaseTestCase):
    def testPosInt(self):
        assert encoder.encode(univ.Integer(12)) == ints2octs((2, 1, 12))

    def testNegInt(self):
        assert encoder.encode(univ.Integer(-12)) == ints2octs((2, 1, 244))

    def testZero(self):
        assert encoder.encode(univ.Integer(0)) == ints2octs((2, 1, 0))

    def testCompactZero(self):
        encoder.IntegerEncoder.supportCompactZero = True
        substrate = encoder.encode(univ.Integer(0))
        encoder.IntegerEncoder.supportCompactZero = False
        assert substrate == ints2octs((2, 0))

    def testMinusOne(self):
        assert encoder.encode(univ.Integer(-1)) == ints2octs((2, 1, 255))

    def testPosLong(self):
        assert encoder.encode(
            univ.Integer(0xffffffffffffffff)
        ) == ints2octs((2, 9, 0, 255, 255, 255, 255, 255, 255, 255, 255))

    def testNegLong(self):
        assert encoder.encode(
            univ.Integer(-0xffffffffffffffff)
        ) == ints2octs((2, 9, 255, 0, 0, 0, 0, 0, 0, 0, 1))


class IntegerEncoderWithSchemaTestCase(BaseTestCase):
    def testPosInt(self):
        assert encoder.encode(12, asn1Spec=univ.Integer()) == ints2octs((2, 1, 12))

    def testNegInt(self):
        assert encoder.encode(-12, asn1Spec=univ.Integer()) == ints2octs((2, 1, 244))

    def testZero(self):
        assert encoder.encode(0, asn1Spec=univ.Integer()) == ints2octs((2, 1, 0))

    def testPosLong(self):
        assert encoder.encode(
            0xffffffffffffffff, asn1Spec=univ.Integer()
        ) == ints2octs((2, 9, 0, 255, 255, 255, 255, 255, 255, 255, 255))


class BooleanEncoderTestCase(BaseTestCase):
    def testTrue(self):
        assert encoder.encode(univ.Boolean(1)) == ints2octs((1, 1, 1))

    def testFalse(self):
        assert encoder.encode(univ.Boolean(0)) == ints2octs((1, 1, 0))


class BooleanEncoderWithSchemaTestCase(BaseTestCase):
    def testTrue(self):
        assert encoder.encode(True, asn1Spec=univ.Boolean()) == ints2octs((1, 1, 1))

    def testFalse(self):
        assert encoder.encode(False, asn1Spec=univ.Boolean()) == ints2octs((1, 1, 0))


class BitStringEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.b = univ.BitString((1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1))

    def testDefMode(self):
        assert encoder.encode(self.b) == ints2octs((3, 3, 1, 169, 138))

    def testIndefMode(self):
        assert encoder.encode(
            self.b, defMode=False
        ) == ints2octs((3, 3, 1, 169, 138))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.b, maxChunkSize=1
        ) == ints2octs((35, 8, 3, 2, 0, 169, 3, 2, 1, 138))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.b, defMode=False, maxChunkSize=1
        ) == ints2octs((35, 128, 3, 2, 0, 169, 3, 2, 1, 138, 0, 0))

    def testEmptyValue(self):
        assert encoder.encode(univ.BitString([])) == ints2octs((3, 1, 0))


class BitStringEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.b = (1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1)
        self.s = univ.BitString()

    def testDefMode(self):
        assert encoder.encode(self.b, asn1Spec=self.s) == ints2octs((3, 3, 1, 169, 138))

    def testIndefMode(self):
        assert encoder.encode(
            self.b, asn1Spec=self.s, defMode=False
        ) == ints2octs((3, 3, 1, 169, 138))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.b, asn1Spec=self.s, maxChunkSize=1
        ) == ints2octs((35, 8, 3, 2, 0, 169, 3, 2, 1, 138))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.b, asn1Spec=self.s, defMode=False, maxChunkSize=1
        ) == ints2octs((35, 128, 3, 2, 0, 169, 3, 2, 1, 138, 0, 0))

    def testEmptyValue(self):
        assert encoder.encode([],  asn1Spec=self.s) == ints2octs((3, 1, 0))


class OctetStringEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.o = univ.OctetString('Quick brown fox')

    def testDefMode(self):
        assert encoder.encode(self.o) == ints2octs(
            (4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120))

    def testIndefMode(self):
        assert encoder.encode(
            self.o, defMode=False
        ) == ints2octs((4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.o, maxChunkSize=4
        ) == ints2octs((36, 23, 4, 4, 81, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 4, 111, 119,
                        110, 32, 4, 3, 102, 111, 120))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.o, defMode=False, maxChunkSize=4
        ) == ints2octs((36, 128, 4, 4, 81, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 4, 111, 119, 110,
                        32, 4, 3, 102,  111, 120, 0, 0))


class OctetStringEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.OctetString()
        self.o = 'Quick brown fox'

    def testDefMode(self):
        assert encoder.encode(self.o, asn1Spec=self.s) == ints2octs(
            (4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120))

    def testIndefMode(self):
        assert encoder.encode(
            self.o, asn1Spec=self.s, defMode=False
        ) == ints2octs((4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.o, asn1Spec=self.s, maxChunkSize=4
        ) == ints2octs((36, 23, 4, 4, 81, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 4, 111, 119,
                        110, 32, 4, 3, 102, 111, 120))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.o, asn1Spec=self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((36, 128, 4, 4, 81, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 4, 111, 119, 110,
                        32, 4, 3, 102,  111, 120, 0, 0))


class ExpTaggedOctetStringEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.o = univ.OctetString().subtype(
            value='Quick brown fox',
            explicitTag=tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 5)
        )

    def testDefMode(self):
        assert encoder.encode(self.o) == ints2octs(
            (101, 17, 4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120))

    def testIndefMode(self):
        assert encoder.encode(
            self.o, defMode=False
        ) == ints2octs((101, 128, 4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120, 0, 0))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.o, defMode=True, maxChunkSize=4
        ) == ints2octs((101, 25, 36, 23, 4, 4, 81, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 4, 111, 119, 110, 32, 4, 3,
                        102, 111, 120))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.o, defMode=False, maxChunkSize=4
        ) == ints2octs((101, 128, 36, 128, 4, 4, 81, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 4, 111, 119, 110, 32, 4, 3, 102, 111, 120, 0, 0, 0, 0))


class NullEncoderTestCase(BaseTestCase):
    def testNull(self):
        assert encoder.encode(univ.Null('')) == ints2octs((5, 0))


class NullEncoderWithSchemaTestCase(BaseTestCase):
    def testNull(self):
        assert encoder.encode(None, univ.Null()) == ints2octs((5, 0))


class ObjectIdentifierEncoderTestCase(BaseTestCase):
    def testOne(self):
        assert encoder.encode(
            univ.ObjectIdentifier((1, 3, 6, 0, 0xffffe))
        ) == ints2octs((6, 6, 43, 6, 0, 191, 255, 126))

    def testEdge1(self):
        assert encoder.encode(
            univ.ObjectIdentifier((0, 39))
        ) == ints2octs((6, 1, 39))

    def testEdge2(self):
        assert encoder.encode(
            univ.ObjectIdentifier((1, 39))
        ) == ints2octs((6, 1, 79))

    def testEdge3(self):
        # 01111111
        assert encoder.encode(
            univ.ObjectIdentifier((2, 40))
        ) == ints2octs((6, 1, 120))

    def testEdge4(self):
        # 10010000|10000000|10000000|10000000|01001111
        assert encoder.encode(
            univ.ObjectIdentifier((2, 0xffffffff))
        ) == ints2octs((6, 5, 0x90, 0x80, 0x80, 0x80, 0x4F))

    def testEdge5(self):
        # 01111111
        assert encoder.encode(
            univ.ObjectIdentifier((2, 47))
        ) == ints2octs((6, 1, 0x7F))

    def testEdge6(self):
        # 10000001|00000000
        assert encoder.encode(
            univ.ObjectIdentifier((2, 48))
        ) == ints2octs((6, 2, 0x81, 0x00))

    def testEdge7(self):
        # 10000001|00110100|00000003
        assert encoder.encode(
            univ.ObjectIdentifier((2, 100, 3))
        ) == ints2octs((6, 3, 0x81, 0x34, 0x03))

    def testEdge8(self):
        # 10000101|00000000
        assert encoder.encode(
            univ.ObjectIdentifier((2, 560))
        ) == ints2octs((6, 2, 133, 0))

    def testEdge9(self):
        # 10001000|10000100|10000111|0000010
        assert encoder.encode(
            univ.ObjectIdentifier((2, 16843570))
        ) == ints2octs((6, 4, 0x88, 0x84, 0x87, 0x02))

    def testEdgeA(self):
        assert encoder.encode(
            univ.ObjectIdentifier((2, 5))
        ) == ints2octs((6, 1, 85))

    def testImpossible1(self):
        try:
            encoder.encode(univ.ObjectIdentifier((3, 1, 2)))
        except PyAsn1Error:
            pass
        else:
            assert 0, 'impossible leading arc tolerated'

    def testImpossible2(self):
        try:
            encoder.encode(univ.ObjectIdentifier((0,)))
        except PyAsn1Error:
            pass
        else:
            assert 0, 'single arc OID tolerated'

    def testImpossible3(self):
        try:
            encoder.encode(univ.ObjectIdentifier((0, 40)))
        except PyAsn1Error:
            pass
        else:
            assert 0, 'second arc overflow tolerated'

    def testImpossible4(self):
        try:
            encoder.encode(univ.ObjectIdentifier((1, 40)))
        except PyAsn1Error:
            pass
        else:
            assert 0, 'second arc overflow tolerated'

    def testLarge1(self):
        assert encoder.encode(
            univ.ObjectIdentifier((2, 18446744073709551535184467440737095))
        ) == ints2octs((0x06, 0x11, 0x83, 0xC6, 0xDF, 0xD4, 0xCC, 0xB3, 0xFF, 0xFF, 0xFE, 0xF0, 0xB8, 0xD6, 0xB8, 0xCB,
                        0xE2, 0xB7, 0x17))

    def testLarge2(self):
        assert encoder.encode(
            univ.ObjectIdentifier((2, 999, 18446744073709551535184467440737095))
        ) == ints2octs((0x06, 0x13, 0x88, 0x37, 0x83, 0xC6, 0xDF, 0xD4, 0xCC, 0xB3, 0xFF, 0xFF, 0xFE, 0xF0, 0xB8, 0xD6,
                        0xB8, 0xCB, 0xE2, 0xB6, 0x47))


class ObjectIdentifierWithSchemaEncoderTestCase(BaseTestCase):
    def testOne(self):
        assert encoder.encode(
            (1, 3, 6, 0, 0xffffe), asn1Spec=univ.ObjectIdentifier()
        ) == ints2octs((6, 6, 43, 6, 0, 191, 255, 126))


class RealEncoderTestCase(BaseTestCase):
    def testChar(self):
        assert encoder.encode(
            univ.Real((123, 10, 11))
        ) == ints2octs((9, 7, 3, 49, 50, 51, 69, 49, 49))

    def testBin1(self):
        assert encoder.encode(  # default binEncBase = 2
            univ.Real((0.5, 2, 0))  # check encbase = 2 and exponent = -1
        ) == ints2octs((9, 3, 128, 255, 1))

    def testBin2(self):
        r = univ.Real((3.25, 2, 0))
        r.binEncBase = 8  # change binEncBase only for this instance of Real
        assert encoder.encode(
            r  # check encbase = 8
        ) == ints2octs((9, 3, 148, 255, 13))

    def testBin3(self):
        # change binEncBase in the RealEncoder instance => for all further Real
        binEncBase, encoder.typeMap[univ.Real.typeId].binEncBase = encoder.typeMap[univ.Real.typeId].binEncBase, 16
        assert encoder.encode(
            univ.Real((0.00390625, 2, 0))  # check encbase = 16
        ) == ints2octs((9, 3, 160, 254, 1))
        encoder.typeMap[univ.Real.typeId].binEncBase = binEncBase

    def testBin4(self):
        # choose binEncBase automatically for all further Real (testBin[4-7])
        binEncBase, encoder.typeMap[univ.Real.typeId].binEncBase = encoder.typeMap[univ.Real.typeId].binEncBase, None
        assert encoder.encode(
            univ.Real((1, 2, 0))  # check exponenta = 0
        ) == ints2octs((9, 3, 128, 0, 1))
        encoder.typeMap[univ.Real.typeId].binEncBase = binEncBase

    def testBin5(self):
        assert encoder.encode(
            univ.Real((3, 2, -1020))  # case of 2 octs for exponent and
            # negative exponenta and abs(exponent) is
            # all 1's and fills the whole octet(s)
        ) == ints2octs((9, 4, 129, 252, 4, 3))

    def testBin6(self):
        assert encoder.encode(
            univ.Real((1, 2, 262140))  # case of 3 octs for exponent and
            # check that first 9 bits for exponent
            # are not all 1's
        ) == ints2octs((9, 5, 130, 3, 255, 252, 1))

    def testBin7(self):
        assert encoder.encode(
            univ.Real((-1, 2, 76354972))  # case of >3 octs for exponent and
            # mantissa < 0
        ) == ints2octs((9, 7, 195, 4, 4, 141, 21, 156, 1))

    def testPlusInf(self):
        assert encoder.encode(univ.Real('inf')) == ints2octs((9, 1, 64))

    def testMinusInf(self):
        assert encoder.encode(univ.Real('-inf')) == ints2octs((9, 1, 65))

    def testZero(self):
        assert encoder.encode(univ.Real(0)) == ints2octs((9, 0))


class RealEncoderWithSchemaTestCase(BaseTestCase):
    def testChar(self):
        assert encoder.encode(
            (123, 10, 11), asn1Spec=univ.Real()
        ) == ints2octs((9, 7, 3, 49, 50, 51, 69, 49, 49))


if sys.version_info[0:2] > (2, 5):
    class UniversalStringEncoderTestCase(BaseTestCase):
        def testEncoding(self):
            assert encoder.encode(char.UniversalString(sys.version_info[0] == 3 and 'abc' or unicode('abc'))) == ints2octs(
                (28, 12, 0, 0, 0, 97, 0, 0, 0, 98, 0, 0, 0, 99)), 'Incorrect encoding'


    class UniversalStringEncoderWithSchemaTestCase(BaseTestCase):
        def testEncoding(self):
            assert encoder.encode(
                sys.version_info[0] == 3 and 'abc' or unicode('abc'), asn1Spec=char.UniversalString()
            ) == ints2octs((28, 12, 0, 0, 0, 97, 0, 0, 0, 98, 0, 0, 0, 99)), 'Incorrect encoding'


class BMPStringEncoderTestCase(BaseTestCase):
    def testEncoding(self):
        assert encoder.encode(char.BMPString(sys.version_info[0] == 3 and 'abc' or unicode('abc'))) == ints2octs(
            (30, 6, 0, 97, 0, 98, 0, 99)), 'Incorrect encoding'


class BMPStringEncoderWithSchemaTestCase(BaseTestCase):
    def testEncoding(self):
        assert encoder.encode(
            sys.version_info[0] == 3 and 'abc' or unicode('abc'), asn1Spec=char.BMPString()
        ) == ints2octs((30, 6, 0, 97, 0, 98, 0, 99)), 'Incorrect encoding'


class UTF8StringEncoderTestCase(BaseTestCase):
    def testEncoding(self):
        assert encoder.encode(char.UTF8String(sys.version_info[0] == 3 and 'abc' or unicode('abc'))) == ints2octs(
            (12, 3, 97, 98, 99)), 'Incorrect encoding'


class UTF8StringEncoderWithSchemaTestCase(BaseTestCase):
    def testEncoding(self):
        assert encoder.encode(
            sys.version_info[0] == 3 and 'abc' or unicode('abc'), asn1Spec=char.UTF8String()
        ) == ints2octs((12, 3, 97, 98, 99)), 'Incorrect encoding'


class SequenceOfEncoderTestCase(BaseTestCase):
    def testEmpty(self):
        s = univ.SequenceOf()
        assert encoder.encode(s) == ints2octs((48, 0))

    def testDefMode(self):
        s = univ.SequenceOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(s) == ints2octs((48, 13, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testIndefMode(self):
        s = univ.SequenceOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=False
        ) == ints2octs((48, 128, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testDefModeChunked(self):
        s = univ.SequenceOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 19, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testIndefModeChunked(self):
        s = univ.SequenceOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))


class SequenceOfEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.SequenceOf(componentType=univ.OctetString())
        self.v = ['quick brown']

    def testEmpty(self):
        assert encoder.encode([], asn1Spec=self.s) == ints2octs((48, 0))

    def testDefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s
        ) == ints2octs((48, 13, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testIndefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False
        ) == ints2octs((48, 128, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 19, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))


class SequenceOfEncoderWithComponentsSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.SequenceOf(componentType=univ.OctetString())

    def __init(self):
        self.s.clear()
        self.s.setComponentByPosition(0, 'quick brown')

    def testDefMode(self):
        self.__init()
        assert encoder.encode(self.s) == ints2octs((48, 13, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testIndefMode(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((48, 128, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testDefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 19, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testIndefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))


class SetOfEncoderTestCase(BaseTestCase):
    def testEmpty(self):
        s = univ.SetOf()
        assert encoder.encode(s) == ints2octs((49, 0))

    def testDefMode(self):
        s = univ.SetOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(s) == ints2octs((49, 13, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testIndefMode(self):
        s = univ.SetOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=False
        ) == ints2octs((49, 128, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testDefModeChunked(self):
        s = univ.SetOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 19, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testIndefModeChunked(self):
        s = univ.SetOf()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=False, maxChunkSize=4
        ) == ints2octs((49, 128, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))


class SetOfEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.SetOf(componentType=univ.OctetString())
        self.v = ['quick brown']

    def testEmpty(self):
        s = univ.SetOf()
        assert encoder.encode([], asn1Spec=self.s) == ints2octs((49, 0))

    def testDefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s
        ) == ints2octs((49, 13, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testIndefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False
        ) == ints2octs((49, 128, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 19, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False, maxChunkSize=4
        ) == ints2octs(
            (49, 128, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))


class SetOfEncoderWithComponentsSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.SetOf(componentType=univ.OctetString())

    def __init(self):
        self.s.clear()
        self.s.setComponentByPosition(0, 'quick brown')

    def testDefMode(self):
        self.__init()
        assert encoder.encode(self.s) == ints2octs((49, 13, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testIndefMode(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((49, 128, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testDefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 19, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testIndefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((49, 128, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))


class SequenceEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Sequence()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testDefMode(self):
        assert encoder.encode(self.s) == ints2octs((48, 18, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1))

    def testIndefMode(self):
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 24, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 2, 1, 1))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 2, 1, 1, 0, 0))


class SequenceEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('place-holder', univ.Null()),
                namedtype.OptionalNamedType('first-name', univ.OctetString()),
                namedtype.DefaultedNamedType('age', univ.Integer(33)),
            )
        )
        self.v = {
            'place-holder': None,
            'first-name': 'quick brown',
            'age': 1
        }

    def testEmpty(self):
        try:
            assert encoder.encode({}, asn1Spec=self.s)

        except PyAsn1Error:
            pass

        else:
            assert False, 'empty bare sequence tolerated'

    def testDefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s
        ) == ints2octs((48, 18, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1))

    def testIndefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 24, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 2, 1, 1))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 2, 1, 1, 0, 0))


class SequenceEncoderWithUntaggedOpenTypesTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        openType = opentype.OpenType(
            'id',
            {1: univ.Integer(),
             2: univ.OctetString()}
        )
        self.s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer()),
                namedtype.NamedType('blob', univ.Any(), openType=openType)
            )
        )

    def testEncodeOpenTypeChoiceOne(self):
        self.s.clear()

        self.s[0] = 1
        self.s[1] = univ.Integer(12)

        assert encoder.encode(self.s, asn1Spec=self.s) == ints2octs(
            (48, 6, 2, 1, 1, 2, 1, 12)
        )

    def testEncodeOpenTypeChoiceTwo(self):
        self.s.clear()

        self.s[0] = 2
        self.s[1] = univ.OctetString('quick brown')

        assert encoder.encode(self.s, asn1Spec=self.s) == ints2octs(
            (48, 16, 2, 1, 2, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110)
        )

    def testEncodeOpenTypeUnknownId(self):
        self.s.clear()

        self.s[0] = 2
        self.s[1] = univ.ObjectIdentifier('1.3.6')

        try:
            encoder.encode(self.s, asn1Spec=self.s)

        except PyAsn1Error:
            assert False, 'incompatible open type tolerated'

    def testEncodeOpenTypeIncompatibleType(self):
        self.s.clear()

        self.s[0] = 2
        self.s[1] = univ.ObjectIdentifier('1.3.6')

        try:
            encoder.encode(self.s, asn1Spec=self.s)

        except PyAsn1Error:
            assert False, 'incompatible open type tolerated'


class SequenceEncoderWithImplicitlyTaggedOpenTypesTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        openType = opentype.OpenType(
            'id',
            {1: univ.Integer(),
             2: univ.OctetString()}
        )
        self.s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer()),
                namedtype.NamedType('blob', univ.Any().subtype(implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 3)), openType=openType)
            )
        )

    def testEncodeOpenTypeChoiceOne(self):
        self.s.clear()

        self.s[0] = 1
        self.s[1] = univ.Integer(12)

        assert encoder.encode(self.s, asn1Spec=self.s) == ints2octs(
            (48, 8, 2, 1, 1, 131, 3, 2, 1, 12)
        )


class SequenceEncoderWithExplicitlyTaggedOpenTypesTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        openType = opentype.OpenType(
            'id',
            {1: univ.Integer(),
             2: univ.OctetString()}
        )
        self.s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer()),
                namedtype.NamedType('blob', univ.Any().subtype(explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 3)), openType=openType)
            )
        )

    def testEncodeOpenTypeChoiceOne(self):
        self.s.clear()

        self.s[0] = 1
        self.s[1] = univ.Integer(12)

        assert encoder.encode(self.s, asn1Spec=self.s) == ints2octs(
            (48, 8, 2, 1, 1, 163, 3, 2, 1, 12)
        )


class SequenceEncoderWithComponentsSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('place-holder', univ.Null()),
                namedtype.OptionalNamedType('first-name', univ.OctetString()),
                namedtype.DefaultedNamedType('age', univ.Integer(33)),
            )
        )

    def __init(self):
        self.s.clear()
        self.s.setComponentByPosition(0, '')

    def __initWithOptional(self):
        self.s.clear()
        self.s.setComponentByPosition(0, '')
        self.s.setComponentByPosition(1, 'quick brown')

    def __initWithDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0, '')
        self.s.setComponentByPosition(2, 1)

    def __initWithOptionalAndDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testDefMode(self):
        self.__init()
        assert encoder.encode(self.s) == ints2octs((48, 2, 5, 0))

    def testIndefMode(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((48, 128, 5, 0, 0, 0))

    def testDefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 2, 5, 0))

    def testIndefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 5, 0, 0, 0))

    def testWithOptionalDefMode(self):
        self.__initWithOptional()
        assert encoder.encode(self.s) == ints2octs(
            (48, 15, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testWithOptionalIndefMode(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testWithOptionalDefModeChunked(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 21, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testWithOptionalIndefModeChunked(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs(
            (48, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))

    def testWithDefaultedDefMode(self):
        self.__initWithDefaulted()
        assert encoder.encode(self.s) == ints2octs((48, 5, 5, 0, 2, 1, 1))

    def testWithDefaultedIndefMode(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((48, 128, 5, 0, 2, 1, 1, 0, 0))

    def testWithDefaultedDefModeChunked(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((48, 5, 5, 0, 2, 1, 1))

    def testWithDefaultedIndefModeChunked(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 5, 0, 2, 1, 1, 0, 0))

    def testWithOptionalAndDefaultedDefMode(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(self.s) == ints2octs(
            (48, 18, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1))

    def testWithOptionalAndDefaultedIndefMode(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testWithOptionalAndDefaultedDefModeChunked(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs(
            (48, 24, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 2, 1, 1))

    def testWithOptionalAndDefaultedIndefModeChunked(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((48, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0,
                        0, 2, 1, 1, 0, 0))


class ExpTaggedSequenceEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('number', univ.Integer()),
            )
        )

        s = s.subtype(
            explicitTag=tag.Tag(tag.tagClassApplication, tag.tagFormatConstructed, 5)
        )

        s[0] = 12

        self.s = s

    def testDefMode(self):
        assert encoder.encode(self.s) == ints2octs((101, 5, 48, 3, 2, 1, 12))

    def testIndefMode(self):
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((101, 128, 48, 128, 2, 1, 12, 0, 0, 0, 0))


class ExpTaggedSequenceComponentEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('number', univ.Boolean().subtype(explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 0))),
            )
        )

        self.s[0] = True

    def testDefMode(self):
        assert encoder.encode(self.s) == ints2octs((48, 5, 160, 3, 1, 1, 1))

    def testIndefMode(self):
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((48, 128, 160, 3, 1, 1, 1, 0, 0, 0, 0))


class SetEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Set()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testDefMode(self):
        assert encoder.encode(self.s) == ints2octs((49, 18, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1))

    def testIndefMode(self):
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((49, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 24, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 2, 1, 1))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((49, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 2, 1, 1, 0, 0))


class SetEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Set(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('place-holder', univ.Null()),
                namedtype.OptionalNamedType('first-name', univ.OctetString()),
                namedtype.DefaultedNamedType('age', univ.Integer(33)),
            )
        )
        self.v = {
            'place-holder': None,
            'first-name': 'quick brown',
            'age': 1
        }

    def testEmpty(self):
        try:
            assert encoder.encode({}, asn1Spec=self.s)

        except PyAsn1Error:
            pass

        else:
            assert False, 'empty bare SET tolerated'

    def testDefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s
        ) == ints2octs((49, 18, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1))

    def testIndefMode(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False
        ) == ints2octs((49, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testDefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 24, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 2, 1, 1))

    def testIndefModeChunked(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((49, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 2, 1, 1, 0, 0))


class SetEncoderWithComponentsSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Set(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('place-holder', univ.Null()),
                namedtype.OptionalNamedType('first-name', univ.OctetString()),
                namedtype.DefaultedNamedType('age', univ.Integer(33)),
            )
        )

    def __init(self):
        self.s.clear()
        self.s.setComponentByPosition(0, '')

    def __initWithOptional(self):
        self.s.clear()
        self.s.setComponentByPosition(0, '')
        self.s.setComponentByPosition(1, 'quick brown')

    def __initWithDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0, '')
        self.s.setComponentByPosition(2, 1)

    def __initWithOptionalAndDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testDefMode(self):
        self.__init()
        assert encoder.encode(self.s) == ints2octs((49, 2, 5, 0))

    def testIndefMode(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((49, 128, 5, 0, 0, 0))

    def testDefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 2, 5, 0))

    def testIndefModeChunked(self):
        self.__init()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((49, 128, 5, 0, 0, 0))

    def testWithOptionalDefMode(self):
        self.__initWithOptional()
        assert encoder.encode(self.s) == ints2octs(
            (49, 15, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testWithOptionalIndefMode(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((49, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testWithOptionalDefModeChunked(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 21, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testWithOptionalIndefModeChunked(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs(
            (49, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 0, 0))

    def testWithDefaultedDefMode(self):
        self.__initWithDefaulted()
        assert encoder.encode(self.s) == ints2octs((49, 5, 5, 0, 2, 1, 1))

    def testWithDefaultedIndefMode(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((49, 128, 5, 0, 2, 1, 1, 0, 0))

    def testWithDefaultedDefModeChunked(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs((49, 5, 5, 0, 2, 1, 1))

    def testWithDefaultedIndefModeChunked(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((49, 128, 5, 0, 2, 1, 1, 0, 0))

    def testWithOptionalAndDefaultedDefMode(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(self.s) == ints2octs(
            (49, 18, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1))

    def testWithOptionalAndDefaultedIndefMode(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s, defMode=False
        ) == ints2octs((49, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testWithOptionalAndDefaultedDefModeChunked(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s, defMode=True, maxChunkSize=4
        ) == ints2octs(
            (49, 24, 5, 0, 36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 2, 1, 1))

    def testWithOptionalAndDefaultedIndefModeChunked(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s, defMode=False, maxChunkSize=4
        ) == ints2octs((49, 128, 5, 0, 36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0, 2, 1, 1, 0, 0))


class ChoiceEncoderTestCase(BaseTestCase):

    def testEmpty(self):
        s = univ.Choice()
        try:
            encoder.encode(s)
        except PyAsn1Error:
            pass
        else:
            assert 0, 'encoded unset choice'

    def testDefModeOptionOne(self):
        s = univ.Choice()
        s.setComponentByPosition(0, univ.Null(''))
        assert encoder.encode(s) == ints2octs((5, 0))

    def testDefModeOptionTwo(self):
        s = univ.Choice()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(s) == ints2octs((4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testIndefMode(self):
        s = univ.Choice()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=False
        ) == ints2octs((4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110))

    def testDefModeChunked(self):
        s = univ.Choice()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=True, maxChunkSize=4
        ) == ints2octs((36, 17, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110))

    def testIndefModeChunked(self):
        s = univ.Choice()
        s.setComponentByPosition(0, univ.OctetString('quick brown'))
        assert encoder.encode(
            s, defMode=False, maxChunkSize=4
        ) == ints2octs((36, 128, 4, 4, 113, 117, 105, 99, 4, 4, 107, 32, 98, 114, 4, 3, 111, 119, 110, 0, 0))


class ChoiceEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('place-holder', univ.Null('')),
                namedtype.NamedType('number', univ.Integer(0)),
                namedtype.NamedType('string', univ.OctetString())
            )
        )
        self.v = {
            'place-holder': None
        }

    def testFilled(self):
        assert encoder.encode(
            self.v, asn1Spec=self.s
        ) == ints2octs((5, 0))


class ChoiceEncoderWithComponentsSchemaTestCase(BaseTestCase):
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
            assert 0, 'encoded unset choice'

    def testFilled(self):
        self.s.setComponentByPosition(0, univ.Null(''))
        assert encoder.encode(self.s) == ints2octs((5, 0))

    def testTagged(self):
        s = self.s.subtype(
            explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 4)
        )
        s.setComponentByPosition(0, univ.Null(''))
        assert encoder.encode(s) == ints2octs((164, 2, 5, 0))

    def testUndefLength(self):
        self.s.setComponentByPosition(2, univ.OctetString('abcdefgh'))
        assert encoder.encode(self.s, defMode=False, maxChunkSize=3) == ints2octs(
            (36, 128, 4, 3, 97, 98, 99, 4, 3, 100, 101, 102, 4, 2, 103, 104, 0, 0))

    def testTaggedUndefLength(self):
        s = self.s.subtype(
            explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 4)
        )
        s.setComponentByPosition(2, univ.OctetString('abcdefgh'))
        assert encoder.encode(s, defMode=False, maxChunkSize=3) == ints2octs(
            (164, 128, 36, 128, 4, 3, 97, 98, 99, 4, 3, 100, 101, 102, 4, 2, 103, 104, 0, 0, 0, 0))


class AnyEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Any(encoder.encode(univ.OctetString('fox')))

    def testUntagged(self):
        assert encoder.encode(self.s) == ints2octs((4, 3, 102, 111, 120))

    def testTaggedEx(self):
        s = self.s.subtype(
            explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 4)
        )
        assert encoder.encode(s) == ints2octs((164, 5, 4, 3, 102, 111, 120))

    def testTaggedIm(self):
        s = self.s.subtype(
            implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 4)
        )
        assert encoder.encode(s) == ints2octs((132, 5, 4, 3, 102, 111, 120))


class AnyEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Any()
        self.v = encoder.encode(univ.OctetString('fox'))

    def testUntagged(self):
        assert encoder.encode(self.v, asn1Spec=self.s) == ints2octs((4, 3, 102, 111, 120))

    def testTaggedEx(self):
        s = self.s.subtype(
            explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 4)
        )
        assert encoder.encode(self.v, asn1Spec=s) == ints2octs((164, 5, 4, 3, 102, 111, 120))

    def testTaggedIm(self):
        s = self.s.subtype(
            implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 4)
        )
        assert encoder.encode(self.v, asn1Spec=s) == ints2octs((132, 5, 4, 3, 102, 111, 120))


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
