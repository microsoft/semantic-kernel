#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
try:
    import unittest2 as unittest

except ImportError:
    import unittest

suite = unittest.TestLoader().loadTestsFromNames(
    ['tests.test_rfc2314.suite',
     'tests.test_rfc2315.suite',
     'tests.test_rfc2437.suite',
     'tests.test_rfc2459.suite',
     'tests.test_rfc2511.suite',
     'tests.test_rfc2560.suite',
     'tests.test_rfc4210.suite',
     'tests.test_rfc5208.suite',
     'tests.test_rfc5280.suite',
     'tests.test_rfc5652.suite',]
)


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
