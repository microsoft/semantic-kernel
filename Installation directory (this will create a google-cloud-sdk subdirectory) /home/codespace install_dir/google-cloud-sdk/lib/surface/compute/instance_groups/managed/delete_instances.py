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
"""Command for deleting instances managed by managed instance group."""

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
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as mig_flags


def _AddCommonDeleteInstancesArgs(parser):
  """Add parser configuration common for all release tracks."""
  parser.display_info.AddFormat(
      mig_flags.GetCommonPerInstanceCommandOutputFormat())
  parser.add_argument(
      '--instances',
      type=arg_parsers.ArgList(min_length=1),
      metavar='INSTANCE',
      required=True,
      help='Names of instances to delete.')
  instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
      parser)
  mig_flags.AddGracefulValidationArg(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class DeleteInstances(base.Command):
  """Delete instances managed by managed instance group."""

  @staticmethod
  def Args(parser):
    _AddCommonDeleteInstancesArgs(parser)

  def Run(self, args):
    self._UpdateDefaultOutputFormatForGracefulValidation(args)

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
      instances_holder_field = 'instanceGroupManagersDeleteInstancesRequest'
      request = self._CreateZonalIgmDeleteInstancesRequest(
          client.messages, igm_ref, args)
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      instances_holder_field = 'regionInstanceGroupManagersDeleteInstancesRequest'
      request = self._CreateRegionalIgmDeleteInstancesRequest(
          client.messages, igm_ref, args)
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    return instance_groups_utils.SendInstancesRequestsAndPostProcessOutputs(
        api_holder=holder,
        method_name='DeleteInstances',
        request_template=request,
        instances_holder_field=instances_holder_field,
        igm_ref=igm_ref,
        instances=args.instances,
        per_instance_status_enabled=True)

  def _CreateZonalIgmDeleteInstancesRequest(self, messages, igm_ref, args):
    request = messages.ComputeInstanceGroupManagersDeleteInstancesRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagersDeleteInstancesRequest=messages
        .InstanceGroupManagersDeleteInstancesRequest(instances=[]),
        project=igm_ref.project,
        zone=igm_ref.zone)
    if args.IsSpecified('skip_instances_on_validation_error'):
      (request.instanceGroupManagersDeleteInstancesRequest.
       skipInstancesOnValidationError) = args.skip_instances_on_validation_error
    return request

  def _CreateRegionalIgmDeleteInstancesRequest(self, messages, igm_ref, args):
    request = messages.ComputeRegionInstanceGroupManagersDeleteInstancesRequest(
        instanceGroupManager=igm_ref.Name(),
        regionInstanceGroupManagersDeleteInstancesRequest=messages
        .RegionInstanceGroupManagersDeleteInstancesRequest(instances=[]),
        project=igm_ref.project,
        region=igm_ref.region)
    if args.IsSpecified('skip_instances_on_validation_error'):
      (request.regionInstanceGroupManagersDeleteInstancesRequest.
       skipInstancesOnValidationError) = args.skip_instances_on_validation_error
    return request

  def _UpdateDefaultOutputFormatForGracefulValidation(self, args):
    # Do not override output format if specified by user.
    if args.IsSpecified('format'):
      return
    # Add VALIDATION_ERROR column if graceful validation is enabled.
    if args.skip_instances_on_validation_error:
      args.format = mig_flags.GetCommonPerInstanceCommandOutputFormat(
          with_validation_error=True)


DeleteInstances.detailed_help = {
    'brief':
        'Delete instances that are managed by a managed instance group.',
    'DESCRIPTION':
        """
        *{command}* is used to delete one or more instances from a managed
instance group. Once the instances are deleted, the size of the group is
automatically reduced to reflect the changes.

The command returns the operation status per instance, which might be ``FAIL'',
``SUCCESS'', ``SKIPPED'', or ``MEMBER_NOT_FOUND''. ``MEMBER_NOT_FOUND'' is
returned only for regional groups when the gcloud command-line tool wasn't able
to resolve the zone from the instance name. ``SKIPPED'' is returned only when
the `--skip-instances-on-validation-error` flag is used and the instance is not
a member of the group or is already being deleted or abandoned.

If you want to keep the underlying virtual machines but still remove them
from the managed instance group, use the abandon-instances command instead.
""",
}
