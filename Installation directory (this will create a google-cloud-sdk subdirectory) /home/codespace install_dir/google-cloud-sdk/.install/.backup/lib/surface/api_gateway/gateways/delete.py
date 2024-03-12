# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""`gcloud api-gateway gateways delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import gateways
from googlecloudsdk.api_lib.api_gateway import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.api_gateway import operations_util
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete an API Gateway."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To delete a gateway 'my-gateway' in 'us-central1', run:

          $ {command} my-gateway --location=us-central1
        """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddGatewayResourceArg(parser, 'deleted', positional=True)

  def Run(self, args):
    """Run 'api-gateway gateways delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      OperationCancelledError
    Returns:
      The response from the Delete API call.
    """

    gateway_ref = args.CONCEPTS.gateway.Parse()

    # Prompt with a warning before continuing.
    console_io.PromptContinue(
        message='Are you sure? This will delete the gateway \'{}\', '
        'along with all of the associated consumer '
        'information.'.format(gateway_ref.RelativeName()),
        prompt_string='Continue anyway',
        default=True,
        throw_if_unattended=True,
        cancel_on_no=True)

    resp = gateways.GatewayClient().Delete(gateway_ref)

    wait = 'Waiting for API Gateway [{}] to be deleted'.format(
        gateway_ref.Name())

    return operations_util.PrintOperationResult(
        resp.name, operations.OperationsClient(), wait_string=wait,
        is_async=args.async_)
