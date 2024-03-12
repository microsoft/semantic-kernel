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
"""Command to import and update an Anthos clusters on VMware API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages

_EXAMPLES = """
A cluster can be imported by running:

  $ {command} NAME --source=<path-to-file>
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class UpdateFromFile(base.Command):
  """Update an Anthos on VMware user cluster using a configuration file."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def GetSchemaPath(for_help=False):
    return export_util.GetSchemaPath(
        'gkeonprem', 'v1', 'VmwareCluster', for_help=for_help
    )

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    flags.AddClusterResourceArg(parser, 'to import and update')
    export_util.AddImportFlags(
        parser, UpdateFromFile.GetSchemaPath(for_help=True)
    )
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddValidationOnly(parser)

  def Run(self, args):
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = apis.ClustersClient()
    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

    vmware_cluster = export_util.Import(
        message_type=messages.VmwareCluster,
        stream=data,
        schema_path=UpdateFromFile.GetSchemaPath(),
    )

    operation = cluster_client.UpdateFromFile(args, vmware_cluster)

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
