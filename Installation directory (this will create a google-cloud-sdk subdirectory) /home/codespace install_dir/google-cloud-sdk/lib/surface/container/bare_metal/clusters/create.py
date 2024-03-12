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
"""Command to create an Anthos cluster on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Optional

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_clusters as apis
from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import cluster_flags as bare_metal_flags
from googlecloudsdk.command_lib.container.bare_metal import constants as bare_metal_constants
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.gkeonprem import flags
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages

_EXAMPLES = """
To create a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Anthos cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_CLUSTERS_FORMAT
    )
    bare_metal_flags.AddClusterResourceArg(
        parser, verb='to create', positional=True
    )
    bare_metal_flags.AddAdminClusterMembershipResourceArg(
        parser, positional=False
    )
    base.ASYNC_FLAG.AddToParser(parser)
    bare_metal_flags.AddValidationOnly(parser)
    bare_metal_flags.AddDescription(parser)
    bare_metal_flags.AddAnnotations(parser)
    bare_metal_flags.AddVersion(parser)
    bare_metal_flags.AddNetworkConfig(parser)
    bare_metal_flags.AddLoadBalancerConfig(parser)
    bare_metal_flags.AddStorageConfig(parser)
    bare_metal_flags.AddControlPlaneConfig(parser)
    bare_metal_flags.AddProxyConfig(parser)
    bare_metal_flags.AddClusterOperationsConfig(parser)
    bare_metal_flags.AddMaintenanceConfig(parser)
    bare_metal_flags.AddWorkloadNodeConfig(parser)
    bare_metal_flags.AddSecurityConfig(parser)
    bare_metal_flags.AddNodeAccessConfig(parser)
    flags.AddBinauthzEvaluationMode(parser)

  def Run(self, args) -> Optional[messages.Operation]:
    """Runs the create command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the created
      resource. If `--validate-only` is specified, it returns None or any
      possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      return operation

    operation_client = operations.OperationsClient()
    operation_response = operation_client.Wait(operation)

    if not args.validate_only:
      log.CreatedResource(
          cluster_ref, 'Anthos cluster on bare metal', args.async_
      )
    return operation_response


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create an Anthos cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_CLUSTERS_FORMAT
    )
    bare_metal_flags.AddClusterResourceArg(
        parser, verb='to create', positional=True
    )
    bare_metal_flags.AddAdminClusterMembershipResourceArg(
        parser, positional=False
    )
    base.ASYNC_FLAG.AddToParser(parser)
    bare_metal_flags.AddValidationOnly(parser)
    bare_metal_flags.AddDescription(parser)
    bare_metal_flags.AddAnnotations(parser)
    bare_metal_flags.AddVersion(parser)
    bare_metal_flags.AddNetworkConfig(parser)
    bare_metal_flags.AddLoadBalancerConfig(parser)
    bare_metal_flags.AddStorageConfig(parser)
    bare_metal_flags.AddControlPlaneConfig(parser)
    bare_metal_flags.AddProxyConfig(parser)
    bare_metal_flags.AddClusterOperationsConfig(parser)
    bare_metal_flags.AddMaintenanceConfig(parser)
    bare_metal_flags.AddWorkloadNodeConfig(parser)
    bare_metal_flags.AddSecurityConfig(parser)
    bare_metal_flags.AddNodeAccessConfig(parser)
    flags.AddBinauthzEvaluationMode(parser)

  def Run(self, args) -> Optional[messages.Operation]:
    """Runs the create command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the created
      resource. If `--validate-only` is specified, it returns None or any
      possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      return operation

    operation_client = operations.OperationsClient()
    operation_response = operation_client.Wait(operation)

    if not args.validate_only:
      log.CreatedResource(
          cluster_ref, 'Anthos cluster on bare metal', args.async_
      )
    return operation_response


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Create an Anthos cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(
      parser: parser_arguments.ArgumentInterceptor,
  ) -> None:
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_CLUSTERS_FORMAT
    )
    bare_metal_flags.AddClusterResourceArg(
        parser, verb='to create', positional=True
    )
    bare_metal_flags.AddAdminClusterMembershipResourceArg(
        parser, positional=False
    )
    base.ASYNC_FLAG.AddToParser(parser)
    bare_metal_flags.AddValidationOnly(parser)
    bare_metal_flags.AddDescription(parser)
    bare_metal_flags.AddAnnotations(parser)
    bare_metal_flags.AddVersion(parser)
    bare_metal_flags.AddNetworkConfig(parser)
    bare_metal_flags.AddLoadBalancerConfig(parser)
    bare_metal_flags.AddStorageConfig(parser)
    bare_metal_flags.AddControlPlaneConfig(parser)
    bare_metal_flags.AddProxyConfig(parser)
    bare_metal_flags.AddClusterOperationsConfig(parser)
    bare_metal_flags.AddMaintenanceConfig(parser)
    bare_metal_flags.AddWorkloadNodeConfig(parser)
    bare_metal_flags.AddSecurityConfig(parser)
    bare_metal_flags.AddNodeAccessConfig(parser)
    flags.AddBinauthzEvaluationMode(parser)
    bare_metal_flags.AddUpgradePolicy(parser)

  def Run(self, args) -> Optional[messages.Operation]:
    """Runs the create command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the created
      resource. If `--validate-only` is specified, it returns None or any
      possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      return operation

    operation_client = operations.OperationsClient()
    operation_response = operation_client.Wait(operation)

    if not args.validate_only:
      log.CreatedResource(cluster_ref, 'Anthos cluster on bare metal',
                          args.async_)
    return operation_response
