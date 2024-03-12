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


class TagTestCaseBase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.t1 = tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 3)
        self.t2 = tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 3)


class TagReprTestCase(TagTestCaseBase):
    def testRepr(self):
        assert 'Tag' in repr(self.t1)


class TagCmpTestCase(TagTestCaseBase):
    def testCmp(self):
        assert self.t1 == self.t2, 'tag comparation fails'

    def testHash(self):
        assert hash(self.t1) == hash(self.t2), 'tag hash comparation fails'

    def testSequence(self):
        assert self.t1[0] == self.t2[0] and \
               self.t1[1] == self.t2[1] and \
               self.t1[2] == self.t2[2], 'tag sequence protocol fails'


class TagSetTestCaseBase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)

        self.ts1 = tag.initTagSet(
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12)
        )

        self.ts2 = tag.initTagSet(
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12)
        )


class TagSetReprTestCase(TagSetTestCaseBase):
    def testRepr(self):
        assert 'TagSet' in repr(self.ts1)


class TagSetCmpTestCase(TagSetTestCaseBase):
    def testCmp(self):
        assert self.ts1 == self.ts2, 'tag set comparation fails'

    def testHash(self):
        assert hash(self.ts1) == hash(self.ts2), 'tag set hash comp. fails'

    def testLen(self):
        assert len(self.ts1) == len(self.ts2), 'tag length comparation fails'


class TaggingTestSuite(TagSetTestCaseBase):
    def testImplicitTag(self):
        t = self.ts1.tagImplicitly(
            tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 14)
        )
        assert t == tag.TagSet(
            tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 12),
            tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 14)
        ), 'implicit tagging went wrong'

    def testExplicitTag(self):
        t = self.ts1.tagExplicitly(
            tag.Tag(tag.tagClassPrivate, tag.tagFormatSimple, 32)
        )
        assert t == tag.TagSet(
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12),
            tag.Tag(tag.tagClassPrivate, tag.tagFormatConstructed, 32)
        ), 'explicit tagging went wrong'


class TagSetAddTestSuite(TagSetTestCaseBase):
    def testAdd(self):
        t = self.ts1 + tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 2)
        assert t == tag.TagSet(
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12),
            tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 2)
        ), 'TagSet.__add__() fails'

    def testRadd(self):
        t = tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 2) + self.ts1
        assert t == tag.TagSet(
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12),
            tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 2),
            tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12)
        ), 'TagSet.__radd__() fails'


class SuperTagSetTestCase(TagSetTestCaseBase):
    def testSuperTagCheck1(self):
        assert self.ts1.isSuperTagSetOf(
            tag.TagSet(
                tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12),
                tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12)
            )), 'isSuperTagSetOf() fails'

    def testSuperTagCheck2(self):
        assert not self.ts1.isSuperTagSetOf(
            tag.TagSet(
                tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 12),
                tag.Tag(tag.tagClassUniversal, tag.tagFormatSimple, 13)
            )), 'isSuperTagSetOf() fails'

    def testSuperTagCheck3(self):
        assert self.ts1.isSuperTagSetOf(
            tag.TagSet((), tag.Tag(tag.tagClassUniversal,
                                   tag.tagFormatSimple, 12))
        ), 'isSuperTagSetOf() fails'


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
