#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
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
#
"""Common utility library."""
from __future__ import with_statement

import datetime
import functools
import inspect
import logging
import os
import re
import sys

import six

__all__ = [
    'Error',
    'decode_datetime',
    'get_package_for_module',
    'positional',
    'TimeZoneOffset',
    'total_seconds',
]


class Error(Exception):
    """Base class for protorpc exceptions."""


_TIME_ZONE_RE_STRING = r"""
  # Examples:
  #   +01:00
  #   -05:30
  #   Z12:00
  ((?P<z>Z) | (?P<sign>[-+])
   (?P<hours>\d\d) :
   (?P<minutes>\d\d))$
"""
_TIME_ZONE_RE = re.compile(_TIME_ZONE_RE_STRING, re.IGNORECASE | re.VERBOSE)


def positional(max_positional_args):
    """A decorator that declares only the first N arguments may be positional.

    This decorator makes it easy to support Python 3 style keyword-only
    parameters. For example, in Python 3 it is possible to write:

      def fn(pos1, *, kwonly1=None, kwonly1=None):
        ...

    All named parameters after * must be a keyword:

      fn(10, 'kw1', 'kw2')  # Raises exception.
      fn(10, kwonly1='kw1')  # Ok.

    Example:
      To define a function like above, do:

        @positional(1)
        def fn(pos1, kwonly1=None, kwonly2=None):
          ...

      If no default value is provided to a keyword argument, it
      becomes a required keyword argument:

        @positional(0)
        def fn(required_kw):
          ...

      This must be called with the keyword parameter:

        fn()  # Raises exception.
        fn(10)  # Raises exception.
        fn(required_kw=10)  # Ok.

      When defining instance or class methods always remember to account for
      'self' and 'cls':

        class MyClass(object):

          @positional(2)
          def my_method(self, pos1, kwonly1=None):
            ...

          @classmethod
          @positional(2)
          def my_method(cls, pos1, kwonly1=None):
            ...

      One can omit the argument to 'positional' altogether, and then no
      arguments with default values may be passed positionally. This
      would be equivalent to placing a '*' before the first argument
      with a default value in Python 3. If there are no arguments with
      default values, and no argument is given to 'positional', an error
      is raised.

        @positional
        def fn(arg1, arg2, required_kw1=None, required_kw2=0):
          ...

        fn(1, 3, 5)  # Raises exception.
        fn(1, 3)  # Ok.
        fn(1, 3, required_kw1=5)  # Ok.

    Args:
      max_positional_arguments: Maximum number of positional arguments.  All
        parameters after the this index must be keyword only.

    Returns:
      A decorator that prevents using arguments after max_positional_args from
      being used as positional parameters.

    Raises:
      TypeError if a keyword-only argument is provided as a positional
        parameter.
      ValueError if no maximum number of arguments is provided and the function
        has no arguments with default values.
    """
    def positional_decorator(wrapped):
        """Creates a function wraper to enforce number of arguments."""
        @functools.wraps(wrapped)
        def positional_wrapper(*args, **kwargs):
            if len(args) > max_positional_args:
                plural_s = ''
                if max_positional_args != 1:
                    plural_s = 's'
                raise TypeError('%s() takes at most %d positional argument%s '
                                '(%d given)' % (wrapped.__name__,
                                                max_positional_args,
                                                plural_s, len(args)))
            return wrapped(*args, **kwargs)
        return positional_wrapper

    if isinstance(max_positional_args, six.integer_types):
        return positional_decorator
    else:
        args, _, _, defaults = inspect.getargspec(max_positional_args)
        if defaults is None:
            raise ValueError(
                'Functions with no keyword arguments must specify '
                'max_positional_args')
        return positional(len(args) - len(defaults))(max_positional_args)


@positional(1)
def get_package_for_module(module):
    """Get package name for a module.

    Helper calculates the package name of a module.

    Args:
      module: Module to get name for.  If module is a string, try to find
        module in sys.modules.

    Returns:
      If module contains 'package' attribute, uses that as package name.
      Else, if module is not the '__main__' module, the module __name__.
      Else, the base name of the module file name.  Else None.
    """
    if isinstance(module, six.string_types):
        try:
            module = sys.modules[module]
        except KeyError:
            return None

    try:
        return six.text_type(module.package)
    except AttributeError:
        if module.__name__ == '__main__':
            try:
                file_name = module.__file__
            except AttributeError:
                pass
            else:
                base_name = os.path.basename(file_name)
                split_name = os.path.splitext(base_name)
                if len(split_name) == 1:
                    return six.text_type(base_name)
                return u'.'.join(split_name[:-1])

        return six.text_type(module.__name__)


def total_seconds(offset):
    """Backport of offset.total_seconds() from python 2.7+."""
    seconds = offset.days * 24 * 60 * 60 + offset.seconds
    microseconds = seconds * 10**6 + offset.microseconds
    return microseconds / (10**6 * 1.0)


class TimeZoneOffset(datetime.tzinfo):
    """Time zone information as encoded/decoded for DateTimeFields."""

    def __init__(self, offset):
        """Initialize a time zone offset.

        Args:
          offset: Integer or timedelta time zone offset, in minutes from UTC.
            This can be negative.
        """
        super(TimeZoneOffset, self).__init__()
        if isinstance(offset, datetime.timedelta):
            offset = total_seconds(offset) / 60
        self.__offset = offset

    def utcoffset(self, _):
        """Get the a timedelta with the time zone's offset from UTC.

        Returns:
          The time zone offset from UTC, as a timedelta.
        """
        return datetime.timedelta(minutes=self.__offset)

    def dst(self, _):
        """Get the daylight savings time offset.

        The formats that ProtoRPC uses to encode/decode time zone
        information don't contain any information about daylight
        savings time. So this always returns a timedelta of 0.

        Returns:
          A timedelta of 0.

        """
        return datetime.timedelta(0)


def decode_datetime(encoded_datetime, truncate_time=False):
    """Decode a DateTimeField parameter from a string to a python datetime.

    Args:
      encoded_datetime: A string in RFC 3339 format.
      truncate_time: If true, truncate time string with precision higher than
          microsecs.

    Returns:
      A datetime object with the date and time specified in encoded_datetime.

    Raises:
      ValueError: If the string is not in a recognized format.
    """
    # Check if the string includes a time zone offset.  Break out the
    # part that doesn't include time zone info.  Convert to uppercase
    # because all our comparisons should be case-insensitive.
    time_zone_match = _TIME_ZONE_RE.search(encoded_datetime)
    if time_zone_match:
        time_string = encoded_datetime[:time_zone_match.start(1)].upper()
    else:
        time_string = encoded_datetime.upper()

    if '.' in time_string:
        format_string = '%Y-%m-%dT%H:%M:%S.%f'
    else:
        format_string = '%Y-%m-%dT%H:%M:%S'

    try:
        decoded_datetime = datetime.datetime.strptime(time_string,
                                                      format_string)
    except ValueError:
        if truncate_time and '.' in time_string:
            datetime_string, decimal_secs = time_string.split('.')
            if len(decimal_secs) > 6:
                # datetime can handle only microsecs precision.
                truncated_time_string = '{}.{}'.format(
                    datetime_string, decimal_secs[:6])
                decoded_datetime = datetime.datetime.strptime(
                    truncated_time_string,
                    format_string)
                logging.warning(
                    'Truncating the datetime string from %s to %s',
                    time_string, truncated_time_string)
            else:
                raise
        else:
            raise

    if not time_zone_match:
        return decoded_datetime

    # Time zone info was included in the parameter.  Add a tzinfo
    # object to the datetime.  Datetimes can't be changed after they're
    # created, so we'll need to create a new one.
    if time_zone_match.group('z'):
        offset_minutes = 0
    else:
        sign = time_zone_match.group('sign')
        hours, minutes = [int(value) for value in
                          time_zone_match.group('hours', 'minutes')]
        offset_minutes = hours * 60 + minutes
        if sign == '-':
            offset_minutes *= -1

    return datetime.datetime(decoded_datetime.year,
                             decoded_datetime.month,
                             decoded_datetime.day,
                             decoded_datetime.hour,
                             decoded_datetime.minute,
                             decoded_datetime.second,
                             decoded_datetime.microsecond,
                             TimeZoneOffset(offset_minutes))
