#
# Copyright 2010 Google Inc. All Rights Reserved.

"""Tests for Dulwich.

This module is a stub that runs the builtin Dulwich test suite.
"""
from __future__ import print_function

import sys
import types
import unittest

import google3
from absl import flags
from dulwich import tests
from dulwich.tests import utils

if sys.version_info.major >= 3:
  from importlib import reload

# Hold on to the original unittest.TestCase. It is overwritten as a side effect
# of importing googletest, which breaks the default test runner.
_real_testcase = unittest.TestCase

from google3.devtools.git.common import (  # pylint: disable-msg=C6204
    git_test_util)

# We need googletest to define FLAGS.test_tmpdir
from google3.testing.pybase import googletest  # pylint: disable-msg=W0611

unittest.TestCase = _real_testcase

FLAGS = flags.FLAGS


def NonSkippingExtFunctestBuilder(method, func):
  """Alternate implementation of dulwich.tests.utils.ext_functest_builder.

  Dulwich skips extension tests for missing C extensions, but we need them in
  google3. This implementation fails fast if the C extensions are not found.

  Args:
    method: The method to run.
    func: The function implementation to pass to method.

  Returns:
    A test method to run the given C extension function.
  """

  def DoTest(self):
    self.assertTrue(isinstance(func, types.BuiltinFunctionType),
                    'C extension for %s not found' % func.__name__)
    method(self, func)

  return DoTest


# Replace Dulwich's ext_functest_builder with our implementation. This works
# because the test modules aren't loaded until test_suite() is called below.
utils.ext_functest_builder = NonSkippingExtFunctestBuilder


if __name__ == '__main__':
  print('ENCODING: ' + sys.getfilesystemencoding(), file=sys.stderr)
  reload(sys)
  sys.getfilesystemencoding = lambda: 'ascii'
  print('ENCODING: ' + sys.getfilesystemencoding(), file=sys.stderr)
  googletest.ThisTestIsUsefulWithoutCallingMain()
  result = unittest.TextTestRunner().run(tests.test_suite())
  sys.exit(not result.wasSuccessful())
