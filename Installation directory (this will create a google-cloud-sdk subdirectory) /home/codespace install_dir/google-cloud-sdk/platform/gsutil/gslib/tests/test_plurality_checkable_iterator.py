# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Unit tests for PluralityCheckableIterator."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sys

import six
from six.moves import range

from gslib.plurality_checkable_iterator import PluralityCheckableIterator
import gslib.tests.testcase as testcase


class CustomTestException(Exception):
  pass


class PluralityCheckableIteratorTests(testcase.GsUtilUnitTestCase):
  """Unit tests for PluralityCheckableIterator."""

  def testPluralityCheckableIteratorWith0Elems(self):
    """Tests empty PluralityCheckableIterator."""
    input_list = list(range(0))
    it = iter(input_list)
    pcit = PluralityCheckableIterator(it)
    self.assertTrue(pcit.IsEmpty())
    self.assertFalse(pcit.HasPlurality())
    output_list = list(pcit)
    self.assertEqual(input_list, output_list)

  def testPluralityCheckableIteratorWith1Elem(self):
    """Tests PluralityCheckableIterator with 1 element."""
    input_list = list(range(1))
    it = iter(input_list)
    pcit = PluralityCheckableIterator(it)
    self.assertFalse(pcit.IsEmpty())
    self.assertFalse(pcit.HasPlurality())
    output_list = list(pcit)
    self.assertEqual(input_list, output_list)

  def testPluralityCheckableIteratorWith2Elems(self):
    """Tests PluralityCheckableIterator with 2 elements."""
    input_list = list(range(2))
    it = iter(input_list)
    pcit = PluralityCheckableIterator(it)
    self.assertFalse(pcit.IsEmpty())
    self.assertTrue(pcit.HasPlurality())
    output_list = list(pcit)
    self.assertEqual(input_list, output_list)

  def testPluralityCheckableIteratorWith3Elems(self):
    """Tests PluralityCheckableIterator with 3 elements."""
    input_list = list(range(3))
    it = iter(input_list)
    pcit = PluralityCheckableIterator(it)
    self.assertFalse(pcit.IsEmpty())
    self.assertTrue(pcit.HasPlurality())
    output_list = list(pcit)
    self.assertEqual(input_list, output_list)

  def testPluralityCheckableIteratorWith1Elem1Exception(self):
    """Tests PluralityCheckableIterator with 2 elements.

    The second element raises an exception.
    """

    class IterTest(six.Iterator):

      def __init__(self):
        self.position = 0

      def __iter__(self):
        return self

      def __next__(self):
        if self.position == 0:
          self.position += 1
          return 1
        elif self.position == 1:
          self.position += 1
          raise CustomTestException('Test exception')
        else:
          raise StopIteration()

    pcit = PluralityCheckableIterator(IterTest())
    self.assertFalse(pcit.IsEmpty())
    self.assertTrue(pcit.HasPlurality())
    iterated_value = None
    try:
      for value in pcit:
        iterated_value = value
      self.fail('Expected exception from iterator')
    except CustomTestException:
      pass
    self.assertEqual(iterated_value, 1)

  def testPluralityCheckableIteratorWith2Exceptions(self):
    """Tests PluralityCheckableIterator with 2 elements that both raise."""

    class IterTest(six.Iterator):

      def __init__(self):
        self.position = 0

      def __iter__(self):
        return self

      def __next__(self):
        if self.position < 2:
          self.position += 1
          raise CustomTestException('Test exception %s' % self.position)
        else:
          raise StopIteration()

    pcit = PluralityCheckableIterator(IterTest())
    try:
      pcit.PeekException()
      self.fail('Expected exception 1 from PeekException')
    except CustomTestException as e:
      self.assertIn(str(e), 'Test exception 1')
    try:
      for _ in pcit:
        pass
      self.fail('Expected exception 1 from iterator')
    except CustomTestException as e:
      self.assertIn(str(e), 'Test exception 1')
    try:
      pcit.PeekException()
      self.fail('Expected exception 2 from PeekException')
    except CustomTestException as e:
      self.assertIn(str(e), 'Test exception 2')
    try:
      for _ in pcit:
        pass
      self.fail('Expected exception 2 from iterator')
    except CustomTestException as e:
      self.assertIn(str(e), 'Test exception 2')
    for _ in pcit:
      self.fail('Expected StopIteration')

  def testPluralityCheckableIteratorWithYieldedException(self):
    """Tests PCI with an iterator that yields an exception.

    The yielded exception is in the form of a tuple and must also contain a
    stack trace.
    """

    class IterTest(six.Iterator):

      def __init__(self):
        self.position = 0

      def __iter__(self):
        return self

      def __next__(self):
        if self.position == 0:
          try:
            self.position += 1
            raise CustomTestException('Test exception 0')
          except CustomTestException as e:
            return (e, sys.exc_info()[2])
        elif self.position == 1:
          self.position += 1
          return 1
        else:
          raise StopIteration()

    pcit = PluralityCheckableIterator(IterTest())
    iterated_value = None
    try:
      for _ in pcit:
        pass
      self.fail('Expected exception 0 from iterator')
    except CustomTestException as e:
      self.assertIn(str(e), 'Test exception 0')
    for value in pcit:
      iterated_value = value
    self.assertEqual(iterated_value, 1)

  def testPluralityCheckableIteratorReadsAheadAsNeeded(self):
    """Tests that the PCI does not unnecessarily read new elements."""

    class IterTest(six.Iterator):

      def __init__(self):
        self.position = 0

      def __iter__(self):
        return self

      def __next__(self):
        if self.position == 3:
          raise StopIteration()
        self.position += 1

    # IsEmpty and PeekException should retrieve only 1 element from the
    # underlying iterator.
    pcit = PluralityCheckableIterator(IterTest())
    pcit.IsEmpty()
    pcit.PeekException()
    self.assertEqual(pcit.orig_iterator.position, 1)
    # HasPlurality requires populating 2 elements into the iterator.
    pcit.HasPlurality()
    self.assertEqual(pcit.orig_iterator.position, 2)
    # next should yield already-populated elements without advancing the
    # iterator.
    next(pcit)  # Yields element 1
    self.assertEqual(pcit.orig_iterator.position, 2)
    next(pcit)  # Yields element 2
    self.assertEqual(pcit.orig_iterator.position, 2)
    next(pcit)  # Yields element 3
    self.assertEqual(pcit.orig_iterator.position, 3)
    try:
      next(pcit)  # Underlying iterator is empty
      self.fail('Expected StopIteration')
    except StopIteration:
      pass
