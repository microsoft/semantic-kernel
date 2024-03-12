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
"""Command for creating VM instances running Docker images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.instances.create import utils as create_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _Args(parser,
          deprecate_maintenance_policy=False,
          container_mount_enabled=False,
          support_multi_writer=True,
          support_confidential_compute_type=False,
          support_confidential_compute_type_tdx=False):
  """Add flags shared by all release tracks."""
  parser.display_info.AddFormat(instances_flags.DEFAULT_LIST_FORMAT)
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(
      parser, True, container_mount_enabled=container_mount_enabled)
  instances_flags.AddCreateDiskArgs(
      parser,
      container_mount_enabled=container_mount_enabled,
      support_multi_writer=support_multi_writer)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddContainerMountDiskFlag(parser)
  instances_flags.AddAddressArgs(parser, instances=True, containers=True)
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  instances_flags.AddMaintenancePolicyArgs(
      parser, deprecate=deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddProvisioningModelVmArgs(parser)
  instances_flags.AddInstanceTerminationActionVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(parser, False)
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddNetworkPerformanceConfigsArgs(parser)
  instances_flags.AddShieldedInstanceConfigArgs(
      parser=parser, for_container=True)
  instances_flags.AddKonletArgs(parser)
  instances_flags.AddPublicPtrArgs(parser, instance=True)
  instances_flags.AddImageArgs(parser)
  instances_flags.AddConfidentialComputeArgs(
      parser,
      support_confidential_compute_type,
      support_confidential_compute_type_tdx)
  instances_flags.AddNestedVirtualizationArgs(parser)
  instances_flags.AddThreadsPerCoreArgs(parser)
  instances_flags.AddIPv6AddressArgs(parser)
  instances_flags.AddIPv6PrefixLengthArgs(parser)
  labels_util.AddCreateLabelsFlags(parser)

  parser.add_argument(
      '--description', help='Specifies a textual description of the instances.')

  instances_flags.INSTANCES_ARG.AddArgument(parser, operation_type='create')

  CreateWithContainer.SOURCE_INSTANCE_TEMPLATE = (
      instances_flags.MakeSourceInstanceTemplateArg())
  CreateWithContainer.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)
  parser.display_info.AddCacheUpdater(completers.InstancesCompleter)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateWithContainer(base.CreateCommand):
  """Command for creating VM instances running container images."""

  _container_mount_disk_enabled = True
  _support_create_boot_disk = True
  _support_match_container_mount_disks = True
  _support_nvdimm = False
  _support_host_error_timeout_seconds = False
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_confidential_compute_type = False
  _support_confidential_compute_type_tdx = False
  _support_local_ssd_recovery_timeout = True
  _support_internal_ipv6_reservation = False

  @staticmethod
  def Args(parser):
    """Register parser args."""
    _Args(
        parser,
        container_mount_enabled=True,
        support_multi_writer=False,
        support_confidential_compute_type=False,
        support_confidential_compute_type_tdx=False)
    instances_flags.AddNetworkTierArgs(parser, instance=True)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.GA)
    instances_flags.AddPrivateIpv6GoogleAccessArg(parser,
                                                  utils.COMPUTE_GA_API_VERSION)
    instances_flags.AddVisibleCoreCountArgs(parser)
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)

  def _ValidateArgs(self, args):
    self._ValidateTrackSpecificArgs(args)
    instances_flags.ValidateAcceleratorArgs(args)
    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateNetworkTierArgs(args)
    instances_flags.ValidateKonletArgs(args)
    instances_flags.ValidateDiskCommonFlags(args)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    instances_flags.ValidatePublicPtrFlags(args)
    instances_flags.ValidateNetworkPerformanceConfigsArgs(args)
    instances_flags.ValidateInstanceScheduling(args)
    if instance_utils.UseExistingBootDisk(args.disk or []):
      raise exceptions.InvalidArgumentException(
          '--disk', 'Boot disk specified for containerized VM.')

  def _ValidateTrackSpecificArgs(self, args):
    return None

  def GetImageUri(self, args, compute_client, resource_parser, instance_refs):
    if (args.IsSpecified('image') or args.IsSpecified('image_family') or
        args.IsSpecified('image_project')):
      image_expander = image_utils.ImageExpander(compute_client,
                                                 resource_parser)
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=instance_refs[0].project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project)
      if resource_parser.Parse(image_uri).project != 'cos-cloud':
        log.warning('This container deployment mechanism requires a '
                    'Container-Optimized OS image in order to work. Select an '
                    'image from a cos-cloud project (cos-stable, cos-beta, '
                    'cos-dev image families).')
    else:
      image_uri = containers_utils.ExpandKonletCosImageFlag(compute_client)
    return image_uri

  def _GetNetworkInterfaces(self, args, client, holder, project, location,
                            scope, skip_defaults):
    return create_utils.GetNetworkInterfaces(args, client, holder, project,
                                             location, scope, skip_defaults)

  def GetNetworkInterfaces(self, args, resources, client, holder, project,
                           location, scope, skip_defaults):
    if args.network_interface:
      return create_utils.CreateNetworkInterfaceMessages(
          resources=resources,
          compute_client=client,
          network_interface_arg=args.network_interface,
          project=project,
          location=location,
          scope=scope,
          support_internal_ipv6_reservation=self._support_internal_ipv6_reservation,
      )
    return self._GetNetworkInterfaces(args, client, holder, project, location,
                                      scope, skip_defaults)

  def CheckDiskMessageArgs(self, args, skip_defaults):
    """Creates API messages with disks attached to VM instance."""
    flags_to_check = [
        'create_disk', 'local_ssd', 'boot_disk_type', 'boot_disk_device_name',
        'boot_disk_auto_delete', 'boot_disk_provisioned_iops'
    ]
    if hasattr(args, 'local_nvdimm'):
      flags_to_check.append('local_nvdimm')
    if (skip_defaults and not args.IsSpecified('disk') and
        not instance_utils.IsAnySpecified(args, *flags_to_check)):
      return False
    return True

  def Run(self, args):
    self._ValidateArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client
    resource_parser = holder.resources

    container_mount_disk = instances_flags.GetValidatedContainerMountDisk(
        holder, args.container_mount_disk, args.disk, args.create_disk)
    source_instance_template = instance_utils.GetSourceInstanceTemplate(
        args, resource_parser, self.SOURCE_INSTANCE_TEMPLATE)
    skip_defaults = instance_utils.GetSkipDefaults(source_instance_template)
    scheduling = instance_utils.GetScheduling(
        args,
        compute_client,
        skip_defaults,
        support_min_node_cpu=False,
        support_host_error_timeout_seconds=self
        ._support_host_error_timeout_seconds,
        support_local_ssd_recovery_timeout=self._support_local_ssd_recovery_timeout)
    service_accounts = instance_utils.GetServiceAccounts(
        args, compute_client, skip_defaults)
    user_metadata = instance_utils.GetValidatedMetadata(args, compute_client)
    boot_disk_size_gb = instance_utils.GetBootDiskSizeGb(args)
    instance_refs = instance_utils.GetInstanceRefs(args, compute_client, holder)
    network_interfaces = self.GetNetworkInterfaces(
        args, resource_parser, compute_client, holder, instance_refs[0].project,
        instance_refs[0].zone, compute_scopes.ScopeEnum.ZONE, skip_defaults)
    image_uri = self.GetImageUri(args, compute_client, resource_parser,
                                 instance_refs)
    labels = containers_utils.GetLabelsMessageWithCosVersion(
        args.labels, image_uri, resource_parser,
        compute_client.messages.Instance)
    can_ip_forward = instance_utils.GetCanIpForward(args, skip_defaults)
    tags = containers_utils.CreateTagsMessage(compute_client.messages,
                                              args.tags)
    confidential_vm_type = instance_utils.GetConfidentialVmType(
        args, self._support_confidential_compute_type)

    requests = []
    for instance_ref in instance_refs:
      metadata = containers_utils.CreateKonletMetadataMessage(
          compute_client.messages,
          args,
          instance_ref.Name(),
          user_metadata,
          container_mount_disk_enabled=self._container_mount_disk_enabled,
          container_mount_disk=container_mount_disk)

      disks = []
      if self.CheckDiskMessageArgs(args, skip_defaults):
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
            create_boot_disk=self._support_create_boot_disk,
            support_nvdimm=self._support_nvdimm,
            support_match_container_mount_disks=self
            ._support_match_container_mount_disks)

      machine_type_uri = None
      if instance_utils.CheckSpecifiedMachineTypeArgs(args, skip_defaults):
        machine_type_uri = create_utils.CreateMachineTypeUri(
            args=args,
            compute_client=compute_client,
            resource_parser=resource_parser,
            project=instance_ref.project,
            location=instance_ref.zone,
            scope=compute_scopes.ScopeEnum.ZONE,
            confidential_vm_type=confidential_vm_type)

      guest_accelerators = create_utils.GetAccelerators(
          args=args,
          compute_client=compute_client,
          resource_parser=resource_parser,
          project=instance_ref.project,
          location=instance_ref.zone,
          scope=compute_scopes.ScopeEnum.ZONE)

      instance = compute_client.messages.Instance(
          canIpForward=can_ip_forward,
          disks=disks,
          guestAccelerators=guest_accelerators,
          description=args.description,
          labels=labels,
          machineType=machine_type_uri,
          metadata=metadata,
          minCpuPlatform=args.min_cpu_platform,
          name=instance_ref.Name(),
          networkInterfaces=network_interfaces,
          serviceAccounts=service_accounts,
          scheduling=scheduling,
          tags=tags)
      if args.private_ipv6_google_access_type is not None:
        instance.privateIpv6GoogleAccess = (
            instances_flags.GetPrivateIpv6GoogleAccessTypeFlagMapper(
                compute_client.messages).GetEnumForChoice(
                    args.private_ipv6_google_access_type))

      confidential_instance_config = (
          create_utils.BuildConfidentialInstanceConfigMessage(
              messages=compute_client.messages,
              args=args,
              support_confidential_compute_type=self
              ._support_confidential_compute_type,
              support_confidential_compute_type_tdx=self
              ._support_confidential_compute_type_tdx))
      if confidential_instance_config:
        instance.confidentialInstanceConfig = confidential_instance_config

      has_visible_core_count = (
          self._support_visible_core_count and
          args.visible_core_count is not None)
      if (args.enable_nested_virtualization is not None or
          args.threads_per_core is not None or
          (self._support_numa_node_count and
           args.numa_node_count is not None) or has_visible_core_count):
        visible_core_count = args.visible_core_count if has_visible_core_count else None
        instance.advancedMachineFeatures = (
            instance_utils.CreateAdvancedMachineFeaturesMessage(
                compute_client.messages, args.enable_nested_virtualization,
                args.threads_per_core,
                args.numa_node_count if self._support_numa_node_count else None,
                visible_core_count))

      shielded_instance_config = create_utils.BuildShieldedInstanceConfigMessage(
          messages=compute_client.messages, args=args)
      if shielded_instance_config:
        instance.shieldedInstanceConfig = shielded_instance_config

      if args.IsSpecified('network_performance_configs'):
        instance.networkPerformanceConfig = (
            instance_utils.GetNetworkPerformanceConfig(args, compute_client))

      request = compute_client.messages.ComputeInstancesInsertRequest(
          instance=instance,
          sourceInstanceTemplate=source_instance_template,
          project=instance_ref.project,
          zone=instance_ref.zone)

      requests.append(
          (compute_client.apitools_client.instances, 'Insert', request))

    return compute_client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateWithContainerBeta(CreateWithContainer):
  """Command for creating VM instances running container images."""

  _container_mount_disk_enabled = True
  _support_create_boot_disk = True
  _support_match_container_mount_disks = True
  _support_nvdimm = False
  _support_visible_core_count = True
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = False
  _support_local_ssd_recovery_timeout = True

  @staticmethod
  def Args(parser):
    """Register parser args."""
    _Args(
        parser,
        container_mount_enabled=True,
        support_confidential_compute_type=True,
        support_confidential_compute_type_tdx=True)
    instances_flags.AddNetworkTierArgs(parser, instance=True)
    instances_flags.AddLocalSsdArgs(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.BETA)
    instances_flags.AddPrivateIpv6GoogleAccessArg(
        parser, utils.COMPUTE_BETA_API_VERSION)
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)
    instances_flags.AddVisibleCoreCountArgs(parser)
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)

  def _ValidateTrackSpecificArgs(self, args):
    instances_flags.ValidateLocalSsdFlags(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateWithContainerAlpha(CreateWithContainerBeta):
  """Alpha version of compute instances create-with-container command."""

  _container_mount_disk_enabled = True
  _support_create_boot_disk = True
  _support_match_container_mount_disks = True
  _support_nvdimm = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = True
  _support_visible_core_count = True
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_local_ssd_recovery_timeout = True

  @staticmethod
  def Args(parser):
    _Args(
        parser,
        deprecate_maintenance_policy=True,
        container_mount_enabled=True,
        support_confidential_compute_type=True,
        support_confidential_compute_type_tdx=True)

    instances_flags.AddNetworkTierArgs(parser, instance=True)
    instances_flags.AddLocalSsdArgsWithSize(parser)
    instances_flags.AddLocalNvdimmArgs(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.ALPHA)
    instances_flags.AddPublicDnsArgs(parser, instance=True)
    instances_flags.AddPrivateIpv6GoogleAccessArg(
        parser, utils.COMPUTE_ALPHA_API_VERSION)
    instances_flags.AddStackTypeArgs(parser)
    instances_flags.AddIpv6NetworkTierArgs(parser)
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)
    instances_flags.AddNumaNodeCountArgs(parser)
    instances_flags.AddVisibleCoreCountArgs(parser)
    instances_flags.AddIPv6AddressAlphaArgs(parser)
    instances_flags.AddIPv6PrefixLengthAlphaArgs(parser)
    instances_flags.AddInternalIPv6AddressArgs(parser)
    instances_flags.AddInternalIPv6PrefixLengthArgs(parser)

  def _ValidateTrackSpecificArgs(self, args):
    instances_flags.ValidateLocalSsdFlags(args)
    instances_flags.ValidatePublicDnsFlags(args)
    instances_flags.ValidatePublicPtrFlags(args)

  def _GetNetworkInterfaces(self, args, client, holder, project, location,
                            scope, skip_defaults):
    return create_utils.GetNetworkInterfacesAlpha(args, client, holder, project,
                                                  location, scope,
                                                  skip_defaults)


CreateWithContainer.detailed_help = {
    'brief':
        """\
    Creates Compute Engine virtual machine instances running
    container images.
    """,
    'DESCRIPTION':
        """\
        *{command}* creates Compute Engine virtual
        machines that runs a Docker image. For example:

          $ {command} instance-1 --zone us-central1-a \
            --container-image=gcr.io/google-containers/busybox

        creates an instance called instance-1, in the us-central1-a zone,
        running the 'busybox' image.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES':
        """\
        To run the gcr.io/google-containers/busybox image on an instance named
        'instance-1' that executes 'echo "Hello world"' as a run command, run:

          $ {command} instance-1 \
            --container-image=gcr.io/google-containers/busybox \
            --container-command='echo "Hello world"'

        To run the gcr.io/google-containers/busybox image in privileged mode,
        run:

          $ {command} instance-1 \
            --container-image=gcr.io/google-containers/busybox
            --container-privileged
        """
}
