 # -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to copy a model in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.models import client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import models_util
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import region_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CopyV1(base.CreateCommand):
  """Copy a model.

  ## EXAMPLES

  To copy a model `123` of project `example` from region `us-central1` to region
  `europe-west4`, run:

    $ {command} --source-model=projects/example/locations/us-central1/models/123
      --region=projects/example/locations/europe-west4
  """

  def __init__(self, *args, **kwargs):
    super(CopyV1, self).__init__(*args, **kwargs)
    client_instance = apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[constants.GA_VERSION])
    self.messages = client.ModelsClient(
        client=client_instance,
        messages=client_instance.MESSAGES_MODULE).messages

  @staticmethod
  def Args(parser):
    flags.AddCopyModelFlags(parser, region_util.PromptForOpRegion)

  def Run(self, args):
    destination_region_ref = args.CONCEPTS.region.Parse()
    destination_region = destination_region_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.GA_VERSION, region=destination_region):
      client_instance = apis.GetClientInstance(
          constants.AI_PLATFORM_API_NAME,
          constants.AI_PLATFORM_API_VERSION[constants.GA_VERSION])
      operation = client.ModelsClient(
          client=client_instance,
          messages=client_instance.MESSAGES_MODULE).CopyV1(
              destination_region_ref, args.source_model, args.kms_key_name,
              args.destination_model_id, args.destination_parent_model)
      return operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(
              client=client_instance, messages=client_instance.MESSAGES_MODULE),
          op=operation,
          op_ref=models_util.ParseModelOperation(operation.name))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CopyV1Beta1(CopyV1):
  """Copy a model.

  ## EXAMPLES

  To copy a model `123` of project `example` from region `us-central1` to region
  `europe-west4`, run:

    $ {command} --source-model=projects/example/locations/us-central1/models/123
      --region=projects/example/locations/europe-west4
  """

  def __init__(self, *args, **kwargs):
    super(CopyV1Beta1, self).__init__(*args, **kwargs)
    self.messages = client.ModelsClient().messages

  @staticmethod
  def Args(parser):
    flags.AddCopyModelFlags(parser, region_util.PromptForOpRegion)

  def Run(self, args):
    destination_region_ref = args.CONCEPTS.region.Parse()
    destination_region = destination_region_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.BETA_VERSION, region=destination_region):
      client_instance = apis.GetClientInstance(
          constants.AI_PLATFORM_API_NAME,
          constants.AI_PLATFORM_API_VERSION[constants.BETA_VERSION])
      operation = client.ModelsClient(
          client=client_instance,
          messages=client_instance.MESSAGES_MODULE).CopyV1Beta1(
              destination_region_ref, args.source_model, args.kms_key_name,
              args.destination_model_id, args.destination_parent_model)
      return operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(),
          op=operation,
          op_ref=models_util.ParseModelOperation(operation.name))
