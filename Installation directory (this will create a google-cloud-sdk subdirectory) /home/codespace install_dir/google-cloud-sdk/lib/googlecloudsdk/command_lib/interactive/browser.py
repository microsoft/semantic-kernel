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

"""Tools for launching a browser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import os
import subprocess
import sys
import webbrowser

from googlecloudsdk.command_lib.interactive import parser
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
import six


class FakeSubprocessModule(object):

  def Popen(self, args, **kwargs):
    with files.FileWriter(os.devnull) as devnull:
      kwargs.update({'stderr': devnull, 'stdout': devnull})
      return subprocess.Popen(args, **kwargs)


class CommandReferenceMapper(six.with_metaclass(abc.ABCMeta, object)):
  """Command to URL or man page reference mapper base class."""

  def __init__(self, cli, args):
    self.cli = cli
    self.args = args

  @abc.abstractmethod
  def GetMan(self):
    """Returns the man-style command for the command in args."""
    return None

  @abc.abstractmethod
  def GetURL(self):
    """Returns the help doc URL for the command in args."""
    return None


class GcloudReferenceMapper(CommandReferenceMapper):
  """gcloud help reference mapper."""

  def GetMan(self):
    return ' '.join(self.args + ['--help'])

  def GetURL(self):
    return '/'.join(
        ['https://cloud.google.com/sdk/gcloud/reference'] + self.args[1:])


class BqReferenceMapper(CommandReferenceMapper):
  """bq help reference mapper."""

  def GetMan(self):
    return self.args[0] + ' help | less'

  def GetURL(self):
    return 'https://cloud.google.com/bigquery/bq-command-line-tool'


class GsutilReferenceMapper(CommandReferenceMapper):
  """gsutil help reference mapper."""

  def __init__(self, cli, args):
    super(GsutilReferenceMapper, self).__init__(cli, args)
    self.subcommand = args[1] if len(args) > 1 else ''
    self.ref = ['https://cloud.google.com/storage/docs/gsutil']

  def GetMan(self):
    cmd = ['gsutil help']
    if self.subcommand:
      cmd.append(self.subcommand)
    cmd.append('| less')
    return ' '.join(cmd)

  def GetURL(self):
    if self.subcommand:
      self.ref.append('commands')
      self.ref.append(self.subcommand)
    return '/'.join(self.ref)


class KubectlReferenceMapper(CommandReferenceMapper):
  """kubectl help reference mapper."""

  def __init__(self, cli, args):
    super(KubectlReferenceMapper, self).__init__(cli, args)
    self.subcommand = args[1] if len(args) > 1 else ''
    try:
      full_version = (cli.root[parser.LOOKUP_COMMANDS][args[0]]
                      [parser.LOOKUP_CLI_VERSION])
      version = '.'.join(full_version.split('.')[0:2])
    except (IndexError, KeyError):
      version = 'v1.8'
    self.ref = ['https://kubernetes.io/docs/user-guide/kubectl', version]

  def GetMan(self):
    cmd = ['kubectl help']
    if self.subcommand:
      cmd.append(self.subcommand)
    cmd.append('| less')
    return ' '.join(cmd)

  def GetURL(self):
    if self.subcommand:
      self.ref.append('#' + self.subcommand)
    return '/'.join(self.ref)


class UnknownReferenceMapper(CommandReferenceMapper):
  """Unkmown command help reference mapper."""

  def __init__(self, cli, args):
    super(UnknownReferenceMapper, self).__init__(cli, args)
    self.known = files.FindExecutableOnPath(args[0])

  def GetMan(self):
    if not self.known:
      return None
    return 'man ' + self.args[0]

  def GetURL(self):
    if not self.known:
      return None
    if 'darwin' in sys.platform:
      ref = ['https://developer.apple.com/legacy/library/documentation',
             'Darwin/Reference/ManPages/man1']
    else:
      ref = ['http://man7.org/linux/man-pages/man1']
    ref.append(self.args[0] + '.1.html')
    return '/'.join(ref)


def _GetReferenceURL(cli, line, pos=None, man_page=False):
  """Determine the reference url of the command/group preceding the pos.

  Args:
    cli: the prompt CLI object
    line: a string with the current string directly from the shell.
    pos: the position of the cursor on the line.
    man_page: Return help/man page command line if True.

  Returns:
    A string containing the URL of the reference page.
  """
  mappers = {
      'bq': BqReferenceMapper,
      'gcloud': GcloudReferenceMapper,
      'gsutil': GsutilReferenceMapper,
      'kubectl': KubectlReferenceMapper,
  }

  if pos is None:
    pos = len(line)
  args = []
  for arg in cli.parser.ParseCommand(line):
    if arg.start < pos and (
        not args or
        arg.tree.get(parser.LOOKUP_COMMANDS) or  # IS_GROUP workaround
        arg.token_type in (parser.ArgTokenType.COMMAND,
                           parser.ArgTokenType.GROUP)):
      args.append(arg.value)
  if not args:
    if line:
      return None
    args = ['gcloud', 'alpha', 'interactive']

  mapper_class = mappers.get(args[0], UnknownReferenceMapper)
  mapper = mapper_class(cli, args)
  return mapper.GetMan() if man_page else mapper.GetURL()


def OpenReferencePage(cli, line, pos):
  """Opens a web browser or local help/man page for line at pos."""
  man_page = bool(encoding.GetEncodedValue(os.environ, 'SSH_CLIENT'))
  ref = _GetReferenceURL(cli, line, pos, man_page)
  if not ref:
    return
  if man_page:
    cli.Run(ref, alternate_screen=True)
    return

  webbrowser.subprocess = FakeSubprocessModule()
  try:
    browser = webbrowser.get()
    browser.open_new_tab(ref)
  except webbrowser.Error as e:
    cli.run_in_terminal(
        lambda: log.error('failed to open browser: %s', e))
