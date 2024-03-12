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
"""Command to update an Anthos cluster on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.vmware import constants as vmware_constants
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.core import log

_EXAMPLES = """
To update a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the update command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    flags.AddClusterResourceArg(parser, 'to update', True)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddValidationOnly(parser)
    flags.AddAllowMissingUpdateCluster(parser)
    flags.AddDescription(parser)
    flags.AddVersion(parser)
    flags.AddVmwareControlPlaneNodeConfig(parser, for_update=True)
    flags.AddVmwareAAGConfig(parser, for_update=True)
    flags.AddVmwareStorageConfig(parser, for_update=True)
    flags.AddVmwareNetworkConfig(parser, for_update=True)
    flags.AddVmwareLoadBalancerConfig(parser, for_update=True)
    flags.AddVmwareDataplaneV2Config(parser, for_update=True)
    flags.AddEnableVmwareTracking(parser, for_update=True)
    flags.AddVmwareAutoRepairConfig(parser, for_update=True)
    flags.AddAuthorization(parser)
    flags.AddUpdateAnnotations(parser)
    flags.AddUpgradePolicy(parser)

  def Run(self, args):
    """Runs the update command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the updated
      resource. If `--validate-only` is specified, it returns None or any
      possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Update(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return

    if args.async_:
      log.UpdatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      log.UpdatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)

      return operation_response


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the update command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    flags.AddClusterResourceArg(parser, 'to update', True)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddValidationOnly(parser)
    flags.AddAllowMissingUpdateCluster(parser)
    flags.AddDescription(parser)
    flags.AddVersion(parser)
    flags.AddVmwareControlPlaneNodeConfig(parser, for_update=True)
    flags.AddVmwareAAGConfig(parser, for_update=True)
    flags.AddVmwareStorageConfig(parser, for_update=True)
    flags.AddVmwareNetworkConfig(parser, for_update=True)
    flags.AddVmwareLoadBalancerConfig(parser, for_update=True)
    flags.AddVmwareDataplaneV2Config(parser, for_update=True)
    flags.AddEnableVmwareTracking(parser, for_update=True)
    flags.AddVmwareAutoRepairConfig(parser, for_update=True)
    flags.AddAuthorization(parser)
    flags.AddUpdateAnnotations(parser)
    flags.AddUpgradePolicy(parser)

  def Run(self, args):
    """Runs the update command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the updated
      resource. If `--validate-only` is specified, it returns None or any
      possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Update(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return

    if args.async_:
      log.UpdatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      log.UpdatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)

      return operation_response


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the update command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    flags.AddClusterResourceArg(parser, 'to update', True)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddValidationOnly(parser)
    flags.AddAllowMissingUpdateCluster(parser)
    flags.AddDescription(parser)
    flags.AddVersion(parser)
    flags.AddVmwareControlPlaneNodeConfig(parser, for_update=True)
    flags.AddVmwareAAGConfig(parser, for_update=True)
    flags.AddVmwareStorageConfig(parser, for_update=True)
    flags.AddVmwareNetworkConfig(parser, for_update=True)
    flags.AddVmwareLoadBalancerConfig(parser, for_update=True)
    flags.AddVmwareDataplaneV2Config(parser, for_update=True)
    flags.AddEnableVmwareTracking(parser, for_update=True)
    flags.AddVmwareAutoRepairConfig(parser, for_update=True)
    flags.AddAuthorization(parser)
    flags.AddUpdateAnnotations(parser)
    flags.AddUpgradePolicy(parser)

  def Run(self, args):
    """Runs the update command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the updated
      resource. If `--validate-only` is specified, it returns None or any
      possible error.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    operation = cluster_client.Update(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return

    if args.async_:
      log.UpdatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      log.UpdatedResource(cluster_ref, 'Anthos Cluster on VMware', args.async_)

      return operation_response
