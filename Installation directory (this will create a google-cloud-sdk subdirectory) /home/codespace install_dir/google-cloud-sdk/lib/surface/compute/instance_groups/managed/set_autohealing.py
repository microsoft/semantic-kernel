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
"""Command for setting autohealing policy of managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import auto_healing_utils


@base.Deprecate(
    is_removed=False,
    warning=('This command is deprecated and will not be promoted to GA. '
             'Please use `gcloud beta instance-groups managed update` instead.')
)
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class SetAutohealing(base.Command):
  """Set autohealing policy for managed instance group.

    *{command}* updates the autohealing policy for an existing managed
  instance group.

  If health check is specified, the resulting autohealing policy will be
  triggered by the health-check signal i.e. the autohealing action (RECREATE) on
  an instance will be performed if the health-check signals that the instance is
  UNHEALTHY. If no health check is specified, the resulting autohealing policy
  will be triggered by instance's status i.e. the autohealing action (RECREATE)
  on an instance will be performed if the instance.status is not RUNNING.
  """

  @classmethod
  def Args(cls, parser):
    auto_healing_utils.AddAutohealingArgs(parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    health_check = managed_instance_groups_utils.GetHealthCheckUri(
        holder.resources, args)
    auto_healing_policies = (
        managed_instance_groups_utils.CreateAutohealingPolicies(
            client.messages, health_check, args.initial_delay))

    managed_instance_groups_utils.ValidateAutohealingPolicies(
        auto_healing_policies)

    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister)
    igm_resource = messages.InstanceGroupManager(
        autoHealingPolicies=auto_healing_policies)

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
