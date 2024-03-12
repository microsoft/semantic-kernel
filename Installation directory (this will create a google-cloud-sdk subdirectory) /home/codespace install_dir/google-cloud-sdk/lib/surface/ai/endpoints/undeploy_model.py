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
"""Vertex AI endpoints undeploy-model command."""

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


def _AddArgs(parser):
  flags.AddEndpointResourceArg(
      parser,
      'to undeploy a model from',
      prompt_func=region_util.PromptForOpRegion)
  flags.GetDeployedModelId().AddToParser(parser)
  flags.GetTrafficSplitArg().AddToParser(parser)


def _Run(args, version):
  """Undeploy a model fro man existing Vertex AI endpoint."""
  endpoint_ref = args.CONCEPTS.endpoint.Parse()
  args.region = endpoint_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    endpoints_client = client.EndpointsClient(version=version)
    operation_client = operations.OperationsClient()
    if version == constants.GA_VERSION:
      op = endpoints_client.UndeployModel(
          endpoint_ref,
          args.deployed_model_id,
          traffic_split=args.traffic_split)
    else:
      op = endpoints_client.UndeployModelBeta(
          endpoint_ref,
          args.deployed_model_id,
          traffic_split=args.traffic_split)
    return operations_util.WaitForOpMaybe(
        operation_client, op, endpoints_util.ParseOperation(op.name))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UndeployModelGa(base.Command):
  """Undeploy a model from an existing Vertex AI endpoint.

  ## EXAMPLES

  To undeploy a model ``456'' from an endpoint ``123'' under project ``example''
  in region ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
    --deployed-model-id=456
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UndeployModelBeta(UndeployModelGa):
  """Undeploy a model from an existing Vertex AI endpoint.

  ## EXAMPLES

  To undeploy a model ``456'' from an endpoint ``123'' under project ``example''
  in region ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
    --deployed-model-id=456
  """

  def Run(self, args):
    _Run(args, constants.BETA_VERSION)
