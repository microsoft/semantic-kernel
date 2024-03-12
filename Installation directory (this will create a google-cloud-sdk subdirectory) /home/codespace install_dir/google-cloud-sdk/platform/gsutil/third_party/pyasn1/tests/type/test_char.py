#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/pyasn1/license.html
#
import pickle
import sys

try:
    import unittest2 as unittest

except ImportError:
    import unittest

from tests.base import BaseTestCase

from pyasn1.type import char
from pyasn1.type import univ
from pyasn1.type import constraint
from pyasn1.compat.octets import ints2octs
from pyasn1.error import PyAsn1Error


class AbstractStringTestCase(object):

    initializer = ()
    encoding = 'us-ascii'
    asn1Type = None

    def setUp(self):
        BaseTestCase.setUp(self)

        self.asn1String = self.asn1Type(ints2octs(self.initializer), encoding=self.encoding)
        self.pythonString = ints2octs(self.initializer).decode(self.encoding)

    def testUnicode(self):
        assert self.asn1String == self.pythonString, 'unicode init fails'

    def testLength(self):
        assert len(self.asn1String) == len(self.pythonString), 'unicode len() fails'

    def testSizeConstraint(self):
        asn1Spec = self.asn1Type(subtypeSpec=constraint.ValueSizeConstraint(1, 1))

        try:
            asn1Spec.clone(self.pythonString)
        except PyAsn1Error:
            pass
        else:
            assert False, 'Size constraint tolerated'

        try:
            asn1Spec.clone(self.pythonString[0])
        except PyAsn1Error:
            assert False, 'Size constraint failed'

    def testSerialised(self):
        if sys.version_info[0] < 3:
            assert str(self.asn1String) == self.pythonString.encode(self.encoding), '__str__() fails'
        else:
            assert bytes(self.asn1String) == self.pythonString.encode(self.encoding), '__str__() fails'

    def testPrintable(self):
        if sys.version_info[0] < 3:
            assert unicode(self.asn1String) == self.pythonString, '__str__() fails'
        else:
            assert str(self.asn1String) == self.pythonString, '__str__() fails'

    def testInit(self):
        assert self.asn1Type(self.pythonString) == self.pythonString
        assert self.asn1Type(self.pythonString.encode(self.encoding)) == self.pythonString
        assert self.asn1Type(univ.OctetString(self.pythonString.encode(self.encoding))) == self.pythonString
        assert self.asn1Type(self.asn1Type(self.pythonString)) == self.pythonString
        assert self.asn1Type(self.initializer, encoding=self.encoding) == self.pythonString

    def testInitFromAsn1(self):
        assert self.asn1Type(self.asn1Type(self.pythonString)) == self.pythonString
        assert self.asn1Type(univ.OctetString(self.pythonString.encode(self.encoding), encoding=self.encoding)) == self.pythonString

    def testAsOctets(self):
        assert self.asn1String.asOctets() == self.pythonString.encode(self.encoding), 'testAsOctets() fails'

    def testAsNumbers(self):
        assert self.asn1String.asNumbers() == self.initializer, 'testAsNumbers() fails'

    def testSeq(self):
        assert self.asn1String[0] == self.pythonString[0], '__getitem__() fails'

    def testEmpty(self):
        try:
            str(self.asn1Type())
        except PyAsn1Error:
            pass
        else:
            assert 0, 'Value operation on ASN1 type tolerated'

    def testAdd(self):
        assert self.asn1String + self.pythonString.encode(self.encoding) == self.pythonString + self.pythonString, '__add__() fails'

    def testRadd(self):
        assert self.pythonString.encode(self.encoding) + self.asn1String == self.pythonString + self.pythonString, '__radd__() fails'

    def testMul(self):
        assert self.asn1String * 2 == self.pythonString * 2, '__mul__() fails'

    def testRmul(self):
        assert 2 * self.asn1String == 2 * self.pythonString, '__rmul__() fails'

    def testContains(self):
        assert self.pythonString in self.asn1String
        assert self.pythonString + self.pythonString not in self.asn1String

    if sys.version_info[:2] > (2, 4):
        def testReverse(self):
            assert list(reversed(self.asn1String)) == list(reversed(self.pythonString))

    def testSchemaPickling(self):
        old_asn1 = self.asn1Type()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == self.asn1Type
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = self.asn1String
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == self.asn1String


class VisibleStringTestCase(AbstractStringTestCase, BaseTestCase):

    initializer = (97, 102)
    encoding = 'us-ascii'
    asn1Type = char.VisibleString


class GeneralStringTestCase(AbstractStringTestCase, BaseTestCase):

    initializer = (169, 174)
    encoding = 'iso-8859-1'
    asn1Type = char.GeneralString


class UTF8StringTestCase(AbstractStringTestCase, BaseTestCase):

    initializer = (209, 132, 208, 176)
    encoding = 'utf-8'
    asn1Type = char.UTF8String


class BMPStringTestCase(AbstractStringTestCase, BaseTestCase):

    initializer = (4, 48, 4, 68)
    encoding = 'utf-16-be'
    asn1Type = char.BMPString


if sys.version_info[0] > 2:

    # Somehow comparison of UTF-32 encoded strings does not work in Py2

    class UniversalStringTestCase(AbstractStringTestCase, BaseTestCase):
        initializer = (0, 0, 4, 48, 0, 0, 4, 68)
        encoding = 'utf-32-be'
        asn1Type = char.UniversalString


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
