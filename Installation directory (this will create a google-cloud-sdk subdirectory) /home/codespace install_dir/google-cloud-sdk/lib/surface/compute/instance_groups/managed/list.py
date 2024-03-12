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
"""Command for listing managed instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Compute Engine managed instance groups."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_CREATE_OR_LIST_FORMAT)
    lister.AddMultiScopeListerFlags(parser, zonal=True, regional=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        zonal_service=client.apitools_client.instanceGroupManagers,
        regional_service=client.apitools_client.regionInstanceGroupManagers,
        aggregation_service=client.apitools_client.instanceGroupManagers)

    migs = lister.Invoke(request_data, list_implementation)

    (self._had_errors,
     results) = managed_instance_groups_utils.AddAutoscaledPropertyToMigs(
         list(migs), client, holder.resources)

    return results

  def Epilog(self, unused_resources_were_displayed):
    if self._had_errors:
      log.err.Print('(*) - there are errors in your autoscaling setup, please '
                    'describe the resource to see details')


List.detailed_help = base_classes.GetMultiScopeListerHelp(
    'managed instance groups',
    [base_classes.ScopeType.regional_scope, base_classes.ScopeType.zonal_scope])
