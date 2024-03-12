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
"""Creates a user in a given cluster.

Creates a user in a given cluster with specified username, type, and password.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.command_lib.alloydb import user_helper
from googlecloudsdk.core import properties


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Creates a user in a given cluster.

  Creates a user in a given cluster with specified username, cluster, region,
  type, and password.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
      To create a new user, run:

        $ {command} my-username --cluster=my-cluster --region=us-central1 --password=postgres
      """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs
    """
    flags.AddUsername(parser)
    flags.AddCluster(parser, False)
    flags.AddRegion(parser)
    flags.AddUserPassword(parser)
    flags.AddUserType(parser)
    flags.AddCreateSuperuser(parser)
    flags.AddDBRoles(parser)

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
    req = user_helper.ConstructCreateRequestFromArgs(
        client, alloydb_messages, cluster_ref, args
    )
    return alloydb_client.projects_locations_clusters_users.Create(req)
