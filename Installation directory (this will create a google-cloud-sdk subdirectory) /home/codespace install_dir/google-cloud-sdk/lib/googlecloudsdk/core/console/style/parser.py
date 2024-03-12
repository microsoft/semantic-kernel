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
"""Stylized printing using ANSI codes utility module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.console.style import mappings
from googlecloudsdk.core.console.style import text

import six


class _StyleContext(object):
  """Contains style information used in recursive parsingin TypedTextParser."""

  def __init__(self, color, attrs):
    self.color = color
    self.attrs = attrs

  @classmethod
  def FromTextAttributes(cls, text_attributes):
    if not text_attributes:
      return cls(None, [])
    return cls(text_attributes.color, text_attributes.attrs or [])

  def UpdateFromTextAttributes(self, text_attributes):
    if not text_attributes:
      return self
    new_color = text_attributes.color or self.color
    new_attrs = getattr(text_attributes, 'attrs', []) + self.attrs
    # Return a new object so children attributes don't propagate back up.
    return self.__class__(new_color, new_attrs)


class TypedTextParser(object):
  """Logger used to styled text to stderr."""

  CSI = '\x1b['  # Control Sequence Introducer
  SGR = 'm'  # Select Graphic Rendition, acts as a terminator for the sequence
  SET_FOREGROUND = '38;5;{}'
  RESET = '39;0'
  # Adding 0x20 to a given attr value changes it from turning the attribute on,
  # to turning the attribute off.
  ATTR_OFF = 0x20

  def __init__(self, style_mappings, style_enabled):
    """Creates a styled logger used to print styled text to stdout.

    Args:
      style_mappings: (StyleMapping), A mapping from TextTypes to
        mappings.TextAttributes used to stylize the output. If the map does
        not contain a TextAttribute object, plain text will bef
        logged.
      style_enabled: (bool), whether logged text should be styled.
    """
    self.style_mappings = style_mappings
    self.style_enabled = style_enabled

  def _GetAnsiSequenceForAttribute(self, text_attributes, style_context):
    """Returns the ANSI start and reset sequences for the text_attributes."""
    style_sequence = ''
    reset_sequence = ''
    attrs = (set(getattr(style_context, 'attrs', [])) |
             set(getattr(text_attributes, 'attrs', [])))
    if attrs:
      style_sequence += ';'.join(sorted([
          six.text_type(attr.value) for attr in attrs]))
      reset_sequence += ';'.join(
          sorted([
              six.text_type('%02x' % (attr.value + self.ATTR_OFF))
              for attr in attrs
          ]))
    color = (getattr(text_attributes, 'color', None) or
             getattr(style_context, 'color', None))
    if color:
      if style_sequence:
        style_sequence += ';'
      style_sequence += self.SET_FOREGROUND.format(color.value)
      if reset_sequence:
        reset_sequence += ';'
      reset_sequence += self.RESET
    begin_style, end_style = '', ''
    if style_sequence:
      begin_style = self.CSI + style_sequence + self.SGR
    if reset_sequence:
      end_style = self.CSI + reset_sequence + self.SGR
    return begin_style, end_style

  def ParseTypedTextToString(self, typed_text, style_context=None,
                             stylize=True):
    """Parses a TypedText object into plain and ansi-annotated unicode.

    The reason this returns both the plain and ansi-annotated strings is to
    support file logging.

    Args:
      typed_text: mappings.TypedText, typed text to be converted to unicode.
      style_context: _StyleContext, argument used for recursive calls
        to preserve text attributes and colors. Recursive calls are made when a
        TypedText object contains TypedText objects.
      stylize: bool, Whether or not to stylize the string.

    Returns:
      str, the parsed text.
    """
    if isinstance(typed_text, six.string_types):
      return typed_text

    stylize = stylize and self.style_enabled

    parsed_chunks = []
    text_attributes = self.style_mappings[typed_text.text_type]
    begin_style, end_style = self._GetAnsiSequenceForAttribute(
        text_attributes, style_context)

    if style_context:
      new_style_context = style_context.UpdateFromTextAttributes(
          text_attributes)
    else:
      new_style_context = _StyleContext.FromTextAttributes(text_attributes)
    for chunk in typed_text.texts:
      if isinstance(chunk, text.TypedText):
        parsed_chunks.append(self.ParseTypedTextToString(
            chunk,
            style_context=new_style_context,
            stylize=stylize))
        # For correctness, the style gets terminated at the end of the last
        # text object. So we need to output the style code again.
        if stylize:
          parsed_chunks.append(begin_style)
      else:
        parsed_chunks.append(chunk)
    parsed_text = ''.join(parsed_chunks)
    if text_attributes and text_attributes.format_str:
      parsed_text = text_attributes.format_str.format(parsed_text)
    if stylize:
      parsed_text = '{begin_style}{text}{end_style}'.format(
          begin_style=begin_style,
          text=parsed_text,
          end_style=end_style)
    return parsed_text


def _ColorsEnabled():
  """Returns true if colors should be enabled."""
  style = properties.VALUES.core.interactive_ux_style.Get()
  if any([
      style == properties.VALUES.core.InteractiveUXStyles.OFF.name,
      properties.VALUES.core.show_structured_logs.Get() != 'never',
      properties.VALUES.core.disable_color.GetBool()]):
    return False
  return True


def GetTypedTextParser(enabled=True, style_mappings=None):
  """Returns a typed text parser, creating a new one if necessary."""
  can_enable = _ColorsEnabled()
  enabled = can_enable and enabled  # Cannot force color printing.
  style_mappings = style_mappings or mappings.GetStyleMappings()
  return TypedTextParser(style_mappings, enabled)
