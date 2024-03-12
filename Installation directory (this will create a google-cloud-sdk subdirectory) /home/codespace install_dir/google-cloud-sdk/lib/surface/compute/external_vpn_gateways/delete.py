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
"""Command to delete External VPN Gateway."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.external_vpn_gateways import external_vpn_gateways_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.external_vpn_gateways import flags


_EXTERNAL_VPN_GATEWAY_ARG = flags.ExternalVpnGatewayArgument(plural=True)


class DeleteBatchPoller(poller.BatchPoller):

  def GetResult(self, operation_batch):
    # For delete operations, once the operation status is DONE, there is
    # nothing further to fetch.
    return


class Delete(base.DeleteCommand):
  """Delete a Compute Engine external VPN gateway.

  *{command}* is used to delete all data associated with a Compute Engine
  external VPN gateway in a project.

  An external VPN gateway provides the information to Google Cloud
  about your on-premises side or another Cloud provider's VPN gateway.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To delete an external VPN gateway, run:

              $ {command} my-external-gateway"""
  }

  @staticmethod
  def Args(parser):
    _EXTERNAL_VPN_GATEWAY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.ExternalVpnGatewaysCompleter)

  def Run(self, args):
    """Issues the request to delete an external VPN gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = external_vpn_gateways_utils.ExternalVpnGatewayHelper(holder)
    client = holder.client.apitools_client
    refs = _EXTERNAL_VPN_GATEWAY_ARG.ResolveAsResource(args, holder.resources)
    utils.PromptForDeletion(refs)

    operation_refs = [helper.Delete(ref) for ref in refs]
    wait_message = 'Deleting external VPN {}'.format(
        ('gateways' if (len(operation_refs) > 1) else 'gateway'))
    operation_poller = DeleteBatchPoller(holder.client,
                                         client.externalVpnGateways)
    return waiter.WaitFor(operation_poller,
                          poller.OperationBatch(operation_refs), wait_message)
