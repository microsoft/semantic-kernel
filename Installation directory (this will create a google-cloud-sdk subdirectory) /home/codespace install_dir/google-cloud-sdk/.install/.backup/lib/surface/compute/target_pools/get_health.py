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

"""Command for getting a target pool's health."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.target_pools import flags


class GetHealth(base.DescribeCommand):
  """Get the health of instances in a target pool.

  *{command}* displays the health of instances in a target pool.
  """

  TARGET_POOL_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.TARGET_POOL_ARG = flags.TargetPoolArgument()
    cls.TARGET_POOL_ARG.AddArgument(
        parser, operation_type='get health information for')

  def GetTargetPool(self, client, target_pool_ref):
    """Fetches the target pool resource."""
    objects = client.MakeRequests(
        [(client.apitools_client.targetPools, 'Get',
          client.messages.ComputeTargetPoolsGetRequest(
              project=target_pool_ref.project,
              region=target_pool_ref.region,
              targetPool=target_pool_ref.Name()))])
    return objects[0]

  def Run(self, args):
    """Returns a list of TargetPoolInstanceHealth objects."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_pool_ref = self.TARGET_POOL_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    target_pool = self.GetTargetPool(client, target_pool_ref)
    instances = target_pool.instances

    # If the target pool has no instances, we should return an empty
    # list.
    if not instances:
      return

    requests = []
    for instance in instances:
      request_message = client.messages.ComputeTargetPoolsGetHealthRequest(
          instanceReference=client.messages.InstanceReference(
              instance=instance),
          project=target_pool_ref.project,
          region=target_pool_ref.region,
          targetPool=target_pool_ref.Name())
      requests.append((client.apitools_client.targetPools, 'GetHealth',
                       request_message))

    errors = []
    resources = client.MakeRequests(
        requests=requests,
        errors_to_collect=errors)

    for resource in resources:
      yield resource

    if errors:
      utils.RaiseToolException(
          errors,
          error_message='Could not get health for some targets:')
