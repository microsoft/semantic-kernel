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
"""services api-keys delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log

OP_BASE_CMD = 'gcloud services operations '
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Delete(base.DeleteCommand):
  """Delete an API key.

  Delete an API key.

  ## EXAMPLES

   Delete an API Key :

   $ {command} projects/myproject/locations/global/keys/1234

   $ {command} 1234
  """

  @staticmethod
  def Args(parser):

    common_flags.key_flag(parser=parser, suffix='to delete')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The response from the Delete API call.
    """

    client = apikeys.GetClientInstance()
    messages = client.MESSAGES_MODULE

    key_ref = args.CONCEPTS.key.Parse()
    request = messages.ApikeysProjectsLocationsKeysDeleteRequest(
        name=key_ref.RelativeName())
    op = client.projects_locations_keys.Delete(request)

    if not op.done:
      if args.async_:
        cmd = OP_WAIT_CMD.format(op.name)
        log.status.Print('Asynchronous operation is in progress... '
                         'Use the following command to wait for its '
                         'completion:\n {0}'.format(cmd))
        return op
      op = services_util.WaitOperation(op.name, apikeys.GetOperation)
    services_util.PrintOperationWithResponse(op)
    return op
