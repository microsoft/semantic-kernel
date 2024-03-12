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

from pyasn1.type import namedval


class NamedValuesCaseBase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.e = namedval.NamedValues(('off', 0), ('on', 1))

    def testDict(self):
        assert set(self.e.items()) == set([('off', 0), ('on', 1)])
        assert set(self.e.keys()) == set(['off', 'on'])
        assert set(self.e) == set(['off', 'on'])
        assert set(self.e.values()) == set([0, 1])
        assert 'on' in self.e and 'off' in self.e and 'xxx' not in self.e
        assert 0 in self.e and 1 in self.e and 2 not in self.e

    def testInit(self):
        assert namedval.NamedValues(off=0, on=1) == {'off': 0, 'on': 1}
        assert namedval.NamedValues('off', 'on') == {'off': 0, 'on': 1}
        assert namedval.NamedValues(('c', 0)) == {'c': 0}
        assert namedval.NamedValues('a', 'b', ('c', 0), d=1) == {'c': 0, 'd': 1, 'a': 2, 'b': 3}

    def testLen(self):
        assert len(self.e) == 2
        assert len(namedval.NamedValues()) == 0

    def testAdd(self):
        assert namedval.NamedValues(off=0) + namedval.NamedValues(on=1) == {'off': 0, 'on': 1}

    def testClone(self):
        assert namedval.NamedValues(off=0).clone(('on', 1)) == {'off': 0, 'on': 1}
        assert namedval.NamedValues(off=0).clone(on=1) == {'off': 0, 'on': 1}

    def testStrRepr(self):
        assert str(self.e)
        assert repr(self.e)


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
