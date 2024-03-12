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
"""Command to print access tokens for a GKE cluster on GEC."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.container import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
@base.Hidden
class PrintAccessToken(base.Command):
  """Generate an access token for an Edge Container cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    resource_args.AddClusterResourceArg(parser, "to access")

  def Run(self, args):
    """Run the command."""
    cluster_ref = args.CONCEPTS.cluster.Parse()

    messages = util.GetMessagesModule(self.ReleaseTrack())
    cluster_client = util.GetClientInstance(self.ReleaseTrack())
    req = messages.EdgecontainerProjectsLocationsClustersGenerateAccessTokenRequest(
        cluster=cluster_ref.RelativeName())
    resp = cluster_client.projects_locations_clusters.GenerateAccessToken(req)
    return resp
