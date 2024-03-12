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
"""Packet mirroring."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class PacketMirroring(object):
  """Abstracts PacketMirroring resource."""

  def __init__(self, ref, compute_client=None, registry=None):
    self.ref = ref
    self._compute_client = compute_client
    self._registry = registry

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  def _MakeCreateRequestTuple(self, packet_mirroring):
    return (self._client.packetMirrorings, 'Insert',
            self._messages.ComputePacketMirroringsInsertRequest(
                project=self.ref.project,
                region=self.ref.region,
                packetMirroring=packet_mirroring))

  def Create(self,
             packet_mirroring=None,
             only_generate_request=False,
             is_async=False):
    """Sends requests to create the packet mirroring."""
    requests = [self._MakeCreateRequestTuple(packet_mirroring)]

    if only_generate_request:
      return requests

    if not is_async:
      return self._compute_client.MakeRequests(requests)

    errors_to_collect = []
    result = self._compute_client.AsyncRequests(requests, errors_to_collect)[0]

    if errors_to_collect:
      raise exceptions.MultiError(errors_to_collect)

    operation_ref = self._registry.Parse(
        result.name,
        collection='compute.regionOperations',
        params={
            'project': self.ref.project,
            'region': self.ref.region,
        },
        api_version='v1')
    log.CreatedResource(
        operation_ref,
        kind='packet mirroring [{0}]'.format(self.ref.Name()),
        is_async=True,
        details='Run the [gcloud compute operations describe] command '
        'to check the status of this operation.')
    return result

  def _MakeUpdateRequestTuple(self, packet_mirroring):
    return (self._client.packetMirrorings, 'Patch',
            self._messages.ComputePacketMirroringsPatchRequest(
                project=self.ref.project,
                region=self.ref.region,
                packetMirroring=self.ref.Name(),
                packetMirroringResource=packet_mirroring))

  def Update(self,
             packet_mirroring=None,
             only_generate_request=False,
             is_async=False,
             cleared_fields=None):
    """Sends requests to update the packet mirroring."""
    requests = [self._MakeUpdateRequestTuple(packet_mirroring)]

    if only_generate_request:
      return requests

    errors_to_collect = []

    with self._client.IncludeFields(cleared_fields or []):
      if not is_async:
        return self._compute_client.MakeRequests(requests)
      result = self._compute_client.BatchRequests(requests,
                                                  errors_to_collect)[0]

    if errors_to_collect:
      raise exceptions.MultiError(errors_to_collect)

    operation_ref = self._registry.Parse(
        result.name,
        collection='compute.regionOperations',
        params={
            'project': self.ref.project,
            'region': self.ref.region,
        },
        api_version='v1')
    log.UpdatedResource(
        operation_ref,
        kind='packet mirroring [{0}]'.format(self.ref.Name()),
        is_async=True,
        details='Run the [gcloud compute operations describe] command '
        'to check the status of this operation.')
    return result

  def MakeDeleteRequestTuple(self):
    return (self._client.packetMirrorings, 'Delete',
            self._messages.ComputePacketMirroringsDeleteRequest(
                region=self.ref.region,
                project=self.ref.project,
                packetMirroring=self.ref.Name()))

  def Delete(self, only_generate_request=False):
    requests = [self.MakeDeleteRequestTuple()]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def _MakeDescribeRequestTuple(self):
    return (self._client.packetMirrorings, 'Get',
            self._messages.ComputePacketMirroringsGetRequest(
                region=self.ref.region,
                project=self.ref.project,
                packetMirroring=self.ref.Name()))

  def Describe(self, only_generate_request=False):
    requests = [self._MakeDescribeRequestTuple()]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests
