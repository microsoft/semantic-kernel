# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base classes for diagnostics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


class Diagnostic(object):
  """Base class for diagnostics.

  Attributes:
    intro: A message to introduce the objectives and tasks of the diagnostic.
    title: The name of the diagnostic.
    checklist: An iterator of checkbase.Check objects to be run by the
       diagnostic.
  """

  _MAX_RETRIES = 5

  def __init__(self, intro, title, checklist):
    """Initializes Diagnostic with necessary attributes.

    Args:
      intro: A message to introduce the objectives and tasks of the diagnostic.
      title: The name of the diagnostic.
      checklist: An iterable of checkbase.Check objects to be run by the
         diagnostic.
    """
    self.intro = intro
    self.title = title
    self.checklist = checklist

  def RunChecks(self):
    """Runs one or more checks, tries fixes, and outputs results.

    Returns:
      True if the diagnostic ultimately passed.
    """
    self._Print(self.intro)

    num_checks_passed = 0
    for check in self.checklist:
      result, fixer = self._RunCheck(check)

      # If the initial check failed, and a fixer is available try to fix issue
      # and recheck.
      num_retries = 0
      while not result.passed and fixer and num_retries < self._MAX_RETRIES:
        num_retries += 1
        should_check_again = fixer()
        if should_check_again:
          result, fixer = self._RunCheck(check, first_run=False)
        else:
          fixer = None

      if not result.passed and fixer and num_retries == self._MAX_RETRIES:
        log.warning('Unable to fix {0} failure after {1} attempts.'.format(
            self.title, num_retries))
      if result.passed:
        num_checks_passed += 1

    num_checks = len(self.checklist)
    passed = num_checks_passed == num_checks
    summary = ('{check} {status} ({num_passed}/{num_checks} checks passed).\n'.
               format(check=self.title,
                      num_passed=num_checks_passed,
                      num_checks=num_checks,
                      status='passed' if passed else 'failed'))
    self._Print(summary, as_error=not passed)
    return passed

  def _RunCheck(self, check, first_run=True):
    with progress_tracker.ProgressTracker('{0} {1}'.format(
        'Checking' if first_run else 'Rechecking', check.issue)):
      result, fixer = check.Check(first_run=first_run)
    self._PrintResult(result)
    return result, fixer

  def _Print(self, message, as_error=False):
    logger = log.status.Print if not as_error else log.error
    logger(message)

  def _PrintResult(self, result):
    self._Print(result.message, not result.passed)
