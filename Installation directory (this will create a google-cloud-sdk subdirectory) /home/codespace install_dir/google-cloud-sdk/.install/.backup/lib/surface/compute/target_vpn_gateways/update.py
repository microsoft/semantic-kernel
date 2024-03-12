# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to update labels for target VPN gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.target_vpn_gateways import flags as target_vpn_gateway_flags
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  r"""Update a Compute Engine Cloud VPN Classic Target VPN Gateway.

  *{command}* updates labels for a Compute Engine Cloud VPN Classic
  Target VPN gateway.  For example:

    $ {command} example-gateway --region us-central1 \
      --update-labels=k0=value1,k1=value2 --remove-labels=k3

  will add/update labels ``k0'' and ``k1'' and remove labels with key ``k3''.

  Labels can be used to identify the target VPN gateway and to filter them as in

    $ {parent_command} list --filter='labels.k1:value2'

  To list existing labels

    $ {parent_command} describe example-gateway --format="default(labels)"

  """

  TARGET_VPN_GATEWAY_ARG = None

  @classmethod
  def Args(cls, parser):
    """Adds arguments to the supplied parser.

    Args:
      parser: The argparse parser to add arguments to.
    """
    cls.TARGET_VPN_GATEWAY_ARG = (
        target_vpn_gateway_flags.TargetVpnGatewayArgument())
    cls.TARGET_VPN_GATEWAY_ARG.AddArgument(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def _CreateRegionalSetLabelsRequest(self, messages, target_vpn_gateway_ref,
                                      target_vpn_gateway, replacement):
    """Creates the API request to update labels on a Target VPN Gateway.

    Args:
      messages: Module with request messages.
      target_vpn_gateway_ref: Resource reference for the target VPN gateway.
      target_vpn_gateway: The target_vpn_gateway being updated.
      replacement: A new labels request proto representing the update and remove
                   edits.
    Returns:
      Request to be sent to update the target VPN gateway's labels.
    """
    return messages.ComputeTargetVpnGatewaysSetLabelsRequest(
        project=target_vpn_gateway_ref.project,
        resource=target_vpn_gateway_ref.Name(),
        region=target_vpn_gateway_ref.region,
        regionSetLabelsRequest=messages.RegionSetLabelsRequest(
            labelFingerprint=target_vpn_gateway.labelFingerprint,
            labels=replacement))

  def Run(self, args):
    """Issues API requests to update a Target VPN Gateway.

    Args:
      args: argparse.Namespace, The arguments received by this command.
    Returns:
      [protorpc.messages.Message], A list of responses returned
      by the compute API.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    target_vpn_gateway_ref = self.TARGET_VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if not labels_diff.MayHaveUpdates():
      raise calliope_exceptions.RequiredArgumentException(
          'LABELS', 'At least one of --update-labels or '
          '--remove-labels must be specified.')

    target_vpn_gateway = client.targetVpnGateways.Get(
        messages.ComputeTargetVpnGatewaysGetRequest(
            **target_vpn_gateway_ref.AsDict()))
    labels_value = messages.RegionSetLabelsRequest.LabelsValue

    labels_update = labels_diff.Apply(labels_value, target_vpn_gateway.labels)

    if not labels_update.needs_update:
      return target_vpn_gateway

    request = self._CreateRegionalSetLabelsRequest(
        messages, target_vpn_gateway_ref, target_vpn_gateway,
        labels_update.labels)

    operation = client.targetVpnGateways.SetLabels(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.regionOperations')

    operation_poller = poller.Poller(client.targetVpnGateways)

    return waiter.WaitFor(operation_poller, operation_ref,
                          'Updating labels of target VPN gateway [{0}]'.format(
                              target_vpn_gateway_ref.Name()))
