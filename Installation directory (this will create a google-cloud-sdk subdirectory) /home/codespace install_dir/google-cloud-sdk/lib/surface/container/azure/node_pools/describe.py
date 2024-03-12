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

"""Command to describe a node pool in an Anthos cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import azure as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import versions
from googlecloudsdk.core import log

_EXAMPLES = """
To describe a node pool named ``my-node-pool'' in a cluster named
``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a node pool in an Anthos cluster on Azure."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureNodePoolResourceArg(parser, 'to describe')

  def Run(self, args):
    """Runs the describe command."""
    self._upgrade_hint = None
    node_pool_ref = resource_args.ParseAzureNodePoolResourceArg(args)
    with endpoint_util.GkemulticloudEndpointOverride(node_pool_ref.locationsId):
      node_pool_client = api_util.NodePoolsClient()
      node_pool_info = node_pool_client.Get(node_pool_ref)
      self._upgrade_hint = versions.upgrade_hint_node_pool(
          node_pool_ref, node_pool_info, constants.AZURE
      )

      return node_pool_info

  def Epilog(self, results_were_displayed):
    if self._upgrade_hint:
      log.status.Print(self._upgrade_hint)
