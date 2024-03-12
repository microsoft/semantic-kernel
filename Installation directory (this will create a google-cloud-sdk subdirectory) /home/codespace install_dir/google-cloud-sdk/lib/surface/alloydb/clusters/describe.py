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
"""Describes a AlloyDB cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an AlloyDB cluster in a given project and region."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To describe a cluster, run:

          $ {command} my-cluster --region=us-central1
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    flags.AddRegion(parser)
    flags.AddCluster(parser)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
          arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    client = api_util.AlloyDBClient(self.ReleaseTrack())
    alloydb_client = client.alloydb_client
    alloydb_messages = client.alloydb_messages
    cluster_ref = client.resource_parser.Create(
        'alloydb.projects.locations.clusters',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region, clustersId=args.cluster)
    req = alloydb_messages.AlloydbProjectsLocationsClustersGetRequest(
        name=cluster_ref.RelativeName()
    )
    cluster = alloydb_client.projects_locations_clusters.Get(req)
    normalize_automated_backup_policy(cluster.automatedBackupPolicy)
    return cluster


def normalize_automated_backup_policy(policy):
  """Normalizes the policy so that it looks correct when printed."""
  if policy is None:
    return
  if policy.weeklySchedule is None:
    return
  for start_time in policy.weeklySchedule.startTimes:
    # If the customer selects 00:00 as a start time, this ultimately becomes
    # a start time with all None fields. In the terminal this is then
    # confusingly printed as `{}`. We manually set the hours to be 0 in this
    # case so that it appears as `hours: 0`.
    if start_time.hours is None:
      start_time.hours = 0
