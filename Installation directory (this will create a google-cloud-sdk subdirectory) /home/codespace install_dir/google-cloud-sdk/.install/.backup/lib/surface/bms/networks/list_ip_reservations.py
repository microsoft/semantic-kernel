# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""'Bare Metal Solution networks list-ip-reservations command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.command_lib.bms import util

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List IP range reservations for Bare Metal Solution networks
          in a project.
        """,
    'EXAMPLES':
        """
          To list IP range reservations for networks in the region
          `us-central1`, run:

            $ {command} --region=us-central1

          Or:

          To list all IP range reservations in the project, run:

            $ {command}
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List IP range reservations for Bare Metal Solution networks in a project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Remove unsupported default List flags.
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

    flags.AddRegionArgToParser(parser)
    # The default format picks out the components of the relative name: given
    # projects/myproject/locations/us-central1/networks/my-test
    # it takes -1 (my-test), -3 (us-central1), and -5 (myproject).
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NETWORK_NAME,id:label=NETWORK_ID,'
        'name.segment(-3):label=REGION,start_address:label=RESERVATION_'
        'START_ADDRESS,end_address:label=RESERVATION_END_ADDRESS,note:'
        'label=RESERVATION_NOTE)')

  def Run(self, args):
    region = util.FixParentPathWithGlobalRegion(args.CONCEPTS.region.Parse())
    client = BmsClient()
    networks_gen = client.ListNetworks(region, limit=args.limit)

    for network in networks_gen:
      for reservation in _ExtractReservations(network):
        yield reservation


def _ExtractReservations(network):
  """Extracts reservations from network object."""
  out = []
  for res in network.reservations:
    reservation_dict = {}
    reservation_dict['name'] = network.name
    reservation_dict['id'] = network.id
    reservation_dict['start_address'] = res.startAddress
    reservation_dict['end_address'] = res.endAddress
    reservation_dict['note'] = res.note
    out.append(reservation_dict)
  return out


List.detailed_help = DETAILED_HELP
