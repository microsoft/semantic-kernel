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
"""services api-keys get-key-string command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class GetKeyString(base.DescribeCommand):
  """Get the key string of an API key.

  Get the key string of an API key

  ## EXAMPLES


    To get the key string of API key `1234`, run:

     $ {command} 1234

    To get the key string of API key `1234` in project
    `myproject` using the fully qualified API key name, run:

     $ {command} projects/myproject/locations/global/keys/1234
  """

  @staticmethod
  def Args(parser):
    common_flags.key_flag(parser=parser, suffix='to retrieve key string')

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Key string.
    """

    client = apikeys.GetClientInstance()
    messages = client.MESSAGES_MODULE

    key_ref = args.CONCEPTS.key.Parse()
    request = messages.ApikeysProjectsLocationsKeysGetKeyStringRequest(
        name=key_ref.RelativeName())
    return client.projects_locations_keys.GetKeyString(request)
