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

"""Lists the installed gcloud interactive CLI trees."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import list_cli_trees


class List(base.Command):
  """List the installed gcloud interactive CLI trees.

  This command lists all CLI trees found in the Cloud SDK installation and
  config directories. Duplicates may be listed; commands that load the trees
  search the configuration directory first.

  A CLI tree is a module or JSON file that describes a command and its
  subcommands, flags, arguments, help text and TAB completers.
  *gcloud interactive* uses CLI trees for typeahead, command line completion,
  and as-you-type documentation.

  Most CLI tree files are cached in the *cli* subdirectory of the *gcloud*
  installation root directory. The cache is automatically updated by the
  Cloud SDK installers and the *gcloud components* command group.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--directory',
        help='Insert this directory into the list of directories to search.')
    parser.display_info.AddFormat(
        'table[box](command:sort=1, cli_version:label=CLI, version:label=VER, '
        'path, error)')

  def Run(self, args):
    return list_cli_trees.ListAll(directory=args.directory)
