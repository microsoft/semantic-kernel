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
"""Command to create a channel connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import channel_connections
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """\
        To create a new channel connection ``my-channel-connection'' for channel ``my-channel'' with activation token ``channel-activation-token'', run:

          $ {command} my-channel-connection --channel=my-channel --activation-token=channel-activation-token
        """,
}

ACTIVATION_TOKEN_FLAG = base.Argument(
    '--activation-token',
    dest='activation_token',
    help="""Activation token for the specified channel.""",
    required=True)

CHANNEL_FLAG = base.Argument(
    '--channel',
    dest='channel',
    help="""Subscriber channel for which to create the channel connection. This argument should be the full channel name, including project, location and the channel id. """,
    required=True)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Eventarc channel connection."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddChannelConnectionResourceArg(parser,
                                          'Channel connection to create.')
    CHANNEL_FLAG.AddToParser(parser)
    ACTIVATION_TOKEN_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the create command."""
    client = channel_connections.ChannelConnectionClientV1()
    channel_connection_ref = args.CONCEPTS.channel_connection.Parse()

    project_name = channel_connection_ref.Parent().Parent().Name()
    location_name = channel_connection_ref.Parent().Name()
    log.debug('Creating channel {} for project {} in location {}'.format(
        channel_connection_ref.Name(), project_name, location_name))
    operation = client.Create(
        channel_connection_ref,
        client.BuildChannelConnection(
            channel_connection_ref,
            channel=args.channel,
            activation_token=args.activation_token))

    if args.async_:
      return operation
    return client.WaitFor(operation, 'Creating', channel_connection_ref)
