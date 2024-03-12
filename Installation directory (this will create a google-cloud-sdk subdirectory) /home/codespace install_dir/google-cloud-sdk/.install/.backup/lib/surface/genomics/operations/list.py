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
"""Implementation of the gcloud genomics operations list command.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.genomics import filter_rewrite
from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class List(base.Command):
  """List Genomics operations in a project.

  Prints a table with summary information on operations in the project.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.LIMIT_FLAG.AddToParser(parser)
    parser.add_argument(
        '--filter',
        default='',
        type=str,
        help="""\
        A string for filtering operations created with the v2alpha1 API. In
        addition to typical operators (AND, OR, =, >, etc.) the following
        filter fields are supported:

          metadata.createTime - The time the operation was created as a
                                timestamp YYYY-MM-DD HH:MM:SS<time zone>.  T can
                                also be used as a separator between the date and
                                time.  The time zone is optional and can be
                                specified as an offset from UTC, a name, or 'Z'
                                for UTC. Run $ gcloud topic datetimes
                                to see more examples.
                                    2018-02-15T16:53:38
                                    2018-02-15 16:53:38-5:00
                                    2018-02-15T16:53:38Z
                                    2018-02-15 16:53:38 America/Los_Angeles
                         done - A boolean for whether the operation has
                                completed.
                   error.code - A google.rpc.Code for a completed operation.
              metadata.events - A set of strings for all events on the
                                operation.
                                    events:WorkerStartedEvent
              metadata.labels - A map of string key and value for the operation.
                                    labels.key = value
                                    labels."key with space" = "value with space"
                                For the existence of a key with any value.
                                    labels.key:*
        Run "$ gcloud topic filters" for more information.
        """)

  def Run(self, args):
    """Run 'operations list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of operations for this project.
    """
    apitools_client = genomics_util.GetGenomicsClient('v2alpha1')
    genomics_messages = genomics_util.GetGenomicsMessages('v2alpha1')

    request_filter = None
    if args.filter:
      rewriter = filter_rewrite.OperationsBackend()
      args.filter, request_filter = rewriter.Rewrite(args.filter)
      log.info('client_filter=%r server_filter=%r', args.filter, request_filter)

    request = genomics_messages.GenomicsProjectsOperationsListRequest(
        name='projects/%s/operations' % (genomics_util.GetProjectId(),),
        filter=request_filter)

    return list_pager.YieldFromList(
        apitools_client.projects_operations,
        request,
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.limit,  # Use limit if any, else server default.
        field='operations')
