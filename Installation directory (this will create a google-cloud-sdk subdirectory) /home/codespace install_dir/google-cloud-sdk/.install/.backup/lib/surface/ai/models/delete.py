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
"""Vertex AI models delete command."""

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
class DeleteV1(base.DeleteCommand):
  """Delete an existing Vertex AI model.

  ## EXAMPLES

  To delete a model `123` under project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddModelResourceArg(parser, 'to delete',
                              region_util.PromptForOpRegion)

  def _Run(self, args, model_ref, region):
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.GA_VERSION, region=region):
      client_instance = apis.GetClientInstance(
          constants.AI_PLATFORM_API_NAME,
          constants.AI_PLATFORM_API_VERSION[constants.GA_VERSION])
      return client.ModelsClient(
          client=client_instance,
          messages=client_instance.MESSAGES_MODULE).Delete(model_ref)

  def Run(self, args):
    model_ref = args.CONCEPTS.model.Parse()
    region = model_ref.AsDict()['locationsId']
    return self._Run(args, model_ref, region)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeleteV1Beta1(DeleteV1):
  """Delete an existing Vertex AI model.

  ## EXAMPLES

  To delete a model `123` under project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  def _Run(self, args, model_ref, region):
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.BETA_VERSION, region=region):
      operation = client.ModelsClient().Delete(model_ref)
      return operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(),
          op=operation,
          op_ref=models_util.ParseModelOperation(operation.name))
