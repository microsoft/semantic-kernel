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
"""Updates an AlloyDB instance."""


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
class Update(base.UpdateCommand):
  """Updates an AlloyDB instance within a given cluster."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To update the number of nodes in the read pool, run:

          $ {command} my-read-instance --cluster=my-cluster --region=us-central1 --read-pool-node-count=3
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser, Parser object for command line inputs
    """
    base.ASYNC_FLAG.AddToParser(parser)
    # Update runs for a long time, it is better to default to async mode so that
    # users can query the operation status and find the status.
    base.ASYNC_FLAG.SetDefault(parser, True)
    flags.AddAvailabilityType(parser)
    flags.AddCluster(parser, False)
    flags.AddDatabaseFlags(parser)
    flags.AddInstance(parser)
    flags.AddCPUCount(parser, required=False)
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
    flags.AddSSLMode(parser, update=True)
    flags.AddRequireConnectors(parser)
    # TODO(b/185795425): Add --ssl-required and --labels later once we
    # understand the use cases

  def ConstructPatchRequestFromArgs(self, alloydb_messages, instance_ref, args):
    return instance_helper.ConstructPatchRequestFromArgs(
        alloydb_messages, instance_ref, args)

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
    instance_ref = client.resource_parser.Create(
        'alloydb.projects.locations.clusters.instances',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
        clustersId=args.cluster,
        instancesId=args.instance,
    )
    req = self.ConstructPatchRequestFromArgs(
        alloydb_messages, instance_ref, args
    )
    op = alloydb_client.projects_locations_clusters_instances.Patch(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations'
    )
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      instance_operations.Await(
          op_ref, 'Updating instance', self.ReleaseTrack(), False
      )
    return op


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Updates an AlloyDB instance within a given cluster."""

  @staticmethod
  def Args(parser):
    super(UpdateBeta, UpdateBeta).Args(parser)
    flags.AddUpdateMode(parser)
    flags.AddAssignInboundPublicIp(parser, update=True)
    flags.AddAuthorizedExternalNetworks(parser)

  def ConstructPatchRequestFromArgs(self, alloydb_messages, instance_ref, args):
    return instance_helper.ConstructPatchRequestFromArgsBeta(
        alloydb_messages, instance_ref, args
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Updates an AlloyDB instance within a given cluster."""

  @staticmethod
  def Args(parser):
    super(UpdateAlpha, UpdateAlpha).Args(parser)

  def ConstructPatchRequestFromArgs(self, alloydb_messages, instance_ref, args):
    return instance_helper.ConstructPatchRequestFromArgsAlpha(
        alloydb_messages, instance_ref, args
    )
