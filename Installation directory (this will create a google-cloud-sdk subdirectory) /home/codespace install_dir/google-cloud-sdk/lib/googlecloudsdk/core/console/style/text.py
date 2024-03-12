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
"""Semantic text objects that are used for styled outputting."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum


class TextAttributes(object):
  """Attributes to use to style text with."""

  def __init__(self, format_str=None, color=None, attrs=None):
    """Defines a set of attributes for a piece of text.

    Args:
      format_str: (str), string that will be used to format the text
        with. For example '[{}]', to enclose text in brackets.
      color: (Colors), the color the text should be formatted with.
      attrs: (Attrs), the attributes to apply to text.
    """
    self._format_str = format_str
    self._color = color
    self._attrs = attrs or []

  @property
  def format_str(self):
    return self._format_str

  @property
  def color(self):
    return self._color

  @property
  def attrs(self):
    return self._attrs


class TypedText(object):
  """Text with a semantic type that will be used for styling."""

  def __init__(self, texts, text_type=None):
    """String of text and a corresponding type to use to style that text.

    Args:
     texts: (list[str]), list of strs or TypedText objects
       that should be styled using text_type.
     text_type: (TextTypes), the semantic type of the text that
       will be used to style text.
    """
    self.texts = texts
    self.text_type = text_type

  def __len__(self):
    length = 0
    for text in self.texts:
      length += len(text)
    return length

  def __add__(self, other):
    texts = [self, other]
    return TypedText(texts)

  def __radd__(self, other):
    texts = [other, self]
    return TypedText(texts)


class _TextTypes(enum.Enum):
  """Text types base class that defines base functionality."""

  def __call__(self, *args):
    """Returns a TypedText object using this style."""
    return TypedText(list(args), self)


class TextTypes(_TextTypes):
  """Defines text types that can be used for styling text."""
  RESOURCE_NAME = 1
  URL = 2
  USER_INPUT = 3
  COMMAND = 4
  INFO = 5
  URI = 6
  OUTPUT = 7
  PT_SUCCESS = 8
  PT_FAILURE = 9

