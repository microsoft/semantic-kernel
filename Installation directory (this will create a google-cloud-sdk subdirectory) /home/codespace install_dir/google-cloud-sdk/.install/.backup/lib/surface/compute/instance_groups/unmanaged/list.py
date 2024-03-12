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
"""Command for listing unmanaged instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List Compute Engine unmanaged instance groups."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table(
            name,
            zone.basename(),
            network.basename(),
            network.segment(-4):label=NETWORK_PROJECT,
            isManaged:label=MANAGED,
            size:label=INSTANCES
          )
    """)
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    lister.AddZonalListerArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseZonalFlags(args, holder.resources)

    list_implementation = lister.ZonalLister(
        client, client.apitools_client.instanceGroups)

    results = lister.Invoke(request_data, list_implementation)
    results = (resource for resource in results if 'zone' in resource)

    return instance_groups_utils.ComputeInstanceGroupManagerMembership(
        compute_holder=holder,
        items=results,
        filter_mode=instance_groups_utils.InstanceGroupFilteringMode.
        ONLY_UNMANAGED_GROUPS)


List.detailed_help = base_classes.GetZonalListerHelp('unmanaged '
                                                     'instance groups')
