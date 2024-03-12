# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for creating instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import kms_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import partner_metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.instances.create import utils as create_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import resource_manager_tags_utils
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute import secure_tags_utils
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags as maintenance_flags
from googlecloudsdk.command_lib.compute.resource_policies import util as maintenance_util
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
import six
from six.moves import zip

DETAILED_HELP = {
    'DESCRIPTION':
        """
        *{command}* facilitates the creation of Compute Engine
        virtual machines.

        When an instance is in RUNNING state and the system begins to boot,
        the instance creation is considered finished, and the command returns
        with a list of new virtual machines.  Note that you usually cannot log
        into a new instance until it finishes booting. Check the progress of an
        instance using `gcloud compute instances get-serial-port-output`.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES':
        """
        To create an instance with the latest 'Red Hat Enterprise Linux 8' image
        available, run:

          $ {command} example-instance --image-family=rhel-8 --image-project=rhel-cloud --zone=us-central1-a

        To create instances called 'example-instance-1', 'example-instance-2',
        and 'example-instance-3' in the 'us-central1-a' zone, run:

          $ {command} example-instance-1 example-instance-2 example-instance-3 --zone=us-central1-a

        To create an instance called 'instance-1' from a source snapshot called
        'instance-snapshot' in zone 'us-central1-a' and attached regional disk
        'disk-1', run:

          $ {command} instance-1 --source-snapshot=https://compute.googleapis.com/compute/v1/projects/myproject/global/snapshots/instance-snapshot --zone=us-central1-a --disk=name=disk1,scope=regional

        To create an instance called instance-1 as a Shielded VM instance with
        Secure Boot, virtual trusted platform module (vTPM) enabled and
        integrity monitoring, run:

          $ {command} instance-1 --zone=us-central1-a --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring

        To create a preemptible instance called 'instance-1', run:

          $ {command} instance-1 --machine-type=n1-standard-1 --zone=us-central1-b --preemptible --no-restart-on-failure --maintenance-policy=terminate

        """,
}


def _CommonArgs(
    parser,
    enable_regional=False,
    enable_kms=False,
    deprecate_maintenance_policy=False,
    supports_erase_vss=True,
    snapshot_csek=False,
    image_csek=False,
    support_multi_writer=False,
    support_replica_zones=True,
    support_subinterface=False,
    support_host_error_timeout_seconds=False,
    support_numa_node_count=False,
    support_network_queue_count=False,
    support_instance_kms=False,
    support_max_run_duration=False,
    support_network_attachments=False,
    support_local_ssd_recovery_timeout=True,
    support_local_ssd_size=False,
    support_vlan_nic=False,
    support_storage_pool=False,
    support_source_instant_snapshot=False,
    support_enable_confidential_compute=False,
    support_specific_then_x_affinity=False,
    support_ipv6_only=False,
    support_graceful_shutdown=False,
    support_igmp_query=False,
):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser, enable_regional, enable_kms=enable_kms)
  instances_flags.AddCreateDiskArgs(
      parser,
      enable_kms=enable_kms,
      enable_snapshots=True,
      source_snapshot_csek=snapshot_csek,
      image_csek=image_csek,
      support_boot=True,
      support_multi_writer=support_multi_writer,
      support_replica_zones=support_replica_zones,
      support_storage_pool=support_storage_pool,
      enable_source_instant_snapshots=support_source_instant_snapshot,
      enable_confidential_compute=support_enable_confidential_compute,
  )
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(
      parser,
      instances=True,
      support_subinterface=support_subinterface,
      instance_create=True,
      support_network_queue_count=support_network_queue_count,
      support_network_attachments=support_network_attachments,
      support_vlan_nic=support_vlan_nic,
      support_ipv6_only=support_ipv6_only,
      support_igmp_query=support_igmp_query)
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(
      parser, deprecate=deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(
      parser,
      False,
      extra_scopes_help='However, if neither `--scopes` nor `--no-scopes` are '
      'specified and the project has no default service '
      'account, then the instance will be created with no '
      'scopes. Note that the level of access that a service '
      'account has is determined by a combination of access '
      'scopes and IAM roles so you must configure both '
      'access scopes and IAM roles for the service account '
      'to work properly.')
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddHostnameArg(parser)
  instances_flags.AddImageArgs(
      parser,
      enable_snapshots=True,
      support_image_family_scope=True,
      enable_instant_snapshots=support_source_instant_snapshot,
  )
  instances_flags.AddDeletionProtectionFlag(parser)
  instances_flags.AddPublicPtrArgs(parser, instance=True)
  instances_flags.AddIpv6PublicPtrDomainArg(parser)
  instances_flags.AddNetworkTierArgs(parser, instance=True)
  instances_flags.AddShieldedInstanceConfigArgs(parser)
  instances_flags.AddDisplayDeviceArg(parser)
  instances_flags.AddMinNodeCpuArg(parser)
  instances_flags.AddNestedVirtualizationArgs(parser)
  instances_flags.AddThreadsPerCoreArgs(parser)
  instances_flags.AddEnableUefiNetworkingArgs(parser)
  instances_flags.AddResourceManagerTagsArgs(parser)
  if support_numa_node_count:
    instances_flags.AddNumaNodeCountArgs(parser)
  instances_flags.AddStackTypeArgs(parser, support_ipv6_only=support_ipv6_only)
  instances_flags.AddIpv6NetworkTierArgs(parser)
  instances_flags.AddNetworkPerformanceConfigsArgs(parser)
  instances_flags.AddProvisioningModelVmArgs(parser)
  instances_flags.AddInstanceTerminationActionVmArgs(parser)
  instances_flags.AddIPv6AddressArgs(parser)
  instances_flags.AddIPv6PrefixLengthArgs(parser)
  instances_flags.AddInternalIPv6AddressArgs(parser)
  instances_flags.AddInternalIPv6PrefixLengthArgs(parser)

  instances_flags.AddReservationAffinityGroup(
      parser,
      group_text='Specifies the reservation for the instance.',
      affinity_text='The type of reservation for the instance.',
      support_specific_then_x_affinity=support_specific_then_x_affinity,
  )

  maintenance_flags.AddResourcePoliciesArgs(parser, 'added to', 'instance')

  sole_tenancy_flags.AddNodeAffinityFlagToParser(parser)

  instances_flags.AddLocationHintArg(parser)

  if supports_erase_vss:
    flags.AddEraseVssSignature(parser, 'source snapshots or source machine'
                               ' image')

  labels_util.AddCreateLabelsFlags(parser)

  parser.add_argument(
      '--description', help='Specifies a textual description of the instances.')

  instances_flags.INSTANCES_ARG_FOR_CREATE.AddArgument(
      parser, operation_type='create')

  csek_utils.AddCsekKeyArgs(parser)

  base.ASYNC_FLAG.AddToParser(parser)
  parser.display_info.AddFormat(instances_flags.DEFAULT_LIST_FORMAT)
  parser.display_info.AddCacheUpdater(completers.InstancesCompleter)

  instances_flags.AddNodeProjectArgs(parser)

  if support_graceful_shutdown:
    instances_flags.AddGracefulShutdownArgs(parser, is_create=True)

  if support_host_error_timeout_seconds:
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)

  if support_local_ssd_recovery_timeout:
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)

  if support_instance_kms:
    instances_flags.AddInstanceKmsArgs(parser)

  if support_max_run_duration:
    instances_flags.AddMaxRunDurationVmArgs(parser)

  if support_local_ssd_size:
    instances_flags.AddLocalSsdArgsWithSize(parser)
  else:
    instances_flags.AddLocalSsdArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create Compute Engine virtual machine instances."""

  _support_regional = True
  _support_kms = True
  _support_nvdimm = False
  _support_public_dns = False
  _support_erase_vss = True
  _support_machine_image_key = True
  _support_source_snapshot_csek = False
  _support_image_csek = False
  _support_post_key_revocation_action_type = False
  _support_rsa_encrypted = False
  _deprecate_maintenance_policy = False
  _support_create_disk_snapshots = True
  _support_boot_snapshot_uri = True
  _enable_pd_interface = False
  _support_replica_zones = True
  _support_multi_writer = False
  _support_subinterface = False
  _support_secure_tag = False
  _support_host_error_timeout_seconds = False
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_network_queue_count = True
  _support_instance_kms = True
  _support_max_run_duration = False
  _support_ipv6_assignment = False
  _support_confidential_compute_type = False
  _support_confidential_compute_type_tdx = False
  _support_network_attachments = False
  _support_local_ssd_recovery_timeout = True
  _support_internal_ipv6_reservation = True
  _support_local_ssd_size = True
  _support_vlan_nic = False
  _support_performance_monitoring_unit = False
  _support_storage_pool = False
  _support_source_instant_snapshot = False
  _support_boot_instant_snapshot_uri = False
  _support_partner_metadata = False
  _support_enable_confidential_compute = True
  _support_specific_then_x_affinity = False
  _support_graceful_shutdown = False
  _support_igmp_query = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        enable_kms=cls._support_kms,
        support_multi_writer=cls._support_multi_writer,
        support_replica_zones=cls._support_replica_zones,
        enable_regional=cls._support_regional,
        support_subinterface=cls._support_subinterface,
        support_host_error_timeout_seconds=cls._support_host_error_timeout_seconds,
        support_numa_node_count=cls._support_numa_node_count,
        support_instance_kms=cls._support_instance_kms,
        support_max_run_duration=cls._support_max_run_duration,
        supports_erase_vss=cls._support_erase_vss,
        support_network_attachments=cls._support_network_attachments,
        support_local_ssd_recovery_timeout=cls._support_local_ssd_recovery_timeout,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_network_queue_count=cls._support_network_queue_count,
        support_vlan_nic=cls._support_vlan_nic,
        support_storage_pool=cls._support_storage_pool,
        support_enable_confidential_compute=cls._support_enable_confidential_compute,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
        support_graceful_shutdown=cls._support_graceful_shutdown,
        support_igmp_query=cls._support_igmp_query,
    )
    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg()
    )
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    cls.SOURCE_MACHINE_IMAGE = (instances_flags.AddMachineImageArg())
    cls.SOURCE_MACHINE_IMAGE.AddArgument(parser)
    instances_flags.AddSourceMachineImageEncryptionKey(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.GA)
    instances_flags.AddPrivateIpv6GoogleAccessArg(parser,
                                                  utils.COMPUTE_GA_API_VERSION)
    instances_flags.AddConfidentialComputeArgs(
        parser,
        support_confidential_compute_type=cls
        ._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx)
    instances_flags.AddKeyRevocationActionTypeArgs(parser)
    instances_flags.AddVisibleCoreCountArgs(parser)

  def Collection(self):
    return 'compute.instances'

  def GetSourceMachineImage(self, args, resources):
    """Retrieves the specified source machine image's selflink.

    Args:
      args: The arguments passed into the gcloud command calling this function.
      resources: Resource parser used to retrieve the specified resource
        reference.

    Returns:
      A string containing the specified source machine image's selflink.
    """
    if not args.IsSpecified('source_machine_image'):
      return None
    ref = self.SOURCE_MACHINE_IMAGE.ResolveAsResource(args, resources)
    return ref.SelfLink()

  def _CreateRequests(self, args, instance_refs, project, zone, compute_client,
                      resource_parser, holder):
    """Creates a request for gcloud based on parameters.
    """
    # gcloud creates default values for some fields in Instance resource
    # when no value was specified on command line.
    # When --source-instance-template was specified, defaults are taken from
    # Instance Template and gcloud flags are used to override them - by default
    # fields should not be initialized.
    source_instance_template = instance_utils.GetSourceInstanceTemplate(
        args, resource_parser, self.SOURCE_INSTANCE_TEMPLATE
    )
    skip_defaults = source_instance_template is not None

    source_machine_image = self.GetSourceMachineImage(args, resource_parser)
    skip_defaults = skip_defaults or source_machine_image is not None

    scheduling = instance_utils.GetScheduling(
        args,
        compute_client,
        skip_defaults,
        support_node_affinity=True,
        support_node_project=True,
        support_host_error_timeout_seconds=self._support_host_error_timeout_seconds,
        support_max_run_duration=self._support_max_run_duration,
        support_local_ssd_recovery_timeout=self._support_local_ssd_recovery_timeout,
        support_graceful_shutdown=self._support_graceful_shutdown,
    )
    tags = instance_utils.GetTags(args, compute_client)
    labels = instance_utils.GetLabels(args, compute_client)
    metadata = instance_utils.GetMetadata(args, compute_client, skip_defaults)
    boot_disk_size_gb = instance_utils.GetBootDiskSizeGb(args)

    network_interfaces = create_utils.GetNetworkInterfacesWithValidation(
        args=args,
        resource_parser=resource_parser,
        compute_client=compute_client,
        holder=holder,
        project=project,
        location=zone,
        scope=compute_scopes.ScopeEnum.ZONE,
        skip_defaults=skip_defaults,
        support_public_dns=self._support_public_dns,
        support_ipv6_assignment=self._support_ipv6_assignment,
        support_internal_ipv6_reservation=self._support_internal_ipv6_reservation,
    )

    confidential_vm_type = instance_utils.GetConfidentialVmType(
        args, self._support_confidential_compute_type)

    create_boot_disk = not (
        instance_utils.UseExistingBootDisk((args.disk or []) +
                                           (args.create_disk or [])))

    image_uri = create_utils.GetImageUri(
        args,
        compute_client,
        create_boot_disk,
        project,
        resource_parser,
        confidential_vm_type,
        image_family_scope=args.image_family_scope,
        support_image_family_scope=True)

    shielded_instance_config = create_utils.BuildShieldedInstanceConfigMessage(
        messages=compute_client.messages, args=args)

    confidential_instance_config = (
        create_utils.BuildConfidentialInstanceConfigMessage(
            messages=compute_client.messages,
            args=args,
            support_confidential_compute_type=self
            ._support_confidential_compute_type,
            support_confidential_compute_type_tdx=self
            ._support_confidential_compute_type_tdx))

    csek_keys = csek_utils.CsekKeyStore.FromArgs(args,
                                                 self._support_rsa_encrypted)

    project_to_sa = create_utils.GetProjectToServiceAccountMap(
        args, instance_refs, compute_client, skip_defaults)

    requests = []
    for instance_ref in instance_refs:

      disks = []
      if create_utils.CheckSpecifiedDiskArgs(
          args=args, skip_defaults=skip_defaults,
          support_kms=self._support_kms):
        disks = create_utils.CreateDiskMessages(
            args=args,
            instance_name=instance_ref.Name(),
            project=instance_ref.project,
            location=instance_ref.zone,
            scope=compute_scopes.ScopeEnum.ZONE,
            compute_client=compute_client,
            resource_parser=resource_parser,
            boot_disk_size_gb=boot_disk_size_gb,
            image_uri=image_uri,
            create_boot_disk=create_boot_disk,
            csek_keys=csek_keys,
            holder=holder,
            support_kms=self._support_kms,
            support_nvdimm=self._support_nvdimm,
            support_source_snapshot_csek=self._support_source_snapshot_csek,
            support_boot_snapshot_uri=self._support_boot_snapshot_uri,
            support_image_csek=self._support_image_csek,
            support_create_disk_snapshots=self._support_create_disk_snapshots,
            support_replica_zones=self._support_replica_zones,
            support_multi_writer=self._support_multi_writer,
            support_storage_pool=self._support_storage_pool,
            support_source_instant_snapshot=self._support_source_instant_snapshot,
            support_boot_instant_snapshot_uri=self._support_boot_instant_snapshot_uri,
            support_enable_confidential_compute=self._support_enable_confidential_compute,
        )

      machine_type_uri = None
      if instance_utils.CheckSpecifiedMachineTypeArgs(args, skip_defaults):
        machine_type_uri = instance_utils.CreateMachineTypeUri(
            args=args,
            compute_client=compute_client,
            resource_parser=resource_parser,
            project=instance_ref.project,
            location=instance_ref.zone,
            scope=compute_scopes.ScopeEnum.ZONE,
            confidential_vm_type=confidential_vm_type)

      can_ip_forward = instance_utils.GetCanIpForward(args, skip_defaults)
      guest_accelerators = create_utils.GetAccelerators(
          args=args,
          compute_client=compute_client,
          resource_parser=resource_parser,
          project=instance_ref.project,
          location=instance_ref.zone,
          scope=compute_scopes.ScopeEnum.ZONE)

      instance = compute_client.messages.Instance(
          canIpForward=can_ip_forward,
          deletionProtection=args.deletion_protection,
          description=args.description,
          disks=disks,
          guestAccelerators=guest_accelerators,
          hostname=args.hostname,
          labels=labels,
          machineType=machine_type_uri,
          metadata=metadata,
          minCpuPlatform=args.min_cpu_platform,
          name=instance_ref.Name(),
          networkInterfaces=network_interfaces,
          serviceAccounts=project_to_sa[instance_ref.project],
          scheduling=scheduling,
          tags=tags)

      if self._support_partner_metadata and (
          args.partner_metadata or args.partner_metadata_from_file
      ):
        partner_metadata_dict = (
            partner_metadata_utils.CreatePartnerMetadataDict(args)
        )
        partner_metadata_utils.ValidatePartnerMetadata(partner_metadata_dict)
        partner_metadata_message = (
            compute_client.messages.Instance.PartnerMetadataValue()
        )
        for namespace, structured_entries in partner_metadata_dict.items():
          partner_metadata_message.additionalProperties.append(
              compute_client.messages.Instance.PartnerMetadataValue.AdditionalProperty(
                  key=namespace,
                  value=partner_metadata_utils.ConvertStructuredEntries(
                      structured_entries
                  ),
              )
          )
        instance.partnerMetadata = partner_metadata_message

      if self._support_instance_kms and args.CONCEPTS.instance_kms_key:
        instance.instanceEncryptionKey = kms_utils.MaybeGetKmsKey(
            args,
            compute_client.messages,
            instance.instanceEncryptionKey,
            instance_prefix=True)

      if self._support_secure_tag and args.secure_tags:
        instance.secureTags = secure_tags_utils.GetSecureTags(args.secure_tags)

      if args.resource_manager_tags:
        ret_resource_manager_tags = (
            resource_manager_tags_utils.GetResourceManagerTags(
                args.resource_manager_tags
            )
        )
        if ret_resource_manager_tags is not None:
          params = compute_client.messages.InstanceParams
          instance.params = params(
              resourceManagerTags=params.ResourceManagerTagsValue(
                  additionalProperties=[
                      params.ResourceManagerTagsValue.AdditionalProperty(
                          key=key, value=value) for key, value in sorted(
                              six.iteritems(ret_resource_manager_tags))
                  ]))

      if args.private_ipv6_google_access_type is not None:
        instance.privateIpv6GoogleAccess = (
            instances_flags.GetPrivateIpv6GoogleAccessTypeFlagMapper(
                compute_client.messages).GetEnumForChoice(
                    args.private_ipv6_google_access_type))

      has_visible_core_count = (
          self._support_visible_core_count and
          args.visible_core_count is not None)
      if (args.enable_nested_virtualization is not None or
          args.threads_per_core is not None or
          (self._support_numa_node_count and args.numa_node_count is not None)
          or has_visible_core_count or args.enable_uefi_networking is not None
          or (self._support_performance_monitoring_unit
              and args.performance_monitoring_unit)):
        visible_core_count = (
            args.visible_core_count if has_visible_core_count else None
        )
        instance.advancedMachineFeatures = (
            instance_utils.CreateAdvancedMachineFeaturesMessage(
                compute_client.messages, args.enable_nested_virtualization,
                args.threads_per_core,
                args.numa_node_count if self._support_numa_node_count else None,
                visible_core_count, args.enable_uefi_networking,
                args.performance_monitoring_unit
                if self._support_performance_monitoring_unit else None))

      resource_policies = getattr(args, 'resource_policies', None)
      if resource_policies:
        parsed_resource_policies = []
        for policy in resource_policies:
          resource_policy_ref = maintenance_util.ParseResourcePolicyWithZone(
              resource_parser,
              policy,
              project=instance_ref.project,
              zone=instance_ref.zone)
          parsed_resource_policies.append(resource_policy_ref.SelfLink())
        instance.resourcePolicies = parsed_resource_policies

      if shielded_instance_config:
        instance.shieldedInstanceConfig = shielded_instance_config

      if confidential_instance_config:
        instance.confidentialInstanceConfig = confidential_instance_config

      if self._support_erase_vss and args.IsSpecified(
          'erase_windows_vss_signature'):
        instance.eraseWindowsVssSignature = args.erase_windows_vss_signature

      if self._support_post_key_revocation_action_type and args.IsSpecified(
          'post_key_revocation_action_type'):
        instance.postKeyRevocationActionType = arg_utils.ChoiceToEnum(
            args.post_key_revocation_action_type, compute_client.messages
            .Instance.PostKeyRevocationActionTypeValueValuesEnum)

      if args.IsSpecified('key_revocation_action_type'):
        instance.keyRevocationActionType = arg_utils.ChoiceToEnum(
            args.key_revocation_action_type, compute_client.messages.Instance
            .KeyRevocationActionTypeValueValuesEnum)

      if args.IsSpecified('network_performance_configs'):
        instance.networkPerformanceConfig = (
            instance_utils.GetNetworkPerformanceConfig(args, compute_client)
        )

      request = compute_client.messages.ComputeInstancesInsertRequest(
          instance=instance,
          project=instance_ref.project,
          zone=instance_ref.zone)

      if source_instance_template:
        request.sourceInstanceTemplate = source_instance_template

      if source_machine_image:
        request.instance.sourceMachineImage = source_machine_image
        if args.IsSpecified('source_machine_image_csek_key_file'):
          key = instance_utils.GetSourceMachineImageKey(
              args, self.SOURCE_MACHINE_IMAGE, compute_client, holder)
          request.instance.sourceMachineImageEncryptionKey = key

      if self._support_machine_image_key and args.IsSpecified(
          'source_machine_image_csek_key_file'):
        if not args.IsSpecified('source_machine_image'):
          raise exceptions.RequiredArgumentException(
              '`--source-machine-image`',
              '`--source-machine-image-csek-key-file` requires '
              '`--source-machine-image` to be specified`')

      if args.IsSpecified('enable_display_device'):
        request.instance.displayDevice = compute_client.messages.DisplayDevice(
            enableDisplay=args.enable_display_device)

      request.instance.reservationAffinity = (
          instance_utils.GetReservationAffinity(
              args, compute_client, self._support_specific_then_x_affinity
          )
      )

      requests.append(
          (compute_client.apitools_client.instances, 'Insert', request))
    return requests

  def Run(self, args):
    instances_flags.ValidateDiskFlags(
        args,
        enable_kms=self._support_kms,
        enable_snapshots=True,
        enable_source_snapshot_csek=self._support_source_snapshot_csek,
        enable_image_csek=self._support_image_csek,
        enable_source_instant_snapshot=self._support_source_instant_snapshot,
    )
    instances_flags.ValidateImageFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)
    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    instances_flags.ValidateAcceleratorArgs(args)
    instances_flags.ValidateNetworkTierArgs(args)
    instances_flags.ValidateReservationAffinityGroup(args)
    instances_flags.ValidateNetworkPerformanceConfigsArgs(args)
    instances_flags.ValidateInstanceScheduling(
        args, support_max_run_duration=self._support_max_run_duration)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client
    resource_parser = holder.resources

    instance_refs = instance_utils.GetInstanceRefs(args, compute_client, holder)
    if len(instance_refs) > 1 and args.IsSpecified('address'):
      raise exceptions.BadArgumentException(
          '--address',
          'Multiple instances were specified for creation. --address flag can '
          'be used when creating a single instance.')

    requests = self._CreateRequests(args, instance_refs,
                                    instance_refs[0].project,
                                    instance_refs[0].zone, compute_client,
                                    resource_parser, holder)
    if not args.async_:
      # TODO(b/63664449): Replace this with poller + progress tracker.
      try:
        # Using legacy MakeRequests (which also does polling) here until
        # replaced by api_lib.utils.waiter.
        return compute_client.MakeRequests(requests)
      except exceptions.ToolException as e:
        invalid_machine_type_message_regex = (
            r'Invalid value for field \'resource.machineType\': .+. '
            r'Machine type with name \'.+\' does not exist in zone \'.+\'\.')
        if re.search(invalid_machine_type_message_regex, six.text_type(e)):
          raise compute_exceptions.ArgumentError(
              six.text_type(e) +
              '\nUse `gcloud compute machine-types list --zones` to see the '
              'available machine  types.')
        raise

    errors_to_collect = []
    responses = compute_client.AsyncRequests(requests, errors_to_collect)
    for r in responses:
      err = getattr(r, 'error', None)
      if err:
        errors_to_collect.append(poller.OperationErrors(err.errors))
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]

    log.status.Print('NOTE: The users will be charged for public IPs when VMs '
                     'are created.')

    for instance_ref, operation_ref in zip(instance_refs, operation_refs):
      log.status.Print('Instance creation in progress for [{}]: {}'.format(
          instance_ref.instance, operation_ref.SelfLink()))
    log.status.Print('Use [gcloud compute operations describe URI] command '
                     'to check the status of the operation(s).')
    if not args.IsSpecified('format'):
      # For async output we need a separate format. Since we already printed in
      # the status messages information about operations there is nothing else
      # needs to be printed.
      args.format = 'disable'
    return responses


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Compute Engine virtual machine instances."""

  _support_regional = True
  _support_kms = True
  _support_nvdimm = False
  _support_public_dns = False
  _support_erase_vss = True
  _support_machine_image_key = True
  _support_source_snapshot_csek = False
  _support_image_csek = False
  _support_post_key_revocation_action_type = True
  _support_rsa_encrypted = True
  _deprecate_maintenance_policy = False
  _support_create_disk_snapshots = True
  _support_boot_snapshot_uri = True
  _support_replica_zones = True
  _support_multi_writer = True
  _support_subinterface = False
  _support_secure_tag = False
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_network_queue_count = True
  _support_instance_kms = True
  _support_max_run_duration = True
  _support_ipv6_assignment = False
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_network_attachments = False
  _support_local_ssd_recovery_timeout = True
  _support_local_ssd_size = True
  _support_vlan_nic = False
  _support_performance_monitoring_unit = False
  _support_storage_pool = False
  _support_source_instant_snapshot = False
  _support_boot_instant_snapshot_uri = False
  _support_partner_metadata = False
  _support_enable_confidential_compute = True
  _support_specific_then_x_affinity = True
  _support_graceful_shutdown = False
  _support_igmp_query = False

  def GetSourceMachineImage(self, args, resources):
    """Retrieves the specified source machine image's selflink.

    Args:
      args: The arguments passed into the gcloud command calling this function.
      resources: Resource parser used to retrieve the specified resource
        reference.

    Returns:
      A string containing the specified source machine image's selflink.
    """
    if not args.IsSpecified('source_machine_image'):
      return None
    ref = self.SOURCE_MACHINE_IMAGE.ResolveAsResource(args, resources)
    return ref.SelfLink()

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        enable_regional=cls._support_regional,
        enable_kms=cls._support_kms,
        supports_erase_vss=cls._support_erase_vss,
        support_replica_zones=cls._support_replica_zones,
        support_multi_writer=cls._support_multi_writer,
        support_subinterface=cls._support_subinterface,
        support_host_error_timeout_seconds=cls._support_host_error_timeout_seconds,
        support_numa_node_count=cls._support_numa_node_count,
        support_instance_kms=cls._support_instance_kms,
        support_max_run_duration=cls._support_max_run_duration,
        support_network_attachments=cls._support_network_attachments,
        support_network_queue_count=cls._support_network_queue_count,
        support_local_ssd_recovery_timeout=cls._support_local_ssd_recovery_timeout,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_vlan_nic=cls._support_vlan_nic,
        support_storage_pool=cls._support_storage_pool,
        support_enable_confidential_compute=cls._support_enable_confidential_compute,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
        support_graceful_shutdown=cls._support_graceful_shutdown,
        support_igmp_query=cls._support_igmp_query,
    )
    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg()
    )
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    cls.SOURCE_MACHINE_IMAGE = (instances_flags.AddMachineImageArg())
    cls.SOURCE_MACHINE_IMAGE.AddArgument(parser)
    instances_flags.AddSourceMachineImageEncryptionKey(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.BETA)
    instances_flags.AddPrivateIpv6GoogleAccessArg(
        parser, utils.COMPUTE_BETA_API_VERSION)
    instances_flags.AddConfidentialComputeArgs(
        parser,
        support_confidential_compute_type=cls
        ._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx)
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
    instances_flags.AddKeyRevocationActionTypeArgs(parser)
    instances_flags.AddVisibleCoreCountArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create Compute Engine virtual machine instances."""

  _support_regional = True
  _support_kms = True
  _support_nvdimm = True
  _support_public_dns = True
  _support_erase_vss = True
  _support_machine_image_key = True
  _support_source_snapshot_csek = True
  _support_image_csek = True
  _support_post_key_revocation_action_type = True
  _support_rsa_encrypted = True
  _deprecate_maintenance_policy = True
  _support_create_disk_snapshots = True
  _support_boot_snapshot_uri = True
  _enable_pd_interface = True
  _support_replica_zones = True
  _support_multi_writer = True
  _support_subinterface = True
  _support_secure_tag = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = True
  _support_visible_core_count = True
  _support_network_queue_count = True
  _support_instance_kms = True
  _support_max_run_duration = True
  _support_ipv6_assignment = True
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_network_attachments = True
  _support_local_ssd_recovery_timeout = True
  _support_local_ssd_size = True
  _support_vlan_nic = True
  _support_performance_monitoring_unit = True
  _support_storage_pool = True
  _support_source_instant_snapshot = True
  _support_boot_instant_snapshot_uri = True
  _support_partner_metadata = True
  _support_enable_confidential_compute = True
  _support_specific_then_x_affinity = True
  _support_ipv6_only = True
  _support_graceful_shutdown = True
  _support_igmp_query = True

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        enable_regional=cls._support_regional,
        enable_kms=cls._support_kms,
        deprecate_maintenance_policy=cls._deprecate_maintenance_policy,
        supports_erase_vss=cls._support_erase_vss,
        snapshot_csek=cls._support_source_snapshot_csek,
        image_csek=cls._support_image_csek,
        support_replica_zones=cls._support_replica_zones,
        support_multi_writer=cls._support_multi_writer,
        support_subinterface=cls._support_subinterface,
        support_host_error_timeout_seconds=cls._support_host_error_timeout_seconds,
        support_numa_node_count=cls._support_numa_node_count,
        support_network_queue_count=cls._support_network_queue_count,
        support_instance_kms=cls._support_instance_kms,
        support_max_run_duration=cls._support_max_run_duration,
        support_network_attachments=cls._support_network_attachments,
        support_local_ssd_recovery_timeout=cls._support_local_ssd_recovery_timeout,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_vlan_nic=cls._support_vlan_nic,
        support_storage_pool=cls._support_storage_pool,
        support_source_instant_snapshot=cls._support_source_instant_snapshot,
        support_enable_confidential_compute=cls._support_enable_confidential_compute,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
        support_ipv6_only=cls._support_ipv6_only,
        support_graceful_shutdown=cls._support_graceful_shutdown,
        support_igmp_query=cls._support_igmp_query,
    )

    CreateAlpha.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg()
    )
    CreateAlpha.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
    CreateAlpha.SOURCE_MACHINE_IMAGE = (instances_flags.AddMachineImageArg())
    CreateAlpha.SOURCE_MACHINE_IMAGE.AddArgument(parser)
    instances_flags.AddSourceMachineImageEncryptionKey(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.ALPHA)
    instances_flags.AddPublicDnsArgs(parser, instance=True)
    instances_flags.AddLocalNvdimmArgs(parser)
    instances_flags.AddConfidentialComputeArgs(
        parser,
        support_confidential_compute_type=cls
        ._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx)
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
    instances_flags.AddPrivateIpv6GoogleAccessArg(
        parser, utils.COMPUTE_ALPHA_API_VERSION)
    instances_flags.AddStableFleetArgs(parser)
    instances_flags.AddSecureTagsArgs(parser)
    instances_flags.AddVisibleCoreCountArgs(parser)
    instances_flags.AddKeyRevocationActionTypeArgs(parser)
    instances_flags.AddIPv6AddressAlphaArgs(parser)
    instances_flags.AddIPv6PrefixLengthAlphaArgs(parser)
    instances_flags.AddPerformanceMonitoringUnitArgs(parser)
    instances_flags.AddAvailabilityDomainAgrs(parser)
    partner_metadata_utils.AddPartnerMetadataArgs(parser)


Create.detailed_help = DETAILED_HELP
