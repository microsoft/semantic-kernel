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
"""Command to create an Anthos cluster on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Optional

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.vmware import constants as vmware_constants
from googlecloudsdk.command_lib.container.vmware import flags as vmware_flags
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


_EXAMPLES = """
To create a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Create an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    vmware_flags.AddClusterResourceArg(parser, 'to create', True)
    vmware_flags.AddAdminClusterMembershipResourceArg(parser, positional=False)
    base.ASYNC_FLAG.AddToParser(parser)
    vmware_flags.AddValidationOnly(parser)
    vmware_flags.AddDescription(parser)
    vmware_flags.AddVersion(parser, required=True)
    vmware_flags.AddClusterAnnotations(parser)
    vmware_flags.AddVmwareControlPlaneNodeConfig(
        parser, release_track=base.ReleaseTrack.ALPHA
    )
    vmware_flags.AddVmwareAAGConfig(parser)
    vmware_flags.AddVmwareStorageConfig(parser)
    vmware_flags.AddVmwareNetworkConfig(parser)
    vmware_flags.AddVmwareLoadBalancerConfig(parser)
    vmware_flags.AddVCenterConfig(parser)
    vmware_flags.AddVmwareDataplaneV2Config(parser)
    vmware_flags.AddEnableVmwareTracking(parser)
    vmware_flags.AddVmwareAutoRepairConfig(parser)
    vmware_flags.AddAuthorization(parser)
    vmware_flags.AddEnableControlPlaneV2(parser)
    vmware_flags.AddUpgradePolicy(parser)

  def Run(
      self, args: parser_extensions.Namespace
  ) -> Optional[messages.Operation]:
    """Runs the create command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation to be polled; otherwise, it returns a
      completed operation. If `--validate-only` is specified, it returns None or
      any possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return None

    if args.async_:
      log.CreatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      log.CreatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)

      return operation_response


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    vmware_flags.AddClusterResourceArg(parser, 'to create', True)
    vmware_flags.AddAdminClusterMembershipResourceArg(parser, positional=False)
    base.ASYNC_FLAG.AddToParser(parser)
    vmware_flags.AddValidationOnly(parser)
    vmware_flags.AddDescription(parser)
    vmware_flags.AddVersion(parser, required=True)
    vmware_flags.AddClusterAnnotations(parser)
    vmware_flags.AddVmwareControlPlaneNodeConfig(parser)
    vmware_flags.AddVmwareAAGConfig(parser)
    vmware_flags.AddVmwareStorageConfig(parser)
    vmware_flags.AddVmwareNetworkConfig(parser)
    vmware_flags.AddVmwareLoadBalancerConfig(parser)
    vmware_flags.AddVCenterConfig(parser)
    vmware_flags.AddVmwareDataplaneV2Config(parser)
    vmware_flags.AddEnableVmwareTracking(parser)
    vmware_flags.AddVmwareAutoRepairConfig(parser)
    vmware_flags.AddAuthorization(parser)
    vmware_flags.AddEnableControlPlaneV2(parser)
    vmware_flags.AddUpgradePolicy(parser)

  def Run(
      self, args: parser_extensions.Namespace
  ) -> Optional[messages.Operation]:
    """Runs the create command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation to be polled; otherwise, it returns a
      completed operation. If `--validate-only` is specified, it returns None or
      any possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return None

    if args.async_:
      log.CreatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      log.CreatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)

      return operation_response


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    vmware_flags.AddClusterResourceArg(parser, 'to create', True)
    vmware_flags.AddAdminClusterMembershipResourceArg(parser, positional=False)
    base.ASYNC_FLAG.AddToParser(parser)
    vmware_flags.AddValidationOnly(parser)
    vmware_flags.AddDescription(parser)
    vmware_flags.AddVersion(parser, required=True)
    vmware_flags.AddClusterAnnotations(parser)
    vmware_flags.AddVmwareControlPlaneNodeConfig(parser)
    vmware_flags.AddVmwareAAGConfig(parser)
    vmware_flags.AddVmwareStorageConfig(parser)
    vmware_flags.AddVmwareNetworkConfig(parser)
    vmware_flags.AddVmwareLoadBalancerConfig(parser)
    vmware_flags.AddVCenterConfig(parser)
    vmware_flags.AddVmwareDataplaneV2Config(parser)
    vmware_flags.AddEnableVmwareTracking(parser)
    vmware_flags.AddVmwareAutoRepairConfig(parser)
    vmware_flags.AddAuthorization(parser)
    vmware_flags.AddEnableControlPlaneV2(parser)
    vmware_flags.AddUpgradePolicy(parser)

  def Run(
      self, args: parser_extensions.Namespace
  ) -> Optional[messages.Operation]:
    """Runs the create command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation to be polled; otherwise, it returns a
      completed operation. If `--validate-only` is specified, it returns None or
      any possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return None

    if args.async_:
      log.CreatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      log.CreatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)

      return operation_response
