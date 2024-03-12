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
"""Command to upgrade an Edge Container cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.container import cluster
from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.container import flags as container_flags
from googlecloudsdk.command_lib.edge_cloud.container import print_warning
from googlecloudsdk.command_lib.edge_cloud.container import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_EXAMPLES = """
To upgrade an Edge Container cluster to 1.5.1 immediately, run:

$ {command} my-cluster --version=1.5.1 --schedule=IMMEDIATELY
"""

_API_REFERENCE_ = """
  This command uses the edgecontainer/{API} API. The full documentation for this
  API can be found at: https://cloud.google.com/edge-cloud
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Upgrade(base.Command):
  """Upgrade an Edge Container cluster."""

  detailed_help = {
      'EXAMPLES': _EXAMPLES,
      'API REFERENCE': _API_REFERENCE_.format(
          API=util.VERSION_MAP.get(base.ReleaseTrack.GA)
      ),
  }

  @staticmethod
  def Args(parser):
    resource_args.AddClusterResourceArg(parser, 'to upgrade')
    container_flags.AddUpgradeVersion(parser)
    container_flags.AddUpgradeSchedule(parser)

  def Run(self, args):
    cluster_ref = cluster.GetClusterReference(args)
    req = cluster.GetClusterUpgradeRequest(args, self.ReleaseTrack())
    cluster_client = util.GetClientInstance(self.ReleaseTrack())
    op = cluster_client.projects_locations_clusters.Upgrade(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='edgecontainer.projects.locations.operations'
    )

    log.status.Print(
        'Upgrade request issued for: [{cluster}]\nCheck operation [{operation}]'
        ' for status.'.format(
            cluster=cluster_ref.clustersId, operation=op_ref.RelativeName()
        )
    )

    return print_warning.PrintWarning(op, None)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpgradeAlpha(Upgrade):
  """Upgrade an Edge Container cluster."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    Upgrade.detailed_help['API REFERENCE'] = _API_REFERENCE_.format(
        API=util.VERSION_MAP.get(track)
    )
    Upgrade.Args(parser)
