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
"""List nodes command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.sole_tenancy.node_groups import flags


class ListNodes(base.ListCommand):
  """List Compute Engine sole-tenant nodes present in a node group."""

  detailed_help = {
      'brief':
          'List Compute Engine sole-tenant nodes present in a node'
          'group.',
      'EXAMPLES':
          """
         To list sole-tenant nodes present in a node group, run:

           $ {command} my-node-group
       """
  }

  @staticmethod
  def _Flags(parser):
    """Adds the flags for this command.

    Removes the URI flag since nodes don't have URIs.

    Args:
      parser: The argparse parser.
    """
    base.ListCommand._Flags(parser)

    base.URI_FLAG.RemoveFromParser(parser)

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(name, status, nodeType.basename(),'
        'instances.map().basename().list(), serverId)')
    flags.MakeNodeGroupArg().AddArgument(parser)

  def Run(self, args):
    """Retrieves response with nodes in the node group."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    group_ref = flags.MakeNodeGroupArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    request = client.messages.ComputeNodeGroupsListNodesRequest(
        nodeGroup=group_ref.Name(),
        zone=group_ref.zone,
        project=group_ref.project)

    errors = []
    results = list(
        request_helper.MakeRequests(
            requests=[(client.apitools_client.nodeGroups, 'ListNodes', request)
                     ],
            http=client.apitools_client.http,
            batch_url=client.batch_url,
            errors=errors))

    if errors:
      utils.RaiseToolException(errors)

    return self.getItems(results)

  def getItems(self, results):
    for result in results:
      for item in getattr(result, 'items'):
        yield item
