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

"""Create a cluster from a file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateFromFile(base.CreateCommand):
  """Create a cluster from a file."""

  detailed_help = {
      'EXAMPLES': """
To create a cluster from a YAML file, run:

  $ {command} --file=cluster.yaml
"""
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--file',
        help="""
        The path to a YAML file containing a Dataproc Cluster resource.

        For more information, see:
        https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters#Cluster.
        """,
        required=True)
    # TODO(b/80197067): Move defaults to a common location.
    flags.AddTimeoutFlag(parser, default='35m')
    flags.AddRegionFlag(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    data = console_io.ReadFromFileOrStdin(args.file or '-', binary=False)
    cluster = export_util.Import(
        message_type=dataproc.messages.Cluster, stream=data)
    cluster_ref = util.ParseCluster(cluster.clusterName, dataproc)
    return clusters.CreateCluster(dataproc, cluster_ref, cluster, args.async_,
                                  args.timeout)
