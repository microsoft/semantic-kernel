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
"""services api-keys lookup command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.calliope import base


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Lookup(base.Command):
  """Look up resource name of a key string.

  Look up resource name of a key string.

  ## EXAMPLES

   Look up resource name of a key string named my-key-string:

    $ {command} my-key-string
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('key_string', help='Key string of the key')

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Resource name and its parent name.
    """

    client = apikeys.GetClientInstance()
    messages = client.MESSAGES_MODULE

    request = messages.ApikeysKeysLookupKeyRequest(keyString=args.key_string)
    return client.keys.LookupKey(request)
