# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Shared utility methods that calculate, convert, and simplify units."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import math
import re

import six

if six.PY3:
  long = int

# Binary exponentiation strings.
_EXP_STRINGS = [
    (0, 'B', 'bit'),
    (10, 'KiB', 'Kibit', 'K'),
    (20, 'MiB', 'Mibit', 'M'),
    (30, 'GiB', 'Gibit', 'G'),
    (40, 'TiB', 'Tibit', 'T'),
    (50, 'PiB', 'Pibit', 'P'),
    (60, 'EiB', 'Eibit', 'E'),
]

_EXP_TEN_STRING = [
    (3, 'k'),
    (6, 'm'),
    (9, 'b'),
    (12, 't'),
    (15, 'q'),
]


# Define this method before constants below, as some call it to init themselves.
def _GenerateSuffixRegex():
  """Creates a suffix regex for human-readable byte counts."""
  human_bytes_re = r'(?P<num>\d*\.\d+|\d+)\s*(?P<suffix>%s)?'
  suffixes = []
  suffix_to_si = {}
  for i, si in enumerate(_EXP_STRINGS):
    si_suffixes = [s.lower() for s in list(si)[1:]]
    for suffix in si_suffixes:
      suffix_to_si[suffix] = i
    suffixes.extend(si_suffixes)
  human_bytes_re %= '|'.join(suffixes)
  matcher = re.compile(human_bytes_re)
  return suffix_to_si, matcher


# TODO: These should include the unit in the name, e.g. BYTES_PER_KIB, or
# BYTES_IN_ONE_KIB.
ONE_KIB = 1024
ONE_MIB = 1024 * ONE_KIB
ONE_GIB = 1024 * ONE_MIB

# TODO: Remove 2, 8, 10 MIB vars.
TWO_MIB = 2 * ONE_MIB
EIGHT_MIB = 8 * ONE_MIB
TEN_MIB = 10 * ONE_MIB

SECONDS_PER_DAY = long(60 * 60 * 24)
SUFFIX_TO_SI, MATCH_HUMAN_BYTES = _GenerateSuffixRegex()


def _RoundToNearestExponent(num):
  i = 0
  while i + 1 < len(_EXP_STRINGS) and num >= (2**_EXP_STRINGS[i + 1][0]):
    i += 1
  return i, round(float(num) / 2.0**_EXP_STRINGS[i][0], 2)


def CalculateThroughput(total_bytes_transferred, total_elapsed_time):
  """Calculates throughput and checks for a small total_elapsed_time.

  Args:
    total_bytes_transferred: Total bytes transferred in a period of time.
    total_elapsed_time: The amount of time elapsed in seconds.

  Returns:
    The throughput as a float.
  """
  if total_elapsed_time < 0.01:
    total_elapsed_time = 0.01
  return float(total_bytes_transferred) / float(total_elapsed_time)


def DecimalShort(num):
  """Creates a shorter string version for a given number of objects.

  Args:
    num: The number of objects to be shortened.
  Returns:
    shortened string version for this number. It takes the largest
    scale (thousand, million or billion) smaller than the number and divides it
    by that scale, indicated by a suffix with one decimal place. This will thus
    create a string of at most 6 characters, assuming num < 10^18.
    Example: 123456789 => 123.4m
  """
  for divisor_exp, suffix in reversed(_EXP_TEN_STRING):
    if num >= 10**divisor_exp:
      quotient = '%.1lf' % (float(num) / 10**divisor_exp)
      return quotient + suffix
  return str(num)


def DivideAndCeil(dividend, divisor):
  """Returns ceil(dividend / divisor).

  Takes care to avoid the pitfalls of floating point arithmetic that could
  otherwise yield the wrong result for large numbers.

  Args:
    dividend: Dividend for the operation.
    divisor: Divisor for the operation.

  Returns:
    Quotient.
  """
  quotient = dividend // divisor
  if (dividend % divisor) != 0:
    quotient += 1
  return quotient


def HumanReadableToBytes(human_string):
  """Tries to convert a human-readable string to a number of bytes.

  Args:
    human_string: A string supplied by user, e.g. '1M', '3 GiB'.
  Returns:
    An integer containing the number of bytes.
  Raises:
    ValueError: on an invalid string.
  """
  human_string = human_string.lower()
  m = MATCH_HUMAN_BYTES.match(human_string)
  if m:
    num = float(m.group('num'))
    if m.group('suffix'):
      power = _EXP_STRINGS[SUFFIX_TO_SI[m.group('suffix')]][0]
      num *= (2.0**power)
    num = int(round(num))
    return num
  raise ValueError('Invalid byte string specified: %s' % human_string)


def HumanReadableWithDecimalPlaces(number, decimal_places=1):
  """Creates a human readable format for bytes with fixed decimal places.

  Args:
    number: The number of bytes.
    decimal_places: The number of decimal places.
  Returns:
    String representing a readable format for number with decimal_places
     decimal places.
  """
  number_format = MakeHumanReadable(number).split()
  num = str(int(round(10**decimal_places * float(number_format[0]))))
  if num == '0':
    number_format[0] = ('0' +
                        (('.' +
                          ('0' * decimal_places)) if decimal_places else ''))
  else:
    num_length = len(num)
    if decimal_places:
      num = (num[:num_length - decimal_places] + '.' +
             num[num_length - decimal_places:])
    number_format[0] = num
  return ' '.join(number_format)


def MakeBitsHumanReadable(num):
  """Generates human readable string for a number of bits.

  Args:
    num: The number, in bits.

  Returns:
    A string form of the number using bit size abbreviations (kbit, Mbit, etc.)
  """
  i, rounded_val = _RoundToNearestExponent(num)
  return '%g %s' % (rounded_val, _EXP_STRINGS[i][2])


def MakeHumanReadable(num):
  """Generates human readable string for a number of bytes.

  Args:
    num: The number, in bytes.

  Returns:
    A string form of the number using size abbreviations (KiB, MiB, etc.).
  """
  i, rounded_val = _RoundToNearestExponent(num)
  return '%g %s' % (rounded_val, _EXP_STRINGS[i][1])


def Percentile(values, percent, key=lambda x: x):
  """Find the percentile of a list of values.

  Taken from: http://code.activestate.com/recipes/511478/

  Args:
    values: a list of numeric values. Note that the values MUST BE already
            sorted.
    percent: a float value from 0.0 to 1.0.
    key: optional key function to compute value from each element of the list
         of values.

  Returns:
    The percentile of the values.
  """
  if not values:
    return None
  k = (len(values) - 1) * percent
  f = math.floor(k)
  c = math.ceil(k)
  if f == c:
    return key(values[int(k)])
  d0 = key(values[int(f)]) * (c - k)
  d1 = key(values[int(c)]) * (k - f)
  return d0 + d1


def PrettyTime(remaining_time):
  """Creates a standard version for a given remaining time in seconds.

  Created over using strftime because strftime seems to be
    more suitable for a datetime object, rather than just a number of
    seconds remaining.
  Args:
    remaining_time: The number of seconds remaining as a float, or a
      string/None value indicating time was not correctly calculated.
  Returns:
    if remaining_time is a valid float, %H:%M:%D time remaining format with
    the nearest integer from remaining_time (%H might be higher than 23).
    Else, it returns the same message it received.
  """
  remaining_time = int(round(remaining_time))
  hours = remaining_time // 3600
  if hours >= 100:
    # Too large to display with precision of minutes and seconds.
    # If over 1000, saying 999+ hours should be enough.
    return '%d+ hrs' % min(hours, 999)
  remaining_time -= (3600 * hours)
  minutes = remaining_time // 60
  remaining_time -= (60 * minutes)
  seconds = remaining_time
  return (str('%02d' % hours) + ':' + str('%02d' % minutes) + ':' +
          str('%02d' % seconds))
