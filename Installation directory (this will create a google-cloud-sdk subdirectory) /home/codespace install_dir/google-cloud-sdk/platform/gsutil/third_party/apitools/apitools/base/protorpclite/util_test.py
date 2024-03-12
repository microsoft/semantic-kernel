#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Tests for apitools.base.protorpclite.util."""
import datetime
import sys
import types
import unittest

import six

from apitools.base.protorpclite import test_util
from apitools.base.protorpclite import util


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

    MODULE = util


class UtilTest(test_util.TestCase):

    def testDecoratedFunction_LengthZero(self):
        @util.positional(0)
        def fn(kwonly=1):
            return [kwonly]
        self.assertEquals([1], fn())
        self.assertEquals([2], fn(kwonly=2))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'fn\(\) takes at most 0 positional '
                                         r'arguments \(1 given\)',
                                         fn, 1)

    def testDecoratedFunction_LengthOne(self):
        @util.positional(1)
        def fn(pos, kwonly=1):
            return [pos, kwonly]
        self.assertEquals([1, 1], fn(1))
        self.assertEquals([2, 2], fn(2, kwonly=2))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'fn\(\) takes at most 1 positional '
                                         r'argument \(2 given\)',
                                         fn, 2, 3)

    def testDecoratedFunction_LengthTwoWithDefault(self):
        @util.positional(2)
        def fn(pos1, pos2=1, kwonly=1):
            return [pos1, pos2, kwonly]
        self.assertEquals([1, 1, 1], fn(1))
        self.assertEquals([2, 2, 1], fn(2, 2))
        self.assertEquals([2, 3, 4], fn(2, 3, kwonly=4))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'fn\(\) takes at most 2 positional '
                                         r'arguments \(3 given\)',
                                         fn, 2, 3, 4)

    def testDecoratedMethod(self):
        class MyClass(object):

            @util.positional(2)
            def meth(self, pos1, kwonly=1):
                return [pos1, kwonly]
        self.assertEquals([1, 1], MyClass().meth(1))
        self.assertEquals([2, 2], MyClass().meth(2, kwonly=2))
        self.assertRaisesWithRegexpMatch(
            TypeError,
            r'meth\(\) takes at most 2 positional arguments \(3 given\)',
            MyClass().meth, 2, 3)

    def testDefaultDecoration(self):
        @util.positional
        def fn(a, b, c=None):
            return a, b, c
        self.assertEquals((1, 2, 3), fn(1, 2, c=3))
        self.assertEquals((3, 4, None), fn(3, b=4))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'fn\(\) takes at most 2 positional '
                                         r'arguments \(3 given\)',
                                         fn, 2, 3, 4)

    def testDefaultDecorationNoKwdsFails(self):
        def fn(a):
            return a
        self.assertRaisesRegexp(
            ValueError,
            ('Functions with no keyword arguments must specify '
             'max_positional_args'),
            util.positional, fn)

    def testDecoratedFunctionDocstring(self):
        @util.positional(0)
        def fn(kwonly=1):
            """fn docstring."""
            return [kwonly]
        self.assertEquals('fn docstring.', fn.__doc__)


class GetPackageForModuleTest(test_util.TestCase):

    def setUp(self):
        self.original_modules = dict(sys.modules)

    def tearDown(self):
        sys.modules.clear()
        sys.modules.update(self.original_modules)

    def CreateModule(self, name, file_name=None):
        if file_name is None:
            file_name = '%s.py' % name
        module = types.ModuleType(name)
        sys.modules[name] = module
        return module

    def assertPackageEquals(self, expected, actual):
        self.assertEquals(expected, actual)
        if actual is not None:
            self.assertTrue(isinstance(actual, six.text_type))

    def testByString(self):
        module = self.CreateModule('service_module')
        module.package = 'my_package'
        self.assertPackageEquals('my_package',
                                 util.get_package_for_module('service_module'))

    def testModuleNameNotInSys(self):
        self.assertPackageEquals(None,
                                 util.get_package_for_module('service_module'))

    def testHasPackage(self):
        module = self.CreateModule('service_module')
        module.package = 'my_package'
        self.assertPackageEquals(
            'my_package', util.get_package_for_module(module))

    def testHasModuleName(self):
        module = self.CreateModule('service_module')
        self.assertPackageEquals('service_module',
                                 util.get_package_for_module(module))

    def testIsMain(self):
        module = self.CreateModule('__main__')
        module.__file__ = '/bing/blam/bloom/blarm/my_file.py'
        self.assertPackageEquals(
            'my_file', util.get_package_for_module(module))

    def testIsMainCompiled(self):
        module = self.CreateModule('__main__')
        module.__file__ = '/bing/blam/bloom/blarm/my_file.pyc'
        self.assertPackageEquals(
            'my_file', util.get_package_for_module(module))

    def testNoExtension(self):
        module = self.CreateModule('__main__')
        module.__file__ = '/bing/blam/bloom/blarm/my_file'
        self.assertPackageEquals(
            'my_file', util.get_package_for_module(module))

    def testNoPackageAtAll(self):
        module = self.CreateModule('__main__')
        self.assertPackageEquals(
            '__main__', util.get_package_for_module(module))


class DateTimeTests(test_util.TestCase):

    def testDecodeDateTime(self):
        """Test that a RFC 3339 datetime string is decoded properly."""
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262', (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50', (2012, 9, 30, 15, 31, 50, 0))):
            decoded = util.decode_datetime(datetime_string)
            expected = datetime.datetime(*datetime_vals)
            self.assertEquals(expected, decoded)

    def testDecodeDateTimeWithTruncateTime(self):
       """Test that nanosec time is truncated with truncate_time flag."""
       decoded = util.decode_datetime('2012-09-30T15:31:50.262343123',
                                      truncate_time=True)
       expected = datetime.datetime(2012, 9, 30, 15, 31, 50, 262343)
       self.assertEquals(expected, decoded)

    def testDateTimeTimeZones(self):
        """Test that a datetime string with a timezone is decoded correctly."""
        tests = (
            ('2012-09-30T15:31:50.262-06:00',
             (2012, 9, 30, 15, 31, 50, 262000, util.TimeZoneOffset(-360))),
            ('2012-09-30T15:31:50.262+01:30',
             (2012, 9, 30, 15, 31, 50, 262000, util.TimeZoneOffset(90))),
            ('2012-09-30T15:31:50+00:05',
             (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(5))),
            ('2012-09-30T15:31:50+00:00',
             (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(0))),
            ('2012-09-30t15:31:50-00:00',
             (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(0))),
            ('2012-09-30t15:31:50z',
             (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(0))),
            ('2012-09-30T15:31:50-23:00',
             (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(-1380))))
        for datetime_string, datetime_vals in tests:
            decoded = util.decode_datetime(datetime_string)
            expected = datetime.datetime(*datetime_vals)
            self.assertEquals(expected, decoded)

    def testDecodeDateTimeInvalid(self):
        """Test that decoding malformed datetime strings raises execptions."""
        for datetime_string in ('invalid',
                                '2012-09-30T15:31:50.',
                                '-08:00 2012-09-30T15:31:50.262',
                                '2012-09-30T15:31',
                                '2012-09-30T15:31Z',
                                '2012-09-30T15:31:50ZZ',
                                '2012-09-30T15:31:50.262 blah blah -08:00',
                                '1000-99-99T25:99:99.999-99:99',
                                '2012-09-30T15:31:50.262343123'):
            self.assertRaises(
                ValueError, util.decode_datetime, datetime_string)

    def testTimeZoneOffsetDelta(self):
        """Test that delta works with TimeZoneOffset."""
        time_zone = util.TimeZoneOffset(datetime.timedelta(minutes=3))
        epoch = time_zone.utcoffset(datetime.datetime.utcfromtimestamp(0))
        self.assertEqual(180, util.total_seconds(epoch))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
