# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Vertex AI endpoints delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import endpoints_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.core.console import console_io


def _Run(args, version):
  """Delete an existing Vertex AI endpoint."""
  endpoint_ref = args.CONCEPTS.endpoint.Parse()
  args.region = endpoint_ref.AsDict()['locationsId']
  endpoint_id = endpoint_ref.AsDict()['endpointsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    endpoints_client = client.EndpointsClient(version=version)
    operation_client = operations.OperationsClient()
    console_io.PromptContinue(
        'This will delete endpoint [{}]...'.format(endpoint_id),
        cancel_on_no=True)
    op = endpoints_client.Delete(endpoint_ref)
    return operations_util.WaitForOpMaybe(
        operation_client, op, endpoints_util.ParseOperation(op.name))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeleteGa(base.DeleteCommand):
  """Delete an existing Vertex AI endpoint.

  ## EXAMPLES

  To delete an endpoint ``123'' under project ``example'' in region
  ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddEndpointResourceArg(
        parser, 'to delete', prompt_func=region_util.PromptForOpRegion)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DeleteBeta(DeleteGa):
  """Delete an existing Vertex AI endpoint.

  ## EXAMPLES

  To delete an endpoint ``123'' under project ``example'' in region
  ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
  """

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
