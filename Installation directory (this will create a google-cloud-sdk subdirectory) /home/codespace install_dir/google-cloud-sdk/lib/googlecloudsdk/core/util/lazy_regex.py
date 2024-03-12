# -*- coding: utf-8 -*- #
#
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

"""A utility for setting up lazy compiling of regex to improve performance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core.util import lazy_regex_patterns

# Save a reference to the real re.compile, since it will be redefined.
real_compile = re.compile


# Name class to match the wrapped SRE_Pattern class.
class _Lazy_SRE_Pattern(object):  # pylint: disable=invalid-name
  """A class to lazily compile regex."""

  def __init__(self, pattern, flags=0):
    # Use object.__setattr__ to avoid triggering compilation with setattr.
    object.__setattr__(self, 'pattern', pattern)
    object.__setattr__(self, 'flags', flags)
    object.__setattr__(self, 'sre_pattern', None)

  def _compile(self):
    sre_pattern = real_compile(self.pattern, self.flags)
    object.__setattr__(self, 'sre_pattern', sre_pattern)

  def __getattr__(self, name):
    self._compile()
    return getattr(self.sre_pattern, name)

  def __setattr__(self, name, value):
    self._compile()
    setattr(self.sre_pattern, name, value)


def _lazy_compile(pattern, flags=0):
  """Return a Lazy or normal SRE_Pattern object depending on the args.

  Patterns in lazy_regex_patterns.PATTERNS are known to be valid, so they will
  be compiled lazily. Other patterns will be compiled immediately, as it is not
  known if they will compile or raise an re.error.

  For more information on the arguments, see:
  https://docs.python.org/3/howto/regex.html#compilation-flags

  Args:
    pattern: The pattern to be compiled.
    flags: Flags to be used during compilation.
  Returns:
    An SRE_Pattern or a _Lazy_SRE_Pattern.
  Raises:
    re.error: If the arguments do not form a valid regex pattern.
  """
  if pattern in lazy_regex_patterns.PATTERNS:
    return _Lazy_SRE_Pattern(pattern, flags)
  return real_compile(pattern, flags)


def initialize_lazy_compile():
  re.compile = _lazy_compile

