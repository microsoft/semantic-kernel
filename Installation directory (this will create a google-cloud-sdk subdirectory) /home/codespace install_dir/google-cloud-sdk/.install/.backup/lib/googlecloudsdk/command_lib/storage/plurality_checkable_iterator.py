# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Iterator wrapper that allows checking if an iterator is empty or plural."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import sys

from googlecloudsdk.core import exceptions


BufferedException = collections.namedtuple(
    'BufferedException',
    ['exception', 'stack_trace']
)


def _get_item_or_raise_exception(item):
  """Detects and raises BufferedException's or simply returns item."""
  if isinstance(item, BufferedException):
    exceptions.reraise(item.exception, tb=item.stack_trace)
  else:
    return item


class PluralityCheckableIterator:
  """Iterator that can check if no items or more than one item can be yielded.

  This iterator accepts two types of values from an iterator it wraps:
    1. A yielded item.
    2. A raised exception, which will be buffered and re-raised when it
       is reached in this iterator.

  Both types count when determining the number of items left.
  """

  def __init__(self, iterable):
    """Initilizes a PluralityCheckableIterator instance.

    Args:
      iterable: An iterable to be wrapped.
        PluralityCheckableIterator yields items from this iterable and checks
        its plurality and emptiness.
    """

    self._iterator = iter(iterable)
    self._buffer = []

  def __iter__(self):
    return self

  def __next__(self):
    self._populate_buffer()
    if self._buffer:
      return _get_item_or_raise_exception(self._buffer.pop(0))
    else:
      raise StopIteration

  def is_empty(self):
    self._populate_buffer()
    return not self._buffer

  def is_plural(self):
    self._populate_buffer(num_elements=2)
    return len(self._buffer) > 1

  def peek(self):
    """Get first item of iterator without removing it from buffer.

    Returns:
      First item of iterator or None if empty iterator (or first item is None).
    """
    self._populate_buffer(num_elements=1)
    if self._buffer:
      return _get_item_or_raise_exception(self._buffer[0])
    return None

  def _populate_buffer(self, num_elements=1):
    while len(self._buffer) < num_elements:
      try:
        self._buffer.append(next(self._iterator))
      except StopIteration:
        break
      except Exception as e:  # pylint: disable=broad-except
        self._buffer.append(BufferedException(
            exception=e,
            stack_trace=sys.exc_info()[2]
        ))
