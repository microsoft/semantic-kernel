# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""List Compute Engine reservations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List Compute Engine reservations."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(name,
              specificReservation.inUseCount,
              specificReservation.count,
              zone.basename(),
              shareSettings.shareType)
        """)
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    lister.AddZonalListerArgs(parser, hidden=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseZonalFlags(args, holder.resources)

    list_implementation = lister.ZonalLister(
        client, client.apitools_client.reservations)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = {
    'brief': 'List Compute Engine reservations.',
    'EXAMPLES': '''
      To list all Compute Engine reservations, run:

          $ {command}
    '''
}
