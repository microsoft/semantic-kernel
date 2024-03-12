# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""A module that provides parsing utilities for argparse.

For details of how argparse argument pasers work, see:

http://docs.python.org/dev/library/argparse.html#type

Example usage:

import argparse
import arg_parsers

parser = argparse.ArgumentParser()

parser.add_argument(
'--metadata',
type=arg_parsers.ArgDict())
parser.add_argument(
'--delay',
default='5s',
type=arg_parsers.Duration(lower_bound='1s', upper_bound='10s')
parser.add_argument(
'--disk-size',
default='10GB',
type=arg_parsers.BinarySize(lower_bound='1GB', upper_bound='10TB')

res = parser.parse_args(
'--names --metadata x=y,a=b,c=d --delay 1s --disk-size 10gb'.split())

assert res.metadata == {'a': 'b', 'c': 'd', 'x': 'y'}
assert res.delay == 1
assert res.disk_size == 10737418240

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import collections
import copy
import decimal
import json
import re

from dateutil import tz

from googlecloudsdk.calliope import arg_parsers_usage_text as usage_text
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times

import six
from six.moves import zip  # pylint: disable=redefined-builtin

__all__ = ['Duration', 'BinarySize']


class Error(Exception):
  """Exceptions that are defined by this module."""


class ArgumentTypeError(Error, argparse.ArgumentTypeError):
  """Exceptions for parsers that are used as argparse types."""


class ArgumentParsingError(Error, argparse.ArgumentError):
  """Raised when there is a problem with user input.

  argparse.ArgumentError takes both the action and a message as constructor
  parameters.
  """


class InvalidTypeError(Error):
  """Error for when contributor provides incorrect type arguments."""


def _GenerateErrorMessage(error, user_input=None, error_idx=None):
  """Constructs an error message for an exception.

  Args:
    error: str, The error message that should be displayed. This message should
      not end with any punctuation--the full error message is constructed by
      appending more information to error.
    user_input: str, The user input that caused the error.
    error_idx: int, The index at which the error occurred. If None, the index
      will not be printed in the error message.

  Returns:
    str: The message to use for the exception.
  """
  if user_input is None:
    return error
  elif not user_input:  # Is input empty?
    return error + '; received empty string'
  elif error_idx is None:
    return error + '; received: ' + user_input
  return ('{error_message} at index {error_idx}: {user_input}'.format(
      error_message=error, user_input=user_input, error_idx=error_idx))


def InvalidInputErrorMessage(unit_scales):
  """Constructs an error message for exception thrown invalid input.

  Args:
    unit_scales: list, A list of strings with units that will be recommended to
      user.

  Returns:
    str: The message to use for the exception.
  """
  return ('given value must be of the form DECIMAL[UNITS] where units can '
          'be one of {0} and value must be a whole number of Bytes'.format(
              ', '.join(unit_scales)))


_VALUE_PATTERN = r"""
    ^                           # Beginning of input marker.
    (?P<amount>\d+\.?\d*)       # Amount.
    ((?P<suffix>[-/a-zA-Z]+))?  # Optional scale and type abbr.
    $                           # End of input marker.
"""

_RANGE_PATTERN = r'^(?P<start>[0-9]+)(-(?P<end>[0-9]+))?$'

_SECOND = 1
_MINUTE = 60 * _SECOND
_HOUR = 60 * _MINUTE
_DAY = 24 * _HOUR

# The units are adopted from sleep(1):
#   http://linux.die.net/man/1/sleep
_DURATION_SCALES = {
    's': _SECOND,
    'm': _MINUTE,
    'h': _HOUR,
    'd': _DAY,
}

_BINARY_SIZE_SCALES = {
    '': 1,
    'K': 1 << 10,
    'M': 1 << 20,
    'G': 1 << 30,
    'T': 1 << 40,
    'P': 1 << 50,
    'Ki': 1 << 10,
    'Mi': 1 << 20,
    'Gi': 1 << 30,
    'Ti': 1 << 40,
    'Pi': 1 << 50,
}

_UnitToLowerUnitDict = {
    'PiB': 'TiB',
    'PB': 'TiB',
    'TiB': 'GiB',
    'TB': 'GiB',
    'GiB': 'MiB',
    'GB': 'MiB',
    'MiB': 'KiB',
    'MB': 'KiB',
    'KiB': 'B',
    'KB': 'B',
}


def ConvertToWholeNumber(amount, unit):
  """Convert input value and units to a whole number of a lower unit.

  Args:
    amount: str, a number, for example '3.25'
    unit: str, a binary prefix, for example 'GB' or 'GiB'

  Returns:
    (decimal.Decimal(), str), a tuple of number and suffix, converted such that
    the number returned is an integer, or the value, in Bytes, of the amount
    input. For example (23, 'MiB'). Note that IEC binary prefixes are always
    assumed and returned.
  """
  return_amount = decimal.Decimal(amount)
  return_unit = unit
  while (not float(return_amount).is_integer() and return_unit and
         return_unit in _UnitToLowerUnitDict):
    return_amount, return_unit = (
        # The units are binary so 1KB = 1024B
        return_amount * 1024,
        _UnitToLowerUnitDict[return_unit])
  return return_amount, return_unit


def GetMultiCompleter(individual_completer):
  """Create a completer to handle completion for comma separated lists.

  Args:
    individual_completer: A function that completes an individual element.

  Returns:
    A function that completes the last element of the list.
  """

  def MultiCompleter(prefix, parsed_args, **kwargs):
    start = ''
    lst = prefix.rsplit(',', 1)
    if len(lst) > 1:
      start = lst[0] + ','
      prefix = lst[1]
    matches = individual_completer(prefix, parsed_args, **kwargs)
    return [start + match for match in matches]

  return MultiCompleter


def _DeleteTypeAbbr(suffix, type_abbr='B'):
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


def GetBinarySizePerUnit(suffix, type_abbr='B'):
  """Returns the binary size per unit for binary suffix string.

  Args:
    suffix: str, A case insensitive unit suffix string with optional type
      abbreviation.
    type_abbr: str, The optional case insensitive type abbreviation following
      the suffix.

  Raises:
    ValueError for unknown units.

  Returns:
    The binary size per unit for a unit+type_abbr suffix.
  """
  unit = _DeleteTypeAbbr(suffix.upper(), type_abbr)
  return _BINARY_SIZE_SCALES.get(unit)


def _ValueParser(scales,
                 default_unit,
                 lower_bound=None,
                 upper_bound=None,
                 strict_case=True,
                 type_abbr='B',
                 suggested_binary_size_scales=None):
  """A helper that returns a function that can parse values with units.

  Casing for all units matters.

  Args:
    scales: {str: int}, A dictionary mapping units to their magnitudes in
      relation to the lowest magnitude unit in the dict.
    default_unit: str, The default unit to use if the user's input is missing
      unit.
    lower_bound: str, An inclusive lower bound.
    upper_bound: str, An inclusive upper bound.
    strict_case: bool, whether to be strict on case-checking
    type_abbr: str, the type suffix abbreviation, e.g., B for bytes, b/s for
      bits/sec.
    suggested_binary_size_scales: list, A list of strings with units that will
      be recommended to user.

  Returns:
    A function that can parse values.
  """

  def UnitsByMagnitude(suggested_binary_size_scales=None):
    """Returns a list of the units in scales sorted by magnitude."""
    scale_items = sorted(
        six.iteritems(scales), key=lambda value: (value[1], value[0]))
    if suggested_binary_size_scales is None:
      return [key + type_abbr for key, _ in scale_items]
    return [
        key + type_abbr
        for key, _ in scale_items
        if key + type_abbr in suggested_binary_size_scales
    ]

  def Parse(value):
    """Parses value that can contain a unit and type abbreviation."""
    match = re.match(_VALUE_PATTERN, value, re.VERBOSE)
    if not match:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              InvalidInputErrorMessage(
                  UnitsByMagnitude(suggested_binary_size_scales)),
              user_input=value))
    suffix = match.group('suffix') or ''
    amount, suffix = ConvertToWholeNumber(match.group('amount'), suffix)
    if not float(amount).is_integer():
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              InvalidInputErrorMessage(
                  UnitsByMagnitude(suggested_binary_size_scales)),
              user_input=value))
    amount = int(amount)
    unit = _DeleteTypeAbbr(suffix, type_abbr)
    if strict_case:
      unit_case = unit
      default_unit_case = _DeleteTypeAbbr(default_unit, type_abbr)
      scales_case = scales
    else:
      unit_case = unit.upper()
      default_unit_case = _DeleteTypeAbbr(default_unit.upper(), type_abbr)
      scales_case = dict([(k.upper(), v) for k, v in scales.items()])

    if not unit and unit == suffix:
      return amount * scales_case[default_unit_case]
    elif unit_case in scales_case:
      return amount * scales_case[unit_case]
    else:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'unit must be one of {0}'.format(', '.join(UnitsByMagnitude())),
              user_input=unit))

  if lower_bound is None:
    parsed_lower_bound = None
  else:
    parsed_lower_bound = Parse(lower_bound)

  if upper_bound is None:
    parsed_upper_bound = None
  else:
    parsed_upper_bound = Parse(upper_bound)

  def ParseWithBoundsChecking(value):
    """Same as Parse except bound checking is performed."""
    if value is None:
      return None
    else:
      parsed_value = Parse(value)
      if parsed_lower_bound is not None and parsed_value < parsed_lower_bound:
        raise ArgumentTypeError(
            _GenerateErrorMessage(
                'value must be greater than or equal to {0}'.format(
                    lower_bound),
                user_input=value))
      elif parsed_upper_bound is not None and parsed_value > parsed_upper_bound:
        raise ArgumentTypeError(
            _GenerateErrorMessage(
                'value must be less than or equal to {0}'.format(upper_bound),
                user_input=value))
      else:
        return parsed_value

  return ParseWithBoundsChecking


def RegexpValidator(pattern, description):
  """Returns a function that validates a string against a regular expression.

  For example:

  >>> alphanumeric_type = RegexpValidator(
  ...   r'[a-zA-Z0-9]+',
  ...   'must contain one or more alphanumeric characters')
  >>> parser.add_argument('--foo', type=alphanumeric_type)
  >>> parser.parse_args(['--foo', '?'])
  >>> # SystemExit raised and the error "error: argument foo: Bad value [?]:
  >>> # must contain one or more alphanumeric characters" is displayed

  Args:
    pattern: str, the pattern to compile into a regular expression to check
    description: an error message to show if the argument doesn't match

  Returns:
    function: str -> str, usable as an argparse type
  """

  def Parse(value):
    if not re.match(pattern + '$', value):
      raise ArgumentTypeError('Bad value [{0}]: {1}'.format(value, description))
    return value

  return Parse


def CustomFunctionValidator(fn, description, parser=None):
  """Returns a function that validates the input by running it through fn.

  For example:

  >>> def isEven(val):
  ...   return val % 2 == 0
  >>> even_number_parser = arg_parsers.CustomFunctionValidator(
        isEven, 'This is not even!', parser=arg_parsers.BoundedInt(0))
  >>> parser.add_argument('--foo', type=even_number_parser)
  >>> parser.parse_args(['--foo', '3'])
  >>> # SystemExit raised and the error "error: argument foo: Bad value [3]:
  >>> # This is not even!" is displayed

  Args:
    fn: str -> boolean
    description: an error message to show if boolean function returns False
    parser: an arg_parser that is applied to to value before validation. The
      value is also returned by this parser.

  Returns:
    function: str -> str, usable as an argparse type
  """

  def Parse(value):
    """Validates and returns a custom object from an argument string value."""
    try:
      parsed_value = parser(value) if parser else value
    except ArgumentTypeError:
      pass
    else:
      if fn(parsed_value):
        return parsed_value
    encoded_value = console_attr.SafeText(value)
    formatted_err = 'Bad value [{0}]: {1}'.format(encoded_value, description)
    raise ArgumentTypeError(formatted_err)

  return Parse


def Duration(default_unit='s',
             lower_bound='0',
             upper_bound=None,
             parsed_unit='s'):
  """Returns a function that can parse time durations.

  See times.ParseDuration() for details. If the unit is omitted, seconds is
  assumed. The parsed unit is assumed to be seconds, but can be specified as
  ms or us.
  For example:

    parser = Duration()
    assert parser('10s') == 10
    parser = Duration(parsed_unit='ms')
    assert parser('10s') == 10000
    parser = Duration(parsed_unit='us')
    assert parser('10s') == 10000000

  Args:
    default_unit: str, The default duration unit.
    lower_bound: str, An inclusive lower bound for values.
    upper_bound: str, An inclusive upper bound for values.
    parsed_unit: str, The unit that the result should be returned as. Can be
      's', 'ms', or 'us'.

  Raises:
    ArgumentTypeError: If either the lower_bound or upper_bound
      cannot be parsed. The returned function will also raise this
      error if it cannot parse its input. This exception is also
      raised if the returned function receives an out-of-bounds
      input.

  Returns:
    A function that accepts a single time duration as input to be
      parsed an returns an integer if the parsed value is not a fraction;
      Otherwise, a float value rounded up to 4 decimals places.
  """

  def Parse(value):
    """Parses a duration from value and returns it in the parsed_unit."""
    if parsed_unit == 'ms':
      multiplier = 1000
    elif parsed_unit == 'us':
      multiplier = 1000000
    elif parsed_unit == 's':
      multiplier = 1
    else:
      raise ArgumentTypeError(
          _GenerateErrorMessage('parsed_unit must be one of s, ms, us.'))
    try:
      duration = times.ParseDuration(value, default_suffix=default_unit)
      parsed_value = duration.total_seconds * multiplier
      parsed_int_value = int(parsed_value)
      parsed_rounded_value = round(parsed_value, 4)
      fraction = parsed_rounded_value - parsed_int_value
      if fraction:
        return parsed_rounded_value
      return parsed_int_value
    except times.Error as e:
      message = six.text_type(e).rstrip('.')
      raise ArgumentTypeError(_GenerateErrorMessage(
          'Failed to parse duration: {0}'.format(message, user_input=value)))

  parsed_lower_bound = Parse(lower_bound)

  if upper_bound is None:
    parsed_upper_bound = None
  else:
    parsed_upper_bound = Parse(upper_bound)

  def ParseWithBoundsChecking(value):
    """Same as Parse except bound checking is performed."""
    if value is None:
      return None
    parsed_value = Parse(value)
    if parsed_lower_bound is not None and parsed_value < parsed_lower_bound:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'value must be greater than or equal to {0}'.format(lower_bound),
              user_input=value))
    if parsed_upper_bound is not None and parsed_value > parsed_upper_bound:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'value must be less than or equal to {0}'.format(upper_bound),
              user_input=value))
    return parsed_value

  return ParseWithBoundsChecking


def BinarySize(lower_bound=None,
               upper_bound=None,
               suggested_binary_size_scales=None,
               default_unit='G',
               type_abbr='B'):
  """Returns a function that can parse binary sizes.

  Binary sizes are defined as base-2 values representing number of
  bytes.

  Input to the parsing function must be a string of the form:

    DECIMAL[UNIT]

  The amount must be non-negative. Valid units are "B", "KB", "MB",
  "GB", "TB", "PB", "KiB", "MiB", "GiB", "TiB", "PiB".  If the unit is
  omitted then default_unit is assumed.

  The result is parsed in bytes. For example:

    parser = BinarySize()
    assert parser('10GB') == 1073741824

  Another example:

    parser = BinarySize()
    assert parser('2.5KB') == 2560

  Args:
    lower_bound: str, An inclusive lower bound for values.
    upper_bound: str, An inclusive upper bound for values.
    suggested_binary_size_scales: list, A list of strings with units that will
      be recommended to user.
    default_unit: str, unit used when user did not specify unit.
    type_abbr: str, the type suffix abbreviation, e.g., B for bytes, b/s for
      bits/sec.

  Raises:
    ArgumentTypeError: If either the lower_bound or upper_bound
      cannot be parsed. The returned function will also raise this
      error if it cannot parse its input. This exception is also
      raised if the returned function receives an out-of-bounds
      input.

  Returns:
    A function that accepts a single binary size as input to be
      parsed.
  """
  return _ValueParser(
      _BINARY_SIZE_SCALES,
      default_unit=default_unit,
      lower_bound=lower_bound,
      upper_bound=upper_bound,
      strict_case=False,
      type_abbr=type_abbr,
      suggested_binary_size_scales=suggested_binary_size_scales)


_KV_PAIR_DELIMITER = '='


class Range(object):
  """Range of integer values."""

  def __init__(self, start, end):
    self.start = start
    self.end = end

  @staticmethod
  def Parse(string_value):
    """Creates Range object out of given string value."""
    match = re.match(_RANGE_PATTERN, string_value)
    if not match:
      raise ArgumentTypeError(
          'Expected a non-negative integer value or a '
          'range of such values instead of "{0}"'.format(string_value))
    start = int(match.group('start'))
    end = match.group('end')
    if end is None:
      end = start
    else:
      end = int(end)
    if end < start:
      raise ArgumentTypeError('Expected range start {0} smaller or equal to '
                              'range end {1} in "{2}"'.format(
                                  start, end, string_value))
    return Range(start, end)

  def Combine(self, other):
    """Combines two overlapping or adjacent ranges, raises otherwise."""
    if self.end + 1 < other.start or self.start > other.end + 1:
      raise Error('Cannot combine non-overlapping or non-adjacent ranges '
                  '{0} and {1}'.format(self, other))
    return Range(min(self.start, other.start), max(self.end, other.end))

  def __eq__(self, other):
    if isinstance(other, Range):
      return self.start == other.start and self.end == other.end
    return False

  def __lt__(self, other):
    if self.start == other.start:
      return self.end < other.end
    return self.start < other.start

  def __str__(self):
    if self.start == self.end:
      return six.text_type(self.start)
    return '{0}-{1}'.format(self.start, self.end)


class HostPort(object):
  """A class for holding host and port information."""

  IPV4_OR_HOST_PATTERN = r'^(?P<address>[\w\d\.-]+)?(:|:(?P<port>[\d]+))?$'
  # includes hostnames
  IPV6_PATTERN = r'^(\[(?P<address>[\w\d:]+)\])(:|:(?P<port>[\d]+))?$'

  def __init__(self, host, port):
    self.host = host
    self.port = port

  @staticmethod
  def Parse(s, ipv6_enabled=False):
    """Parse the given string into a HostPort object.

    This can be used as an argparse type.

    Args:
      s: str, The string to parse. If ipv6_enabled and host is an IPv6 address,
      it should be placed in square brackets: e.g.
        [2001:db8:0:0:0:ff00:42:8329] or
        [2001:db8:0:0:0:ff00:42:8329]:8080
      ipv6_enabled: boolean, If True then accept IPv6 addresses.

    Raises:
      ArgumentTypeError: If the string is not valid.

    Returns:
      HostPort, The parsed object.
    """
    if not s:
      return HostPort(None, None)

    match = re.match(HostPort.IPV4_OR_HOST_PATTERN, s, re.UNICODE)
    if ipv6_enabled and not match:
      match = re.match(HostPort.IPV6_PATTERN, s, re.UNICODE)
      if not match:
        raise ArgumentTypeError(
            _GenerateErrorMessage(
                'Failed to parse host and port. Expected format \n\n'
                '  IPv4_ADDRESS_OR_HOSTNAME:PORT\n\n'
                'or\n\n'
                '  [IPv6_ADDRESS]:PORT\n\n'
                '(where :PORT is optional).',
                user_input=s))
    elif not match:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Failed to parse host and port. Expected format \n\n'
              '  IPv4_ADDRESS_OR_HOSTNAME:PORT\n\n'
              '(where :PORT is optional).',
              user_input=s))
    return HostPort(match.group('address'), match.group('port'))


class Day(object):
  """A class for parsing a datetime object for a specific day."""

  @staticmethod
  def Parse(s):
    if not s:
      return None
    try:
      return times.ParseDateTime(s, '%Y-%m-%d').date()
    except times.Error as e:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Failed to parse date: {0}'.format(six.text_type(e)),
              user_input=s))


class Datetime(object):
  """A class for parsing a datetime object."""

  @staticmethod
  def Parse(s):
    """Parses a string value into a Datetime object in local timezone."""
    if not s:
      return None
    try:
      return times.ParseDateTime(s)
    except times.Error as e:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Failed to parse date/time: {0}'.format(six.text_type(e)),
              user_input=s))

  @staticmethod
  def ParseUtcTime(s):
    """Parses a string representing a time in UTC into a Datetime object."""
    if not s:
      return None
    try:
      return times.ParseDateTime(s, tzinfo=tz.tzutc())
    except times.Error as e:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Failed to parse UTC time: {0}'.format(six.text_type(e)),
              user_input=s))


class DayOfWeek(object):
  """A class for parsing a day of the week."""

  DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

  @staticmethod
  def Parse(s):
    """Validates and normalizes a string as a day of the week."""
    if not s:
      return None
    fixed = s.upper()[:3]
    if fixed not in DayOfWeek.DAYS:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Failed to parse day of week. Value should be one of {0}'.format(
                  ', '.join(DayOfWeek.DAYS)),
              user_input=s))
    return fixed


def _BoundedType(type_builder,
                 type_description,
                 lower_bound=None,
                 upper_bound=None,
                 unlimited=False):
  """Returns a function that can parse given type within some bound.

  Args:
    type_builder: A callable for building the requested type from the value
      string.
    type_description: str, Description of the requested type (for verbose
      messages).
    lower_bound: of type compatible with type_builder, The value must be >=
      lower_bound.
    upper_bound: of type compatible with type_builder, The value must be <=
      upper_bound.
    unlimited: bool, If True then a value of 'unlimited' means no limit.

  Returns:
    A function that can parse given type within some bound.
  """

  def Parse(value):
    """Parses value as a type constructed by type_builder.

    Args:
      value: str, Value to be converted to the requested type.

    Raises:
      ArgumentTypeError: If the provided value is out of bounds or unparsable.

    Returns:
      Value converted to the requested type.
    """
    if unlimited and value == 'unlimited':
      return None

    try:
      v = type_builder(value)
    except ValueError:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Value must be {0}'.format(type_description), user_input=value))

    if lower_bound is not None and v < lower_bound:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Value must be greater than or equal to {0}'.format(lower_bound),
              user_input=value))

    if upper_bound is not None and upper_bound < v:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'Value must be less than or equal to {0}'.format(upper_bound),
              user_input=value))

    return v

  return Parse


def BoundedInt(*args, **kwargs):
  return _BoundedType(int, 'an integer', *args, **kwargs)


def BoundedFloat(*args, **kwargs):
  return _BoundedType(float, 'a floating point number', *args, **kwargs)


def _SplitOnDelim(arg_value, delim):
  if not arg_value:
    return []
  if not arg_value.endswith(delim):
    arg_value += delim
  return arg_value.split(delim)[:-1]


def _ContainsValidJson(str_value):
  """Checks whether the string contains balanced json."""
  closing_brackets = {'}': '{', ']': '['}
  opening_brackets = set(closing_brackets.values())
  current_brackets = []

  for i in range(len(str_value)):
    # ignore if escaped value
    if i > 0 and str_value[i - 1] == '\\':
      continue

    ch = str_value[i]
    if ch in closing_brackets:
      matching_brace = closing_brackets[ch]
      if not current_brackets or current_brackets[-1] != matching_brace:
        return False
      current_brackets.pop()
    elif ch in opening_brackets:
      current_brackets.append(ch)

  return not current_brackets


def _RejoinJsonStrs(json_list, delim, arg_value):
  """Rejoins json substrings that are part of the same json strings.

  For example:
      [
          'key={"a":"b"',
          '"c":"d"}'
      ]

  Is merged together into: ['key={"a":"b","c":"d"}']

  Args:
    json_list: [str], list of json snippets
    delim: str, delim used to rejoin the json snippets
    arg_value: str, original value used to make json_list

  Returns:
    list of strings containing balanced json
  """
  result = []
  current_substr = None

  for token in json_list:
    if not current_substr:
      current_substr = token
    else:
      current_substr += delim + token

    if _ContainsValidJson(current_substr):
      result.append(current_substr)
      current_substr = None

  if current_substr:
    raise ValueError(
        'Invalid entry "{}": missing opening brace ("{{" or "[") or closing '
        'brace ("}}" or "]").'.format(arg_value))

  return result


def _TokenizeQuotedList(arg_value, delim=',', includes_json=False):
  """Tokenize an argument into a list.

  Deliminators that are inside json will not be split. Even when the
  json is nested, we will not split on the delimitor until we reach the
  json's closing bracket. For example:

    '{"a": [1, 2], "b": 3},{"c": 4}'

  with default delim (',') will be split only on the `,` separating the 2
  json strings i.e.

    [
        '{"a": [1, 2], "b": 3}',
        '{"c": 4}'
    ]

  This also works for strings that contain dictionary pattern. For example:

    'key1={"a": [1, 2], "b": 3},key2={"c": 4}'

  with default delim (',') will be split on the delim (',') separating the
  two strings into

    [
        'key1={"a": [1, 2], "b": 3}',
        'key2={"c": 4}'
    ]


  Args:
    arg_value: str, The raw argument.
    delim: str, The delimiter on which to split the argument string.
    includes_json: str, determines whether to ignore delimiter inside json

  Returns:
    [str], The tokenized list.
  """
  if not arg_value:
    return []

  str_list = _SplitOnDelim(arg_value, delim)
  if not includes_json or delim != ',':
    return str_list

  return _RejoinJsonStrs(str_list, delim, arg_value)


def _ConcatList(existing_values, new_values):
  if existing_values is None:
    existing_values = []
  if isinstance(new_values, list):
    for new_value in new_values:
      _ConcatList(existing_values, new_value)
  else:
    existing_values.append(new_values)
  return existing_values


class ArgType(object):
  """Base class for arg types."""


class ArgBoolean(ArgType):
  """Interpret an argument value as a bool."""

  def __init__(self,
               truthy_strings=None,
               falsey_strings=None,
               case_sensitive=False):
    self._case_sensitive = case_sensitive
    if truthy_strings:
      self._truthy_strings = truthy_strings
    else:
      self._truthy_strings = ['true', 'yes']
    if falsey_strings:
      self._falsey_strings = falsey_strings
    else:
      self._falsey_strings = ['false', 'no']

  def __call__(self, arg_value):
    if not self._case_sensitive:
      normalized_arg_value = arg_value.lower()
    else:
      normalized_arg_value = arg_value
    if normalized_arg_value in self._truthy_strings:
      return True
    if normalized_arg_value in self._falsey_strings:
      return False
    raise ArgumentTypeError(
        'Invalid flag value [{0}], expected one of [{1}]'.format(
            arg_value, ', '.join(self._truthy_strings + self._falsey_strings)))


class ArgList(usage_text.ArgTypeUsage, ArgType):
  """Interpret an argument value as a list.

  Intended to be used as the type= for a flag argument. Splits the string on
  commas or another delimiter and returns a list.

  By default, splits on commas:
      'a,b,c' -> ['a', 'b', 'c']
  There is an available syntax for using an alternate delimiter:
      '^:^a,b:c' -> ['a,b', 'c']
      '^::^a:b::c' -> ['a:b', 'c']
      '^,^^a^,b,c' -> ['^a^', ',b', 'c']
  """

  DEFAULT_DELIM_CHAR = ','
  ALT_DELIM_CHAR = '^'

  def __init__(self,
               element_type=None,
               min_length=0,
               max_length=None,
               choices=None,
               custom_delim_char=None,
               visible_choices=None,
               includes_json=False):
    """Initialize an ArgList.

    Args:
      element_type: (str)->str, A function to apply to each of the list items.
      min_length: int, The minimum size of the list.
      max_length: int, The maximum size of the list.
      choices: [element_type], a list of valid possibilities for elements. If
        None, then no constraints are imposed.
      custom_delim_char: char, A customized delimiter character.
      visible_choices: [element_type], a list of valid possibilities for
        elements to be shown to the user. If None, defaults to choices.
      includes_json: bool, whether the list contains any json

    Returns:
      (str)->[str], A function to parse the list of values in the argument.

    Raises:
      ArgumentTypeError: If the list is malformed.
    """
    self.element_type = element_type
    self.choices = choices
    self.visible_choices = (
        visible_choices if visible_choices is not None else choices)

    if self.visible_choices:

      def ChoiceType(raw_value):
        if element_type:
          typed_value = element_type(raw_value)
        else:
          typed_value = raw_value
        if typed_value not in choices:
          raise ArgumentTypeError('{value} must be one of [{choices}]'.format(
              value=typed_value,
              choices=', '.join(
                  [six.text_type(choice) for choice in self.visible_choices])))
        return typed_value

      self.element_type = ChoiceType

    self.min_length = min_length
    self.max_length = max_length

    self.custom_delim_char = custom_delim_char
    self.includes_json = includes_json

  def __call__(self, arg_value):  # pylint:disable=missing-docstring

    if isinstance(arg_value, list):
      arg_list = arg_value
    elif not isinstance(arg_value, six.string_types):
      raise ArgumentTypeError('Invalid type [{}] for flag value [{}]'.format(
          type(arg_value).__name__, arg_value))
    else:
      delim = self.custom_delim_char or self.DEFAULT_DELIM_CHAR
      if (arg_value.startswith(self.ALT_DELIM_CHAR) and
          self.ALT_DELIM_CHAR in arg_value[1:]):
        delim, arg_value = arg_value[1:].split(self.ALT_DELIM_CHAR, 1)
        if not delim:
          raise ArgumentTypeError(
              'Invalid delimeter. Please see `gcloud topic flags-file` or '
              '`gcloud topic escaping` for information on providing list or '
              'dictionary flag values with special characters.')
      arg_list = _TokenizeQuotedList(
          arg_value, delim=delim, includes_json=self.includes_json)

    if len(arg_list) < self.min_length:
      raise ArgumentTypeError('not enough args')
    if self.max_length is not None and len(arg_list) > self.max_length:
      raise ArgumentTypeError('too many args')

    if self.element_type:
      arg_list = [self.element_type(arg) for arg in arg_list]

    return arg_list

  _MAX_METAVAR_LENGTH = 30  # arbitrary, but this is pretty long

  @property
  def hidden(self):
    return False

  def GetUsageMetavar(self, is_custom_metavar, metavar):
    """Get a specially-formatted metavar for the ArgList to use in help.

    An example is worth 1,000 words:

    >>> ArgList().GetUsageMetavar('FOO')
    '[FOO,...]'
    >>> ArgList(min_length=1).GetUsageMetavar('FOO')
    'FOO,[FOO,...]'
    >>> ArgList(max_length=2).GetUsageMetavar('FOO')
    'FOO,[FOO]'
    >>> ArgList(max_length=3).GetUsageMetavar('FOO')  # One, two, many...
    'FOO,[FOO,...]'
    >>> ArgList(min_length=2, max_length=2).GetUsageMetavar('FOO')
    'FOO,FOO'
    >>> ArgList().GetUsageMetavar('REALLY_VERY_QUITE_LONG_METAVAR')
    'REALLY_VERY_QUITE_LONG_METAVAR,[...]'

    Args:
      is_custom_metavar: unused in GetUsageMetavar
      metavar: string, the base metavar to turn into an ArgList metavar

    Returns:
      string, the ArgList usage metavar
    """
    del is_custom_metavar  # Unused in GetUsageMetavar

    delim_char = self.custom_delim_char or self.DEFAULT_DELIM_CHAR
    required = delim_char.join([metavar] * self.min_length)

    if self.max_length:
      num_optional = self.max_length - self.min_length
    else:
      num_optional = None

    # Use the "1, 2, many" approach to counting
    if num_optional == 0:
      optional = ''
    elif num_optional == 1:
      optional = '[{}]'.format(metavar)
    elif num_optional == 2:
      optional = '[{0}{1}[{0}]]'.format(metavar, delim_char)
    else:
      optional = '[{}{}...]'.format(metavar, delim_char)

    msg = delim_char.join([x for x in [required, optional] if x])

    if len(msg) < self._MAX_METAVAR_LENGTH:
      return msg

    # With long metavars, only put it in once.
    if self.min_length == 0:
      return '[{}{}...]'.format(metavar, delim_char)
    if self.min_length == 1:
      return '{}{}[...]'.format(metavar, delim_char)
    else:
      return '{0}{1}...{1}[...]'.format(metavar, delim_char)

  def GetUsageExample(self, shorthand):
    del shorthand  # Unused arguments
    return None

  def GetUsageHelpText(self, field_name, required, flag_name=None):
    del field_name, required, flag_name  # Unused arguments
    return None


class ArgDict(ArgList):
  """Interpret an argument value as a dict.

  Intended to be used as the type= for a flag argument. Splits the string on
  commas to get a list, and then splits the items on equals to get a set of
  key-value pairs to get a dict.
  """

  def __init__(self,
               key_type=None,
               value_type=None,
               spec=None,
               min_length=0,
               max_length=None,
               allow_key_only=False,
               required_keys=None,
               operators=None,
               includes_json=False):
    """Initialize an ArgDict.

    Args:
      key_type: (str)->str, A function to apply to each of the dict keys.
      value_type: (str)->str, A function to apply to each of the dict values.
      spec: {str: (str)->str}, A mapping of expected keys to functions. The
        functions are applied to the values. If None, an arbitrary set of keys
        will be accepted. If not None, it is an error for the user to supply a
        key that is not in the spec. If the function specified is None, then
        accept a key only without '=value'.
      min_length: int, The minimum number of keys in the dict.
      max_length: int, The maximum number of keys in the dict.
      allow_key_only: bool, Allow empty values.
      required_keys: [str], Required keys in the dict.
      operators: operator_char -> value_type, Define multiple single character
        operators, each with its own value_type converter. Use value_type==None
        for no conversion. The default value is {'=': value_type}
      includes_json: bool, whether string parsed includes json

    Returns:
      (str)->{str:str}, A function to parse the dict in the argument.

    Raises:
      ArgumentTypeError: If the list is malformed.
      ValueError: If both value_type and spec are provided.
    """
    super(ArgDict, self).__init__(
        min_length=min_length, max_length=max_length,
        includes_json=includes_json)
    if spec and value_type:
      raise ValueError('cannot have both spec and sub_type')
    self.key_type = key_type
    self.value_type = value_type
    self.spec = spec
    self.allow_key_only = allow_key_only
    self.required_keys = required_keys or []
    if not operators:
      operators = {'=': value_type}
    for op in operators.keys():
      if len(op) != 1:
        raise ArgumentTypeError(
            'Operator [{}] must be one character.'.format(op))
    ops = ''.join(six.iterkeys(operators))
    key_op_value_pattern = '([^{ops}]+)([{ops}]?)(.*)'.format(
        ops=re.escape(ops))
    self.key_op_value = re.compile(key_op_value_pattern, re.DOTALL)
    self.operators = operators

  def _ApplySpec(self, key, value):
    if key in self.spec:
      if self.spec[key] is None:
        if value:
          raise ArgumentTypeError('Key [{0}] does not take a value'.format(key))
        return None
      return self.spec[key](value)
    else:
      raise ArgumentTypeError(
          _GenerateErrorMessage(
              'valid keys are [{0}]'.format(', '.join(sorted(
                  self.spec.keys()))),
              user_input=key))

  def _ValidateKeyValue(self, key, value, op='='):
    """Converts and validates <key,value> and returns (key,value)."""
    if (not op or value is None) and not self.allow_key_only:
      raise ArgumentTypeError(
          'Bad syntax for dict arg: [{0}]. Please see '
          '`gcloud topic flags-file` or `gcloud topic escaping` for '
          'information on providing list or dictionary flag values with '
          'special characters.'.format(key))
    if self.key_type:
      try:
        key = self.key_type(key)
      except ValueError:
        raise ArgumentTypeError('Invalid key [{0}]'.format(key))
    convert_value = self.operators.get(op, None)
    if convert_value:
      try:
        value = convert_value(value)
      except ValueError:
        raise ArgumentTypeError('Invalid value [{0}]'.format(value))
    if self.spec:
      value = self._ApplySpec(key, value)
    return key, value

  def _CheckRequiredKeys(self, arg_dict):
    for required_key in self.required_keys:
      if required_key not in arg_dict:
        raise ArgumentTypeError(
            'Key [{0}] required in dict arg but not provided'.format(
                required_key))

  def __call__(self, arg_value):  # pylint:disable=missing-docstring

    if isinstance(arg_value, dict):
      raw_dict = arg_value
      arg_dict = collections.OrderedDict()
      for key, value in six.iteritems(raw_dict):
        key, value = self._ValidateKeyValue(key, value)
        arg_dict[key] = value
    elif not isinstance(arg_value, six.string_types):
      raise ArgumentTypeError('Invalid type [{}] for flag value [{}]'.format(
          type(arg_value).__name__, arg_value))
    else:
      arg_list = super(ArgDict, self).__call__(arg_value)
      arg_dict = collections.OrderedDict()
      for arg in arg_list:
        match = self.key_op_value.match(arg)
        # TODO(b/35944028): These exceptions won't present well to the user.
        if not match:
          raise ArgumentTypeError('Invalid flag value [{0}]'.format(arg))
        key, op, value = match.group(1), match.group(2), match.group(3)
        key, value = self._ValidateKeyValue(key, value, op=op)
        arg_dict[key] = value

    self._CheckRequiredKeys(arg_dict)

    return arg_dict

  @property
  def hidden(self):
    return False

  def GetUsageMetavar(self, is_custom_metavar, metavar):
    # If we're not using a spec to limit the key values or if metavar
    # has been overridden, then use the normal ArgList formatting
    if not self.spec or is_custom_metavar:
      return super(ArgDict, self).GetUsageMetavar(is_custom_metavar, metavar)

    msg_list = []
    spec_list = sorted(six.iteritems(self.spec))

    # First put the spec keys with no value followed by those that expect a
    # value
    for spec_key, spec_function in spec_list:
      if spec_function is None:
        if not self.allow_key_only:
          raise ArgumentTypeError(
              'Key [{0}] specified in spec without a function but '
              'allow_key_only is set to False'.format(spec_key))
        msg_list.append(spec_key)

    for spec_key, spec_function in spec_list:
      if spec_function and not usage_text.IsHidden(spec_function):
        msg_list.append('{0}={1}'.format(spec_key, spec_key.upper()))

    msg = '[' + '],['.join(msg_list) + ']'
    return msg

  def GetUsageExample(self, shorthand):
    """Returns a string of usage examples.

    Generates an example of expected user input.
    For example, an ArgDict with spec={'x': int, 'y': str} will generate

      x=int,y=string

    An ArgDict with key_type=str and value_type=str will generate

      string=string

    Args:
      shorthand: unused bool, whether to display in shorthand (ArgDict is
        always parsed as shorthand)

    Returns:
      str, example text of usage
    """
    del shorthand  # Unused arguments

    if self.spec:
      return ','.join(
          usage_text.GetNestedKeyValueExample(key, value, shorthand=True)
          for key, value in sorted(self.spec.items()))

    # keys are parsed as string by default in ArgDict
    # However, values can be None if allow_key_only
    if self.allow_key_only:
      value_type = self.value_type
    else:
      value_type = self.value_type or str

    return usage_text.GetNestedKeyValueExample(
        key_type=self.key_type or str,
        value_type=value_type,
        shorthand=True
    )

  def GetUsageHelpText(self, field_name, required, flag_name=None):
    del field_name, required, flag_name  # Unused arguments
    return None


class ArgObject(ArgDict):
  """Catch all arg type that will accept a file, json, or ArgDict.

  ArgObject is very similar to ArgDict with some extra functionality. ArgObject
  will first try to parse a value as an arg_dict if string contains '='. The
  type will then try to parse string as a file if string contains
  .yaml or .json. Finally, parser will parse the string as json.

  I. For example, with the following flag defintion:

    parser.add_argument(
        '--inputs',
        type=arg_parsers.ArgObject(key_type=str, value_type=int))

  a caller can retrieve {"foo": 100} by specifying any of the following
  on the command line.

    (1) --inputs=foo=100
    (2) --inputs='{"foo": 100}'
    (3) --inputs=path_to_json.(json|yaml)

  II. If we need the type return a list of messages, use the repeated arg.
  NOTE: when using repeated values, it is recommended to specify the
  action as arg_parsers.FlattenAction()

  For example, with the following flag defintion:

    parser.add_argument(
        '--inputs',
        type=arg_parsers.ArgObject(key_type=str, value_type=int),
        action=arg_parsers.FlattenAction()
        repeated=True)

  a caller can retrieve [{"foo": 1, "bar": 2}, {"bax": 3}] by specifying any
  of the following on the command line.

    (1) --inputs=foo=1,bar=2 --inputs=bax=3
    (2) --inputs='[{"foo": 1, "bar": 2}, {"bax": 3}]'
    (3) --inputs=path_to_json.(json|yaml)

  III. If we need to parse non key-value pairs, do not provide key_type or spec.
  For example, with the following flag defintion:

    parser.add_argument(
        '--inputs',
        type=arg_parsers.ArgObject(value_type=int))

  a caller can retrieve 100 by specifying the following
  on the command line.

    (1) --inputs=100
    (2) --inputs=path_to_json.(json|yaml)

  IV. If we need to create nested objects, set value_type to another ArgObject
  type. ArgDict syntax is automatically disabled for the nested ArgObject type
  with enable_shorthand=False

  For example, with the following flag defintion:

    parser.add_argument(
        '--inputs',
        type=arg_parsers.ArgObject(
            key_type=str,
            value_type=arg_parsers.ArgObject(
                key_type=str, value_type=int, enable_shorthand=False)))

  a caller can retrieve {"foo": {"bar": 1}} by specifying any
  of the following on the command line.

    (1) --inputs='foo={"bar": 1}'
    (2) --inputs='{"foo": {"bar": 1}}'
    (3) --inputs=path_to_json.(json|yaml)
  """

  def _DisableShorthand(self, arg_type):
    if isinstance(arg_type, ArgObject) and arg_type.enable_shorthand:
      arg_type.enable_shorthand = False

  def __init__(self, key_type=None, value_type=None, spec=None,
               required_keys=None, help_text=None, repeated=False,
               hidden=None, enable_shorthand=True):
    # Disable arg_dict syntax for nested values
    if value_type:
      self._DisableShorthand(value_type)
    elif spec:
      for value in spec.values():
        self._DisableShorthand(value)

    super(ArgObject, self).__init__(
        key_type=key_type, value_type=value_type, spec=spec,
        required_keys=required_keys, includes_json=True)
    self.help_text = help_text
    self.repeated = repeated
    self._keyed_values = key_type is not None or spec is not None
    self._hidden = hidden
    self.enable_shorthand = enable_shorthand

    if self.required_keys and not self._keyed_values:
      raise InvalidTypeError(
          'ArgObject type listed required keys as {}. Keys can only be '
          'listed as required if `spec` or `key_type` arguments are '
          'provided to the ArgObject type.'.format(self.required_keys))

  @property
  def parse_as_arg_dict(self):
    return self.enable_shorthand and self._keyed_values

  def _Map(self, arg_value, callback):
    """Applies callback for arg_value.

    Arg_value can be a dictionary, list, or other value.

    Args:
      arg_value: can be a dictionary, list, or other value,
      callback: (key, val) -> key, val, function that accepts key and value
        and returns transformed values.

    Returns:
      dictionary, list, or value with callback operation performed on it.
    """
    if isinstance(arg_value, list) and self.repeated:
      arg_list = []
      for value in arg_value:
        value = self._Map(value, callback)
        arg_list.append(value)
      return arg_list

    if isinstance(arg_value, dict) and self._keyed_values:
      arg_dict = collections.OrderedDict()
      for key, value in arg_value.items():
        key, value = callback(key, value)
        arg_dict[key] = value
      return arg_dict

    _, value = callback(None, arg_value)
    return value

  def _StringifyValues(self, key, value):
    """Returns string version of arguments."""
    if key is None and self._keyed_values:
      raise ArgumentTypeError(
          'Expecting {} to be json or arg_dict format'.format(value))

    if key and not isinstance(key, str):
      key = str(key)
    if value and not isinstance(value, str):
      value = json.dumps(value)
    return key, value

  def _StringifyDictValues(self, arg_value):
    # Convert the dictionary key-value pairs back into strings to simplify
    # logic and keep type functions (key_type, value_type, spec, etc)
    # consistent.
    # TODO(b/286382512): improve performance so that we're not parsing and
    # stringifying json at each level
    return self._Map(arg_value, self._StringifyValues)

  def _LooksLikeJson(self, arg_value):
    list_pattern = r'^\s*\[.*\]\s*$'
    json_pattern = r'^\s*\{.*\}\s*$'
    return ((self.repeated and re.match(list_pattern, arg_value)) or
            (self._keyed_values and re.match(json_pattern, arg_value)))

  def _LoadJsonOrFile(self, arg_value):
    """Loads json string or file into a dictionary.

    Args:
      arg_value: str, path to a json or yaml file or json string

    Returns:
      Dictionary [str: str] where the value is a json string or other String
        value
    """
    file_path_pattern = r'^\S*\.(yaml|json)$'
    if re.match(file_path_pattern, arg_value):
      arg_value = FileContents()(arg_value)

    if self._LooksLikeJson(arg_value):
      json_value = yaml.load(arg_value)
    else:
      json_value = arg_value

    return self._StringifyDictValues(json_value)

  def _CheckRequiredKeys(self, arg_dict):
    if isinstance(arg_dict, list):
      for value in arg_dict:
        super(ArgObject, self)._CheckRequiredKeys(value)
    else:
      super(ArgObject, self)._CheckRequiredKeys(arg_dict)

  def _ParseAndValidateJson(self, arg_value):
    result = self._Map(arg_value, self._ValidateKeyValue)

    if self.required_keys:
      self._CheckRequiredKeys(result)

    return result

  def __call__(self, arg_value):
    if not isinstance(arg_value, str):
      raise ValueError(
          'ArgObject can only convert string values. Received {}.'.format(
              arg_value))

    ops = self.operators.keys()
    arg_dict_pattern = '({})'.format('|'.join(ops))
    if re.search(arg_dict_pattern, arg_value) and self.parse_as_arg_dict:
      # parse as arg_dict
      value = super(ArgObject, self).__call__(arg_value)
    else:
      # parse as json
      json_dict = self._LoadJsonOrFile(arg_value)
      value = self._ParseAndValidateJson(json_dict)

    if self.repeated and not isinstance(value, list):
      value = [value]

    return value

  @property
  def hidden(self):
    if self._hidden is not None:
      return self._hidden
    elif self.spec:
      return all(usage_text.IsHidden(value) for value in self.spec.values())
    else:
      return (usage_text.IsHidden(self.key_type) or
              usage_text.IsHidden(self.value_type))

  def GetUsageMetavar(self, is_custom_metavar, metavar):
    if self._keyed_values:
      return super(ArgObject, self).GetUsageMetavar(is_custom_metavar, metavar)
    else:
      return metavar

  def GetUsageExample(self, shorthand):
    """Returns a string of usage examples.

    Recursively generates an example of expected user input.
    For example, an ArgObject with spec={'x': int, 'y': str} will generate...

      x=int,y=string (shorthand) and
      {"x": int, "y": "string"} (json)

    An ArgObject with key_type=str and value_type=str will generate...

      string=string (shorthand) and
      {"string": "string"} (json)

    An ArgObject with value_type=str will always generate...

      string (shorthand and json)

    Args:
      shorthand: bool, whether to display in shorthand

    Returns:
      str | None, example text of usage. None if hidden.
    """
    if self.hidden:
      return None

    shorthand_enabled = shorthand and self.enable_shorthand
    is_json_obj = not shorthand_enabled and self._keyed_values
    is_array = not shorthand_enabled and self.repeated

    # Default to formatting single values as shorthand in example.
    # See method descriptor above.
    format_as_shorthand = not (is_json_obj or is_array)

    if self.spec:
      comma = ',' if format_as_shorthand else ', '
      example = (
          usage_text.GetNestedKeyValueExample(key, value, format_as_shorthand)
          for key, value in sorted(self.spec.items()))
      usage = comma.join(line for line in example if line is not None)
    else:
      # Keys can be None but values are parsed as string
      # by default in ArgObject
      usage = usage_text.GetNestedKeyValueExample(
          self.key_type, self.value_type or str, format_as_shorthand)

    if is_json_obj:
      usage = '{' + usage + '}'
    if is_array:
      usage = '[' + usage + ']'

    return usage

  def _GetCodeExamples(self, flag_name):
    """Returns a string of user input examples."""
    shorthand_example = usage_text.FormatCodeSnippet(
        arg_name=flag_name,
        arg_value=self.GetUsageExample(shorthand=True),
        append=self.repeated)

    json_example = usage_text.FormatCodeSnippet(
        arg_name=flag_name, arg_value=self.GetUsageExample(shorthand=False))

    file_example = usage_text.FormatCodeSnippet(
        arg_name=flag_name, arg_value='path_to_file.(yaml|json)')

    if shorthand_example == json_example:
      return ('*Input Example:*\n\n{}\n\n'
              '*File Example:*\n\n{}').format(shorthand_example, file_example)
    else:
      return ('*Shorthand Example:*\n\n{}\n\n'
              '*JSON Example:*\n\n{}\n\n'
              '*File Example:*\n\n{}').format(
                  shorthand_example, json_example, file_example)

  def GetUsageHelpText(self, field_name, required, flag_name=None):
    """Returns a string of usage help text.

    Recursively generates usage help text to provide the user with
    more information on valid flag values and the general schema.
    For example, ArgObject with...

      spec={
          'x': int,
          'y': arg_parsers.ArgObject(help_text='Y help.', spec={'z': str}),
      }

    will generate the following by default...

      ```
      *x*
        Sets `z` value.

      *y*
        Y help.

        *z*
          Sets `z` value.
      ```

    Args:
      field_name: str | None, field the flag of this type is setting
      required: bool, whether the flag of this type is required
      flag_name: str | None, the name of the flag. If not none, will generate
        code examples.

    Returns:
      str | None, help text with schema and examples. None if hidden.
    """
    if self.hidden:
      return None

    result = []
    result.append(usage_text.FormatHelpText(
        field_name, required, help_text=self.help_text))

    if self.spec:
      items = (
          usage_text.GetNestedUsageHelpText(key, val, key in self.required_keys)
          for key, val in sorted(self.spec.items()))
      result.extend(items)

    elif self.key_type:
      # Keys can be None but values are parsed as string
      # by default in ArgObject
      result.append(
          usage_text.GetNestedUsageHelpText('KEY', self.key_type))
      result.append(
          usage_text.GetNestedUsageHelpText('VALUE', self.value_type or str))

    if flag_name:
      # Reset indentation back to root level
      result.append(usage_text.ASCII_INDENT + self._GetCodeExamples(flag_name))

    return '\n\n'.join(line for line in result if line is not None)


class UpdateAction(argparse.Action):
  r"""Create a single dict value from delimited or repeated flags.

  This class is intended to be a more flexible version of
  argparse._AppendAction.

  For example, with the following flag definition:

      parser.add_argument(
        '--inputs',
        type=arg_parsers.ArgDict(),
        action='append')

  a caller can specify on the command line flags such as:

    --inputs k1=v1,k2=v2

  and the result will be a list of one dict:

    [{ 'k1': 'v1', 'k2': 'v2' }]

  Specifying two separate command line flags such as:

    --inputs k1=v1 \
    --inputs k2=v2

  will produce a list of dicts:

    [{ 'k1': 'v1'}, { 'k2': 'v2' }]

  The UpdateAction class allows for both of the above user inputs to result
  in the same: a single dictionary:

    { 'k1': 'v1', 'k2': 'v2' }

  This gives end-users a lot more flexibility in constructing their command
  lines, especially when scripting calls.

  Note that this class will raise an exception if a key value is specified
  more than once. To allow for a key value to be specified multiple times,
  use UpdateActionWithAppend.
  """

  def OnDuplicateKeyRaiseError(self, key, existing_value=None, new_value=None):
    if existing_value is None:
      user_input = None
    else:
      # Note this isn't quite right - the keys and values here have already been
      # transformed by the key_type/value_type functions and/or spec in the
      # ArgDict definition, so it's not the original user input. For simple
      # key_type/value_type functions like int() it's hopefully clear enough.
      # TODO(b/273284280): Maybe try to improve this.
      user_input = ', '.join([
          six.text_type(existing_value), six.text_type(new_value)])
    raise argparse.ArgumentError(
        self,
        _GenerateErrorMessage(
            '"{0}" cannot be specified multiple times'.format(key),
            user_input=user_input))

  def __init__(
      self,
      option_strings,
      dest,
      nargs=None,
      const=None,
      default=None,
      type=None,  # pylint:disable=redefined-builtin
      choices=None,
      required=False,
      help=None,  # pylint:disable=redefined-builtin
      metavar=None,
      onduplicatekey_handler=OnDuplicateKeyRaiseError):
    if nargs == 0:
      raise ValueError('nargs for append actions must be > 0; if arg '
                       'strings are not supplying the value to append, '
                       'the append const action may be more appropriate')
    if const is not None and nargs != argparse.OPTIONAL:
      raise ValueError('nargs must be %r to supply const' % argparse.OPTIONAL)
    self.choices = choices
    if isinstance(choices, dict):
      choices = sorted(choices.keys())
    super(UpdateAction, self).__init__(
        option_strings=option_strings,
        dest=dest,
        nargs=nargs,
        const=const,
        default=default,
        type=type,
        choices=choices,
        required=required,
        help=help,
        metavar=metavar)
    self.onduplicatekey_handler = onduplicatekey_handler

  def _EnsureValue(self, namespace, name, value):
    if getattr(namespace, name, None) is None:
      setattr(namespace, name, value)
    return getattr(namespace, name)

  # pylint: disable=protected-access
  def __call__(self, parser, namespace, values, option_string=None):

    if isinstance(values, dict):
      # Get the existing arg value (if any)
      items = copy.copy(
          self._EnsureValue(namespace, self.dest, collections.OrderedDict()))
      # Merge the new key/value pair(s) in
      for k, v in six.iteritems(values):
        if k in items:
          v = self.onduplicatekey_handler(self, k, items[k], v)
        items[k] = v
    else:
      # Get the existing arg value (if any)
      items = copy.copy(self._EnsureValue(namespace, self.dest, []))
      # Merge the new key/value pair(s) in
      for k in values:
        if k in items:
          self.onduplicatekey_handler(self, k)
        else:
          items.append(k)

    # Saved the merged dictionary
    setattr(namespace, self.dest, items)


class UpdateActionWithAppend(UpdateAction):
  """Create a single dict value from delimited or repeated flags.

  This class provides a variant of UpdateAction, which allows for users to
  append, rather than reject, duplicate key values. For example, the user
  can specify:

    --inputs k1=v1a --inputs k1=v1b --inputs k2=v2

  and the result will be:

     { 'k1': ['v1a', 'v1b'], 'k2': 'v2' }
  """

  def OnDuplicateKeyAppend(self, key, existing_value=None, new_value=None):
    if existing_value is None:
      return key
    elif isinstance(existing_value, list):
      return existing_value + [new_value]
    else:
      return [existing_value, new_value]

  def __init__(
      self,
      option_strings,
      dest,
      nargs=None,
      const=None,
      default=None,
      type=None,  # pylint:disable=redefined-builtin
      choices=None,
      required=False,
      help=None,  # pylint:disable=redefined-builtin
      metavar=None,
      onduplicatekey_handler=OnDuplicateKeyAppend):
    super(UpdateActionWithAppend, self).__init__(
        option_strings=option_strings,
        dest=dest,
        nargs=nargs,
        const=const,
        default=default,
        type=type,
        choices=choices,
        required=required,
        help=help,
        metavar=metavar,
        onduplicatekey_handler=onduplicatekey_handler)


class RemainderAction(argparse._StoreAction):  # pylint: disable=protected-access
  """An action with a couple of helpers to better handle --.

  argparse on its own does not properly handle -- implementation args.
  argparse.REMAINDER greedily steals valid flags before a --, and nargs='*' will
  bind to [] and not  parse args after --. This Action represents arguments to
  be passed through to a subcommand after --.

  Primarily, this Action provides two utility parsers to help a modified
  ArgumentParser parse -- properly.

  There is one additional property kwarg:
    example: A usage statement used to construct nice additional help.
  """

  def __init__(self, *args, **kwargs):
    if kwargs['nargs'] is not argparse.REMAINDER:
      raise ValueError('The RemainderAction should only be used when '
                       'nargs=argparse.REMAINDER.')

    # Create detailed help.
    self.explanation = (
        "The '--' argument must be specified between gcloud specific args on "
        'the left and {metavar} on the right.').format(
            metavar=kwargs['metavar'])
    if 'help' in kwargs:
      kwargs['help'] += '\n+\n' + self.explanation
      if 'example' in kwargs:
        kwargs['help'] += ' Example:\n\n' + kwargs['example']
        del kwargs['example']
    super(RemainderAction, self).__init__(*args, **kwargs)

  def _SplitOnDash(self, args):
    split_index = args.index('--')
    # Remove -- before passing through
    return args[:split_index], args[split_index + 1:]

  def ParseKnownArgs(self, args, namespace):
    """Binds all args after -- to the namespace."""
    # Not [], so that we can distinguish between empty remainder args and
    # absent remainder args.
    remainder_args = None
    if '--' in args:
      args, remainder_args = self._SplitOnDash(args)
    self(None, namespace, remainder_args)
    return namespace, args

  def ParseRemainingArgs(self, remaining_args, namespace, original_args):
    """Parses the unrecognized args from the end of the remaining_args.

    This method identifies all unrecognized arguments after the last argument
    recognized by a parser (but before --). It then either logs a warning and
    binds them to the namespace or raises an error, depending on strictness.

    Args:
      remaining_args: A list of arguments that the parsers did not recognize.
      namespace: The Namespace to bind to.
      original_args: The full list of arguments given to the top parser,

    Raises:
      ArgumentError: If there were remaining arguments after the last recognized
      argument and this action is strict.

    Returns:
      A tuple of the updated namespace and unrecognized arguments (before the
      last recognized argument).
    """
    # Only parse consecutive unknown args from the end of the original args.
    # Strip out everything after '--'
    if '--' in original_args:
      original_args, _ = self._SplitOnDash(original_args)
    # Find common suffix between remaining_args and original_args
    split_index = 0
    for i, (arg1, arg2) in enumerate(
        zip(reversed(remaining_args), reversed(original_args))):
      if arg1 != arg2:
        split_index = len(remaining_args) - i
        break
    pass_through_args = remaining_args[split_index:]
    remaining_args = remaining_args[:split_index]

    if pass_through_args:
      msg = ('unrecognized args: {args}\n' +
             self.explanation).format(args=' '.join(pass_through_args))
      raise parser_errors.UnrecognizedArgumentsError(msg)
    self(None, namespace, pass_through_args)
    return namespace, remaining_args


def FlattenAction(dedup=True):
  """Creates an action that concats flag values.

  Args:
    dedup: bool, determines whether values in generated list should be unique

  Returns:
    A custom argparse action that flattens the values before adding
    to namespace
  """

  class Action(argparse.Action):
    """Create a single list from delimited flags.

    For example, with the following flag defition:

        parser.add_argument(
            '--inputs',
            type=arg_parsers.ArgObject(repeated=True),
            action=FlattenAction(dedup=True))

    a caller can specify on the command line flags such as:

        --inputs '["v1", "v2"]' --inputs '["v3", "v4"]'

    and the result will be one list of non-repeating values:

        ["v1", "v2", "v3", "v4"]

    Recommend using this action with ArgObject where `repeated` is set to True.
    This allows users to set the list either with append action or with
    one json list. For example, all below examples result
    in ["v1", "v2", "v3", "v4"]

        1) --inputs v1 --inputs v2 --inputs v3 --inputs v4
        2) --inputs '["v1", "v2", "v3", "v4"]'
    """

    def __call__(self, parser, namespace, values, option_string=None):
      existing_values = getattr(namespace, self.dest, None)
      all_values = _ConcatList(existing_values, values)
      if dedup:
        # Cannot use a Set since apitools messages are not hashable
        deduped_values = []
        for value in all_values:
          if value not in deduped_values:
            deduped_values.append(value)
        all_values = deduped_values
      setattr(namespace, self.dest, all_values)

  return Action


class StoreOnceAction(argparse.Action):
  r"""Action that disallows repeating a flag.

  When using action='store' (the default), argparse allows multiple instances of
  a flag to be specified with the last one determining the value and the rest
  silently dropped. This is often undesirable if the command accepts only one
  value but users try to repeat the flag (either accidentally, or when
  mistakenly expecting the repeated values to be appended or merged somehow).

  In such cases, one can instead use StoreOnceAction which disallows specifying
  the same flag multiple times. So for instance, providing:

    --foo 123 --foo 456

  will result in an error stating that --foo cannot be specified more than once.
  """

  def OnSecondArgumentRaiseError(self):
    raise argparse.ArgumentError(
        self,
        _GenerateErrorMessage(
            '"{0}" argument cannot be specified multiple times'.format(
                self.dest)))

  def __init__(self, *args, **kwargs):
    self.dest_is_populated = False
    super(StoreOnceAction, self).__init__(*args, **kwargs)

  # pylint: disable=protected-access
  def __call__(self, parser, namespace, values, option_string=None):
    # Make sure no existing arg value exist
    if self.dest_is_populated:
      self.OnSecondArgumentRaiseError()
    self.dest_is_populated = True
    setattr(namespace, self.dest, values)


def StoreOnceWarningAction(flag_name):
  """Emits a warning message when a flag is specified more than once.

  The created action is similar to StoreOnceAction. The difference is that
  this action prints a warning message instead of raising an exception when the
  flag is specified more than once. Because it is a breaking change to switch an
  existing flag to StoreOnceAction, StoreOnceWarningAction can be used in the
  deprecation period.

  Args:
    flag_name: The name of the flag to apply this action on.

  Returns:
    An Action class.
  """

  class Action(argparse.Action):
    """Emits a warning message when a flag is specified more than once."""

    def OnSecondArgumentPrintWarning(self):
      log.warning(
          '"{0}" argument is specified multiple times which will be disallowed '
          'in future versions. Please only specify it once.'.format(flag_name))

    def __init__(self, *args, **kwargs):
      self.dest_is_populated = False
      super(Action, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
      # Make sure no existing arg value exist
      if self.dest_is_populated:
        self.OnSecondArgumentPrintWarning()
      self.dest_is_populated = True
      setattr(namespace, self.dest, values)

  return Action


class _HandleNoArgAction(argparse.Action):
  """This class should not be used directly, use HandleNoArgAction instead."""

  def __init__(self, none_arg, deprecation_message, **kwargs):
    super(_HandleNoArgAction, self).__init__(**kwargs)
    self.none_arg = none_arg
    self.deprecation_message = deprecation_message

  def __call__(self, parser, namespace, value, option_string=None):
    if value is None:
      log.warning(self.deprecation_message)
      if self.none_arg:
        setattr(namespace, self.none_arg, True)

    setattr(namespace, self.dest, value)


def HandleNoArgAction(none_arg, deprecation_message):
  """Creates an argparse.Action that warns when called with no arguments.

  This function creates an argparse action which can be used to gracefully
  deprecate a flag using nargs=?. When a flag is created with this action, it
  simply log.warning()s the given deprecation_message and then sets the value of
  the none_arg to True.

  This means if you use the none_arg no_foo and attach this action to foo,
  `--foo` (no argument), it will have the same effect as `--no-foo`.

  Args:
    none_arg: a boolean argument to write to. For --no-foo use "no_foo"
    deprecation_message: msg to tell user to stop using with no arguments.

  Returns:
    An argparse action.

  """

  def HandleNoArgActionInit(**kwargs):
    return _HandleNoArgAction(none_arg, deprecation_message, **kwargs)

  return HandleNoArgActionInit


class FileContents(object):
  """Creates an argparse type that reads the contents of a file or stdin.

  This is similar to argparse.FileType, but unlike FileType it does not leave
  a dangling file handle open. The argument stored in the argparse Namespace
  is the file's contents.

  Attributes:
    binary: bool, If True, the contents of the file will be returned as bytes.

  Returns:
    A function that accepts a filename, or "-" representing that stdin should be
    used as input.
  """

  def __init__(self, binary=False):
    self.binary = binary

  def __call__(self, name):
    """Return the contents of the file with the specified name.

    If name is "-", stdin is read until EOF. Otherwise, the named file is read.

    Args:
      name: str, The file name, or '-' to indicate stdin.

    Returns:
      The contents of the file.

    Raises:
      ArgumentTypeError: If the file cannot be read or is too large.
    """
    try:
      return console_io.ReadFromFileOrStdin(name, binary=self.binary)
    except files.Error as e:
      raise ArgumentTypeError(e)


class YAMLFileContents(object):
  """Creates an argparse type that reads the contents of a YAML or JSON file.

  This is similar to argparse.FileType, but unlike FileType it does not leave
  a dangling file handle open. The argument stored in the argparse Namespace
  is the file's contents parsed as a YAML object.

  Attributes:
    validator: function, Function that will validate the provided input file
      contents.

  Returns:
    A function that accepts a filename that should be parsed as a YAML
    or JSON file.
  """

  def __init__(self, validator=None):
    if validator and not callable(validator):
      raise ArgumentTypeError('Validator must be callable')
    self.validator = validator

  def _AssertJsonLike(self, yaml_data):
    if not (yaml.dict_like(yaml_data) or yaml.list_like(yaml_data)):
      raise ArgumentTypeError('Invalid YAML/JSON Data [{}]'.format(yaml_data))

  def _LoadSingleYamlDocument(self, name):
    """Returns the yaml data for a file or from stdin for a single document.

    YAML allows multiple documents in a single file by using `---` as a
    separator between documents. See https://yaml.org/spec/1.1/#id857577.
    However, some YAML-generating tools generate a single document followed by
    this separator before ending the file.

    This method supports the case of a single document in a file that contains
    superfluous document separators, but still throws if multiple documents are
    actually found.

    Args:
      name: str, The file path to the file or "-" to read from stdin.

    Returns:
      The contents of the file parsed as a YAML data object.
    """
    if name == '-':
      stdin = console_io.ReadStdin()  # Save to potentially reuse below
      yaml_data = yaml.load_all(stdin)
    else:
      yaml_data = yaml.load_all_path(name)
    yaml_data = [d for d in yaml_data if d is not None]  # Remove empty docs

    # Return the single document if only 1 is found.
    if len(yaml_data) == 1:
      return yaml_data[0]

    # Multiple (or 0) documents found. Try to parse again with single-document
    # loader so its error is propagated rather than creating our own.
    if name == '-':
      return yaml.load(stdin)
    else:
      return yaml.load_path(name)

  def __call__(self, name):
    """Load YAML data from file path (name) or stdin.

    If name is "-", stdin is read until EOF. Otherwise, the named file is read.
    If self.validator is set, call it on the yaml data once it is loaded.

    Args:
      name: str, The file path to the file.

    Returns:
      The contents of the file parsed as a YAML data object.

    Raises:
      ArgumentTypeError: If the file cannot be read or is not a JSON/YAML like
        object.
      ValueError: If file content fails validation.
    """
    try:
      yaml_data = self._LoadSingleYamlDocument(name)
      self._AssertJsonLike(yaml_data)
      if self.validator:
        if not self.validator(yaml_data):
          raise ValueError('Invalid YAML/JSON content [{}]'.format(yaml_data))

      return yaml_data

    except (yaml.YAMLParseError, yaml.FileLoadError) as e:
      raise ArgumentTypeError(e)


class StoreTrueFalseAction(argparse._StoreTrueAction):  # pylint: disable=protected-access
  """Argparse action that acts as a combination of store_true and store_false.

  Calliope already gives any bool-type arguments the standard and `--no-`
  variants. In most cases we only want to document the option that does
  something---if we have `default=False`, we don't want to show `--no-foo`,
  since it won't do anything.

  But in some cases we *do* want to show both variants: one example is when
  `--foo` means "enable," `--no-foo` means "disable," and neither means "do
  nothing." The obvious way to represent this is `default=None`; however, (1)
  the default value of `default` is already None, so most boolean actions would
  have this setting by default (not what we want), and (2) we still want an
  option to have this True/False/None behavior *without* the flag documentation.

  To get around this, we have an opt-in version of the same thing that documents
  both the flag and its inverse.
  """

  def __init__(self, *args, **kwargs):
    super(StoreTrueFalseAction, self).__init__(*args, default=None, **kwargs)


def StoreFilePathAndContentsAction(binary=False):
  """Returns Action that stores both file content and file path.

  Args:
   binary: boolean, whether or not this is a binary file.

  Returns:
   An argparse action.
  """

  class Action(argparse.Action):
    """Stores both file content and file path.

      Stores file contents under original flag DEST and stores file path under
      DEST_path.
    """

    def __init__(self, *args, **kwargs):
      super(Action, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
      """Stores the contents of the file and the file name in namespace."""
      try:
        content = console_io.ReadFromFileOrStdin(value, binary=binary)
      except files.Error as e:
        raise ArgumentTypeError(e)
      setattr(namespace, self.dest, content)
      new_dest = '{}_path'.format(self.dest)
      setattr(namespace, new_dest, value)

  return Action


class ExtendConstAction(argparse.Action):
  """Extends the dest arg with a constant list."""

  def __init__(self, *args, **kwargs):
    super(ExtendConstAction, self).__init__(*args, nargs=0, **kwargs)

  def __call__(self, parser, namespace, value, option_string=None):
    """Extends the dest with the const list."""
    cur = getattr(self, self.dest, [])
    setattr(namespace, self.dest, cur + self.const)


class FilePathOrStdinContents(object):
  """Creates an argparse type that stores a file path or the contents of stdin.

  This is similar to FileContents above but only reads content from stdin,
  otherwise just stores the file/directory path.

  Attributes:
    binary: bool, If True, the contents of the file will be returned as bytes.

  Returns:
    A function that accepts a filename, or "-" representing that stdin should be
    used as input.
  """

  def __init__(self, binary=False):
    self.binary = binary

  def __call__(self, name):
    """Return the contents of stdin or the filepath specified.

    If name is "-", stdin is read until EOF. Otherwise, the named file path is
    returned.

    Args:
      name: str, The file name, or '-' to indicate stdin.

    Returns:
      The contents of stdin or the file path.

    Raises:
      ArgumentTypeError: If stdin cannot be read or is too large.
    """
    try:
      if name == '-':
        return console_io.ReadFromFileOrStdin(name, binary=self.binary)
      return files.ExpandHomeAndVars(name)
    except files.Error as e:
      raise ArgumentTypeError(e)
