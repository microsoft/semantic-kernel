#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/pyasn1/license.html
#
import datetime
import pickle
import sys
from copy import deepcopy

try:
    import unittest2 as unittest

except ImportError:
    import unittest

from tests.base import BaseTestCase

from pyasn1.type import useful


class FixedOffset(datetime.tzinfo):
    def __init__(self, offset, name):
        self.__offset = datetime.timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta(0)


UTC = FixedOffset(0, 'UTC')
UTC2 = FixedOffset(120, 'UTC')


class ObjectDescriptorTestCase(BaseTestCase):
    pass


class GeneralizedTimeTestCase(BaseTestCase):

    def testFromDateTime(self):
        assert useful.GeneralizedTime.fromDateTime(datetime.datetime(2017, 7, 11, 0, 1, 2, 30000, tzinfo=UTC)) == '20170711000102.3Z'

    def testToDateTime0(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2) == useful.GeneralizedTime('20170711000102').asDateTime

    def testToDateTime1(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, tzinfo=UTC) == useful.GeneralizedTime('20170711000102Z').asDateTime

    def testToDateTime2(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, 30000, tzinfo=UTC) == useful.GeneralizedTime('20170711000102.3Z').asDateTime

    def testToDateTime3(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, 30000, tzinfo=UTC) == useful.GeneralizedTime('20170711000102,3Z').asDateTime

    def testToDateTime4(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, 30000, tzinfo=UTC) == useful.GeneralizedTime('20170711000102.3+0000').asDateTime

    def testToDateTime5(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, 30000, tzinfo=UTC2) == useful.GeneralizedTime('20170711000102.3+0200').asDateTime

    def testToDateTime6(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, 30000, tzinfo=UTC2) == useful.GeneralizedTime('20170711000102.3+02').asDateTime

    def testToDateTime7(self):
        assert datetime.datetime(2017, 7, 11, 0, 1) == useful.GeneralizedTime('201707110001').asDateTime

    def testToDateTime8(self):
        assert datetime.datetime(2017, 7, 11, 0) == useful.GeneralizedTime('2017071100').asDateTime

    def testCopy(self):
        dt = useful.GeneralizedTime("20170916234254+0130").asDateTime
        assert dt == deepcopy(dt)


class GeneralizedTimePicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = useful.GeneralizedTime()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == useful.GeneralizedTime
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = useful.GeneralizedTime("20170916234254+0130")
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == old_asn1


class UTCTimeTestCase(BaseTestCase):

    def testFromDateTime(self):
        assert useful.UTCTime.fromDateTime(datetime.datetime(2017, 7, 11, 0, 1, 2, tzinfo=UTC)) == '170711000102Z'

    def testToDateTime0(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2) == useful.UTCTime('170711000102').asDateTime

    def testToDateTime1(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, tzinfo=UTC) == useful.UTCTime('170711000102Z').asDateTime

    def testToDateTime2(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, tzinfo=UTC) == useful.UTCTime('170711000102+0000').asDateTime

    def testToDateTime3(self):
        assert datetime.datetime(2017, 7, 11, 0, 1, 2, tzinfo=UTC2) == useful.UTCTime('170711000102+0200').asDateTime

    def testToDateTime4(self):
        assert datetime.datetime(2017, 7, 11, 0, 1) == useful.UTCTime('1707110001').asDateTime


class UTCTimePicklingTestCase(unittest.TestCase):

    def testSchemaPickling(self):
        old_asn1 = useful.UTCTime()
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert type(new_asn1) == useful.UTCTime
        assert old_asn1.isSameTypeWith(new_asn1)

    def testValuePickling(self):
        old_asn1 = useful.UTCTime("170711000102")
        serialised = pickle.dumps(old_asn1)
        assert serialised
        new_asn1 = pickle.loads(serialised)
        assert new_asn1 == old_asn1


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
