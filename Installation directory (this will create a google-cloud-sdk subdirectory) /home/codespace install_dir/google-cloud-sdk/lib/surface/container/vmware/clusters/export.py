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
"""Command to export an Anthos clusters on VMware API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.container.gkeonprem import vmware_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files

_EXAMPLES = """
A cluster can be exported to a file by running:

  $ {command} NAME --destination=<path-to-file>

A cluster can also be exported to stdout by running:

  $ {command} NAME
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Export(base.Command):
  """Export an Anthos on VMware user cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def GetSchemaPath(for_help=False):
    return export_util.GetSchemaPath(
        'gkeonprem', 'v1', 'VmwareCluster', for_help=for_help
    )

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    flags.AddClusterResourceArg(parser, 'to export')
    export_util.AddExportFlags(
        parser, schema_path=Export.GetSchemaPath(for_help=True)
    )

  def Run(self, args):
    cluster_ref = args.CONCEPTS.cluster.Parse()
    client = apis.ClustersClient()
    user_cluster = client.Describe(cluster_ref)

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(
            message=user_cluster,
            stream=stream,
            schema_path=self.GetSchemaPath(),
        )
    else:
      export_util.Export(
          message=user_cluster,
          stream=sys.stdout,
          schema_path=self.GetSchemaPath(),
      )
