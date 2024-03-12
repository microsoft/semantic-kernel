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

"""Code for the gcloud shell help window."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.calliope import cli_tree_markdown as markdown
from googlecloudsdk.command_lib.interactive import parser
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.document_renderers import token_renderer
from prompt_toolkit.layout import controls


class HelpWindowControl(controls.UIControl):
  """Implementation of the help window."""

  def __init__(self, default_char=None):
    self._default_char = default_char

  def create_content(self, cli, width, height):
    data = GenerateHelpContent(cli, width)

    return controls.UIContent(
        lambda i: data[i],
        line_count=len(data),
        show_cursor=False,
        default_char=self._default_char)


def GenerateHelpContent(cli, width):
  """Returns help lines for the current token."""
  if width > 80:
    width = 80
  doc = cli.current_buffer.document
  args = cli.parser.ParseCommand(doc.text_before_cursor)
  if not args:
    return []
  arg = args[-1]

  if arg.token_type in (parser.ArgTokenType.GROUP, parser.ArgTokenType.COMMAND):
    return GenerateHelpForCommand(cli, arg, width)
  elif arg.token_type == parser.ArgTokenType.FLAG:
    return GenerateHelpForFlag(cli, arg, width)
  elif arg.token_type == parser.ArgTokenType.FLAG_ARG:
    return GenerateHelpForFlag(cli, args[-2], width)
  elif arg.token_type == parser.ArgTokenType.POSITIONAL:
    return GenerateHelpForPositional(cli, arg, width)

  return []


def GenerateHelpForCommand(cli, token, width):
  """Returns help lines for a command token."""
  lines = []

  # Get description
  height = 4
  gen = markdown.CliTreeMarkdownGenerator(token.tree, cli.root)
  gen.PrintSectionIfExists('DESCRIPTION', disable_header=True)
  doc = gen.Edit()
  fin = io.StringIO(doc)
  lines.extend(render_document.MarkdownRenderer(
      token_renderer.TokenRenderer(
          width=width, height=height), fin=fin).Run())

  lines.append([])  # blank line

  # Get synopis
  height = 5
  gen = markdown.CliTreeMarkdownGenerator(token.tree, cli.root)
  gen.PrintSynopsisSection()
  doc = gen.Edit()
  fin = io.StringIO(doc)
  lines.extend(render_document.MarkdownRenderer(
      token_renderer.TokenRenderer(
          width=width, height=height, compact=False), fin=fin).Run())

  return lines


def GenerateHelpForFlag(cli, token, width):
  """Returns help lines for a flag token."""
  gen = markdown.CliTreeMarkdownGenerator(cli.root, cli.root)
  gen.PrintFlagDefinition(token.tree)
  mark = gen.Edit()

  fin = io.StringIO(mark)
  return render_document.MarkdownRenderer(
      token_renderer.TokenRenderer(
          width=width, height=cli.config.help_lines), fin=fin).Run()


def GenerateHelpForPositional(cli, token, width):
  """Returns help lines for a positional token."""
  gen = markdown.CliTreeMarkdownGenerator(cli.root, cli.root)
  gen.PrintPositionalDefinition(markdown.Positional(token.tree))
  mark = gen.Edit()

  fin = io.StringIO(mark)
  return render_document.MarkdownRenderer(
      token_renderer.TokenRenderer(
          width=width, height=cli.config.help_lines), fin=fin).Run()
