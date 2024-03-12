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
"""Command to delete VPN Gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.compute.vpn_gateways import vpn_gateways_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.vpn_gateways import flags

_VPN_GATEWAY_ARG = flags.GetVpnGatewayArgument(plural=True)


class DeleteBatchPoller(poller.BatchPoller):

  def GetResult(self, operation_batch):
    # For delete operations, once the operation status is DONE, there is
    # nothing further to fetch.
    return


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete Compute Engine Highly Available VPN Gateways.

  *{command}* is used to delete one or more Compute Engine Highly
  Available VPN Gateways. VPN Gateways can only be deleted when no VPN tunnels
  refer to them.

  Highly Available VPN Gateway provides a means to create a VPN solution with a
  higher availability SLA compared to Classic Target VPN Gateway.
  Highly Available VPN gateways are simply referred to as VPN gateways in the
  API documentation and gcloud commands.
  A VPN Gateway can reference one or more VPN tunnels that connect it to
  external VPN gateways or Cloud VPN Gateways.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To delete a VPN gateway, run:

              $ {command} my-gateway --region=us-central1"""
  }

  @staticmethod
  def Args(parser):
    _VPN_GATEWAY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.VpnGatewaysCompleter)

  def Run(self, args):
    """Issues the request to delete a VPN Gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = vpn_gateways_utils.VpnGatewayHelper(holder)
    client = holder.client.apitools_client
    refs = _VPN_GATEWAY_ARG.ResolveAsResource(args, holder.resources)
    utils.PromptForDeletion(refs)

    operation_refs = [helper.Delete(ref) for ref in refs]
    wait_message = 'Deleting VPN {}'.format(
        ('Gateways' if (len(operation_refs) > 1) else 'Gateway'))
    operation_poller = DeleteBatchPoller(holder.client, client.vpnGateways)
    return waiter.WaitFor(operation_poller,
                          poller.OperationBatch(operation_refs), wait_message)
