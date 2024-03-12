# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Import cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Import(base.UpdateCommand):
  """Import a cluster.

  This will create a new cluster with the given configuration. If a cluster with
  this name already exists, an error will be thrown.
  """

  detailed_help = {
      'EXAMPLES': """
To import a cluster from a YAML file, run:

  $ {command} my-cluster --region=us-central1 --source=cluster.yaml

To import a cluster from standard output, run:

  $ {command} my-cluster --region=us-central1
"""
  }

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    return 'v1'

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddClusterResourceArg(parser, 'import', dataproc.api_version)
    export_util.AddImportFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    # 30m is backend timeout + 5m for safety buffer.
    flags.AddTimeoutFlag(parser, default='35m')

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages

    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)
    cluster = export_util.Import(message_type=msgs.Cluster, stream=data)

    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster.clusterName = cluster_ref.clusterName
    cluster.projectId = cluster_ref.projectId

    # Import only supports create, not update (for now).
    return clusters.CreateCluster(dataproc, cluster_ref, cluster, args.async_,
                                  args.timeout)
