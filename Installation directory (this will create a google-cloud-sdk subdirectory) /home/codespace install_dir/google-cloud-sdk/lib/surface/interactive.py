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

"""Extensible interactive shell with auto completion and help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.interactive import config as configuration
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.util import encoding

import six

if six.PY3:
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.command_lib.interactive import application
  from googlecloudsdk.command_lib.interactive import bindings
  # pylint: enable=g-import-not-at-top


_FEATURES = """
* auto-completion and active help for all commands
* state preservation across commands: *cd*, local/environment variables
"""

_SPLASH = """
# Welcome to the gcloud interactive shell environment.

Tips:

* start by typing commands to get auto-suggestions and inline help
* use `tab`, `up-arrow`, or `down-arrow` to navigate completion dropdowns
* use `space` or `/` to accept the highlighted dropdown item
* run gcloud <alpha|beta> interactive --help for more info

Run *$ gcloud feedback* to report bugs or request new features.

"""


def _AppendMetricsEnvironment(tag):
  """Appends tag to the Cloud SDK metrics environment tag.

  The metrics/environment tag is sent via the useragent. This tag is visible in
  metrics for all gcloud commands executed by the calling command.

  Args:
    tag: The string to append to the metrics/environment tag.
  """
  metrics_environment = properties.VALUES.metrics.environment.Get() or ''
  if metrics_environment:
    metrics_environment += '.'
  metrics_environment += tag
  encoding.SetEncodedValue(os.environ, 'CLOUDSDK_METRICS_ENVIRONMENT',
                           metrics_environment)


def _GetKeyBindingsHelp():
  """Returns the function key bindings help markdown."""
  if six.PY2:
    return ''
  lines = []
  for key in bindings.KeyBindings().bindings:
    help_text = key.GetHelp(markdown=True)
    if help_text:
      lines.append('\n{}:::'.format(key.GetLabel(markdown=True)))
      lines.append(help_text)
  return '\n'.join(lines)


def _GetPropertiesHelp():
  """Returns the properties help markdown."""
  lines = []
  for prop in sorted(properties.VALUES.interactive, key=lambda p: p.name):
    if prop.help_text:
      lines.append('\n*{}*::'.format(prop.name))
      lines.append(prop.help_text)
      default = prop.default
      if default is not None:
        if isinstance(default, six.string_types):
          default = '"{}"'.format(default)
        else:
          if default in (False, True):
            default = six.text_type(default).lower()
          default = '*{}*'.format(default)
        lines.append('The default value is {}.'.format(default))
  return '\n'.join(lines)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Interactive(base.Command):
  # pylint: disable=line-too-long
  """Start the gcloud interactive shell.

  *{command}* provides an enhanced *bash*(1) command line with features that
  include:
  {features}

  ### Display

  The *{command}* display window is divided into sections, described here
  from top to bottom.

  *Previous Output*::

  Command output scrolls above the command input section as commands are
  executed.

  *Command Input*::

  Commands are typed, completed, and edited in this section. The default prompt
  is "$ ". If a context has been set, then its tokens are prepopulated before
  the cursor.

  *Active Help*::

  As you type, this section displays in-line help summaries for commands, flags,
  and arguments. You can toggle active help on and off via the *F2* key.
  Hit *F8* to display the help text in your browser.

  *Status Display*::

  Current *gcloud* project and account information, and function key
  descriptions and settings are displayed in this section. Function keys
  toggle mode/state settings or run specific actions.
  {bindings}

  ### Auto and Tab Completion

  Command completions are displayed in a scrolling pop-up menu. Use `tab` and
  up/down keys to navigate the completions, and `space` or `/` to select the
  highlighted completion.

  Completions for _known_ commands, flags, and static flag values are displayed
  automatically. Positional and dynamic flag value completions for known
  commands are displayed after `tab` is entered. Known commands include
  `gcloud`, `bq`, `gsutil`, `kubectl`, and any command with a man page that has
  been executed at least once in any *interactive* session.

  `tab` completion for unknown commands defers to *bash*(1), while still using
  the *interactive* user interface. Absent specific command information, a
  file/path completer is used when `tab` is entered for unknown positionals
  (arguments that do not start with '-'). The default completer handles '~' path
  notation and embedded _$var_ references, but does not expand their values in
  completions.

  Configure bash completions as you normally would. *{command}* starts up bash
  in a mode that sources *~/.bashrc* with the environment variable
  *COSHELL_VERSION* set to a non-empty version value.

  Command completion resets with each simple command in the command line. Simple
  commands are separated by '|', ';', '&' and may appear after '$(', '(', '{',
  '!', *if*, *then*, *elif*, *while*, and _name_=_value_ per command exports.
  Use `tab` on an empty line to enable command executable search on PATH for
  the first token in each simple command.

  Currently simple and compound commands must be entered in a single line.

  Refer to
  [Using gcloud interactive](https://cloud.google.com/sdk/docs/interactive-gcloud)
  for more information and animated GIFs.

  ### Control Characters

  Control characters affect the currently running command or the current
  command line being entered at the prompt.

  *ctrl-c*::
  If a command is currently running, then that command is interrupted. This
  terminates the command. Otherwise, if no command is running, ctrl-c clears
  the current command line.

  *ctrl-d*::
  Exits when entered as the first character at the command prompt. You can
  also run the *exit* command at the prompt.

  *ctrl-w*::
  If a command is not currently running, then the last word on the command
  line is deleted. This is handy for "walking back" partial completions.

  ### Command history

  *{command}* maintains persistent command history across sessions.

  #### emacs mode

  *^N*:: Move ahead one line in the history.
  *^P*:: Move back one line in the history.
  *^R*:: Search backwards in the history.

  #### vi mode

  /:: Search backwards in the history.
  *j*:: Move ahead one line in the history.
  *k*:: Move back one line in the history.
  *n*:: Search backwards for the next match.
  *N*:: Search forwards for the next match.

  #### history search mode

  *ENTER/RETURN*:: Retrieve the matched command line from the history.
  *^R*:: Search backwards for the next match.
  *^S*:: Search forwards for the next match.

  ### Layout Configuration

  Parts of the layout are configurable via
  *$ gcloud config set* interactive/_property_. These properties are only
  checked at startup. You must exit and restart to see the effects of new
  settings.
  {properties}

  ### CLI Trees

  *{command}* uses CLI tree data files for typeahead, command line completion,
  and help snippet generation. A few CLI trees are installed with their
  respective Google Cloud CLI components: *gcloud* (core component), *bq*,
  *gsutil*, and *kubectl*. Trees for commands that have man(1) pages are
  generated on the fly. See `$ gcloud topic cli-trees` for details.

  ## EXAMPLES

  To set the command context of *{command}* to "gcloud ", run:

      {command} --context="gcloud "

  ## NOTES

  On Windows, install *git*(1) for a *bash*(1) experience. *{command}* will
  then use the *git* (MinGW) *bash* instead of *cmd.exe*.

  Please run *$ gcloud feedback* to report bugs or request new features.
  """

  detailed_help = {
      'bindings': _GetKeyBindingsHelp,
      'features': _FEATURES,
      'properties': _GetPropertiesHelp,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--context',
        help=('Default command context. This is a string containing a '
              'command name, flags, and arguments. The context is prepopulated '
              'in each command line. You can inline edit any part of the '
              'context, or ctrl-c to eliminate it.'))
    parser.add_argument(
        '--debug',
        hidden=True,
        action='store_true',
        default=None,
        help='Enable debugging display.')
    parser.add_argument(
        '--hidden',
        hidden=True,
        action='store_true',
        default=None,
        help='Enable completion of hidden commands and flags.')
    parser.add_argument(
        '--prompt',
        hidden=True,
        help='The interactive shell prompt.')
    parser.add_argument(
        '--suggest',
        hidden=True,
        action='store_true',
        default=None,
        help=('Enable auto suggestion from history. The defaults are currently '
              'too rudimentary for prime time.'))

  def Run(self, args):
    if six.PY2:
      raise exceptions.Error('This command does not support Python 2. Please '
                             'upgrade to Python 3.')

    if not args.quiet:
      render_document.RenderDocument(fin=io.StringIO(_SPLASH))
    config = configuration.Config(
        context=args.context,
        debug=args.debug,
        hidden=args.hidden,
        prompt=args.prompt,
        suggest=args.suggest,
    )
    _AppendMetricsEnvironment('interactive_shell')
    application.main(args=args, config=config)
