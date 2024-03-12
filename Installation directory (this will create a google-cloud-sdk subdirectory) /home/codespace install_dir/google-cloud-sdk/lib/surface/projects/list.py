# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command to list all project IDs associated with the active user."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import filter_rewrite
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.resource_manager import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_projection_spec


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(base.ListCommand):
  """List projects for which the user has resourcemanager.projects.list permission.

  List all projects to which the user has access under the specified
  parent (either an Organization or a Folder). Exactly one of --folder
  or --organization can be provided.

  The output format slightly differs from the Beta and GA versions.

  ## EXAMPLES

  The following command lists projects under the organization with
  ID `123456789`:

    $ {command} --organization=123456789

  The following command lists projects with display names starting with a
  under folder with ID `123456789`:

    $ {command} --folder=123456789 --filter='displayName:a*'

  The following command lists the last five created projects, sorted
  alphabetically by project ID:

    $ {command} --sort-by=projectId --limit=5

  To list projects that have been marked for deletion:

    $ {command} --filter='lifecycleState:DELETE_REQUESTED'
  """

  @staticmethod
  def Args(parser):
    flags.FolderIdFlag('to list projects under').AddToParser(parser)
    flags.OrganizationIdFlag('to list projects under').AddToParser(parser)
    parser.display_info.AddFormat(command_lib_util.LIST_FORMAT)

  def Run(self, args):
    """Run the list command."""

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases)
    args.filter, server_filter = filter_rewrite.ListRewriter().Rewrite(
        args.filter, defaults=defaults)
    log.info('client_filter="%s" server_filter="%s"',
             args.filter, server_filter)
    server_limit = args.limit
    if args.filter:
      # We must use client-side limiting if we
      # are using client-side filtering.
      server_limit = None

    if args.organization or args.folder:
      flags.CheckParentFlags(args)
      return projects_api.ListV3(parent=flags.GetParentFromFlags(args),
                                 limit=args.limit, batch_size=args.page_size)
    else:
      return projects_api.List(limit=server_limit, filter=server_filter)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List projects accessible by the active account.

  Lists all active projects, where the active account has Owner, Editor, Browser
  or Viewer permissions. Projects are listed in alphabetical order by project
  name. Projects that have been deleted or are pending deletion are not
  included.

  You can specify the maximum number of projects to list using the `--limit`
  flag.

  ## EXAMPLES

  The following command lists the last five created projects, sorted
  alphabetically by project ID:

    $ {command} --sort-by=projectId --limit=5

  To list projects that have been marked for deletion:

    $ {command} --filter='lifecycleState:DELETE_REQUESTED'
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(command_lib_util.LIST_FORMAT)

  def Run(self, args):
    """Run the list command."""
    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases)
    args.filter, server_filter = filter_rewrite.ListRewriter().Rewrite(
        args.filter, defaults=defaults)
    log.info('client_filter="%s" server_filter="%s"',
             args.filter, server_filter)
    server_limit = args.limit
    if args.filter:
      # We must use client-side limiting if we are using client-side filtering.
      server_limit = None
    return projects_api.List(limit=server_limit, filter=server_filter)
