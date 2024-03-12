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
"""API utilities for gcloud compute vpn-tunnels commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter


class VpnTunnelHelper(object):
  """Helper for VPN tunnel service in the Compute API."""

  def __init__(self, holder):
    """Initializes the helper for VPN tunnel operations.

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
    return self._client.vpnTunnels

  def GetHighAvailabilityVpnTunnelForInsert(
      self, name, description, ike_version, peer_ip, shared_secret, vpn_gateway,
      vpn_gateway_interface, router, peer_external_gateway,
      peer_external_gateway_interface, peer_gcp_gateway):
    """Returns the HA VpnTunnel message for an insert request.

    Args:
      name: String representing the name of the VPN tunnel resource.
      description: String representing the description for the VPN tunnel
        resource.
      ike_version: The IKE protocol version for establishing the VPN tunnel.
      peer_ip: String representing the peer IP address for the VPN tunnel.
      shared_secret: String representing the shared secret (IKE pre-shared key).
      vpn_gateway: String representing the VPN Gateway URL the VPN tunnel
        resource should be associated with.
      vpn_gateway_interface: Integer representing the VPN Gateway interface ID
        that VPN tunnel resource should be associated with.
      router: String representing the Router URL the VPN tunnel resource should
        be associated with.
      peer_external_gateway: String representing of the peer side external VPN
        gateway to which the VPN tunnel is connected.
      peer_external_gateway_interface: Interface ID of the External VPN gateway
        to which this VPN tunnel is connected.
      peer_gcp_gateway:  String representing of peer side HA GCP VPN gateway
        to which this VPN tunnel is connected.

    Returns:
      The VpnTunnel message object that can be used in an insert request.
    """
    return self._messages.VpnTunnel(
        name=name,
        description=description,
        ikeVersion=ike_version,
        peerIp=peer_ip,
        sharedSecret=shared_secret,
        vpnGateway=vpn_gateway,
        vpnGatewayInterface=vpn_gateway_interface,
        router=router,
        peerExternalGateway=peer_external_gateway,
        peerExternalGatewayInterface=peer_external_gateway_interface,
        peerGcpGateway=peer_gcp_gateway)

  def GetClassicVpnTunnelForInsert(self,
                                   name,
                                   description,
                                   ike_version,
                                   peer_ip,
                                   shared_secret,
                                   target_vpn_gateway,
                                   router=None,
                                   local_traffic_selector=None,
                                   remote_traffic_selector=None):
    """Returns the Classic VpnTunnel message for an insert request.

    Args:
      name: String representing the name of the VPN tunnel resource.
      description: String representing the description for the VPN tunnel
        resource.
      ike_version: The IKE protocol version for establishing the VPN tunnel.
      peer_ip: String representing the peer IP address for the VPN tunnel.
      shared_secret: String representing the shared secret (IKE pre-shared key).
      target_vpn_gateway: String representing the Target VPN Gateway URL the VPN
        tunnel resource should be associated with.
      router: String representing the Router URL the VPN tunnel resource should
        be associated with.
      local_traffic_selector: List of strings representing the local CIDR ranges
        that should be able to send traffic using this VPN tunnel.
      remote_traffic_selector: List of strings representing the remote CIDR
        ranges that should be able to send traffic using this VPN tunnel.

    Returns:
      The VpnTunnel message object that can be used in an insert request.
    """
    return self._messages.VpnTunnel(
        name=name,
        description=description,
        ikeVersion=ike_version,
        peerIp=peer_ip,
        sharedSecret=shared_secret,
        targetVpnGateway=target_vpn_gateway,
        router=router,
        localTrafficSelector=local_traffic_selector or [],
        remoteTrafficSelector=remote_traffic_selector or [])

  def WaitForOperation(self, vpn_tunnel_ref, operation_ref, wait_message):
    """Waits for the specified operation to complete and returns the target.

    Args:
      vpn_tunnel_ref: The VPN tunnel reference object.
      operation_ref: The operation reference object to wait for.
      wait_message: String representing the wait message to display while the
        operation is in progress.

    Returns:
      The resulting resource object after the operation completes.
    """
    operation_poller = poller.Poller(self._service, vpn_tunnel_ref)
    return waiter.WaitFor(operation_poller, operation_ref, wait_message)

  def Create(self, ref, vpn_tunnel):
    """Sends an Insert request for a VPN tunnel and returns the operation.

    Args:
      ref: The VPN tunnel reference object.
      vpn_tunnel: The VPN tunnel message object to use in the insert request.

    Returns:
      The operation reference object for the insert request.
    """
    request = self._messages.ComputeVpnTunnelsInsertRequest(
        project=ref.project, region=ref.region, vpnTunnel=vpn_tunnel)
    operation = self._service.Insert(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.regionOperations')

  def Describe(self, ref):
    """Sends a Get request for a VPN tunnel and returns the resource.

    Args:
      ref: The VPN tunnel reference object.

    Returns:
      The VPN tunnel resource object.
    """
    request = self._messages.ComputeVpnTunnelsGetRequest(
        project=ref.project, region=ref.region, vpnTunnel=ref.Name())
    return self._service.Get(request)

  def Delete(self, ref):
    """Sends a Delete request for a VPN tunnel and returns the operation.

    Args:
      ref: The VPN tunnel reference object.

    Returns:
      The operation reference object for the delete request.
    """
    request = self._messages.ComputeVpnTunnelsDeleteRequest(
        project=ref.project, region=ref.region, vpnTunnel=ref.Name())
    operation = self._service.Delete(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.regionOperations')

  def List(self, project, filter_expr):
    """Yields a VPN tunnel resource from the list of VPN tunnels.

    Sends an AggregatedList request to obtain the list of VPN tunnels and
    yields the next VPN tunnel in this list.

    Args:
      project: String representing the project to use for the request.
      filter_expr: The expression used to filter the results.
    """
    next_page_token = None
    while True:
      request = self._messages.ComputeVpnTunnelsAggregatedListRequest(
          project=project, filter=filter_expr, pageToken=next_page_token)
      response = self._service.AggregatedList(request)
      next_page_token = response.nextPageToken
      for scoped_vpn_tunnels in response.items.additionalProperties:
        for vpn_tunnel in scoped_vpn_tunnels.value.vpnTunnels:
          yield vpn_tunnel
      if not next_page_token:
        break

  def SetLabels(self, ref, existing_label_fingerprint, new_labels):
    """Sends a SetLabels request for a VPN tunnel and returns the operation.

    Args:
      ref: The VPN tunnel reference object.
      existing_label_fingerprint: The existing label fingerprint.
      new_labels: List of new label key, value pairs.

    Returns:
      The operation reference object for the SetLabels request.
    """

    set_labels_request = self._messages.RegionSetLabelsRequest(
        labelFingerprint=existing_label_fingerprint, labels=new_labels)
    request = self._messages.ComputeVpnTunnelsSetLabelsRequest(
        project=ref.project,
        region=ref.region,
        resource=ref.Name(),
        regionSetLabelsRequest=set_labels_request)
    operation = self._service.SetLabels(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.regionOperations')
