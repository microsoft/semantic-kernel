# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for deleting networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.networks import flags


class Delete(base.DeleteCommand):
  r"""Delete Compute Engine networks.

  *{command}* deletes one or more Compute Engine
  networks. Networks can only be deleted when no other resources
  (e.g., virtual machine instances) refer to them.

  ## EXAMPLES

  To delete a network with the name 'network-name', run:

    $ {command} network-name

  To delete two networks with the names 'network-name1' and 'network-name2',
  run:

    $ {command} network-name1 network-name2

  """

  NETWORK_ARG = None

  @staticmethod
  def Args(parser):
    Delete.NETWORK_ARG = flags.NetworkArgument(plural=True)
    Delete.NETWORK_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.NetworksCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    network_refs = Delete.NETWORK_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(network_refs)

    requests = []
    for network_ref in network_refs:
      requests.append((client.apitools_client.networks, 'Delete',
                       client.messages.ComputeNetworksDeleteRequest(
                           **network_ref.AsDict())))

    return client.MakeRequests(requests)
