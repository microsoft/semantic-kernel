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
"""Command for creating instance with per instance config."""

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
from googlecloudsdk.command_lib.compute.instance_groups.managed.instance_configs import instance_configs_messages


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateInstanceGA(base.CreateCommand):
  """Create a new virtual machine instance in a managed instance group."""

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=True).AddArgument(
            parser, operation_type='create instance in')
    instance_groups_flags.AddCreateInstancesFlags(parser)

  @staticmethod
  def _CreateNewInstanceReference(holder, igm_ref, instance_name):
    """Creates reference to instance in instance group (zonal or regional)."""
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      instance_ref = holder.resources.Parse(
          instance_name,
          params={
              'project': igm_ref.project,
              'zone': igm_ref.zone,
          },
          collection='compute.instances')
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      instance_ref = holder.resources.Parse(
          instance_name,
          params={
              'project': igm_ref.project,
              'zone': igm_ref.region + '-a',
          },
          collection='compute.instances')
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))
    if not instance_ref:
      raise managed_instance_groups_utils.ResourceCannotBeResolvedException(
          'Instance name {0} cannot be resolved.'.format(instance_name))
    return instance_ref

  def Run(self, args):
    self._ValidateStatefulFlagsForInstanceConfigs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
               .ResolveAsResource)(
                   args,
                   resources,
                   scope_lister=compute_flags.GetDefaultScopeLister(client))

    instance_ref = self._CreateNewInstanceReference(
        holder=holder, igm_ref=igm_ref, instance_name=args.instance)

    per_instance_config_message = self._CreatePerInstanceConfgMessage(
        holder, instance_ref, args)

    operation_ref, service = instance_configs_messages.CallCreateInstances(
        holder=holder,
        igm_ref=igm_ref,
        per_instance_config_message=per_instance_config_message)

    operation_poller = poller.Poller(service)
    create_result = waiter.WaitFor(operation_poller, operation_ref,
                                   'Creating instance.')
    return create_result

  def _ValidateStatefulFlagsForInstanceConfigs(self, args):
    instance_groups_flags.ValidateMigStatefulFlagsForInstanceConfigs(
        args, need_disk_source=True)
    instance_groups_flags.ValidateMigStatefulIPFlagsForInstanceConfigs(
        args, current_internal_addresses=[], current_external_addresses=[]
    )

  def _CreatePerInstanceConfgMessage(self, holder, instance_ref, args):
    return instance_configs_messages.CreatePerInstanceConfigMessageWithIPs(
        holder,
        instance_ref,
        args.stateful_disk,
        args.stateful_metadata,
        args.stateful_internal_ip,
        args.stateful_external_ip,
        disk_getter=NonExistentDiskGetter(),
    )


CreateInstanceGA.detailed_help = {
    'brief': (
        'Create a new virtual machine instance in a managed instance group '
        'with a defined name and optionally its stateful configuration.'
    ),
    'DESCRIPTION': """\
      *{command}* creates a  virtual machine instance with a defined name and
      optionally its stateful configuration: stateful disk, stateful
      metadata key-values, and stateful IP addresses. Stateful configuration
      is stored in the corresponding newly created per-instance config.
      An instance with a per-instance config will preserve its given name,
      specified disks, specified metadata key-values, and specified internal
      and external IPs during instance recreation, auto-healing, updates,
      and any other lifecycle transitions of the instance.
      """,
    'EXAMPLES': """\
      To create an instance `instance-1` in `my-group`
      (in region europe-west4) with metadata `my-key: my-value`, a disk
      `disk-1` attached to it as the device `device-1`,
      stateful internal IP `192.168.0.10` on the default interface (nic0),
      and existing address reservation `my-address` for stateful external IP
      on interface `nic1`, run:

          $ {command} \\
                my-group --region=europe-west4 \\
                --instance=instance-1 \\
                --stateful-disk='device-name=foo,source=https://compute.googleapis.com/compute/alpha/projects/my-project/zones/europe-west4/disks/disk-1,mode=rw,auto-delete=on-permanent-instance-deletion' \\
                --stateful-metadata='my-key=my-value' \\
                --stateful-internal-ip=address=192.168.0.10,auto-delete=on-permanent-instance-deletion \\
                --stateful-external-ip=address=/projects/example-project/regions/europe-west4/addresses/my-address,interface-name=nic1
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateInstanceBeta(CreateInstanceGA):
  """Create a new virtual machine instance in a managed instance group."""


CreateInstanceBeta.detailed_help = CreateInstanceGA.detailed_help


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateInstanceAlpha(CreateInstanceBeta):
  """Create a new virtual machine instance in a managed instance group."""


CreateInstanceAlpha.detailed_help = CreateInstanceBeta.detailed_help


class NonExistentDiskGetter(object):
  """Placeholder class returning None."""

  def __init__(self):
    self.instance_exists = False

  def get_disk(self, device_name):  # pylint: disable=unused-argument,g-bad-name
    return
