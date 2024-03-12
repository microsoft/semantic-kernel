# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""services api-keys describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags

DETAILED_HELP = {
    'DESCRIPTION':
        """Describe an API key's metadata.""",
    'EXAMPLES':
        """\
        To describe an API key using Key:

          $ {command} 1234
                OR
          $ {command} projects/myproject/locations/global/keys/1234

        To describe an API key with key and project:

          $ {command} 1234 --project=myproject

        To describe an API key with key, project, and location:

            $ {command} 1234 --project=myproject --location=global
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class DescribeGa(base.DescribeCommand):
  """Describe an API key's metadata."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    common_flags.key_flag(parser=parser, suffix='to describe', api_version='v2')

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The metadata of API key.
    """

    client = apikeys.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    key_ref = args.CONCEPTS.key.Parse()
    request = messages.ApikeysProjectsLocationsKeysGetRequest(
        name=key_ref.RelativeName())
    return client.projects_locations_keys.Get(request)
