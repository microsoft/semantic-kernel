# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""List session command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import display_helper
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List sessions in a project.

    List sessions in a project. Page-size sets the maximum number of sessions
    returned per page, and Page-token retrieves subsequent results.

  ## EXAMPLES

  List sessions in the "us-central1" location:

    $ {command} --location="us-central1"
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, constants.DEFAULT_PAGE_SIZE)
    # TODO(b/207032388): Use built-in filter arg after it is supported by
    # backend.
    # Filter is not supported yet.
    base.FILTER_FLAG.RemoveFromParser(parser)
    # Temporarily add a fake hidden implementation so that no parsing logic
    # needs to be changed.
    parser.add_argument(
        '--filter',
        hidden=True,
        metavar='EXPRESSION',
        require_coverage_in_tests=False,
        help="""\
        Apply a Boolean filter EXPRESSION to each resource item to be listed
        (the '=' equality operator is the only supported operator).
        If the expression evaluates true for an item, the item is listed.
        This flag interacts with other flags, which are applied in the
        following order: *--flatten*, *--sort-by*, *--filter*, *--limit*.
        For more information, run 'gcloud topic filters'.""")

    flags.AddLocationFlag(parser)
    parser.display_info.AddFormat("""
          table(
            name.basename():label=SESSION_ID,
            sessionType.yesno(no="-"):label=SESSION_TYPE,
            state:label=STATUS
          )
    """)

  def Run(self, args):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)

    request = List.GetRequest(dataproc.messages,
                              util.ParseProjectsLocationsForSession(dataproc),
                              args)

    sessions = list_pager.YieldFromList(
        dataproc.client.projects_locations_sessions,
        request,
        limit=args.limit,
        field='sessions',
        batch_size=args.page_size,
        batch_size_attribute='pageSize')
    return (display_helper.DisplayHelper(session) for session in sessions)

  @staticmethod
  def GetRequest(messages, resource, args):
    # Remove args.filter to prevent post-filter behavior.
    backend_filter = None
    if args.filter:
      backend_filter = args.filter
      args.filter = None

    return messages.DataprocProjectsLocationsSessionsListRequest(
        filter=backend_filter,
        pageSize=args.page_size,
        parent=resource.RelativeName())

