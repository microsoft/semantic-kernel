# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A command that lists the gcloud group and command tree with details."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.static_completion import generate


class ListGCloud(base.Command):
  """List the gcloud CLI command tree with flag, positional and help details."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--branch',
        metavar='COMMAND_PATH',
        help=('The branch of the CLI subtree to generate as a dotted command '
              'path. Mainly used to generate test data. For example, for the '
              '`gcloud compute instances` branch use "compute.instances".'))
    parser.add_argument(
        '--completions',
        action='store_true',
        help=('List the static completion CLI tree. This is a stripped down '
              'variant of the CLI tree that only contains the subcommand and '
              'flag name dictionaries. The tree is written as a Python '
              'source file (~1MiB) that loads fast (~30ms) as a .pyc file.'))

  def Run(self, args):
    branch = args.branch.split('.') if args.branch else None
    if args.completions:
      generate.ListCompletionTree(cli=self._cli_power_users_only, branch=branch)
    else:
      cli_tree.Dump(cli=self._cli_power_users_only, path='-', branch=branch)
