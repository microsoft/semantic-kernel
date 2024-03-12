#!/usr/bin/env python
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base functionality for google tests.

This module contains base classes and high-level functions for Google-style
tests.
"""

__author__ = 'dborowitz@google.com (Dave Borowitz)'

import commands
import difflib
import getpass
import itertools
import os
import re
import subprocess
import sys
import tempfile
import types


# unittest2 is a backport of Python 2.7's unittest for Python 2.6, so
# we don't need it if we are running 2.7 or newer.

if sys.version_info < (2, 7):
  import unittest2 as unittest
else:
  import unittest

from google.apputils import app
import gflags as flags
from google.apputils import shellutil

FLAGS = flags.FLAGS

# ----------------------------------------------------------------------
# Internal functions to extract default flag values from environment.
# ----------------------------------------------------------------------
def _GetDefaultTestRandomSeed():
  random_seed = 301
  value = os.environ.get('TEST_RANDOM_SEED', '')
  try:
    random_seed = int(value)
  except ValueError:
    pass
  return random_seed


def _GetDefaultTestTmpdir():
  tmpdir = os.environ.get('TEST_TMPDIR', '')
  if not tmpdir:
    tmpdir = os.path.join(tempfile.gettempdir(), 'google_apputils_basetest')

  return tmpdir


flags.DEFINE_integer('test_random_seed', _GetDefaultTestRandomSeed(),
                     'Random seed for testing. Some test frameworks may '
                     'change the default value of this flag between runs, so '
                     'it is not appropriate for seeding probabilistic tests.',
                     allow_override=1)
flags.DEFINE_string('test_srcdir',
                    os.environ.get('TEST_SRCDIR', ''),
                    'Root of directory tree where source files live',
                    allow_override=1)
flags.DEFINE_string('test_tmpdir', _GetDefaultTestTmpdir(),
                    'Directory for temporary testing files',
                    allow_override=1)


class BeforeAfterTestCaseMeta(type):

  """Adds setUpTestCase() and tearDownTestCase() methods.

  These may be needed for setup and teardown of shared fixtures usually because
  such fixtures are expensive to setup and teardown (eg Perforce clients).  When
  using such fixtures, care should be taken to keep each test as independent as
  possible (eg via the use of sandboxes).

  Example:

    class MyTestCase(basetest.TestCase):

      __metaclass__ = basetest.BeforeAfterTestCaseMeta

      @classmethod
      def setUpTestCase(cls):
        cls._resource = foo.ReallyExpensiveResource()

      @classmethod
      def tearDownTestCase(cls):
        cls._resource.Destroy()

      def testSomething(self):
        self._resource.Something()
        ...
  """

  _test_loader = unittest.defaultTestLoader

  def __init__(cls, name, bases, dict):
    super(BeforeAfterTestCaseMeta, cls).__init__(name, bases, dict)

    # Notes from mtklein

    # This code can be tricky to think about.  Here are a few things to remember
    # as you read through it.

    # When inheritance is involved, this __init__ is called once on each class
    # in the inheritance chain when that class is defined.  In a typical
    # scenario where a BaseClass inheriting from TestCase declares the
    # __metaclass__ and SubClass inherits from BaseClass, __init__ will be first
    # called with cls=BaseClass when BaseClass is defined, and then called later
    # with cls=SubClass when SubClass is defined.

    # To know when to call setUpTestCase and tearDownTestCase, this class wraps
    # the setUp, tearDown, and test* methods in a TestClass.  We'd like to only
    # wrap those methods in the leaves of the inheritance tree, but we can't
    # know when we're a leaf at wrapping time.  So instead we wrap all the
    # setUp, tearDown, and test* methods, but code them so that we only do the
    # counting we want at the leaves, which we *can* detect when we've got an
    # actual instance to look at --- i.e. self, when a method is running.

    # Because we're wrapping at every level of inheritance, some methods get
    # wrapped multiple times down the inheritance chain; if SubClass were to
    # inherit, say, setUp or testFoo from BaseClass, that method would be
    # wrapped twice, first by BaseClass then by SubClass.  That's OK, because we
    # ensure that the extra code we inject with these wrappers is idempotent.

    # test_names are the test methods this class can see.
    test_names = set(cls._test_loader.getTestCaseNames(cls))

    # Each class keeps a set of the tests it still has to run.  When it's empty,
    # we know we should call tearDownTestCase.  For now, it holds the sentinel
    # value of None, acting as a indication that we need to call setUpTestCase,
    # which fills in the actual tests to run.
    cls.__tests_to_run = None

    # These calls go through and monkeypatch various methods, in no particular
    # order.
    BeforeAfterTestCaseMeta.SetSetUpAttr(cls, test_names)
    BeforeAfterTestCaseMeta.SetTearDownAttr(cls)
    BeforeAfterTestCaseMeta.SetTestMethodAttrs(cls, test_names)
    BeforeAfterTestCaseMeta.SetBeforeAfterTestCaseAttr()

  # Just a little utility function to help with monkey-patching.
  @staticmethod
  def SetMethod(cls, method_name, replacement):
    """Like setattr, but also preserves name, doc, and module metadata."""
    original = getattr(cls, method_name)
    replacement.__name__ = original.__name__
    replacement.__doc__ = original.__doc__
    replacement.__module__ = original.__module__
    setattr(cls, method_name, replacement)

  @staticmethod
  def SetSetUpAttr(cls, test_names):
    """Wraps setUp() with per-class setUp() functionality."""
    # Remember that SetSetUpAttr is eventually called on each class in the
    # inheritance chain.  This line can be subtle because of inheritance.  Say
    # we've got BaseClass that defines setUp, and SubClass inheriting from it
    # that doesn't define setUp.  This method will run twice, and both times
    # cls_setUp will be BaseClass.setUp.  This is one of the tricky cases where
    # setUp will be wrapped multiple times.
    cls_setUp = cls.setUp

    # We create a new setUp method that first checks to see if we need to run
    # setUpTestCase (looking for the __tests_to_run==None flag), and then runs
    # the original setUp method.
    def setUp(self):
      """Function that will encapsulate and replace cls.setUp()."""
      # This line is unassuming but crucial to making this whole system work.
      # It sets leaf to the class of the instance we're currently testing.  That
      # is, leaf is going to be a leaf class.  It's not necessarily the same
      # class as the parameter cls that's being passed in.  For example, in the
      # case above where setUp is in BaseClass, when we instantiate a SubClass
      # and call setUp, we need leaf to be pointing at the class SubClass.
      leaf = self.__class__

      # The reason we want to do this is that it makes sure setUpTestCase is
      # only run once, not once for each class down the inheritance chain.  When
      # multiply-wrapped, this extra code is called multiple times.  In the
      # running example:
      #
      #  1) cls=BaseClass: replace BaseClass' setUp with a wrapped setUp
      #  2) cls=SubClass: set SubClass.setUp to what it thinks was its original
      #     setUp --- the wrapped setUp from 1)
      #
      # So it's double-wrapped, but that's OK.  When we actually call setUp from
      # an instance, we're calling the double-wrapped method.  It sees
      # __tests_to_run is None and fills that in.  Then it calls what it thinks
      # was its original setUp, the singly-wrapped setUp from BaseClass.  The
      # singly-wrapped setUp *skips* the if-statement, as it sees
      # leaf.__tests_to_run is not None now.  It just runs the real, original
      # setUp().

      # test_names is passed in from __init__, and holds all the test cases that
      # cls can see.  In the BaseClass call, that's probably the empty set, and
      # for SubClass it'd have your test methods.

      if leaf.__tests_to_run is None:
        leaf.__tests_to_run = set(test_names)
        self.setUpTestCase()
      cls_setUp(self)

    # Monkeypatch our new setUp method into the place of the original.
    BeforeAfterTestCaseMeta.SetMethod(cls, 'setUp', setUp)

  @staticmethod
  def SetTearDownAttr(cls):
    """Wraps tearDown() with per-class tearDown() functionality."""

    # This is analagous to SetSetUpAttr, except of course it's patching tearDown
    # to run tearDownTestCase when there are no more tests to run.  All the same
    # hairy logic applies.
    cls_tearDown = cls.tearDown

    def tearDown(self):
      """Function that will encapsulate and replace cls.tearDown()."""
      cls_tearDown(self)

      leaf = self.__class__
      # We need to make sure that tearDownTestCase is only run when
      # we're executing this in the leaf class, so we need the
      # explicit leaf == cls check below.
      if (leaf.__tests_to_run is not None
          and not leaf.__tests_to_run
          and leaf == cls):
        leaf.__tests_to_run = None
        self.tearDownTestCase()

    BeforeAfterTestCaseMeta.SetMethod(cls, 'tearDown', tearDown)

  @staticmethod
  def SetTestMethodAttrs(cls, test_names):
    """Makes each test method first remove itself from the remaining set."""
    # This makes each test case remove itself from the set of remaining tests.
    # You might think that this belongs more logically in tearDown, and I'd
    # agree except that tearDown doesn't know what test case it's tearing down!
    # Instead we have the test method itself remove itself before attempting the
    # test.

    # Note that having the test remove itself after running doesn't work, as we
    # never get to 'after running' for tests that fail.

    # Like setUp and tearDown, the test case could conceivably be wrapped
    # twice... but as noted it's an implausible situation to have an actual test
    # defined in a base class.  Just in case, we take the same precaution by
    # looking in only the leaf class' set of __tests_to_run, and using discard()
    # instead of remove() to make the operation idempotent.

    for test_name in test_names:
      cls_test = getattr(cls, test_name)

      # The default parameters here make sure that each new test() function
      # remembers its own values of cls_test and test_name.  Without these
      # default parameters, they'd all point to the values from the last
      # iteration of the loop, causing some arbitrary test method to run
      # multiple times and the others never. :(
      def test(self, cls_test=cls_test, test_name=test_name):
        leaf = self.__class__
        leaf.__tests_to_run.discard(test_name)
        return cls_test(self)

      BeforeAfterTestCaseMeta.SetMethod(cls, test_name, test)

  @staticmethod
  def SetBeforeAfterTestCaseAttr():
    # This just makes sure every TestCase has a setUpTestCase or
    # tearDownTestCase, so that you can safely define only one or neither of
    # them if you want.
    TestCase.setUpTestCase = lambda self: None
    TestCase.tearDownTestCase = lambda self: None


class TestCase(unittest.TestCase):
  """Extension of unittest.TestCase providing more powerful assertions."""

  maxDiff = 80 * 20

  def __init__(self, methodName='runTest'):
    super(TestCase, self).__init__(methodName)
    self.__recorded_properties = {}

  def shortDescription(self):
    """Format both the test method name and the first line of its docstring.

    If no docstring is given, only returns the method name.

    This method overrides unittest.TestCase.shortDescription(), which
    only returns the first line of the docstring, obscuring the name
    of the test upon failure.

    Returns:
      desc: A short description of a test method.
    """
    desc = str(self)
    # NOTE: super() is used here instead of directly invoking
    # unittest.TestCase.shortDescription(self), because of the
    # following line that occurs later on:
    #       unittest.TestCase = TestCase
    # Because of this, direct invocation of what we think is the
    # superclass will actually cause infinite recursion.
    doc_first_line = super(TestCase, self).shortDescription()
    if doc_first_line is not None:
      desc = '\n'.join((desc, doc_first_line))
    return desc

  def assertSequenceStartsWith(self, prefix, whole, msg=None):
    """An equality assertion for the beginning of ordered sequences.

    If prefix is an empty sequence, it will raise an error unless whole is also
    an empty sequence.

    If prefix is not a sequence, it will raise an error if the first element of
    whole does not match.

    Args:
      prefix: A sequence expected at the beginning of the whole parameter.
      whole: The sequence in which to look for prefix.
      msg: Optional message to append on failure.
    """
    try:
      prefix_len = len(prefix)
    except (TypeError, NotImplementedError):
      prefix = [prefix]
      prefix_len = 1

    try:
      whole_len = len(whole)
    except (TypeError, NotImplementedError):
      self.fail('For whole: len(%s) is not supported, it appears to be type: '
                '%s' % (whole, type(whole)))

    assert prefix_len <= whole_len, (
        'Prefix length (%d) is longer than whole length (%d).' %
        (prefix_len, whole_len))

    if not prefix_len and whole_len:
      self.fail('Prefix length is 0 but whole length is %d: %s' %
                (len(whole), whole))

    try:
      self.assertSequenceEqual(prefix, whole[:prefix_len], msg)
    except AssertionError:
      self.fail(msg or 'prefix: %s not found at start of whole: %s.' %
                (prefix, whole))

  def assertContainsSubset(self, expected_subset, actual_set, msg=None):
    """Checks whether actual iterable is a superset of expected iterable."""
    missing = set(expected_subset) - set(actual_set)
    if not missing:
      return

    missing_msg = 'Missing elements %s\nExpected: %s\nActual: %s' % (
        missing, expected_subset, actual_set)
    if msg:
      msg += ': %s' % missing_msg
    else:
      msg = missing_msg
    self.fail(msg)

  def assertSameElements(self, expected_seq, actual_seq, msg=None):
    """Assert that two sequences have the same elements (in any order).

    This method, unlike assertItemsEqual, doesn't care about any
    duplicates in the expected and actual sequences.

      >> assertSameElements([1, 1, 1, 0, 0, 0], [0, 1])
      # Doesn't raise an AssertionError

    If possible, you should use assertItemsEqual instead of
    assertSameElements.

    Args:
      expected_seq: A sequence containing elements we are expecting.
      actual_seq: The sequence that we are testing.
      msg: The message to be printed if the test fails.
    """
    # `unittest2.TestCase` used to have assertSameElements, but it was
    # removed in favor of assertItemsEqual. As there's a unit test
    # that explicitly checks this behavior, I am leaving this method
    # alone.
    try:
      expected = dict([(element, None) for element in expected_seq])
      actual = dict([(element, None) for element in actual_seq])
      missing = [element for element in expected if element not in actual]
      unexpected = [element for element in actual if element not in expected]
      missing.sort()
      unexpected.sort()
    except TypeError:
      # Fall back to slower list-compare if any of the objects are
      # not hashable.
      expected = list(expected_seq)
      actual = list(actual_seq)
      expected.sort()
      actual.sort()
      missing, unexpected = _SortedListDifference(expected, actual)
    errors = []
    if missing:
      errors.append('Expected, but missing:\n  %r\n' % missing)
    if unexpected:
      errors.append('Unexpected, but present:\n  %r\n' % unexpected)
    if errors:
      self.fail(msg or ''.join(errors))

  # unittest2.TestCase.assertMulitilineEqual works very similarly, but it
  # has a different error format. However, I find this slightly more readable.
  def assertMultiLineEqual(self, first, second, msg=None):
    """Assert that two multi-line strings are equal."""
    assert isinstance(first, types.StringTypes), (
        'First argument is not a string: %r' % (first,))
    assert isinstance(second, types.StringTypes), (
        'Second argument is not a string: %r' % (second,))

    if first == second:
      return
    if msg:
      raise self.failureException(msg)

    failure_message = ['\n']
    for line in difflib.ndiff(first.splitlines(True), second.splitlines(True)):
      failure_message.append(line)
      if not line.endswith('\n'):
        failure_message.append('\n')
    raise self.failureException(''.join(failure_message))

  def assertBetween(self, value, minv, maxv, msg=None):
    """Asserts that value is between minv and maxv (inclusive)."""
    if msg is None:
      msg = '"%r" unexpectedly not between "%r" and "%r"' % (value, minv, maxv)
    self.assert_(minv <= value, msg)
    self.assert_(maxv >= value, msg)

  def assertRegexMatch(self, actual_str, regexes, message=None):
    """Asserts that at least one regex in regexes matches str.

    If possible you should use assertRegexpMatches, which is a simpler
    version of this method. assertRegexpMatches takes a single regular
    expression (a string or re compiled object) instead of a list.

    Notes:
    1. This function uses substring matching, i.e. the matching
       succeeds if *any* substring of the error message matches *any*
       regex in the list.  This is more convenient for the user than
       full-string matching.

    2. If regexes is the empty list, the matching will always fail.

    3. Use regexes=[''] for a regex that will always pass.

    4. '.' matches any single character *except* the newline.  To
       match any character, use '(.|\n)'.

    5. '^' matches the beginning of each line, not just the beginning
       of the string.  Similarly, '$' matches the end of each line.

    6. An exception will be thrown if regexes contains an invalid
       regex.

    Args:
      actual_str:  The string we try to match with the items in regexes.
      regexes:  The regular expressions we want to match against str.
        See "Notes" above for detailed notes on how this is interpreted.
      message:  The message to be printed if the test fails.
    """
    if isinstance(regexes, basestring):
      self.fail('regexes is a string; it needs to be a list of strings.')
    if not regexes:
      self.fail('No regexes specified.')

    regex = '(?:%s)' % ')|(?:'.join(regexes)

    if not re.search(regex, actual_str, re.MULTILINE):
      self.fail(message or ('String "%s" does not contain any of these '
                            'regexes: %s.' % (actual_str, regexes)))

  def assertCommandSucceeds(self, command, regexes=[''], env=None,
                            close_fds=True):
    """Asserts that a shell command succeeds (i.e. exits with code 0).

    Args:
      command: List or string representing the command to run.
      regexes: List of regular expression strings.
      env: Dictionary of environment variable settings.
      close_fds: Whether or not to close all open fd's in the child after
        forking.
    """
    (ret_code, err) = GetCommandStderr(command, env, close_fds)

    command_string = GetCommandString(command)
    self.assert_(
        ret_code == 0,
        'Running command\n'
        '%s failed with error code %s and message\n'
        '%s' % (
            _QuoteLongString(command_string),
            ret_code,
            _QuoteLongString(err)))
    self.assertRegexMatch(
        err,
        regexes,
        message=(
            'Running command\n'
            '%s failed with error code %s and message\n'
            '%s which matches no regex in %s' % (
                _QuoteLongString(command_string),
                ret_code,
                _QuoteLongString(err),
                regexes)))

  def assertCommandFails(self, command, regexes, env=None, close_fds=True):
    """Asserts a shell command fails and the error matches a regex in a list.

    Args:
      command: List or string representing the command to run.
      regexes: the list of regular expression strings.
      env: Dictionary of environment variable settings.
      close_fds: Whether or not to close all open fd's in the child after
        forking.
    """
    (ret_code, err) = GetCommandStderr(command, env, close_fds)

    command_string = GetCommandString(command)
    self.assert_(
        ret_code != 0,
        'The following command succeeded while expected to fail:\n%s' %
        _QuoteLongString(command_string))
    self.assertRegexMatch(
        err,
        regexes,
        message=(
            'Running command\n'
            '%s failed with error code %s and message\n'
            '%s which matches no regex in %s' % (
                _QuoteLongString(command_string),
                ret_code,
                _QuoteLongString(err),
                regexes)))

  def assertRaisesWithPredicateMatch(self, expected_exception, predicate,
                                     callable_obj, *args,
                                     **kwargs):
    """Asserts that exception is thrown and predicate(exception) is true.

    Args:
      expected_exception: Exception class expected to be raised.
      predicate: Function of one argument that inspects the passed-in exception
        and returns True (success) or False (please fail the test).
      callable_obj: Function to be called.
      args: Extra args.
      kwargs: Extra keyword args.
    """
    try:
      callable_obj(*args, **kwargs)
    except expected_exception as err:
      self.assert_(predicate(err),
                   '%r does not match predicate %r' % (err, predicate))
    else:
      self.fail(expected_exception.__name__ + ' not raised')

  def assertRaisesWithLiteralMatch(self, expected_exception,
                                   expected_exception_message, callable_obj,
                                   *args, **kwargs):
    """Asserts that the message in a raised exception equals the given string.

    Unlike assertRaisesWithRegexpMatch this method takes a literal string, not
    a regular expression.

    Args:
      expected_exception: Exception class expected to be raised.
      expected_exception_message: String message expected in the raised
        exception.  For a raise exception e, expected_exception_message must
        equal str(e).
      callable_obj: Function to be called.
      args: Extra args.
      kwargs: Extra kwargs.
    """
    try:
      callable_obj(*args, **kwargs)
    except expected_exception as err:
      actual_exception_message = str(err)
      self.assert_(expected_exception_message == actual_exception_message,
                   'Exception message does not match.\n'
                   'Expected: %r\n'
                   'Actual: %r' % (expected_exception_message,
                                   actual_exception_message))
    else:
      self.fail(expected_exception.__name__ + ' not raised')

  def assertRaisesWithRegexpMatch(self, expected_exception, expected_regexp,
                                  callable_obj, *args, **kwargs):
    """Asserts that the message in a raised exception matches the given regexp.

    This is just a wrapper around assertRaisesRegexp. Please use
    assertRaisesRegexp instead of assertRaisesWithRegexpMatch.

    Args:
      expected_exception: Exception class expected to be raised.
      expected_regexp: Regexp (re pattern object or string) expected to be
        found in error message.
      callable_obj: Function to be called.
      args: Extra args.
      kwargs: Extra keyword args.
    """
    # TODO(user): this is a good candidate for a global
    # search-and-replace.
    self.assertRaisesRegexp(
        expected_exception,
        expected_regexp,
        callable_obj,
        *args,
        **kwargs)

  def assertContainsInOrder(self, strings, target):
    """Asserts that the strings provided are found in the target in order.

    This may be useful for checking HTML output.

    Args:
      strings: A list of strings, such as [ 'fox', 'dog' ]
      target: A target string in which to look for the strings, such as
        'The quick brown fox jumped over the lazy dog'.
    """
    if not isinstance(strings, list):
      strings = [strings]

    current_index = 0
    last_string = None
    for string in strings:
      index = target.find(str(string), current_index)
      if index == -1 and current_index == 0:
        self.fail("Did not find '%s' in '%s'" %
                  (string, target))
      elif index == -1:
        self.fail("Did not find '%s' after '%s' in '%s'" %
                  (string, last_string, target))
      last_string = string
      current_index = index

  def assertTotallyOrdered(self, *groups):
    """Asserts that total ordering has been implemented correctly.

    For example, say you have a class A that compares only on its attribute x.
    Comparators other than __lt__ are omitted for brevity.

    class A(object):
      def __init__(self, x, y):
        self.x = xio
        self.y = y

      def __hash__(self):
        return hash(self.x)

      def __lt__(self, other):
        try:
          return self.x < other.x
        except AttributeError:
          return NotImplemented

    assertTotallyOrdered will check that instances can be ordered correctly.
    For example,

    self.assertTotallyOrdered(
      [None],  # None should come before everything else.
      [1],     # Integers sort earlier.
      ['foo'],  # As do strings.
      [A(1, 'a')],
      [A(2, 'b')],  # 2 is after 1.
      [A(2, 'c'), A(2, 'd')],  # The second argument is irrelevant.
      [A(3, 'z')])

    Args:
     groups: A list of groups of elements.  Each group of elements is a list
       of objects that are equal.  The elements in each group must be less than
       the elements in the group after it.  For example, these groups are
       totally ordered: [None], [1], [2, 2], [3].
    """

    def CheckOrder(small, big):
      """Ensures small is ordered before big."""
      self.assertFalse(small == big,
                       '%r unexpectedly equals %r' % (small, big))
      self.assertTrue(small != big,
                      '%r unexpectedly equals %r' % (small, big))
      self.assertLess(small, big)
      self.assertFalse(big < small,
                       '%r unexpectedly less than %r' % (big, small))
      self.assertLessEqual(small, big)
      self.assertFalse(big <= small,
                       '%r unexpectedly less than or equal to %r'
                       % (big, small))
      self.assertGreater(big, small)
      self.assertFalse(small > big,
                       '%r unexpectedly greater than %r' % (small, big))
      self.assertGreaterEqual(big, small)
      self.assertFalse(small >= big,
                       '%r unexpectedly greater than or equal to %r'
                       % (small, big))

    def CheckEqual(a, b):
      """Ensures that a and b are equal."""
      self.assertEqual(a, b)
      self.assertFalse(a != b, '%r unexpectedly equals %r' % (a, b))
      self.assertEqual(hash(a), hash(b),
                       'hash %d of %r unexpectedly not equal to hash %d of %r'
                       % (hash(a), a, hash(b), b))
      self.assertFalse(a < b, '%r unexpectedly less than %r' % (a, b))
      self.assertFalse(b < a, '%r unexpectedly less than %r' % (b, a))
      self.assertLessEqual(a, b)
      self.assertLessEqual(b, a)
      self.assertFalse(a > b, '%r unexpectedly greater than %r' % (a, b))
      self.assertFalse(b > a, '%r unexpectedly greater than %r' % (b, a))
      self.assertGreaterEqual(a, b)
      self.assertGreaterEqual(b, a)

    # For every combination of elements, check the order of every pair of
    # elements.
    for elements in itertools.product(*groups):
      elements = list(elements)
      for index, small in enumerate(elements[:-1]):
        for big in elements[index + 1:]:
          CheckOrder(small, big)

    # Check that every element in each group is equal.
    for group in groups:
      for a in group:
        CheckEqual(a, a)
      for a, b in itertools.product(group, group):
        CheckEqual(a, b)

  def getRecordedProperties(self):
    """Return any properties that the user has recorded."""
    return self.__recorded_properties

  def recordProperty(self, property_name, property_value):
    """Record an arbitrary property for later use.

    Args:
      property_name: str, name of property to record; must be a valid XML
        attribute name
      property_value: value of property; must be valid XML attribute value
    """
    self.__recorded_properties[property_name] = property_value

  def _getAssertEqualityFunc(self, first, second):
    try:
      return super(TestCase, self)._getAssertEqualityFunc(first, second)
    except AttributeError:
      # This happens if unittest2.TestCase.__init__ was never run. It
      # usually means that somebody created a subclass just for the
      # assertions and has overriden __init__. "assertTrue" is a safe
      # value that will not make __init__ raise a ValueError (this is
      # a bit hacky).
      test_method = getattr(self, '_testMethodName', 'assertTrue')
      super(TestCase, self).__init__(test_method)

    return super(TestCase, self)._getAssertEqualityFunc(first, second)


# This is not really needed here, but some unrelated code calls this
# function.
# TODO(user): sort it out.
def _SortedListDifference(expected, actual):
  """Finds elements in only one or the other of two, sorted input lists.

  Returns a two-element tuple of lists.  The first list contains those
  elements in the "expected" list but not in the "actual" list, and the
  second contains those elements in the "actual" list but not in the
  "expected" list.  Duplicate elements in either input list are ignored.

  Args:
    expected:  The list we expected.
    actual:  The list we actualy got.
  Returns:
    (missing, unexpected)
    missing: items in expected that are not in actual.
    unexpected: items in actual that are not in expected.
  """
  i = j = 0
  missing = []
  unexpected = []
  while True:
    try:
      e = expected[i]
      a = actual[j]
      if e < a:
        missing.append(e)
        i += 1
        while expected[i] == e:
          i += 1
      elif e > a:
        unexpected.append(a)
        j += 1
        while actual[j] == a:
          j += 1
      else:
        i += 1
        try:
          while expected[i] == e:
            i += 1
        finally:
          j += 1
          while actual[j] == a:
            j += 1
    except IndexError:
      missing.extend(expected[i:])
      unexpected.extend(actual[j:])
      break
  return missing, unexpected


# ----------------------------------------------------------------------
# Functions to compare the actual output of a test to the expected
# (golden) output.
#
# Note: We could just replace the sys.stdout and sys.stderr objects,
# but we actually redirect the underlying file objects so that if the
# Python script execs any subprocess, their output will also be
# redirected.
#
# Usage:
#   basetest.CaptureTestStdout()
#   ... do something ...
#   basetest.DiffTestStdout("... path to golden file ...")
# ----------------------------------------------------------------------


class CapturedStream(object):
  """A temporarily redirected output stream."""

  def __init__(self, stream, filename):
    self._stream = stream
    self._fd = stream.fileno()
    self._filename = filename

    # Keep original stream for later
    self._uncaptured_fd = os.dup(self._fd)

    # Open file to save stream to
    cap_fd = os.open(self._filename,
                     os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
                     0o600)

    # Send stream to this file
    self._stream.flush()
    os.dup2(cap_fd, self._fd)
    os.close(cap_fd)

  def RestartCapture(self):
    """Resume capturing output to a file (after calling StopCapture)."""
    # Original stream fd
    assert self._uncaptured_fd

    # Append stream to file
    cap_fd = os.open(self._filename,
                     os.O_CREAT | os.O_APPEND | os.O_WRONLY,
                     0o600)

    # Send stream to this file
    self._stream.flush()
    os.dup2(cap_fd, self._fd)
    os.close(cap_fd)

  def StopCapture(self):
    """Remove output redirection."""
    self._stream.flush()
    os.dup2(self._uncaptured_fd, self._fd)

  def filename(self):
    return self._filename

  def __del__(self):
    self.StopCapture()
    os.close(self._uncaptured_fd)
    del self._uncaptured_fd


_captured_streams = {}


def _CaptureTestOutput(stream, filename):
  """Redirect an output stream to a file.

  Args:
    stream: Should be sys.stdout or sys.stderr.
    filename: File where output should be stored.
  """
  assert not _captured_streams.has_key(stream)
  _captured_streams[stream] = CapturedStream(stream, filename)


def _DiffTestOutput(stream, golden_filename):
  """Compare ouput of redirected stream to contents of golden file.

  Args:
    stream: Should be sys.stdout or sys.stderr.
    golden_filename: Absolute path to golden file.
  """
  assert _captured_streams.has_key(stream)
  cap = _captured_streams[stream]

  for cap_stream in _captured_streams.itervalues():
    cap_stream.StopCapture()

  try:
    _Diff(cap.filename(), golden_filename)
  finally:
    # remove the current stream
    del _captured_streams[stream]
    # restore other stream capture
    for cap_stream in _captured_streams.itervalues():
      cap_stream.RestartCapture()


# Public interface
def CaptureTestStdout(outfile=None):
  if not outfile:
    outfile = os.path.join(FLAGS.test_tmpdir, 'captured.out')

  _CaptureTestOutput(sys.stdout, outfile)


def CaptureTestStderr(outfile=None):
  if not outfile:
    outfile = os.path.join(FLAGS.test_tmpdir, 'captured.err')

  _CaptureTestOutput(sys.stderr, outfile)


def DiffTestStdout(golden):
  _DiffTestOutput(sys.stdout, golden)


def DiffTestStderr(golden):
  _DiffTestOutput(sys.stderr, golden)


def StopCapturing():
  while _captured_streams:
    _, cap_stream = _captured_streams.popitem()
    cap_stream.StopCapture()
    del cap_stream


def _WriteTestData(data, filename):
  """Write data into file named filename."""
  fd = os.open(filename, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
  os.write(fd, data)
  os.close(fd)


class OutputDifferedError(AssertionError):
  pass


class DiffFailureError(Exception):
  pass


def _Diff(lhs, rhs):
  """Run standard unix 'diff' against two files."""

  cmd = '${TEST_DIFF:-diff} %s %s' % (commands.mkarg(lhs), commands.mkarg(rhs))
  (status, output) = commands.getstatusoutput(cmd)
  if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 1:
    # diff outputs must be the same as c++ and shell
    raise OutputDifferedError('\nRunning %s\n%s\nTest output differed '
                              'from golden file\n' % (cmd, output))
  elif not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
    raise DiffFailureError('\nRunning %s\n%s\nFailure diffing test output '
                           'with golden file\n' % (cmd, output))


def DiffTestStringFile(data, golden):
  """Diff data agains a golden file."""
  data_file = os.path.join(FLAGS.test_tmpdir, 'provided.dat')
  _WriteTestData(data, data_file)
  _Diff(data_file, golden)


def DiffTestStrings(data1, data2):
  """Diff two strings."""
  data1_file = os.path.join(FLAGS.test_tmpdir, 'provided_1.dat')
  _WriteTestData(data1, data1_file)
  data2_file = os.path.join(FLAGS.test_tmpdir, 'provided_2.dat')
  _WriteTestData(data2, data2_file)
  _Diff(data1_file, data2_file)


def DiffTestFiles(testgen, golden):
  _Diff(testgen, golden)


def GetCommandString(command):
  """Returns an escaped string that can be used as a shell command.

  Args:
    command: List or string representing the command to run.
  Returns:
    A string suitable for use as a shell command.
  """
  if isinstance(command, types.StringTypes):
    return command
  else:
    return shellutil.ShellEscapeList(command)


def GetCommandStderr(command, env=None, close_fds=True):
  """Runs the given shell command and returns a tuple.

  Args:
    command: List or string representing the command to run.
    env: Dictionary of environment variable settings.
    close_fds: Whether or not to close all open fd's in the child after forking.

  Returns:
    Tuple of (exit status, text printed to stdout and stderr by the command).
  """
  if env is None: env = {}
  # Forge needs PYTHON_RUNFILES in order to find the runfiles directory when a
  # Python executable is run by a Python test.  Pass this through from the
  # parent environment if not explicitly defined.
  if os.environ.get('PYTHON_RUNFILES') and not env.get('PYTHON_RUNFILES'):
    env['PYTHON_RUNFILES'] = os.environ['PYTHON_RUNFILES']

  use_shell = isinstance(command, types.StringTypes)
  process = subprocess.Popen(
      command,
      close_fds=close_fds,
      env=env,
      shell=use_shell,
      stderr=subprocess.STDOUT,
      stdout=subprocess.PIPE)
  output = process.communicate()[0]
  exit_status = process.wait()
  return (exit_status, output)


def _QuoteLongString(s):
  """Quotes a potentially multi-line string to make the start and end obvious.

  Args:
    s: A string.

  Returns:
    The quoted string.
  """
  return ('8<-----------\n' +
          s + '\n' +
          '----------->8\n')


class TestProgramManualRun(unittest.TestProgram):
  """A TestProgram which runs the tests manually."""

  def runTests(self, do_run=False):
    """Run the tests."""
    if do_run:
      unittest.TestProgram.runTests(self)


def main(*args, **kwargs):
  """Executes a set of Python unit tests.

  Usually this function is called without arguments, so the
  unittest.TestProgram instance will get created with the default settings,
  so it will run all test methods of all TestCase classes in the __main__
  module.

  Args:
    args: Positional arguments passed through to unittest.TestProgram.__init__.
    kwargs: Keyword arguments passed through to unittest.TestProgram.__init__.
  """
  _RunInApp(RunTests, args, kwargs)


def _IsInAppMain():
  """Returns True iff app.main or app.really_start is active."""
  f = sys._getframe().f_back
  app_dict = app.__dict__
  while f:
    if f.f_globals is app_dict and f.f_code.co_name in ('run', 'really_start'):
      return True
    f = f.f_back
  return False


class SavedFlag(object):
  """Helper class for saving and restoring a flag value."""

  def __init__(self, flag):
    self.flag = flag
    self.value = flag.value
    self.present = flag.present

  def RestoreFlag(self):
    self.flag.value = self.value
    self.flag.present = self.present


def _RunInApp(function, args, kwargs):
  """Executes a set of Python unit tests, ensuring app.really_start.

  Most users should call basetest.main() instead of _RunInApp.

  _RunInApp calculates argv to be the command-line arguments of this program
  (without the flags), sets the default of FLAGS.alsologtostderr to True,
  then it calls function(argv, args, kwargs), making sure that `function'
  will get called within app.run() or app.really_start(). _RunInApp does this
  by checking whether it is called by either app.run() or
  app.really_start(), or by calling app.really_start() explicitly.

  The reason why app.really_start has to be ensured is to make sure that
  flags are parsed and stripped properly, and other initializations done by
  the app module are also carried out, no matter if basetest.run() is called
  from within or outside app.run().

  If _RunInApp is called from within app.run(), then it will reparse
  sys.argv and pass the result without command-line flags into the argv
  argument of `function'. The reason why this parsing is needed is that
  __main__.main() calls basetest.main() without passing its argv. So the
  only way _RunInApp could get to know the argv without the flags is that
  it reparses sys.argv.

  _RunInApp changes the default of FLAGS.alsologtostderr to True so that the
  test program's stderr will contain all the log messages unless otherwise
  specified on the command-line. This overrides any explicit assignment to
  FLAGS.alsologtostderr by the test program prior to the call to _RunInApp()
  (e.g. in __main__.main).

  Please note that _RunInApp (and the function it calls) is allowed to make
  changes to kwargs.

  Args:
    function: basetest.RunTests or a similar function. It will be called as
      function(argv, args, kwargs) where argv is a list containing the
      elements of sys.argv without the command-line flags.
    args: Positional arguments passed through to unittest.TestProgram.__init__.
    kwargs: Keyword arguments passed through to unittest.TestProgram.__init__.
  """
  if _IsInAppMain():
    # Save command-line flags so the side effects of FLAGS(sys.argv) can be
    # undone.
    saved_flags = dict((f.name, SavedFlag(f))
                       for f in FLAGS.FlagDict().itervalues())

    # Here we'd like to change the default of alsologtostderr from False to
    # True, so the test programs's stderr will contain all the log messages.
    # The desired effect is that if --alsologtostderr is not specified in
    # the command-line, and __main__.main doesn't set FLAGS.logtostderr
    # before calling us (basetest.main), then our changed default takes
    # effect and alsologtostderr becomes True.
    #
    # However, we cannot achive this exact effect, because here we cannot
    # distinguish these situations:
    #
    # A. main.__main__ has changed it to False, it hasn't been specified on
    #    the command-line, and the default was kept as False. We should keep
    #    it as False.
    #
    # B. main.__main__ hasn't changed it, it hasn't been specified on the
    #    command-line, and the default was kept as False. We should change
    #    it to True here.
    #
    # As a workaround, we assume that main.__main__ never changes
    # FLAGS.alsologstderr to False, thus the value of the flag is determined
    # by its default unless the command-line overrides it. We want to change
    # the default to True, and we do it by setting the flag value to True, and
    # letting the command-line override it in FLAGS(sys.argv) below by not
    # restoring it in saved_flag.RestoreFlag().
    if 'alsologtostderr' in saved_flags:
      FLAGS.alsologtostderr = True
      del saved_flags['alsologtostderr']

    # The call FLAGS(sys.argv) parses sys.argv, returns the arguments
    # without the flags, and -- as a side effect -- modifies flag values in
    # FLAGS. We don't want the side effect, because we don't want to
    # override flag changes the program did (e.g. in __main__.main)
    # after the command-line has been parsed. So we have the for loop below
    # to change back flags to their old values.
    argv = FLAGS(sys.argv)
    for saved_flag in saved_flags.itervalues():
      saved_flag.RestoreFlag()


    function(argv, args, kwargs)
  else:
    # Send logging to stderr. Use --alsologtostderr instead of --logtostderr
    # in case tests are reading their own logs.
    if 'alsologtostderr' in FLAGS:
      FLAGS.SetDefault('alsologtostderr', True)

    def Main(argv):
      function(argv, args, kwargs)

    app.really_start(main=Main)


def RunTests(argv, args, kwargs):
  """Executes a set of Python unit tests within app.really_start.

  Most users should call basetest.main() instead of RunTests.

  Please note that RunTests should be called from app.really_start (which is
  called from app.run()). Calling basetest.main() would ensure that.

  Please note that RunTests is allowed to make changes to kwargs.

  Args:
    argv: sys.argv with the command-line flags removed from the front, i.e. the
      argv with which app.run() has called __main__.main.
    args: Positional arguments passed through to unittest.TestProgram.__init__.
    kwargs: Keyword arguments passed through to unittest.TestProgram.__init__.
  """
  test_runner = kwargs.get('testRunner')

  # Make sure tmpdir exists
  if not os.path.isdir(FLAGS.test_tmpdir):
    os.makedirs(FLAGS.test_tmpdir)

  # Run main module setup, if it exists
  main_mod = sys.modules['__main__']
  if hasattr(main_mod, 'setUp') and callable(main_mod.setUp):
    main_mod.setUp()

  # Let unittest.TestProgram.__init__ called by
  # TestProgramManualRun.__init__ do its own argv parsing, e.g. for '-v',
  # on argv, which is sys.argv without the command-line flags.
  kwargs.setdefault('argv', argv)

  try:
    result = None
    test_program = TestProgramManualRun(*args, **kwargs)
    if test_runner:
      test_program.testRunner = test_runner
    else:
      test_program.testRunner = unittest.TextTestRunner(
          verbosity=test_program.verbosity)
    result = test_program.testRunner.run(test_program.test)
  finally:
    # Run main module teardown, if it exists
    if hasattr(main_mod, 'tearDown') and callable(main_mod.tearDown):
      main_mod.tearDown()

  sys.exit(not result.wasSuccessful())
