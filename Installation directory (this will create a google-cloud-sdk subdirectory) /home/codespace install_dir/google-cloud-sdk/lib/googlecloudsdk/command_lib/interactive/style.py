# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""gcloud interactive static styles."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from prompt_toolkit import styles
from prompt_toolkit import token


BLUE = '#00DED1'
GREEN = '#008000'
GRAY = '#666666'
DARK_GRAY = '#333333'
BLACK = '#000000'
PURPLE = '#FF00FF'

BOLD = 'bold'
ITALIC = 'underline'  # there is no italic
REVERSE = 'reverse'


def Color(foreground=None, background=None, bold=False):
  components = []
  if foreground:
    components.append(foreground)
  if background:
    components.append('bg:' + background)
  if bold:
    components.append('bold')
  return ' '.join(components)


def GetDocumentStyle():
  """Return the color styles for the layout."""
  prompt_styles = styles.default_style_extensions
  prompt_styles.update({
      token.Token.Menu.Completions.Completion.Current: Color(BLUE, GRAY),
      token.Token.Menu.Completions.Completion: Color(BLUE, DARK_GRAY),
      token.Token.Toolbar: BOLD,
      token.Token.Toolbar.Account: BOLD,
      token.Token.Toolbar.Separator: BOLD,
      token.Token.Toolbar.Project: BOLD,
      token.Token.Toolbar.Help: BOLD,
      token.Token.Prompt: BOLD,
      token.Token.HSep: Color(GREEN),
      token.Token.Markdown.Section: BOLD,
      token.Token.Markdown.Definition: BOLD,
      token.Token.Markdown.Value: ITALIC,
      token.Token.Markdown.Truncated: REVERSE,
      token.Token.Purple: BOLD,
  })
  return styles.PygmentsStyle.from_defaults(style_dict=prompt_styles)
