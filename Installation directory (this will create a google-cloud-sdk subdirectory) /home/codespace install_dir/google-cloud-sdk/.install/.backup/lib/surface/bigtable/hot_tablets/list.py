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
"""bigtable hottablets command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core.util import times


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class ListHotTablets(base.ListCommand):
  """List hot tablets in a Cloud Bigtable cluster."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
            Search for hot tablets in the past 24 hours:

              $ {command} my-cluster-id --instance=my-instance-id

            Search for hot tablets with start and end times by minute:

              $ {command} my-cluster-id --instance=my-instance-id --start-time="2018-08-12 03:30:00" --end-time="2018-08-13 17:00:00"

            Search for hot tablets with start and end times by day:

              $ {command} my-cluster-id --instance=my-instance-id --start-time=2018-01-01 --end-time=2018-01-05
          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddClusterResourceArg(parser, 'to list hot tablets for')
    arguments.AddStartTimeArgs(parser, 'to search for hot tablets')
    arguments.AddEndTimeArgs(parser, 'to search for hot tablets')

    # Define how the output should look like in a table.
    # Display startTime and endTime up to second precision.
    # `sort=1:reverse` sorts the display order of hot tablets by cpu usage.
    parser.display_info.AddFormat("""
      table(
        tableName.basename():label=TABLE,
        nodeCpuUsagePercent:label=CPU_USAGE:sort=1:reverse,
        startTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'):label=START_TIME,
        endTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'):label=END_TIME,
        startKey:label=START_KEY,
        endKey:label=END_KEY
      )
    """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Some value that we want to have printed later.
    """

    cli = util.GetAdminClient()
    # cluster_ref: A resource reference to the cluster to search for hottablets.
    cluster_ref = args.CONCEPTS.cluster.Parse()

    # Create a ListHotTablets Request and send through Admin Client.
    msg = (
        util.GetAdminMessages()
        .BigtableadminProjectsInstancesClustersHotTabletsListRequest(
            parent=cluster_ref.RelativeName(),
            startTime=args.start_time and times.FormatDateTime(args.start_time),
            endTime=args.end_time and times.FormatDateTime(args.end_time)))

    for hot_tablet in list_pager.YieldFromList(
        cli.projects_instances_clusters_hotTablets,
        msg,
        field='hotTablets',
        batch_size_attribute=None):
      yield hot_tablet
