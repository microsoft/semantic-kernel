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
"""Updates a AlloyDB cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import cluster_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.alloydb import cluster_helper
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Update(base.UpdateCommand):
  """Update an AlloyDB cluster within a given project and region."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To update a cluster, run:

          $ {command} my-cluster --region=us-central1 --automated-backup-start-times=12:00 --automated-backup-days-of-week=MONDAY --automated-backup-retention-count=10
        """,
  }

  def __init__(self, *args, **kwargs):
    super(Update, self).__init__(*args, **kwargs)
    self.parameters = [
        (
            '--automated-backup-* | --disable-automated-backup | '
            '--clear-automated-backup'
        ),
        (
            '--enable-continuous-backup | '
            '--continuous-backup-* | --clear-continuous-backup-encryption-key'
        ),
    ]

  @classmethod
  def Args(cls, parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    alloydb_messages = api_util.GetMessagesModule(cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddRegion(parser)
    flags.AddCluster(parser)
    flags.AddAutomatedBackupFlags(
        parser, alloydb_messages, cls.ReleaseTrack(), update=True
    )
    flags.AddContinuousBackupConfigFlags(
        parser, cls.ReleaseTrack(), update=True
    )

  def ConstructPatchRequestFromArgs(self, alloydb_messages, cluster_ref, args):
    return cluster_helper.ConstructPatchRequestFromArgsGA(
        alloydb_messages, cluster_ref, args)

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
    req = self.ConstructPatchRequestFromArgs(alloydb_messages, cluster_ref,
                                             args)
    if not req.updateMask:
      raise exceptions.MinimumArgumentException(
          self.parameters, 'Please specify at least one property to update')
    op = alloydb_client.projects_locations_clusters.Patch(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations')
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      cluster_operations.Await(op_ref, 'Updating cluster', self.ReleaseTrack(),
                               False)
    return op
