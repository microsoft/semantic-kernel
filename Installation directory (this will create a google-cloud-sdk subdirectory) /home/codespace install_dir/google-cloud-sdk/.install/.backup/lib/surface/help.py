# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""A calliope command that prints help for another calliope command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.help_search import search
from googlecloudsdk.command_lib.help_search import search_util
from googlecloudsdk.core import log


_DEFAULT_LIMIT = 5


class Help(base.ListCommand):
  """Search gcloud help text.

  If a full gcloud command is specified after the ``help'' operand, {command}
  prints a detailed help message for that command.

  Otherwise, {command} runs a search for all commands with help text matching
  the given argument or arguments. It prints the command name and a summary of
  the help text for any command that it finds as a result.

  To run a search directly, you can use remainder arguments, following a `--`.

  By default, command results are displayed in a table that shows the name
  of the command and snippets of the help text that relate to your search terms.

  By default, search results are sorted from most to least relevant by default,
  using a localized rating based on several heuristics. These heuristics may
  change in future runs of this command.

  ## EXAMPLES

  To get the help for the command `gcloud projects describe`, run:

    $ {command} projects describe

  To search for all commands whose help text contains the word `project`, run:

    $ {command} -- project

  To search for commands whose help text contains the word `project` and the
  string `--foo`, run:

    $ {command} -- project --foo

  To search and receive more than the default limit of 5 search results, run:

    $ {command} --limit=20 -- project

  To search for a term and sort the results by a different characteristic, such
  as command name, run:

    $ {command} --sort-by=name -- project
  """

  category = base.SDK_TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    parser.display_info.AddTransforms(search_util.GetTransforms())
    parser.display_info.AddFormat("""
        table[all-box,pager](
            commandpath():label='COMMAND',
            summary():wrap)
        """)
    base.URI_FLAG.RemoveFromParser(parser)
    base.LIMIT_FLAG.SetDefault(parser, _DEFAULT_LIMIT)
    base.SORT_BY_FLAG.SetDefault(parser, '~relevance')
    parser.add_argument(
        'command',
        nargs='*',
        help="""\
Sequence of names representing a gcloud group or command name.

If the arguments provide the name of a gcloud command, the full help
text of that command will be displayed. Otherwise, all arguments will
be considered search terms and used to search through all of gcloud's
help text.
""")

    parser.add_argument(
        'search_terms',
        nargs=argparse.REMAINDER,
        help="""\
Search terms. The command will return a list of gcloud commands that are
relevant to the searched term. If this argument is provided, the command
will always return a list of search results rather than displaying help
text of a single command.

For example, to search for commands that relate to the term `project` or
`folder`, run:

  $ {command} -- project folder
""")

  def Run(self, args):
    if not args.search_terms:
      try:
        # --document=style=help to signal the metrics.Help() 'help' label in
        # actions.RenderDocumentAction().Action().
        self.ExecuteCommandDoNotUse(args.command + ['--document=style=help'])
        return None
      except Exception:  # pylint: disable=broad-except
        # In this case, we will treat the arguments as search terms.
        pass

    results = search.RunSearch(
        args.command + (args.search_terms or []),
        self._cli_power_users_only)

    self._resources_found = len(results)
    self._resources_displayed = min(len(results), args.limit)
    return results

  def Epilog(self, resources_were_displayed):
    if not self._resources_found:
      return
    if resources_were_displayed:
      log.status.Print(
          'Listed {} of {} items.'.format(self._resources_displayed,
                                          self._resources_found))
    else:
      log.status.Print('Listed 0 items.')
