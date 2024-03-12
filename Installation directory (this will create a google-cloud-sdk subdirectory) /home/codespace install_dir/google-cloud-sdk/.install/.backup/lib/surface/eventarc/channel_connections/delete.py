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
"""Command to delete the specified channel connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import channel_connections
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.core.console import console_io

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """\
        To delete the channel connection ``my-channel-connection'' in location ``us-central1'', run:

          $ {command} my-channel-connection --location=us-central1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete an Eventarc channel connection."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddChannelConnectionResourceArg(parser,
                                          'Channel connection to delete.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client = channel_connections.ChannelConnectionClientV1()
    channel_connection_ref = args.CONCEPTS.channel_connection.Parse()

    location_name = channel_connection_ref.Parent().Name()
    console_io.PromptContinue(
        message=('The following channel connection will be deleted.\n'
                 '[{name}] in location [{location}]'.format(
                     name=channel_connection_ref.Name(),
                     location=location_name)),
        throw_if_unattended=True,
        cancel_on_no=True)
    operation = client.Delete(channel_connection_ref)

    if args.async_:
      return operation
    return client.WaitFor(operation, 'Deleting', channel_connection_ref)
