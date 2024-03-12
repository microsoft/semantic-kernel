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

"""Helpers for constructing messages for instance configs requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.instance_groups.flags import AutoDeleteFlag
from googlecloudsdk.command_lib.compute.instance_groups.flags import STATEFUL_IP_DEFAULT_INTERFACE_NAME
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_disk_getter
import six


def GetMode(messages, mode):
  """Returns mode message based on short user friendly string."""
  enum_class = messages.PreservedStatePreservedDisk.ModeValueValuesEnum
  if isinstance(mode, six.string_types):
    return {
        'ro': enum_class.READ_ONLY,
        'rw': enum_class.READ_WRITE,
    }[mode]
  else:
    # handle converting from AttachedDisk.ModeValueValuesEnum
    return enum_class(mode.name)


def MakePreservedStateDiskEntry(messages, stateful_disk_data, disk_getter):
  """Prepares disk preserved state entry, combining with params from the instance."""
  if stateful_disk_data.get('source'):
    source = stateful_disk_data.get('source')
    mode = stateful_disk_data.get('mode', 'rw')
  else:
    disk = disk_getter.get_disk(
        device_name=stateful_disk_data.get('device-name'))
    if disk is None:
      if disk_getter.instance_exists:
        error_message = ('[source] is required because the disk with the '
                         '[device-name]: `{0}` is not yet configured in the '
                         'instance config'.format(
                             stateful_disk_data.get('device-name')))
      else:
        error_message = ('[source] must be given while defining stateful disks '
                         'in instance configs for new instances')
      raise exceptions.BadArgumentException('stateful_disk', error_message)
    source = disk.source
    mode = stateful_disk_data.get('mode') or disk.mode
  preserved_disk = (
      messages.PreservedStatePreservedDisk(
          autoDelete=(stateful_disk_data.get('auto-delete') or
                      AutoDeleteFlag.NEVER).GetAutoDeleteEnumValue(
                          messages.PreservedStatePreservedDisk
                          .AutoDeleteValueValuesEnum),
          source=source,
          mode=GetMode(messages, mode)))
  return messages.PreservedState.DisksValue.AdditionalProperty(
      key=stateful_disk_data.get('device-name'), value=preserved_disk)


def MakePreservedStateMetadataEntry(messages, key, value):
  return messages.PreservedState.MetadataValue.AdditionalProperty(
      key=key,
      value=value
  )


def _CreateIpAddress(messages, ip_address):
  # Checking if the address is not an IP v4 address, assumed to be a URL then.
  if re.search('[A-Za-z]', ip_address):
    return messages.PreservedStatePreservedNetworkIpIpAddress(
        address=ip_address)
  else:
    return messages.PreservedStatePreservedNetworkIpIpAddress(
        literal=ip_address)


def _MakePreservedStateNetworkIpEntry(messages, stateful_ip):
  """Prepares stateful ip preserved state entry."""
  auto_delete = (stateful_ip.get('auto-delete') or
                 AutoDeleteFlag.NEVER).GetAutoDeleteEnumValue(
                     messages.PreservedStatePreservedNetworkIp
                     .AutoDeleteValueValuesEnum)
  address = None
  if stateful_ip.get('address'):
    ip_address = stateful_ip.get('address')
    address = _CreateIpAddress(messages, ip_address)
  return messages.PreservedStatePreservedNetworkIp(
      autoDelete=auto_delete,
      ipAddress=address)


def PatchPreservedStateNetworkIpEntry(messages, stateful_ip_to_patch,
                                      update_stateful_ip):
  """Prepares stateful ip preserved state entry."""
  auto_delete = update_stateful_ip.get('auto-delete')
  if auto_delete:
    stateful_ip_to_patch.autoDelete = auto_delete.GetAutoDeleteEnumValue(
        messages.PreservedStatePreservedNetworkIp.AutoDeleteValueValuesEnum)
  ip_address = update_stateful_ip.get('address')
  if ip_address:
    stateful_ip_to_patch.ipAddress = _CreateIpAddress(messages, ip_address)
  return stateful_ip_to_patch


def MakePreservedStateInternalNetworkIpEntry(messages, stateful_ip):
  return messages.PreservedState.InternalIPsValue.AdditionalProperty(
      key=stateful_ip.get('interface-name',
                          STATEFUL_IP_DEFAULT_INTERFACE_NAME),
      value=_MakePreservedStateNetworkIpEntry(messages, stateful_ip)
  )


def MakePreservedStateExternalNetworkIpEntry(messages, stateful_ip):
  return messages.PreservedState.ExternalIPsValue.AdditionalProperty(
      key=stateful_ip.get('interface-name',
                          STATEFUL_IP_DEFAULT_INTERFACE_NAME),
      value=_MakePreservedStateNetworkIpEntry(messages, stateful_ip)
  )


def CreatePerInstanceConfigMessage(holder,
                                   instance_ref,
                                   stateful_disks,
                                   stateful_metadata,
                                   disk_getter=None):
  """Create per-instance config message from the given stateful disks and metadata."""
  if not disk_getter:
    disk_getter = instance_disk_getter.InstanceDiskGetter(
        instance_ref=instance_ref, holder=holder)
  messages = holder.client.messages
  preserved_state_disks = []
  for stateful_disk in stateful_disks or []:
    preserved_state_disks.append(
        MakePreservedStateDiskEntry(messages, stateful_disk, disk_getter))
  preserved_state_metadata = []
  # Keeping the metadata sorted to maintain consistency across commands
  for metadata_key, metadata_value in sorted(six.iteritems(stateful_metadata)):
    preserved_state_metadata.append(
        MakePreservedStateMetadataEntry(
            messages, key=metadata_key, value=metadata_value))
  per_instance_config = messages.PerInstanceConfig(
      name=path_simplifier.Name(six.text_type(instance_ref)))
  per_instance_config.preservedState = messages.PreservedState(
      disks=messages.PreservedState.DisksValue(
          additionalProperties=preserved_state_disks),
      metadata=messages.PreservedState.MetadataValue(
          additionalProperties=preserved_state_metadata))
  return per_instance_config


def CreatePerInstanceConfigMessageWithIPs(holder,
                                          instance_ref,
                                          stateful_disks,
                                          stateful_metadata,
                                          stateful_internal_ips,
                                          stateful_external_ips,
                                          disk_getter=None):
  """Create per-instance config message from the given stateful attributes."""
  messages = holder.client.messages
  per_instance_config = CreatePerInstanceConfigMessage(holder,
                                                       instance_ref,
                                                       stateful_disks,
                                                       stateful_metadata,
                                                       disk_getter)
  preserved_state_internal_ips = []
  for stateful_internal_ip in stateful_internal_ips or []:
    preserved_state_internal_ips.append(
        MakePreservedStateInternalNetworkIpEntry(messages,
                                                 stateful_internal_ip))
  per_instance_config.preservedState.internalIPs = (
      messages.PreservedState.InternalIPsValue(
          additionalProperties=preserved_state_internal_ips))

  preserved_state_external_ips = []
  for stateful_external_ip in stateful_external_ips or []:
    preserved_state_external_ips.append(
        MakePreservedStateExternalNetworkIpEntry(messages,
                                                 stateful_external_ip))
  per_instance_config.preservedState.externalIPs = (
      messages.PreservedState.ExternalIPsValue(
          additionalProperties=preserved_state_external_ips))

  return per_instance_config


def CallPerInstanceConfigUpdate(holder, igm_ref, per_instance_config_message):
  """Calls proper (zonal or regional) resource for instance config update."""
  messages = holder.client.messages
  if igm_ref.Collection() == 'compute.instanceGroupManagers':
    service = holder.client.apitools_client.instanceGroupManagers
    request = (
        messages.ComputeInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagersUpdatePerInstanceConfigsReq=messages.
            InstanceGroupManagersUpdatePerInstanceConfigsReq(
                perInstanceConfigs=[per_instance_config_message]),
            project=igm_ref.project,
            zone=igm_ref.zone,
        )
    operation_collection = 'compute.zoneOperations'
  elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
    service = holder.client.apitools_client.regionInstanceGroupManagers
    request = (
        messages.
        ComputeRegionInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager=igm_ref.Name(),
            regionInstanceGroupManagerUpdateInstanceConfigReq=messages.
            RegionInstanceGroupManagerUpdateInstanceConfigReq(
                perInstanceConfigs=[per_instance_config_message]),
            project=igm_ref.project,
            region=igm_ref.region,
        )
    operation_collection = 'compute.regionOperations'
  else:
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))

  operation = service.UpdatePerInstanceConfigs(request)
  operation_ref = holder.resources.Parse(
      operation.selfLink, collection=operation_collection)
  return operation_ref


def CallCreateInstances(holder, igm_ref, per_instance_config_message):
  """Make CreateInstances API call using the given per-instance config messages."""
  messages = holder.client.messages
  if igm_ref.Collection() == 'compute.instanceGroupManagers':
    service = holder.client.apitools_client.instanceGroupManagers
    request = (
        messages.ComputeInstanceGroupManagersCreateInstancesRequest(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagersCreateInstancesRequest=
            messages.InstanceGroupManagersCreateInstancesRequest(
                instances=[per_instance_config_message]),
            project=igm_ref.project,
            zone=igm_ref.zone))
    operation_collection = 'compute.zoneOperations'
  elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
    service = holder.client.apitools_client.regionInstanceGroupManagers
    request = (
        messages.ComputeRegionInstanceGroupManagersCreateInstancesRequest(
            instanceGroupManager=igm_ref.Name(),
            regionInstanceGroupManagersCreateInstancesRequest=
            messages.RegionInstanceGroupManagersCreateInstancesRequest(
                instances=[per_instance_config_message]),
            project=igm_ref.project,
            region=igm_ref.region))
    operation_collection = 'compute.regionOperations'
  else:
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))
  operation = service.CreateInstances(request)
  operation_ref = holder.resources.Parse(
      operation.selfLink, collection=operation_collection)
  return operation_ref, service


def GetApplyUpdatesToInstancesRequestsZonal(holder, igm_ref, instances,
                                            minimal_action):
  """Immediately applies updates to instances (zonal case)."""
  messages = holder.client.messages
  request = messages.InstanceGroupManagersApplyUpdatesRequest(
      instances=instances,
      minimalAction=minimal_action,
      mostDisruptiveAllowedAction=messages
      .InstanceGroupManagersApplyUpdatesRequest
      .MostDisruptiveAllowedActionValueValuesEnum.REPLACE)
  return messages.ComputeInstanceGroupManagersApplyUpdatesToInstancesRequest(
      instanceGroupManager=igm_ref.Name(),
      instanceGroupManagersApplyUpdatesRequest=request,
      project=igm_ref.project,
      zone=igm_ref.zone,
  )


def GetApplyUpdatesToInstancesRequestsRegional(holder, igm_ref, instances,
                                               minimal_action):
  """Immediately applies updates to instances (regional case)."""
  messages = holder.client.messages
  request = messages.RegionInstanceGroupManagersApplyUpdatesRequest(
      instances=instances,
      minimalAction=minimal_action,
      mostDisruptiveAllowedAction=messages
      .RegionInstanceGroupManagersApplyUpdatesRequest
      .MostDisruptiveAllowedActionValueValuesEnum.REPLACE)
  return (
      messages.ComputeRegionInstanceGroupManagersApplyUpdatesToInstancesRequest
  )(
      instanceGroupManager=igm_ref.Name(),
      regionInstanceGroupManagersApplyUpdatesRequest=request,
      project=igm_ref.project,
      region=igm_ref.region,
  )


def CallApplyUpdatesToInstances(holder, igm_ref, instances, minimal_action):
  """Calls proper (zonal or reg.) resource for applying updates to instances."""
  if igm_ref.Collection() == 'compute.instanceGroupManagers':
    operation_collection = 'compute.zoneOperations'
    service = holder.client.apitools_client.instanceGroupManagers
    minimal_action = (
        holder.client.messages.InstanceGroupManagersApplyUpdatesRequest
        .MinimalActionValueValuesEnum(minimal_action.upper()))
    apply_request = GetApplyUpdatesToInstancesRequestsZonal(
        holder, igm_ref, instances, minimal_action)
  elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
    operation_collection = 'compute.regionOperations'
    service = holder.client.apitools_client.regionInstanceGroupManagers
    minimal_action = (
        holder.client.messages.RegionInstanceGroupManagersApplyUpdatesRequest
        .MinimalActionValueValuesEnum(minimal_action.upper()))
    apply_request = GetApplyUpdatesToInstancesRequestsRegional(
        holder, igm_ref, instances, minimal_action)
  else:
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))
  apply_operation = service.ApplyUpdatesToInstances(apply_request)
  apply_operation_ref = holder.resources.Parse(
      apply_operation.selfLink, collection=operation_collection)
  return apply_operation_ref
