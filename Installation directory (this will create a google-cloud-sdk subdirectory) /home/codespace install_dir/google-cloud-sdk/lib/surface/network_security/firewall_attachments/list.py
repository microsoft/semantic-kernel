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
"""List attachment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_attachments import attachment_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import attachment_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          List firewall attachments.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To list firewall attachments in project my-proj, run:

            $ {command} --project=my-proj

        """,
}

_FORMAT = """\
table(
    name.scope("firewallAttachments"):label=ID,
    name.scope("locations").segment(0):label=LOCATION,
    state
)
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Firewall attachments."""

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(
        attachment_flags.MakeGetUriFunc(cls.ReleaseTrack())
    )
    attachment_flags.AddProjectArg(
        parser, help_text='The project for a list operation'
    )
    attachment_flags.AddZoneArg(
        parser, required=False, help_text='The zone for a list operation'
    )

  def Run(self, args):
    client = attachment_api.Client(self.ReleaseTrack())

    zone = args.zone if args.zone else '-'
    parent = 'projects/{}/locations/{}'.format(args.project, zone)

    return client.ListAttachments(parent, args.limit, args.page_size)


List.detailed_help = DETAILED_HELP
