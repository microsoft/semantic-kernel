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
"""A module for capturing time-related functions.

This makes mocking for time-related functionality easier.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import calendar
import datetime
import re
import time

from six.moves import map  # pylint: disable=redefined-builtin


def CurrentTimeSec():
  """Returns a float of the current time in seconds."""
  return time.time()


def Sleep(duration_sec):
  """Sleeps for the given duration."""
  time.sleep(duration_sec)


def CurrentDatetimeUtc():
  """Returns the current date and time in the UTC timezone."""
  return datetime.datetime.utcnow()


def IsExpired(timestamp_rfc3993_str):
  no_expiration = ''
  if timestamp_rfc3993_str == no_expiration:
    return False
  timestamp_unix = Strptime(timestamp_rfc3993_str)
  if timestamp_unix < CurrentTimeSec():
    return True
  return False


def Strptime(rfc3339_str):
  """Converts an RFC 3339 timestamp to Unix time in seconds since the epoch.

  Args:
    rfc3339_str: a timestamp in RFC 3339 format (yyyy-mm-ddThh:mm:ss.sss
        followed by a time zone, given as Z, +hh:mm, or -hh:mm)

  Returns:
    a number of seconds since January 1, 1970, 00:00:00 UTC

  Raises:
    ValueError: if the timestamp is not in an acceptable format
  """
  match = re.match(r'(\d\d\d\d)-(\d\d)-(\d\d)T'
                   r'(\d\d):(\d\d):(\d\d)(?:\.(\d+))?'
                   r'(?:(Z)|([-+])(\d\d):(\d\d))', rfc3339_str)
  if not match:
    raise ValueError('not a valid timestamp: %r' % rfc3339_str)

  (year, month, day, hour, minute, second, frac_seconds,
   zulu, zone_sign, zone_hours, zone_minutes) = match.groups()

  time_tuple = list(map(int, [year, month, day, hour, minute, second]))

  # Parse the time zone offset.
  if zulu == 'Z':  # explicit
    zone_offset = 0
  else:
    zone_offset = int(zone_hours) * 3600 + int(zone_minutes) * 60
    if zone_sign == '-':
      zone_offset = -zone_offset

  integer_time = calendar.timegm(time_tuple) - zone_offset
  if frac_seconds:
    sig_dig = len(frac_seconds)
    return ((integer_time * (10 ** sig_dig)
             + int(frac_seconds)) * (10 ** -sig_dig))
  else:
    return integer_time


def CalculateExpiration(num_seconds):
  """Takes a number of seconds and returns the expiration time in RFC 3339."""
  if num_seconds is None:
    return None

  utc_now = CurrentDatetimeUtc()
  adjusted = utc_now + datetime.timedelta(0, int(num_seconds))
  formatted_expiration = _FormatDateString(adjusted)
  return formatted_expiration


def _FormatDateString(d):
  return ('%04d-%02d-%02dT%02d:%02d:%02dZ' %
          (d.year, d.month, d.day, d.hour, d.minute, d.second))
