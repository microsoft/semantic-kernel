# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for setting machine type for virtual machine instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instances import flags


def _CommonArgs(parser):
  """Register parser args common to all tracks."""
  flags.INSTANCE_ARG.AddArgument(parser)
  flags.AddMachineTypeArgs(
      parser,
      unspecified_help=(
          ' Either this flag, --custom-cpu, or --custom-memory must be '
          'specified.'))
  flags.AddCustomMachineTypeArgs(parser)


class SetMachineType(base.SilentCommand):
  """Set machine type for Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def _ValidateMachineTypePresence(self, args):
    if (not args.IsSpecified('custom_cpu') and
        not args.IsSpecified('custom_memory') and
        not args.IsSpecified('machine_type')):
      raise calliope_exceptions.OneOfArgumentsRequiredException(
          ['--custom-cpu', '--custom-memory', '--machine-type'],
          'One of --custom-cpu, --custom-memory, --machine-type must be '
          'specified.')

  def Run(self, args):
    """Invokes request necessary for setting scheduling options."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    self._ValidateMachineTypePresence(args)

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    machine_type = instance_utils.InterpretMachineType(
        machine_type=args.machine_type,
        custom_cpu=args.custom_cpu,
        custom_memory=args.custom_memory,
        ext=getattr(args, 'custom_extensions', None),
        vm_type=getattr(args, 'custom_vm_type', None))

    instance_utils.CheckCustomCpuRamRatio(client,
                                          instance_ref.project,
                                          instance_ref.zone, machine_type)

    machine_type_uri = holder.resources.Parse(
        machine_type, collection='compute.machineTypes',
        params={
            'project': instance_ref.project,
            'zone': instance_ref.zone
        }).SelfLink()

    set_machine_type_request = client.messages.InstancesSetMachineTypeRequest(
        machineType=machine_type_uri)
    request = client.messages.ComputeInstancesSetMachineTypeRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        instancesSetMachineTypeRequest=set_machine_type_request,
        zone=instance_ref.zone)

    return client.MakeRequests([(client.apitools_client.instances,
                                 'SetMachineType', request)])


SetMachineType.detailed_help = {
    'brief': 'Set machine type for Compute Engine virtual machines',
    'DESCRIPTION': """
        ``{command}'' lets you change the machine type of a virtual machine
        in the *TERMINATED* state (that is, a virtual machine instance that
        has been stopped).

        For example, if ``example-instance'' is a ``g1-small'' virtual machine
        currently in the *TERMINATED* state, running:

          $ {command} example-instance --zone us-central1-b --machine-type n1-standard-4

        will change the machine type to ``n1-standard-4'', so that when you
        next start ``example-instance'', it will be provisioned as an
        ``n1-standard-4'' instead of a ``g1-small''.

        See [](https://cloud.google.com/compute/docs/machine-types) for more
        information on machine types.
        """,
    'EXAMPLES': """
      To change the machine type of a VM to `n1-standard-4`, run:

        $ {command} example-instance --zone=us-central1-b --machine-type=n1-standard-4

      """
}
