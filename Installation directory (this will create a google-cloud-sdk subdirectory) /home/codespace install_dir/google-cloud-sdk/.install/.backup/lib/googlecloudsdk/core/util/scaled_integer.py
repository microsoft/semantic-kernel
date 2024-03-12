# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Scaled integer ISO/IEC unit prefix parsing and formatting."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

import six


_INTEGER_SUFFIX_TYPE_PATTERN = r"""
    ^                           # Beginning of input marker.
    (?P<amount>\d+)             # Amount.
    ((?P<suffix>[-/a-zA-Z]+))?  # Optional scale and type abbr.
    $                           # End of input marker.
"""

_ISO_IEC_UNITS = {
    '': 1,
    'k': 1000 ** 1,
    'M': 1000 ** 2,
    'G': 1000 ** 3,
    'T': 1000 ** 4,
    'P': 1000 ** 5,
    'ki': 1 << 10,
    'Mi': 1 << 20,
    'Gi': 1 << 30,
    'Ti': 1 << 40,
    'Pi': 1 << 50,
}

_BINARY_UNITS = {
    '': 1,
    'k': 1 << 10,
    'M': 1 << 20,
    'G': 1 << 30,
    'T': 1 << 40,
    'P': 1 << 50,
    'ki': 1 << 10,
    'Mi': 1 << 20,
    'Gi': 1 << 30,
    'Ti': 1 << 40,
    'Pi': 1 << 50,
}


def _UnitsByMagnitude(units, type_abbr):
  """Returns a list of the units in scales sorted by magnitude."""
  scale_items = sorted(six.iteritems(units),
                       key=lambda value: (value[1], value[0]))
  return [key + type_abbr for key, _ in scale_items if key]


def DeleteTypeAbbr(suffix, type_abbr='B'):
  """Returns suffix with trailing type abbreviation deleted."""
  if not suffix:
    return suffix
  s = suffix.upper()
  i = len(s)
  for c in reversed(type_abbr.upper()):
    if not i:
      break
    if s[i - 1] == c:
      i -= 1
  return suffix[:i]


def GetUnitSize(suffix, type_abbr='B', default_unit='', units=None):
  """Returns the size per unit for binary suffix string.

  Args:
    suffix: str, A case insensitive unit suffix string with optional type
      abbreviation.
    type_abbr: str, The optional case insensitive type abbreviation following
      the suffix.
    default_unit: The default unit prefix name.
    units: {str: int} map of unit prefix => size.

  Raises:
    ValueError: on unknown units of type suffix.

  Returns:
    The binary size per unit for a unit+type_abbr suffix.
  """
  prefix = DeleteTypeAbbr(suffix, type_abbr)
  if not prefix:
    unit = default_unit
    if not unit:
      unit = ''
    elif unit.startswith('K'):
      unit = 'k' + unit[1:]
  else:
    unit = prefix[0].upper()
    if unit == 'K':
      unit = 'k'
    if len(prefix) > 1 and prefix[1] in ('i', 'I'):
      unit += 'i'
      prefix = prefix[2:]
    else:
      prefix = prefix[1:]
    if prefix:
      raise ValueError('Invalid type [{}] in [{}], expected [{}] or nothing.'
                       .format(prefix, suffix, type_abbr))

  size = (units or _ISO_IEC_UNITS).get(unit)
  if not size:
    raise ValueError('Invalid suffix [{}] in [{}], expected one of [{}].'
                     .format(unit, suffix,
                             ','.join(_UnitsByMagnitude(units, ''))))
  return size


def GetBinaryUnitSize(suffix, type_abbr='B', default_unit=''):
  """Returns the binary size per unit for binary suffix string.

  Args:
    suffix: str, A case insensitive unit suffix string with optional type
      abbreviation.
    type_abbr: str, The optional case insensitive type abbreviation following
      the suffix.
    default_unit: The default unit prefix name.

  Raises:
    ValueError for unknown units.

  Returns:
    The binary size per unit for a unit+type_abbr suffix.
  """
  return GetUnitSize(suffix, type_abbr=type_abbr, default_unit=default_unit,
                     units=_BINARY_UNITS)


def _ParseScaledInteger(units, string, default_unit='', type_abbr='B'):
  """Parses and returns a units scaled integer from string.

  ISO/IEC/SI rules relaxed to ignore case in unit and type names/abbreviations.

  Args:
    units: {str: int} map of unit prefix => size.
    string: The string to parse the integer + units.
    default_unit: The default unit prefix name.
    type_abbr: The optional type abbreviation suffix, validated but otherwise
      ignored.

  Raises:
    ValueError: on invalid input.

  Returns:
    The scaled integer value.
  """

  match = re.match(_INTEGER_SUFFIX_TYPE_PATTERN, string, re.VERBOSE)
  if not match:
    optional_type_abbr = '[' + type_abbr + ']' if type_abbr else ''
    raise ValueError(
        '[{}] must the form INTEGER[UNIT]{} where units may be one of [{}].'
        .format(string, optional_type_abbr,
                ','.join(_UnitsByMagnitude(units, type_abbr))))
  suffix = match.group('suffix') or ''
  size = GetUnitSize(
      suffix, type_abbr=type_abbr, default_unit=default_unit, units=units)
  amount = int(match.group('amount'))
  return amount * size


def ParseInteger(string, default_unit='', type_abbr='B'):
  """Parses and returns an ISO Decimal/Binary scaled integer from string.

  ISO/IEC prefixes: 1k == 1000, 1ki == 1024.

  Args:
    string: The string to parse the integer + units.
    default_unit: The default unit prefix name.
    type_abbr: The optional type abbreviation suffix, validated but otherwise
      ignored.

  Returns:
    The scaled integer value.
  """
  return _ParseScaledInteger(
      _ISO_IEC_UNITS, string, default_unit=default_unit, type_abbr=type_abbr)


def FormatInteger(value, type_abbr='B'):
  """Returns a pretty string representation of an ISO Decimal value.

  Args:
    value: A scaled integer value.
    type_abbr: The optional type abbreviation suffix, validated but otherwise
      ignored.

  Returns:
    The formatted scaled integer value.
  """
  for suffix, size in reversed(sorted(six.iteritems(_ISO_IEC_UNITS),
                                      key=lambda value: (value[1], value[0]))):
    if size <= value and not value % size:
      return '{}{}{}'.format(value // size, suffix, type_abbr)
  return '{}{}'.format(value, type_abbr)


def FormatBinaryNumber(value, type_abbr='B', decimal_places=-1):
  """Returns a pretty string of a binary-base number with decimal precision.

  Args:
    value (float|int): A number.
    type_abbr (str): The optional type abbreviation suffix, validated but
      otherwise ignored.
    decimal_places (int): Number of decimal places to include of quotient for
      unit conversion. Does not allow rounding if -1. Will suffer float
      inaccuracy at high values.

  Returns:
    A formatted scaled value string.
  """
  for suffix, size in reversed(sorted(six.iteritems(_BINARY_UNITS),
                                      key=lambda value: (value[1], value[0]))):
    if size <= value:
      if decimal_places == -1 and value % size:
        # Do not allow rounding if round_to_decimal_places is -1.
        continue
      scaled_value = value / size
      # format() cannot interpet negative precisions, so make the minimum 0.
      precision = max(decimal_places, 0)
      return '{:.{precision}f}{}{}'.format(
          scaled_value, suffix, type_abbr, precision=precision)
  return '{}{}'.format(value, type_abbr)


def ParseBinaryInteger(string, default_unit='', type_abbr='B'):
  """Parses and returns a Binary scaled integer from string.

  All ISO/IEC prefixes are powers of 2: 1k == 1ki == 1024. This is a
  concession to the inconsistent mix of binary/decimal unit measures for
  memory capacity, disk capacity, cpu speed. Ideally ParseInteger should be
  used.

  Args:
    string: The string to parse the integer + units.
    default_unit: The default unit prefix name.
    type_abbr: The optional type abbreviation suffix, validated but otherwise
      ignored.

  Returns:
    The scaled integer value.
  """
  return _ParseScaledInteger(
      _BINARY_UNITS, string, default_unit=default_unit, type_abbr=type_abbr)
