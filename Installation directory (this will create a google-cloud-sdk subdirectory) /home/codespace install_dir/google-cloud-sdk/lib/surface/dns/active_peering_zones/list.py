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
"""gcloud dns active-managed-zones list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """View the list of all active managed zones that target your network.

  ## EXAMPLES

  To see the full list of active managed zones, run:

    $ {command}

  To see the list of the first 10 active managed zones, run:

    $ {command} --limit=10

  """

  @staticmethod
  def Args(parser):
    flags.GetPeeringZoneListArg().AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    dns = util.GetApiClient('v1alpha2')
    messages = apis.GetMessagesModule('dns', 'v1alpha2')

    project_id = args.project if args.project is not None \
        else properties.VALUES.core.project.GetOrFail()
    network_url = args.target_network

    ids_response = dns.activePeeringZones.List(
        messages.DnsActivePeeringZonesListRequest(
            project=project_id, targetNetwork=network_url))

    zone_list = []
    for zone_id in ids_response.peeringZones:
      zone_list.append(
          dns.activePeeringZones.GetPeeringZoneInfo(
              messages.DnsActivePeeringZonesGetPeeringZoneInfoRequest(
                  project=project_id, peeringZoneId=zone_id.id)))
    return zone_list
