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
"""Common utility functions to consturct compute reservations message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.resource_policies import util as maintenance_util
from googlecloudsdk.core.util import times
import six


def MakeReservationMessageFromArgs(messages, args, reservation_ref, resources):
  """Construct reservation message from args passed in."""
  accelerators = MakeGuestAccelerators(messages,
                                       getattr(args, 'accelerator', None))
  local_ssds = MakeLocalSsds(messages, getattr(args, 'local_ssd', None))
  share_settings = MakeShareSettingsWithArgs(
      messages, args, getattr(args, 'share_setting', None))
  source_instance_template_ref = (
      ResolveSourceInstanceTemplate(args, resources)
      if args.IsKnownAndSpecified('source_instance_template')
      else None
  )
  specific_reservation = MakeSpecificSKUReservationMessage(
      messages,
      args.vm_count,
      accelerators,
      local_ssds,
      args.machine_type,
      args.min_cpu_platform,
      getattr(args, 'location_hint', None),
      getattr(args, 'maintenance_freeze_duration', None),
      getattr(args, 'maintenance_interval', None),
      source_instance_template_ref,
  )
  resource_policies = MakeResourcePolicies(
      messages, reservation_ref, getattr(args, 'resource_policies', None),
      resources)

  return MakeReservationMessage(
      messages,
      reservation_ref.Name(),
      share_settings,
      specific_reservation,
      resource_policies,
      args.require_specific_reservation,
      reservation_ref.zone,
      getattr(args, 'delete_at_time', None),
      getattr(args, 'delete_after_duration', None),
  )


def ResolveSourceInstanceTemplate(args, resources):
  return compute_flags.ResourceArgument(
      '--source-instance-template',
      resource_name='instance template',
      scope_flags_usage=compute_flags.ScopeFlagsUsage.DONT_USE_SCOPE_FLAGS,
      global_collection='compute.instanceTemplates',
      regional_collection='compute.regionInstanceTemplates',
  ).ResolveAsResource(
      args, resources, default_scope=compute_scope.ScopeEnum.GLOBAL
  )


def MakeGuestAccelerators(messages, accelerator_configs):
  """Constructs the repeated accelerator message objects."""
  if accelerator_configs is None:
    return []

  accelerators = []

  for a in accelerator_configs:
    m = messages.AcceleratorConfig(
        acceleratorCount=a['count'], acceleratorType=a['type'])
    accelerators.append(m)

  return accelerators


def MakeLocalSsds(messages, ssd_configs):
  """Constructs the repeated local_ssd message objects."""
  if ssd_configs is None:
    return []

  local_ssds = []
  disk_msg = (
      messages
      .AllocationSpecificSKUAllocationAllocatedInstancePropertiesReservedDisk)
  interface_msg = disk_msg.InterfaceValueValuesEnum
  total_partitions = 0
  for s in ssd_configs:
    if s['interface'].upper() == 'NVME':
      interface = interface_msg.NVME
    else:
      interface = interface_msg.SCSI
    m = disk_msg(diskSizeGb=s['size'], interface=interface)
    partitions = s.get('count', 1)
    if partitions not in range(24 + 1):
      raise exceptions.InvalidArgumentException(
          '--local-ssd',
          'The number of SSDs attached to an instance must be in the range of 1-24.'
      )

    total_partitions += partitions
    if total_partitions > 24:
      raise exceptions.InvalidArgumentException(
          '--local-ssd',
          'The total number of SSDs attached to an instance must not exceed 24.'
      )

    local_ssds.extend([m] * partitions)

  return local_ssds


def MakeShareSettingsWithArgs(messages,
                              args,
                              setting_configs,
                              share_with='share_with'):
  """Constructs the share settings message object from raw args as input."""
  if setting_configs:
    if setting_configs == 'organization':
      return messages.ShareSettings(shareType=messages.ShareSettings
                                    .ShareTypeValueValuesEnum.ORGANIZATION)
    if setting_configs == 'local':
      if args.IsSpecified(share_with):
        raise exceptions.InvalidArgumentException(
            '--share_with',
            'The scope this reservation is to be shared with must not be '
            'specified with share setting local.')
      return messages.ShareSettings(
          shareType=messages.ShareSettings.ShareTypeValueValuesEnum.LOCAL)
    if setting_configs == 'projects':
      if not args.IsSpecified(share_with):
        raise exceptions.InvalidArgumentException(
            '--share_with',
            'The projects this reservation is to be shared with must be '
            'specified.')
      return messages.ShareSettings(
          shareType=messages.ShareSettings.ShareTypeValueValuesEnum
          .SPECIFIC_PROJECTS,
          projectMap=MakeProjectMapFromProjectList(
              messages, getattr(args, share_with, None)))
    if setting_configs == 'folders':
      if not args.IsSpecified(share_with):
        raise exceptions.InvalidArgumentException(
            '--share_with',
            'The folders this reservation is to be shared with must be '
            'specified.')
      return messages.ShareSettings(
          shareType=messages.ShareSettings.ShareTypeValueValuesEnum
          .DIRECT_PROJECTS_UNDER_SPECIFIC_FOLDERS,
          folderMap=MakeFolderMapFromFolderList(messages,
                                                getattr(args, share_with,
                                                        None)))
  else:
    if args.IsKnownAndSpecified(share_with):
      raise exceptions.InvalidArgumentException(
          '--share_setting',
          'Please specify share setting if specifying share with.')
    return None


def MakeShareSettingsWithDict(messages, dictionary, setting_configs):
  """Constructs the share settings message object from dictionary form of input."""
  if setting_configs:
    if setting_configs == 'organization':
      return messages.ShareSettings(shareType=messages.ShareSettings
                                    .ShareTypeValueValuesEnum.ORGANIZATION)
    if setting_configs == 'local':
      if 'share_with' in dictionary.keys():
        raise exceptions.InvalidArgumentException(
            '--share_with',
            'The scope this reservation is to be shared with must not be '
            'specified with share setting local.')
      return messages.ShareSettings(
          shareType=messages.ShareSettings.ShareTypeValueValuesEnum.LOCAL)
    if setting_configs == 'projects':
      if 'share_with' not in dictionary.keys():
        raise exceptions.InvalidArgumentException(
            '--share_with',
            'The projects this reservation is to be shared with must be '
            'specified.')
      return messages.ShareSettings(
          shareType=messages.ShareSettings.ShareTypeValueValuesEnum
          .SPECIFIC_PROJECTS,
          projectMap=MakeProjectMapFromProjectList(
              messages, dictionary.get('share_with', None)))
    if setting_configs == 'folders':
      if 'share_with' not in dictionary.keys():
        raise exceptions.InvalidArgumentException(
            '--share_with',
            'The folders this reservation is to be shared with must be '
            'specified.')
      return messages.ShareSettings(
          shareType=messages.ShareSettings.ShareTypeValueValuesEnum
          .DIRECT_PROJECTS_UNDER_SPECIFIC_FOLDERS,
          folderMap=MakeFolderMapFromFolderList(
              messages, dictionary.get('share_with', None)))
  else:
    if 'share_with' in dictionary.keys():
      raise exceptions.InvalidArgumentException(
          '--share_setting',
          'Please specify share setting if specifying share with.')
    return None


def MakeSpecificSKUReservationMessage(
    messages,
    vm_count,
    accelerators,
    local_ssds,
    machine_type,
    min_cpu_platform,
    location_hint=None,
    freeze_duration=None,
    freeze_interval=None,
    source_instance_template_ref=None,
):
  """Constructs a single specific sku reservation message object."""
  prop_msgs = (
      messages.AllocationSpecificSKUAllocationReservedInstanceProperties)
  if source_instance_template_ref:
    return messages.AllocationSpecificSKUReservation(
        count=vm_count,
        sourceInstanceTemplate=source_instance_template_ref.SelfLink(),
        instanceProperties=None,
    )
  else:
    instance_properties = prop_msgs(
        guestAccelerators=accelerators,
        localSsds=local_ssds,
        machineType=machine_type,
        minCpuPlatform=min_cpu_platform)
    if freeze_duration:
      instance_properties.maintenanceFreezeDurationHours = freeze_duration // 3600
    if freeze_interval:
      instance_properties.maintenanceInterval = (
          messages.AllocationSpecificSKUAllocationReservedInstanceProperties
          .MaintenanceIntervalValueValuesEnum(freeze_interval))
    if location_hint:
      instance_properties.locationHint = location_hint
    return messages.AllocationSpecificSKUReservation(
        count=vm_count, instanceProperties=instance_properties)


def MakeReservationMessage(messages, reservation_name, share_settings,
                           specific_reservation, resource_policies,
                           require_specific_reservation,
                           reservation_zone,
                           delete_at_time=None,
                           delete_after_duration=None):
  """Constructs a single reservations message object."""
  reservation_message = messages.Reservation(
      name=reservation_name,
      specificReservation=specific_reservation,
      specificReservationRequired=require_specific_reservation,
      zone=reservation_zone)
  if share_settings:
    reservation_message.shareSettings = share_settings
  if resource_policies:
    reservation_message.resourcePolicies = resource_policies

  if delete_at_time:
    reservation_message.deleteAtTime = times.FormatDateTime(delete_at_time)

  if delete_after_duration:
    reservation_message.deleteAfterDuration = messages.Duration(
        seconds=delete_after_duration
    )

  return reservation_message


def MakeProjectMapFromProjectList(messages, projects):
  additional_properties = []
  for project in projects:
    additional_properties.append(
        messages.ShareSettings.ProjectMapValue.AdditionalProperty(
            key=project,
            value=messages.ShareSettingsProjectConfig(projectId=project)))
  return messages.ShareSettings.ProjectMapValue(
      additionalProperties=additional_properties)


def MakeFolderMapFromFolderList(messages, folders):
  additional_properties = []
  for folder in folders:
    additional_properties.append(
        messages.ShareSettings.FolderMapValue.AdditionalProperty(
            key=folder,
            value=messages.ShareSettingsFolderConfig(folderId=folder)))
  return messages.ShareSettings.FolderMapValue(
      additionalProperties=additional_properties)


def MakeResourcePolicies(messages, reservation_ref, resource_policy_dictionary,
                         resources):
  """Constructs the resource policies message objects."""
  if resource_policy_dictionary is None:
    return None

  return messages.Reservation.ResourcePoliciesValue(additionalProperties=[
      messages.Reservation.ResourcePoliciesValue.AdditionalProperty(
          key=key, value=MakeUrl(resources, value, reservation_ref))
      for key, value in sorted(six.iteritems(resource_policy_dictionary))
  ])


def MakeUrl(resources, value, reservation_ref):
  return maintenance_util.ParseResourcePolicyWithZone(
      resources,
      value,
      project=reservation_ref.project,
      zone=reservation_ref.zone).SelfLink()
