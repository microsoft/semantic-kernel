# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Command for creating managed instance group resize requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed.resize_requests import flags as rr_flags
from googlecloudsdk.core.util import times

DETAILED_HELP = {
    'brief': 'Create a Compute Engine managed instance group resize request.',
    'EXAMPLES': """

     To create a resize request for a managed instance group, run the following command:

       $ {command} my-mig --resize-request=resize-request-1 --resize-by=1 --requested-run-duration=3d1h30s
   """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a Compute Engine managed instance group resize request."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(parser)
    rr_flags.AddOutputFormat(parser, base.ReleaseTrack.BETA)

    parser.add_argument(
        '--resize-request',
        metavar='RESIZE_REQUEST_NAME',
        type=str,
        required=True,
        help="""The name of the resize request to create.""",
    )
    parser.add_argument(
        '--resize-by',
        type=int,
        required=True,
        help="""The number of VMs to resize managed instance group by.""",
    )
    parser.add_argument(
        '--requested-run-duration',
        type=arg_parsers.Duration(),
        required=True,
        help="""The time you need the requested VMs to run before being
        automatically deleted. The value must be formatted as the number of
        days, hours, minutes, or seconds followed by `d`, `h`, `m`, and `s`
        respectively. For example, specify `30m` for a duration of 30
        minutes or `1d2h3m4s` for 1 day, 2 hours, 3 minutes, and 4 seconds.
        The value must be between `10m` (10 minutes) and `7d` (7 days).""",
    )

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      List containing the created resize request.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(holder.client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister,
    )

    resize_request = client.messages.InstanceGroupManagerResizeRequest(
        name=args.resize_request,
        resizeBy=args.resize_by,
        requestedRunDuration=client.messages.Duration(
            seconds=args.requested_run_duration
        ),
    )

    request = (
        client.messages.ComputeInstanceGroupManagerResizeRequestsInsertRequest(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagerResizeRequest=resize_request,
            project=igm_ref.project,
            zone=igm_ref.zone,
        )
    )
    return client.MakeRequests([(
        client.apitools_client.instanceGroupManagerResizeRequests,
        'Insert',
        request,
    )])


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Create a Compute Engine managed instance group resize request."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(parser)
    rr_flags.AddOutputFormat(parser, base.ReleaseTrack.ALPHA)

    parser.add_argument(
        '--resize-request',
        metavar='RESIZE_REQUEST_NAME',
        type=str,
        required=True,
        help="""The name of the resize request to create.""",
    )

    count_resize_by_group = parser.add_group(mutex=True, required=True)
    count_resize_by_group.add_argument(
        '--count',
        type=int,
        hidden=True,
        help="""(ALPHA only) The number of VMs to create.""",
    )
    count_resize_by_group.add_argument(
        '--resize-by',
        type=int,
        help="""The number of VMs to resize managed instance group by.""",
    )

    valid_until_group = parser.add_group(
        mutex=True, required=False, hidden=True
    )
    valid_until_group.add_argument(
        '--valid-until-duration',
        type=arg_parsers.Duration(),
        help="""Relative deadline for waiting for capacity.""",
    )
    valid_until_group.add_argument(
        '--valid-until-time',
        type=arg_parsers.Datetime.Parse,
        help="""Absolute deadline for waiting for capacity in RFC3339 text format.""",
    )

    parser.add_argument(
        '--requested-run-duration',
        type=arg_parsers.Duration(),
        required=False,
        help="""The time you need the requested VMs to run before being
        automatically deleted. The value must be formatted as the number of
        days, hours, minutes, or seconds followed by `d`, `h`, `m`, and `s`
        respectively. For example, specify `30m` for a duration of 30
        minutes or `1d2h3m4s` for 1 day, 2 hours, 3 minutes, and 4 seconds.
        The value must be between `10m` (10 minutes) and `7d` (7 days).""",
    )

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      List containing the created resize request with its queuing policy.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(holder.client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister,
    )

    if args.IsKnownAndSpecified('valid_until_duration'):
      queuing_policy = client.messages.QueuingPolicy(
          validUntilDuration=client.messages.Duration(
              seconds=args.valid_until_duration
          )
      )
    elif args.IsKnownAndSpecified('valid_until_time'):
      queuing_policy = client.messages.QueuingPolicy(
          validUntilTime=times.FormatDateTime(args.valid_until_time)
      )
    else:
      queuing_policy = None

    requested_run_duration = None
    if args.IsKnownAndSpecified('requested_run_duration'):
      requested_run_duration = client.messages.Duration(
          seconds=args.requested_run_duration
      )

    if args.IsKnownAndSpecified('resize_by'):
      resize_request = client.messages.InstanceGroupManagerResizeRequest(
          name=args.resize_request,
          queuingPolicy=queuing_policy,
          requestedRunDuration=requested_run_duration,
          resizeBy=args.resize_by,
      )
    else:
      resize_request = client.messages.InstanceGroupManagerResizeRequest(
          name=args.resize_request,
          queuingPolicy=queuing_policy,
          requestedRunDuration=requested_run_duration,
          resizeBy=args.count,
      )

    request = (
        client.messages.ComputeInstanceGroupManagerResizeRequestsInsertRequest(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagerResizeRequest=resize_request,
            project=igm_ref.project,
            zone=igm_ref.zone,
        )
    )
    return client.MakeRequests([(
        client.apitools_client.instanceGroupManagerResizeRequests,
        'Insert',
        request,
    )])
