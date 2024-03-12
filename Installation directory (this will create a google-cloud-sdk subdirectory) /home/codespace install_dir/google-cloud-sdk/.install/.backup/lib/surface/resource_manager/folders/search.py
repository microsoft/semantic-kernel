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
"""Command to search folders associated with the active user."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Search(base.Command):
  """Search folders matching the specified query.

  You can specify the maximum number of folders to return in the result
  using the `--limit`flag.

  ## EXAMPLES

  The following command lists the folders that have been marked for deletion:

    $ {command} --query='state:DELETE_REQUESTED'

  Folders with their displayNames starting with sun like sunflower-folder,
  sunburn-folder etc. can be listed using the below command

    $ {command} --query='displayName:sun*'

  """
  FOLDERS_API_VERSION = 'v3'

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
          A boolean expression for the search criteria used to select the folders to return.
          If no search criteria is specified then all accessible projects will be returned.
          Query expressions can be used to restrict results based upon displayName, state
          and parent, where the operators `=` (`:`) `NOT`, `AND` and `OR` can be used along
          with the suffix wildcard symbol `*`. The `displayName` field in a query expression should
          use escaped quotes for values that include whitespace to prevent unexpected behavior.

          For more details and fields supported by the query expression please refer
          query parameters section `[here]
          (https://cloud.google.com/resource-manager/reference/rest/v3/folders/search#query-parameters)`
          """)
    parser.add_argument(
        '--page-size',
        type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
            This flag specifies the maximum number of folders per page.
        """)

  def Run(self, args):
    """Run the search command."""
    return list_pager.YieldFromList(
        folders.FoldersService(self.FOLDERS_API_VERSION),
        folders.FoldersMessages(
            self.FOLDERS_API_VERSION).CloudresourcemanagerFoldersSearchRequest(
                query=args.query),
        method='Search',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='folders')
