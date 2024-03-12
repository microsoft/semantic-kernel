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
"""Command for setting scheduling for virtual machine instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.core.util import times


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetSchedulingInstances(base.SilentCommand):
  """Set scheduling options for Compute Engine virtual machines.

    *${command}* is used to update scheduling options for VM instances.
    You can only call this method on a VM instance that is stopped
    (a VM instance in a `TERMINATED` state).
  """

  detailed_help = {
      'EXAMPLES':
          """
  To set instance to be terminated during maintenance, run:

    $ {command} example-instance  --maintenance-policy=TERMINATE --zone=us-central1-b
  """
  }

  _support_host_error_timeout_seconds = False
  _support_local_ssd_recovery_timeout = True
  _support_max_run_duration = False
  _support_graceful_shutdown = False

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--restart-on-failure',
        action=arg_parsers.StoreTrueFalseAction,
        help="""\
        The instances will be restarted if they are terminated by Compute
        Engine.  This does not affect terminations performed by the user.
        This option is mutually exclusive with --preemptible.
        """)

    flags.AddPreemptibleVmArgs(parser, is_update=True)
    flags.AddProvisioningModelVmArgs(parser)
    flags.AddInstanceTerminationActionVmArgs(parser, is_update=True)
    flags.AddMaintenancePolicyArgs(parser)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)
    flags.INSTANCE_ARG.AddArgument(parser)
    flags.AddMinNodeCpuArg(parser, is_update=True)
    flags.AddLocalSsdRecoveryTimeoutArgs(parser)

  def _Run(self, args):
    """Issues request necessary for setting scheduling options."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    scheduling_options = client.messages.Scheduling()

    scheduling_options.automaticRestart = args.restart_on_failure

    if args.IsSpecified('preemptible'):
      scheduling_options.preemptible = args.preemptible

    if self._support_host_error_timeout_seconds and hasattr(
        args, 'host_error_timeout_seconds'):
      scheduling_options.hostErrorTimeoutSeconds = args.host_error_timeout_seconds

    if self._support_graceful_shutdown:
      graceful_shutdown = instance_utils.ExtractGracefulShutdownFromArgs(
          args, self._support_graceful_shutdown
      )
      if graceful_shutdown is not None:
        scheduling_options.gracefulShutdown = (
            client.messages.SchedulingGracefulShutdown()
        )
        if 'enabled' in graceful_shutdown:
          scheduling_options.gracefulShutdown.enabled = graceful_shutdown[
              'enabled'
          ]
        if 'maxDuration' in graceful_shutdown:
          scheduling_options.gracefulShutdown.maxDuration = (
              client.messages.Duration(seconds=graceful_shutdown['maxDuration'])
          )

    if (
        self._support_local_ssd_recovery_timeout
        and hasattr(args, 'local_ssd_recovery_timeout')
        and args.IsSpecified('local_ssd_recovery_timeout')
    ):
      scheduling_options.localSsdRecoveryTimeout = client.messages.Duration(
          seconds=args.local_ssd_recovery_timeout)

    if (hasattr(args, 'provisioning_model') and
        args.IsSpecified('provisioning_model')):
      scheduling_options.provisioningModel = (
          client.messages.Scheduling.ProvisioningModelValueValuesEnum(
              args.provisioning_model))

    cleared_fields = []

    if (hasattr(args, 'instance_termination_action') and
        args.IsSpecified('instance_termination_action')):
      flags.ValidateInstanceScheduling(args, self._support_max_run_duration)
      scheduling_options.instanceTerminationAction = (
          client.messages.Scheduling.InstanceTerminationActionValueValuesEnum(
              args.instance_termination_action))
    elif args.IsSpecified('clear_instance_termination_action'):
      scheduling_options.instanceTerminationAction = None
      cleared_fields.append('instanceTerminationAction')

    if args.IsSpecified('min_node_cpu'):
      scheduling_options.minNodeCpus = int(args.min_node_cpu)
    elif args.IsSpecified('clear_min_node_cpu'):
      scheduling_options.minNodeCpus = None
      cleared_fields.append('minNodeCpus')

    if args.IsSpecified('maintenance_policy'):
      scheduling_options.onHostMaintenance = (
          client.messages.Scheduling.OnHostMaintenanceValueValuesEnum(
              args.maintenance_policy))

    if hasattr(args, 'max_run_duration') and args.IsSpecified(
        'max_run_duration'
    ):
      scheduling_options.maxRunDuration = client.messages.Duration(
          seconds=args.max_run_duration
      )
    elif hasattr(args, 'clear_max_run_duration') and args.IsSpecified(
        'clear_max_run_duration'
    ):
      scheduling_options.maxRunDuration = None
      cleared_fields.append('maxRunDuration')

    if hasattr(args, 'termination_time') and args.IsSpecified(
        'termination_time'
    ):
      scheduling_options.terminationTime = times.FormatDateTime(
          args.termination_time
      )
    elif hasattr(args, 'clear_termination_time') and args.IsSpecified(
        'clear_termination_time'
    ):
      scheduling_options.terminationTime = None
      cleared_fields.append('terminationTime')

    if instance_utils.IsAnySpecified(args, 'node', 'node_affinity_file',
                                     'node_group'):
      affinities = sole_tenancy_util.GetSchedulingNodeAffinityListFromArgs(
          args, client.messages)
      scheduling_options.nodeAffinities = affinities
    elif args.IsSpecified('clear_node_affinities'):
      scheduling_options.nodeAffinities = []
      cleared_fields.append('nodeAffinities')

    with holder.client.apitools_client.IncludeFields(cleared_fields):
      request = client.messages.ComputeInstancesSetSchedulingRequest(
          instance=instance_ref.Name(),
          project=instance_ref.project,
          scheduling=scheduling_options,
          zone=instance_ref.zone)

      return client.MakeRequests([(client.apitools_client.instances,
                                   'SetScheduling', request)])

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetSchedulingInstancesBeta(SetSchedulingInstances):
  """Set scheduling options for Compute Engine virtual machines.

    *${command}* is used to update scheduling options for VM instances.
    You can only call this method on a VM instance that is stopped
    (a VM instance in a `TERMINATED` state).
  """
  _support_host_error_timeout_seconds = True
  _support_max_run_duration = True
  _support_local_ssd_recovery_timeout = True

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--restart-on-failure',
        action=arg_parsers.StoreTrueFalseAction,
        help="""\
        The instances will be restarted if they are terminated by Compute
        Engine.  This does not affect terminations performed by the user.
        This option is mutually exclusive with --preemptible.
        """)

    flags.AddPreemptibleVmArgs(parser, is_update=True)
    flags.AddProvisioningModelVmArgs(parser)
    flags.AddInstanceTerminationActionVmArgs(parser, is_update=True)
    flags.AddMaintenancePolicyArgs(parser)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)
    flags.INSTANCE_ARG.AddArgument(parser)
    flags.AddMinNodeCpuArg(parser, is_update=True)
    flags.AddHostErrorTimeoutSecondsArgs(parser)
    flags.AddMaxRunDurationVmArgs(parser, is_update=True)
    flags.AddLocalSsdRecoveryTimeoutArgs(parser)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetSchedulingInstancesAlpha(SetSchedulingInstancesBeta):
  """Set scheduling options for Compute Engine virtual machines.

    *${command}* is used to update scheduling options for VM instances.
    You can only call this method on a VM instance that is stopped
    (a VM instance in a `TERMINATED` state).
  """
  _support_host_error_timeout_seconds = True
  _support_local_ssd_recovery_timeout = True
  _support_max_run_duration = True
  _support_graceful_shutdown = True

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--restart-on-failure',
        action=arg_parsers.StoreTrueFalseAction,
        help="""\
        The instances will be restarted if they are terminated by Compute
        Engine.  This does not affect terminations performed by the user.
        This option is mutually exclusive with --preemptible.
        """)

    flags.AddPreemptibleVmArgs(parser, is_update=True)
    flags.AddProvisioningModelVmArgs(parser)
    flags.AddInstanceTerminationActionVmArgs(parser, is_update=True)
    # Deprecated in Alpha
    flags.AddMaintenancePolicyArgs(parser, deprecate=True)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser, is_update=True)
    flags.INSTANCE_ARG.AddArgument(parser)
    flags.AddMinNodeCpuArg(parser, is_update=True)
    flags.AddHostErrorTimeoutSecondsArgs(parser)
    flags.AddLocalSsdRecoveryTimeoutArgs(parser)
    flags.AddMaxRunDurationVmArgs(parser, is_update=True)
    flags.AddGracefulShutdownArgs(parser)
