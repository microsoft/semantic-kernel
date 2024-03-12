# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to print access tokens for an Anthos cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import azure as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import kubeconfig


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class PrintAccessToken(base.Command):
  """Generate an access token for an Anthos cluster on Azure."""

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddAzureClusterResourceArg(parser, "to access")
    flags.AddExecCredential(parser)

  def Run(self, args):
    """Runs the print-access-token command."""
    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureClusterResourceArg(args).locationsId,
        self.ReleaseTrack(),
    ):
      cluster_ref = resource_args.ParseAzureClusterResourceArg(args)
      client = api_util.ClustersClient()
      response = client.GenerateAccessToken(cluster_ref)
      if args.exec_credential:
        return kubeconfig.ExecCredential(
            expiration_timestamp=response.expirationTime,
            access_token=response.accessToken,
        )
      return response
