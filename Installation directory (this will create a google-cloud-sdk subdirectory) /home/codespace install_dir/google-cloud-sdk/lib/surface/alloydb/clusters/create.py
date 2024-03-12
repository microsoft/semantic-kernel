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
"""Creates a new AlloyDB cluster."""

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


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new AlloyDB cluster within a given project."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To create a new cluster, run:

          $ {command} my-cluster --region=us-central1 --password=postgres
        """,
  }

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
    flags.AddNetwork(parser)
    flags.AddPassword(parser)
    flags.AddAllocatedIPRangeName(parser)
    kms_resource_args.AddKmsKeyResourceArg(
        parser,
        'cluster',
        permission_info="The 'AlloyDB Service Agent' service account must hold permission 'Cloud KMS CryptoKey Encrypter/Decrypter'"
    )
    flags.AddAutomatedBackupFlags(
        parser, alloydb_messages, cls.ReleaseTrack(), update=False
    )
    flags.AddContinuousBackupConfigFlags(parser, cls.ReleaseTrack())
    flags.AddDatabaseVersion(parser, alloydb_messages)

  def ConstructCreateRequestFromArgs(self, alloydb_messages, location_ref,
                                     args):
    return cluster_helper.ConstructCreateRequestFromArgsGA(
        alloydb_messages, location_ref, args)

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
    req = self.ConstructCreateRequestFromArgs(alloydb_messages, location_ref,
                                              args)
    op = alloydb_client.projects_locations_clusters.Create(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations')
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      cluster_operations.Await(op_ref, 'Creating cluster', self.ReleaseTrack())
    return op


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a new AlloyDB cluster within a given project."""

  @classmethod
  def Args(cls, parser):
    super(CreateBeta, cls).Args(parser)

  def ConstructCreateRequestFromArgs(
      self, alloydb_messages, location_ref, args
  ):
    return cluster_helper.ConstructCreateRequestFromArgsBeta(
        alloydb_messages, location_ref, args
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a new AlloyDB cluster within a given project."""

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    flags.AddEnablePrivateServicesConnect(parser)

  def ConstructCreateRequestFromArgs(
      self, alloydb_messages, location_ref, args
  ):
    return cluster_helper.ConstructCreateRequestFromArgsAlpha(
        alloydb_messages, location_ref, args
    )
