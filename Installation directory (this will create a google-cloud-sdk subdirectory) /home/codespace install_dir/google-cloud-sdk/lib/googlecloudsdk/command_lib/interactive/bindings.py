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

"""The gcloud interactive key bindings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import sys

from googlecloudsdk.command_lib.interactive import browser
from prompt_toolkit import keys
from prompt_toolkit.key_binding import manager

import six


class _KeyBinding(object):
  """Key binding base info to keep registered bindings and toolbar in sync.

  Attributes:
    key: The keys.Key.* object.
    help_text: The UX help text.
    label: The short word label for the bottom toolbar.
    metavar: Display this value in GetLabel(markdown=True) instead of the real
      value.
    status: The bool => string toggle status map.
    toggle: The bool toggle state.
  """

  def __init__(self, key, help_text=None, label=None, metavar=None,
               status=None, toggle=True):
    self.key = key
    self.help_text = help_text
    self.label = label
    self.metavar = metavar
    self.status = status
    self.toggle = toggle

  def GetName(self):
    """Returns the binding display name."""
    return re.sub('.*<(.*)>.*', r'\1',
                  six.text_type(self.key)).replace('C-', 'ctrl-')

  def GetLabel(self, markdown=False):
    """Returns the key binding display label containing the name and value."""
    if self.label is None and self.status is None:
      return None
    label = []
    if markdown:
      label.append('*')
    label.append(self.GetName())
    label.append(':')
    if self.label:
      label.append(self.label)
      if self.status:
        label.append(':')
    if markdown:
      label.append('*')
    if self.status:
      if markdown:
        label.append('_')
        label.append(self.metavar or 'STATE')
        label.append('_')
      else:
        label.append(self.status[self.toggle])
    return ''.join(label)

  def GetHelp(self, markdown=False):
    """Returns the key help text."""
    if not self.help_text:
      return None
    key = self.GetName()
    if markdown:
      key = '*{}*'.format(key)
    return self.help_text.format(key=key)

  def SetMode(self, cli):
    """Sets the toggle mode in the cli."""
    del cli

  def Handle(self, event):
    """Handles a bound key event."""
    self.toggle = not self.toggle
    self.SetMode(event.cli)


class _WebHelpKeyBinding(_KeyBinding):
  """The web help key binding."""

  def __init__(self, key):
    super(_WebHelpKeyBinding, self).__init__(
        key=key,
        label='web-help',
        help_text=(
            'Opens a web browser tab/window to display the complete man page '
            'help for the current command. If there is no active web browser '
            '(running in *ssh*(1) for example), then command specific help or '
            '*man*(1) help is attempted.'
        ),
    )

  def Handle(self, event):
    doc = event.cli.current_buffer.document
    browser.OpenReferencePage(event.cli, doc.text, doc.cursor_position)


class _ContextKeyBinding(_KeyBinding):
  """set context key binding."""

  def __init__(self, key):
    super(_ContextKeyBinding, self).__init__(
        key=key,
        label='context',
        help_text=(
            'Sets the context for command input, so you won\'t have to re-type '
            'common command prefixes at every prompt. The context is the '
            'command line from just after the prompt up to the cursor.'
            '\n+\n'
            'For example, if you are about to work with `gcloud compute` for '
            'a while, type *gcloud compute* and hit {key}. This will display '
            '*gcloud compute* at subsequent prompts until the context is '
            'changed.'
            '\n+\n'
            'Hit ctrl-c and {key} to clear the context, or edit a command line '
            'and/or move the cursor and hit {key} to set a different context.'
        ),
    )

  def Handle(self, event):
    event.cli.config.context = (
        event.cli.current_buffer.document.text_before_cursor)


class _HelpKeyBinding(_KeyBinding):
  """The help key binding."""

  def __init__(self, key, toggle=True):
    super(_HelpKeyBinding, self).__init__(
        key=key,
        label='help',
        toggle=toggle, status={False: 'OFF', True: 'ON'},
        help_text=(
            'Toggles the active help section, *ON* when enabled, *OFF* when '
            'disabled.'
        ),
    )


class _QuitKeyBinding(_KeyBinding):
  """The quit key binding."""

  def __init__(self, key):
    super(_QuitKeyBinding, self).__init__(
        key=key,
        label='quit',
        help_text=(
            'Exit.'
        ),
    )

  def Handle(self, event):
    del event
    sys.exit(1)


class _InterruptKeyBinding(_KeyBinding):
  """The interrupt (ctrl-c) key binding.

  Catches control-C and clears the prompt input buffer and completer.
  """

  def __init__(self, key):
    super(_InterruptKeyBinding, self).__init__(
        key=key,
    )

  def Handle(self, event):
    event.cli.current_buffer.reset()
    event.cli.completer.reset()


class _StopKeyBinding(_KeyBinding):
  """The stop (^Z) key binding.

  This binding's sole purpose is to ignore ^Z and prevent it from echoing
  in the prompt window.
  """

  def __init__(self, key):
    super(_StopKeyBinding, self).__init__(
        key=key,
    )


class KeyBindings(object):
  """All key bindings.

  Attributes:
    bindings: The list of key bindings in left to right order.
    help_key: The help visibility key binding. True for ON, false for
      OFF.
    context_key: The command prefix context key that sets the context to the
      command substring from the beginning of the input line to the current
      cursor position.
    web_help_key: The browse key binding that pops up the full reference
      doc in a browser.
    quit_key: The key binding that exits the shell.
  """

  def __init__(self, help_mode=True):
    """Associates keys with handlers. Toggle states are reachable from here."""

    # The actual key bindings. Changing keys.Keys.* here automatically
    # propagates to the bottom toolbar labels.
    self.help_key = _HelpKeyBinding(keys.Keys.F2, toggle=help_mode)
    self.context_key = _ContextKeyBinding(keys.Keys.F7)
    self.web_help_key = _WebHelpKeyBinding(keys.Keys.F8)
    self.quit_key = _QuitKeyBinding(keys.Keys.F9)
    self.interrupt_signal = _InterruptKeyBinding(keys.Keys.ControlC)
    self.stop_signal = _StopKeyBinding(keys.Keys.ControlZ)

    # This is the order of binding label appearance in the bottom toolbar.
    self.bindings = [
        self.help_key,
        self.context_key,
        self.web_help_key,
        self.quit_key,
        self.interrupt_signal,
        self.stop_signal,
    ]

  def MakeRegistry(self):
    """Makes and returns a key binding registry populated with the bindings."""
    m = manager.KeyBindingManager(
        enable_abort_and_exit_bindings=True,
        enable_system_bindings=True,
        enable_search=True,
        enable_auto_suggest_bindings=True,)

    for binding in self.bindings:
      m.registry.add_binding(binding.key, eager=True)(binding.Handle)

    return m.registry

  def Initialize(self, cli):
    """Initialize key binding defaults in the cli."""
    for binding in self.bindings:
      binding.SetMode(cli)
