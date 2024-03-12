# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""List endpoint associations command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_endpoint_associations import association_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import association_flags
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION': """
          List firewall endpoint associations.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To list firewall endpoint associations, run:

            $ {command} --zone=us-central1-a --project=my-project

            To list firewall endpoint associations in all zones, run:

            $ {command} --project=my-project

            The project is automatically read from the core/project property if it is defined.
        """,
}

_FORMAT = """\
table(
    name.scope("firewallEndpointAssociations"):label=ID,
    name.scope("locations").segment(0):label=LOCATION,
    network.scope("networks"):label=NETWORK,
    firewallEndpoint.scope("firewallEndpoints"):label=ENDPOINT,
    state
)
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Firewall Plus endpoint associations."""

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(
        association_flags.MakeGetUriFunc(cls.ReleaseTrack())
    )
    association_flags.AddZoneArg(
        parser, required=False, help_text='Zone for the list operation'
    )

  def Run(self, args):
    client = association_api.Client(self.ReleaseTrack())

    project = args.project or properties.VALUES.core.project.GetOrFail()
    zone = args.zone or '-'
    parent = 'projects/{}/locations/{}'.format(project, zone)

    return client.ListAssociations(parent, args.limit, args.page_size)


List.detailed_help = DETAILED_HELP
