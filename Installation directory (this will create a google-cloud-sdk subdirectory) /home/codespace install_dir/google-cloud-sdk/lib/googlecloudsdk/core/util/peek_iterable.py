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

"""Iterable peek utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Peeker(object):
  """Peeks the first element from an iterable.

  The returned object is another iterable that is equivalent to the original.
  If the object is not iterable then the first item is the object itself.

  Example:
    iterable = Peeker(iterable)
    first_item = iterable.Peek()
    assert list(iterable)[0] == first_item

  Attributes:
    _iterable: The original iterable.
    _peek: The first item in the iterable, or the iterable itself if its not
      iterable.
    _peek_seen: _peek was already seen by the first next() call.
  """

  def __init__(self, iterable):
    self._iterable = iterable
    self._peek = self._Peek()
    self._peek_seen = False

  def __iter__(self):
    return self

  def _Peek(self):
    """Peeks the first item from the iterable."""
    try:
      # Object is a generator or iterator.
      return next(self._iterable)
    except TypeError:
      pass
    except StopIteration:
      self._peek_seen = True
      return None
    try:
      # Object is a list.
      return self._iterable.pop(0)
    except (AttributeError, IndexError, KeyError, TypeError):
      pass
    # Object is not iterable -- treat it as the only item.
    return self._iterable

  def next(self):
    """For Python 2 compatibility."""
    return self.__next__()

  def __next__(self):
    """Returns the next item in the iterable."""
    if not self._peek_seen:
      self._peek_seen = True
      return self._peek
    try:
      # Object is a generator or iterator.
      return next(self._iterable)
    except TypeError:
      pass
    try:
      # Object is a list.
      return self._iterable.pop(0)
    except AttributeError:
      pass
    except (AttributeError, IndexError, KeyError, TypeError):
      raise StopIteration
    # Object is not iterable -- treat it as the only item.
    raise StopIteration

  def Peek(self):
    """Returns the first item in the iterable."""
    return self._peek


class TapInjector(object):
  """Tap item injector."""

  def __init__(self, value, replace=False):
    self._value = value
    self._is_replacement = replace

  @property
  def value(self):
    return self._value

  @property
  def is_replacement(self):
    return self._is_replacement


class Tap(object):
  """A Tapper Tap object."""

  def Tap(self, item):
    """Called on each item as it is fetched.

    Args:
      item: The current item to be tapped.

    Returns:
      True: The item is retained in the iterable.
      False: The item is deleted from the iterable.
      None: The item is deleted from the iterable and the iteration stops.
      Injector(): Injector.value is injected into the iterable. If
        Injector.is_replacement then the item is deleted from the iterable,
        otherwise the item appears in the iterable after the injected value.
    """
    _ = item
    return True

  def Done(self):
    """Called after the last item."""
    pass


class Tapper(object):
  """Taps an iterable by calling a method for each item and after the last item.

  The returned object is another iterable that is equivalent to the original.
  If the object is not iterable then the first item is the object itself.

  Tappers may be used when it is not efficient or possible to completely drain
  a resource generator before the resources are finally consumed. For example,
  a paged resource may return the first page of resources immediately but have a
  significant delay between subsequent pages. A tapper allows the first page to
  be examined and consumed without waiting for the next page. If the tapper is a
  filter then it can filter and display a page before waiting for the next page.

  Example:
    tap = Tap()
    iterable = Tapper(iterable, tap)
    # The next statement calls tap.Tap(item) for each item and
    # tap.Done() after the last item.
    list(iterable)

  Attributes:
    _iterable: The original iterable.
    _tap: The Tap object.
    _stop: If True then the object is not iterable and it has already been
      returned.
    _injected: True if the previous _call_on_each injected a new item.
    _injected_value: The value to return next.
  """

  def __init__(self, iterable, tap):
    self._iterable = iterable
    self._tap = tap
    self._stop = False
    self._injected = False
    self._injected_value = None

  def __iter__(self):
    return self

  def _NextItem(self):
    """Returns the next item in self._iterable."""
    if self._injected:
      self._injected = False
      return self._injected_value
    try:
      # Object is a generator or iterator.
      return next(self._iterable)
    except TypeError:
      pass
    except StopIteration:
      self._tap.Done()
      raise
    try:
      # Object is a list.
      return self._iterable.pop(0)
    except (AttributeError, KeyError, TypeError):
      pass
    except IndexError:
      self._tap.Done()
      raise StopIteration
    # Object is not iterable -- treat it as the only item.
    if self._iterable is None or self._stop:
      self._tap.Done()
      raise StopIteration
    self._stop = True
    return self._iterable

  def next(self):
    """For Python 2 compatibility."""
    return self.__next__()

  def __next__(self):
    """Gets the next item, calls _tap.Tap() on it, and returns it."""
    while True:
      item = self._NextItem()
      inject_or_keep = self._tap.Tap(item)
      if inject_or_keep is None:
        self._tap.Done()
        raise StopIteration
      if isinstance(inject_or_keep, TapInjector):
        if not inject_or_keep.is_replacement:
          self._injected = True
          self._injected_value = item
        return inject_or_keep.value
      if inject_or_keep:
        return item
