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
"""Command for listing regions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers


class List(base.ListCommand):
  """List Compute Engine regions."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          quotas.metric.CPUS.quota():label=CPUS,
          quotas.metric.DISKS_TOTAL_GB.quota():label=DISKS_GB,
          quotas.metric.IN_USE_ADDRESSES.quota():label=ADDRESSES,
          quotas.metric.STATIC_ADDRESSES.quota():label=RESERVED_ADDRESSES,
          status():label=STATUS,
          deprecated.deleted:label=TURNDOWN_DATE
        )""")
    lister.AddBaseListerArgs(parser)
    parser.display_info.AddCacheUpdater(completers.RegionsCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseNamesAndRegexpFlags(args, holder.resources)

    list_implementation = lister.GlobalLister(
        client, client.apitools_client.regions)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetGlobalListerHelp('regions')
