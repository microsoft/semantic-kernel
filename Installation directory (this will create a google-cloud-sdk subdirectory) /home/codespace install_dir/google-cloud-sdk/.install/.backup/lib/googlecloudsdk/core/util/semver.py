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

"""Helper functions for comparing semantic versions.

Basic rules of semver:

Format: major.minor.patch-prerelease+build

major, minor, patch, must all be present and integers with no leading zeros.
They are compared numerically by segment.

prerelease is an optional '.' separated series of identifiers where each is
either an integer with no leading zeros, or an alphanumeric string
(including '-'). Prereleases are compared by comparing each identifier in
order.  Integers are compared numerically, alphanumeric strings are compared
lexigraphically.  A prerelease version is lower precedence than it's associated
normal version.

The build number is optional and not included in the comparison.  It is '.'
separated series of alphanumeric identifiers.

Two SemVer objects are considered equal if they represent the exact same string
(including the build number and including case differences).  For comparison
operators, we follow the SemVer spec of precedence and ignore the build number
and case of alphanumeric strings.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from six.moves import zip_longest


# Only digits, with no leading zeros.
_DIGITS = r'(?:0|[1-9][0-9]*)'
# Digits, letters and dashes
_ALPHA_NUM = r'[-0-9A-Za-z]+'
# This is an alphanumeric string that must have at least once letter (or else it
# would be considered digits).
_STRICT_ALPHA_NUM = r'[-0-9A-Za-z]*[-A-Za-z]+[-0-9A-Za-z]*'

_PRE_RELEASE_IDENTIFIER = r'(?:{0}|{1})'.format(_DIGITS, _STRICT_ALPHA_NUM)
_PRE_RELEASE = r'(?:{0}(?:\.{0})*)'.format(_PRE_RELEASE_IDENTIFIER)
_BUILD = r'(?:{0}(?:\.{0})*)'.format(_ALPHA_NUM)

_SEMVER = (
    r'^(?P<major>{digits})\.(?P<minor>{digits})\.(?P<patch>{digits})'
    r'(?:\-(?P<prerelease>{release}))?(?:\+(?P<build>{build}))?$'
).format(digits=_DIGITS, release=_PRE_RELEASE, build=_BUILD)


class ParseError(Exception):
  """An exception for when a string failed to parse as a valid semver."""
  pass


class SemVer(object):
  """Object to hold a parsed semantic version string."""

  def __init__(self, version):
    """Creates a SemVer object from the given version string.

    Args:
      version: str, The version string to parse.

    Raises:
      ParseError: If the version could not be correctly parsed.

    Returns:
      SemVer, The parsed version.
    """
    (self.major, self.minor, self.patch, self.prerelease, self.build) = (
        SemVer._FromString(version))

  @classmethod
  def _FromString(cls, version):
    """Parse the given version string into its parts."""
    if version is None:
      raise ParseError('The value is not a valid SemVer string: [None]')

    try:
      match = re.match(_SEMVER, version)
    except (TypeError, re.error) as e:
      raise ParseError('Error parsing version string: [{0}].  {1}'
                       .format(version, e))

    if not match:
      raise ParseError(
          'The value is not a valid SemVer string: [{0}]'.format(version))

    parts = match.groupdict()
    return (
        int(parts['major']), int(parts['minor']), int(parts['patch']),
        parts['prerelease'], parts['build'])

  @classmethod
  def _CmpHelper(cls, x, y):
    """Just a helper equivalent to the cmp() function in Python 2."""
    return (x > y) - (x < y)

  @classmethod
  def _ComparePrereleaseStrings(cls, s1, s2):
    """Compares the two given prerelease strings.

    Args:
      s1: str, The first prerelease string.
      s2: str, The second prerelease string.

    Returns:
      1 if s1 is greater than s2, -1 if s2 is greater than s1, and 0 if equal.
    """
    s1 = s1.split('.') if s1 else []
    s2 = s2.split('.') if s2 else []

    for (this, other) in zip_longest(s1, s2):
      # They can't both be None because empty parts of the string split will
      # come through as the empty string. None indicates it ran out of parts.
      if this is None:
        return 1
      elif other is None:
        return -1

      # Both parts have a value
      if this == other:
        # This part is the same, move on to the next.
        continue
      if this.isdigit() and other.isdigit():
        # Numerical comparison if they are both numbers.
        return SemVer._CmpHelper(int(this), int(other))
      # Lexical comparison if either is a string. Numbers will always sort
      # before strings.
      return SemVer._CmpHelper(this.lower(), other.lower())

    return 0

  def _Compare(self, other):
    """Compare this SemVer to other.

    Args:
      other: SemVer, the other version to compare this one to.

    Returns:
      1 if self > other, -1 if other > self, 0 if equal.
    """
    # Compare the required parts.
    result = SemVer._CmpHelper(
        (self.major, self.minor, self.patch),
        (other.major, other.minor, other.patch))
    # Only if required parts are equal, compare the prerelease strings.
    # Never include build number in comparison.
    result = result or SemVer._ComparePrereleaseStrings(
        self.prerelease, other.prerelease)
    return result

  def Distance(self, other):
    """Compare this SemVer to other and returns the distances.

    Args:
      other: SemVer, the other version to compare this one to.

    Returns:
      Distances between the major, minor and patch versions.
    """
    major_diff = self.major - other.major
    minor_diff = self.minor - other.minor
    patch_diff = self.patch - other.patch
    return major_diff, minor_diff, patch_diff

  def __eq__(self, other):
    return other and (
        (self.major, self.minor, self.patch, self.prerelease, self.build) ==
        (other.major, other.minor, other.patch, other.prerelease, other.build))

  def __ne__(self, other):
    return not self == other

  def __gt__(self, other):
    return self._Compare(other) > 0

  def __lt__(self, other):
    return self._Compare(other) < 0

  def __ge__(self, other):
    return not self < other

  def __le__(self, other):
    return not self > other


class LooseVersion:
  """Version numbering for anarchists and software realists.


  This is mostly copied from distutils.version.

  Implements the standard interface for version number classes as
  described above.  A version number consists of a series of numbers,
  separated by either periods or strings of letters.  When comparing
  version numbers, the numeric components will be compared
  numerically, and the alphabetic components lexically.  The following
  are all valid version numbers, in no particular order:
      1.5.1
      1.5.2b2
      161
      3.10a
      8.02
      3.4j
      1996.07.12
      3.2.pl0
      3.1.1.6
      2g6
      11g
      0.960923
      2.2beta29
      1.13++
      5.5.kw
      2.0b1pl0
  In fact, there is no such thing as an invalid version number under
  this scheme; the rules for comparison are simple and predictable,
  but may not always give the results you want (for some definition
  of "want").
  """

  component_re = re.compile(r'(\d+ | [a-z]+ | \.)', re.VERBOSE)

  def __init__(self, vstring=None):
    if vstring:
      self.parse(vstring)

  def __str__(self):
    return self.vstring

  def __repr__(self):
    return "LooseVersion('%s')" % str(self)

  def parse(self, vstring):  # pylint: disable=invalid-name
    """Instantiate self from string."""
    # I've given up on thinking I can reconstruct the version string
    # from the parsed tuple -- so I just store the string here for
    # use by __str__
    self.vstring = vstring
    components = [x for x in self.component_re.split(vstring)
                  if x and x != '.']
    for i, obj in enumerate(components):
      try:
        components[i] = int(obj)
      except ValueError:
        pass

    self.version = components

  def __eq__(self, other):
    c = self._cmp(other)
    if c is NotImplemented:
      return c
    return c == 0

  def __lt__(self, other):
    c = self._cmp(other)
    if c is NotImplemented:
      return c
    return c < 0

  def __le__(self, other):
    c = self._cmp(other)
    if c is NotImplemented:
      return c
    return c <= 0

  def __gt__(self, other):
    c = self._cmp(other)
    if c is NotImplemented:
      return c
    return c > 0

  def __ge__(self, other):
    c = self._cmp(other)
    if c is NotImplemented:
      return c
    return c >= 0

  def _cmp(self, other):  # pylint: disable=invalid-name
    """Compare self with other."""
    if isinstance(other, str):
      other = LooseVersion(other)
    elif not isinstance(other, LooseVersion):
      return NotImplemented

    if self.version == other.version:
      return 0
    if self.version < other.version:
      return -1
    if self.version > other.version:
      return 1
