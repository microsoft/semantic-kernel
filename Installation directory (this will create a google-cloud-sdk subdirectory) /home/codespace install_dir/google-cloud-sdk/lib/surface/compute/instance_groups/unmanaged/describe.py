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
"""instance-groups unmanaged describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags


class Describe(base.DescribeCommand):
  """Describe an instance group."""

  @staticmethod
  def Args(parser):
    Describe.ZonalInstanceGroupArg = flags.MakeZonalInstanceGroupArg()
    Describe.ZonalInstanceGroupArg.AddArgument(
        parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_group_ref = Describe.ZonalInstanceGroupArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeInstanceGroupsGetRequest(
        **instance_group_ref.AsDict())

    response = client.MakeRequests([(client.apitools_client.instanceGroups,
                                     'Get', request)])[0]

    return instance_groups_utils.ComputeInstanceGroupManagerMembership(
        compute_holder=holder,
        items=[encoding.MessageToDict(response)],
        filter_mode=instance_groups_utils.InstanceGroupFilteringMode.ALL_GROUPS
    )[0]

  detailed_help = {
      'brief': 'Describe an instance group',
      'DESCRIPTION': """\
          *{command}* displays detailed information about a Google Compute
          Engine instance group.
          """,
  }
