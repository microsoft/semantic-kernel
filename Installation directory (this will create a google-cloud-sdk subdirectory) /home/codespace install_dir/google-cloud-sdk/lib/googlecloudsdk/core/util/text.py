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
"""Utilities for manipulating text."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections


def Pluralize(num, word, plural=None):
  """Pluralize word based on num.

  Args:
    num: int, the number of objects to count.
    word: str, the word to pluralize.
    plural: str, the plural form of word if not "add s"

  Returns:
    str: the plural or singular form of word in accord with num.
  """
  if num == 1:
    return word
  return plural or word + 's'

_SECONDS_PER = collections.OrderedDict([
    ('second', 1),
    ('minute', 60),
    ('hour', 60 * 60),
    ('day', 60 * 60 * 24)
])


def GetArticle(noun):
  """Gets article (a or an) for given noun."""
  return 'an' if noun[0] in ['a', 'e', 'i', 'o', 'u'] else 'a'


def _TotalSeconds(delta):
  """Re-implementation of datetime.timedelta.total_seconds() for Python 2.6."""
  return delta.days * 24 * 60 * 60 + delta.seconds


def PrettyTimeDelta(delta):
  """Pretty print the given time delta.

  Rounds down.

  >>> _PrettyTimeDelta(datetime.timedelta(seconds=0))
  '0 seconds'
  >>> _PrettyTimeDelta(datetime.timedelta(minutes=1))
  '1 minute'
  >>> _PrettyTimeDelta(datetime.timedelta(hours=2))
  '2 hours'
  >>> _PrettyTimeDelta(datetime.timedelta(days=3))
  '3 days'

  Args:
    delta: a datetime.timedelta object

  Returns:
    str, a human-readable version of the time delta
  """
  seconds = int(_TotalSeconds(delta))
  num = seconds
  unit = 'second'
  for u, seconds_per in _SECONDS_PER.items():
    if seconds < seconds_per:
      break
    unit = u
    num = seconds // seconds_per
  return '{0} {1}'.format(num, Pluralize(num, unit))
