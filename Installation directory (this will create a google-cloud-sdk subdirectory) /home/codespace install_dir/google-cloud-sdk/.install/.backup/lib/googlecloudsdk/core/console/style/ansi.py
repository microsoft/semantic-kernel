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
"""Contains a list of colors and attributes available in ANSI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum


_colors = {
    'NO_COLOR': -1,
    'BLACK': 0,
    'RED': 1,
    'GREEN': 2,
    'YELLOW': 3,
    'BLUE': 4,
    'MAGENTA': 5,
    'CYAN': 6,
    'WHITE': 7,
    'BRIGHT_BLACK': 8,
    'BRIGHT_RED': 9,
    'BRIGHT_GREEN': 10,
    'BRIGHT_YELLOW': 11,
    'BRIGHT_BLUE': 12,
    'BRIGHT_MAGENTA': 13,
    'BRIGHT_CYAN': 14,
    'BRIGHT_WHITE': 15,
}
_colors.update(dict([('COLOR_{}'.format(i), i) for i in range(16, 256)]))


# ANSI Colors with the enum values being the color code. Pseudo enum class.
Colors = enum.Enum('Colors', _colors)  # pylint: disable=invalid-name


class Attrs(enum.Enum):
  """ANSI text attributes with the enum values being the attributes code."""
  BOLD = 1
  ITALICS = 3
  UNDERLINE = 4
