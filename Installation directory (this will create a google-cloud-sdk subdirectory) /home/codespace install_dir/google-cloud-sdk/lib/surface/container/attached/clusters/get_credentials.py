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
"""Command to get credentials of an Attached cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import attached as api_util
from googlecloudsdk.api_lib.container.gkemulticloud import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import kubeconfig
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class GetCredentials(base.Command):
  """Get credentials of an Attached cluster."""

  detailed_help = {
      'EXAMPLES': kubeconfig.COMMAND_EXAMPLE,
      'DESCRIPTION': kubeconfig.COMMAND_DESCRIPTION.format(
          cluster_type='Attached cluster'
      ),
  }

  @staticmethod
  def Args(parser):
    resource_args.AddAttachedClusterResourceArg(parser, 'to get credentials')
    flags.AddAuthProviderCmdPath(parser)

  def Run(self, args):
    """Runs the get-credentials command."""
    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAttachedClusterResourceArg(args).locationsId,
        self.ReleaseTrack(),
    ):
      cluster_ref = resource_args.ParseAttachedClusterResourceArg(args)
      cluster_client = api_util.ClustersClient()
      log.status.Print('Fetching cluster endpoint and auth data.')
      resp = cluster_client.Get(cluster_ref)
      if (
          resp.state
          != util.GetMessagesModule().GoogleCloudGkemulticloudV1AttachedCluster.StateValueValuesEnum.RUNNING
      ):
        log.warning(
            kubeconfig.NOT_RUNNING_MSG.format(cluster_ref.attachedClustersId)
        )
      context = kubeconfig.GenerateContext(
          'attached',
          cluster_ref.projectsId,
          cluster_ref.locationsId,
          cluster_ref.attachedClustersId,
      )

      kubeconfig.GenerateAttachedKubeConfig(
          resp,
          cluster_ref.attachedClustersId,
          context,
          args.auth_provider_cmd_path,
      )
