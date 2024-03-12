# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to list all channels in a project and location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import channels
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags

_DETAILED_HELP = {
    "DESCRIPTION":
        "{description}",
    "EXAMPLES":
        """ \
        To list all channels in location `us-central1`, run:

          $ {command} --location=us-central1

        To list all channels in all locations, run:

          $ {command} --location=-

        or

          $ {command}
        """,
}

_FORMAT = """ \
table(
    name.scope("channels"):label=NAME,
    provider:label=PROVIDER,
    state:label=STATE,
    pubsubTopic.scope("topics"):label=PUBSUB_TOPIC
)
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Eventarc channels."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddLocationResourceArg(
        parser,
        "Location for which to list channels. This should be one of the supported regions.",
        required=False)
    flags.AddProjectResourceArg(parser)
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(channels.GetChannelURI)

  def Run(self, args):
    client = channels.ChannelClientV1()
    args.CONCEPTS.project.Parse()
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(location_ref, args.limit, args.page_size)
