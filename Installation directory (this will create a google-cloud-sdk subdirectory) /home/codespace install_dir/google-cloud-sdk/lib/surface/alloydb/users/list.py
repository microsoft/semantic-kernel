# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Lists AlloyDB users in a given cluster."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import properties

_USER_FORMAT = """
    table(
        name,
        userType:label="USER_TYPE",
        databaseRoles:label="DATABASE_ROLES"
    )
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class List(base.ListCommand):
  """Lists AlloyDB users in a given cluster."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
      To list users, run:

        $ {command} --cluster=my-cluster --region=us-central1
      """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser, Parser object for command line inputs
    """
    flags.AddRegion(parser)
    flags.AddCluster(parser, False)
    parser.display_info.AddFormat(_USER_FORMAT)

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
        locationsId=args.region,
        clustersId=args.cluster,
    )

    result = api_util.YieldFromListHandlingUnreachable(
        alloydb_client.projects_locations_clusters_users,
        alloydb_messages.AlloydbProjectsLocationsClustersUsersListRequest(
            parent=cluster_ref.RelativeName()
        ),
        field='users',
        limit=args.limit,
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
    )

    return result
