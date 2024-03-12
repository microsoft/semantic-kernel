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

"""Command for updating managed instance config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_configs_getter
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_configs_messages
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_disk_getter
import six


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update per-instance config of a managed instance group."""

  @staticmethod
  def _PatchDiskData(messages, preserved_disk, update_disk_data):
    """Patch preserved disk according to arguments of `update_disk_data`."""
    auto_delete = update_disk_data.get('auto-delete')
    if update_disk_data.get('source'):
      preserved_disk.source = update_disk_data.get('source')
    if update_disk_data.get('mode'):
      preserved_disk.mode = instance_configs_messages.GetMode(
          messages=messages, mode=update_disk_data.get('mode'))
    if auto_delete:
      preserved_disk.autoDelete = auto_delete.GetAutoDeleteEnumValue(
          messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum)
    return preserved_disk

  @staticmethod
  def _UpdateStatefulDisks(messages, per_instance_config, disks_to_update_dict,
                           disks_to_remove_set, disk_getter):
    """Patch and return the updated list of stateful disks."""
    new_stateful_disks = []
    existing_disks = ((
        per_instance_config.preservedState.disks.additionalProperties)
                      if per_instance_config.preservedState.disks else [])
    removed_stateful_disks_set = set()
    for current_stateful_disk in existing_disks:
      disk_name = current_stateful_disk.key
      # Disk to be removed
      if disk_name in disks_to_remove_set:
        removed_stateful_disks_set.add(disk_name)
        continue
      # Disk to be updated
      if disk_name in disks_to_update_dict:
        UpdateGA._PatchDiskData(messages, current_stateful_disk.value,
                                disks_to_update_dict[disk_name])
        del disks_to_update_dict[disk_name]
      new_stateful_disks.append(current_stateful_disk)
    # Verify that there are no extraneous disks to be removed.
    unremoved_stateful_disks_set = (
        disks_to_remove_set.difference(removed_stateful_disks_set))
    if unremoved_stateful_disks_set:
      raise exceptions.InvalidArgumentException(
          parameter_name='--remove-stateful-disk',
          message=('The following are invalid stateful disks: `{0}`'.format(
              ','.join(unremoved_stateful_disks_set))))
    for update_stateful_disk in disks_to_update_dict.values():
      new_stateful_disks.append(
          instance_configs_messages.MakePreservedStateDiskEntry(
              messages=messages,
              stateful_disk_data=update_stateful_disk,
              disk_getter=disk_getter))
    return new_stateful_disks

  @staticmethod
  def _UpdateStatefulMetadata(messages, per_instance_config,
                              update_stateful_metadata,
                              remove_stateful_metadata):
    """Patch and return updated stateful metadata."""
    existing_metadata = []
    if per_instance_config.preservedState.metadata:
      existing_metadata = (per_instance_config.preservedState.metadata
                           .additionalProperties)
    new_stateful_metadata = {
        metadata.key: metadata.value
        for metadata in existing_metadata
    }
    for metadata_key in remove_stateful_metadata or []:
      if metadata_key in new_stateful_metadata:
        del new_stateful_metadata[metadata_key]
      else:
        raise exceptions.InvalidArgumentException(
            parameter_name='--remove-stateful-metadata',
            message=('stateful metadata key to remove `{0}` does not exist in'
                     ' the given instance config'.format(metadata_key)))
    new_stateful_metadata.update(update_stateful_metadata)
    return new_stateful_metadata

  def _CombinePerInstanceConfigMessage(self, holder, per_instance_config,
                                       instance_ref, args):
    update_stateful_disks = args.stateful_disk
    remove_stateful_disks = args.remove_stateful_disks
    update_stateful_metadata = args.stateful_metadata
    remove_stateful_metadata = args.remove_stateful_metadata

    messages = holder.client.messages
    # Patch stateful disks.
    disk_getter = instance_disk_getter.InstanceDiskGetter(
        instance_ref=instance_ref, holder=holder)
    disks_to_remove_set = set(remove_stateful_disks or [])
    disks_to_update_dict = {
        update_stateful_disk.get('device-name'): update_stateful_disk
        for update_stateful_disk in (update_stateful_disks or [])
    }
    new_stateful_disks = UpdateGA._UpdateStatefulDisks(
        messages, per_instance_config, disks_to_update_dict,
        disks_to_remove_set, disk_getter)

    # Patch stateful metadata.
    new_stateful_metadata = UpdateGA._UpdateStatefulMetadata(
        messages, per_instance_config, update_stateful_metadata,
        remove_stateful_metadata)

    per_instance_config.preservedState.disks = (
        messages.PreservedState.DisksValue(
            additionalProperties=new_stateful_disks))

    per_instance_config.preservedState.metadata = (
        messages.PreservedState.MetadataValue(additionalProperties=[
            instance_configs_messages.MakePreservedStateMetadataEntry(
                messages, key=key, value=value)
            for key, value in sorted(six.iteritems(new_stateful_metadata))
        ]))

    UpdateGA._PatchStatefulInternalIPs(
        messages=messages,
        per_instance_config=per_instance_config,
        ips_to_update=args.stateful_internal_ip,
        ips_to_remove=args.remove_stateful_internal_ips,
    )
    UpdateGA._PatchStatefulExternalIPs(
        messages=messages,
        per_instance_config=per_instance_config,
        ips_to_update=args.stateful_external_ip,
        ips_to_remove=args.remove_stateful_external_ips,
    )

    return per_instance_config

  @staticmethod
  def _PatchStatefulInternalIPs(
      messages, per_instance_config, ips_to_update, ips_to_remove
  ):
    """Patch and return the updated list of stateful internal IPs."""
    existing_ips = (
        per_instance_config.preservedState.internalIPs.additionalProperties
        if per_instance_config.preservedState.internalIPs
        else []
    )
    ips_to_update_dict = {
        (
            ip.get(
                'interface-name',
                instance_groups_flags.STATEFUL_IP_DEFAULT_INTERFACE_NAME,
            )
        ): ip
        for ip in iter(ips_to_update or [])
    }
    UpdateGA._VerifyStatefulIPsToRemoveSet(
        '--remove-stateful-internal-ips', existing_ips, ips_to_remove
    )
    new_stateful_ips, remaining_ips_to_update = UpdateGA._UpdateExistingIPs(
        messages, existing_ips, ips_to_update_dict, ips_to_remove
    )
    new_stateful_ips.extend(
        UpdateGA._CreateInternalIPs(messages, remaining_ips_to_update)
    )
    per_instance_config.preservedState.internalIPs = (
        messages.PreservedState.InternalIPsValue(
            additionalProperties=new_stateful_ips
        )
    )

  @staticmethod
  def _PatchStatefulExternalIPs(
      messages, per_instance_config, ips_to_update, ips_to_remove
  ):
    """Patch and return the updated list of stateful external IPs."""
    existing_ips = (
        per_instance_config.preservedState.externalIPs.additionalProperties
        if per_instance_config.preservedState.externalIPs
        else []
    )
    ips_to_update_dict = {
        (
            ip.get(
                'interface-name',
                instance_groups_flags.STATEFUL_IP_DEFAULT_INTERFACE_NAME,
            )
        ): ip
        for ip in iter(ips_to_update or [])
    }
    UpdateGA._VerifyStatefulIPsToRemoveSet(
        '--remove-stateful-external-ips', existing_ips, ips_to_remove
    )
    new_stateful_ips, remaining_ips_to_update = UpdateGA._UpdateExistingIPs(
        messages, existing_ips, ips_to_update_dict, ips_to_remove
    )
    new_stateful_ips.extend(
        UpdateGA._CreateExternalIPs(messages, remaining_ips_to_update)
    )
    per_instance_config.preservedState.externalIPs = (
        messages.PreservedState.ExternalIPsValue(
            additionalProperties=new_stateful_ips
        )
    )

  @staticmethod
  def _CreateInstanceReference(holder, igm_ref, instance_name):
    """Creates reference to instance in instance group (zonal or regional)."""
    if instance_name.startswith('https://') or instance_name.startswith(
        'http://'):
      return holder.resources.ParseURL(instance_name)
    instance_references = (
        managed_instance_groups_utils.CreateInstanceReferences)(
            holder=holder, igm_ref=igm_ref, instance_names=[instance_name])
    if not instance_references:
      raise managed_instance_groups_utils.ResourceCannotBeResolvedException(
          'Instance name {0} cannot be resolved'.format(instance_name))
    return instance_references[0]

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=True).AddArgument(
            parser, operation_type='update per-instance config for')
    instance_groups_flags.AddMigStatefulFlagsForUpdateInstanceConfigs(parser)
    instance_groups_flags.AddMigStatefulUpdateInstanceFlag(parser)
    instance_groups_flags.AddMigStatefulIPsFlagsForUpdateInstanceConfigs(parser)

  def _ValidateStatefulFlagsForInstanceConfigs(self, args, per_instance_config):
    instance_groups_flags.ValidateMigStatefulFlagsForInstanceConfigs(
        args, for_update=True)
    instance_groups_flags.ValidateMigStatefulIPFlagsForInstanceConfigs(
        args,
        UpdateGA._GetInterfacesWithInternalAddresses(per_instance_config),
        UpdateGA._GetInterfacesWithExternalAddresses(per_instance_config),
        for_update=True,
    )

  @staticmethod
  def _GetExistingInterfaceNames(existing_ips):
    return map(lambda x: x.key, existing_ips)

  @staticmethod
  def _VerifyStatefulIPsToRemoveSet(
      remove_ips_flag_name, existing_ips, ips_to_remove
  ):
    """Verify that there are no extraneous IP interfaces to be removed."""
    ips_to_remove_set = set(ips_to_remove or [])
    existing_interfaces = UpdateGA._GetExistingInterfaceNames(existing_ips)
    extraneous_interfaces = ips_to_remove_set.difference(existing_interfaces)
    if extraneous_interfaces:
      raise exceptions.InvalidArgumentException(
          parameter_name=remove_ips_flag_name,
          message=(
              'The following are invalid stateful IPs to remove: `{0}`'.format(
                  ','.join(extraneous_interfaces)
              )
          ),
      )

  @staticmethod
  def _UpdateExistingIPs(
      messages, existing_ips, ips_to_update_dict, ips_to_remove
  ):
    new_stateful_ips = []
    remaining_ips_to_update = dict(ips_to_update_dict)
    ips_to_remove_set = set(ips_to_remove or [])
    for current_stateful_ip in existing_ips:
      interface_name = current_stateful_ip.key
      # Interface to be removed.
      if interface_name in ips_to_remove_set:
        continue
      # Interface to be updated.
      if interface_name in remaining_ips_to_update:
        instance_configs_messages.PatchPreservedStateNetworkIpEntry(
            messages,
            current_stateful_ip.value,
            remaining_ips_to_update[interface_name],
        )
        del remaining_ips_to_update[interface_name]
      new_stateful_ips.append(current_stateful_ip)
    return new_stateful_ips, remaining_ips_to_update

  @staticmethod
  def _CreateInternalIPs(messages, new_ips_dict):
    new_stateful_ips = []
    for update_stateful_ip in new_ips_dict.values():
      new_stateful_ips.append(
          instance_configs_messages.MakePreservedStateInternalNetworkIpEntry(
              messages=messages, stateful_ip=update_stateful_ip
          )
      )
    return new_stateful_ips

  @staticmethod
  def _CreateExternalIPs(messages, new_ips_dict):
    new_stateful_ips = []
    for update_stateful_ip in new_ips_dict.values():
      new_stateful_ips.append(
          instance_configs_messages.MakePreservedStateExternalNetworkIpEntry(
              messages=messages, stateful_ip=update_stateful_ip
          )
      )
    return new_stateful_ips

  @staticmethod
  def _GetInterfacesWithInternalAddresses(per_instance_config):
    existing_ips = (
        per_instance_config.preservedState.internalIPs.additionalProperties
        if per_instance_config.preservedState.internalIPs
        else []
    )
    return UpdateGA._GetExistingInterfaceNames(existing_ips)

  @staticmethod
  def _GetInterfacesWithExternalAddresses(per_instance_config):
    existing_ips = (
        per_instance_config.preservedState.externalIPs.additionalProperties
        if per_instance_config.preservedState.externalIPs
        else []
    )
    return UpdateGA._GetExistingInterfaceNames(existing_ips)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
               ResolveAsResource)(
                   args,
                   resources,
                   scope_lister=compute_flags.GetDefaultScopeLister(client),
               )
    instance_ref = self._CreateInstanceReference(
        holder=holder, igm_ref=igm_ref, instance_name=args.instance)

    configs_getter = (
        instance_configs_getter.InstanceConfigsGetterWithSimpleCache)(
            client)
    configs_getter.check_if_instance_config_exists(
        igm_ref=igm_ref, instance_ref=instance_ref, should_exist=True)
    per_instance_config = configs_getter.get_instance_config(
        igm_ref=igm_ref, instance_ref=instance_ref)

    self._ValidateStatefulFlagsForInstanceConfigs(args, per_instance_config)

    per_instance_config_message = self._CombinePerInstanceConfigMessage(
        holder, per_instance_config, instance_ref, args)

    operation_ref = instance_configs_messages.CallPerInstanceConfigUpdate(
        holder=holder,
        igm_ref=igm_ref,
        per_instance_config_message=per_instance_config_message)

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = holder.client.apitools_client.instanceGroupManagers
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = holder.client.apitools_client.regionInstanceGroupManagers
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    operation_poller = poller.Poller(service)
    update_result = waiter.WaitFor(operation_poller, operation_ref,
                                   'Updating instance config.')

    if args.update_instance:
      apply_operation_ref = (
          instance_configs_messages.CallApplyUpdatesToInstances)(
              holder=holder,
              igm_ref=igm_ref,
              instances=[six.text_type(instance_ref)],
              minimal_action=args.instance_update_minimal_action)
      return waiter.WaitFor(operation_poller, apply_operation_ref,
                            'Applying updates to instances.')

    return update_result


UpdateGA.detailed_help = {
    'brief': 'Update per-instance config of a managed instance group.',
    'DESCRIPTION': """\
        *{command}* updates the per-instance config of an instance controlled by
        a Compute Engine managed instance group. The command lets you
        change the list of instance-specific stateful resources, that is, the
        list of resources that are preserved during instance restarts and
        recreations.

        Changes are applied immediately to the corresponding instances, by
        performing the necessary action (for example, REFRESH), unless
        overridden by providing the ``--no-update-instance'' flag.
        """,
    'EXAMPLES': """\
        To updates the stateful disk ``my-disk-3'' to the image provided by
        ``source'', and clear ``my-disk1'' and ``my-disk2'' as stateful
        disks, and to add stateful metadata ``my-key'': ``my-value'', on
        instance ``my-instance'', run:

          $ {{command}} {group} {region} {instance} {disk} {remove_disks} {meta}

        If ``my-disk-3'' did not exist previously in the per-instance config,
        and if it does not exist in the group's instance template, then the
        command adds ``my-disk-3'' to ``my-instance''. The command also removes
        stateful configuration for ``my-disk-1'' and ``my-disk-2''; if these
        disk are not defined in the group's instance template, then they are
        detached.

        To update a per-instance configuration with a stateful internal IP
        ``192.168.0.10'', on instance ``my-instance'', run:

          $ {{command}} {group} {region} {instance} {internal_ip}

        To update a per-instance configuration to remove a stateful external IP
        that's defined in network interface nic0, on instance my-instance, run:

          $ {{command}} {group} {region} {instance} {remove_internal_ip}
        """.format(
        group='my-group',
        region='--region=europe-west4',
        instance='--instance=my-instance',
        disk=(
            '--stateful-disk=device-name=my-disk-3,source='
            'projects/my-project/zones/us-central1-a/disks/my-disk-3'
        ),
        remove_disks='--remove-stateful-disks=my-disk-1,my-disk-2',
        meta="--stateful-metadata='my-key=my-value'",
        internal_ip=(
            '--stateful-internal-ip=address=192.168.0.10,interface-name=nic0'
        ),
        remove_internal_ip='--remove-stateful-internal-ips=nic0',
    ),
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(UpdateGA):
  """Update per-instance config of a managed instance group."""

  @classmethod
  def Args(cls, parser):
    UpdateGA.Args(parser)


UpdateBeta.detailed_help = UpdateGA.detailed_help


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update per-instance config of a managed instance group."""

  @classmethod
  def Args(cls, parser):
    UpdateBeta.Args(parser)


UpdateAlpha.detailed_help = UpdateBeta.detailed_help
