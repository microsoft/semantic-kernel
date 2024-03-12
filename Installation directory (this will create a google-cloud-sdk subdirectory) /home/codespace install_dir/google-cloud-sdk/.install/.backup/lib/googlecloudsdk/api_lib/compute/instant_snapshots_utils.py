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
"""Utilities for handling Compute InstantSnapshotsService and RegionInstantSnapshotsService."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
from googlecloudsdk.core.exceptions import Error
import six


class UnknownResourceError(Error):
  """Raised when a instant snapshot resource argument is neither regional nor zonal."""


class _CommonInstantSnapshot(six.with_metaclass(abc.ABCMeta, object)):
  """Common class for InstantSnapshot Service API client."""

  def GetService(self):
    return self._service

  def GetInstantSnapshotResource(self):
    request_msg = self.GetInstantSnapshotRequestMessage()
    return self._service.Get(request_msg)

  @abc.abstractmethod
  def GetInstantSnapshotRequestMessage(self):
    raise NotImplementedError

  @abc.abstractmethod
  def GetSetLabelsRequestMessage(self):
    raise NotImplementedError

  @abc.abstractmethod
  def GetSetInstantSnapshotLabelsRequestMessage(self):
    raise NotImplementedError


class _InstantSnapshot(_CommonInstantSnapshot):
  """A wrapper for Compute Engine InstantSnapshotsService API client."""

  def __init__(self, client, ips_ref, messages):
    _CommonInstantSnapshot.__init__(self)
    self._ips_ref = ips_ref
    self._client = client
    self._service = client.instantSnapshots
    self._messages = messages

  @classmethod
  def GetOperationCollection(cls):
    return 'compute.zoneOperations'

  def GetInstantSnapshotRequestMessage(self):
    return self._messages.ComputeInstantSnapshotsGetRequest(
        **self._ips_ref.AsDict())

  def GetSetLabelsRequestMessage(self):
    return self._messages.ZoneSetLabelsRequest

  def GetSetInstantSnapshotLabelsRequestMessage(self, ips, labels):
    req = self._messages.ComputeInstantSnapshotsSetLabelsRequest
    return req(
        project=self._ips_ref.project,
        resource=self._ips_ref.instantSnapshot,
        zone=self._ips_ref.zone,
        zoneSetLabelsRequest=self._messages.ZoneSetLabelsRequest(
            labelFingerprint=ips.labelFingerprint, labels=labels))


class _RegionInstantSnapshot(_CommonInstantSnapshot):
  """A wrapper for Compute Engine RegionInstantSnapshotService API client."""

  def __init__(self, client, ips_ref, messages):
    _CommonInstantSnapshot.__init__(self)
    self._ips_ref = ips_ref
    self._client = client
    self._service = client.regionInstantSnapshots
    self._messages = messages

  @classmethod
  def GetOperationCollection(cls):
    return 'compute.regionOperations'

  def GetInstantSnapshotRequestMessage(self):
    return self._messages.ComputeRegionInstantSnapshotsGetRequest(
        **self._ips_ref.AsDict())

  def GetSetLabelsRequestMessage(self):
    return self._messages.RegionSetLabelsRequest

  def GetSetInstantSnapshotLabelsRequestMessage(self, ips, labels):
    req = self._messages.ComputeRegionInstantSnapshotsSetLabelsRequest
    return req(
        project=self._ips_ref.project,
        resource=self._ips_ref.instantSnapshot,
        region=self._ips_ref.region,
        regionSetLabelsRequest=self._messages.RegionSetLabelsRequest(
            labelFingerprint=ips.labelFingerprint, labels=labels))


def IsZonal(ips_ref):
  """Checks if a compute instant snapshot is zonal or regional.

  Args:
    ips_ref: the instant snapshot resource reference that is parsed from
      resource arguments to modify.

  Returns:
    Boolean, true when the compute instant snapshot resource to modify is a
    zonal compute instant snapshot resource, false when a regional compute
    instant snapshot resource.

  Raises:
    UnknownResourceError: when the compute instant snapshot resource is not in
    the
      correct format.
  """
  # There are 2 types of instant snapshot services,
  # InstantSnapshotsService (by zone) and
  # RegionInstantSnapshotsService (by region).
  if ips_ref.Collection() == 'compute.instantSnapshots':
    return True
  elif ips_ref.Collection() == 'compute.regionInstantSnapshots':
    return False
  else:
    raise UnknownResourceError(
        'Unexpected instant snapshot resource argument of {}'.format(
            ips_ref.Collection()))


def GetInstantSnapshotInfo(ips_ref, client, messages):
  """Gets the zonal or regional instant snapshot api info.

  Args:
    ips_ref: the instant snapshot resource reference that is parsed from
      resource arguments.
    client: the compute api_tools_client.
    messages: the compute message module.

  Returns:
    _ZoneInstantSnapshot or _RegionInstantSnapshot.
  """
  if IsZonal(ips_ref):
    return _InstantSnapshot(client, ips_ref, messages)
  else:
    return _RegionInstantSnapshot(client, ips_ref, messages)
