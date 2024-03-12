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
"""Utilities for handling Compute DisksService and RegionDisksService."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.core.exceptions import Error


_THROUGHPUT_PROVISIONING_SUPPORTED_DISK_TYPES = (
    'cs-throughput',
    'hyperdisk-throughput',
    'hyperdisk-balanced',
    'hyperdisk-ml',
)


class UnknownDiskResourceError(Error):
  """Raised when a disk resource argument is neither regional nor zonal."""


class _ZonalDisk(object):
  """A wrapper for Compute Engine DisksService API client."""

  def __init__(self, client, disk_ref, messages):
    self._disk_ref = disk_ref
    self._client = client
    self._service = client.disks or client.apitools_client.disks
    self._messages = messages

  @classmethod
  def GetOperationCollection(cls):
    """Gets the zonal operation collection of a compute disk reference."""
    return 'compute.zoneOperations'

  def GetService(self):
    return self._service

  def GetDiskRequestMessage(self):
    """Gets the zonal compute disk get request message."""
    return self._messages.ComputeDisksGetRequest(**self._disk_ref.AsDict())

  def GetDiskResource(self):
    request_msg = self.GetDiskRequestMessage()
    return self._service.Get(request_msg)

  def GetSetLabelsRequestMessage(self):
    return self._messages.ZoneSetLabelsRequest

  def GetSetDiskLabelsRequestMessage(self, disk, labels):
    req = self._messages.ComputeDisksSetLabelsRequest
    return req(
        project=self._disk_ref.project,
        resource=self._disk_ref.disk,
        zone=self._disk_ref.zone,
        zoneSetLabelsRequest=self._messages.ZoneSetLabelsRequest(
            labelFingerprint=disk.labelFingerprint, labels=labels))

  def GetDiskRegionName(self):
    return compute_utils.ZoneNameToRegionName(self._disk_ref.zone)

  def MakeAddResourcePoliciesRequest(self, resource_policies,
                                     client_to_make_request):
    add_request = self._messages.ComputeDisksAddResourcePoliciesRequest(
        disk=self._disk_ref.Name(),
        project=self._disk_ref.project,
        zone=self._disk_ref.zone,
        disksAddResourcePoliciesRequest=self._messages
        .DisksAddResourcePoliciesRequest(resourcePolicies=resource_policies))
    return client_to_make_request.MakeRequests(
        [(self._client.disks, 'AddResourcePolicies', add_request)])

  def MakeRemoveResourcePoliciesRequest(self, resource_policies,
                                        client_to_make_request):
    remove_request = self._messages.ComputeDisksRemoveResourcePoliciesRequest(
        disk=self._disk_ref.Name(),
        project=self._disk_ref.project,
        zone=self._disk_ref.zone,
        disksRemoveResourcePoliciesRequest=self._messages
        .DisksRemoveResourcePoliciesRequest(resourcePolicies=resource_policies))
    return client_to_make_request.MakeRequests(
        [(self._client.disks, 'RemoveResourcePolicies', remove_request)])


class _RegionalDisk(object):
  """A wrapper for Compute Engine RegionDisksService API client."""

  def __init__(self, client, disk_ref, messages):
    self._disk_ref = disk_ref
    self._client = client
    self._service = client.regionDisks
    self._messages = messages

  @classmethod
  def GetOperationCollection(cls):
    return 'compute.regionOperations'

  def GetService(self):
    return self._service

  def GetDiskRequestMessage(self):
    return self._messages.ComputeRegionDisksGetRequest(
        **self._disk_ref.AsDict())

  def GetDiskResource(self):
    request_msg = self.GetDiskRequestMessage()
    return self._service.Get(request_msg)

  def GetSetLabelsRequestMessage(self):
    return self._messages.RegionSetLabelsRequest

  def GetSetDiskLabelsRequestMessage(self, disk, labels):
    req = self._messages.ComputeRegionDisksSetLabelsRequest
    return req(
        project=self._disk_ref.project,
        resource=self._disk_ref.disk,
        region=self._disk_ref.region,
        regionSetLabelsRequest=self._messages.RegionSetLabelsRequest(
            labelFingerprint=disk.labelFingerprint, labels=labels))

  def GetDiskRegionName(self):
    return self._disk_ref.region

  def MakeAddResourcePoliciesRequest(self, resource_policies,
                                     client_to_make_request):
    add_request = self._messages.ComputeRegionDisksAddResourcePoliciesRequest(
        disk=self._disk_ref.Name(),
        project=self._disk_ref.project,
        region=self._disk_ref.region,
        regionDisksAddResourcePoliciesRequest=self._messages
        .RegionDisksAddResourcePoliciesRequest(
            resourcePolicies=resource_policies))
    return client_to_make_request.MakeRequests(
        [(self._client.regionDisks, 'AddResourcePolicies', add_request)])

  def MakeRemoveResourcePoliciesRequest(self, resource_policies,
                                        client_to_make_request):
    remove_request = self._messages.ComputeRegionDisksRemoveResourcePoliciesRequest(  # pylint:disable=line-too-long
        disk=self._disk_ref.Name(),
        project=self._disk_ref.project,
        region=self._disk_ref.region,
        regionDisksRemoveResourcePoliciesRequest=self._messages
        .RegionDisksRemoveResourcePoliciesRequest(
            resourcePolicies=resource_policies))
    return client_to_make_request.MakeRequests(
        [(self._client.regionDisks, 'RemoveResourcePolicies', remove_request)])


def IsZonal(disk_ref):
  """Checks if a compute disk is zonal or regional.

  Args:
    disk_ref: the disk resource reference that is parsed from resource arguments
      to modify.

  Returns:
    Boolean, true when the compute disk resource to modify is a zonal compute
      disk resource, false when a regional compute disk resource.

  Raises:
    UnknownDiskResourceError: when the compute disk resource is not in the
      correct format.
  """
  # There are 2 types of disk services, DisksService (by zone) and
  # RegionDisksService (by region).
  if disk_ref.Collection() == 'compute.disks':
    return True
  elif disk_ref.Collection() == 'compute.regionDisks':
    return False
  else:
    raise UnknownDiskResourceError(
        'Unexpected disk resource argument of {}'.format(disk_ref.Collection()))


def GetDiskInfo(disk_ref, client, messages):
  """Gets the zonal or regional disk api info.

  Args:
    disk_ref: the disk resource reference that is parsed from resource
      arguments.
    client: the compute api_tools_client.
    messages: the compute message module.

  Returns:
    _ZonalDisk or _RegionalDisk.
  """
  if IsZonal(disk_ref):
    return _ZonalDisk(client, disk_ref, messages)
  else:
    return _RegionalDisk(client, disk_ref, messages)


def IsProvisioningTypeIops(disk_type):
  """Check if the given disk type (name or URI) supports IOPS provisioning.

  Args:
    disk_type: name of URI of the disk type to be checked.

  Returns:
    Whether the disk_type supports IOPS provisioning.
  """

  return (disk_type.endswith('/pd-extreme') or
          disk_type.endswith('/cs-extreme') or
          disk_type.endswith('/hyperdisk-extreme') or
          disk_type.endswith('/hyperdisk-balanced') or
          disk_type in ['pd-extreme', 'cs-extreme', 'hyperdisk-extreme',
                        'hyperdisk-balanced'])


def IsProvisioningTypeThroughput(disk_type):
  """Check if the given disk type (name or URI) supports throughput provisioning.

  Args:
    disk_type: name of URI of the disk type to be checked.

  Returns:
    Boolean, true if the disk_type supports throughput provisioning, false
    otherwise.
  """

  return (
      disk_type.endswith('/cs-throughput')
      or disk_type.endswith('/hyperdisk-throughput')
      or disk_type.endswith('/hyperdisk-balanced')
      or disk_type.endswith('/hyperdisk-ml')
      or disk_type in _THROUGHPUT_PROVISIONING_SUPPORTED_DISK_TYPES
  )
