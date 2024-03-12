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

"""Command for creating per-instance config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_configs_getter
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_configs_messages
import six


# TODO(b/70321546): rewrite help
@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create per-instance config for an instance in a managed instance group."""

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=True).AddArgument(
            parser, operation_type='create a per-instance config for')
    instance_groups_flags.AddMigStatefulFlagsForInstanceConfigs(parser)
    instance_groups_flags.AddMigStatefulUpdateInstanceFlag(parser)
    instance_groups_flags.AddMigStatefulIPsFlagsForInstanceConfigs(parser)

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

  def Run(self, args):
    self._ValidateStatefulFlagsForInstanceConfigs(args)

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
        igm_ref=igm_ref, instance_ref=instance_ref, should_exist=False)

    per_instance_config_message = self._CreatePerInstanceConfigMessage(
        holder, instance_ref, args)

    operation_ref = instance_configs_messages.CallPerInstanceConfigUpdate(
        holder=holder,
        igm_ref=igm_ref,
        per_instance_config_message=per_instance_config_message)

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = client.apitools_client.instanceGroupManagers
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = client.apitools_client.regionInstanceGroupManagers
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    operation_poller = poller.Poller(service)
    create_result = waiter.WaitFor(operation_poller, operation_ref,
                                   'Creating instance config.')

    if args.update_instance:
      apply_operation_ref = (
          instance_configs_messages.CallApplyUpdatesToInstances)(
              holder=holder,
              igm_ref=igm_ref,
              instances=[six.text_type(instance_ref)],
              minimal_action=args.instance_update_minimal_action)
      return waiter.WaitFor(operation_poller, apply_operation_ref,
                            'Applying updates to instances.')

    return create_result

  def _ValidateStatefulFlagsForInstanceConfigs(self, args):
    instance_groups_flags.ValidateMigStatefulFlagsForInstanceConfigs(args)
    instance_groups_flags.ValidateMigStatefulIPFlagsForInstanceConfigs(
        args=args, current_internal_addresses=[], current_external_addresses=[])

  def _CreatePerInstanceConfigMessage(self, holder, instance_ref, args):
    return instance_configs_messages.CreatePerInstanceConfigMessageWithIPs(
        holder,
        instance_ref,
        args.stateful_disk,
        args.stateful_metadata,
        args.stateful_internal_ip,
        args.stateful_external_ip,
    )


CreateGA.detailed_help = {
    'brief': (
        'Create a per-instance config for an instance in a '
        'managed instance group.'
    ),
    'DESCRIPTION': """\
        *{command}* creates a per-instance config for an instance controlled by
        a Compute Engine managed instance group. An instance with a per-instance
        config preserves the specified metadata and/or disks during
        instance recreation and deletion.

        Once created, the config is applied immediately to the corresponding
        instance, by performing the necessary action (for example, REFRESH),
        unless overridden by providing the ``--no-update-instance'' flag.
        """,
    'EXAMPLES': """\
        To create a per-instance config with a stateful disk ``my-disk'' and to
        add stateful metadata ``my-key:my-value'', on instance
        ``my-instance'', run:

          $ {{command}} {group} {region} {instance} {disk} {metadata}

        If ``my-disk'' did not exist previously in the per-instance config,
        and if it does not exist in the group's instance template, then the
        command adds ``my-disk'' to my-instance.

        To create a per-instance config with a stateful internal IP
        ``192.168.0.10'' and a stateful external IP reserved in address
        ``my-address'', on instance ``my-instance'', run:

          $ {{command}} {group} {region} {instance} {internal_ip} {external_ip}

        If the provided IP address is not yet reserved, the MIG automatically
        creates a corresponding IP address reservation.
        """.format(
        group='my-group',
        region='--region=europe-west4',
        instance='--instance=my-instance',
        disk=(
            '--stateful-disk=device-name=my-disk,source='
            'projects/my-project/zones/us-central1-a/disks/my-disk-3'
        ),
        metadata='--stateful-metadata="my-key=my-value"',
        internal_ip=(
            '--stateful-internal-ip=address=192.168.0.10,interface-name=nic0'
        ),
        external_ip=(
            '--stateful-external-ip=address='
            '/projects/example-project/regions/europe-west4/'
            'addresses/my-address'
            ',interface-name=nic0'
        ),
    ),
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create per-instance config for an instance in a managed instance group."""

  @classmethod
  def Args(cls, parser):
    CreateGA.Args(parser)


CreateBeta.detailed_help = CreateGA.detailed_help


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create per-instance config for an instance in a managed instance group."""

  @classmethod
  def Args(cls, parser):
    CreateBeta.Args(parser)


CreateAlpha.detailed_help = CreateBeta.detailed_help
