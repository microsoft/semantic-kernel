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
"""Command for labels update to instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import partner_metadata_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.command_lib.util.args import labels_util


DETAILED_HELP = {
    'DESCRIPTION': """
        *{command}* updates labels and requested CPU Platform for a
        Compute
        Engine virtual machine.
    """,
    'EXAMPLES': """
    To modify the instance 'example-instance' in 'us-central1-a' by adding
    labels 'k0', with value 'value1' and label 'k1' with value 'value2' and
    removing labels with key 'k3', run:

      $ {command} example-instance --zone=us-central1-a --update-labels=k0=value1,k1=value2 --remove-labels=k3

    Labels can be used to identify the instance. To list instances with the 'k1:value2' label, run:

      $ {parent_command} list --filter='labels.k1:value2'

    To list only the labels when describing a resource, use --format to filter the result:

      $ {parent_command} describe example-instance --format="default(labels)"
  """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Compute Engine virtual machine."""

  @staticmethod
  def Args(parser):

    flags.INSTANCE_ARG.AddArgument(parser, operation_type='update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddMinCpuPlatformArgs(parser, Update.ReleaseTrack())
    flags.AddDeletionProtectionFlag(parser, use_default_value=False)
    flags.AddShieldedInstanceConfigArgs(
        parser, use_default_value=False, for_update=True)
    flags.AddShieldedInstanceIntegrityPolicyArgs(parser)
    flags.AddDisplayDeviceArg(parser, is_update=True)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(holder.client))

    result = None

    labels_operation_ref = None
    min_cpu_platform_operation_ref = None
    deletion_protection_operation_ref = None
    shielded_instance_config_ref = None
    display_device_ref = None
    partner_metadata_operation_ref = None
    graceful_shutdown_operation_ref = None

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      instance = client.instances.Get(
          messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
      result = instance
      labels_operation_ref = self._GetLabelsOperationRef(
          labels_diff, instance, instance_ref, holder)
    if hasattr(args, 'min_cpu_platform') and args.min_cpu_platform is not None:
      min_cpu_platform_operation_ref = self._GetMinCpuPlatformOperationRef(
          args.min_cpu_platform, instance_ref, holder)
    if args.deletion_protection is not None:
      deletion_protection_operation_ref = (
          self._GetDeletionProtectionOperationRef(
              args.deletion_protection, instance_ref, holder))
    if hasattr(args, 'partner_metadata') and (
        args.partner_metadata or args.partner_metadata_from_file
    ):
      partner_metadata_operation_ref = self._GetPartnerMetadataOperationRef(
          args, instance_ref, holder
      )
    if (
        hasattr(args, 'graceful_shutdown')
        and args.IsSpecified('graceful_shutdown')
    ) or (
        hasattr(args, 'graceful_shutdown_max_duration')
        and args.IsSpecified('graceful_shutdown_max_duration')
    ):
      graceful_shutdown_operation_ref = self._GetGracefulShutdownOperationRef(
          args, instance_ref, holder
      )

    operation_poller = poller.Poller(client.instances)
    result = self._WaitForResult(
        operation_poller, labels_operation_ref,
        'Updating labels of instance [{0}]', instance_ref.Name()) or result
    result = self._WaitForResult(
        operation_poller, min_cpu_platform_operation_ref,
        'Changing minimum CPU platform of instance [{0}]',
        instance_ref.Name()) or result
    result = self._WaitForResult(
        operation_poller, deletion_protection_operation_ref,
        'Setting deletion protection of instance [{0}] to [{1}]',
        instance_ref.Name(), args.deletion_protection) or result
    result = self._WaitForResult(
        operation_poller, partner_metadata_operation_ref,
        'Updating partner metadata of instance [{0}]',
        instance_ref.Name()) or result
    result = (
        self._WaitForResult(
            operation_poller,
            graceful_shutdown_operation_ref,
            'Updating graceful shutdown configuration of instance [{0}]',
            instance_ref.Name(),
        )
        or result
    )

    if (args.IsSpecified('shielded_vm_secure_boot') or
        args.IsSpecified('shielded_vm_vtpm') or
        args.IsSpecified('shielded_vm_integrity_monitoring')):
      shielded_instance_config_ref = self._GetShieldedInstanceConfigRef(
          instance_ref, args, holder)
      result = self._WaitForResult(
          operation_poller, shielded_instance_config_ref,
          'Setting shieldedInstanceConfig  of instance [{0}]',
          instance_ref.Name()) or result

    if args.IsSpecified('shielded_vm_learn_integrity_policy'):
      shielded_instance_integrity_policy_ref = (
          self._GetShieldedInstanceIntegrityPolicyRef(instance_ref, holder))
      result = self._WaitForResult(
          operation_poller, shielded_instance_integrity_policy_ref,
          'Setting shieldedInstanceIntegrityPolicy of instance [{0}]',
          instance_ref.Name()) or result

    if args.IsSpecified('enable_display_device'):
      display_device_ref = self._GetDisplayDeviceOperationRef(
          args.enable_display_device, instance_ref, holder)
      result = self._WaitForResult(operation_poller, display_device_ref,
                                   'Updating display device of instance [{0}]',
                                   instance_ref.Name()) or result

    if instance_utils.IsAnySpecified(args, 'node', 'node_affinity_file',
                                     'node_group', 'clear_node_affinities'):
      update_scheduling_ref = self._GetUpdateInstanceSchedulingRef(
          instance_ref, args, holder)
      result = self._WaitForResult(
          operation_poller,
          update_scheduling_ref, 'Updating the scheduling of instance [{0}]',
          instance_ref.Name()) or result

    return result

  def _GetUpdateInstanceSchedulingRef(self, instance_ref, args, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages
    if instance_utils.IsAnySpecified(args, 'node', 'node_affinity_file',
                                     'node_group'):
      affinities = sole_tenancy_util.GetSchedulingNodeAffinityListFromArgs(
          args, messages)
    elif args.IsSpecified('clear_node_affinities'):
      affinities = []
    else:
      # No relevant args were specified. We shouldn't have called this function.
      return None
    instance = client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
    instance.scheduling.nodeAffinities = affinities

    request = messages.ComputeInstancesUpdateRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
        instanceResource=instance,
        minimalAction=messages.ComputeInstancesUpdateRequest
        .MinimalActionValueValuesEnum.NO_EFFECT,
        mostDisruptiveAllowedAction=messages.ComputeInstancesUpdateRequest
        .MostDisruptiveAllowedActionValueValuesEnum.REFRESH)

    operation = client.instances.Update(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _GetShieldedInstanceConfigRef(self, instance_ref, args, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages

    if (args.shielded_vm_secure_boot is None and
        args.shielded_vm_vtpm is None and
        args.shielded_vm_integrity_monitoring is None):
      return None
    shieldedinstance_config_message = instance_utils.CreateShieldedInstanceConfigMessage(
        messages, args.shielded_vm_secure_boot, args.shielded_vm_vtpm,
        args.shielded_vm_integrity_monitoring)

    request = messages.ComputeInstancesUpdateShieldedInstanceConfigRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        shieldedInstanceConfig=shieldedinstance_config_message,
        zone=instance_ref.zone)

    operation = client.instances.UpdateShieldedInstanceConfig(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _GetShieldedInstanceIntegrityPolicyRef(self, instance_ref, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages

    shieldedinstance_integrity_policy_message = (
        instance_utils.CreateShieldedInstanceIntegrityPolicyMessage(messages))

    request = messages.ComputeInstancesSetShieldedInstanceIntegrityPolicyRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        shieldedInstanceIntegrityPolicy=shieldedinstance_integrity_policy_message,
        zone=instance_ref.zone)

    operation = client.instances.SetShieldedInstanceIntegrityPolicy(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _GetLabelsOperationRef(self, labels_diff, instance, instance_ref, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages

    labels_update = labels_diff.Apply(
        messages.InstancesSetLabelsRequest.LabelsValue,
        instance.labels)

    if labels_update.needs_update:
      request = messages.ComputeInstancesSetLabelsRequest(
          project=instance_ref.project,
          instance=instance_ref.instance,
          zone=instance_ref.zone,
          instancesSetLabelsRequest=
          messages.InstancesSetLabelsRequest(
              labelFingerprint=instance.labelFingerprint,
              labels=labels_update.labels))

      operation = client.instances.SetLabels(request)
      return holder.resources.Parse(
          operation.selfLink, collection='compute.zoneOperations')

  def _GetMinCpuPlatformOperationRef(self, min_cpu_platform, instance_ref,
                                     holder):
    client = holder.client.apitools_client
    messages = holder.client.messages
    embedded_request = messages.InstancesSetMinCpuPlatformRequest(
        minCpuPlatform=min_cpu_platform or None)
    request = messages.ComputeInstancesSetMinCpuPlatformRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        instancesSetMinCpuPlatformRequest=embedded_request,
        zone=instance_ref.zone)

    operation = client.instances.SetMinCpuPlatform(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _GetDeletionProtectionOperationRef(self, deletion_protection,
                                         instance_ref, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages
    request = messages.ComputeInstancesSetDeletionProtectionRequest(
        deletionProtection=deletion_protection,
        project=instance_ref.project,
        resource=instance_ref.instance,
        zone=instance_ref.zone)

    operation = client.instances.SetDeletionProtection(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _GetDisplayDeviceOperationRef(self, display_device, instance_ref, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages
    request = messages.ComputeInstancesUpdateDisplayDeviceRequest(
        displayDevice=messages.DisplayDevice(
            enableDisplay=display_device),
        project=instance_ref.project,
        instance=instance_ref.instance,
        zone=instance_ref.zone)

    operation = client.instances.UpdateDisplayDevice(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _GetGracefulShutdownOperationRef(self, args, instance_ref, holder):
    messages = holder.client.messages
    client = holder.client.apitools_client
    instance = client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict())
    )

    updated_graceful_shutdown_message = instance.scheduling.gracefulShutdown
    if hasattr(args, 'graceful_shutdown') and args.IsSpecified(
        'graceful_shutdown'
    ):
      if updated_graceful_shutdown_message is None:
        updated_graceful_shutdown_message = (
            messages.SchedulingGracefulShutdown()
        )
      updated_graceful_shutdown_message.enabled = args.graceful_shutdown
    if hasattr(args, 'graceful_shutdown_max_duration') and args.IsSpecified(
        'graceful_shutdown_max_duration'
    ):
      if updated_graceful_shutdown_message is None:
        updated_graceful_shutdown_message = (
            messages.SchedulingGracefulShutdown()
        )
      updated_graceful_shutdown_message.maxDuration = messages.Duration(
          seconds=args.graceful_shutdown_max_duration
      )

    instance.scheduling.gracefulShutdown = updated_graceful_shutdown_message

    request = messages.ComputeInstancesUpdateRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
        instanceResource=instance,
        minimalAction=messages.ComputeInstancesUpdateRequest.MinimalActionValueValuesEnum.NO_EFFECT,
        mostDisruptiveAllowedAction=messages.ComputeInstancesUpdateRequest.MostDisruptiveAllowedActionValueValuesEnum.REFRESH,
    )

    operation = client.instances.Update(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations'
    )

  def _GetPartnerMetadataOperationRef(self, args, instance_ref, holder):
    messages = holder.client.messages
    client = holder.client.apitools_client
    partner_metadata_dict = (
        partner_metadata_utils.CreatePartnerMetadataDict(args)
    )
    partner_metadata_utils.ValidatePartnerMetadata(partner_metadata_dict)
    partner_metadata_message = messages.Instance.PartnerMetadataValue()
    for namespace, structured_entries in partner_metadata_dict.items():
      partner_metadata_message.additionalProperties.append(
          messages.Instance.PartnerMetadataValue.AdditionalProperty(
              key=namespace,
              value=partner_metadata_utils.ConvertStructuredEntries(
                  structured_entries
              ),
          )
      )
    instance = client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
    instance.partnerMetadata = partner_metadata_message
    request = messages.ComputeInstancesUpdateRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
        instanceResource=instance,
        minimalAction=messages.ComputeInstancesUpdateRequest
        .MinimalActionValueValuesEnum.NO_EFFECT,
        mostDisruptiveAllowedAction=messages.ComputeInstancesUpdateRequest
        .MostDisruptiveAllowedActionValueValuesEnum.REFRESH)

    operation = client.instances.Update(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _WaitForResult(self, operation_poller, operation_ref, message, *args):
    if operation_ref:
      return waiter.WaitFor(
          operation_poller, operation_ref, message.format(*args))
    return None


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Compute Engine virtual machine."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddMinCpuPlatformArgs(parser, UpdateBeta.ReleaseTrack())
    flags.AddDeletionProtectionFlag(parser, use_default_value=False)
    flags.AddShieldedInstanceConfigArgs(
        parser, use_default_value=False, for_update=True)
    flags.AddShieldedInstanceIntegrityPolicyArgs(parser)
    flags.AddDisplayDeviceArg(parser, is_update=True)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Compute Engine virtual machine."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddMinCpuPlatformArgs(parser, UpdateAlpha.ReleaseTrack())
    flags.AddDeletionProtectionFlag(parser, use_default_value=False)
    flags.AddShieldedInstanceConfigArgs(
        parser, use_default_value=False, for_update=True)
    flags.AddShieldedInstanceIntegrityPolicyArgs(parser)
    flags.AddDisplayDeviceArg(parser, is_update=True)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)
    partner_metadata_utils.AddPartnerMetadataArgs(parser)
    flags.AddGracefulShutdownArgs(parser)


Update.detailed_help = DETAILED_HELP
