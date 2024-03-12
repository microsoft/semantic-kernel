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


class ExternalVpnGatewayHelper(object):
  """Helper for external VPN gateway service in the Compute API."""

  def __init__(self, holder):
    """Initializes the helper for external VPN Gateway operations.

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
    return self._client.externalVpnGateways

  def GetExternalVpnGatewayForInsert(self, name, description, redundancy_type,
                                     interfaces):
    """Returns the VpnGateway message for an insert request.

    Args:
      name: String representing the name of the external VPN Gateway resource.
      description: String representing the description for the VPN Gateway
        resource.
      redundancy_type: Redundancy type of the external VPN gateway.
      interfaces: list of interfaces for the external VPN gateway

    Returns:
      The ExternalVpnGateway message object that can be used in an insert
      request.
    """
    return self._messages.ExternalVpnGateway(
        name=name,
        description=description,
        redundancyType=redundancy_type,
        interfaces=interfaces)

  def WaitForOperation(self, external_vpn_gateway_ref, operation_ref,
                       wait_message):
    """Waits for the specified operation to complete and returns the target.

    Args:
      external_vpn_gateway_ref: The external VPN Gateway reference object.
      operation_ref: The operation reference object to wait for.
      wait_message: String representing the wait message to display while the
        operation is in progress.

    Returns:
      The resulting resource object after the operation completes.
    """
    operation_poller = poller.Poller(self._service, external_vpn_gateway_ref)
    return waiter.WaitFor(operation_poller, operation_ref, wait_message)

  def Create(self, ref, external_vpn_gateway):
    """Sends an Insert request for an external VPN Gateway.

    Args:
      ref: The external VPN Gateway reference object.
      external_vpn_gateway: The external VPN Gateway message object to use in
      the insert request.

    Returns:
      The operation reference object for the insert request.
    """
    request = self._messages.ComputeExternalVpnGatewaysInsertRequest(
        project=ref.project, externalVpnGateway=external_vpn_gateway)
    operation = self._service.Insert(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

  def Describe(self, ref):
    """Sends a Get request for an external VPN Gateway and returns the resource.

    Args:
      ref: The external VPN gateway reference object.

    Returns:
      The external VPN gateway resource object.
    """
    request = self._messages.ComputeExternalVpnGatewaysGetRequest(
        project=ref.project, externalVpnGateway=ref.Name())
    return self._service.Get(request)

  def Delete(self, ref):
    """Sends a Delete request for an external VPN Gateway.

    Args:
      ref: The external VPN Gateway reference object.

    Returns:
      The operation reference object for the delete request.
    """
    request = self._messages.ComputeExternalVpnGatewaysDeleteRequest(
        project=ref.project, externalVpnGateway=ref.Name())
    operation = self._service.Delete(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

  def SetLabels(self, ref, existing_label_fingerprint, new_labels):
    """Sends a SetLabels request and returns the operation.

    Args:
      ref: The External VPN Gateway reference object.
      existing_label_fingerprint: The existing label fingerprint.
      new_labels: List of new label key, value pairs.

    Returns:
      The operation reference object for the SetLabels request.
    """

    set_labels_request = self._messages.GlobalSetLabelsRequest(
        labelFingerprint=existing_label_fingerprint, labels=new_labels)
    request = self._messages.ComputeExternalVpnGatewaysSetLabelsRequest(
        project=ref.project,
        resource=ref.Name(),
        globalSetLabelsRequest=set_labels_request)
    operation = self._service.SetLabels(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.globalOperations')
