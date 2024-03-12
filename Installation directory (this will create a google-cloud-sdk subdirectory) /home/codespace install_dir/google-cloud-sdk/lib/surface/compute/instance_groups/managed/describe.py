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
"""Command for describing managed instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags


class Describe(base.DescribeCommand):
  """Display detailed information about a managed instance group."""

  @staticmethod
  def Args(parser):
    flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser, operation_type='describe')

  def Collection(self):
    return 'compute.instanceGroupManagers'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    apitools_client = client.apitools_client
    messages = client.messages
    resources = holder.resources

    ref = flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.ResolveAsResource(
        args, resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if ref.Collection() == 'compute.instanceGroupManagers':
      service = apitools_client.instanceGroupManagers
      request_type = messages.ComputeInstanceGroupManagersGetRequest
    elif ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = apitools_client.regionInstanceGroupManagers
      request_type = messages.ComputeRegionInstanceGroupManagersGetRequest
    else:
      raise ValueError('Unknown reference type {0}'.format(ref.Collection()))

    igm = encoding.MessageToDict(service.Get(request_type(**ref.AsDict())))
    annoted_igm = managed_instance_groups_utils.AddAutoscalersToMigs(
        migs_iterator=[igm],
        client=client,
        resources=resources,
        fail_when_api_not_supported=False)

    return list(annoted_igm)[0]


Describe.detailed_help = base_classes.GetMultiScopeDescriberHelp(
    'instance group', (base_classes.ScopeType.regional_scope,
                       base_classes.ScopeType.zonal_scope))
