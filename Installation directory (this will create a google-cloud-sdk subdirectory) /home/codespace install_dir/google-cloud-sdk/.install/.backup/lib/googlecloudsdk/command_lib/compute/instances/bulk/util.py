# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utils for compute instances bulk commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute.instances.create import utils as create_utils
from googlecloudsdk.command_lib.compute import resource_manager_tags_utils
from googlecloudsdk.command_lib.compute import secure_tags_utils
from googlecloudsdk.command_lib.compute.resource_policies import util as maintenance_util
from googlecloudsdk.command_lib.util.apis import arg_utils

import six


class SupportedFeatures:
  """Simple dataclass to hold status of supported features in Bulk."""

  def __init__(
      self,
      support_nvdimm,
      support_public_dns,
      support_erase_vss,
      support_min_node_cpu,
      support_source_snapshot_csek,
      support_image_csek,
      support_confidential_compute,
      support_post_key_revocation_action_type,
      support_rsa_encrypted,
      deprecate_maintenance_policy,
      support_create_disk_snapshots,
      support_boot_snapshot_uri,
      support_display_device,
      support_local_ssd_size,
      support_secure_tags,
      support_host_error_timeout_seconds,
      support_numa_node_count,
      support_visible_core_count,
      support_max_run_duration,
      support_local_ssd_recovery_timeout,
      support_enable_target_shape,
      support_confidential_compute_type,
      support_confidential_compute_type_tdx,
      support_max_count_per_zone,
      support_performance_monitoring_unit,
      support_custom_hostnames,
      support_storage_pool,
      support_specific_then_x_affinity,
  ):
    self.support_rsa_encrypted = support_rsa_encrypted
    self.support_secure_tags = support_secure_tags
    self.support_erase_vss = support_erase_vss
    self.support_public_dns = support_public_dns
    self.support_nvdimm = support_nvdimm
    self.support_min_node_cpu = support_min_node_cpu
    self.support_source_snapshot_csek = support_source_snapshot_csek
    self.support_image_csek = support_image_csek
    self.support_confidential_compute = support_confidential_compute
    self.support_post_key_revocation_action_type = (
        support_post_key_revocation_action_type
    )
    self.deprecate_maintenance_policy = deprecate_maintenance_policy
    self.support_create_disk_snapshots = support_create_disk_snapshots
    self.support_boot_snapshot_uri = support_boot_snapshot_uri
    self.support_display_device = support_display_device
    self.support_local_ssd_size = support_local_ssd_size
    self.support_host_error_timeout_seconds = support_host_error_timeout_seconds
    self.support_numa_node_count = support_numa_node_count
    self.support_visible_core_count = support_visible_core_count
    self.support_max_run_duration = support_max_run_duration
    self.support_enable_target_shape = support_enable_target_shape
    self.support_confidential_compute_type = support_confidential_compute_type
    self.support_confidential_compute_type_tdx = (
        support_confidential_compute_type_tdx
    )
    self.support_max_count_per_zone = support_max_count_per_zone
    self.support_local_ssd_recovery_timeout = support_local_ssd_recovery_timeout
    self.support_performance_monitoring_unit = (
        support_performance_monitoring_unit
    )
    self.support_custom_hostnames = support_custom_hostnames
    self.support_storage_pool = support_storage_pool
    self.support_specific_then_x_affinity = support_specific_then_x_affinity


def _GetSourceInstanceTemplate(args, resources, instance_template_resource):
  """Get sourceInstanceTemplate value as required by API."""
  if not args.IsSpecified('source_instance_template'):
    return None
  ref = instance_template_resource.ResolveAsResource(args, resources)
  return ref.SelfLink()


def _GetLocationPolicy(
    args, messages, target_shape_enabled, max_count_per_zone_enabled
):
  """Get locationPolicy value as required by API."""
  if not (
      args.IsKnownAndSpecified('location_policy')
      or args.IsKnownAndSpecified('max_count_per_zone')
  ) and (
      not target_shape_enabled
      or not (args.IsKnownAndSpecified('target_distribution_shape'))
  ):
    return None

  location_policy = messages.LocationPolicy()

  if args.IsKnownAndSpecified('location_policy') or args.IsKnownAndSpecified(
      'max_count_per_zone'
  ):
    if max_count_per_zone_enabled:
      location_policy.locations = (
          _GetLocationPolicyLocationsMaxCountPerZoneFeatureEnabled(
              args, messages
          )
      )
    else:
      location_policy.locations = (
          _GetLocationPolicyLocationsMaxCountPerZoneFeatureDisabled(
              args, messages
          )
      )

  if target_shape_enabled and args.IsKnownAndSpecified(
      'target_distribution_shape'
  ):
    location_policy.targetShape = arg_utils.ChoiceToEnum(
        args.target_distribution_shape,
        messages.LocationPolicy.TargetShapeValueValuesEnum)
  return location_policy


def _GetLocationPolicyLocationsMaxCountPerZoneFeatureDisabled(args, messages):
  """Helper function for getting location for location policy."""
  locations = []
  for zone, policy in args.location_policy.items():
    zone_policy = arg_utils.ChoiceToEnum(
        policy, messages.LocationPolicyLocation.PreferenceValueValuesEnum)
    locations.append(
        messages.LocationPolicy.LocationsValue.AdditionalProperty(
            key='zones/{}'.format(zone),
            value=messages.LocationPolicyLocation(preference=zone_policy)))

  return messages.LocationPolicy.LocationsValue(additionalProperties=locations)


def _GetLocationPolicyLocationsMaxCountPerZoneFeatureEnabled(args, messages):
  """Helper function for getting location for location policy."""
  locations = []
  # list including only zones listed in location policy flag.
  if args.location_policy:
    for zone, policy in args.location_policy.items():
      zone_policy = arg_utils.ChoiceToEnum(
          policy, messages.LocationPolicyLocation.PreferenceValueValuesEnum
      )
      if args.max_count_per_zone and zone in args.max_count_per_zone:
        locations.append(
            messages.LocationPolicy.LocationsValue.AdditionalProperty(
                key='zones/{}'.format(zone),
                value=messages.LocationPolicyLocation(
                    preference=zone_policy,
                    constraints=messages.LocationPolicyLocationConstraints(
                        maxCount=int(args.max_count_per_zone[zone])
                    ),
                ),
            )
        )
      else:
        locations.append(
            messages.LocationPolicy.LocationsValue.AdditionalProperty(
                key='zones/{}'.format(zone),
                value=messages.LocationPolicyLocation(preference=zone_policy),
            )
        )

  zone_policy_allowed_preference = arg_utils.ChoiceToEnum(
      'allow', messages.LocationPolicyLocation.PreferenceValueValuesEnum
  )
  # list including zones not listed in location policy flag.
  if args.max_count_per_zone:
    for zone, count in args.max_count_per_zone.items():
      if (args.location_policy and zone not in args.location_policy) or (
          not args.location_policy
      ):
        locations.append(
            messages.LocationPolicy.LocationsValue.AdditionalProperty(
                key='zones/{}'.format(zone),
                value=messages.LocationPolicyLocation(
                    preference=zone_policy_allowed_preference,
                    constraints=messages.LocationPolicyLocationConstraints(
                        maxCount=int(count)
                    ),
                ),
            )
        )

  return messages.LocationPolicy.LocationsValue(additionalProperties=locations)


def _GetPerInstanceProperties(
    args, messages, instance_names, support_custom_hostnames
):
  """Helper function for getting per_instance_properties."""
  per_instance_hostnames = {}
  if support_custom_hostnames and args.IsSpecified('per_instance_hostnames'):
    per_instance_hostnames = args.per_instance_hostnames

  per_instance_properties = {}
  for name in instance_names:
    if name in per_instance_hostnames:
      per_instance_properties[name] = (
          messages.BulkInsertInstanceResourcePerInstanceProperties(
              hostname=per_instance_hostnames[name]
          )
      )
    else:
      per_instance_properties[name] = (
          messages.BulkInsertInstanceResourcePerInstanceProperties()
      )

  return encoding.DictToAdditionalPropertyMessage(
      per_instance_properties,
      messages.BulkInsertInstanceResource.PerInstancePropertiesValue,
  )


def CreateBulkInsertInstanceResource(args, holder, compute_client,
                                     resource_parser, project, location, scope,
                                     instance_template_resource,
                                     supported_features):
  """Create bulkInsertInstanceResource."""
  # gcloud creates default values for some fields in Instance resource
  # when no value was specified on command line.
  # When --source-instance-template was specified, defaults are taken from
  # Instance Template and gcloud flags are used to override them - by default
  # fields should not be initialized.

  name_pattern = args.name_pattern
  instance_names = args.predefined_names or []
  instance_count = args.count or len(instance_names)
  per_instance_props = _GetPerInstanceProperties(
      args,
      compute_client.messages,
      instance_names,
      supported_features.support_custom_hostnames,
  )

  location_policy = _GetLocationPolicy(
      args,
      compute_client.messages,
      supported_features.support_enable_target_shape,
      supported_features.support_max_count_per_zone,
  )

  instance_min_count = instance_count
  if args.IsSpecified('min_count'):
    instance_min_count = args.min_count

  source_instance_template = _GetSourceInstanceTemplate(
      args, resource_parser, instance_template_resource)
  skip_defaults = source_instance_template is not None

  scheduling = instance_utils.GetScheduling(
      args,
      compute_client,
      skip_defaults,
      support_node_affinity=False,
      support_min_node_cpu=supported_features.support_min_node_cpu,
      support_host_error_timeout_seconds=supported_features
      .support_host_error_timeout_seconds,
      support_max_run_duration=supported_features.support_max_run_duration,
      support_local_ssd_recovery_timeout=supported_features.support_local_ssd_recovery_timeout)
  tags = instance_utils.GetTags(args, compute_client)
  labels = instance_utils.GetLabels(
      args, compute_client, instance_properties=True)
  metadata = instance_utils.GetMetadata(args, compute_client, skip_defaults)

  network_interfaces = create_utils.GetBulkNetworkInterfaces(
      args=args,
      resource_parser=resource_parser,
      compute_client=compute_client,
      holder=holder,
      project=project,
      location=location,
      scope=scope,
      skip_defaults=skip_defaults)

  create_boot_disk = not (
      instance_utils.UseExistingBootDisk((args.disk or []) +
                                         (args.create_disk or [])))
  image_uri = create_utils.GetImageUri(args, compute_client, create_boot_disk,
                                       project, resource_parser)

  shielded_instance_config = create_utils.BuildShieldedInstanceConfigMessage(
      messages=compute_client.messages, args=args
  )

  confidential_vm_type = None
  if supported_features.support_confidential_compute:
    confidential_instance_config = (
        create_utils.BuildConfidentialInstanceConfigMessage(
            messages=compute_client.messages,
            args=args,
            support_confidential_compute_type=supported_features
            .support_confidential_compute_type,
            support_confidential_compute_type_tdx=supported_features
            .support_confidential_compute_type_tdx))

    confidential_vm_type = instance_utils.GetConfidentialVmType(
        args, supported_features.support_confidential_compute_type)

  service_accounts = create_utils.GetProjectServiceAccount(
      args, project, compute_client, skip_defaults)

  boot_disk_size_gb = instance_utils.GetBootDiskSizeGb(args)

  disks = []
  if create_utils.CheckSpecifiedDiskArgs(
      args=args, support_disks=False, skip_defaults=skip_defaults):

    # Disks in bulk insert should be in READ_ONLY mode.
    for disk in args.disk or []:
      disk['mode'] = 'ro'
    disks = create_utils.CreateDiskMessages(
        args=args,
        project=project,
        location=location,
        scope=scope,
        compute_client=compute_client,
        resource_parser=resource_parser,
        image_uri=image_uri,
        create_boot_disk=create_boot_disk,
        boot_disk_size_gb=boot_disk_size_gb,
        support_kms=True,
        support_nvdimm=supported_features.support_nvdimm,
        support_source_snapshot_csek=supported_features
        .support_source_snapshot_csek,
        support_boot_snapshot_uri=supported_features.support_boot_snapshot_uri,
        support_image_csek=supported_features.support_image_csek,
        support_create_disk_snapshots=supported_features
        .support_create_disk_snapshots,
        use_disk_type_uri=False,
        support_storage_pool=supported_features.support_storage_pool)

  machine_type_name = None
  if instance_utils.CheckSpecifiedMachineTypeArgs(args, skip_defaults):
    machine_type_name = instance_utils.CreateMachineTypeName(
        args, confidential_vm_type)

  can_ip_forward = instance_utils.GetCanIpForward(args, skip_defaults)
  guest_accelerators = create_utils.GetAcceleratorsForInstanceProperties(
      args=args, compute_client=compute_client)

  # Create an AdvancedMachineFeatures message if any arguments are supplied
  # that require one.
  advanced_machine_features = None
  if (
      args.enable_nested_virtualization is not None
      or args.threads_per_core is not None
      or (
          supported_features.support_numa_node_count
          and args.numa_node_count is not None
      )
      or (
          supported_features.support_visible_core_count
          and args.visible_core_count is not None
      )
      or args.enable_uefi_networking is not None
      or (
          supported_features.support_performance_monitoring_unit
          and args.performance_monitoring_unit
      )
  ):
    visible_core_count = (
        args.visible_core_count
        if supported_features.support_visible_core_count
        else None
    )
    advanced_machine_features = (
        instance_utils.CreateAdvancedMachineFeaturesMessage(
            compute_client.messages,
            args.enable_nested_virtualization,
            args.threads_per_core,
            args.numa_node_count
            if supported_features.support_numa_node_count
            else None,
            visible_core_count,
            args.enable_uefi_networking,
            args.performance_monitoring_unit
            if supported_features.support_performance_monitoring_unit
            else None,
        )
    )

  parsed_resource_policies = []
  resource_policies = getattr(args, 'resource_policies', None)
  if resource_policies:
    for policy in resource_policies:
      resource_policy_ref = maintenance_util.ParseResourcePolicyWithScope(
          resource_parser,
          policy,
          project=project,
          location=location,
          scope=scope)
      parsed_resource_policies.append(resource_policy_ref.Name())

  display_device = None
  if supported_features.support_display_device and args.IsSpecified(
      'enable_display_device'):
    display_device = compute_client.messages.DisplayDevice(
        enableDisplay=args.enable_display_device)

  reservation_affinity = instance_utils.GetReservationAffinity(
      args, compute_client, supported_features.support_specific_then_x_affinity
  )

  instance_properties = compute_client.messages.InstanceProperties(
      canIpForward=can_ip_forward,
      description=args.description,
      disks=disks,
      guestAccelerators=guest_accelerators,
      labels=labels,
      machineType=machine_type_name,
      metadata=metadata,
      minCpuPlatform=args.min_cpu_platform,
      networkInterfaces=network_interfaces,
      serviceAccounts=service_accounts,
      scheduling=scheduling,
      tags=tags,
      resourcePolicies=parsed_resource_policies,
      shieldedInstanceConfig=shielded_instance_config,
      reservationAffinity=reservation_affinity,
      advancedMachineFeatures=advanced_machine_features)

  if supported_features.support_secure_tags and args.secure_tags:
    instance_properties.secureTags = secure_tags_utils.GetSecureTags(
        args.secure_tags)
  if args.resource_manager_tags:
    ret_resource_manager_tags = resource_manager_tags_utils.GetResourceManagerTags(
        args.resource_manager_tags)
    if ret_resource_manager_tags is not None:
      properties_message = compute_client.messages.InstanceProperties
      instance_properties.resourceManagerTags = properties_message.ResourceManagerTagsValue(
          additionalProperties=[
              properties_message.ResourceManagerTagsValue.AdditionalProperty(
                  key=key, value=value) for key, value in sorted(
                      six.iteritems(ret_resource_manager_tags))
          ])

  if supported_features.support_display_device and display_device:
    instance_properties.displayDevice = display_device

  if supported_features.support_confidential_compute and confidential_instance_config:
    instance_properties.confidentialInstanceConfig = confidential_instance_config

  if supported_features.support_erase_vss and args.IsSpecified(
      'erase_windows_vss_signature'):
    instance_properties.eraseWindowsVssSignature = args.erase_windows_vss_signature

  if supported_features.support_post_key_revocation_action_type and args.IsSpecified(
      'post_key_revocation_action_type'):
    instance_properties.postKeyRevocationActionType = arg_utils.ChoiceToEnum(
        args.post_key_revocation_action_type, compute_client.messages.Instance
        .PostKeyRevocationActionTypeValueValuesEnum)

  if args.IsSpecified('network_performance_configs'):
    instance_properties.networkPerformanceConfig = (
        instance_utils.GetNetworkPerformanceConfig(args, compute_client))

  return compute_client.messages.BulkInsertInstanceResource(
      count=instance_count,
      instanceProperties=instance_properties,
      minCount=instance_min_count,
      perInstanceProperties=per_instance_props,
      sourceInstanceTemplate=source_instance_template,
      namePattern=name_pattern,
      locationPolicy=location_policy)
