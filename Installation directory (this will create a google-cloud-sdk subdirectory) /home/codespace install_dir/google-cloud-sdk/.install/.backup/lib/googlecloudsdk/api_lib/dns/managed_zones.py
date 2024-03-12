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
"""API client library for Cloud DNS managed zones."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import operations
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.core import log


class Client(object):
  """API client for Cloud DNS managed zones."""

  def __init__(self, version, client, messages=None, location=None):
    self.version = version
    self.client = client
    self._service = self.client.managedZones
    self.messages = messages or self.client.MESSAGES_MODULE
    self.location = location

  @classmethod
  def FromApiVersion(cls, version, location=None):
    return cls(version, util.GetApiClient(version), location=location)

  def Get(self, zone_ref):
    if self.location:
      return self._service.Get(
          self.messages.DnsManagedZonesGetRequest(
              project=zone_ref.project,
              managedZone=zone_ref.managedZone,
              location=self.location))
    return self._service.Get(
        self.messages.DnsManagedZonesGetRequest(
            project=zone_ref.project,
            managedZone=zone_ref.managedZone))

  def Patch(self,
            zone_ref,
            is_async,
            dnssec_config=None,
            description=None,
            labels=None,
            private_visibility_config=None,
            forwarding_config=None,
            peering_config=None,
            service_directory_config=None,
            cloud_logging_config=None,
            cleared_fields=None):
    """Managed Zones Update Request.

    Args:
      zone_ref: the managed zones being patched.
      is_async: if the PATCH operation is asynchronous.
      dnssec_config: zone DNSSEC config.
      description: zone description.
      labels: zone labels.
      private_visibility_config: zone visibility config.
      forwarding_config: zone forwarding config.
      peering_config: zone peering config.
      service_directory_config: zone service directory config.
      cloud_logging_config: Stackdriver logging config.
      cleared_fields: the fields that should be included in the request JSON as
        their default value (fields that are their default value will be omitted
        otherwise).

    Returns:
      The PATCH response, if operation is not asynchronous.
    """
    zone = self.messages.ManagedZone(
        name=zone_ref.Name(),
        dnssecConfig=dnssec_config,
        description=description,
        labels=labels)
    if private_visibility_config:
      zone.privateVisibilityConfig = private_visibility_config
    if forwarding_config:
      zone.forwardingConfig = forwarding_config
    if peering_config:
      zone.peeringConfig = peering_config
    if service_directory_config:
      zone.serviceDirectoryConfig = service_directory_config
    if cloud_logging_config:
      zone.cloudLoggingConfig = cloud_logging_config
    request = self.messages.DnsManagedZonesPatchRequest(
        managedZoneResource=zone,
        project=zone_ref.project,
        managedZone=zone_ref.Name())

    if self.location:
      request.location = self.location

    # Tell the client that the cleared fields should be included in the JSON as
    # their default value, otherwise they will be omitted.
    with self.client.IncludeFields(cleared_fields):
      operation = self.client.managedZones.Patch(request)

    operation_param = {
        'project': zone_ref.project,
        'managedZone': zone_ref.Name(),
    }

    if self.location:
      operation_param['location'] = self.location
    operation_ref = util.GetRegistry(self.version).Parse(
        operation.id,
        params=operation_param,
        collection='dns.managedZoneOperations')

    if is_async:
      log.status.write(
          'Updating [{0}] with operation [{1}].'.format(
              zone_ref.Name(), operation_ref.Name()))
      return

    return operations.WaitFor(
        self.version,
        operation_ref,
        'Updating managed zone [{}]'.format(zone_ref.Name()),
        self.location
    )

  def UpdateLabels(self, zone_ref, labels):
    """Update labels using Managed Zones Update request."""
    zone = self.Get(zone_ref)
    zone.labels = labels

    operation = self._service.Update(
        self.messages.DnsManagedZonesUpdateRequest(
            managedZoneResource=zone,
            project=zone_ref.project,
            managedZone=zone_ref.Name()))

    operation_param = {
        'project': zone_ref.project,
        'managedZone': zone_ref.Name(),
    }

    if self.location:
      operation_param['location'] = self.location
    operation_ref = util.GetRegistry(self.version).Parse(
        operation.id,
        params=operation_param,
        collection='dns.managedZoneOperations')

    return operations.WaitFor(
        self.version, operation_ref,
        'Updating managed zone [{}]'.format(zone_ref.Name()))
