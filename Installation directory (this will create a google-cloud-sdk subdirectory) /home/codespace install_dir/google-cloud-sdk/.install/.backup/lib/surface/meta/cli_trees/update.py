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

"""Updates non-gcloud CLI command trees in the installation directory."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.meta import generate_cli_trees


def _GetCliTreeGeneratorList():
  return ', '.join(sorted([cli_tree.DEFAULT_CLI_NAME] +
                          list(generate_cli_trees.GENERATORS.keys())))


class Update(base.Command):
  """Updates gcloud CLI command trees in the installation directory.

  A CLI tree is a module or JSON file that describes a command and its
  subcommands, flags, arguments, help text and TAB completers.
  *gcloud interactive* uses CLI trees for typeahead, command line completion,
  and as-you-type documentation.

  Most CLI tree files are cached in the *cli* subdirectory of the *gcloud*
  installation root directory. The cache is automatically updated by the
  Cloud SDK installers and the *gcloud components* command group.

  These CLIs are currently supported: {generators}.
  """

  detailed_help = {'generators': _GetCliTreeGeneratorList}

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--commands',
        type=arg_parsers.ArgList(),
        metavar='COMMAND',
        help='Update only the commands in this list.')
    parser.add_argument(
        '--directory',
        help=('Update this directory instead of the default installation '
              'directory.'))
    parser.add_argument(
        '--force',
        action='store_true',
        help=('Force existing CLI trees to be out of date. This causes them '
              'to be regenerated.'))
    parser.add_argument(
        '--tarball',
        help=('For packaging CLI trees. --commands specifies one command '
              'that is a relative path in this tarball. The tarball is '
              'extracted to a temporary directory and the command path is '
              'adjusted to point to the temporary directory.'))

  def Run(self, args):
    generate_cli_trees.UpdateCliTrees(cli=self._cli_power_users_only,
                                      commands=args.commands,
                                      directory=args.directory,
                                      tarball=args.tarball,
                                      force=args.force,
                                      verbose=not args.quiet)
