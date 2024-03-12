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
"""Restores an AlloyDB cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import cluster_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import cluster_helper
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Restore(base.RestoreCommand):
  """Restore an AlloyDB cluster from a given backup or a source cluster and a timestamp."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To restore a cluster from a backup, run:

              $ {command} my-cluster --region=us-central1 --backup=my-backup

          To restore a cluster from a source cluster and a timestamp, run:

              $ {command} my-cluster --region=us-central1 \
                --source-cluster=old-cluster \
                --point-in-time=2012-11-15T16:19:00.094Z
        """,
  }

  @staticmethod
  def CommonArgs(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddCluster(parser)
    flags.AddRegion(parser)
    flags.AddNetwork(parser)
    flags.AddAllocatedIPRangeName(parser)
    kms_resource_args.AddKmsKeyResourceArg(
        parser,
        'cluster',
        permission_info=(
            "The 'AlloyDB Service Agent' service account must hold permission"
            " 'Cloud KMS CryptoKey Encrypter/Decrypter'"
        ),
    )

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """
    Restore.CommonArgs(parser)
    flags.AddRestoreClusterSourceFlags(parser)

  def ConstructRestoreRequestFromArgs(self, alloydb_messages, location_ref,
                                      resource_parser, args):
    return cluster_helper.ConstructRestoreRequestFromArgsGA(
        alloydb_messages, location_ref, resource_parser, args)

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
    location_ref = client.resource_parser.Create(
        'alloydb.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region)

    req = self.ConstructRestoreRequestFromArgs(
        alloydb_messages, location_ref, client.resource_parser, args)

    op = alloydb_client.projects_locations_clusters.Restore(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations')
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      cluster_operations.Await(op_ref, 'Restoring cluster', self.ReleaseTrack())
    return op


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RestoreAlpha(Restore):
  """Restore an AlloyDB cluster from a given backup or a source cluster and a timestamp."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To restore a cluster from a backup, run:

              $ {command} my-cluster --region=us-central1 --backup=my-backup

          To restore a cluster from a source cluster and a timestamp, run:

              $ {command} my-cluster --region=us-central1 \
                --source-cluster=old-cluster \
                --point-in-time=2012-11-15T16:19:00.094Z
        """,
  }

  @classmethod
  def Args(cls, parser):
    super(RestoreAlpha, cls).Args(parser)
    flags.AddEnablePrivateServicesConnect(parser)

  def ConstructRestoreRequestFromArgs(
      self, alloydb_messages, location_ref, resource_parser, args
  ):
    return cluster_helper.ConstructRestoreRequestFromArgsAlpha(
        alloydb_messages, location_ref, resource_parser, args
    )
