# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command to list all folder IDs associated with the active user."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  r"""List folders accessible by the active account.

  List all folders to which the user has access under the specified
  parent (either an Organization or a Folder). Exactly one of --folder
  or --organization must be provided.

  ## EXAMPLES

  The following command lists folders under org with ID `123456789`:

    $ {command} --organization=123456789

  The following command lists folders under folder with ID `123456789`:

    $ {command} --folder=123456789

  The following command lists all the folders including the delete requested
  ones under the folder with ID `123456789`:

    $ {command} --folder=123456789 --show-deleted

  The following command lists only the deleted folders under folder with
  ID `123456789`:

    $ {command} --folder=123456789 --show-deleted \

        --filter='lifecycleState:DELETE_REQUESTED':

  """

  @staticmethod
  def Args(parser):
    flags.FolderIdFlag('to list folders under').AddToParser(parser)
    flags.OrganizationIdFlag('to list folders under').AddToParser(parser)
    parser.add_argument(
        '--show-deleted',
        action='store_true',
        help="""\
            Put --show-deleted flag to include folders
            for which delete is requested.
        """)
    parser.display_info.AddFormat("""
        table(
          displayName:label=DISPLAY_NAME,
          parent:label=PARENT_NAME,
          name.segment():label=ID:align=right:sort=1,
          lifecycleState
        )
    """)

  def Run(self, args):
    """Run the list command."""
    flags.CheckParentFlags(args)
    return list_pager.YieldFromList(
        folders.FoldersService(),
        folders.FoldersMessages().CloudresourcemanagerFoldersListRequest(
            parent=flags.GetParentFromFlags(args),
            showDeleted=args.show_deleted),
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='folders')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List folders accessible by the active account.

  List all folders to which the user has access under the specified
  parent (either an Organization or a Folder). Exactly one of --folder
  or --organization must be provided.

  ## EXAMPLES

  The following command lists folders under org with ID `123456789`:

    $ {command} --organization=123456789

  The following command lists folders under folder with ID `123456789`:

    $ {command} --folder=123456789
  """

  @staticmethod
  def Args(parser):
    flags.FolderIdFlag('to list folders under').AddToParser(parser)
    flags.OrganizationIdFlag('to list folders under').AddToParser(parser)
    parser.display_info.AddFormat("""
        table(
          displayName:label=DISPLAY_NAME,
          parent:label=PARENT_NAME,
          name.segment():label=ID:align=right:sort=1
        )
    """)

  def Run(self, args):
    """Run the list command."""
    flags.CheckParentFlags(args)
    return list_pager.YieldFromList(
        folders.FoldersService(),
        folders.FoldersMessages().CloudresourcemanagerFoldersListRequest(
            parent=flags.GetParentFromFlags(args)),
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='folders')
