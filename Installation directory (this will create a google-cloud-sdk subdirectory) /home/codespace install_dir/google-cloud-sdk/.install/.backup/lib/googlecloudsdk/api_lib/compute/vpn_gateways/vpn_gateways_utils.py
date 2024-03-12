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
"""API utilities for gcloud compute vpn-gateways commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
import six


class VpnGatewayHelper(object):
  """Helper for VPN gateway service in the Compute API."""

  def __init__(self, holder):
    """Initializes the helper for VPN Gateway operations.

    Args:
      holder: Object representing the Compute API holder instance.
    """
    self._compute_client = holder.client
    self._resources = holder.resources

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  @property
  def _service(self):
    return self._client.vpnGateways

  def GetVpnGatewayForInsert(
      self,
      name,
      description,
      network,
      vpn_interfaces_with_interconnect_attachments,
      stack_type=None,
      gateway_ip_version=None,
  ):
    """Returns the VpnGateway message for an insert request.

    Args:
      name: String representing the name of the VPN Gateway resource.
      description: String representing the description for the VPN Gateway
        resource.
      network: String representing the network URL the VPN gateway resource
        belongs to.
      vpn_interfaces_with_interconnect_attachments: Dict representing pairs
        interface id and interconnected attachment associated with vpn gateway
        on this interface.
      stack_type: Enum presenting the stack type of the vpn gateway resource.
      gateway_ip_version: Enum presenting the gateway IP version of the vpn
        gateway resource.

    Returns:
      The VpnGateway message object that can be used in an insert request.
    """
    target_stack_type = None
    target_gateway_ip_version = None
    if stack_type is not None:
      target_stack_type = self._messages.VpnGateway.StackTypeValueValuesEnum(
          stack_type
      )
    if gateway_ip_version is not None:
      target_gateway_ip_version = (
          self._messages.VpnGateway.GatewayIpVersionValueValuesEnum(
              gateway_ip_version
          )
      )

    if vpn_interfaces_with_interconnect_attachments is not None:
      vpn_interfaces = []
      for key, value in sorted(
          vpn_interfaces_with_interconnect_attachments.items()):
        vpn_interfaces.append(
            self._messages.VpnGatewayVpnGatewayInterface(
                id=int(key), interconnectAttachment=six.text_type(value)))
      if gateway_ip_version is not None:
        return self._messages.VpnGateway(
            name=name,
            description=description,
            network=network,
            vpnInterfaces=vpn_interfaces,
            stackType=target_stack_type,
            gatewayIpVersion=target_gateway_ip_version,
        )
      return self._messages.VpnGateway(
          name=name,
          description=description,
          network=network,
          vpnInterfaces=vpn_interfaces,
          stackType=target_stack_type,
      )
    else:
      if gateway_ip_version is not None:
        return self._messages.VpnGateway(
            name=name,
            description=description,
            network=network,
            stackType=target_stack_type,
            gatewayIpVersion=target_gateway_ip_version,
        )
      return self._messages.VpnGateway(
          name=name,
          description=description,
          network=network,
          stackType=target_stack_type,
      )

  def WaitForOperation(self, vpn_gateway_ref, operation_ref, wait_message):
    """Waits for the specified operation to complete and returns the target.

    Args:
      vpn_gateway_ref: The VPN Gateway reference object.
      operation_ref: The operation reference object to wait for.
      wait_message: String representing the wait message to display while the
        operation is in progress.

    Returns:
      The resulting resource object after the operation completes.
    """
    operation_poller = poller.Poller(self._service, vpn_gateway_ref)
    return waiter.WaitFor(operation_poller, operation_ref, wait_message)

  def Create(self, ref, vpn_gateway):
    """Sends an Insert request for a VPN Gateway and returns the operation.

    Args:
      ref: The VPN Gateway reference object.
      vpn_gateway: The VPN Gateway message object to use in the insert request.

    Returns:
      The operation reference object for the insert request.
    """
    request = self._messages.ComputeVpnGatewaysInsertRequest(
        project=ref.project, region=ref.region, vpnGateway=vpn_gateway)
    operation = self._service.Insert(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.regionOperations')

  def Describe(self, ref):
    """Sends a Get request for a VPN Gateway and returns the resource.

    Args:
      ref: The VPN Gateway reference object.

    Returns:
      The VPN Gateway resource object.
    """
    request = self._messages.ComputeVpnGatewaysGetRequest(
        project=ref.project, region=ref.region, vpnGateway=ref.Name())
    return self._service.Get(request)

  def Delete(self, ref):
    """Sends a Delete request for a VPN Gateway and returns the operation.

    Args:
      ref: The VPN Gateway reference object.

    Returns:
      The operation reference object for the delete request.
    """
    request = self._messages.ComputeVpnGatewaysDeleteRequest(
        project=ref.project, region=ref.region, vpnGateway=ref.Name())
    operation = self._service.Delete(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.regionOperations')

  def List(self, project, filter_expr):
    """Yields a VPN Gateway resource from the list of VPN Gateways.

    Sends an AggregatedList request to obtain the list of VPN Gateways and
    yields the next VPN Gateway in this list.

    Args:
      project: String representing the project to use for the request.
      filter_expr: The expression used to filter the results.
    """
    next_page_token = None
    while True:
      request = self._messages.ComputeVpnGatewaysAggregatedListRequest(
          project=project, filter=filter_expr, pageToken=next_page_token)
      response = self._service.AggregatedList(request)
      next_page_token = response.nextPageToken
      for scoped_vpn_gateways in response.items.additionalProperties:
        for vpn_gateway in scoped_vpn_gateways.value.vpnGateways:
          yield vpn_gateway
      if not next_page_token:
        break

  def SetLabels(self, ref, existing_label_fingerprint, new_labels):
    """Sends a SetLabels request for a VPN Gateway and returns the operation.

    Args:
      ref: The VPN Gateway reference object.
      existing_label_fingerprint: The existing label fingerprint.
      new_labels: List of new label key, value pairs.

    Returns:
      The operation reference object for the SetLabels request.
    """

    set_labels_request = self._messages.RegionSetLabelsRequest(
        labelFingerprint=existing_label_fingerprint, labels=new_labels)
    request = self._messages.ComputeVpnGatewaysSetLabelsRequest(
        project=ref.project,
        region=ref.region,
        resource=ref.Name(),
        regionSetLabelsRequest=set_labels_request)
    operation = self._service.SetLabels(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.regionOperations')
