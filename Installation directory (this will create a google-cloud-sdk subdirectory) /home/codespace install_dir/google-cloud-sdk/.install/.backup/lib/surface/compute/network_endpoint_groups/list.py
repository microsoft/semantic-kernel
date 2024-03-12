# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""List network endpoint groups command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """Lists Compute Engine network endpoint groups."""

  support_port_mapping_neg = False

  detailed_help = base_classes.GetMultiScopeListerHelp(
      'network endpoint groups',
      [
          base_classes.ScopeType.zonal_scope,
          base_classes.ScopeType.regional_scope,
          base_classes.ScopeType.global_scope,
      ],
  )

  @classmethod
  def Args(cls, parser):
    table = """\
        table(
            name,
            selfLink.scope().segment(-3).yesno(no="global"):label=LOCATION,
            networkEndpointType:label=ENDPOINT_TYPE,
            size"""
    if cls.support_port_mapping_neg:
      table += """,
          clientPortMappingMode:label=CLIENT_PORT_MAPPING_MODE
          """
    table += """\
                )
        """

    parser.display_info.AddFormat(table)
    lister.AddMultiScopeListerFlags(
        parser, zonal=True, regional=True, global_=True
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)
    list_implementation = lister.MultiScopeLister(
        client,
        zonal_service=client.apitools_client.networkEndpointGroups,
        regional_service=client.apitools_client.regionNetworkEndpointGroups,
        global_service=client.apitools_client.globalNetworkEndpointGroups,
        aggregation_service=client.apitools_client.networkEndpointGroups,
    )

    return lister.Invoke(request_data, list_implementation)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List a Google Compute Engine network endpoint group."""

  support_port_mapping_neg = True

