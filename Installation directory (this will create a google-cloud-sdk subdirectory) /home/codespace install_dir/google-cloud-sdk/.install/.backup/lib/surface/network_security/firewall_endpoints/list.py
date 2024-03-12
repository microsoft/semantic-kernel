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
"""List endpoints command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import activation_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          List firewall endpoints.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To list firewall endpoints in organization ID 1234, run:

            $ {command} --organization=1234

        """,
}

_FORMAT = """\
table(
    name.scope("firewallEndpoints"):label=ID,
    name.scope("locations").segment(0):label=LOCATION,
    state
)
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Firewall Plus endpoints."""

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(
        activation_flags.MakeGetUriFunc(cls.ReleaseTrack())
    )
    activation_flags.AddOrganizationArg(
        parser, help_text='The organization for a list operation'
    )
    # TODO(b/274296391): Change to required=False once it's supported.
    activation_flags.AddZoneArg(
        parser, required=True, help_text='The zone for a list operation'
    )

  def Run(self, args):
    client = activation_api.Client(self.ReleaseTrack())

    zone = args.zone if args.zone else '-'
    parent = 'organizations/{}/locations/{}'.format(args.organization, zone)

    return client.ListEndpoints(parent, args.limit, args.page_size)


List.detailed_help = DETAILED_HELP
