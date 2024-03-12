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
"""Utils for Stateful policy API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.instance_groups import flags


def MakePreservedStateDisksMapEntry(messages, stateful_disk):
  """Make a map entry for disks field in preservedState message."""
  auto_delete_map = {
      'never':
          messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum.NEVER,
      'on-permanent-instance-deletion':
          messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum
          .ON_PERMANENT_INSTANCE_DELETION
  }
  disk_device = messages.PreservedStatePreservedDisk()
  if 'auto_delete' in stateful_disk:
    disk_device.autoDelete = auto_delete_map[stateful_disk['auto_delete']]
  return messages.PreservedState.DisksValue.AdditionalProperty(
      key=stateful_disk['device_name'], value=disk_device)


def MakePreservedState(messages, preserved_state_disks=None):
  """Make preservedState message for preservedStateFromPolicy."""
  preserved_state = messages.PreservedState()
  if preserved_state:
    preserved_state.disks = messages.PreservedState.DisksValue(
        additionalProperties=preserved_state_disks)
  return preserved_state


def MakeStatefulPolicyPreservedStateDiskEntry(messages, stateful_disk_dict):
  """Create StatefulPolicyPreservedState from a list of device names."""
  disk_device = messages.StatefulPolicyPreservedStateDiskDevice()
  if stateful_disk_dict.get('auto-delete'):
    disk_device.autoDelete = (
        stateful_disk_dict.get('auto-delete').GetAutoDeleteEnumValue(
            messages.StatefulPolicyPreservedStateDiskDevice
            .AutoDeleteValueValuesEnum))
  return (messages.StatefulPolicyPreservedState.DisksValue.AdditionalProperty(
      key=stateful_disk_dict.get('device-name'), value=disk_device))


def MakeDiskDeviceNullEntryForDisablingInPatch(client, device_name):
  return (client.messages.StatefulPolicyPreservedState.DisksValue
          .AdditionalProperty(key=device_name, value=None))


def MakeInternalIPEntry(messages, stateful_ip_dict):
  return (messages.StatefulPolicyPreservedState.InternalIPsValue
          .AdditionalProperty(
              key=stateful_ip_dict.get(
                  'interface-name', flags.STATEFUL_IP_DEFAULT_INTERFACE_NAME),
              value=_MakeNetworkIPForStatefulIP(messages, stateful_ip_dict)))


def MakeInternalIPNullEntryForDisablingInPatch(client, interface_name):
  return (client.messages.StatefulPolicyPreservedState.InternalIPsValue
          .AdditionalProperty(key=interface_name, value=None))


def MakeExternalIPEntry(messages, stateful_ip_dict):
  return (messages.StatefulPolicyPreservedState.ExternalIPsValue
          .AdditionalProperty(
              key=stateful_ip_dict.get(
                  'interface-name', flags.STATEFUL_IP_DEFAULT_INTERFACE_NAME),
              value=_MakeNetworkIPForStatefulIP(messages, stateful_ip_dict)))


def MakeExternalIPNullEntryForDisablingInPatch(client, interface_name):
  return (client.messages.StatefulPolicyPreservedState.ExternalIPsValue
          .AdditionalProperty(key=interface_name, value=None))


def _MakeNetworkIPForStatefulIP(messages, stateful_ip_dict):
  """Make NetworkIP proto out of stateful IP configuration dict."""
  network_ip = messages.StatefulPolicyPreservedStateNetworkIp()
  if stateful_ip_dict.get('auto-delete'):
    network_ip.autoDelete = (
        stateful_ip_dict.get('auto-delete').GetAutoDeleteEnumValue(
            messages.StatefulPolicyPreservedStateNetworkIp
            .AutoDeleteValueValuesEnum))
  return network_ip


def MakeStatefulPolicyPreservedStateInternalIPEntry(messages, stateful_ip_dict):
  """Make InternalIPsValue proto for a given stateful IP configuration dict."""
  return (messages.StatefulPolicyPreservedState.InternalIPsValue
          .AdditionalProperty(
              key=stateful_ip_dict.get(
                  'interface-name', flags.STATEFUL_IP_DEFAULT_INTERFACE_NAME),
              value=_MakeNetworkIPForStatefulIP(messages, stateful_ip_dict)))


def MakeStatefulPolicyPreservedStateExternalIPEntry(messages, stateful_ip_dict):
  """Make ExternalIPsValue proto for a given stateful IP configuration dict."""
  return (messages.StatefulPolicyPreservedState.ExternalIPsValue
          .AdditionalProperty(
              key=stateful_ip_dict.get(
                  'interface-name', flags.STATEFUL_IP_DEFAULT_INTERFACE_NAME),
              value=_MakeNetworkIPForStatefulIP(messages, stateful_ip_dict)))


def MakeStatefulPolicy(messages, preserved_state_disks):
  """Make stateful policy proto from a list of preserved state disk protos."""
  if not preserved_state_disks:
    preserved_state_disks = []
  return messages.StatefulPolicy(
      preservedState=messages.StatefulPolicyPreservedState(
          disks=messages.StatefulPolicyPreservedState.DisksValue(
              additionalProperties=preserved_state_disks)))


def UpdateStatefulPolicy(messages, stateful_policy_to_update,
                         preserved_state_disks=None,
                         preserved_state_internal_ips=None,
                         preserved_state_external_ips=None):
  """Update stateful policy proto from a list of preserved state attributes."""
  if preserved_state_disks is not None:
    stateful_policy_to_update.preservedState.disks = (
        messages.StatefulPolicyPreservedState.DisksValue(
            additionalProperties=preserved_state_disks))
  if preserved_state_internal_ips is not None:
    stateful_policy_to_update.preservedState.internalIPs = (
        messages.StatefulPolicyPreservedState.InternalIPsValue(
            additionalProperties=preserved_state_internal_ips))
  if preserved_state_external_ips is not None:
    stateful_policy_to_update.preservedState.externalIPs = (
        messages.StatefulPolicyPreservedState.ExternalIPsValue(
            additionalProperties=preserved_state_external_ips))
  return stateful_policy_to_update


def PatchStatefulPolicyDisk(preserved_state, patch):
  """Patch the preserved state proto."""
  if patch.value.autoDelete:
    preserved_state.value.autoDelete = patch.value.autoDelete

