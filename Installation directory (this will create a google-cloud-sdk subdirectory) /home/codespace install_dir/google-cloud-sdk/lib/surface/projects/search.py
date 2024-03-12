# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to search projects associated with the active user."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Search(base.Command):
  """Search for projects matching the given query.

  You can specify the maximum number of projects to list using the `--limit`
  flag.

  ## EXAMPLES

  The following command lists the last five created projects with
  names starting with z, sorted by the project number (now called name)
  with 2 projects listed on each page

    $ {command} --query="name:z*" --sort-by=name --limit=5 --page-size=2

  To list projects that have been marked for deletion:

    $ {command} --query='state:DELETE_REQUESTED'
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
    table(
      displayName,
      name,
      parent,
      state
    )
    """)
    base.LIMIT_FLAG.AddToParser(parser)
    base.SORT_BY_FLAG.AddToParser(parser)
    parser.add_argument(
        '--query',
        help="""\
          A boolean expression for the search criteria used to select the projects to return.
          If no search criteria is specified then all accessible projects will be returned.
          Query expressions can be used to restrict results based upon displayName, state
          and parent, where the operators `=` (`:`) `NOT`, `AND` and `OR` can be used along
          with the suffix wildcard symbol `*`. The `displayName` field in a query expression should
          use escaped quotes for values that include whitespace to prevent unexpected behavior.

          """)
    parser.add_argument(
        '--page-size',
        type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
            This flag specifies the maximum number of projects per page.
        """)

  def Run(self, args):
    """Run the search command."""
    return projects_api.Search(limit=args.limit, query=args.query)
