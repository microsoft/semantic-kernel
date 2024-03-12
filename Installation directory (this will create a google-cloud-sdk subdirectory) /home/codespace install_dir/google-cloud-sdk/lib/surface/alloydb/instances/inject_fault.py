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
"""Inject fault on an AlloyDB instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import instance_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class InjectFault(base.SilentCommand):
  """Inject fault on an AlloyDB instance within a given cluster."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
      To Inject fault on an instance, run:

        $ {command} my-instance --cluster=my-cluster --region=us-central1 --fault-type=stop-vm
      """,
  }

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser, Parser object for command line inputs
    """
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddCluster(parser, False)
    flags.AddInstance(parser)
    flags.AddRegion(parser)
    flags.AddFaultType(parser, True)

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
    fault_type = flags.GetInjectFaultTypeFlagMapper(
        alloydb_messages
    ).GetEnumForChoice(args.fault_type)
    project_ref = client.resource_parser.Create(
        'alloydb.projects.locations.clusters.instances',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
        clustersId=args.cluster,
        instancesId=args.instance,
    )
    req = alloydb_messages.AlloydbProjectsLocationsClustersInstancesInjectFaultRequest(
        name=project_ref.RelativeName(),
        injectFaultRequest=alloydb_messages.InjectFaultRequest(
            faultType=fault_type
        ),
    )
    op = alloydb_client.projects_locations_clusters_instances.InjectFault(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations'
    )
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      instance_operations.Await(
          op_ref, 'Injecting fault over instance', self.ReleaseTrack(), False
      )
    return op
