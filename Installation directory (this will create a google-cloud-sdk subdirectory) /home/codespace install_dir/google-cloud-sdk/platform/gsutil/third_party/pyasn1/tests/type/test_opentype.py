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

from pyasn1.type import univ
from pyasn1.type import tag
from pyasn1.type import namedtype
from pyasn1.type import opentype
from pyasn1.compat.octets import str2octs
from pyasn1.error import PyAsn1Error


class UntaggedAnyTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)

        class Sequence(univ.Sequence):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer()),
                namedtype.NamedType('blob', univ.Any())
            )

        self.s = Sequence()

    def testTypeCheckOnAssignment(self):

        self.s.clear()

        self.s['blob'] = univ.Any(str2octs('xxx'))

        # this should succeed because Any is untagged and unconstrained
        self.s['blob'] = univ.Integer(123)


class TaggedAnyTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)

        self.taggedAny = univ.Any().subtype(implicitTag=tag.Tag(tag.tagClassPrivate, tag.tagFormatSimple, 20))

        class Sequence(univ.Sequence):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer()),
                namedtype.NamedType('blob', self.taggedAny)
            )

        self.s = Sequence()

    def testTypeCheckOnAssignment(self):

        self.s.clear()

        self.s['blob'] = self.taggedAny.clone('xxx')

        try:
            self.s.setComponentByName('blob', univ.Integer(123))

        except PyAsn1Error:
            pass

        else:
            assert False, 'non-open type assignment tolerated'


class TaggedAnyOpenTypeTestCase(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)

        self.taggedAny = univ.Any().subtype(implicitTag=tag.Tag(tag.tagClassPrivate, tag.tagFormatSimple, 20))

        class Sequence(univ.Sequence):
            componentType = namedtype.NamedTypes(
                namedtype.NamedType('id', univ.Integer()),
                namedtype.NamedType('blob', self.taggedAny, openType=opentype.OpenType(name='id'))
            )

        self.s = Sequence()

    def testTypeCheckOnAssignment(self):

        self.s.clear()

        self.s['blob'] = univ.Any(str2octs('xxx'))
        self.s['blob'] = univ.Integer(123)


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
