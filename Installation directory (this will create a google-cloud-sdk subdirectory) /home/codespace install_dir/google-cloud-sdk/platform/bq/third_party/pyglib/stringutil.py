#!/usr/bin/env python
# Copyright 2003 Google, Inc.
# All Rights Reserved.

"""Some common string manipulation utilities."""
import base64
import binascii
import re
import string

import six

# NOTE: These are re-exported to allow their use within google3 without the need
# to depend on the visibility-restricted //third_party/py/six target.
ensure_str = six.ensure_str
ensure_binary = six.ensure_binary

_RE_NONASCII = re.compile(r'[^\000-\177]')

# Java Language Specification: Escape Sequences for Char and String Literals
# https://docs.oracle.com/javase/tutorial/java/data/characters.html
_JAVA_ESCAPE_MAP = {
    '\b': '\\b',
    '\t': '\\t',
    '\n': '\\n',
    '\f': '\\f',
    '\r': '\\r',
    '"': '\\"',
    "'": "\\'",
    '\\': '\\\\',
}
# Octal-escape unprintable characters
#
# Since stringutil.JavaEscape calls stringutil.UnicodeEscape for all input
# byte values outside of [0-128), we simply fill the escape map with valid
# ASCII characters (i.e., [0,128)) and rely on UnicodeEscape to handle the
# rest.
for i in range(128):
  c = chr(i)
  if c not in _JAVA_ESCAPE_MAP and c not in string.printable:
    _JAVA_ESCAPE_MAP[c] = '\\%03o' % i
# Compile characters-to-be-escaped into regex for matching
_JAVA_ESCAPE_RE = re.compile('|'.join(
    [re.escape(c) for c in _JAVA_ESCAPE_MAP.keys()]))

_COMMON_TRUE_STRINGS = frozenset(('true', 't', '1', 'yes', 'y'))
_COMMON_FALSE_STRINGS = frozenset(('false', 'f', '0', 'no', 'n'))


class Base64ValueError(Exception): "Illegal Base64-encoded value"


def UnicodeEscape(s):
  r"""Replaces each non-ASCII character in s with an escape sequence.

  Non-ASCII characters are substituted with their 6-character unicode
  escape sequence \uxxxx, where xxxx is a hex number.  The resulting
  string consists entirely of ASCII characters.  Existing escape
  sequences are unaffected, i.e., this operation is idempotent.

  Sample usage:
    >>> UnicodeEscape('asdf\xff')
    'asdf\\u00ff'

  This escaping differs from the built-in s.encode('unicode_escape').  The
  built-in escape function uses hex escape sequences (e.g., '\xe9') and escapes
  some control characters in lower ASCII (e.g., '\x00').

  Args:
    s: string to be escaped

  Returns:
    escaped string
  """
  return _RE_NONASCII.sub(lambda m: '\\u%04x' % ord(m.group(0)), s)


def JavaEscape(s):
  r"""Escapes a string so it can be inserted in a Java string or char literal.

  Follows the Java Language Specification for "Escape Sequences for Character
  and String Literals":

  https://docs.oracle.com/javase/tutorial/java/data/characters.html

  Escapes unprintable and non-ASCII characters.  The resulting string consists
  entirely of ASCII characters.

  This operation is NOT idempotent.

  Sample usage:
    >>> JavaEscape('single\'double"\n\x00')
    'single\\\'double\\"\\n\\000'

  Args:
    s: string to be escaped

  Returns:
    escaped string
  """
  s_esc = _JAVA_ESCAPE_RE.sub(lambda m: _JAVA_ESCAPE_MAP[m.group(0)], s)
  # Unicode-escape remaining non-ASCII characters.  In the default Python
  # locale, printable characters are all ASCII, and we octal-escaped all
  # unprintable characters above, so this step actually does nothing.  Leave it
  # in for locales that have non-ASCII printable characters.
  return UnicodeEscape(s_esc)


# FYI, Python 2.4's base64 module has a websafe encode/decode. However:
#
# (1) The encode still appends =-padding. Even more annoying,
# (2) The decode still *requires* that =-padding be present. This makes it
# incompatible with the C++ or Sawzall (based on the C++) implementations.
# (3) On decode, the handling of invalid characters varies (both versions ignore
# whitespace, otherwise the C++ version fails, the Python version ignores
# invalid characters).
def WebSafeBase64Escape(unescaped, do_padding):
  """Python implementation of the Google C library's WebSafeBase64Escape().

  Python implementation of the Google C library's WebSafeBase64Escape() (from
  strings/strutil.h), using Python's base64 API and string replacement.

  Args:
    unescaped: any data (byte) string (example: b"12345~6")
    do_padding: whether to add =-padding (example: false)

  Returns:
    The base64 encoding (with web-safe replacements) of unescaped,
    with =-padding depending on the value of do_padding
    (example: b"MTIzNDV-Ng")
  """
  escaped = base64.urlsafe_b64encode(unescaped)

  if not do_padding:
    escaped = escaped.rstrip(b'=')

  return escaped

# Mapping table to convert web-safe base64 encoding to the standard
# encoding ('-' becomes '+', '_' becomes '/', and other valid base64
# input characters map to themselves).  To maintain compatibility with
# the C++ library, characters that are neither valid base64 input
# characters nor whitespace are mapped to '!'.

_BASE64_DECODE_TRANSLATION = (
    b'!!!!!!!!!     !!!!!!!!!!!!!!!!!!'
    b' !!!!!!!!!!!!+!!0123456789!!!=!!'
    b'!ABCDEFGHIJKLMNOPQRSTUVWXYZ!!!!/'
    b'!abcdefghijklmnopqrstuvwxyz!!!!!'
    b'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    b'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    b'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    b'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')


def WebSafeBase64Unescape(escaped):
  """Python implementation of the Google C library's WebSafeBase64Unescape().

  Python implementation of the Google C library's WebSafeBase64Unescape() (from
  strings/strutil.h), using Python's base64 API and string replacement.

  Args:
    escaped: A base64 binary string using the web-safe encoding
        (example: b"MTIzNDV-Ng")

  Returns:
    The corresponding unescaped string (example: b"12345~6")

  Raises:
    Base64ValueError: Invalid character in encoding of string, escaped.
  """
  escaped_standard = escaped.translate(_BASE64_DECODE_TRANSLATION)
  if escaped_standard.find(b'!') >= 0:
    raise Base64ValueError('%r: Invalid character in encoded string.' % escaped)

  # Make the encoded string a multiple of 4 characters long, adding "="
  # characters as padding.  This is the format standard base64 expects.
  if not escaped_standard.endswith(b'='):
    padding_len = len(escaped_standard) % 4
    escaped_standard += b'=' * padding_len

  try:
    return binascii.a2b_base64(escaped_standard)

  except binascii.Error as msg:
    raise Base64ValueError('%r: %s' % (escaped, msg))


def Chunk(value, size, start=0):
  """Break a string into chunks of a given size.

  Args:
    value: The value to split.
    size: The maximum size of a chunk.
    start: The index at which to start (defaults to 0).

  Returns:
    Iterable over string slices of as close to the given size as possible.
    Chunk('hello', 2) => 'he', 'll', 'o'

  Raises:
    ValueError: If start < 0 or if size <= 0.
  """
  if start < 0:
    raise ValueError('invalid starting position')
  if size <= 0:
    raise ValueError('invalid chunk size')
  return (value[i:i + size] for i in range(start, len(value), size))


def ReverseChunk(value, size):
  """Break a string into chunks of a given size, starting at the rear.

  Like chunk, except the smallest chunk comes at the beginning.

  Args:
    value: The value to split.
    size: The maximum size of a chunk.

  Returns:
    Iterable over string slices of as close to the given size as possible.
    ReverseChunk('hello', 2) => 'h', 'el', 'lo'

  Raises:
    ValueError: If size <= 0.
  """
  # Check at call, to raise the error as soon as possible, rather than
  # on the first .next()
  if size <= 0:
    raise ValueError('invalid chunk size')

  def DoChunk():
    """Actually perform the chunking."""
    start = 0
    # special-case the first chunk, so that the smallest
    # chunk comes first
    if len(value) % size:
      yield value[:len(value) % size]
      start = len(value) % size
    for chunk in Chunk(value, size, start=start):
      yield chunk
  return DoChunk()


def IsCommonTrue(value):
  """Checks if the string is a commonly accepted True value.

  Useful if you want most strings to default to False except a few
  accepted values.  This method is case-insensitive.

  Args:
    value: The string to check for true.  Or None.

  Returns:
    True if the string is one of the commonly accepted true values.
    False if value is None.  False otherwise.

  Raises:
    ValueError: when value is something besides a string or None.
  """
  if value is None:
    return False
  if not isinstance(value, str):
    raise ValueError('IsCommonTrue() called with %s type.  Expected string.'
                     % type(value))
  if value:
    return value.strip().lower() in _COMMON_TRUE_STRINGS
  return False


def IsCommonFalse(value):
  """Checks if the string is a commonly accepted False value.

  Useful if you want most strings to default to True except a few
  accepted values.  This method is case-insensitive.

  Args:
    value: The string to check for true.  Or None.

  Returns:
    True if the string is one of the commonly accepted false values.
    True if value is None.  False otherwise.

  Raises:
    ValueError: when value is something besides a string or None.
  """
  if value is None:
    return True
  if not isinstance(value, str):
    raise ValueError('IsCommonFalse() called with %s type.  Expected string.'
                     % type(value))
  if value:
    return value.strip().lower() in _COMMON_FALSE_STRINGS
  return True
