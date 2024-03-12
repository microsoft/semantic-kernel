# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Creates a new AlloyDB secondary instance."""

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


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class CreateSecondary(base.CreateCommand):
  """Creates a new AlloyDB SECONDARY instance within a given cluster."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
        To create a new secondary instance, run:

          $ {command} my-instance --cluster=my-cluster --region=us-central1
        """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddCluster(parser, False)
    flags.AddAvailabilityType(parser)
    flags.AddInstance(parser)
    flags.AddRegion(parser)

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
    instance_resource = alloydb_messages.Instance()
    instance_ref = client.resource_parser.Create(
        'alloydb.projects.locations.clusters.instances',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
        clustersId=args.cluster,
        instancesId=args.instance,
    )
    instance_resource.name = instance_ref.RelativeName()
    instance_resource.instanceType = (
        alloydb_messages.Instance.InstanceTypeValueValuesEnum.SECONDARY
    )
    instance_resource.availabilityType = instance_helper.ParseAvailabilityType(
        alloydb_messages, args.availability_type)
    req = alloydb_messages.AlloydbProjectsLocationsClustersInstancesCreatesecondaryRequest(
        instance=instance_resource,
        instanceId=args.instance,
        parent=cluster_ref.RelativeName(),
    )
    op = alloydb_client.projects_locations_clusters_instances.Createsecondary(
        req
    )
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations'
    )
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      instance_operations.Await(
          op_ref, 'Creating secondary instance', self.ReleaseTrack()
      )
    return op
