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
"""List node types command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Compute Engine node types."""

  detailed_help = {
      'brief':
          'List Compute Engine node types.',
      'EXAMPLES':
          """
         To list node types, run:

           $ {command}
       """
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          zone.basename(),
          guestCpus:label=CPUs,
          memoryMb,
          deprecated.state:label=DEPRECATED
        )""")

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)
    list_implementation = lister.MultiScopeLister(
        client,
        aggregation_service=client.apitools_client.nodeTypes)

    return list(lister.Invoke(request_data, list_implementation))


List.detailed_help = base_classes.GetZonalListerHelp('node types')
