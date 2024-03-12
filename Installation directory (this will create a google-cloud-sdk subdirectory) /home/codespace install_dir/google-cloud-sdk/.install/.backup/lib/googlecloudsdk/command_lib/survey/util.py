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
"""Utility module for CLI survey."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def Indent(paragraph, indent_level=1, indent_size=2, indent_char=' '):
  r"""Indent a paragraph.

  Args:
    paragraph: str, the paragraph to indent. Each line is separated by '\r',
      '\n', or '\r\n'.
    indent_level: int, the level of indentation.
    indent_size: int, width of each indentation.
    indent_char: character, padding character.

  Returns:
    Indented paragraph.
  """

  lines = paragraph.splitlines(True)
  lines_indent = [
      (indent_char * indent_size * indent_level) + line for line in lines
  ]
  return ''.join(lines_indent)
