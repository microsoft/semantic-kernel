# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""Implementation of gsutil test command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from collections import namedtuple
import logging
import os
import subprocess
import re
import sys
import tempfile
import textwrap
import time
import traceback

import six
from six.moves import range

import gslib
from gslib.cloud_api import ProjectIdException
from gslib.command import Command
from gslib.command import ResetFailureCount
from gslib.exception import CommandException
from gslib.project_id import PopulateProjectId
import gslib.tests as tests
from gslib.tests.util import GetTestNames
from gslib.tests.util import InvokedFromParFile
from gslib.tests.util import unittest
from gslib.utils.constants import NO_MAX
from gslib.utils.constants import UTF8
from gslib.utils.system_util import IS_WINDOWS

# pylint: disable=g-import-not-at-top
try:
  import coverage
except ImportError:
  coverage = None

if six.PY3:
  long = int

_DEFAULT_TEST_PARALLEL_PROCESSES = 5
_DEFAULT_S3_TEST_PARALLEL_PROCESSES = 50
_SEQUENTIAL_ISOLATION_FLAG = 'sequential_only'

_SYNOPSIS = """
  gsutil test [-l] [-u] [-f] [command command...]
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The gsutil test command runs the gsutil unit tests and integration tests.
  The unit tests use an in-memory mock storage service implementation, while
  the integration tests send requests to the production service using the
  `preferred API
  <https://cloud.google.com/storage/docs/request-endpoints#gsutil>`_ set in the
  boto configuration file.

  CAUTION: The ``test`` command creates test buckets and objects in your project.
  Force quitting the ``test`` command can leave behind stale buckets, objects,
  and HMAC keys in your project.

  To run both the unit tests and integration tests, run the command with no
  arguments:

    gsutil test

  To run the unit tests only (which run quickly):

    gsutil test -u

  Tests run in parallel regardless of whether the top-level -m flag is
  present. To limit the number of tests run in parallel to 10 at a time:

    gsutil test -p 10

  To force tests to run sequentially:

    gsutil test -p 1

  To have sequentially-run tests stop running immediately when an error occurs:

    gsutil test -f

  To run tests for one or more individual commands add those commands as
  arguments. For example, the following command will run the cp and mv command
  tests:

    gsutil test cp mv

  To list available tests, run the test command with the -l argument:

    gsutil test -l

  The tests are defined in the code under the gslib/tests module. Each test
  file is of the format test_[name].py where [name] is the test name you can
  pass to this command. For example, running "gsutil test ls" would run the
  tests in "gslib/tests/test_ls.py".

  You can also run an individual test class or function name by passing the
  test module followed by the class name and optionally a test name. For
  example, to run the an entire test class by name:

    gsutil test naming.GsutilNamingTests

  or an individual test function:

    gsutil test cp.TestCp.test_streaming

  You can list the available tests under a module or class by passing arguments
  with the -l option. For example, to list all available test functions in the
  cp module:

    gsutil test -l cp

  To output test coverage:

    gsutil test -c -p 500
    coverage html

  This will output an HTML report to a directory named 'htmlcov'.

  Test coverage is compatible with v4.1 of the coverage module
  (https://pypi.python.org/pypi/coverage).


<B>OPTIONS</B>
  -b          Run tests against multi-regional US buckets. By default,
              tests run against regional buckets in us-central1.

  -c          Output coverage information.

  -f          Exit on first sequential test failure.

  -l          List available tests.

  -p N        Run at most N tests in parallel. The default value is %d.

  -s          Run tests against S3 instead of GS.

  -u          Only run unit tests.
""" % _DEFAULT_TEST_PARALLEL_PROCESSES)

TestProcessData = namedtuple('TestProcessData',
                             'name return_code stdout stderr')


def MakeCustomTestResultClass(total_tests):
  """Creates a closure of CustomTestResult.

  Args:
    total_tests: The total number of tests being run.

  Returns:
    An instance of CustomTestResult.
  """

  class CustomTestResult(unittest.TextTestResult):
    """A subclass of unittest.TextTestResult that prints a progress report."""

    def startTest(self, test):
      super(CustomTestResult, self).startTest(test)
      if self.dots:
        test_id = '.'.join(test.id().split('.')[-2:])
        message = ('\r%d/%d finished - E[%d] F[%d] s[%d] - %s' %
                   (self.testsRun, total_tests, len(self.errors),
                    len(self.failures), len(self.skipped), test_id))
        message = message[:73]
        message = message.ljust(73)
        self.stream.write('%s - ' % message)

  return CustomTestResult


def GetTestNamesFromSuites(test_suite):
  """Takes a list of test suites and returns a list of contained test names."""
  suites = [test_suite]
  test_names = []
  while suites:
    suite = suites.pop()
    for test in suite:
      if isinstance(test, unittest.TestSuite):
        suites.append(test)
      else:
        test_names.append(test.id()[len('gslib.tests.test_'):])
  return test_names


# pylint: disable=protected-access
# Need to get into the guts of unittest to evaluate test cases for parallelism.
def TestCaseToName(test_case):
  """Converts a python.unittest to its gsutil test-callable name."""
  return (str(test_case.__class__).split('\'')[1] + '.' +
          test_case._testMethodName)


# pylint: disable=protected-access
# Need to get into the guts of unittest to evaluate test cases for parallelism.
def SplitParallelizableTestSuite(test_suite):
  """Splits a test suite into groups with different running properties.

  Args:
    test_suite: A python unittest test suite.

  Returns:
    4-part tuple of lists of test names:
    (tests that must be run sequentially,
     tests that must be isolated in a separate process but can be run either
         sequentially or in parallel,
     unit tests that can be run in parallel,
     integration tests that can run in parallel)
  """
  # pylint: disable=import-not-at-top
  # Need to import this after test globals are set so that skip functions work.
  from gslib.tests.testcase.unit_testcase import GsUtilUnitTestCase
  isolated_tests = []
  sequential_tests = []
  parallelizable_integration_tests = []
  parallelizable_unit_tests = []

  items_to_evaluate = [test_suite]
  cases_to_evaluate = []
  # Expand the test suites into individual test cases:
  while items_to_evaluate:
    suite_or_case = items_to_evaluate.pop()
    if isinstance(suite_or_case, unittest.suite.TestSuite):
      for item in suite_or_case._tests:
        items_to_evaluate.append(item)
    elif isinstance(suite_or_case, unittest.TestCase):
      cases_to_evaluate.append(suite_or_case)

  for test_case in cases_to_evaluate:
    test_method = getattr(test_case, test_case._testMethodName, None)
    if getattr(test_method, 'requires_isolation', False):
      # Test must be isolated to a separate process, even it if is being
      # run sequentially.
      isolated_tests.append(TestCaseToName(test_case))
    elif not getattr(test_method, 'is_parallelizable', True):
      sequential_tests.append(TestCaseToName(test_case))
    elif not getattr(test_case, 'is_parallelizable', True):
      sequential_tests.append(TestCaseToName(test_case))
    elif isinstance(test_case, GsUtilUnitTestCase):
      parallelizable_unit_tests.append(TestCaseToName(test_case))
    else:
      parallelizable_integration_tests.append(TestCaseToName(test_case))

  return (sorted(sequential_tests), sorted(isolated_tests),
          sorted(parallelizable_unit_tests),
          sorted(parallelizable_integration_tests))


def CountFalseInList(input_list):
  """Counts number of falses in the input list."""
  num_false = 0
  for item in input_list:
    if not item:
      num_false += 1
  return num_false


def CreateTestProcesses(parallel_tests,
                        test_index,
                        process_list,
                        process_done,
                        max_parallel_tests,
                        root_coverage_file=None):
  """Creates test processes to run tests in parallel.

  Args:
    parallel_tests: List of all parallel tests.
    test_index: List index of last created test before this function call.
    process_list: List of running subprocesses. Created processes are appended
                  to this list.
    process_done: List of booleans indicating process completion. One 'False'
                  will be added per process created.
    max_parallel_tests: Maximum number of tests to run in parallel.
    root_coverage_file: The root .coverage filename if coverage is requested.

  Returns:
    Index of last created test.
  """
  orig_test_index = test_index
  # checking to see if test was invoked from a par file (bundled archive)
  # if not, add python executable path to ensure correct version of python
  # is used for testing
  executable_prefix = [sys.executable] if not InvokedFromParFile() else []
  s3_argument = ['-s'] if tests.util.RUN_S3_TESTS else []
  multiregional_buckets = ['-b'] if tests.util.USE_MULTIREGIONAL_BUCKETS else []
  project_id_arg = []
  try:
    project_id_arg = [
        '-o', 'GSUtil:default_project_id=%s' % PopulateProjectId()
    ]
  except ProjectIdException:
    # If we don't have a project ID, unit tests should still be able to pass.
    pass

  process_create_start_time = time.time()
  last_log_time = process_create_start_time
  while (CountFalseInList(process_done) < max_parallel_tests and
         test_index < len(parallel_tests)):
    env = os.environ.copy()
    if root_coverage_file:
      env['GSUTIL_COVERAGE_OUTPUT_FILE'] = root_coverage_file
    envstr = dict()
    # constructing command list and ensuring each part is str
    cmd = [
        six.ensure_str(part) for part in list(
            executable_prefix +
            [gslib.GSUTIL_PATH] +
            project_id_arg +
            ['test'] +
            s3_argument +
            multiregional_buckets +
            ['--' + _SEQUENTIAL_ISOLATION_FLAG] +
            [parallel_tests[test_index][len('gslib.tests.test_'):]]
        )
    ]  # yapf: disable
    for k, v in six.iteritems(env):
      envstr[six.ensure_str(k)] = six.ensure_str(v)
    process_list.append(
        subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         env=envstr))
    test_index += 1
    process_done.append(False)
    if time.time() - last_log_time > 5:
      print(('Created %d new processes (total %d/%d created)' %
             (test_index - orig_test_index, len(process_list),
              len(parallel_tests))))
      last_log_time = time.time()
  if test_index == len(parallel_tests):
    print(('Test process creation finished (%d/%d created)' %
           (len(process_list), len(parallel_tests))))
  return test_index


class TestCommand(Command):
  """Implementation of gsutil test command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'test',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=NO_MAX,
      supported_sub_args='buflp:sc',
      file_url_ok=True,
      provider_url_ok=False,
      urls_start_arg=0,
      supported_private_args=[_SEQUENTIAL_ISOLATION_FLAG],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='test',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary=(
          'Run gsutil unit/integration tests (for developers)'),
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def RunParallelTests(self, parallel_integration_tests, max_parallel_tests,
                       coverage_filename):
    """Executes the parallel/isolated portion of the test suite.

    Args:
      parallel_integration_tests: List of tests to execute.
      max_parallel_tests: Maximum number of parallel tests to run at once.
      coverage_filename: If not None, filename for coverage output.

    Returns:
      (int number of test failures, float elapsed time)
    """
    process_list = []
    process_done = []
    process_results = []  # Tuples of (name, return code, stdout, stderr)
    num_parallel_failures = 0
    # Number of logging cycles we ran with no progress.
    progress_less_logging_cycles = 0
    completed_as_of_last_log = 0
    num_parallel_tests = len(parallel_integration_tests)
    parallel_start_time = last_log_time = time.time()
    test_index = CreateTestProcesses(parallel_integration_tests,
                                     0,
                                     process_list,
                                     process_done,
                                     max_parallel_tests,
                                     root_coverage_file=coverage_filename)
    while len(process_results) < num_parallel_tests:
      for proc_num in range(len(process_list)):
        if process_done[proc_num] or process_list[proc_num].poll() is None:
          continue
        process_done[proc_num] = True
        stdout, stderr = process_list[proc_num].communicate()
        process_list[proc_num].stdout.close()
        process_list[proc_num].stderr.close()
        # TODO: Differentiate test failures from errors.
        if process_list[proc_num].returncode != 0:
          num_parallel_failures += 1
        process_results.append(
            TestProcessData(name=parallel_integration_tests[proc_num],
                            return_code=process_list[proc_num].returncode,
                            stdout=stdout,
                            stderr=stderr))
      if len(process_list) < num_parallel_tests:
        test_index = CreateTestProcesses(parallel_integration_tests,
                                         test_index,
                                         process_list,
                                         process_done,
                                         max_parallel_tests,
                                         root_coverage_file=coverage_filename)
      if len(process_results) < num_parallel_tests:
        if time.time() - last_log_time > 5:
          print(
              '%d/%d finished - %d failures' %
              (len(process_results), num_parallel_tests, num_parallel_failures))
          if len(process_results) == completed_as_of_last_log:
            progress_less_logging_cycles += 1
          else:
            completed_as_of_last_log = len(process_results)
            # A process completed, so we made progress.
            progress_less_logging_cycles = 0
          if progress_less_logging_cycles > 4:
            # Ran 5 or more logging cycles with no progress, let the user
            # know which tests are running slowly or hanging.
            still_running = []
            for proc_num in range(len(process_list)):
              if not process_done[proc_num]:
                still_running.append(parallel_integration_tests[proc_num])
            elapsed = time.time() - parallel_start_time
            print(('{sec} seconds elapsed since beginning parallel tests.\n'
                   'Still running: {procs}').format(
                       sec=str(int(elapsed)),
                       procs=still_running,
                   ))
            # TODO: Terminate still-running processes if they
            # hang for a long time.
          last_log_time = time.time()
        time.sleep(1)
    process_run_finish_time = time.time()
    if num_parallel_failures:
      for result in process_results:
        if result.return_code != 0:
          new_stderr = result.stderr.split(b'\n')
          print('Results for failed test %s:' % result.name)
          for line in new_stderr:
            print(line.decode(UTF8).strip())

    return (num_parallel_failures,
            (process_run_finish_time - parallel_start_time))

  def PrintTestResults(self, num_sequential_tests, sequential_success,
                       sequential_skipped, sequential_time_elapsed,
                       num_parallel_tests, num_parallel_failures,
                       parallel_time_elapsed):
    """Prints test results for parallel and sequential tests."""
    # TODO: Properly track test skips.
    print('Parallel tests complete. Success: %s Fail: %s' %
          (num_parallel_tests - num_parallel_failures, num_parallel_failures))
    print((
        'Ran %d tests in %.3fs (%d sequential in %.3fs, %d parallel in %.3fs)' %
        (num_parallel_tests + num_sequential_tests,
         float(sequential_time_elapsed + parallel_time_elapsed),
         num_sequential_tests, float(sequential_time_elapsed),
         num_parallel_tests, float(parallel_time_elapsed))))
    self.PrintSkippedTests(sequential_skipped)
    print()

    if not num_parallel_failures and sequential_success:
      print('OK')
    else:
      if num_parallel_failures:
        print('FAILED (parallel tests)')
      if not sequential_success:
        print('FAILED (sequential tests)')

  # TODO: Parallel skipped tests are never gathered anywhere, this needs implementation in RunParallelTests
  def PrintSkippedTests(self, sequential_skipped=set(), parallel_skipped=set()):
    """Prints all skipped tests, and the reasons they  were skipped.

    Takes the union of sequentual_skipped and parallel_skipped,
    and pretty-prints the resulting methods and reasons. Note that these two
    arguments are lists of tuples from TestResult.skipped as described here:
    https://docs.python.org/2/library/unittest.html#unittest.TestResult.skipped

    Args:
        sequentual_skipped: An instance of TestResult.skipped.
        parallel_skipped: An instance of TestResult.skipped.
    """
    if len(sequential_skipped) > 0 or len(parallel_skipped) > 0:
      sequential_skipped = set(sequential_skipped)
      parallel_skipped = set(parallel_skipped)
      all_skipped = sequential_skipped.union(parallel_skipped)

      print('Tests skipped:')
      for method, reason in all_skipped:
        print('  ' + method.id())
        print('    Reason: ' + reason)

  def RunCommand(self):
    """Command entry point for the test command."""
    failfast = False
    list_tests = False
    max_parallel_tests = _DEFAULT_TEST_PARALLEL_PROCESSES
    perform_coverage = False
    sequential_only = False
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-b':
          tests.util.USE_MULTIREGIONAL_BUCKETS = True
        elif o == '-c':
          perform_coverage = True
        elif o == '-f':
          failfast = True
        elif o == '-l':
          list_tests = True
        elif o == ('--' + _SEQUENTIAL_ISOLATION_FLAG):
          # Called to isolate a single test in a separate process.
          # Don't try to isolate it again (would lead to an infinite loop).
          sequential_only = True
        elif o == '-p':
          max_parallel_tests = long(a)
        elif o == '-s':
          if not tests.util.HAS_S3_CREDS:
            raise CommandException('S3 tests require S3 credentials. Please '
                                   'add appropriate credentials to your .boto '
                                   'file and re-run.')
          tests.util.RUN_S3_TESTS = True
        elif o == '-u':
          tests.util.RUN_INTEGRATION_TESTS = False

    if perform_coverage and not coverage:
      raise CommandException(
          'Coverage has been requested but the coverage module was not found. '
          'You can install it with "pip install coverage".')

    if (tests.util.RUN_S3_TESTS and
        max_parallel_tests > _DEFAULT_S3_TEST_PARALLEL_PROCESSES):
      self.logger.warn(
          'Reducing parallel tests to %d due to S3 maximum bucket '
          'limitations.', _DEFAULT_S3_TEST_PARALLEL_PROCESSES)
      max_parallel_tests = _DEFAULT_S3_TEST_PARALLEL_PROCESSES

    test_names = sorted(GetTestNames())
    if list_tests and not self.args:
      print('Found %d test names:' % len(test_names))
      print(' ', '\n  '.join(sorted(test_names)))
      return 0

    # Set list of commands to test if supplied.
    if self.args:
      commands_to_test = []
      for name in self.args:
        if name in test_names or name.split('.')[0] in test_names:
          commands_to_test.append('gslib.tests.test_%s' % name)
        else:
          commands_to_test.append(name)
    else:
      commands_to_test = ['gslib.tests.test_%s' % name for name in test_names]

    # Installs a ctrl-c handler that tries to cleanly tear down tests.
    unittest.installHandler()

    loader = unittest.TestLoader()

    if commands_to_test:
      suite = unittest.TestSuite()
      for command_name in commands_to_test:
        try:
          suite_for_current_command = loader.loadTestsFromName(command_name)
          suite.addTests(suite_for_current_command)
        except (ImportError, AttributeError) as e:
          msg = ('Failed to import test code from file %s. TestLoader provided '
                 'this error:\n\n%s' % (command_name, str(e)))

          # Try to give a better error message; by default, unittest swallows
          # ImportErrors and only shows that an import failed, not why. E.g.:
          # "'module' object has no attribute 'test_cp'
          try:
            __import__(command_name)
          except Exception as e:
            stack_trace = traceback.format_exc()
            err = re.sub('\\n', '\n    ', stack_trace)
            msg += '\n\nAdditional traceback:\n\n%s' % (err)

          raise CommandException(msg)

    if list_tests:
      test_names = GetTestNamesFromSuites(suite)
      print('Found %d test names:' % len(test_names))
      print(' ', '\n  '.join(sorted(test_names)))
      return 0

    if logging.getLogger().getEffectiveLevel() <= logging.INFO:
      verbosity = 1
    else:
      verbosity = 2
      logging.disable(logging.ERROR)

    if perform_coverage:
      # We want to run coverage over the gslib module, but filter out the test
      # modules and any third-party code. We also filter out anything under the
      # temporary directory. Otherwise, the gsutil update test (which copies
      # code to the temporary directory) gets included in the output.
      coverage_controller = coverage.coverage(source=['gslib'],
                                              omit=[
                                                  'gslib/third_party/*',
                                                  'gslib/tests/*',
                                                  tempfile.gettempdir() + '*',
                                              ])
      coverage_controller.erase()
      coverage_controller.start()

    num_parallel_failures = 0
    sequential_success = False

    (sequential_tests, isolated_tests, parallel_unit_tests,
     parallel_integration_tests) = (SplitParallelizableTestSuite(suite))

    # Since parallel integration tests are run in a separate process, they
    # won't get the override to tests.util, so skip them here.
    if not tests.util.RUN_INTEGRATION_TESTS:
      parallel_integration_tests = []

    logging.debug('Sequential tests to run: %s', sequential_tests)
    logging.debug('Isolated tests to run: %s', isolated_tests)
    logging.debug('Parallel unit tests to run: %s', parallel_unit_tests)
    logging.debug('Parallel integration tests to run: %s',
                  parallel_integration_tests)

    # If we're running an already-isolated test (spawned in isolation by a
    # previous test process), or we have no parallel tests to run,
    # just run sequentially. For now, unit tests are always run sequentially.
    run_tests_sequentially = (sequential_only or
                              (len(parallel_integration_tests) <= 1 and
                               not isolated_tests))

    # Disable analytics for the duration of testing. This is set as an
    # environment variable so that the subprocesses will also not report.
    os.environ['GSUTIL_TEST_ANALYTICS'] = '1'

    if run_tests_sequentially:
      total_tests = suite.countTestCases()
      resultclass = MakeCustomTestResultClass(total_tests)

      runner = unittest.TextTestRunner(verbosity=verbosity,
                                       resultclass=resultclass,
                                       failfast=failfast)
      ret = runner.run(suite)
      sequential_success = ret.wasSuccessful()
    else:
      if max_parallel_tests == 1:
        # We can't take advantage of parallelism, though we may have tests that
        # need isolation.
        sequential_tests += parallel_integration_tests
        parallel_integration_tests = []

      sequential_start_time = time.time()
      # TODO: For now, run unit tests sequentially because they are fast.
      # We could potentially shave off several seconds of execution time
      # by executing them in parallel with the integration tests.
      if len(sequential_tests) + len(parallel_unit_tests):
        print('Running %d tests sequentially.' %
              (len(sequential_tests) + len(parallel_unit_tests)))
        sequential_tests_to_run = sequential_tests + parallel_unit_tests
        suite = loader.loadTestsFromNames(
            sorted([test_name for test_name in sequential_tests_to_run]))
        num_sequential_tests = suite.countTestCases()
        resultclass = MakeCustomTestResultClass(num_sequential_tests)
        runner = unittest.TextTestRunner(verbosity=verbosity,
                                         resultclass=resultclass,
                                         failfast=failfast)

        ret = runner.run(suite)
        sequential_success = ret.wasSuccessful()
        sequential_skipped = ret.skipped
      else:
        num_sequential_tests = 0
        sequential_success = True
      sequential_time_elapsed = time.time() - sequential_start_time

      # At this point, all tests get their own process so just treat the
      # isolated tests as parallel tests.
      parallel_integration_tests += isolated_tests
      num_parallel_tests = len(parallel_integration_tests)

      if not num_parallel_tests:
        pass
      else:
        sequential_skipped = []
        num_processes = min(max_parallel_tests, num_parallel_tests)
        if num_parallel_tests > 1 and max_parallel_tests > 1:
          message = 'Running %d tests in parallel mode (%d processes).'
          if num_processes > _DEFAULT_TEST_PARALLEL_PROCESSES:
            message += (
                ' Please be patient while your CPU is incinerated. '
                'If your machine becomes unresponsive, consider reducing '
                'the amount of parallel test processes by running '
                '\'gsutil test -p <num_processes>\'.')
          print(('\n'.join(
              textwrap.wrap(message % (num_parallel_tests, num_processes)))))
        else:
          print(('Running %d tests sequentially in isolated processes.' %
                 num_parallel_tests))
        (num_parallel_failures, parallel_time_elapsed) = self.RunParallelTests(
            parallel_integration_tests, max_parallel_tests,
            coverage_controller.data_files.filename
            if perform_coverage else None)
        self.PrintTestResults(num_sequential_tests, sequential_success,
                              sequential_skipped, sequential_time_elapsed,
                              num_parallel_tests, num_parallel_failures,
                              parallel_time_elapsed)

    if perform_coverage:
      coverage_controller.stop()
      coverage_controller.combine()
      coverage_controller.save()
      print(('Coverage information was saved to: %s' %
             coverage_controller.data_files.filename))

    # Re-enable analytics to report the test command.
    os.environ['GSUTIL_TEST_ANALYTICS'] = '0'

    if sequential_success and not num_parallel_failures:
      ResetFailureCount()
      return 0
    return 1
