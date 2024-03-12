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
from pyasn1.type import univ
from pyasn1.type import useful
from pyasn1.codec.cer import encoder
from pyasn1.compat.octets import ints2octs
from pyasn1.error import PyAsn1Error


class BooleanEncoderTestCase(BaseTestCase):
    def testTrue(self):
        assert encoder.encode(univ.Boolean(1)) == ints2octs((1, 1, 255))

    def testFalse(self):
        assert encoder.encode(univ.Boolean(0)) == ints2octs((1, 1, 0))


class BitStringEncoderTestCase(BaseTestCase):
    def testShortMode(self):
        assert encoder.encode(
            univ.BitString((1, 0) * 5)
        ) == ints2octs((3, 3, 6, 170, 128))

    def testLongMode(self):
        assert encoder.encode(univ.BitString((1, 0) * 501)) == ints2octs((3, 127, 6) + (170,) * 125 + (128,))


class OctetStringEncoderTestCase(BaseTestCase):
    def testShortMode(self):
        assert encoder.encode(
            univ.OctetString('Quick brown fox')
        ) == ints2octs((4, 15, 81, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 32, 102, 111, 120))

    def testLongMode(self):
        assert encoder.encode(
            univ.OctetString('Q' * 1001)
        ) == ints2octs((36, 128, 4, 130, 3, 232) + (81,) * 1000 + (4, 1, 81, 0, 0))


class GeneralizedTimeEncoderTestCase(BaseTestCase):
    #    def testExtraZeroInSeconds(self):
    #        try:
    #            assert encoder.encode(
    #                useful.GeneralizedTime('20150501120112.10Z')
    #            )
    #        except PyAsn1Error:
    #            pass
    #        else:
    #            assert 0, 'Meaningless trailing zero in fraction part tolerated'

    def testLocalTimezone(self):
        try:
            assert encoder.encode(
                useful.GeneralizedTime('20150501120112.1+0200')
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'Local timezone tolerated'

    def testMissingTimezone(self):
        try:
            assert encoder.encode(
                useful.GeneralizedTime('20150501120112.1')
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'Missing timezone tolerated'


    def testDecimalCommaPoint(self):
        try:
            assert encoder.encode(
                    useful.GeneralizedTime('20150501120112,1Z')
             )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'Decimal comma tolerated'

    def testWithSubseconds(self):
        assert encoder.encode(
                    useful.GeneralizedTime('20170801120112.59Z')
             ) == ints2octs((24, 18, 50, 48, 49, 55, 48, 56, 48, 49, 49, 50, 48, 49, 49, 50, 46, 53, 57, 90))

    def testWithSeconds(self):
        assert encoder.encode(
                    useful.GeneralizedTime('20170801120112Z')
             ) == ints2octs((24, 15, 50, 48, 49, 55, 48, 56, 48, 49, 49, 50, 48, 49, 49, 50, 90))

    def testWithMinutes(self):
        assert encoder.encode(
                    useful.GeneralizedTime('201708011201Z')
             ) == ints2octs((24, 13, 50, 48, 49, 55, 48, 56, 48, 49, 49, 50, 48, 49, 90))


class UTCTimeEncoderTestCase(BaseTestCase):
    def testFractionOfSecond(self):
        try:
            assert encoder.encode(
                useful.UTCTime('150501120112.10Z')
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'Decimal point tolerated'

    def testMissingTimezone(self):
        try:
            assert encoder.encode(
                useful.UTCTime('150501120112')
            ) == ints2octs((23, 13, 49, 53, 48, 53, 48, 49, 49, 50, 48, 49, 49, 50, 90))
        except PyAsn1Error:
            pass
        else:
            assert 0, 'Missing timezone tolerated'

    def testLocalTimezone(self):
        try:
            assert encoder.encode(
                useful.UTCTime('150501120112+0200')
            )
        except PyAsn1Error:
            pass
        else:
            assert 0, 'Local timezone tolerated'

    def testWithSeconds(self):
        assert encoder.encode(
                    useful.UTCTime('990801120112Z')
             ) == ints2octs((23, 13, 57, 57, 48, 56, 48, 49, 49, 50, 48, 49, 49, 50, 90))

    def testWithMinutes(self):
        assert encoder.encode(
                    useful.UTCTime('9908011201Z')
             ) == ints2octs((23, 11, 57, 57, 48, 56, 48, 49, 49, 50, 48, 49, 90))


class SequenceOfEncoderTestCase(BaseTestCase):
    def testEmpty(self):
        s = univ.SequenceOf()
        assert encoder.encode(s) == ints2octs((48, 128, 0, 0))

    def testDefMode1(self):
        s = univ.SequenceOf()
        s.append(univ.OctetString('a'))
        s.append(univ.OctetString('ab'))
        assert encoder.encode(s) == ints2octs((48, 128, 4, 1, 97, 4, 2, 97, 98, 0, 0))

    def testDefMode2(self):
        s = univ.SequenceOf()
        s.append(univ.OctetString('ab'))
        s.append(univ.OctetString('a'))
        assert encoder.encode(s) == ints2octs((48, 128, 4, 2, 97, 98, 4, 1, 97, 0, 0))

    def testDefMode3(self):
        s = univ.SequenceOf()
        s.append(univ.OctetString('b'))
        s.append(univ.OctetString('a'))
        assert encoder.encode(s) == ints2octs((48, 128, 4, 1, 98, 4, 1, 97, 0, 0))

    def testDefMode4(self):
        s = univ.SequenceOf()
        s.append(univ.OctetString('a'))
        s.append(univ.OctetString('b'))
        assert encoder.encode(s) == ints2octs((48, 128, 4, 1, 97, 4, 1, 98, 0, 0))


class SequenceOfEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.SequenceOf(componentType=univ.OctetString())

    def testEmpty(self):
        self.s.clear()
        assert encoder.encode(self.s) == ints2octs((48, 128, 0, 0))

    def testIndefMode1(self):
        self.s.clear()
        self.s.append('a')
        self.s.append('ab')
        assert encoder.encode(self.s) == ints2octs((48, 128, 4, 1, 97, 4, 2, 97, 98, 0, 0))

    def testIndefMode2(self):
        self.s.clear()
        self.s.append('ab')
        self.s.append('a')
        assert encoder.encode(self.s) == ints2octs((48, 128, 4, 2, 97, 98, 4, 1, 97, 0, 0))

    def testIndefMode3(self):
        self.s.clear()
        self.s.append('b')
        self.s.append('a')
        assert encoder.encode(self.s) == ints2octs((48, 128, 4, 1, 98, 4, 1, 97, 0, 0))

    def testIndefMode4(self):
        self.s.clear()
        self.s.append('a')
        self.s.append('b')
        assert encoder.encode(self.s) == ints2octs((48, 128, 4, 1, 97, 4, 1, 98, 0, 0))


class SetOfEncoderTestCase(BaseTestCase):
    def testEmpty(self):
        s = univ.SetOf()
        assert encoder.encode(s) == ints2octs((49, 128, 0, 0))

    def testDefMode1(self):
        s = univ.SetOf()
        s.append(univ.OctetString('a'))
        s.append(univ.OctetString('ab'))
        assert encoder.encode(s) == ints2octs((49, 128, 4, 1, 97, 4, 2, 97, 98, 0, 0))

    def testDefMode2(self):
        s = univ.SetOf()
        s.append(univ.OctetString('ab'))
        s.append(univ.OctetString('a'))
        assert encoder.encode(s) == ints2octs((49, 128, 4, 1, 97, 4, 2, 97, 98, 0, 0))

    def testDefMode3(self):
        s = univ.SetOf()
        s.append(univ.OctetString('b'))
        s.append(univ.OctetString('a'))
        assert encoder.encode(s) == ints2octs((49, 128, 4, 1, 97, 4, 1, 98, 0, 0))

    def testDefMode4(self):
        s = univ.SetOf()
        s.append(univ.OctetString('a'))
        s.append(univ.OctetString('b'))
        assert encoder.encode(s) == ints2octs((49, 128, 4, 1, 97, 4, 1, 98, 0, 0))


class SetOfEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.SetOf(componentType=univ.OctetString())

    def testEmpty(self):
        self.s.clear()
        assert encoder.encode(self.s) == ints2octs((49, 128, 0, 0))

    def testIndefMode1(self):
        self.s.clear()
        self.s.append('a')
        self.s.append('ab')

        assert encoder.encode(self.s) == ints2octs((49, 128, 4, 1, 97, 4, 2, 97, 98, 0, 0))

    def testIndefMode2(self):
        self.s.clear()
        self.s.append('ab')
        self.s.append('a')

        assert encoder.encode(self.s) == ints2octs((49, 128, 4, 1, 97, 4, 2, 97, 98, 0, 0))

    def testIndefMode3(self):
        self.s.clear()
        self.s.append('b')
        self.s.append('a')

        assert encoder.encode(self.s) == ints2octs((49, 128, 4, 1, 97, 4, 1, 98, 0, 0))

    def testIndefMode4(self):
        self.s.clear()
        self.s.append('a')
        self.s.append('b')

        assert encoder.encode(self.s) == ints2octs((49, 128, 4, 1, 97, 4, 1, 98, 0, 0))


class SetEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Set()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testIndefMode(self):
        assert encoder.encode(self.s) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))

    def testWithOptionalIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))

    def testWithDefaultedIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))

    def testWithOptionalAndDefaultedIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))


class SetEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Set(componentType=namedtype.NamedTypes(
            namedtype.NamedType('place-holder', univ.Null('')),
            namedtype.OptionalNamedType('first-name', univ.OctetString()),
            namedtype.DefaultedNamedType('age', univ.Integer(33))
        ))

    def __init(self):
        self.s.clear()
        self.s.setComponentByPosition(0)

    def __initWithOptional(self):
        self.s.clear()
        self.s.setComponentByPosition(0)
        self.s.setComponentByPosition(1, 'quick brown')

    def __initWithDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0)
        self.s.setComponentByPosition(2, 1)

    def __initWithOptionalAndDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testIndefMode(self):
        self.__init()
        assert encoder.encode(self.s) == ints2octs((49, 128, 5, 0, 0, 0))

    def testWithOptionalIndefMode(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))

    def testWithDefaultedIndefMode(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 5, 0, 0, 0))

    def testWithOptionalAndDefaultedIndefMode(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))


class SetWithChoiceWithSchemaEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        c = univ.Choice(componentType=namedtype.NamedTypes(
            namedtype.NamedType('actual', univ.Boolean(0))
        ))
        self.s = univ.Set(componentType=namedtype.NamedTypes(
            namedtype.NamedType('place-holder', univ.Null('')),
            namedtype.NamedType('status', c)
        ))

    def testIndefMode(self):
        self.s.setComponentByPosition(0)
        self.s.setComponentByName('status')
        self.s.getComponentByName('status').setComponentByPosition(0, 1)
        assert encoder.encode(self.s) == ints2octs((49, 128, 1, 1, 255, 5, 0, 0, 0))


class SetWithTaggedChoiceEncoderTestCase(BaseTestCase):

    def testWithUntaggedChoice(self):

        c = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('premium', univ.Boolean())
            )
        )

        s = univ.Set(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('customer', c)
            )
        )

        s.setComponentByName('name', 'A')
        s.getComponentByName('customer').setComponentByName('premium', True)

        assert encoder.encode(s) == ints2octs((49, 128, 1, 1, 255, 4, 1, 65, 0, 0))

    def testWithTaggedChoice(self):

        c = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('premium', univ.Boolean())
            )
        ).subtype(implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 7))

        s = univ.Set(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('name', univ.OctetString()),
                namedtype.NamedType('customer', c)
            )
        )

        s.setComponentByName('name', 'A')
        s.getComponentByName('customer').setComponentByName('premium', True)

        assert encoder.encode(s) == ints2octs((49, 128, 4, 1, 65, 167, 128, 1, 1, 255, 0, 0, 0, 0))


class SetEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Set()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testIndefMode(self):
        assert encoder.encode(self.s) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))

    def testWithOptionalIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))

    def testWithDefaultedIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))

    def testWithOptionalAndDefaultedIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((49, 128, 2, 1, 1, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 5, 0, 0, 0))


class SequenceEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Sequence()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testIndefMode(self):
        assert encoder.encode(self.s) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testWithOptionalIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testWithDefaultedIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))

    def testWithOptionalAndDefaultedIndefMode(self):
        assert encoder.encode(
            self.s
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))


class SequenceEncoderWithSchemaTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.s = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('place-holder', univ.Null('')),
                namedtype.OptionalNamedType('first-name', univ.OctetString()),
                namedtype.DefaultedNamedType('age', univ.Integer(33))
            )
        )

    def __init(self):
        self.s.clear()
        self.s.setComponentByPosition(0)

    def __initWithOptional(self):
        self.s.clear()
        self.s.setComponentByPosition(0)
        self.s.setComponentByPosition(1, 'quick brown')

    def __initWithDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0)
        self.s.setComponentByPosition(2, 1)

    def __initWithOptionalAndDefaulted(self):
        self.s.clear()
        self.s.setComponentByPosition(0, univ.Null(''))
        self.s.setComponentByPosition(1, univ.OctetString('quick brown'))
        self.s.setComponentByPosition(2, univ.Integer(1))

    def testIndefMode(self):
        self.__init()
        assert encoder.encode(self.s) == ints2octs((48, 128, 5, 0, 0, 0))

    def testWithOptionalIndefMode(self):
        self.__initWithOptional()
        assert encoder.encode(
            self.s
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 0, 0))

    def testWithDefaultedIndefMode(self):
        self.__initWithDefaulted()
        assert encoder.encode(
            self.s
        ) == ints2octs((48, 128, 5, 0, 2, 1, 1, 0, 0))

    def testWithOptionalAndDefaultedIndefMode(self):
        self.__initWithOptionalAndDefaulted()
        assert encoder.encode(
            self.s
        ) == ints2octs((48, 128, 5, 0, 4, 11, 113, 117, 105, 99, 107, 32, 98, 114, 111, 119, 110, 2, 1, 1, 0, 0))


class NestedOptionalSequenceEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        inner = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.OptionalNamedType('first-name', univ.OctetString()),
                namedtype.DefaultedNamedType('age', univ.Integer(33)),
            )
        )

        outerWithOptional = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.OptionalNamedType('inner', inner),
            )
        )

        outerWithDefault = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.DefaultedNamedType('inner', inner),
            )
        )

        self.s1 = outerWithOptional
        self.s2 = outerWithDefault

    def __initOptionalWithDefaultAndOptional(self):
        self.s1.clear()
        self.s1[0][0] = 'test'
        self.s1[0][1] = 123
        return self.s1

    def __initOptionalWithDefault(self):
        self.s1.clear()
        self.s1[0][1] = 123
        return self.s1

    def __initOptionalWithOptional(self):
        self.s1.clear()
        self.s1[0][0] = 'test'
        return self.s1

    def __initOptional(self):
        self.s1.clear()
        return self.s1

    def __initDefaultWithDefaultAndOptional(self):
        self.s2.clear()
        self.s2[0][0] = 'test'
        self.s2[0][1] = 123
        return self.s2

    def __initDefaultWithDefault(self):
        self.s2.clear()
        self.s2[0][0] = 'test'
        return self.s2

    def __initDefaultWithOptional(self):
        self.s2.clear()
        self.s2[0][1] = 123
        return self.s2

    def testOptionalWithDefaultAndOptional(self):
        s = self.__initOptionalWithDefaultAndOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 4, 4, 116, 101, 115, 116, 2, 1, 123, 0, 0, 0, 0))

    def testOptionalWithDefault(self):
        s = self.__initOptionalWithDefault()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 2, 1, 123, 0, 0, 0, 0))

    def testOptionalWithOptional(self):
        s = self.__initOptionalWithOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 4, 4, 116, 101, 115, 116, 0, 0, 0, 0))

    def testOptional(self):
        s = self.__initOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 0, 0))

    def testDefaultWithDefaultAndOptional(self):
        s = self.__initDefaultWithDefaultAndOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 4, 4, 116, 101, 115, 116, 2, 1, 123, 0, 0, 0, 0))

    def testDefaultWithDefault(self):
        s = self.__initDefaultWithDefault()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 4, 4, 116, 101, 115, 116, 0, 0, 0, 0))

    def testDefaultWithOptional(self):
        s = self.__initDefaultWithOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 2, 1, 123, 0, 0, 0, 0))


class NestedOptionalChoiceEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        layer3 = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.OptionalNamedType('first-name', univ.OctetString()),
                namedtype.DefaultedNamedType('age', univ.Integer(33)),
            )
        )

        layer2 = univ.Choice(
            componentType=namedtype.NamedTypes(
                namedtype.NamedType('inner', layer3),
                namedtype.NamedType('first-name', univ.OctetString())
            )
        )

        layer1 = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.OptionalNamedType('inner', layer2),
            )
        )

        self.s = layer1

    def __initOptionalWithDefaultAndOptional(self):
        self.s.clear()
        self.s[0][0][0] = 'test'
        self.s[0][0][1] = 123
        return self.s

    def __initOptionalWithDefault(self):
        self.s.clear()
        self.s[0][0][1] = 123
        return self.s

    def __initOptionalWithOptional(self):
        self.s.clear()
        self.s[0][0][0] = 'test'
        return self.s

    def __initOptional(self):
        self.s.clear()
        return self.s

    def testOptionalWithDefaultAndOptional(self):
        s = self.__initOptionalWithDefaultAndOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 4, 4, 116, 101, 115, 116, 2, 1, 123, 0, 0, 0, 0))

    def testOptionalWithDefault(self):
        s = self.__initOptionalWithDefault()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 2, 1, 123, 0, 0, 0, 0))

    def testOptionalWithOptional(self):
        s = self.__initOptionalWithOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 4, 4, 116, 101, 115, 116, 0, 0, 0, 0))

    def testOptional(self):
        s = self.__initOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 0, 0))


class NestedOptionalSequenceOfEncoderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        layer2 = univ.SequenceOf(
            componentType=univ.OctetString()
        )

        layer1 = univ.Sequence(
            componentType=namedtype.NamedTypes(
                namedtype.OptionalNamedType('inner', layer2),
            )
        )

        self.s = layer1

    def __initOptionalWithValue(self):
        self.s.clear()
        self.s[0][0] = 'test'
        return self.s

    def __initOptional(self):
        self.s.clear()
        return self.s

    def testOptionalWithValue(self):
        s = self.__initOptionalWithValue()
        assert encoder.encode(s) == ints2octs((48, 128, 48, 128, 4, 4, 116, 101, 115, 116, 0, 0, 0, 0))

    def testOptional(self):
        s = self.__initOptional()
        assert encoder.encode(s) == ints2octs((48, 128, 0, 0))


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
