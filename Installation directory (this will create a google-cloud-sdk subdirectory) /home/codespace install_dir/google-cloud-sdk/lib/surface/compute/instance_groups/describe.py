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
"""Command for describing instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags


class Describe(base.DescribeCommand):
  """Display detailed information about an instance group."""

  @staticmethod
  def Args(parser):
    flags.MULTISCOPE_INSTANCE_GROUP_ARG.AddArgument(
        parser, operation_type='describe')

  def Collection(self):
    return 'compute.instanceGroups'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    ref = flags.MULTISCOPE_INSTANCE_GROUP_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    if ref.Collection() == 'compute.instanceGroups':
      service = client.instanceGroups
      request_type = messages.ComputeInstanceGroupsGetRequest
    elif ref.Collection() == 'compute.regionInstanceGroups':
      service = client.regionInstanceGroups
      request_type = messages.ComputeRegionInstanceGroupsGetRequest

    return service.Get(request_type(**ref.AsDict()))


Describe.detailed_help = base_classes.GetMultiScopeDescriberHelp(
    'instance group', (base_classes.ScopeType.regional_scope,
                       base_classes.ScopeType.zonal_scope))
