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

"""ISO 8601 duration/period support.

https://en.wikipedia.org/wiki/ISO_8601#Durations
https://tools.ietf.org/html/rfc3339

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime


_DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_DAYS_PER_YEAR = 365.2422

_MICROSECONDS_PER_SECOND = 1000000
_SECONDS_PER_MINUTE = 60
_MINUTES_PER_HOUR = 60
_HOURS_PER_DAY = 24
_MONTHS_PER_YEAR = 12

_SECONDS_PER_HOUR = _SECONDS_PER_MINUTE * _MINUTES_PER_HOUR
_SECONDS_PER_DAY = _SECONDS_PER_HOUR * _HOURS_PER_DAY
_SECONDS_PER_YEAR = _SECONDS_PER_DAY * _DAYS_PER_YEAR
_SECONDS_PER_MONTH = _SECONDS_PER_YEAR / _MONTHS_PER_YEAR


def IsLeapYear(year):
  """Returns True if year is a leap year.

  Cheaper than `import calendar` because its the only thing needed here.

  Args:
    year: The 4 digit year.

  Returns:
    True if year is a leap year.
  """
  return (year % 400 == 0) or (year % 100 != 0) and (year % 4 == 0)


def DaysInCalendarMonth(year, month):
  """Returns the number of days in the given month and calendar year.

  Args:
    year: The 4 digit calendar year.
    month: The month number 1..12.

  Returns:
    The number of days in the given month and calendar year.
  """
  return _DAYS_IN_MONTH[month - 1] + (
      1 if month == 2 and IsLeapYear(year) else 0)


def _FormatNumber(result, number, suffix='', precision=3):
  """Appends a formatted number + suffix to result.

  Trailing "0" and "." are stripped. If no digits remain then nothing is
  appended to result.

  Args:
    result: The formatted number, if any is appended to this list.
    number: The int or float to format.
    suffix: A suffix string to append to the number.
    precision: Format the last duration part with precision digits after the
      decimal point. Trailing "0" and "." are always stripped.
  """
  fmt = '{{0:.{precision}f}}'.format(precision=precision)
  s = fmt.format(float(number))
  if precision:
    s = s.rstrip('0')
    if s.endswith('.'):
      s = s[:-1]
  if s and s != '0':
    result.append(s + suffix)


class Duration(object):
  """The parts of an ISO 8601 duration plus microseconds.

  Durations using only hours, miniutes, seconds and microseconds are exact.
  calendar=True allows the constructor to use duration units larger than hours.
  These durations will be inexact across daylight savings time and leap year
  boundaries, but will be "calendar" correct. For example:

    2015-02-14 + P1Y   => 2016-02-14
    2015-02-14 + P365D => 2016-02-14
    2016-02-14 + P1Y   => 2017-02-14
    2016-02-14 + P366D => 2017-02-14

    2016-03-13T01:00:00 + P1D   => 2016-03-14T01:00:00
    2016-03-13T01:00:00 + PT23H => 2016-03-14T01:00:00
    2016-03-13T01:00:00 + PT24H => 2016-03-14T03:00:00

  delta durations (initialized from datetime.timedelta) are calendar=False.
  Parsed durations containing duration units larger than hours are
  calendar=True.
  """

  def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0,
               microseconds=0, delta=None, calendar=False):
    self.years = years
    self.months = months
    self.days = days
    self.hours = hours
    self.minutes = minutes
    self.seconds = seconds
    self.microseconds = microseconds
    self.total_seconds = 0
    if delta:
      self.seconds += delta.total_seconds()
    self.calendar = calendar
    self._Normalize()

  def _Normalize(self):
    """Normalizes duration values to integers in ISO 8601 ranges.

    Normalization makes formatted durations aesthetically pleasing. For example,
    P2H30M0.5S instead of P9000.5S. It also determines if the duration is exact
    or a calendar duration.
    """

    # Percolate fractional parts down to self.microseconds.

    # Returns (whole,fraction) of pleasingly rounded f.
    def _Percolate(f):
      int_value = int(f)
      fraction = round(round(f, 4) - int_value, 4)
      return int_value, fraction

    self.years, fraction = _Percolate(self.years)
    if fraction:
      self.days += _DAYS_PER_YEAR * fraction

    self.months, fraction = _Percolate(self.months)
    if fraction:
      # Truncate to integer days because of irregular months.
      self.days += int(_DAYS_PER_YEAR * fraction / _MONTHS_PER_YEAR)

    self.days, fraction = _Percolate(self.days)
    if fraction:
      self.hours += _HOURS_PER_DAY * fraction

    self.hours, fraction = _Percolate(self.hours)
    if fraction:
      self.minutes += _MINUTES_PER_HOUR * fraction

    self.minutes, fraction = _Percolate(self.minutes)
    if fraction:
      self.seconds += _SECONDS_PER_MINUTE * fraction

    self.seconds, fraction = _Percolate(self.seconds)
    if fraction:
      self.microseconds = int(_MICROSECONDS_PER_SECOND * fraction)

    # Adjust ranges to carry over to larger units.

    self.total_seconds = 0.0

    carry = int(self.microseconds / _MICROSECONDS_PER_SECOND)
    self.microseconds -= int(carry * _MICROSECONDS_PER_SECOND)
    self.total_seconds += self.microseconds / _MICROSECONDS_PER_SECOND
    self.seconds += carry

    carry = int(self.seconds / _SECONDS_PER_MINUTE)
    self.seconds -= carry * _SECONDS_PER_MINUTE
    self.total_seconds += self.seconds
    self.minutes += carry

    carry = int(self.minutes / _MINUTES_PER_HOUR)
    self.minutes -= carry * _MINUTES_PER_HOUR
    self.total_seconds += self.minutes * _SECONDS_PER_MINUTE
    self.hours += carry

    if not self.calendar:
      if self.days or self.months or self.years:
        self.calendar = True
      else:
        self.total_seconds += self.hours * _SECONDS_PER_HOUR
        return

    carry = int(self.hours / _HOURS_PER_DAY)
    self.hours -= carry * _HOURS_PER_DAY
    self.total_seconds += self.hours * _SECONDS_PER_HOUR
    self.days += carry

    # Carry days over to years because of irregular months. Allow the first
    # year to have int(_DAYS_PER_YEAR + 1) days, +1 to allow 366 for leap years.
    if self.days >= int(_DAYS_PER_YEAR + 1):
      self.days -= int(_DAYS_PER_YEAR + 1)
      self.years += 1
    elif self.days <= -int(_DAYS_PER_YEAR + 1):
      self.days += int(_DAYS_PER_YEAR + 1)
      self.years -= 1
    carry = int(self.days / _DAYS_PER_YEAR)
    self.days -= int(carry * _DAYS_PER_YEAR)
    self.total_seconds += self.days * _SECONDS_PER_DAY
    self.years += carry

    carry = int(self.months / _MONTHS_PER_YEAR)
    self.months -= carry * _MONTHS_PER_YEAR
    self.total_seconds += self.months * _SECONDS_PER_MONTH
    self.years += carry
    self.total_seconds += self.years * _SECONDS_PER_YEAR

    self.total_seconds = (round(self.total_seconds, 0) +
                          self.microseconds / _MICROSECONDS_PER_SECOND)

  def Parse(self, string):
    """Parses an ISO 8601 duration from string and returns a Duration object.

    If P is omitted then T is implied (M == minutes).

    Args:
      string: The ISO 8601 duration string to parse.

    Raises:
      ValueError: For invalid duration syntax.

    Returns:
      A Duration object.
    """
    s = string.upper()
    # Signed durations are an extension to the standard. We allow durations to
    # be intialized from signed datetime.timdelta objects, so we must either
    # allow negative durations or make them an error. This supports interval
    # notations like "modify-time / -P7D" for "changes older than 1 week" or
    # "-P7D" for "1 week ago". These cannot be specified in ISO notation.
    t_separator = False  # 'T' separator was seen.
    t_implied = False  # Already saw months or smaller part.
    if s.startswith('-'):
      s = s[1:]
      sign = '-'
    else:
      if s.startswith('+'):
        s = s[1:]
      sign = ''
    if s.startswith('P'):
      s = s[1:]
    else:
      t_implied = True
    amount = [sign]
    for i, c in enumerate(s):
      if c.isdigit():
        amount.append(c)
      elif c == '.' or c == ',':
        amount.append('.')
      elif c == 'T':
        if t_separator:
          raise ValueError("A duration may contain at most one 'T' separator.")
        t_separator = t_implied = True
      elif len(amount) == 1:
        raise ValueError(
            "Duration unit '{}' must be preceded by a number.".format(
                string[i:]))
      else:
        number = float(''.join(amount))
        amount = [sign]
        if c == 'Y':
          self.years += number
        elif c == 'W':
          self.days += number * 7
        elif c == 'D':
          self.days += number
        elif c in ('M', 'U', 'N') and len(s) == i + 2 and s[i + 1] == 'S':
          # ms, us, ns OK if it's the last part.
          if c == 'M':
            n = 1000
          elif c == 'U':
            n = 1000000
          else:
            n = 1000000000
          self.seconds += number / n
          break
        elif c == 'M' and not t_implied:
          t_implied = True
          self.months += number
        else:
          t_implied = True
          if c == 'H':
            self.hours += number
          elif c == 'M':
            self.minutes += number
          elif c == 'S':
            self.seconds += number
          else:
            raise ValueError("Unknown character '{0}' in duration.".format(c))
    if len(amount) > 1 and string.upper().lstrip('+-') != 'P0':
      raise ValueError('Duration must end with time part character.')
    self._Normalize()
    return self

  def Format(self, parts=3, precision=3):
    """Returns an ISO 8601 string representation of the duration.

    The Duration format is: "[-]P[nY][nM][nD][T[nH][nM][n[.m]S]]". The 0
    duration is "P0". Otherwise at least one part will always be displayed.
    Negative durations are prefixed by "-". "T" disambiguates months "P2M" to
    the left of "T" and minutes "PT5M" to the right.

    Args:
      parts: Format at most this many duration parts starting with largest
        non-zero part, 0 for all parts. Zero-valued parts in the count are not
        shown.
      precision: Format the last duration part with precision digits after the
        decimal point. Trailing "0" and "." are always stripped.

    Returns:
      An ISO 8601 string representation of the duration.
    """
    if parts <= 0:
      parts = 7
    total_seconds = abs(self.total_seconds)
    count = 0
    shown = 0
    result = []
    if self.total_seconds < 0:
      result.append('-')
    result.append('P')

    if count < parts and self.years:
      shown = 1
      n = abs(self.years)
      total_seconds -= n * _SECONDS_PER_YEAR
      if count >= parts - 1:
        n += total_seconds / _SECONDS_PER_YEAR
      _FormatNumber(result, n, 'Y', precision=0)
    count += shown

    if count < parts and self.months:
      shown = 1
      n = abs(self.months)
      total_seconds -= n * _SECONDS_PER_MONTH
      if count >= parts - 1:
        n += total_seconds / _SECONDS_PER_MONTH
      _FormatNumber(result, n, 'M', precision=0)
    count += shown

    if count < parts and self.days:
      shown = 1
      n = abs(self.days)
      total_seconds -= n * _SECONDS_PER_DAY
      if count >= parts - 1:
        n += total_seconds / _SECONDS_PER_DAY
      _FormatNumber(result, n, 'D', precision=0)
    result.append('T')
    count += shown

    if count < parts and self.hours:
      shown = 1
      n = abs(self.hours)
      total_seconds -= n * _SECONDS_PER_HOUR
      if count >= parts - 1:
        n += total_seconds / _SECONDS_PER_HOUR
      _FormatNumber(result, n, 'H', precision=0)
    count += shown

    if count < parts and self.minutes:
      shown = 1
      n = abs(self.minutes)
      total_seconds -= n * _SECONDS_PER_MINUTE
      if count >= parts - 1:
        n += total_seconds / _SECONDS_PER_MINUTE
      _FormatNumber(result, n, 'M', precision=0)
    count += shown

    if count < parts and (self.seconds or self.microseconds):
      count += 1
      _FormatNumber(result,
                    (abs(self.seconds) + abs(self.microseconds) /
                     _MICROSECONDS_PER_SECOND),
                    'S',
                    precision=precision)

    # No dangling 'T'.
    if result[-1] == 'T':
      result = result[:-1]
    # 'P0' is the zero duration.
    if result[-1] == 'P':
      result.append('0')
    return ''.join(result)

  def AddTimeDelta(self, delta, calendar=None):
    """Adds a datetime.timdelta to the duration.

    Args:
      delta: A datetime.timedelta object to add.
      calendar: Use duration units larger than hours if True.

    Returns:
      The modified Duration (self).
    """
    if calendar is not None:
      self.calendar = calendar
    self.seconds += delta.total_seconds()
    self._Normalize()
    return self

  def GetRelativeDateTime(self, dt):
    """Returns a copy of the datetime object dt relative to the duration.

    Args:
      dt: The datetime object to add the duration to.

    Returns:
      The a copy of datetime object dt relative to the duration.
    """
    # Add the duration parts to the new dt parts and normalize to valid ranges.

    # All parts are normalized so abs(underflow) and abs(overflow) must be <
    # 2 * the max normalized value.

    microsecond, second, minute, hour, day, month, year = (
        dt.microsecond, dt.second, dt.minute, dt.hour, dt.day, dt.month, dt.year
    )

    microsecond += self.microseconds
    if microsecond >= _MICROSECONDS_PER_SECOND:
      microsecond -= _MICROSECONDS_PER_SECOND
      second += 1
    elif microsecond < 0:
      microsecond += _MICROSECONDS_PER_SECOND
      second -= 1

    second += self.seconds
    if second >= _SECONDS_PER_MINUTE:
      second -= _SECONDS_PER_MINUTE
      minute += 1
    elif second < 0:
      second += _SECONDS_PER_MINUTE
      minute -= 1

    minute += self.minutes
    if minute >= _MINUTES_PER_HOUR:
      minute -= _MINUTES_PER_HOUR
      hour += 1
    elif minute < 0:
      minute += _MINUTES_PER_HOUR
      hour -= 1

    # Non-calendar hours can be > 23 so we normalize here.
    carry = int((hour + self.hours) / _HOURS_PER_DAY)
    hour += self.hours - carry * _HOURS_PER_DAY
    if hour < 0:
      hour += _HOURS_PER_DAY
      carry -= 1
    day += carry

    # Adjust the year before days and months because of irregular months.
    month += self.months
    if month > _MONTHS_PER_YEAR:
      month -= _MONTHS_PER_YEAR
      year += 1
    elif month < 1:
      month += _MONTHS_PER_YEAR
      year -= 1

    year += self.years

    # Normalized days duration range is 0.._DAYS_PER_YEAR+1 because of
    # irregular months and leap years.
    day += self.days
    if day < 1:
      while day < 1:
        month -= 1
        if month < 1:
          month = _MONTHS_PER_YEAR
          year -= 1
        day += DaysInCalendarMonth(year, month)
    else:
      while True:
        days_in_month = DaysInCalendarMonth(year, month)
        if day <= days_in_month:
          break
        day -= days_in_month
        month += 1
        if month > _MONTHS_PER_YEAR:
          month = 1
          year += 1

    return datetime.datetime(
        year, month, day, hour, minute, second, microsecond, dt.tzinfo)
