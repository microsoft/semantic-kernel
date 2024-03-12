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
"""Command to update an Anthos cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import azure as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To update a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1 --cluster-version=CLUSTER_VERSION --client=CLIENT
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an Anthos cluster on Azure."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    auth_config_group = parser.add_argument_group(
        'Authentication configuration', mutex=True
    )
    resource_args.AddAzureClusterAndClientResourceArgs(
        parser, auth_config_group, update=True
    )
    flags.AddAzureServicesAuthentication(auth_config_group, create=False)
    flags.AddClusterVersion(parser, required=False)
    flags.AddVMSize(parser)
    flags.AddAdminUsers(parser, create=False)
    flags.AddAdminGroups(parser)
    flags.AddSSHPublicKey(parser, required=False)
    flags.AddValidateOnly(parser, 'update of the cluster')
    flags.AddDescriptionForUpdate(parser)
    flags.AddAnnotationsForUpdate(parser, 'cluster')
    flags.AddLogging(parser)
    flags.AddMonitoringConfig(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(constants.AZURE_CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the update command."""
    location = resource_args.ParseAzureClusterResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      cluster_ref = resource_args.ParseAzureClusterResourceArg(args)
      cluster_client = api_util.ClustersClient()
      message = command_util.ClusterMessage(
          cluster_ref.azureClustersId, action='Updating'
      )
      return command_util.Update(
          resource_ref=cluster_ref,
          resource_client=cluster_client,
          args=args,
          message=message,
          kind=constants.AZURE_CLUSTER_KIND,
      )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update an Anthos cluster on Azure."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    """Registers alpha track flags for this command."""
    Update.Args(parser)
