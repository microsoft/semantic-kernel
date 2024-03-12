# -*- coding: utf-8 -*- #

# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A module for dealing with unknown string and environment encodings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

import six


def Encode(string, encoding=None):
  """Encode the text string to a byte string.

  Args:
    string: str, The text string to encode.
    encoding: The suggested encoding if known.

  Returns:
    str, The binary string.
  """
  if string is None:
    return None
  if not six.PY2:
    # In Python 3, the environment sets and gets accept and return text strings
    # only, and it handles the encoding itself so this is not necessary.
    return string
  if isinstance(string, six.binary_type):
    # Already an encoded byte string, we are done
    return string

  encoding = encoding or _GetEncoding()
  return string.encode(encoding)


def Decode(data, encoding=None):
  """Returns string with non-ascii characters decoded to UNICODE.

  UTF-8, the suggested encoding, and the usual suspects will be attempted in
  order.

  Args:
    data: A string or object that has str() and unicode() methods that may
      contain an encoding incompatible with the standard output encoding.
    encoding: The suggested encoding if known.

  Returns:
    A text string representing the decoded byte string.
  """
  if data is None:
    return None

  # First we are going to get the data object to be a text string.
  # Don't use six.string_types here because on Python 3 bytes is not considered
  # a string type and we want to include that.
  if isinstance(data, six.text_type) or isinstance(data, six.binary_type):
    string = data
  else:
    # Some non-string type of object.
    try:
      string = six.text_type(data)
    except (TypeError, UnicodeError):
      # The string cannot be converted to unicode -- default to str() which will
      # catch objects with special __str__ methods.
      string = str(data)

  if isinstance(string, six.text_type):
    # Our work is done here.
    return string

  try:
    # Just return the string if its pure ASCII.
    return string.decode('ascii')
  except UnicodeError:
    # The string is not ASCII encoded.
    pass

  # Try the suggested encoding if specified.
  if encoding:
    try:
      return string.decode(encoding)
    except UnicodeError:
      # Bad suggestion.
      pass

  # Try UTF-8 because the other encodings could be extended ASCII. It would
  # be exceptional if a valid extended ascii encoding with extended chars
  # were also a valid UITF-8 encoding.
  try:
    return string.decode('utf-8')
  except UnicodeError:
    # Not a UTF-8 encoding.
    pass

  # Try the filesystem encoding.
  try:
    return string.decode(sys.getfilesystemencoding())
  except UnicodeError:
    # string is not encoded for filesystem paths.
    pass

  # Try the system default encoding.
  try:
    return string.decode(sys.getdefaultencoding())
  except UnicodeError:
    # string is not encoded using the default encoding.
    pass

  # We don't know the string encoding.
  # This works around a Python str.encode() "feature" that throws
  # an ASCII *decode* exception on str strings that contain 8th bit set
  # bytes. For example, this sequence throws an exception:
  #   string = '\xdc'  # iso-8859-1 'Ü'
  #   string = string.encode('ascii', 'backslashreplace')
  # even though 'backslashreplace' is documented to handle encoding
  # errors. We work around the problem by first decoding the str string
  # from an 8-bit encoding to unicode, selecting any 8-bit encoding that
  # uses all 256 bytes (such as ISO-8559-1):
  #   string = string.decode('iso-8859-1')
  # Using this produces a sequence that works:
  #   string = '\xdc'
  #   string = string.decode('iso-8859-1')
  #   string = string.encode('ascii', 'backslashreplace')
  return string.decode('iso-8859-1')


def GetEncodedValue(env, name, default=None):
  """Returns the decoded value of the env var name.

  Args:
    env: {str: str}, The env dict.
    name: str, The env var name.
    default: The value to return if name is not in env.

  Returns:
    The decoded value of the env var name.
  """
  name = Encode(name)
  value = env.get(name)
  if value is None:
    return default
  # In Python 3, the environment sets and gets accept and return text strings
  # only, and it handles the encoding itself so this is not necessary.
  return Decode(value)


def SetEncodedValue(env, name, value, encoding=None):
  """Sets the value of name in env to an encoded value.

  Args:
    env: {str: str}, The env dict.
    name: str, The env var name.
    value: str or unicode, The value for name. If None then name is removed from
      env.
    encoding: str, The encoding to use or None to try to infer it.
  """
  # Python 2 *and* 3 unicode support falls apart at filesystem/argv/environment
  # boundaries. The encoding used for filesystem paths and environment variable
  # names/values is under user control on most systems. With one of those values
  # in hand there is no way to tell exactly how the value was encoded. We get
  # some reasonable hints from sys.getfilesystemencoding() or
  # sys.getdefaultencoding() and use them to encode values that the receiving
  # process will have a chance at decoding. Leaving the values as unicode
  # strings will cause os module Unicode exceptions. What good is a language
  # unicode model when the module support could care less?
  name = Encode(name, encoding=encoding)
  if value is None:
    env.pop(name, None)
    return
  env[name] = Encode(value, encoding=encoding)


def EncodeEnv(env, encoding=None):
  """Encodes all the key value pairs in env in preparation for subprocess.

  Args:
    env: {str: str}, The environment you are going to pass to subprocess.
    encoding: str, The encoding to use or None to use the default.

  Returns:
    {bytes: bytes}, The environment to pass to subprocess.
  """
  encoding = encoding or _GetEncoding()
  encoded_env = {}

  for k, v in six.iteritems(env):
    SetEncodedValue(encoded_env, k, v, encoding=encoding)
  return encoded_env


def _GetEncoding():
  """Gets the default encoding to use."""
  return sys.getfilesystemencoding() or sys.getdefaultencoding()
