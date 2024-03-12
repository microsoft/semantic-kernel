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

"""dateutil and datetime with portable timezone and ISO 8601 durations.

This module supports round-trip conversions between strings, datetime objects
and timestamps:

         => ParseDateTime =>           => GetTimeStampFromDateTime =>
  string                      datetime                                timestamp
         <= FormatDateTime <=          <= GetDateTimeFromTimeStamp <=

GetTimeZone(str) returns the tzinfo object for a timezone name. It handles
abbreviations, IANA timezone names, and on Windows translates timezone names to
the closest Windows TimeZone registry equivalent.

LocalizeDateTime(datetime, tzinfo) returns a datetime object relative to the
timezone tzinfo.

ISO 8601 duration/period conversions are also supported:

         => ParseDuration =>           => GetDateTimePlusDuration =>
  string                      Duration                               datetime
         <= FormatDuration <=

  timedelta => GetDurationFromTimeDelta => Duration

This module is biased to the local timezone by default. To operate on timezone
naiive datetimes specify tzinfo=None in all calls that have a timezone kwarg.

The datetime and/or dateutil modules should have covered all of this.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import re

from dateutil import parser
from dateutil import tz
from dateutil.tz import _common as tz_common
import enum

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times_data

import six

try:
  from dateutil import tzwin  # pylint: disable=g-import-not-at-top, Windows
except ImportError:
  tzwin = None


class Error(exceptions.Error):
  """Base errors for this module."""


class DateTimeSyntaxError(Error):
  """Date/Time string syntax error."""


class DateTimeValueError(Error):
  """Date/Time part overflow error."""


class DurationSyntaxError(Error):
  """Duration string syntax error."""


class DurationValueError(Error):
  """Duration part overflow error."""


tz_common.PY3 = True  # MONKEYPATCH!!! Fixes a Python 2 standard module bug.

LOCAL = tz.tzlocal()  # The local timezone.
UTC = tz.tzutc()  # The UTC timezone.


_MICROSECOND_PRECISION = 6


def _StrFtime(dt, fmt):
  """Convert strftime exceptions to Datetime Errors."""
  try:
    return dt.strftime(fmt)
  # With dateutil 2.8, strftime() now raises a UnicodeError when it cannot
  # decode the string as 'ascii' on Python 2.
  except (TypeError, UnicodeError) as e:
    if '%Z' not in fmt:
      raise DateTimeValueError(six.text_type(e))
    # Most likely a non-ascii tzname() in python2. Fall back to +-HH:MM.
    return FormatDateTime(dt, fmt.replace('%Z', '%Ez'))
  except (AttributeError, OverflowError, ValueError) as e:
    raise DateTimeValueError(six.text_type(e))


def _StrPtime(string, fmt):
  """Convert strptime exceptions to Datetime Errors."""
  try:
    return datetime.datetime.strptime(string, fmt)
  except (AttributeError, OverflowError, TypeError) as e:
    raise DateTimeValueError(six.text_type(e))
  except ValueError as e:
    raise DateTimeSyntaxError(six.text_type(e))


def FormatDuration(duration, parts=3, precision=3):
  """Returns an ISO 8601 string representation of the duration.

  The Duration format is: "[-]P[nY][nM][nD][T[nH][nM][n[.m]S]]". At least one
  part will always be displayed. The 0 duration is "P0". Negative durations
  are prefixed by "-". "T" disambiguates months "P2M" to the left of "T" and
  minutes "PT5MM" to the right.

  Args:
    duration: An iso_duration.Duration object.
    parts: Format at most this many duration parts starting with largest
      non-zero part.
    precision: Format the last duration part with precision digits after the
      decimal point. Trailing "0" and "." are always stripped.

  Raises:
    DurationValueError: A Duration numeric constant exceeded its range.

  Returns:
    An ISO 8601 string representation of the duration.
  """
  return duration.Format(parts=parts, precision=precision)


def FormatDurationForJson(duration):
  """Returns a string representation of the duration, ending in 's'.

  See the section of
  <https://github.com/google/protobuf/blob/master/src/google/protobuf/duration.proto>
  on JSON formats.

  For example:

    >>> FormatDurationForJson(iso_duration.Duration(seconds=10))
    10s
    >>> FormatDurationForJson(iso_duration.Duration(hours=1))
    3600s
    >>> FormatDurationForJson(iso_duration.Duration(seconds=1, microseconds=5))
    1.000005s

  Args:
    duration: An iso_duration.Duration object.

  Raises:
    DurationValueError: A Duration numeric constant exceeded its range.

  Returns:
    An string representation of the duration.
  """
  # Caution: the default precision for formatting floats is also 6, so when
  # introducing adjustable precision, make sure to account for that.
  num = '{}'.format(round(duration.total_seconds, _MICROSECOND_PRECISION))
  if num.endswith('.0'):
    num = num[:-len('.0')]
  return num + 's'


def FormatDurationListForJson(duration_list):
  """Returns a list of string representations of the durations, ending in 's'.

  It will use FormatDurationForJson to process each duration object in the list.

  Args:
    duration_list: A list of iso_duration.Duration objects to be formatted.

  Raises:
    DurationValueError: A Duration numeric constant exceeded its range.

  Returns:
    A list of strings representation of the duration.
  """
  return [FormatDurationForJson(duration) for duration in duration_list]


def ParseDuration(string, calendar=False, default_suffix=None):
  """Parses a duration string and returns a Duration object.

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

  Args:
    string: The ISO 8601 duration/period string to parse.
    calendar: Use duration units larger than hours if True.
    default_suffix: Use this suffix if string is an unqualified int.

  Raises:
    DurationSyntaxError: Invalid duration syntax.
    DurationValueError: A Duration numeric constant exceeded its range.

  Returns:
    An iso_duration.Duration object for the given ISO 8601 duration/period
    string.
  """
  if default_suffix:
    try:
      seconds = int(string)
      string = '{}{}'.format(seconds, default_suffix)
    except ValueError:
      pass
  try:
    return iso_duration.Duration(calendar=calendar).Parse(string)
  except (AttributeError, OverflowError) as e:
    raise DurationValueError(six.text_type(e))
  except ValueError as e:
    raise DurationSyntaxError(six.text_type(e))


def GetDurationFromTimeDelta(delta, calendar=False):
  """Returns a Duration object converted from a datetime.timedelta object.

  Args:
    delta: The datetime.timedelta object to convert.
    calendar: Use duration units larger than hours if True.

  Returns:
    The iso_duration.Duration object converted from a datetime.timedelta object.
  """
  return iso_duration.Duration(delta=delta, calendar=calendar)


def GetDateTimePlusDuration(dt, duration):
  """Returns a new datetime object representing dt + duration.

  Args:
    dt: The datetime object to add the duration to.
    duration: The iso_duration.Duration object.

  Returns:
    A new datetime object representing dt + duration.
  """
  return duration.GetRelativeDateTime(dt)


def GetTimeZone(name):
  """Returns a datetime.tzinfo object for name.

  Args:
    name: A timezone name string, None for the local timezone.

  Returns:
    A datetime.tzinfo object for name, local timezone if name is unknown.
  """
  if name in ('UTC', 'Z'):
    return UTC
  if name in ('LOCAL', 'L'):
    return LOCAL
  name = times_data.ABBREVIATION_TO_IANA.get(name, name)
  tzinfo = tz.gettz(name)
  if not tzinfo and tzwin:
    name = times_data.IANA_TO_WINDOWS.get(name, name)
    try:
      tzinfo = tzwin.tzwin(name)
    except WindowsError:  # pylint: disable=undefined-variable
      pass
  return tzinfo


def FormatDateTime(dt, fmt=None, tzinfo=None):
  """Returns a string of a datetime object formatted by an extended strftime().

  fmt handles these modifier extensions to the standard formatting chars:

    %Nf   Limit the fractional seconds to N digits. The default is N=6.
    %Ez   Format +/-HHMM offsets as ISO RFC 3339 Z for +0000 otherwise +/-HH:MM.
    %Oz   Format +/-HHMM offsets as ISO RFC 3339 +/-HH:MM.

  NOTE: The standard Python 2 strftime() borks non-ascii time parts. It does
  so by encoding non-ascii names to bytes, presumably under the assumption that
  the return value will be immediately output. This code works around that by
  decoding strftime() values to unicode if necessary and then returning either
  an ASCII or UNICODE string.

  Args:
    dt: The datetime object to be formatted.
    fmt: The strftime(3) format string, None for the RFC 3339 format in the dt
      timezone ('%Y-%m-%dT%H:%M:%S.%3f%Ez').
    tzinfo: Format dt relative to this timezone.

  Raises:
    DateTimeValueError: A DateTime numeric constant exceeded its range.

  Returns:
    A string of a datetime object formatted by an extended strftime().
  """
  if tzinfo:
    dt = LocalizeDateTime(dt, tzinfo)
  if not fmt:
    fmt = '%Y-%m-%dT%H:%M:%S.%3f%Ez'
  extension = re.compile('%[1-9]?[EO]?[fsz]')
  m = extension.search(fmt)
  if not m:
    return encoding.Decode(_StrFtime(dt, fmt))

  # Split the format into standard and extension parts.
  parts = []
  start = 0
  while m:
    match = start + m.start()
    if start < match:
      # Format the preceding standard part.
      parts.append(encoding.Decode(_StrFtime(dt, fmt[start:match])))

    # The extensions only have one modifier char.
    match += 1
    if fmt[match].isdigit():
      n = int(fmt[match])
      match += 1
    else:
      n = None
    if fmt[match] in ('E', 'O'):
      alternate = fmt[match]
      match += 1
    else:
      alternate = None
    spec = fmt[match]
    std_fmt = '%' + spec

    if spec == 'f':
      # Round the fractional part to n digits.
      val = _StrFtime(dt, std_fmt)
      if n and n < len(val):
        # Explicitly avoiding implementation dependent floating point rounding
        # diffs.
        v = int(val[:n])  # The rounded value.
        f = int(val[n])  # The first digit after the rounded value.
        if f >= 5:
          # Round up.
          v += 1
        zero_fill_format = '{{0:0{n}d}}'.format(n=n)
        val = zero_fill_format.format(v)
        if len(val) > n:
          # All 9's rounded up by 1 overflowed width. Keep the unrounded value.
          val = zero_fill_format.format(v - 1)
    elif spec == 's':
      # datetime.strftime('%s') botches tz aware dt!
      val = GetTimeStampFromDateTime(dt)
    elif spec == 'z':
      # Convert the time zone offset to RFC 3339 format.
      val = _StrFtime(dt, std_fmt)
      if alternate:
        if alternate == 'E' and val == '+0000':
          val = 'Z'
        elif len(val) == 5:
          val = val[:3] + ':' + val[3:]
    if val:
      parts.append(encoding.Decode(val))

    start += m.end()
    m = extension.search(fmt[start:])

  # Format the trailing part if any.
  if start < len(fmt):
    parts.append(encoding.Decode(_StrFtime(dt, fmt[start:])))

  # Combine the parts.
  return ''.join(parts)


def FormatDateTimeList(dt_list, fmt=None, tzinfo=None):
  """Returns a list of strings of datetime objects formatted by FormatDateTime.

  It will use FormatDateTime to process each datetime object in the list.

  Args:
    dt_list: A list of datetime objects to be formatted.
    fmt: The strftime(3) format string, None for the RFC 3339 format in the dt
      timezone ('%Y-%m-%dT%H:%M:%S.%3f%Ez').
    tzinfo: Format dt relative to this timezone.

  Raises:
    DateTimeValueError: A DateTime numeric constant exceeded its range.

  Returns:
    A list of strings of a datetime objects formatted by an extended strftime().
  """
  return [FormatDateTime(dt, fmt, tzinfo) for dt in dt_list]


class _TzInfoOrOffsetGetter(object):
  """A helper class for dateutil.parser.parse().

  Attributes:
    _timezone_was_specified: True if the parsed date/time string contained
      an explicit timezone name or offset.
  """

  def __init__(self):
    self._timezone_was_specified = False

  def Get(self, name, offset):
    """Returns the tzinfo for name or offset.

    Used by dateutil.parser.parse() to convert timezone names and offsets.

    Args:
      name: A timezone name or None to use offset. If offset is also None then
        the local tzinfo is returned.
      offset: A signed UTC timezone offset in seconds.

    Returns:
      The tzinfo for name or offset or the local tzinfo if both are None.
    """
    if name or offset:
      self._timezone_was_specified = True
    if not name and offset is not None:
      return offset
    return GetTimeZone(name)

  @property
  def timezone_was_specified(self):
    """True if the parsed date/time string contained an explicit timezone."""
    return self._timezone_was_specified


def _SplitTzFromDate(string):
  """Returns (prefix,tzinfo) if string has a trailing tz, else (None,None)."""
  try:
    match = re.match(r'(.*[\d\s])([^\d\s]+)$', string)
  except TypeError:
    return None, None
  if match:
    tzinfo = GetTimeZone(match.group(2))
    if tzinfo:
      return match.group(1), tzinfo
  return None, None


def ParseDateTime(string, fmt=None, tzinfo=LOCAL):
  """Parses a date/time string and returns a datetime.datetime object.

  Args:
    string: The date/time string to parse. This can be a parser.parse()
      date/time or an ISO 8601 duration after Now(tzinfo) or before if prefixed
      by '-'.
    fmt: The input must satisfy this strptime(3) format string.
    tzinfo: A default timezone tzinfo object to use if string has no timezone.

  Raises:
    DateTimeSyntaxError: Invalid date/time/duration syntax.
    DateTimeValueError: A date/time numeric constant exceeds its range.

  Returns:
    A datetime.datetime object for the given date/time string.
  """
  # Check explicit format first.
  if fmt:
    dt = _StrPtime(string, fmt)
    if tzinfo and not dt.tzinfo:
      dt = dt.replace(tzinfo=tzinfo)
    return dt

  # Use tzgetter to determine if string contains an explicit timezone name or
  # offset.
  defaults = GetDateTimeDefaults(tzinfo=tzinfo)
  tzgetter = _TzInfoOrOffsetGetter()

  exc = None
  try:
    dt = parser.parse(string, tzinfos=tzgetter.Get, default=defaults)
    if tzinfo and not tzgetter.timezone_was_specified:
      # The string had no timezone name or offset => localize dt to tzinfo.
      dt = parser.parse(string, tzinfos=None, default=defaults)
      dt = dt.replace(tzinfo=tzinfo)
    return dt
  except OverflowError as e:
    exc = exceptions.ExceptionContext(DateTimeValueError(six.text_type(e)))
  except (AttributeError, ValueError, TypeError) as e:
    exc = exceptions.ExceptionContext(DateTimeSyntaxError(six.text_type(e)))
    if not tzgetter.timezone_was_specified:
      # Good ole parser.parse() has a tzinfos kwarg that it sometimes ignores.
      # Compensate here when the string ends with a tz.
      prefix, explicit_tzinfo = _SplitTzFromDate(string)
      if explicit_tzinfo:
        try:
          dt = parser.parse(prefix, default=defaults)
        except OverflowError as e:
          exc = exceptions.ExceptionContext(
              DateTimeValueError(six.text_type(e)))
        except (AttributeError, ValueError, TypeError) as e:
          exc = exceptions.ExceptionContext(
              DateTimeSyntaxError(six.text_type(e)))
        else:
          return dt.replace(tzinfo=explicit_tzinfo)

  try:
    # Check if it's an iso_duration string.
    return ParseDuration(string).GetRelativeDateTime(Now(tzinfo=tzinfo))
  except Error:
    # Not a duration - reraise the datetime parse error.
    exc.Reraise()


def GetDateTimeFromTimeStamp(timestamp, tzinfo=LOCAL):
  """Returns the datetime object for a UNIX timestamp.

  Args:
    timestamp: A UNIX timestamp in int or float seconds since the epoch
      (1970-01-01T00:00:00.000000Z).
    tzinfo: A tzinfo object for the timestamp timezone, None for naive.

  Raises:
    DateTimeValueError: A date/time numeric constant exceeds its range.

  Returns:
    The datetime object for a UNIX timestamp.
  """
  try:
    return datetime.datetime.fromtimestamp(timestamp, tzinfo)
  # From python 3.3, it raises OverflowError instead of ValueError if the
  # timestamp is out of the range of values supported by C localtime().
  # It raises OSError instead of ValueError on localtime() failure.
  except (ValueError, OSError, OverflowError) as e:
    raise DateTimeValueError(six.text_type(e))


def GetTimeStampFromDateTime(dt, tzinfo=LOCAL):
  """Returns the float UNIX timestamp (with microseconds) for dt.

  Args:
    dt: The datetime object to convert from.
    tzinfo: Use this tzinfo if dt is naiive.

  Returns:
    The float UNIX timestamp (with microseconds) for dt.
  """
  if not dt.tzinfo and tzinfo:
    dt = dt.replace(tzinfo=tzinfo)
  delta = dt - datetime.datetime.fromtimestamp(0, UTC)
  return delta.total_seconds()


def LocalizeDateTime(dt, tzinfo=LOCAL):
  """Returns a datetime object localized to the timezone tzinfo.

  Args:
    dt: The datetime object to localize. It can be timezone naive or aware.
    tzinfo: The timezone of the localized dt. If None then the result is naive,
      otherwise it is aware.

  Returns:
    A datetime object localized to the timezone tzinfo.
  """
  ts = GetTimeStampFromDateTime(dt, tzinfo=tzinfo)
  return GetDateTimeFromTimeStamp(ts, tzinfo=tzinfo)


def Now(tzinfo=LOCAL):
  """Returns a timezone aware datetime object for the current time.

  Args:
    tzinfo: The timezone of the localized dt. If None then the result is naive,
      otherwise it is aware.

  Returns:
    A datetime object localized to the timezone tzinfo.
  """
  return datetime.datetime.now(tzinfo)


def GetDateTimeDefaults(tzinfo=LOCAL):
  """Returns a datetime object of default values for parsing partial datetimes.

  The year, month and day default to today (right now), and the hour, minute,
  second and fractional second values default to 0.

  Args:
    tzinfo: The timezone of the localized dt. If None then the result is naive,
      otherwise it is aware.

  Returns:
    A datetime object of default values for parsing partial datetimes.
  """
  return datetime.datetime.combine(Now(tzinfo=tzinfo).date(),
                                   datetime.time.min)


def TzOffset(offset, name=None):
  """Returns a tzinfo for offset minutes east of UTC with optional name.

  Args:
    offset: The minutes east of UTC. Minutes west are negative.
    name: The optional timezone name. NOTE: no dst name.

  Returns:
    A tzinfo for offset seconds east of UTC.
  """
  return tz.tzoffset(name, offset * 60)  # tz.tzoffset needs seconds east of UTC


class Weekday(enum.Enum):
  """Represents a day of the week."""

  MONDAY = 0
  TUESDAY = 1
  WEDNESDAY = 2
  THURSDAY = 3
  FRIDAY = 4
  SATURDAY = 5
  SUNDAY = 6

  @classmethod
  def Get(cls, day):
    day = day.upper()
    value = getattr(cls, day, None)
    if not value:
      raise KeyError('[{}] is not a valid Weekday'.format(day))
    return value


def GetWeekdayInTimezone(dt, weekday, tzinfo=LOCAL):
  """Returns the Weekday for dt in the timezone specified by tzinfo.

  Args:
    dt: The datetime object that represents the time on weekday.
    weekday: The day of the week specified as a Weekday enum.
    tzinfo: The timezone in which to get the new day of the week in.

  Returns:
    A Weekday that corresponds to dt and weekday pair localized to the timezone
    specified by dt.
  """
  localized_dt = LocalizeDateTime(dt, tzinfo)
  localized_weekday_offset = dt.weekday() - localized_dt.weekday()
  localized_weekday_index = (weekday.value - localized_weekday_offset) % 7
  return Weekday(localized_weekday_index)
