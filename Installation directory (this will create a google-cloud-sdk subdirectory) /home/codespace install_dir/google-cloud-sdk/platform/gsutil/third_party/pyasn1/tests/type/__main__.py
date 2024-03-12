#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/pyasn1/license.html
#
try:
    import unittest2 as unittest

except ImportError:
    import unittest

suite = unittest.TestLoader().loadTestsFromNames(
    ['tests.type.test_constraint.suite',
     'tests.type.test_opentype.suite',
     'tests.type.test_namedtype.suite',
     'tests.type.test_namedval.suite',
     'tests.type.test_tag.suite',
     'tests.type.test_univ.suite',
     'tests.type.test_char.suite',
     'tests.type.test_useful.suite']
)


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
