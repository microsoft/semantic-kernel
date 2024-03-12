# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for regex in gcloud storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core.util import debug_output


class Patterns(object):
  """Holds multiple regex strings and checks matches against all."""

  def __init__(self, pattern_strings, ignore_prefix_length=0):
    """Initializes class."""
    self._patterns = [re.compile(x) for x in pattern_strings]
    self._ignore_prefix_length = ignore_prefix_length

  def match(self, target):
    """Checks if string matches any stored pattern."""
    target_substring = target[self._ignore_prefix_length :]
    return any((p.match(target_substring) for p in self._patterns))

  def __repr__(self):
    return debug_output.generic_repr(self)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        self._patterns == other._patterns
        and self._ignore_prefix_length == other._ignore_prefix_length
    )
