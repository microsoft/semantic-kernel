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

"""Command to list node pools in an Anthos cluster on Azure."""

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
To list all node pools in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} --cluster=my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List node pools in an Anthos cluster on Azure."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClusterResourceArg(
        parser, 'to list Azure node pools', positional=False
    )
    parser.display_info.AddFormat(constants.AZURE_NODE_POOL_FORMAT)

  def Run(self, args):
    """Runs the list command."""
    self._upgrade_hint = None
    cluster_ref = args.CONCEPTS.cluster.Parse()
    with endpoint_util.GkemulticloudEndpointOverride(cluster_ref.locationsId):
      api_client = api_util.NodePoolsClient()
      items, is_empty = api_client.List(
          cluster_ref, page_size=args.page_size, limit=args.limit
      )
      if is_empty:
        return items

      platform = constants.AZURE
      node_pool_info_table, end_of_life_flag = (
          versions.generate_node_pool_versions_table(
              cluster_ref,
              platform,
              items,
          )
      )
      if end_of_life_flag:
        self._upgrade_hint = versions.upgrade_hint_node_pool_list(
            platform, cluster_ref
        )
      return node_pool_info_table

  def Epilog(self, results_were_displayed):
    super(List, self).Epilog(results_were_displayed)
    if self._upgrade_hint:
      log.status.Print(self._upgrade_hint)
