# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Module to define and determine exit codes for 'gcloud test' commands.

Note: Cloud-SDK-eng is reserving exit codes 1..9 for http errors, invalid args,
bad filename, etc. Gcloud command surfaces are free to use exit codes 10..20.
Gaps in exit_code numbering are left in case future expansion is needed.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log


ROLLUP_SUCCESS = 0       # Every test case within an execution passed.
ROLLUP_FAILURE = 10      # One or more test cases did not pass.
INCONCLUSIVE = 15        # The test pass/fail status was not determined.
UNSUPPORTED_ENV = 18     # The specified test environment is not supported.
MATRIX_CANCELLED = 19    # The matrix execution was cancelled by the user.
INFRASTRUCTURE_ERR = 20  # An infrastructure error occurred.


class TestOutcomeError(core_exceptions.Error):
  """The Tool Results backend did not return a valid test outcome."""

  def __init__(self, msg):
    super(TestOutcomeError, self).__init__(msg, exit_code=INFRASTRUCTURE_ERR)


def ExitCodeFromRollupOutcome(outcome, summary_enum):
  """Map a test roll-up outcome into the appropriate gcloud test exit_code.

  Args:
    outcome: a toolresults_v1.Outcome message.
    summary_enum: a toolresults.Outcome.SummaryValueValuesEnum reference.

  Returns:
    The exit_code which corresponds to the test execution's rolled-up outcome.

  Raises:
    TestOutcomeError: If Tool Results service returns an invalid outcome value.
  """
  if not outcome or not outcome.summary:
    log.warning('Tool Results service did not provide a roll-up test outcome.')
    return INCONCLUSIVE
  if (outcome.summary == summary_enum.success
      or outcome.summary == summary_enum.flaky):
    return ROLLUP_SUCCESS
  if outcome.summary == summary_enum.failure:
    return ROLLUP_FAILURE
  if outcome.summary == summary_enum.skipped:
    return UNSUPPORTED_ENV
  if outcome.summary == summary_enum.inconclusive:
    return INCONCLUSIVE
  raise TestOutcomeError(
      "Unknown test outcome summary value '{0}'".format(outcome.summary))
