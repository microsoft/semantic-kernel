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
"""Implementation of Retention Policy configuration command for buckets."""

from __future__ import absolute_import
from six.moves import input

from decimal import Decimal
import re

from gslib.exception import CommandException
from gslib.lazy_wrapper import LazyWrapper
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages

SECONDS_IN_DAY = 24 * 60 * 60
SECONDS_IN_MONTH = 31 * SECONDS_IN_DAY
SECONDS_IN_YEAR = int(365.25 * SECONDS_IN_DAY)
_LOCK_PROMPT = (
    'This will PERMANENTLY set the Retention Policy on gs://{} to:\n\n'
    '{}\n\nThis setting cannot be reverted!  Continue?')
# Regex to match retention period in years.
_RETENTION_IN_YEARS = LazyWrapper(lambda: re.compile(r'(?P<number>\d+)y$'))
# Regex to match retention period in months.
_RETENTION_IN_MONTHS = LazyWrapper(lambda: re.compile(r'(?P<number>\d+)m$'))
# Regex to match retention period in days.
_RETENTION_IN_DAYS = LazyWrapper(lambda: re.compile(r'(?P<number>\d+)d$'))
# Regex to match retention period in seconds.
_RETENTION_IN_SECONDS = LazyWrapper(lambda: re.compile(r'(?P<number>\d+)s$'))


def _ConfirmWithUserPrompt(question, default_response):
  """Prompts user to confirm an action with yes or no response.

  Args:
    question: Yes/No question to be used for the prompt.
    default_response: Default response to the question: True, False

  Returns:
    Returns the rough equivalent duration in seconds.
  """
  prompt = ''
  if default_response:
    prompt = '%s [%s|%s]: ' % (question, 'Y', 'n')
  else:
    prompt = '%s [%s|%s]: ' % (question, 'y', 'N')

  while True:
    response = input(prompt).lower()
    if not response:
      return default_response
    if response not in ['y', 'yes', 'n', 'no']:
      print('\tPlease respond with \'yes\'/\'y\' or \'no\'/\'n\'.')
      continue
    if response == 'yes' or response == 'y':
      return True
    if response == 'no' or response == 'n':
      return False


def _RetentionPeriodToString(retention_period):
  """Converts Retention Period to Human readable format.

  Args:
    retention_period: Retention duration in seconds (integer value).

  Returns:
    Returns a string representing retention duration in human readable format.
  """
  # TODO: add link to public documentation regarding conversion rates.

  period = Decimal(retention_period)
  duration_str = None

  if period // SECONDS_IN_YEAR == period / SECONDS_IN_YEAR:
    duration_str = '{} Year(s)'.format(period // SECONDS_IN_YEAR)
  elif period // SECONDS_IN_MONTH == period / SECONDS_IN_MONTH:
    duration_str = '{} Month(s)'.format(period // SECONDS_IN_MONTH)
  elif period // SECONDS_IN_DAY == period / SECONDS_IN_DAY:
    duration_str = '{} Day(s)'.format(period // SECONDS_IN_DAY)
  elif period > SECONDS_IN_DAY:
    duration_str = '{} Seconds (~{} Day(s))'.format(retention_period,
                                                    period // SECONDS_IN_DAY)
  else:
    duration_str = '{} Second(s)'.format(retention_period)

  return ('    Duration: {}').format(duration_str)


def RetentionPolicyToString(retention_policy, bucket_url):
  """Converts Retention Policy to Human readable format."""
  retention_policy_str = ''
  if retention_policy and retention_policy.retentionPeriod:
    locked_string = '(LOCKED)' if retention_policy.isLocked else '(UNLOCKED)'
    retention_period = _RetentionPeriodToString(
        retention_policy.retentionPeriod)
    retention_effective_time = '    Effective Time: {}'.format(
        retention_policy.effectiveTime.strftime('%a, %d %b %Y %H:%M:%S GMT'))
    retention_policy_str = '  Retention Policy {}:\n{}\n{}'.format(
        locked_string, retention_period, retention_effective_time)
  else:
    retention_policy_str = '{} has no Retention Policy.'.format(bucket_url)

  return retention_policy_str


def ConfirmLockRequest(bucket_url, retention_policy):
  retention_policy = RetentionPolicyToString(retention_policy, bucket_url)
  lock_prompt = _LOCK_PROMPT.format(bucket_url, retention_policy)
  return _ConfirmWithUserPrompt(lock_prompt, False)


def UpdateObjectMetadataExceptionHandler(cls, e):
  """Exception handler that maintains state about post-completion status."""
  cls.logger.error(e)
  cls.everything_set_okay = False


def SetTempHoldFuncWrapper(cls, name_expansion_result, thread_state=None):
  log_template = 'Setting Temporary Hold on %s...'
  object_metadata_update = apitools_messages.Object(temporaryHold=True)
  cls.ObjectUpdateMetadataFunc(object_metadata_update,
                               log_template,
                               name_expansion_result,
                               thread_state=thread_state)


def ReleaseTempHoldFuncWrapper(cls, name_expansion_result, thread_state=None):
  log_template = 'Releasing Temporary Hold on %s...'
  object_metadata_update = apitools_messages.Object(temporaryHold=False)
  cls.ObjectUpdateMetadataFunc(object_metadata_update,
                               log_template,
                               name_expansion_result,
                               thread_state=thread_state)


def SetEventHoldFuncWrapper(cls, name_expansion_result, thread_state=None):
  log_template = 'Setting Event-Based Hold on %s...'
  object_metadata_update = apitools_messages.Object(eventBasedHold=True)
  cls.ObjectUpdateMetadataFunc(object_metadata_update,
                               log_template,
                               name_expansion_result,
                               thread_state=thread_state)


def ReleaseEventHoldFuncWrapper(cls, name_expansion_result, thread_state=None):
  log_template = 'Releasing Event-Based Hold on %s...'
  object_metadata_update = apitools_messages.Object(eventBasedHold=False)
  cls.ObjectUpdateMetadataFunc(object_metadata_update,
                               log_template,
                               name_expansion_result,
                               thread_state=thread_state)


def DaysToSeconds(days):
  """Converts duration specified in days to equivalent seconds.

  Args:
    days: Retention duration in number of days.

  Returns:
    Returns the equivalent duration in seconds.
  """
  return days * SECONDS_IN_DAY


def MonthsToSeconds(months):
  """Converts duration specified in months to equivalent seconds.

    GCS bucket lock API uses following duration equivalencies to convert
    durations specified in terms of months or years to seconds:
      - A month is considered to be 31 days or 2,678,400 seconds.
      - A year is considered to be 365.25 days or 31,557,600 seconds.

  Args:
    months: Retention duration in number of months.

  Returns:
    Returns the rough equivalent duration in seconds.
  """
  return months * SECONDS_IN_MONTH


def YearsToSeconds(years):
  """Converts duration specified in years to equivalent seconds.

    GCS bucket lock API uses following duration equivalencies to convert
    durations specified in terms of months or years to seconds:
      - A month is considered to be 31 days or 2,678,400 seconds.
      - A year is considered to be 365.25 days or 31,557,600 seconds.

  Args:
    years: Retention duration in number of years.

  Returns:
    Returns the rough equivalent duration in seconds.
  """
  return years * SECONDS_IN_YEAR


def RetentionInYearsMatch(years):
  """Test whether the string matches retention in years pattern.

  Args:
    years: string to match for retention specified in years format.

  Returns:
    Returns a match object if the string matches the retention in years
    pattern. The match object will contain a 'number' group for the duration
    in number of years. Otherwise, None is returned.
  """
  return _RETENTION_IN_YEARS().match(years)


def RetentionInMonthsMatch(months):
  """Test whether the string matches retention in months pattern.

  Args:
    months: string to match for retention specified in months format.

  Returns:
    Returns a match object if the string matches the retention in months
    pattern. The match object will contain a 'number' group for the duration
    in number of months. Otherwise, None is returned.
  """
  return _RETENTION_IN_MONTHS().match(months)


def RetentionInDaysMatch(days):
  """Test whether the string matches retention in days pattern.

  Args:
    days: string to match for retention specified in days format.

  Returns:
    Returns a match object if the string matches the retention in days
    pattern. The match object will contain a 'number' group for the duration
    in number of days. Otherwise, None is returned.
  """
  return _RETENTION_IN_DAYS().match(days)


def RetentionInSecondsMatch(seconds):
  """Test whether the string matches retention in seconds pattern.

  Args:
    seconds: string to match for retention specified in seconds format.

  Returns:
    Returns a match object if the string matches the retention in seconds
    pattern. The match object will contain a 'number' group for the duration
    in number of seconds. Otherwise, None is returned.
  """
  return _RETENTION_IN_SECONDS().match(seconds)


def RetentionInSeconds(pattern):
  """Converts a retention period string pattern to equivalent seconds.

  Args:
    pattern: a string pattern that represents a retention period.

  Returns:
    Returns the retention period in seconds. If the pattern does not match
  """
  seconds = None
  year_match = RetentionInYearsMatch(pattern)
  month_match = RetentionInMonthsMatch(pattern)
  day_match = RetentionInDaysMatch(pattern)
  second_match = RetentionInSecondsMatch(pattern)
  if year_match:
    seconds = YearsToSeconds(int(year_match.group('number')))
  elif month_match:
    seconds = MonthsToSeconds(int(month_match.group('number')))
  elif day_match:
    seconds = DaysToSeconds(int(day_match.group('number')))
  elif second_match:
    seconds = int(second_match.group('number'))
  else:
    raise CommandException('Incorrect retention period specified. '
                           'Please use one of the following formats '
                           'to specify the retention period : '
                           '<number>y, <number>m, <number>d, <number>s.')
  return seconds
