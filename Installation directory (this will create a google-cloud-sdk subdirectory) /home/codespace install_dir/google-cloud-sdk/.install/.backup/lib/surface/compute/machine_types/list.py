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
"""Command for listing machine types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers


class List(base.ListCommand):
  """List Compute Engine machine types.

  """

  @staticmethod
  def Args(parser):
    List.detailed_help['DESCRIPTION'] += """
*OBSOLETE* machine types are filtered out by default. Add *--verbosity=info*
to display the default filter expression. Use *--filter=""* to list all images,
or specify your own *--filter* to override the default.
"""
    parser.display_info.AddFilter('deprecated.state!=OBSOLETE')
    parser.display_info.AddFormat("""\
    table(
      name,
      zone.basename(),
      guestCpus:label=CPUS,
      memoryMb.size(units_in=MiB, units_out=GiB, precision=2):label=MEMORY_GB,
      deprecated.state:label=DEPRECATED
    )
""")
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    parser.display_info.AddCacheUpdater(completers.MachineTypesCompleter)
    lister.AddZonalListerArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseZonalFlags(args, holder.resources)

    list_implementation = lister.ZonalLister(
        client, client.apitools_client.machineTypes)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetZonalListerHelp('machine types')
