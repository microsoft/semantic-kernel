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

"""gcloud interactive layout.

  This is the prompt toolkit layout for the shell prompt. It determines the
  positioning and layout of the prompt, toolbars, autocomplete, etc.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.interactive import help_window
from prompt_toolkit import enums
from prompt_toolkit import filters
from prompt_toolkit import layout
from prompt_toolkit import shortcuts
from prompt_toolkit import token
from prompt_toolkit.layout import containers
from prompt_toolkit.layout import controls
from prompt_toolkit.layout import dimension
from prompt_toolkit.layout import margins
from prompt_toolkit.layout import menus
from prompt_toolkit.layout import processors
from prompt_toolkit.layout import prompt
from prompt_toolkit.layout import screen
from prompt_toolkit.layout import toolbars as pt_toolbars


@filters.Condition
def UserTypingFilter(cli):
  """Determine if the input field is empty."""
  return (cli.current_buffer.document.text and
          cli.current_buffer.document.text != cli.config.context)


def CreatePromptLayout(config,
                       lexer=None,
                       is_password=False,
                       get_prompt_tokens=None,
                       get_continuation_tokens=None,
                       get_debug_tokens=None,
                       get_bottom_status_tokens=None,
                       get_bottom_toolbar_tokens=None,
                       extra_input_processors=None,
                       multiline=False,
                       show_help=True,
                       wrap_lines=True):
  """Create a container instance for the prompt."""
  assert get_bottom_status_tokens is None or callable(
      get_bottom_status_tokens)
  assert get_bottom_toolbar_tokens is None or callable(
      get_bottom_toolbar_tokens)
  assert get_prompt_tokens is None or callable(get_prompt_tokens)
  assert get_debug_tokens is None or callable(get_debug_tokens)
  assert not (config.prompt and get_prompt_tokens)

  multi_column_completion_menu = filters.to_cli_filter(
      config.multi_column_completion_menu)
  multiline = filters.to_cli_filter(multiline)

  if get_prompt_tokens is None:
    get_prompt_tokens = lambda _: [(token.Token.Prompt, config.prompt)]

  has_before_tokens, get_prompt_tokens_1, get_prompt_tokens_2 = (
      shortcuts._split_multiline_prompt(get_prompt_tokens))  # pylint: disable=protected-access
  # TODO(b/35347840): reimplement _split_multiline_prompt to remove
  #                   protected-access.

  # Create processors list.
  input_processors = [
      processors.ConditionalProcessor(
          # By default, only highlight search when the search
          # input has the focus. (Note that this doesn't mean
          # there is no search: the Vi 'n' binding for instance
          # still allows to jump to the next match in
          # navigation mode.)
          processors.HighlightSearchProcessor(preview_search=True),
          filters.HasFocus(enums.SEARCH_BUFFER)),
      processors.HighlightSelectionProcessor(),
      processors.ConditionalProcessor(processors.AppendAutoSuggestion(),
                                      filters.HasFocus(enums.DEFAULT_BUFFER)
                                      & ~filters.IsDone()),
      processors.ConditionalProcessor(processors.PasswordProcessor(),
                                      is_password),
  ]

  if extra_input_processors:
    input_processors.extend(extra_input_processors)

  # Show the prompt before the input using the DefaultPrompt processor.
  # This also replaces it with reverse-i-search and 'arg' when required.
  # (Only for single line mode.)
  # (DefaultPrompt should always be at the end of the processors.)
  input_processors.append(
      processors.ConditionalProcessor(
          prompt.DefaultPrompt(get_prompt_tokens_2), ~multiline))

  # Create toolbars
  toolbars = []
  if config.fixed_prompt_position:
    help_height = dimension.LayoutDimension.exact(config.help_lines)
    help_filter = (show_help & ~filters.IsDone() &
                   filters.RendererHeightIsKnown())
  else:
    help_height = dimension.LayoutDimension(
        preferred=config.help_lines,
        max=config.help_lines)
    help_filter = (show_help & UserTypingFilter & ~filters.IsDone() &
                   filters.RendererHeightIsKnown())
  toolbars.append(
      containers.ConditionalContainer(
          layout.HSplit([
              layout.Window(
                  controls.FillControl(char=screen.Char('_', token.Token.HSep)),
                  height=dimension.LayoutDimension.exact(1)),
              layout.Window(
                  help_window.HelpWindowControl(
                      default_char=screen.Char(' ', token.Token.Toolbar)),
                  height=help_height),
          ]),
          filter=help_filter))
  if (config.bottom_status_line and get_bottom_status_tokens or
      config.bottom_bindings_line and get_bottom_toolbar_tokens or
      config.debug and get_debug_tokens):
    windows = []
    windows.append(layout.Window(
        controls.FillControl(char=screen.Char('_', token.Token.HSep)),
        height=dimension.LayoutDimension.exact(1)))
    if config.debug and get_debug_tokens:
      windows.append(
          layout.Window(
              controls.TokenListControl(
                  get_debug_tokens,
                  default_char=screen.Char(' ', token.Token.Text)),
              wrap_lines=True,
              height=dimension.LayoutDimension.exact(3)))
      windows.append(layout.Window(
          controls.FillControl(char=screen.Char('_', token.Token.HSep)),
          height=dimension.LayoutDimension.exact(1)))
    if config.bottom_status_line and get_bottom_status_tokens:
      windows.append(
          layout.Window(
              controls.TokenListControl(
                  get_bottom_status_tokens,
                  default_char=screen.Char(' ', token.Token.Toolbar)),
              height=dimension.LayoutDimension.exact(1)))
    if config.bottom_bindings_line and get_bottom_toolbar_tokens:
      windows.append(
          layout.Window(
              controls.TokenListControl(
                  get_bottom_toolbar_tokens,
                  default_char=screen.Char(' ', token.Token.Toolbar)),
              height=dimension.LayoutDimension.exact(1)))
    toolbars.append(
        containers.ConditionalContainer(
            layout.HSplit(windows),
            filter=~filters.IsDone() & filters.RendererHeightIsKnown()))

  def GetHeight(cli):
    """Determine the height for the input buffer."""
    # If there is an autocompletion menu to be shown, make sure that our
    # layout has at least a minimal height in order to display it.
    if cli.config.completion_menu_lines and not cli.is_done:
      # Reserve the space, either when there are completions, or when
      # `complete_while_typing` is true and we expect completions very
      # soon.
      buf = cli.current_buffer
      # if UserTypingFilter(cli) or not buf.text or buf.complete_state:
      if UserTypingFilter(cli) or buf.complete_state:
        return dimension.LayoutDimension(
            min=cli.config.completion_menu_lines + 1)
    return dimension.LayoutDimension()

  # Create and return Container instance.
  return layout.HSplit([
      # The main input, with completion menus floating on top of it.
      containers.FloatContainer(
          layout.HSplit([
              containers.ConditionalContainer(
                  layout.Window(
                      controls.TokenListControl(get_prompt_tokens_1),
                      dont_extend_height=True,
                      wrap_lines=wrap_lines,
                  ),
                  filters.Condition(has_before_tokens),
              ),
              layout.Window(
                  controls.BufferControl(
                      input_processors=input_processors,
                      lexer=lexer,
                      # Enable preview_search, we want to have immediate
                      # feedback in reverse-i-search mode.
                      preview_search=True,
                  ),
                  get_height=GetHeight,
                  left_margins=[
                      # In multiline mode, use the window margin to display
                      # the prompt and continuation tokens.
                      margins.ConditionalMargin(
                          margins.PromptMargin(get_prompt_tokens_2,
                                               get_continuation_tokens),
                          filter=multiline,
                      ),
                  ],
                  wrap_lines=wrap_lines,
              ),
          ]),
          [
              # Completion menus.
              layout.Float(
                  xcursor=True,
                  ycursor=True,
                  content=menus.CompletionsMenu(
                      max_height=16,
                      scroll_offset=1,
                      extra_filter=(
                          filters.HasFocus(enums.DEFAULT_BUFFER) &
                          ~multi_column_completion_menu
                      ),
                  ),
              ),
              layout.Float(
                  ycursor=True,
                  content=menus.MultiColumnCompletionsMenu(
                      show_meta=True,
                      extra_filter=(
                          filters.HasFocus(enums.DEFAULT_BUFFER) &
                          multi_column_completion_menu
                      ),
                  ),
              ),
          ],
      ),
      pt_toolbars.ValidationToolbar(),
      pt_toolbars.SystemToolbar(),

      # In multiline mode, we use two toolbars for 'arg' and 'search'.
      containers.ConditionalContainer(pt_toolbars.ArgToolbar(), multiline),
      containers.ConditionalContainer(pt_toolbars.SearchToolbar(), multiline),
  ] + toolbars)
