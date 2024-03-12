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

"""gcloud interactive shell configurable styles."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties

import six


class Config(object):
  """gcloud interactive shell configurable styles.

  Attributes:
    bottom_bindings_line: Display bottom key bindings line if true.
    bottom_status_line: Display bottom status line if true.
    completion_menu_lines: Number of lines in the completion menu.
    context: Command context string.
    fixed_prompt_position: Display the prompt at the same position if true.
    help_lines: Maximum number of help snippet lines.
    hidden: Expose hidden commands/flags if true.
    justify_bottom_lines: Left and right justify bottom toolbar lines.
    manpage_generator: Use the manpage CLI tree generator for unsupported
      commands if true.
    multi_column_completion_menu: Display completions as multi-column menu
      if true.
    prompt: Command prompt string.
    show_help: Show help as command args are entered if true.
    suggest: Add command line suggestions based on history if true.
  """

  def __init__(
      self,
      bottom_bindings_line=None,
      bottom_status_line=None,
      completion_menu_lines=None,
      context=None,
      debug=None,
      fixed_prompt_position=None,
      help_lines=None,
      hidden=None,
      justify_bottom_lines=None,
      manpage_generator=None,
      multi_column_completion_menu=None,
      obfuscate=None,
      prompt=None,
      show_help=None,
      suggest=None,
  ):

    interactive = properties.VALUES.interactive

    if bottom_bindings_line is None:
      bottom_bindings_line = interactive.bottom_bindings_line.GetBool()
    self.bottom_bindings_line = bottom_bindings_line

    if bottom_status_line is None:
      bottom_status_line = interactive.bottom_status_line.GetBool()
    self.bottom_status_line = bottom_status_line

    if completion_menu_lines is None:
      completion_menu_lines = interactive.completion_menu_lines.GetInt()
    self.completion_menu_lines = completion_menu_lines

    if context is None:
      context = interactive.context.Get()
    self.context = six.text_type(context)

    if debug is None:
      debug = interactive.debug.GetBool()
    self.debug = debug

    if fixed_prompt_position is None:
      fixed_prompt_position = interactive.fixed_prompt_position.GetBool()
    self.fixed_prompt_position = fixed_prompt_position

    if help_lines is None:
      help_lines = interactive.help_lines.GetInt()
    self.help_lines = help_lines

    if hidden is None:
      hidden = interactive.hidden.GetBool()
    self.hidden = hidden

    if justify_bottom_lines is None:
      justify_bottom_lines = interactive.justify_bottom_lines.GetBool()
    self.justify_bottom_lines = justify_bottom_lines

    if manpage_generator is None:
      manpage_generator = interactive.manpage_generator.Get()
    self.manpage_generator = manpage_generator

    if multi_column_completion_menu is None:
      multi_column_completion_menu = (
          interactive.multi_column_completion_menu.GetBool())
    self.multi_column_completion_menu = multi_column_completion_menu

    if obfuscate is None:
      obfuscate = interactive.obfuscate.GetBool()
    self.obfuscate = obfuscate

    if prompt is None:
      prompt = interactive.prompt.Get()
    self.prompt = six.text_type(prompt)

    if show_help is None:
      show_help = interactive.show_help.GetBool()
    self.show_help = show_help

    if suggest is None:
      suggest = interactive.suggest.GetBool()
    self.suggest = suggest
