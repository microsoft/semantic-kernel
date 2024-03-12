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
"""Command for describing target pools."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.target_pools import flags


class Describe(base.DescribeCommand):
  """Describe a Compute Engine target pool.

  *{command}* displays all data associated with a Compute Engine
  target pool in a project.
  """

  TARGET_POOL_ARG = None

  @staticmethod
  def Args(parser):
    Describe.TARGET_POOL_ARG = flags.TargetPoolArgument()
    Describe.TARGET_POOL_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_pool_ref = self.TARGET_POOL_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeTargetPoolsGetRequest(
        **target_pool_ref.AsDict())

    return client.MakeRequests([(client.apitools_client.targetPools,
                                 'Get', request)])[0]
