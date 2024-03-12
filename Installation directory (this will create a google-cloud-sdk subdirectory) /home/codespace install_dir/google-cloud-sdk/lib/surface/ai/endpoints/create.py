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
"""Vertex AI endpoints create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import endpoints_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _AddArgs(parser):
  flags.GetDisplayNameArg('endpoint').AddToParser(parser)
  flags.AddRegionResourceArg(
      parser, 'to create endpoint', prompt_func=region_util.PromptForOpRegion)
  flags.GetDescriptionArg('endpoint').AddToParser(parser)
  flags.GetUserSpecifiedIdArg('endpoint').AddToParser(parser)
  labels_util.AddCreateLabelsFlags(parser)
  flags.GetEndpointNetworkArg().AddToParser(parser)
  flags.GetEncryptionKmsKeyNameArg().AddToParser(parser)
  flags.AddRequestResponseLoggingConfigGroupArgs(parser)


def _Run(args, version):
  """Create a new Vertex AI endpoint."""
  validation.ValidateDisplayName(args.display_name)

  region_ref = args.CONCEPTS.region.Parse()
  args.region = region_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    endpoints_client = client.EndpointsClient(version=version)
    operation_client = operations.OperationsClient()
    if version == constants.GA_VERSION:
      op = endpoints_client.Create(
          region_ref, args.display_name,
          labels_util.ParseCreateArgs(
              args, endpoints_client.messages.GoogleCloudAiplatformV1Endpoint
              .LabelsValue),
          description=args.description,
          network=args.network,
          endpoint_id=args.endpoint_id,
          encryption_kms_key_name=args.encryption_kms_key_name,
          request_response_logging_table=args.request_response_logging_table,
          request_response_logging_rate=args.request_response_logging_rate)
    else:
      op = endpoints_client.CreateBeta(
          region_ref, args.display_name,
          labels_util.ParseCreateArgs(
              args,
              endpoints_client.messages.GoogleCloudAiplatformV1beta1Endpoint
              .LabelsValue),
          description=args.description,
          network=args.network,
          endpoint_id=args.endpoint_id,
          encryption_kms_key_name=args.encryption_kms_key_name,
          request_response_logging_table=args.request_response_logging_table,
          request_response_logging_rate=args.request_response_logging_rate)
    response_msg = operations_util.WaitForOpMaybe(
        operation_client, op, endpoints_util.ParseOperation(op.name))
    if response_msg is not None:
      response = encoding.MessageToPyValue(response_msg)
      if 'name' in response:
        log.status.Print(
            ('Created Vertex AI endpoint: {}.').format(response['name']))
    return response_msg


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGa(base.CreateCommand):
  """Create a new Vertex AI endpoint.

  ## EXAMPLES

  To create an endpoint under project ``example'' in region ``us-central1'',
  run:

    $ {command} --project=example --region=us-central1
    --display-name=my_endpoint
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(CreateGa):
  """Create a new Vertex AI endpoint.

  ## EXAMPLES

  To create an endpoint under project ``example'' in region ``us-central1'',
  run:

    $ {command} --project=example --region=us-central1
    --display-name=my_endpoint
  """

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
