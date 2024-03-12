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
"""Command to create a channel."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import channels
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.core import log

# TODO(b/188207212): Update documentation when provider will be a resource
_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To create a new channel `my-channel` in location `us-central1`, run:

          $ {command} my-channel --location=us-central1

        To create a new channel `my-channel` in location `us-central1` with a Cloud KMS CryptoKey, run:

          $ {command} my-channel --location=us-central1 --crypto-key=projects/PROJECT_ID/locations/KMS_LOCATION/keyRings/KEYRING/cryptoKeys/KEY
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Eventarc channel."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddCreateChannelArg(parser)
    flags.AddCryptoKeyArg(parser, with_clear=False, hidden=False)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the create command."""
    client = channels.ChannelClientV1()
    channel_ref = args.CONCEPTS.channel.Parse()

    project_name = channel_ref.Parent().Parent().Name()
    location_name = channel_ref.Parent().Name()
    log.debug('Creating channel {} for project {} in location {}'.format(
        channel_ref.Name(), project_name, location_name))
    provider_ref = args.CONCEPTS.provider.Parse()
    operation = client.Create(
        channel_ref,
        client.BuildChannel(channel_ref, provider_ref, args.crypto_key))

    if args.async_:
      return operation
    return client.WaitFor(operation, 'Creating', channel_ref)
