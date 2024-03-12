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
"""Vertex AI endpoints explain command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import endpoints_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.core import log


def _Run(args, version):
  """Run Vertex AI online explanation."""
  endpoint_ref = args.CONCEPTS.endpoint.Parse()
  args.region = endpoint_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(
      version, region=args.region, is_prediction=True):
    endpoints_client = client.EndpointsClient(version=version)

    instances_json = endpoints_util.ReadInstancesFromArgs(args.json_request)
    if version == constants.GA_VERSION:
      results = endpoints_client.Explain(endpoint_ref, instances_json, args)
    else:
      results = endpoints_client.ExplainBeta(endpoint_ref, instances_json, args)

    if getattr(results, 'deployedModelId') is not None:
      log.status.Print(
          'Deployed model id to be used for explanation: {}'.format(
              results.deployedModelId))
    if not args.IsSpecified('format'):
      # default format is based on the response.
      args.format = endpoints_util.GetDefaultFormat(
          results, key_name='explanations')
    return results


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ExplainGa(base.Command):
  """Request an online explanation from an Vertex AI endpoint.

     `{command}` sends an explanation request to the Vertex AI endpoint for
     the given instances. This command reads up to 100 instances, though the
     service itself accepts instances up to the payload limit size
     (currently, 1.5MB).

     ## EXAMPLES

     To send an explanation request to the endpoint for the json file,
     input.json, run:

     $ {command} ENDPOINT_ID --region=us-central1 --json-request=input.json
  """

  @staticmethod
  def Args(parser):
    flags.AddEndpointResourceArg(
        parser,
        'to request an online explanation',
        prompt_func=region_util.PromptForOpRegion)
    flags.AddPredictInstanceArg(parser)
    flags.GetDeployedModelId(required=False).AddToParser(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ExplainBeta(ExplainGa):
  """Request an online explanation from an Vertex AI endpoint.

     `{command}` sends an explanation request to the Vertex AI endpoint for
     the given instances. This command reads up to 100 instances, though the
     service itself accepts instances up to the payload limit size
     (currently, 1.5MB).

     ## EXAMPLES

     To send an explanation request to the endpoint for the json file,
     input.json, run:

     $ {command} ENDPOINT_ID --region=us-central1 --json-request=input.json
  """

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
