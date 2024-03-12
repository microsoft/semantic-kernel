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
"""Shared utility structures and methods for manipulating text."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import binascii
import codecs
import os
import sys
import io
import re
import locale
import collections
import random
import six
import string
from six.moves import urllib
from six.moves import range

from gslib.exception import CommandException
from gslib.lazy_wrapper import LazyWrapper
from gslib.utils.constants import UTF8
from gslib.utils.constants import WINDOWS_1252
from gslib.utils.system_util import IS_CP1252

if six.PY3:
  long = int

STORAGE_CLASS_SHORTHAND_TO_FULL_NAME = {
    # Values should remain uppercase, as required by non-gs providers.
    'CL': 'COLDLINE',
    'DRA': 'DURABLE_REDUCED_AVAILABILITY',
    'NL': 'NEARLINE',
    'S': 'STANDARD',
    'STD': 'STANDARD',
    'A': 'ARCHIVE',
}

VERSION_MATCHER = LazyWrapper(
    lambda: re.compile(r'^(?P<maj>\d+)(\.(?P<min>\d+)(?P<suffix>.*))?'))


def AddQueryParamToUrl(url_str, param_name, param_value):
  """Adds a query parameter to a URL string.

  Appends a query parameter to the query string portion of a url. If a parameter
  with the given name was already present, it is not removed; the new name/value
  pair will be appended to the end of the query string. It is assumed that all
  arguments will be of type `str` (either ASCII or UTF-8 encoded) or `unicode`.

  Note that this method performs no URL-encoding. It is the caller's
  responsibility to ensure proper URL encoding of the entire URL; i.e. if the
  URL is already URL-encoded, you should pass in URL-encoded values for
  param_name and param_value. If the URL is not URL-encoded, you should not pass
  in URL-encoded parameters; instead, you could perform URL-encoding using the
  URL string returned from this function.

  Args:
    url_str: (str or unicode) String representing the URL.
    param_name: (str or unicode) String key of the query parameter.
    param_value: (str or unicode) String value of the query parameter.

  Returns:
    (str or unicode) A string representing the modified url, of type `unicode`
    if the url_str argument was a `unicode`, otherwise a `str` encoded in UTF-8.
  """
  scheme, netloc, path, query_str, fragment = urllib.parse.urlsplit(url_str)

  query_params = urllib.parse.parse_qsl(query_str, keep_blank_values=True)
  query_params.append((param_name, param_value))
  new_query_str = '&'.join(['%s=%s' % (k, v) for (k, v) in query_params])

  new_url = urllib.parse.urlunsplit(
      (scheme, netloc, path, new_query_str, fragment))
  return new_url


def CompareVersions(first, second):
  """Compares the first and second gsutil version strings.

  For example, 3.33 > 3.7, and 4.1 is a greater major version than 3.33.
  Does not handle multiple periods (e.g. 3.3.4) or complicated suffixes
  (e.g., 3.3RC4 vs. 3.3RC5). A version string with a suffix is treated as
  less than its non-suffix counterpart (e.g. 3.32 > 3.32pre).

  Args:
    first: First gsutil version string.
    second: Second gsutil version string.

  Returns:
    (g, m):
       g is True if first known to be greater than second, else False.
       m is True if first known to be greater by at least 1 major version,
         else False.
  """
  m1 = VERSION_MATCHER().match(str(first))
  m2 = VERSION_MATCHER().match(str(second))

  # If passed strings we don't know how to handle, be conservative.
  if not m1 or not m2:
    return (False, False)

  major_ver1 = int(m1.group('maj'))
  minor_ver1 = int(m1.group('min')) if m1.group('min') else 0
  suffix_ver1 = m1.group('suffix')
  major_ver2 = int(m2.group('maj'))
  minor_ver2 = int(m2.group('min')) if m2.group('min') else 0
  suffix_ver2 = m2.group('suffix')

  if major_ver1 > major_ver2:
    return (True, True)
  elif major_ver1 == major_ver2:
    if minor_ver1 > minor_ver2:
      return (True, False)
    elif minor_ver1 == minor_ver2:
      return (bool(suffix_ver2) and not suffix_ver1, False)
  return (False, False)


def ConvertRecursiveToFlatWildcard(url_strs):
  """A generator that adds '**' to each url string in url_strs."""
  for url_str in url_strs:
    yield '%s**' % url_str


def DecodeLongAsString(long_to_convert):
  """Decodes an encoded python long into an ASCII string.

  This is used for modeling S3 version_id's as apitools generation.

  Args:
    long_to_convert: long to convert to ASCII string. If this is already a
                     string, it is simply returned.

  Returns:
    String decoded from the input long.
  """
  unhexed = binascii.unhexlify(hex(long_to_convert)[2:].rstrip('L'))
  return six.ensure_str(unhexed)


def EncodeStringAsLong(string_to_convert):
  """Encodes an ASCII string as a python long.

  This is used for modeling S3 version_id's as apitools generation.  Because
  python longs can be arbitrarily large, this works.

  Args:
    string_to_convert: ASCII string to convert to a long.

  Returns:
    Long that represents the input string.
  """
  hex_bytestr = codecs.encode(six.ensure_binary(string_to_convert), 'hex_codec')
  # Note that `long`/`int` accepts either `bytes` or `unicode` as the
  # first arg in both py2 and py3:
  return long(hex_bytestr, 16)


def FixWindowsEncodingIfNeeded(input_str):
  """Attempts to detect Windows CP1252 encoding and convert to UTF8.

  Windows doesn't provide a way to set UTF-8 for string encodings; you can set
  the system locale (see
  http://windows.microsoft.com/en-us/windows/change-system-locale#1TC=windows-7)
  but that takes you to a "Change system locale" dropdown that just lists
  languages (e.g., "English (United States)". Instead, we're forced to check if
  a encoding as UTF8 raises an exception and if so, try converting from CP1252
  to Unicode.

  Args:
    input_str: (str or bytes) The input string.
  Returns:
    (unicode) The converted string or the original, if conversion wasn't needed.
  """
  if IS_CP1252:
    return six.ensure_text(input_str, WINDOWS_1252)
  else:
    return six.ensure_text(input_str, UTF8)


def GetPrintableExceptionString(exc):
  """Returns a short Unicode string describing the exception."""
  return six.text_type(exc).encode(UTF8) or six.text_type(exc.__class__)


def InsistAscii(string, message):
  """Ensures that the string passed in consists of only ASCII values.

  Args:
    string: Union[str, unicode, bytes] Text that will be checked for
        ASCII values.
    message: Union[str, unicode, bytes] Error message, passed into the
        exception, in the event that the check on `string` fails.

  Returns:
    None

  Raises:
    CommandException
  """
  if not all(ord(c) < 128 for c in string):
    raise CommandException(message)


def InsistAsciiHeader(header):
  """Checks for ASCII-only characters in `header`.

    Also constructs an error message using `header` if the check fails.

    Args:
      header: Union[str, binary, unicode] Text being checked for ASCII values.

    Returns:
      None
    """
  InsistAscii(header, 'Invalid non-ASCII header (%s).' % header)


def InsistAsciiHeaderValue(header, value):
  """Checks for ASCII-only characters in `value`.

  Also constructs an error message using `header` and `value` if the check
  fails.

  Args:
    header: Header name, only used in error message in case of an exception.
    value: Union[str, binary, unicode] Text being checked for ASCII values.

  Returns:
    None
  """
  InsistAscii(
      value,
      'Invalid non-ASCII value (%s) was provided for header %s.\nOnly ASCII '
      'characters are allowed in headers other than x-goog-meta- and '
      'x-amz-meta- headers' % (repr(value), header))


def InsistOnOrOff(value, message):
  """Ensures that the value passed in consists of only "on" or "off"

  Args:
    value: (unicode) Unicode string that will be checked for correct text.
    message: Union[str, unicode, bytes] Error message passed into the exception
        in the event that the check on value fails.

  Returns:
    None

  Raises:
    CommandException
  """
  if value != 'on' and value != 'off':
    raise CommandException(message)


def NormalizeStorageClass(sc):
  """Returns a normalized form of the given storage class name.

  Converts the given string to uppercase and expands valid abbreviations to
  full storage class names (e.g 'std' would return 'STANDARD'). Note that this
  method does not check if the given storage class is valid.

  Args:
    sc: (str) String representing the storage class's full name or abbreviation.

  Returns:
    (str) A string representing the full name of the given storage class.
  """
  # Use uppercase; storage class argument for the S3 API must be uppercase,
  # and it's case-insensitive for GS APIs.
  sc = sc.upper()
  if sc in STORAGE_CLASS_SHORTHAND_TO_FULL_NAME:
    sc = STORAGE_CLASS_SHORTHAND_TO_FULL_NAME[sc]
  return sc


def PrintableStr(input_val):
  """Return an UTF8-encoded string type, or None if `input_val` is None.

  Args:
    input_val: (unicode, str, or None) A string-like object or None. This method
        simply calls encode() on `input_val` if it is not None; if `input_val`
        is not of type "unicode", this will implicitly call decode() with the
        default encoding for strings (for Python 2, this is ASCII), then call
        encode().

  Returns:
    (str) A UTF-8 encoded string, or None.
  """
  return input_val


def print_to_fd(*objects, **kwargs):
  """A Python 2/3 compatible analogue to the print function.

  This function writes text to a file descriptor as the
  builtin print function would, favoring unicode encoding.

  Aguments and return values are the same as documented in
  the Python 2 print function.
  """

  def _get_args(**kwargs):
    """Validates keyword arguments that would be used in Print

    Valid keyword arguments, mirroring print(), are 'sep',
    'end', and 'file'. These must be of types string, string,
    and file / file interface respectively.

    Returns the above kwargs of the above types.
    """
    expected_keywords = collections.OrderedDict([('sep', ' '), ('end', '\n'),
                                                 ('file', sys.stdout)])

    for key, value in kwargs.items():
      if key not in expected_keywords:
        error_msg = ('{} is not a valid keyword argument. '
                     'Please use one of: {}')
        raise KeyError(error_msg.format(key,
                                        ' '.join(expected_keywords.keys())))
      else:
        expected_keywords[key] = value

    return expected_keywords.values()

  def _get_byte_strings(*objects):
    """Gets a `bytes` string for each item in a list of printable objects."""
    byte_objects = []
    for item in objects:
      if not isinstance(item, (six.binary_type, six.text_type)):
        # If the item wasn't bytes or unicode, its __str__ method
        # should return one of those types.
        item = str(item)

      if isinstance(item, six.binary_type):
        byte_objects.append(item)
      else:
        # The item should be unicode. If it's not, ensure_binary()
        # will throw a TypeError.
        byte_objects.append(six.ensure_binary(item))
    return byte_objects

  sep, end, file = _get_args(**kwargs)
  sep = six.ensure_binary(sep)
  end = six.ensure_binary(end)
  data = _get_byte_strings(*objects)
  data = sep.join(data)
  data += end
  write_to_fd(file, data)


def write_to_fd(fd, data):
  """Write given data to given file descriptor, doing any conversions needed"""
  if six.PY2:
    fd.write(data)
    return
  # PY3 logic:
  if isinstance(data, bytes):
    if (hasattr(fd, 'mode') and 'b' in fd.mode) or isinstance(fd, io.BytesIO):
      fd.write(data)
    elif hasattr(fd, 'buffer'):
      fd.buffer.write(data)
    else:
      fd.write(six.ensure_text(data))
  elif 'b' in fd.mode:
    fd.write(six.ensure_binary(data))
  else:
    fd.write(data)


def RemoveCRLFFromString(input_str):
  r"""Returns the input string with all \n and \r removed."""
  return re.sub(r'[\r\n]', '', input_str)


def get_random_ascii_chars(size, seed=0):
  """Generates binary string representation of a list of ASCII characters.

  Args:
    size: Integer quantity of characters to generate.
    seed: A seed may be specified for deterministic behavior.
          Int 0 is used as the default value.

  Returns:
    Binary encoded string representation of a list of characters of length
    equal to size argument.
  """
  random.seed(seed)
  contents = str([random.choice(string.ascii_letters) for _ in range(size)])
  contents = six.ensure_binary(contents)
  random.seed()  # Reset the seed for any other tests.
  return contents
