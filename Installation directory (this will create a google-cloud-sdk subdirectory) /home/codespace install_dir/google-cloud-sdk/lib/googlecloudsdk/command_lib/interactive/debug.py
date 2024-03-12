# -*- coding: utf-8 -*- #
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

"""Generic debug tag accumulator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import time

import six


class Tag(object):
  """A debug tag object.

  Attributes:
    _name: The display name.
    _count: The number of times count() was called.
    _start: Most recent start() time in floating point seconds.
    _text: text() value.
    _intervals: The list or stop()-start() intervals in floating point seconds.
  """

  def __init__(self, name):
    self._name = name
    self._count = 0
    self._start = 0
    self._text = None
    self._intervals = []

  @classmethod
  def needs_quotes(cls, text):
    """Returns True if text "needs" quotes for pretty printing contents."""
    pairs = {'"': '"', "'": "'", '{': '}', '[': ']', '(': ')'}

    if text == '':  # pylint: disable=g-explicit-bool-comparison
      return True
    if ' ' not in text:
      return False
    return pairs.get(text[0]) != text[-1]

  def contents(self):
    """Returns the tag/value display string."""
    buf = io.StringIO()
    buf.write('{}'.format(self._name))
    if self._count:
      buf.write(':{}'.format(self._count))
    if self._intervals:
      n = len(self._intervals)
      buf.write(':{}:{:.6f}'.format(n, sum(self._intervals) / n))
    if self._text is not None:
      text = self._text
      if isinstance(text, six.string_types) and self.needs_quotes(text):
        text = '"' + text + '"'
      buf.write(':{}'.format(text))
    return buf.getvalue()

  def count(self):
    """Increments the tag count."""
    self._count += 1
    return self

  def start(self):
    """Starts the tag timing interval."""
    self._start = time.time()
    return self

  def stop(self):
    """Stops the tag timing interval."""
    self._intervals.append(time.time() - self._start)
    return self

  def text(self, t=None):
    """Sets the tag text value, omit the text arg to unset."""
    self._text = t
    return self


class Debug(object):
  """The controlling debug object.

  Debug "logger". Object tags (attributes) are created on the fly to preserve
  the feel of printf debugging.

  Usage:

    debug.foo.count().text(some_object)
    debug.bar.text('some state')
    debug.tag(some_string).count()
    debug.time.start()
    ...
    debug.time.stop()
    ...
    Display(debug.contents())

  Attributes:
    _changed: If _contents may have changed.
    _contents: The cached sorted list of tag/value strings.
    _tags: The list of debug tags.
  """

  def __init__(self):
    self._changed = False
    self._contents = []
    self._tags = {}

  def tag(self, key):
    """Returns a tag by key name, creates tag in _tags on the fly."""
    try:
      tag = self._tags[key]
    except KeyError:
      tag = Tag(key)
      self._tags[key] = tag
    self._changed = True
    return tag

  def __getattr__(self, key):
    """Called when __getattribute__ fails => creates tags on the fly."""
    return self.tag(key)

  def contents(self):
    """Returns the sorted list of tag/value display strings."""
    if self._changed:
      self._changed = False
      self._contents = [tag.contents()
                        for _, tag in sorted(six.iteritems(self._tags))]
    return self._contents
