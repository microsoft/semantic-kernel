# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for suspending instances owned by a managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SuspendInstances(base.Command):
  """Suspend instances owned by a managed instance group."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
        table(project(),
              zone(),
              instanceName:label=INSTANCE,
              status)""")
    parser.add_argument('--instances',
                        type=arg_parsers.ArgList(min_length=1),
                        metavar='INSTANCE',
                        required=True,
                        help='Names of instances to suspend.')
    parser.add_argument(
        '--force',
        default=False,
        action='store_true',
        help="""
          Immediately suspend the specified instances, skipping the initial
          delay, if one is specified in the standby policy.""")
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister)

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      instances_holder_field = 'instanceGroupManagersSuspendInstancesRequest'
      request = client.messages.ComputeInstanceGroupManagersSuspendInstancesRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagersSuspendInstancesRequest=client.messages
          .InstanceGroupManagersSuspendInstancesRequest(instances=[]),
          project=igm_ref.project,
          zone=igm_ref.zone)
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      instances_holder_field = 'regionInstanceGroupManagersSuspendInstancesRequest'
      request = client.messages.ComputeRegionInstanceGroupManagersSuspendInstancesRequest(
          instanceGroupManager=igm_ref.Name(),
          regionInstanceGroupManagersSuspendInstancesRequest=client.messages
          .RegionInstanceGroupManagersSuspendInstancesRequest(instances=[]),
          project=igm_ref.project,
          region=igm_ref.region,
      )
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    if args.IsSpecified('force'):
      if igm_ref.Collection() == 'compute.instanceGroupManagers':
        request.instanceGroupManagersSuspendInstancesRequest.forceSuspend = args.force
      else:
        request.regionInstanceGroupManagersSuspendInstancesRequest.forceSuspend = args.force

    return instance_groups_utils.SendInstancesRequestsAndPostProcessOutputs(
        api_holder=holder,
        method_name='SuspendInstances',
        request_template=request,
        instances_holder_field=instances_holder_field,
        igm_ref=igm_ref,
        instances=args.instances)


SuspendInstances.detailed_help = {
    'brief': 'Suspend instances owned by a managed instance group.',
    'DESCRIPTION': """
        *{command}* suspends one or more instances from a managed instance
group, thereby reducing the targetSize and increasing the targetSuspendedSize
of the group.

The command returns the operation status per instance, which might be ``FAIL'',
``SUCCESS'', or ``MEMBER_NOT_FOUND''. ``MEMBER_NOT_FOUND'' is returned only for
regional groups when the gcloud command-line tool wasn't able to resolve the
zone from the instance name.
""",
    'EXAMPLES': """\
      To suspend an instance from a managed instance group in the us-central1-a
      zone, run:

              $ {command} example-managed-instance-group --zone=us-central1-a \\
              --instances=example-instance
    """,
}
