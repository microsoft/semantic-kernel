# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Unit tests for retention_util module."""

from __future__ import absolute_import

import gslib.tests.testcase as testcase
from gslib.utils.retention_util import _RetentionPeriodToString
from gslib.utils.retention_util import DaysToSeconds
from gslib.utils.retention_util import MonthsToSeconds
from gslib.utils.retention_util import RetentionInDaysMatch
from gslib.utils.retention_util import RetentionInMonthsMatch
from gslib.utils.retention_util import RetentionInSeconds
from gslib.utils.retention_util import RetentionInSecondsMatch
from gslib.utils.retention_util import RetentionInYearsMatch
from gslib.utils.retention_util import SECONDS_IN_DAY
from gslib.utils.retention_util import SECONDS_IN_MONTH
from gslib.utils.retention_util import SECONDS_IN_YEAR
from gslib.utils.retention_util import YearsToSeconds


class TestRetentionUtil(testcase.GsUtilUnitTestCase):
  """Unit tests for gsutil retention_util module."""

  def testDaysToSeconds(self):
    secs = DaysToSeconds(1)
    self.assertEqual(secs, 1 * SECONDS_IN_DAY)

    secs = DaysToSeconds(3)
    self.assertEqual(secs, 3 * SECONDS_IN_DAY)

  def testMonthsToSeconds(self):
    secs = MonthsToSeconds(1)
    self.assertEqual(secs, 1 * SECONDS_IN_MONTH)

    secs = MonthsToSeconds(3)
    self.assertEqual(secs, 3 * SECONDS_IN_MONTH)

  def testYearsToSeconds(self):
    secs = YearsToSeconds(1)
    self.assertEqual(secs, 1 * SECONDS_IN_YEAR)

    secs = YearsToSeconds(3)
    self.assertEqual(secs, 3 * SECONDS_IN_YEAR)

  def testRetentionInSecondsMatch(self):
    secs = '30s'
    secs_match = RetentionInSecondsMatch(secs)
    self.assertEqual('30', secs_match.group('number'))

    secs = '1s'
    secs_match = RetentionInSecondsMatch(secs)
    self.assertEqual('1', secs_match.group('number'))

    secs = '1second'
    secs_match = RetentionInSecondsMatch(secs)
    self.assertEqual(None, secs_match)

  def testRetentionInMonthsMatch(self):
    months = '30m'
    months_match = RetentionInMonthsMatch(months)
    self.assertEqual('30', months_match.group('number'))

    months = '1m'
    months_match = RetentionInMonthsMatch(months)
    self.assertEqual('1', months_match.group('number'))

    months = '1month'
    months_match = RetentionInMonthsMatch(months)
    self.assertEqual(None, months_match)

  def testRetentionInDaysMatch(self):
    days = '30d'
    days_match = RetentionInDaysMatch(days)
    self.assertEqual('30', days_match.group('number'))

    days = '1d'
    days_match = RetentionInDaysMatch(days)
    self.assertEqual('1', days_match.group('number'))

    days = '1day'
    days_match = RetentionInDaysMatch(days)
    self.assertEqual(None, days_match)

  def testRetentionInYearsMatch(self):
    years = '30y'
    years_match = RetentionInYearsMatch(years)
    self.assertEqual('30', years_match.group('number'))

    years = '1y'
    years_match = RetentionInYearsMatch(years)
    self.assertEqual('1', years_match.group('number'))

    years = '1year'
    years_match = RetentionInYearsMatch(years)
    self.assertEqual(None, years_match)

  def testRetentionInSeconds(self):
    one_year = '1y'
    one_year_in_seconds = RetentionInSeconds(one_year)
    self.assertEqual(SECONDS_IN_YEAR, one_year_in_seconds)

    one_month = '1m'
    one_month_in_seconds = RetentionInSeconds(one_month)
    self.assertEqual(SECONDS_IN_MONTH, one_month_in_seconds)

    one_day = '1d'
    one_day_in_seconds = RetentionInSeconds(one_day)
    self.assertEqual(SECONDS_IN_DAY, one_day_in_seconds)

    one_second = '1s'
    one_second_in_seconds = RetentionInSeconds(one_second)
    self.assertEqual(1, one_second_in_seconds)

  def testRetentionPeriodToString(self):
    retention_str = _RetentionPeriodToString(SECONDS_IN_DAY)
    self.assertRegex(retention_str, r'Duration: 1 Day\(s\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_DAY - 1)
    self.assertRegex(retention_str, r'Duration: 86399 Second\(s\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_DAY + 1)
    self.assertRegex(retention_str,
                             r'Duration: 86401 Seconds \(~1 Day\(s\)\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_MONTH)
    self.assertRegex(retention_str, r'Duration: 1 Month\(s\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_MONTH - 1)
    self.assertRegex(retention_str,
                             r'Duration: 2678399 Seconds \(~30 Day\(s\)\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_MONTH + 1)
    self.assertRegex(retention_str,
                             r'Duration: 2678401 Seconds \(~31 Day\(s\)\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_YEAR)
    self.assertRegex(retention_str, r'Duration: 1 Year\(s\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_YEAR - 1)
    self.assertRegex(retention_str,
                             r'Duration: 31557599 Seconds \(~365 Day\(s\)\)')

    retention_str = _RetentionPeriodToString(SECONDS_IN_YEAR + 1)
    self.assertRegex(retention_str,
                             r'Duration: 31557601 Seconds \(~365 Day\(s\)\)')
