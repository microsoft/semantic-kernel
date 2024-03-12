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
"""Command to describe an event provider."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import providers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To describe the provider ``my-provider'', run:

          $ {command} my-provider
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an Eventarc event provider."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddProviderResourceArg(
        parser, 'The event provider to describe.', True)

  def Run(self, args):
    """Run the describe command."""
    client = providers.ProvidersClient(self.ReleaseTrack())
    provider_ref = args.CONCEPTS.provider.Parse()
    provider = client.Get(provider_ref)

    return provider
