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
"""List resource policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List Compute Engine resource policies."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          description,
          region,
          creationTimestamp
        )""")
    # TODO(b/69426858): Remove these deprecated flags.
    lister.AddRegionsArg(parser, hidden=True)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseRegionalFlags(args, holder.resources)

    list_implementation = lister.RegionalLister(
        client, client.apitools_client.resourcePolicies)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetRegionalListerHelp('resource policies')
