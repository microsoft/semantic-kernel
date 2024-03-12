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
"""Mappings from TextTypes to TextAttributes used by the TextTypeParser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console.style import ansi
from googlecloudsdk.core.console.style import text


class StyleMapping(object):
  """Mapping of TextTypes to TextAttributes."""

  def __init__(self, mappings):
    """Creates a StyleMapping object to be used by a StyledLogger.

    Args:
      mappings: (dict[TextTypes, TextAttributes]), the mapping
        to be used for this StyleMapping object.
    """
    self.mappings = mappings

  def __getitem__(self, key):
    if key in self.mappings:
      return self.mappings[key]
    return None


STYLE_MAPPINGS_BASIC = StyleMapping({
    text.TextTypes.RESOURCE_NAME: text.TextAttributes('[{}]'),
    text.TextTypes.OUTPUT: text.TextAttributes('{}'),
    text.TextTypes.USER_INPUT: text.TextAttributes('{}'),
    text.TextTypes.URI: text.TextAttributes('{}'),
    text.TextTypes.URL: text.TextAttributes('{}'),
    text.TextTypes.COMMAND: text.TextAttributes('{}'),
    text.TextTypes.INFO: text.TextAttributes('{}'),
    text.TextTypes.PT_SUCCESS: text.TextAttributes('{}'),
    text.TextTypes.PT_FAILURE: text.TextAttributes('{}'),
})


STYLE_MAPPINGS_ANSI = StyleMapping({
    text.TextTypes.RESOURCE_NAME: text.TextAttributes(
        '[{}]',
        color=ansi.Colors.BLUE,
        attrs=[]),
    text.TextTypes.OUTPUT: text.TextAttributes(
        '[{}]',
        color=ansi.Colors.BLUE,
        attrs=[]),
    text.TextTypes.USER_INPUT: text.TextAttributes(
        '{}',
        color=ansi.Colors.CYAN,
        attrs=[ansi.Attrs.BOLD]),
    text.TextTypes.URI: text.TextAttributes(
        '{}',
        color=None,
        attrs=[]),
    text.TextTypes.URL: text.TextAttributes(
        '{}',
        color=None,
        attrs=[ansi.Attrs.UNDERLINE]),
    text.TextTypes.COMMAND: text.TextAttributes(
        '{}',
        color=ansi.Colors.GREEN,
        attrs=[]),
    text.TextTypes.INFO: text.TextAttributes(
        '{}',
        color=ansi.Colors.YELLOW,
        attrs=[]),
    text.TextTypes.PT_SUCCESS: text.TextAttributes(
        '{}', color=ansi.Colors.GREEN),
    text.TextTypes.PT_FAILURE: text.TextAttributes(
        '{}', color=ansi.Colors.RED),
})


STYLE_MAPPINGS_ANSI_256 = StyleMapping({
    text.TextTypes.RESOURCE_NAME: text.TextAttributes(
        '[{}]',
        color=ansi.Colors.COLOR_33,
        attrs=[]),
    text.TextTypes.OUTPUT: text.TextAttributes(
        '[{}]',
        color=ansi.Colors.COLOR_33,
        attrs=[]),
    text.TextTypes.USER_INPUT: text.TextAttributes(
        '{}',
        color=ansi.Colors.COLOR_81,
        attrs=[ansi.Attrs.BOLD]),
    text.TextTypes.URI: text.TextAttributes(
        '{}',
        color=None,
        attrs=[]),
    text.TextTypes.URL: text.TextAttributes(
        '{}',
        color=None,
        attrs=[ansi.Attrs.UNDERLINE]),
    text.TextTypes.COMMAND: text.TextAttributes(
        '{}',
        color=ansi.Colors.COLOR_34,
        attrs=[]),
    text.TextTypes.INFO: text.TextAttributes(
        '{}',
        color=ansi.Colors.COLOR_167,
        attrs=[]),
    text.TextTypes.PT_SUCCESS: text.TextAttributes(
        '{}', color=ansi.Colors.GREEN),
    text.TextTypes.PT_FAILURE: text.TextAttributes(
        '{}', color=ansi.Colors.RED),
})


STYLE_MAPPINGS_TESTING = StyleMapping(dict([
    (text_type, text.TextAttributes('[{{}}]({})'.format(text_type.name)))
    for text_type in [
        text.TextTypes.RESOURCE_NAME,
        text.TextTypes.OUTPUT,
        text.TextTypes.USER_INPUT,
        text.TextTypes.URI,
        text.TextTypes.URL,
        text.TextTypes.COMMAND,
        text.TextTypes.INFO,
        text.TextTypes.PT_SUCCESS,
        text.TextTypes.PT_FAILURE]]))


def GetStyleMappings(console_attributes=None):
  """Gets the style mappings based on the console and user properties."""
  console_attributes = console_attributes or console_attr.GetConsoleAttr()
  is_screen_reader = properties.VALUES.accessibility.screen_reader.GetBool()
  if properties.VALUES.core.color_theme.Get() == 'testing':
    return STYLE_MAPPINGS_TESTING
  elif (not is_screen_reader and
        console_attributes.SupportsAnsi() and
        properties.VALUES.core.color_theme.Get() != 'off'):
    if console_attributes._term == 'xterm-256color':  # pylint: disable=protected-access
      return STYLE_MAPPINGS_ANSI_256
    else:
      return STYLE_MAPPINGS_ANSI
  else:
    return STYLE_MAPPINGS_BASIC
