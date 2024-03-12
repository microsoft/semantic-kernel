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
"""Command to delete an Azure Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import azure as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags

_EXAMPLES = """
To delete an Azure client named ``my-client'' in location ``us-west1'', run:

$ {command} my-client --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete an Azure client."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClientResourceArg(parser, 'to delete')

    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddAllowMissing(parser)

  def Run(self, args):
    """Runs the delete command."""
    location = resource_args.ParseAzureClientResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      client_ref = resource_args.ParseAzureClientResourceArg(args)
      api_client = api_util.ClientsClient()
      message = command_util.ClientMessage(
          client_ref.azureClientsId, region=location
      )
      return command_util.Delete(
          resource_ref=client_ref,
          resource_client=api_client,
          message=message,
          args=args,
          kind=constants.AZURE_CLIENT_KIND,
      )
