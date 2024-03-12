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
"""Command to update a node pool in an Anthos cluster on Azure."""

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
To update a node pool named ``my-node-pool'' in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1 --node-version=NODE_VERSION
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a node pool in an Anthos cluster on Azure."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureNodePoolResourceArg(
        parser, 'to update', positional=True
    )

    flags.AddNodeVersion(parser, required=False)
    flags.AddAutoscaling(parser, required=False)
    flags.AddSSHPublicKey(parser, required=False)
    flags.AddAnnotationsForUpdate(parser, 'node pool')
    flags.AddValidateOnly(parser, 'update of the node pool')
    flags.AddEnableAutoRepair(parser, False)

    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(constants.AZURE_NODE_POOL_FORMAT)

  def Run(self, args):
    """Runs the update command."""
    location = resource_args.ParseAzureNodePoolResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      node_pool_ref = resource_args.ParseAzureNodePoolResourceArg(args)
      node_pool_client = api_util.NodePoolsClient()
      message = command_util.NodePoolMessage(
          node_pool_ref.azureNodePoolsId,
          action='Updating',
          cluster=node_pool_ref.azureClustersId,
      )
      return command_util.Update(
          resource_ref=node_pool_ref,
          resource_client=node_pool_client,
          args=args,
          message=message,
          kind=constants.AZURE_NODEPOOL_KIND,
      )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a node pool in an Anthos cluster on Azure."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    """Registers alpha track flags for this command."""
    Update.Args(parser)
