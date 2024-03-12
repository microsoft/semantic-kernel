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
"""Command to publish channels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import channel_connections
from googlecloudsdk.api_lib.eventarc import common_publishing
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To publish an event to your channel connection `my-channel-connection`
        with event id `1234`
        with event type `event-provider.event.v1.eventType`
        with event source `//event-provider/projects/project-id/resource-id`
        with event data `{ "key": "value" }`
        and  event attributes of `attribute1=value`, run:

          $ {command} my-channel-connection --event-id=1234 --event-type=event-provider.event.v1.eventType --event-source="//event-provider/event/source" --event-data='{"key": "value"}' --event-attributes=attribute1=value
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Publish(base.Command):
  """Publish to an Eventarc channel connection."""
  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddChannelConnectionResourceArg(parser,
                                          'Channel connection to publish to.')
    flags.AddEventPublishingArgs(parser)

  def Run(self, args):
    """Run the Publish command."""

    client = channel_connections.ChannelConnectionClientV1()
    channel_connection_ref = args.CONCEPTS.channel_connection.Parse()

    name = channel_connection_ref.Name()
    log.debug('Publishing event with id: {} to channel connection: {}'.format(
        args.event_id, name))

    client.Publish(
        channel_connection_ref,
        common_publishing.CreateCloudEvent(args.event_id, args.event_type,
                                           args.event_source, args.event_data,
                                           args.event_attributes))

    return log.out.Print('Event published successfully')
