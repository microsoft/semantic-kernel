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

"""'logging metrics list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGA(base.ListCommand):
  """Display all logs-based metrics."""

  detailed_help = {
      'DESCRIPTION': """\
      List all logs-based metrics.
      """,
      'EXAMPLES': """\
      To list the top 10 logs-based metrics, run:

        $ {command} --limit=10
      """,
  }

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat('table(name, description, filter)')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of metrics.
    """
    request = util.GetMessages().LoggingProjectsMetricsListRequest(
        parent=util.GetCurrentProjectParent())

    return list_pager.YieldFromList(
        util.GetClient().projects_metrics, request, field='metrics',
        limit=args.limit, batch_size=None, batch_size_attribute='pageSize')


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(ListGA):
  """Display all logs-based metrics."""

  detailed_help = {
      'DESCRIPTION': """\
          Lists all logs-based metrics.
      """,
      'EXAMPLES': """\

      To list up to 10 logs-based metrics, run:

        $ {command} --limit=10

      To view as a simple table with just the name, description, and filter
      fields, run:

        $ {command} --format="table(name, description, filter)"
        """,
  }

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat('yaml')
