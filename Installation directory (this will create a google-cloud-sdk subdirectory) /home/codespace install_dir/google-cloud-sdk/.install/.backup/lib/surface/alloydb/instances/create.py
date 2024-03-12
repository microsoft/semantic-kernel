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
"""Creates a new AlloyDB instance."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import instance_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.command_lib.alloydb import instance_helper
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Creates a new AlloyDB instance within a given cluster."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To create a new primary instance, run:

          $ {command} my-instance --cluster=my-cluster --region=us-central1 --instance-type=PRIMARY --cpu-count=4

        To create a new read pool instance, run:

          $ {command} my-instance --cluster=my-cluster --region=us-central1 --instance-type=READ_POOL --read-pool-node-count=1 --cpu-count=4
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddAvailabilityType(parser)
    flags.AddCluster(parser, False)
    flags.AddDatabaseFlags(parser)
    flags.AddInstance(parser)
    flags.AddInstanceType(parser)
    flags.AddCPUCount(parser)
    flags.AddReadPoolNodeCount(parser)
    flags.AddRegion(parser)
    flags.AddInsightsConfigQueryStringLength(parser)
    flags.AddInsightsConfigQueryPlansPerMinute(parser)
    flags.AddInsightsConfigRecordApplicationTags(
        parser, show_negated_in_help=True
    )
    flags.AddInsightsConfigRecordClientAddress(
        parser, show_negated_in_help=True
    )
    flags.AddSSLMode(parser, update=False)
    flags.AddRequireConnectors(parser)
    # TODO(b/185795425): Add --ssl-required and --labels later once we
    # understand the use cases

  def ConstructCreateRequestFromArgs(
      self, client, alloydb_messages, cluster_ref, args
  ):
    return instance_helper.ConstructCreateRequestFromArgsGA(
        client, alloydb_messages, cluster_ref, args
    )

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
        clustersId=args.cluster)
    req = self.ConstructCreateRequestFromArgs(
        client, alloydb_messages, cluster_ref, args
    )
    op = alloydb_client.projects_locations_clusters_instances.Create(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations')
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      instance_operations.Await(op_ref, 'Creating instance',
                                self.ReleaseTrack())
    return op


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Creates a new AlloyDB instance within a given cluster."""

  @classmethod
  def Args(cls, parser):
    super(CreateBeta, CreateBeta).Args(parser)
    flags.AddAssignInboundPublicIp(parser, False)

  def ConstructCreateRequestFromArgs(
      self, client, alloydb_messages, cluster_ref, args
  ):
    return instance_helper.ConstructCreateRequestFromArgsBeta(
        client, alloydb_messages, cluster_ref, args
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Creates a new AlloyDB instance within a given cluster."""

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, CreateAlpha).Args(parser)

  def ConstructCreateRequestFromArgs(
      self, client, alloydb_messages, cluster_ref, args
  ):
    return instance_helper.ConstructCreateRequestFromArgsAlpha(
        client, alloydb_messages, cluster_ref, args
    )
