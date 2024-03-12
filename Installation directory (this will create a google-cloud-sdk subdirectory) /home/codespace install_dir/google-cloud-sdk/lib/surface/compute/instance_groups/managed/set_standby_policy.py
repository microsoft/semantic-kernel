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
"""Command for setting instance template of managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import standby_policy_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetStandbyPolicyAlpha(base.Command):
  r"""Set the standby policy for a managed instance group.

    *{command}* sets the fields in the standby policy for a managed instance
  group. The standby policy dictates the behaviour of standby (stopped and
  suspended) instances
  """

  @staticmethod
  def Args(parser):
    standby_policy_utils.AddStandbyPolicyArgs(parser)
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
    initial_delay_sec = args.initial_delay or None
    standby_policy = managed_instance_groups_utils.CreateStandbyPolicy(
        client.messages, initial_delay_sec=initial_delay_sec
    )
    if not standby_policy:
      return

    return self._MakePatchRequest(client, igm_ref, standby_policy)

  def _MakePatchRequest(self, client, igm_ref, standby_policy):
    messages = client.messages

    igm_resource = messages.InstanceGroupManager(standbyPolicy=standby_policy)

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = client.apitools_client.instanceGroupManagers
      request_type = messages.ComputeInstanceGroupManagersPatchRequest
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = client.apitools_client.regionInstanceGroupManagers
      request_type = messages.ComputeRegionInstanceGroupManagersPatchRequest
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    request = request_type(**igm_ref.AsDict())
    request.instanceGroupManagerResource = igm_resource

    return client.MakeRequests([(service, 'Patch', request)])
