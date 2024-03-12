#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/pyasn1/license.html
#
import math
import pickle
import sys

try:
    import unittest2 as unittest

except ImportError:
    import unittest

from tests.base import BaseTestCase

from pyasn1.type import univ
from pyasn1.type import tag
from pyasn1.type import constraint
from pyasn1.type import namedtype
from pyasn1.type import namedval
from pyasn1.type import error
from pyasn1.compat.octets import str2octs, ints2octs, octs2ints
from pyasn1.error import PyAsn1Error


class NoValueTestCase(BaseTestCase):
    def testSingleton(self):
        assert univ.NoValue() is univ.NoValue(), 'NoValue is not a singleton'

    def testRepr(self):
        try:
            repr(univ.noValue)

        except PyAsn1Error:
            assert False, 'repr() on NoValue object fails'

    def testIsInstance(self):
        try:
            assert isinstance(univ.noValue, univ.NoValue), 'isinstance() on NoValue() object fails'

        except PyAsn1Error:
            assert False, 'isinstance() on NoValue object fails'

    def testStr(self):
        try:
            str(univ.noValue)

        except PyAsn1Error:
            pass

        else:
            assert False, 'str() works for NoValue object'

    def testLen(self):
        try:
            len(univ.noValue)

        except PyAsn1Error:
            pass

        else:
            assert False, 'len() works for NoValue object'

    def testCmp(self):
        try:
            univ.noValue == 1

        except PyAsn1Error:
            pass

        else:
            assert False, 'comparison works for NoValue object'

    def testSubs(self):
        try:
            univ.noValue[0]

        except PyAsn1Error:
            pass

        else:
            assert False, '__getitem__() works for NoValue object'

    def testKey(self):
        try:
            univ.noValue['key']

        except PyAsn1Error:
            pass

        else:
            assert False, '__getitem__() works for NoValue object'

    def testKeyAssignment(self):
        try:
            univ.noValue['key'] = 123

        except PyAsn1Error:
            pass

        else:
            assert False, '__setitem__() works for NoValue object'

    def testInt(self):
        try:
            int(univ.noValue)

        except PyAsn1Error:
            pass

        else:
            assert False, 'integer conversion works for NoValue object'

    def testAdd(self):
        try:
            univ.noValue + univ.noValue

        except PyAsn1Error:
            pass

        else:
            assert False, 'addition works for NoValue object'

    def testBitShift(self):
        try:
            univ.noValue << 1

        except PyAsn1Error:
            pass

        else:
            assert False, 'bitshift works for NoValue object'

    def testBooleanEvaluation(self):
        try:
            if univ.noValue:
                pass

        except PyAsn1Error:
            pass

        else:
            assert False, 'boolean evaluation works for NoValue object'
    
    def testSizeOf(self):
        try:
            if hasattr(sys, 'getsizeof'):
                sys.getsizeof(univ.noValue)

        except PyAsn1Error:
            assert False, 'sizeof failed for NoValue object'


class IntegerTestCase(BaseTestCase):
    def testStr(self):
        assert str(univ.Integer(1)) in ('1', '1L'), 'str() fails'

    def testRepr(self):
        assert '123' in repr(univ.Integer(123))

    def testAnd(self):
        assert univ.Integer(1) & 0 == 0, '__and__() fails'

    def testOr(self):
        assert univ.Integer(1) | 0 == 1, '__or__() fails'

    def testXor(self):
        assert univ.Integer(1) ^ 0 == 1, '__xor__() fails'

    def testRand(self):
        assert 0 & univ.Integer(1) == 0, '__rand__() fails'

    def testRor(self):
        assert 0 | univ.Integer(1) == 1, '__ror__() fails'

    def testRxor(self):
        assert 0 ^ univ.Integer(1) == 1, '__rxor__() fails'

    def testAdd(self):
        assert univ.Integer(-4) + 6 == 2, '__add__() fails'

    def testRadd(self):
        assert 4 + univ.Integer(5) == 9, '__radd__() fails'

    def testSub(self):
        assert univ.Integer(3) - 6 == -3, '__sub__() fails'

    def testRsub(self):
        assert 6 - univ.Integer(3) == 3, '__rsub__() fails'

    def testMul(self):
        assert univ.Integer(3) * -3 == -9, '__mul__() fails'

    def testRmul(self):
        assert 2 * univ.Integer(3) == 6, '__rmul__() fails'

    def testDivInt(self):
        assert univ.Integer(4) / 2 == 2, '__div__() fails'

    if sys.version_info[0] > 2:
        def testDivFloat(self):
            assert univ.Integer(3) / 2 == 1.5, '__div__() fails'

        def testRdivFloat(self):
            assert 3 / univ.Integer(2) == 1.5, '__rdiv__() fails'
    else:
        def testDivFloat(self):
            assert univ.Integer(3) / 2 == 1, '__div__() fails'

        def testRdivFloat(self):
            assert 3 / univ.Integer(2) == 1, '__rdiv__() fails'

    def testRdivInt(self):
        assert 6 / univ.Integer(3) == 2, '__rdiv__() fails'

    if sys.version_info[0] > 2:
        def testTrueDiv(self):
            assert univ.Integer(3) / univ.Integer(2) == 1.5, '__truediv__() fails'

    def testFloorDiv(self):
        assert univ.Integer(3) // univ.Integer(2) == 1, '__floordiv__() fails'

    def testMod(self):
        assert univ.Integer(3) % 2 == 1, '__mod__() fails'

    def testRmod(self):
        assert 4 % univ.Integer(3) == 1, '__rmod__() fails'

    def testPow(self):
        assert univ.Integer(3) ** 2 == 9, '__pow__() fails'

    def testRpow(self):
        assert 2 ** univ.Integer(2) == 4, '__rpow__() fails'

    def testLshift(self):
        assert univ.Integer(1) << 1 == 2, '<< fails'

    def testRshift(self):
        assert univ.Integer(2) >> 1 == 1, '>> fails'

    def testInt(self):
        assert int(univ.Integer(3)) == 3, '__int__() fails'

    def testLong(self):
        assert int(univ.Integer(8)) == 8, '__long__() fails'

    def testFloat(self):
        assert float(univ.Integer(4)) == 4.0, '__float__() fails'

    def testPos(self):
        assert +univ.Integer(1) == 1, '__pos__() fails'

    def testNeg(self):
        assert -univ.Integer(1) == -1, '__neg__() fails'

    def testInvert(self):
        assert ~univ.Integer(1) == -2, '__invert__() fails'

    def testRound(self):
        assert round(univ.Integer(1), 3) == 1.0, '__round__() fails'

    def testFloor(self):
        assert math.floor(univ.Integer(1)) == 1, '__floor__() fails'

    def testCeil(self):
        assert math.ceil(univ.Integer(1)) == 1, '__ceil__() fails'

    if sys.version_info[0:2] > (2, 5):
        def testTrunc(self):
            assert math.trunc(univ.Integer(1)) == 1, '__trunc__() fails'

    def testPrettyIn(self):
        assert univ.Integer('3') == 3, 'prettyIn() fails'

    def testTag(self):
        assert univ.Integer().tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x02)
        )

    def testNamedVals(self):

        class Integer(univ.Integer):
            namedValues = univ.Integer.namedValues.clone(('asn1', 1))

        assert Integer('asn1') == 1, 'named val fails'
        assert int(Integer('asn1')) == 1, 'named val fails'
        assert str(Integer('asn1')) == 'asn1', 'named val __str__() fails'

    def testSubtype(self):
        assert univ.Integer().subtype(
            value=1,
            implicitTag=tag.Tag(tag.tagClassPrivate, tag.tagFormatSimple, 2),
            subtypeSpec=constraint.SingleValueConstraint(1, 3)
        ) == univ.Integer(
            value=1,
            tagSet=tag.TagSet(tag.Tag(tag.tagClassPrivate,
                                      tag.tagFormatSimple, 2)),
            subtypeSpec=constraint.ConstraintsIntersection(constraint.SingleValueConstraint(1, 3))
        )


class IntegerPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.Integer()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.Integer
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.Integer(-123)
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == -123


class BooleanTestCase(BaseTestCase):
    def testTruth(self):
        assert univ.Boolean(True) and univ.Boolean(1), 'Truth initializer fails'

    def testFalse(self):
        assert not univ.Boolean(False) and not univ.Boolean(0), 'False initializer fails'

    def testStr(self):
        assert str(univ.Boolean(1)) == 'True', 'str() fails'

    def testInt(self):
        assert int(univ.Boolean(1)) == 1, 'int() fails'

    def testRepr(self):
        assert 'Boolean' in repr(univ.Boolean(1))

    def testTag(self):
        assert univ.Boolean().tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x01)
        )

    def testConstraints(self):

        class Boolean(univ.Boolean):
            pass

        try:
            Boolean(2)
        except error.ValueConstraintError:
            pass
        else:
            assert 0, 'constraint fail'


class BooleanPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.Boolean()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.Boolean
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.Boolean(True)
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == True


class BitStringTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        self.b = univ.BitString(
            namedValues=namedval.NamedValues(('Active', 0), ('Urgent', 1))
        )

    def testBinDefault(self):

        class BinDefault(univ.BitString):
            defaultBinValue = '1010100110001010'

        assert BinDefault() == univ.BitString(binValue='1010100110001010')

    def testHexDefault(self):

        class HexDefault(univ.BitString):
            defaultHexValue = 'A98A'

        assert HexDefault() == univ.BitString(hexValue='A98A')

    def testSet(self):
        assert self.b.clone('Active') == (1,)
        assert self.b.clone('Urgent') == (0, 1)
        assert self.b.clone('Urgent, Active') == (1, 1)
        assert self.b.clone("'1010100110001010'B") == (1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0)
        assert self.b.clone("'A98A'H") == (1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0)
        assert self.b.clone(binValue='1010100110001010') == (1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0)
        assert self.b.clone(hexValue='A98A') == (1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0)
        assert self.b.clone('1010100110001010') == (1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0)
        assert self.b.clone((1, 0, 1)) == (1, 0, 1)

    def testStr(self):
        assert str(self.b.clone('Urgent')) == '01'

    def testRepr(self):
        assert 'BitString' in repr(self.b.clone('Urgent,Active'))

    def testTag(self):
        assert univ.BitString().tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x03)
        )

    def testLen(self):
        assert len(self.b.clone("'A98A'H")) == 16

    def testGetItem(self):
        assert self.b.clone("'A98A'H")[0] == 1
        assert self.b.clone("'A98A'H")[1] == 0
        assert self.b.clone("'A98A'H")[2] == 1

    if sys.version_info[:2] > (2, 4):
        def testReverse(self):
            assert list(reversed(univ.BitString([0, 0, 1]))) == list(univ.BitString([1, 0, 0]))

    def testAsOctets(self):
        assert self.b.clone(hexValue='A98A').asOctets() == ints2octs((0xa9, 0x8a)), 'testAsOctets() fails'

    def testAsInts(self):
        assert self.b.clone(hexValue='A98A').asNumbers() == (0xa9, 0x8a), 'testAsNumbers() fails'

    def testMultipleOfEightPadding(self):
        assert self.b.clone((1, 0, 1)).asNumbers() == (5,)

    def testAsInteger(self):
        assert self.b.clone('11000000011001').asInteger() == 12313
        assert self.b.clone('1100110011011111').asInteger() == 52447

    def testStaticDef(self):

        class BitString(univ.BitString):
            pass

        assert BitString('11000000011001').asInteger() == 12313


class BitStringPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.BitString()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.BitString
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.BitString((1, 0, 1, 0))
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == (1, 0, 1, 0)


class OctetStringWithUnicodeMixIn(object):

    initializer = ()
    encoding = 'us-ascii'

    def setUp(self):
        self.pythonString = ints2octs(self.initializer).decode(self.encoding)
        self.encodedPythonString = self.pythonString.encode(self.encoding)
        self.numbersString = tuple(octs2ints(self.encodedPythonString))

    def testInit(self):
        assert univ.OctetString(self.encodedPythonString) == self.encodedPythonString, '__init__() fails'

    def testInitFromAsn1(self):
            assert univ.OctetString(univ.OctetString(self.encodedPythonString)) == self.encodedPythonString
            assert univ.OctetString(univ.Integer(123)) == univ.OctetString('123')

    def testSerialised(self):
        if sys.version_info[0] < 3:
            assert str(univ.OctetString(self.encodedPythonString, encoding=self.encoding)) == self.encodedPythonString, '__str__() fails'
        else:
            assert bytes(univ.OctetString(self.encodedPythonString, encoding=self.encoding)) == self.encodedPythonString, '__str__() fails'

    def testPrintable(self):
        if sys.version_info[0] < 3:
            assert str(univ.OctetString(self.encodedPythonString, encoding=self.encoding)) == self.encodedPythonString, '__str__() fails'
            assert unicode(univ.OctetString(self.pythonString, encoding=self.encoding)) == self.pythonString, 'unicode init fails'
        else:
            assert str(univ.OctetString(self.pythonString, encoding=self.encoding)) == self.pythonString, 'unicode init fails'

    def testSeq(self):
        assert univ.OctetString(self.encodedPythonString)[0] == self.encodedPythonString[0], '__getitem__() fails'

    def testRepr(self):
        assert 'abc' in repr(univ.OctetString('abc'))

    def testAsOctets(self):
        assert univ.OctetString(self.encodedPythonString).asOctets() == self.encodedPythonString, 'testAsOctets() fails'

    def testAsInts(self):
        assert univ.OctetString(self.encodedPythonString).asNumbers() == self.numbersString, 'testAsNumbers() fails'

    def testAdd(self):
        assert univ.OctetString(self.encodedPythonString) + self.encodedPythonString == self.encodedPythonString + self.encodedPythonString, '__add__() fails'

    def testRadd(self):
        assert self.encodedPythonString + univ.OctetString(self.encodedPythonString) == self.encodedPythonString + self.encodedPythonString, '__radd__() fails'

    def testMul(self):
        assert univ.OctetString(self.encodedPythonString) * 2 == self.encodedPythonString * 2, '__mul__() fails'

    def testRmul(self):
        assert 2 * univ.OctetString(self.encodedPythonString) == 2 * self.encodedPythonString, '__rmul__() fails'

    def testContains(self):
        s = univ.OctetString(self.encodedPythonString)
        assert self.encodedPythonString in s
        assert self.encodedPythonString * 2 not in s

    if sys.version_info[:2] > (2, 4):
       def testReverse(self):
           assert list(reversed(univ.OctetString(self.encodedPythonString))) == list(reversed(self.encodedPythonString))


class OctetStringWithAsciiTestCase(OctetStringWithUnicodeMixIn, BaseTestCase):
    initializer = (97, 102)
    encoding = 'us-ascii'


class OctetStringWithUtf8TestCase(OctetStringWithUnicodeMixIn, BaseTestCase):
    initializer = (208, 176, 208, 177, 208, 178)
    encoding = 'utf-8'


class OctetStringWithUtf16TestCase(OctetStringWithUnicodeMixIn, BaseTestCase):
    initializer = (4, 48, 4, 49, 4, 50)
    encoding = 'utf-16-be'


if sys.version_info[0] > 2:

    # Somehow comparison of UTF-32 encoded strings does not work in Py2

    class OctetStringWithUtf32TestCase(OctetStringWithUnicodeMixIn, BaseTestCase):
        initializer = (0, 0, 4, 48, 0, 0, 4, 49, 0, 0, 4, 50)
        encoding = 'utf-32-be'


class OctetStringTestCase(BaseTestCase):

    def testBinDefault(self):

        class BinDefault(univ.OctetString):
            defaultBinValue = '1000010111101110101111000000111011'

        assert BinDefault() == univ.OctetString(binValue='1000010111101110101111000000111011')

    def testHexDefault(self):

        class HexDefault(univ.OctetString):
            defaultHexValue = 'FA9823C43E43510DE3422'

        assert HexDefault() == univ.OctetString(hexValue='FA9823C43E43510DE3422')

    def testBinStr(self):
        assert univ.OctetString(binValue="1000010111101110101111000000111011") == ints2octs((133, 238, 188, 14, 192)), 'bin init fails'

    def testHexStr(self):
        assert univ.OctetString(hexValue="FA9823C43E43510DE3422") == ints2octs((250, 152, 35, 196, 62, 67, 81, 13, 227, 66, 32)), 'hex init fails'

    def testTuple(self):
        assert univ.OctetString((1, 2, 3, 4, 5)) == ints2octs((1, 2, 3, 4, 5)), 'tuple init failed'

    def testRepr(self):
        assert 'abc' in repr(univ.OctetString('abc'))

    def testEmpty(self):
        try:
            str(univ.OctetString())
        except PyAsn1Error:
            pass
        else:
            assert 0, 'empty OctetString() not reported'

    def testTag(self):
        assert univ.OctetString().tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x04)
        )

    def testStaticDef(self):

        class OctetString(univ.OctetString):
            pass

        assert OctetString(hexValue="FA9823C43E43510DE3422") == ints2octs((250, 152, 35, 196, 62, 67, 81, 13, 227, 66, 32))


class OctetStringPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.BitString()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.BitString
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.BitString((1, 0, 1, 0))
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == (1, 0, 1, 0)


class Null(BaseTestCase):

    def testInit(self):
        assert not univ.Null().isValue
        assert univ.Null(0) == str2octs('')
        assert univ.Null(False) == str2octs('')
        assert univ.Null('') == str2octs('')
        assert univ.Null(None) == str2octs('')

        try:
            assert univ.Null(True)

        except PyAsn1Error:
            pass

        try:
            assert univ.Null('xxx')

        except PyAsn1Error:
            pass

    def testStr(self):
        assert str(univ.Null('')) == '', 'str() fails'

    def testRepr(self):
        assert 'Null' in repr(univ.Null(''))

    def testTag(self):
        assert univ.Null().tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x05)
        )

    def testConstraints(self):
        try:
            univ.Null(2)
        except error.ValueConstraintError:
            pass
        else:
            assert 0, 'constraint fail'

    def testStaticDef(self):

        class Null(univ.Null):
            pass

        assert not Null('')


class NullPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.Null()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.Null
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.Null('')
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert not new_asn1


class RealTestCase(BaseTestCase):
    def testFloat4BinEnc(self):
        assert univ.Real((0.25, 2, 3)) == 2.0, 'float initializer for binary encoding fails'

    def testStr(self):
        assert str(univ.Real(1.0)) == '1.0', 'str() fails'

    def testRepr(self):
        assert 'Real' in repr(univ.Real(-4.1))
        assert 'Real' in repr(univ.Real(-4.1))
        assert 'inf' in repr(univ.Real('inf'))
        assert '-inf' in repr(univ.Real('-inf'))

    def testAdd(self):
        assert univ.Real(-4.1) + 1.4 == -2.7, '__add__() fails'

    def testRadd(self):
        assert 4 + univ.Real(0.5) == 4.5, '__radd__() fails'

    def testSub(self):
        assert univ.Real(3.9) - 1.7 == 2.2, '__sub__() fails'

    def testRsub(self):
        assert 6.1 - univ.Real(0.1) == 6, '__rsub__() fails'

    def testMul(self):
        assert univ.Real(3.0) * -3 == -9, '__mul__() fails'

    def testRmul(self):
        assert 2 * univ.Real(3.0) == 6, '__rmul__() fails'

    def testDiv(self):
        assert univ.Real(3.0) / 2 == 1.5, '__div__() fails'

    def testRdiv(self):
        assert 6 / univ.Real(3.0) == 2, '__rdiv__() fails'

    def testMod(self):
        assert univ.Real(3.0) % 2 == 1, '__mod__() fails'

    def testRmod(self):
        assert 4 % univ.Real(3.0) == 1, '__rmod__() fails'

    def testPow(self):
        assert univ.Real(3.0) ** 2 == 9, '__pow__() fails'

    def testRpow(self):
        assert 2 ** univ.Real(2.0) == 4, '__rpow__() fails'

    def testInt(self):
        assert int(univ.Real(3.0)) == 3, '__int__() fails'

    def testLong(self):
        assert int(univ.Real(8.0)) == 8, '__long__() fails'

    def testFloat(self):
        assert float(univ.Real(4.0)) == 4.0, '__float__() fails'

    def testPrettyIn(self):
        assert univ.Real((3, 10, 0)) == 3, 'prettyIn() fails'

    # infinite float values
    def testStrInf(self):
        assert str(univ.Real('inf')) == 'inf', 'str() fails'

    def testAddInf(self):
        assert univ.Real('inf') + 1 == float('inf'), '__add__() fails'

    def testRaddInf(self):
        assert 1 + univ.Real('inf') == float('inf'), '__radd__() fails'

    def testIntInf(self):
        try:
            assert int(univ.Real('inf'))
        except OverflowError:
            pass
        else:
            assert 0, '__int__() fails'

    def testLongInf(self):
        try:
            assert int(univ.Real('inf'))
        except OverflowError:
            pass
        else:
            assert 0, '__long__() fails'
        assert int(univ.Real(8.0)) == 8, '__long__() fails'

    def testFloatInf(self):
        assert float(univ.Real('-inf')) == float('-inf'), '__float__() fails'

    def testPrettyInInf(self):
        assert univ.Real(float('inf')) == float('inf'), 'prettyIn() fails'

    def testPlusInf(self):
        assert univ.Real('inf').isPlusInf, 'isPlusInfinity failed'

    def testMinusInf(self):
        assert univ.Real('-inf').isMinusInf, 'isMinusInfinity failed'

    def testPos(self):
        assert +univ.Real(1.0) == 1.0, '__pos__() fails'

    def testNeg(self):
        assert -univ.Real(1.0) == -1.0, '__neg__() fails'

    def testRound(self):
        assert round(univ.Real(1.123), 2) == 1.12, '__round__() fails'

    def testFloor(self):
        assert math.floor(univ.Real(1.6)) == 1.0, '__floor__() fails'

    def testCeil(self):
        assert math.ceil(univ.Real(1.2)) == 2.0, '__ceil__() fails'

    if sys.version_info[0:2] > (2, 5):
        def testTrunc(self):
            assert math.trunc(univ.Real(1.1)) == 1.0, '__trunc__() fails'

    def testTag(self):
        assert univ.Real().tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x09)
        )

    def testStaticDef(self):

        class Real(univ.Real):
            pass

        assert Real(1.0) == 1.0


class RealPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.Real()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.Real
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.Real((1, 10, 3))
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == 1000


class ObjectIdentifier(BaseTestCase):
    def testStr(self):
        assert str(univ.ObjectIdentifier((1, 3, 6))) == '1.3.6', 'str() fails'

    def testRepr(self):
        assert '1.3.6' in repr(univ.ObjectIdentifier('1.3.6'))

    def testEq(self):
        assert univ.ObjectIdentifier((1, 3, 6)) == (1, 3, 6), '__cmp__() fails'

    def testAdd(self):
        assert univ.ObjectIdentifier((1, 3)) + (6,) == (1, 3, 6), '__add__() fails'

    def testRadd(self):
        assert (1,) + univ.ObjectIdentifier((3, 6)) == (1, 3, 6), '__radd__() fails'

    def testLen(self):
        assert len(univ.ObjectIdentifier((1, 3))) == 2, '__len__() fails'

    def testPrefix(self):
        o = univ.ObjectIdentifier('1.3.6')
        assert o.isPrefixOf((1, 3, 6)), 'isPrefixOf() fails'
        assert o.isPrefixOf((1, 3, 6, 1)), 'isPrefixOf() fails'
        assert not o.isPrefixOf((1, 3)), 'isPrefixOf() fails'

    def testInput1(self):
        assert univ.ObjectIdentifier('1.3.6') == (1, 3, 6), 'prettyIn() fails'

    def testInput2(self):
        assert univ.ObjectIdentifier((1, 3, 6)) == (1, 3, 6), 'prettyIn() fails'

    def testInput3(self):
        assert univ.ObjectIdentifier(univ.ObjectIdentifier('1.3') + (6,)) == (1, 3, 6), 'prettyIn() fails'

    def testUnicode(self):
        s = '1.3.6'
        if sys.version_info[0] < 3:
            s = s.decode()
        assert univ.ObjectIdentifier(s) == (1, 3, 6), 'unicode init fails'

    def testTag(self):
        assert univ.ObjectIdentifier().tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 0x06)
        )

    def testContains(self):
        s = univ.ObjectIdentifier('1.3.6.1234.99999')
        assert 1234 in s
        assert 4321 not in s

    def testStaticDef(self):

        class ObjectIdentifier(univ.ObjectIdentifier):
            pass

        assert str(ObjectIdentifier((1, 3, 6))) == '1.3.6'


class ObjectIdentifierPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.ObjectIdentifier()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.ObjectIdentifier
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.ObjectIdentifier('2.3.1.1.2')
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == (2, 3, 1, 1, 2)


class SequenceOf(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s1 = univ.SequenceOf(
            componentType=univ.OctetString('')
        )
        self.s2 = self.s1.clone()

    def testRepr(self):
        assert 'a' in repr(self.s1.clone().setComponents('a', 'b'))

    def testTag(self):
        assert self.s1.tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x10)
        ), 'wrong tagSet'

    def testSeq(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        assert self.s1[0] == str2octs('abc'), 'set by idx fails'
        self.s1[0] = 'cba'
        assert self.s1[0] == str2octs('cba'), 'set by idx fails'

    def testCmp(self):
        self.s1.clear()
        self.s1.setComponentByPosition(0, 'abc')
        self.s2.clear()
        self.s2.setComponentByPosition(0, univ.OctetString('abc'))
        assert self.s1 == self.s2, '__cmp__() fails'

    def testSubtypeSpec(self):
        s = self.s1.clone(subtypeSpec=constraint.ConstraintsUnion(
            constraint.SingleValueConstraint(str2octs('abc'))
        ))
        try:
            s.setComponentByPosition(0, univ.OctetString('abc'))
        except PyAsn1Error:
            assert 0, 'constraint fails'
        try:
            s.setComponentByPosition(1, univ.OctetString('Abc'))
        except PyAsn1Error:
            try:
                s.setComponentByPosition(1, univ.OctetString('Abc'),
                                         verifyConstraints=False)
            except PyAsn1Error:
                assert 0, 'constraint failes with verifyConstraints=True'
        else:
            assert 0, 'constraint fails'

    def testComponentTagsMatching(self):
        s = self.s1.clone()
        s.strictConstraints = True  # This requires types equality
        o = univ.OctetString('abc').subtype(explicitTag=tag.Tag(tag.tagClassPrivate, tag.tagFormatSimple, 12))
        try:
            s.setComponentByPosition(0, o)
        except PyAsn1Error:
            pass
        else:
            assert 0, 'inner supertype tag allowed'

    def testComponentConstraintsMatching(self):
        s = self.s1.clone()
        o = univ.OctetString().subtype(
            subtypeSpec=constraint.ConstraintsUnion(constraint.SingleValueConstraint(str2octs('cba'))))
        s.strictConstraints = True  # This requires types equality
        try:
            s.setComponentByPosition(0, o.clone('cba'))
        except PyAsn1Error:
            pass
        else:
            assert 0, 'inner supertype constraint allowed'
        s.strictConstraints = False  # This requires subtype relationships
        try:
            s.setComponentByPosition(0, o.clone('cba'))
        except PyAsn1Error:
            assert 0, 'inner supertype constraint disallowed'
        else:
            pass

    def testSizeSpec(self):
        s = self.s1.clone(sizeSpec=constraint.ConstraintsUnion(
            constraint.ValueSizeConstraint(1, 1)
        ))
        s.setComponentByPosition(0, univ.OctetString('abc'))
        try:
            s.verifySizeSpec()
        except PyAsn1Error:
            assert 0, 'size spec fails'
        s.setComponentByPosition(1, univ.OctetString('abc'))
        try:
            s.verifySizeSpec()
        except PyAsn1Error:
            pass
        else:
            assert 0, 'size spec fails'

    def testGetComponentTagMap(self):
        assert self.s1.componentType.tagMap.presentTypes == {
            univ.OctetString.tagSet: univ.OctetString('')
        }

    def testSubtype(self):
        self.s1.clear()
        assert self.s1.subtype(
            implicitTag=tag.Tag(tag.tagClassPrivate, tag.tagFormatSimple, 2),
            subtypeSpec=constraint.SingleValueConstraint(1, 3),
            sizeSpec=constraint.ValueSizeConstraint(0, 1)
        ) == self.s1.clone(
            tagSet=tag.TagSet(tag.Tag(tag.tagClassPrivate,
                                      tag.tagFormatSimple, 2)),
            subtypeSpec=constraint.ConstraintsIntersection(constraint.SingleValueConstraint(1, 3)),
            sizeSpec=constraint.ValueSizeConstraint(0, 1)
        )

    def testClone(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        s = self.s1.clone()
        assert len(s) == 0
        s = self.s1.clone(cloneValueFlag=1)
        assert len(s) == 1
        assert s.getComponentByPosition(0) == self.s1.getComponentByPosition(0)

    def testSetComponents(self):
        assert self.s1.clone().setComponents('abc', 'def') == \
               self.s1.setComponentByPosition(0, 'abc').setComponentByPosition(1, 'def')

    def testGetItem(self):
        s = self.s1.clone()
        s.append('xxx')
        assert s[0]

        try:
            s[2]

        except IndexError:
            pass

        else:
            assert False, 'IndexError not raised'

        # this is a deviation from standart sequence protocol
        assert not s[1]

    def testSetItem(self):
        s = self.s1.clone()
        s.append('xxx')

        try:

            s[2] = 'xxx'

        except IndexError:
            pass

        else:
            assert False, 'IndexError not raised'

    def testAppend(self):
        self.s1.clear()
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        assert len(self.s1) == 1
        self.s1.append('def')
        assert len(self.s1) == 2
        assert list(self.s1) == [str2octs(x) for x in ['abc', 'def']]

    def testExtend(self):
        self.s1.clear()
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        assert len(self.s1) == 1
        self.s1.extend(['def', 'ghi'])
        assert len(self.s1) == 3
        assert list(self.s1) == [str2octs(x) for x in ['abc', 'def', 'ghi']]

    def testCount(self):
        self.s1.clear()
        for x in ['abc', 'def', 'abc']:
            self.s1.append(x)
        assert self.s1.count(str2octs('abc')) == 2
        assert self.s1.count(str2octs('def')) == 1
        assert self.s1.count(str2octs('ghi')) == 0

    def testIndex(self):
        self.s1.clear()
        for x in ['abc', 'def', 'abc']:
            self.s1.append(x)
        assert self.s1.index(str2octs('abc')) == 0
        assert self.s1.index(str2octs('def')) == 1
        assert self.s1.index(str2octs('abc'), 1) == 2

    def testSort(self):
        self.s1.clear()
        self.s1[0] = 'b'
        self.s1[1] = 'a'
        assert list(self.s1) == [str2octs('b'), str2octs('a')]
        self.s1.sort()
        assert list(self.s1) == [str2octs('a'), str2octs('b')]

    def testStaticDef(self):

        class SequenceOf(univ.SequenceOf):
            componentType = univ.OctetString('')

        s = SequenceOf()
        s[0] = 'abc'
        assert len(s) == 1
        assert s == [str2octs('abc')]

    def testLegacyInitializer(self):
        n = univ.SequenceOf(
            componentType=univ.OctetString()
        )
        o = univ.SequenceOf(
            univ.OctetString()  # this is the old way
        )

        assert n.isSameTypeWith(o) and o.isSameTypeWith(n)

        n[0] = 'fox'
        o[0] = 'fox'

        assert n == o

    def testGetComponentWithDefault(self):

        class SequenceOf(univ.SequenceOf):
            componentType = univ.OctetString()

        s = SequenceOf()
        assert s.getComponentByPosition(0, default=None, instantiate=False) is None
        assert s.getComponentByPosition(0, default=None) is None
        s[0] = 'test'
        assert s.getComponentByPosition(0, default=None) is not None
        assert s.getComponentByPosition(0, default=None) == str2octs('test')
        s.clear()
        assert s.getComponentByPosition(0, default=None) is None

    def testGetComponentNoInstantiation(self):

        class SequenceOf(univ.SequenceOf):
            componentType = univ.OctetString()

        s = SequenceOf()
        assert s.getComponentByPosition(0, instantiate=False) is univ.noValue
        s[0] = 'test'
        assert s.getComponentByPosition(0, instantiate=False) is not univ.noValue
        assert s.getComponentByPosition(0, instantiate=False) == str2octs('test')
        s.clear()
        assert s.getComponentByPosition(0, instantiate=False) is univ.noValue


class SequenceOfPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.SequenceOf(componentType=univ.OctetString())
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.SequenceOf
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.SequenceOf(componentType=univ.OctetString())
        old_asn1[0] = 'test'
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1
        assert new_asn1 == [str2octs('test')]


class Sequence(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s1 = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString('')),
                namedtype.OptionalNamedType('nick', univ.OctetString('')),
                namedtype.DefaultedNamedType('age', univ.Integer(34))
            )
        )

    def testRepr(self):
        assert 'name' in repr(self.s1.clone().setComponents('a', 'b'))

    def testTag(self):
        assert self.s1.tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x10)
        ), 'wrong tagSet'

    def testById(self):
        self.s1.setComponentByName('name', univ.OctetString('abc'))
        assert self.s1.getComponentByName('name') == str2octs('abc'), 'set by name fails'

    def testByKey(self):
        self.s1['name'] = 'abc'
        assert self.s1['name'] == str2octs('abc'), 'set by key fails'

    def testContains(self):
        assert 'name' in self.s1
        assert '<missing>' not in self.s1

    def testGetNearPosition(self):
        assert self.s1.componentType.getTagMapNearPosition(1).presentTypes == {
            univ.OctetString.tagSet: univ.OctetString(''),
            univ.Integer.tagSet: univ.Integer(34)
        }
        assert self.s1.componentType.getPositionNearType(
            univ.OctetString.tagSet, 1
        ) == 1

    def testSetDefaultComponents(self):
        self.s1.clear()
        self.s1.setComponentByPosition(0, univ.OctetString('Ping'))
        self.s1.setComponentByPosition(1, univ.OctetString('Pong'))
        assert self.s1.getComponentByPosition(2) == 34

    def testClone(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        self.s1.setComponentByPosition(1, univ.OctetString('def'))
        self.s1.setComponentByPosition(2, univ.Integer(123))
        s = self.s1.clone()
        assert s.getComponentByPosition(0) != self.s1.getComponentByPosition(0)
        assert s.getComponentByPosition(1) != self.s1.getComponentByPosition(1)
        assert s.getComponentByPosition(2) != self.s1.getComponentByPosition(2)
        s = self.s1.clone(cloneValueFlag=1)
        assert s.getComponentByPosition(0) == self.s1.getComponentByPosition(0)
        assert s.getComponentByPosition(1) == self.s1.getComponentByPosition(1)
        assert s.getComponentByPosition(2) == self.s1.getComponentByPosition(2)

    def testComponentTagsMatching(self):
        s = self.s1.clone()
        s.strictConstraints = True  # This requires types equality
        o = univ.OctetString('abc').subtype(explicitTag=tag.Tag(tag.tagClassPrivate, tag.tagFormatSimple, 12))
        try:
            s.setComponentByName('name', o)
        except PyAsn1Error:
            pass
        else:
            assert 0, 'inner supertype tag allowed'

    def testComponentConstraintsMatching(self):
        s = self.s1.clone()
        o = univ.OctetString().subtype(
            subtypeSpec=constraint.ConstraintsUnion(constraint.SingleValueConstraint(str2octs('cba'))))
        s.strictConstraints = True  # This requires types equality
        try:
            s.setComponentByName('name', o.clone('cba'))
        except PyAsn1Error:
            pass
        else:
            assert 0, 'inner supertype constraint allowed'
        s.strictConstraints = False  # This requires subtype relationships
        try:
            s.setComponentByName('name', o.clone('cba'))
        except PyAsn1Error:
            assert 0, 'inner supertype constraint disallowed'
        else:
            pass

    def testSetComponents(self):
        assert self.s1.clone().setComponents(name='a', nick='b', age=1) == \
               self.s1.setComponentByPosition(0, 'a').setComponentByPosition(1, 'b').setComponentByPosition(2, 1)

    def testSetToDefault(self):
        s = self.s1.clone()
        s.setComponentByPosition(0, univ.noValue)
        s[2] = univ.noValue
        assert s[0] == univ.OctetString('')
        assert s[2] == univ.Integer(34)

    def testGetItem(self):
        s = self.s1.clone()
        s['name'] = 'xxx'
        assert s['name']
        assert s[0]

        try:
            s['xxx']

        except KeyError:
            pass

        else:
            assert False, 'KeyError not raised'

        try:
            s[100]

        except IndexError:
            pass

        else:
            assert False, 'IndexError not raised'

    def testSetItem(self):
        s = self.s1.clone()
        s['name'] = 'xxx'

        try:

            s['xxx'] = 'xxx'

        except KeyError:
            pass

        else:
            assert False, 'KeyError not raised'

        try:

            s[100] = 'xxx'

        except IndexError:
            pass

        else:
            assert False, 'IndexError not raised'

    def testIter(self):
        assert list(self.s1) == ['name', 'nick', 'age']

    def testKeys(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        self.s1.setComponentByPosition(1, univ.OctetString('def'))
        self.s1.setComponentByPosition(2, univ.Integer(123))
        assert list(self.s1.keys()) == ['name', 'nick', 'age']

    def testValues(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        self.s1.setComponentByPosition(1, univ.OctetString('def'))
        self.s1.setComponentByPosition(2, univ.Integer(123))
        assert list(self.s1.values()) == [str2octs('abc'), str2octs('def'), 123]

    def testItems(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        self.s1.setComponentByPosition(1, univ.OctetString('def'))
        self.s1.setComponentByPosition(2, univ.Integer(123))
        assert list(self.s1.items()) == [(x[0], str2octs(x[1])) for x in [('name', 'abc'), ('nick', 'def')]] + [('age', 123)]

    def testUpdate(self):
        self.s1.clear()
        assert list(self.s1.values()) == [str2octs(''), str2octs(''), 34]
        self.s1.update(**{'name': 'abc', 'nick': 'def', 'age': 123})
        assert list(self.s1.items()) == [(x[0], str2octs(x[1])) for x in [('name', 'abc'), ('nick', 'def')]] + [('age', 123)]
        self.s1.update(('name', 'ABC'))
        assert list(self.s1.items()) == [(x[0], str2octs(x[1])) for x in [('name', 'ABC'), ('nick', 'def')]] + [('age', 123)]
        self.s1.update(name='CBA')
        assert list(self.s1.items()) == [(x[0], str2octs(x[1])) for x in [('name', 'CBA'), ('nick', 'def')]] + [('age', 123)]

    def testStaticDef(self):

        class Sequence(univ.Sequence):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString('')),
                namedtype.OptionalNamedType('nick', univ.OctetString('')),
                namedtype.DefaultedNamedType('age', univ.Integer(34))
            )

        s = Sequence()
        s['name'] = 'abc'
        assert s['name'] == str2octs('abc')

    def testGetComponentWithDefault(self):

        class Sequence(univ.Sequence):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString('')),
                namedtype.OptionalNamedType('nick', univ.OctetString()),
            )

        s = Sequence()

        assert s[0] == str2octs('')
        assert s.getComponentByPosition(1, default=None, instantiate=False) is None
        assert s.getComponentByName('nick', default=None) is None
        s[1] = 'test'
        assert s.getComponentByPosition(1, default=None) is not None
        assert s.getComponentByPosition(1, default=None) == str2octs('test')
        s.clear()
        assert s.getComponentByPosition(1, default=None) is None

    def testGetComponentNoInstantiation(self):

        class Sequence(univ.Sequence):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString('')),
                namedtype.OptionalNamedType('nick', univ.OctetString()),
            )

        s = Sequence()
        assert s[0] == str2octs('')
        assert s.getComponentByPosition(1, instantiate=False) is univ.noValue
        assert s.getComponentByName('nick', instantiate=False) is univ.noValue
        s[1] = 'test'
        assert s.getComponentByPosition(1, instantiate=False) is not univ.noValue
        assert s.getComponentByPosition(1, instantiate=False) == str2octs('test')
        s.clear()
        assert s.getComponentByPosition(1, instantiate=False) is univ.noValue


class SequenceWithoutSchema(BaseTestCase):

    def testGetItem(self):
        s = univ.Sequence()
        s.setComponentByPosition(0, univ.OctetString('abc'))
        s[0] = 'abc'
        assert s['field-0']
        assert s[0]

        try:
            s['field-1']

        except KeyError:
            pass

        else:
            assert False, 'KeyError not raised'

    def testSetItem(self):
        s = univ.Sequence()
        s.setComponentByPosition(0, univ.OctetString('abc'))
        s['field-0'] = 'xxx'

        try:

            s['field-1'] = 'xxx'

        except KeyError:
            pass

        else:
            assert False, 'KeyError not raised'

    def testIter(self):
        s = univ.Sequence()
        s.setComponentByPosition(0, univ.OctetString('abc'))
        s.setComponentByPosition(1, univ.Integer(123))
        assert list(s) == ['field-0', 'field-1']

    def testKeys(self):
        s = univ.Sequence()
        s.setComponentByPosition(0, univ.OctetString('abc'))
        s.setComponentByPosition(1, univ.Integer(123))
        assert list(s.keys()) == ['field-0', 'field-1']

    def testValues(self):
        s = univ.Sequence()
        s.setComponentByPosition(0, univ.OctetString('abc'))
        s.setComponentByPosition(1, univ.Integer(123))
        assert list(s.values()) == [str2octs('abc'), 123]

    def testItems(self):
        s = univ.Sequence()
        s.setComponentByPosition(0, univ.OctetString('abc'))
        s.setComponentByPosition(1, univ.Integer(123))
        assert list(s.items()) == [('field-0', str2octs('abc')), ('field-1', 123)]

    def testUpdate(self):
        s = univ.Sequence()
        assert not s
        s.setComponentByPosition(0, univ.OctetString('abc'))
        s.setComponentByPosition(1, univ.Integer(123))
        assert s
        assert list(s.keys()) == ['field-0', 'field-1']
        assert list(s.values()) == [str2octs('abc'), 123]
        assert list(s.items()) == [('field-0', str2octs('abc')), ('field-1', 123)]
        s['field-0'] = univ.OctetString('def')
        assert list(s.values()) == [str2octs('def'), 123]
        s['field-1'] = univ.OctetString('ghi')
        assert list(s.values()) == [str2octs('def'), str2octs('ghi')]
        try:
            s['field-2'] = univ.OctetString('xxx')
        except KeyError:
            pass
        else:
            assert False, 'unknown field at schema-less object tolerated'
        assert 'field-0' in s
        s.clear()
        assert 'field-0' not in s


class SequencePicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString())
            )
        )
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.Sequence
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString())
            )
        )
        old_asn1['name'] = 'test'
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1
        assert new_asn1['name'] == str2octs('test')


class SetOf(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s1 = univ.SetOf(componentType=univ.OctetString(''))

    def testTag(self):
        assert self.s1.tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x11)
        ), 'wrong tagSet'

    def testSeq(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        assert self.s1[0] == str2octs('abc'), 'set by idx fails'
        self.s1.setComponentByPosition(0, self.s1[0].clone('cba'))
        assert self.s1[0] == str2octs('cba'), 'set by idx fails'

    def testStaticDef(self):

        class SetOf(univ.SequenceOf):
            componentType = univ.OctetString('')

        s = SetOf()
        s[0] = 'abc'
        assert len(s) == 1
        assert s == [str2octs('abc')]



class SetOfPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.SetOf(componentType=univ.OctetString())
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.SetOf
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.SetOf(componentType=univ.OctetString())
        old_asn1[0] = 'test'
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1
        assert new_asn1 == [str2octs('test')]


class Set(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        self.s1 = univ.Set(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString('')),
                namedtype.OptionalNamedType('null', univ.Null('')),
                namedtype.DefaultedNamedType('age', univ.Integer(34))
            )
        )
        self.s2 = self.s1.clone()

    def testTag(self):
        assert self.s1.tagSet == tag.TagSet(
            (),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatConstructed, 0x11)
        ), 'wrong tagSet'

    def testByTypeWithPythonValue(self):
        self.s1.setComponentByType(univ.OctetString.tagSet, 'abc')
        assert self.s1.getComponentByType(
            univ.OctetString.tagSet
        ) == str2octs('abc'), 'set by name fails'

    def testByTypeWithInstance(self):
        self.s1.setComponentByType(univ.OctetString.tagSet, univ.OctetString('abc'))
        assert self.s1.getComponentByType(
            univ.OctetString.tagSet
        ) == str2octs('abc'), 'set by name fails'

    def testGetTagMap(self):
        assert self.s1.tagMap.presentTypes == {
            univ.Set.tagSet: univ.Set()
        }

    def testGetComponentTagMap(self):
        assert self.s1.componentType.tagMapUnique.presentTypes == {
            univ.OctetString.tagSet: univ.OctetString(''),
            univ.Null.tagSet: univ.Null(''),
            univ.Integer.tagSet: univ.Integer(34)
        }

    def testGetPositionByType(self):
        assert self.s1.componentType.getPositionByType(univ.Null().tagSet) == 1

    def testSetToDefault(self):
        self.s1.setComponentByName('name', univ.noValue)
        assert self.s1['name'] == univ.OctetString('')

    def testIter(self):
        assert list(self.s1) == ['name', 'null', 'age']

    def testStaticDef(self):

        class Set(univ.Set):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString('')),
                namedtype.OptionalNamedType('nick', univ.OctetString('')),
                namedtype.DefaultedNamedType('age', univ.Integer(34))
            )

        s = Set()
        s['name'] = 'abc'
        assert s['name'] == str2octs('abc')

    def testGetComponentWithDefault(self):

        class Set(univ.Set):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer(123)),
                namedtype.OptionalNamedType('nick', univ.OctetString()),
            )

        s = Set()
        assert s[0] == 123
        assert s.getComponentByPosition(1, default=None, instantiate=False) is None
        assert s.getComponentByName('nick', default=None) is None
        s[1] = 'test'
        assert s.getComponentByPosition(1, default=None) is not None
        assert s.getComponentByPosition(1, default=None) == str2octs('test')
        s.clear()
        assert s.getComponentByPosition(1, default=None) is None

    def testGetComponentNoInstantiation(self):

        class Set(univ.Set):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer(123)),
                namedtype.OptionalNamedType('nick', univ.OctetString()),
            )

        s = Set()
        assert s[0] == 123
        assert s.getComponentByPosition(1, instantiate=False) is univ.noValue
        assert s.getComponentByName('nick', instantiate=False) is univ.noValue
        assert s.getComponentByType(univ.OctetString.tagSet, instantiate=False) is univ.noValue
        s[1] = 'test'
        assert s.getComponentByPosition(1, instantiate=False) is not univ.noValue
        assert s.getComponentByPosition(1, instantiate=False) == str2octs('test')
        s.clear()
        assert s.getComponentByPosition(1, instantiate=False) is univ.noValue


class SetPicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.Set(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString())
            )
        )
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.Set
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.Set(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString())
            )
        )
        old_asn1['name'] = 'test'
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1
        assert new_asn1['name'] == str2octs('test')


class Choice(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        innerComp = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('count', univ.Integer()),
                namedtype.NamedType('flag', univ.Boolean())
            )
        )
        self.s1 = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('sex', innerComp)
            )
        )

    def testTag(self):
        assert self.s1.tagSet == tag.TagSet(), 'wrong tagSet'

    def testRepr(self):
        assert 'Choice' in repr(self.s1.clone().setComponents('a'))
        s = self.s1.clone().setComponents(
                sex=self.s1.setComponentByPosition(1).getComponentByPosition(1).clone().setComponents(count=univ.Integer(123))
        )
        assert 'Choice' in repr(s)

    def testContains(self):
        self.s1.setComponentByType(univ.OctetString.tagSet, 'abc')
        assert 'name' in self.s1
        assert 'sex' not in self.s1

        self.s1.setComponentByType(univ.Integer.tagSet, 123, innerFlag=True)
        assert 'name' not in self.s1
        assert 'sex' in self.s1

    def testIter(self):
        self.s1.setComponentByType(univ.OctetString.tagSet, 'abc')
        assert list(self.s1) == ['name']
        self.s1.setComponentByType(univ.Integer.tagSet, 123, innerFlag=True)
        assert list(self.s1) == ['sex']

    def testOuterByTypeWithPythonValue(self):
        self.s1.setComponentByType(univ.OctetString.tagSet, 'abc')
        assert self.s1.getComponentByType(
            univ.OctetString.tagSet
        ) == str2octs('abc')

    def testOuterByTypeWithInstanceValue(self):
        self.s1.setComponentByType(
            univ.OctetString.tagSet, univ.OctetString('abc')
        )
        assert self.s1.getComponentByType(
            univ.OctetString.tagSet
        ) == str2octs('abc')

    def testInnerByTypeWithPythonValue(self):
        self.s1.setComponentByType(univ.Integer.tagSet, 123, innerFlag=True)
        assert self.s1.getComponentByType(
            univ.Integer.tagSet, 1
        ) == 123

    def testInnerByTypeWithInstanceValue(self):
        self.s1.setComponentByType(
            univ.Integer.tagSet, univ.Integer(123), innerFlag=True
        )
        assert self.s1.getComponentByType(
            univ.Integer.tagSet, 1
        ) == 123

    def testCmp(self):
        self.s1.setComponentByName('name', univ.OctetString('abc'))
        assert self.s1 == str2octs('abc'), '__cmp__() fails'

    def testGetComponent(self):
        self.s1.setComponentByType(univ.OctetString.tagSet, 'abc')
        assert self.s1.getComponent() == str2octs('abc'), 'getComponent() fails'

    def testGetName(self):
        self.s1.setComponentByType(univ.OctetString.tagSet, 'abc')
        assert self.s1.getName() == 'name', 'getName() fails'

    def testSetComponentByPosition(self):
        self.s1.setComponentByPosition(0, univ.OctetString('Jim'))
        assert self.s1 == str2octs('Jim')

    def testClone(self):
        self.s1.setComponentByPosition(0, univ.OctetString('abc'))
        s = self.s1.clone()
        assert len(s) == 0
        s = self.s1.clone(cloneValueFlag=1)
        assert len(s) == 1
        assert s.getComponentByPosition(0) == self.s1.getComponentByPosition(0)

    def testSetToDefault(self):
        s = self.s1.clone()
        s.setComponentByName('sex', univ.noValue)
        assert s['sex'] is not univ.noValue

    def testStaticDef(self):

        class InnerChoice(univ.Choice):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('count', univ.Integer()),
                namedtype.NamedType('flag', univ.Boolean())
            )

        class OuterChoice(univ.Choice):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('sex', InnerChoice())
            )

        c = OuterChoice()

        c.setComponentByType(univ.OctetString.tagSet, 'abc')
        assert c.getName() == 'name'

    def testGetComponentWithDefault(self):

        s = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('id', univ.Integer())
            )
        )

        assert s.getComponentByPosition(0, default=None, instantiate=False) is None
        assert s.getComponentByPosition(1, default=None, instantiate=False) is None
        assert s.getComponentByName('name', default=None, instantiate=False) is None
        assert s.getComponentByName('id', default=None, instantiate=False) is None
        assert s.getComponentByType(univ.OctetString.tagSet, default=None) is None
        assert s.getComponentByType(univ.Integer.tagSet, default=None) is None
        s[1] = 123
        assert s.getComponentByPosition(1, default=None) is not None
        assert s.getComponentByPosition(1, univ.noValue) == 123
        s.clear()
        assert s.getComponentByPosition(1, default=None, instantiate=False) is None

    def testGetComponentNoInstantiation(self):

        s = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('id', univ.Integer())
            )
        )

        assert s.getComponentByPosition(0, instantiate=False) is univ.noValue
        assert s.getComponentByPosition(1, instantiate=False) is univ.noValue
        assert s.getComponentByName('name', instantiate=False) is univ.noValue
        assert s.getComponentByName('id', instantiate=False) is univ.noValue
        assert s.getComponentByType(univ.OctetString.tagSet, instantiate=False) is univ.noValue
        assert s.getComponentByType(univ.Integer.tagSet, instantiate=False) is univ.noValue
        s[1] = 123
        assert s.getComponentByPosition(1, instantiate=False) is not univ.noValue
        assert s.getComponentByPosition(1, instantiate=False) == 123
        s.clear()
        assert s.getComponentByPosition(1, instantiate=False) is univ.noValue


class ChoicePicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('id', univ.Integer())
            )
        )
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == univ.Choice
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('id', univ.Integer())
            )
        )
        old_asn1['name'] = 'test'
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1
        assert new_asn1['name'] == str2octs('test')


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
