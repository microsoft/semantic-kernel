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
"""Command for resuming instances owned by a managed instance group."""

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
class ResumeInstances(base.Command):
  """Resume instances owned by a managed instance group."""

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
                        help='Names of instances to resume.')
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
      instances_holder_field = 'instanceGroupManagersResumeInstancesRequest'
      request = client.messages.ComputeInstanceGroupManagersResumeInstancesRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagersResumeInstancesRequest=client.messages
          .InstanceGroupManagersResumeInstancesRequest(instances=[]),
          project=igm_ref.project,
          zone=igm_ref.zone)
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      instances_holder_field = 'regionInstanceGroupManagersResumeInstancesRequest'
      request = client.messages.ComputeRegionInstanceGroupManagersResumeInstancesRequest(
          instanceGroupManager=igm_ref.Name(),
          regionInstanceGroupManagersResumeInstancesRequest=client.messages
          .RegionInstanceGroupManagersResumeInstancesRequest(instances=[]),
          project=igm_ref.project,
          region=igm_ref.region,
      )
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    return instance_groups_utils.SendInstancesRequestsAndPostProcessOutputs(
        api_holder=holder,
        method_name='ResumeInstances',
        request_template=request,
        instances_holder_field=instances_holder_field,
        igm_ref=igm_ref,
        instances=args.instances)


ResumeInstances.detailed_help = {
    'brief': 'Resume the suspended instances in a managed instance group.',
    'DESCRIPTION': """
        *{command}* resumes one or more instances from a managed instance group,
thereby increasing the targetSize and reducing the targetSuspendedSize of the
group.

The command returns the operation status per instance, which might be ``FAIL'',
``SUCCESS'', or ``MEMBER_NOT_FOUND''. ``MEMBER_NOT_FOUND'' is returned only for
regional groups when the gcloud command-line tool wasn't able to resolve the
zone from the instance name.
""",
    'EXAMPLES': """\
      To resume an instance from a managed instance group in the us-central1-a
      zone, run:

              $ {command} example-managed-instance-group --zone=us-central1-a \\
              --instances=example-instance
    """,
}
