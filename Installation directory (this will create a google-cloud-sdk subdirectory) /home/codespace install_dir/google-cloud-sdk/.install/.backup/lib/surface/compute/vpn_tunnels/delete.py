# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for deleting vpn tunnels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.compute.vpn_tunnels import vpn_tunnels_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.vpn_tunnels import flags


_VPN_TUNNEL_ARG = flags.VpnTunnelArgument(plural=True)


class DeleteBatchPoller(poller.BatchPoller):

  def GetResult(self, operation_batch):
    # For delete operations, once the operation status is DONE, there is
    # nothing further to fetch.
    return


class Delete(base.DeleteCommand):
  """Delete VPN tunnels.

  *{command}* deletes one or more Compute Engine VPN tunnels.
  """

  @staticmethod
  def Args(parser):
    _VPN_TUNNEL_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.VpnTunnelsCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    helper = vpn_tunnels_utils.VpnTunnelHelper(holder)

    vpn_tunnel_refs = _VPN_TUNNEL_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    utils.PromptForDeletion(vpn_tunnel_refs, 'region')

    operation_refs = [helper.Delete(ref) for ref in vpn_tunnel_refs]
    wait_message = 'Deleting VPN {}'.format(
        ('tunnels' if (len(operation_refs) > 1) else 'tunnel'))
    operation_poller = DeleteBatchPoller(client,
                                         client.apitools_client.vpnTunnels)
    return waiter.WaitFor(operation_poller,
                          poller.OperationBatch(operation_refs), wait_message)
