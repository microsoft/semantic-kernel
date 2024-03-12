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
"""Vertex AI endpoints predict command."""

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


def _AddArgs(parser):
  flags.AddEndpointResourceArg(
      parser,
      'to do online prediction',
      prompt_func=region_util.PromptForOpRegion)
  flags.AddPredictInstanceArg(parser)


def _Run(args, version):
  """Run Vertex AI online prediction."""
  endpoint_ref = args.CONCEPTS.endpoint.Parse()
  args.region = endpoint_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(
      version, region=args.region, is_prediction=True):
    endpoints_client = client.EndpointsClient(version=version)

    instances_json = endpoints_util.ReadInstancesFromArgs(args.json_request)
    if version == constants.GA_VERSION:
      results = endpoints_client.Predict(endpoint_ref, instances_json)
    else:
      results = endpoints_client.PredictBeta(endpoint_ref, instances_json)

    if not args.IsSpecified('format'):
      # default format is based on the response.
      args.format = endpoints_util.GetDefaultFormat(results.predictions)
    return results


@base.ReleaseTracks(base.ReleaseTrack.GA)
class PredictGa(base.Command):
  """Run Vertex AI online prediction.

     `{command}` sends a prediction request to Vertex AI endpoint for the
     given instances. This command will read up to 100 instances, though the
     service itself will accept instances up to the payload limit size
     (currently, 1.5MB).

  ## EXAMPLES

  To predict against an endpoint ``123'' under project ``example'' in region
  ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
    --json-request=input.json
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class PredictBeta(PredictGa):
  """Run Vertex AI online prediction.

     `{command}` sends a prediction request to Vertex AI endpoint for the
     given instances. This command will read up to 100 instances, though the
     service itself will accept instances up to the payload limit size
     (currently, 1.5MB).

  ## EXAMPLES

  To predict against an endpoint ``123'' under project ``example'' in region
  ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
    --json-request=input.json
  """

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
