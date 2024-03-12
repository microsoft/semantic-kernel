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
"""Command to list model versions in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.models import client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util


_DEFAULT_FORMAT = """
        table(
            name.basename():label=MODEL_ID,
            versionId,
            displayName
        )
    """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListVersionV1(base.ListCommand):
  """List the model versions of the given region and model.

  ## EXAMPLES

  List the model version of a model `123` of project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    """See base class."""
    parser.display_info.AddFormat(_DEFAULT_FORMAT)
    flags.AddModelResourceArg(parser, 'to list versions',
                              region_util.PromptForOpRegion)

  def _Run(self, args, model_ref, region):
    """Runs command with model client.

    Concrete gCloud SDK command subclasses are required to override this.

    Args:
      args: Command arguments.
      model_ref: The model resource reference.
      region: The region of the model resource reference.

    Returns:
      The response from running the given command with model client.
    """
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.GA_VERSION, region=region):
      client_instance = apis.GetClientInstance(
          constants.AI_PLATFORM_API_NAME,
          constants.AI_PLATFORM_API_VERSION[constants.GA_VERSION])
      return client.ModelsClient(
          client=client_instance,
          messages=client_instance.MESSAGES_MODULE).ListVersion(
              model_ref)

  def Run(self, args):
    model_ref = args.CONCEPTS.model.Parse()
    region = model_ref.AsDict()['locationsId']
    return self._Run(args, model_ref, region)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListVersionV1Beta1(ListVersionV1):
  """List the model versions of the given region and model.

  ## EXAMPLES

  List the model version of a model `123` of project `example` in region
  `us-central1`, run:

    $ {command} 123 --project=example --region=us-central1
  """

  def _Run(self, args, model_ref, region):
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.BETA_VERSION, region=region):
      return client.ModelsClient().ListVersion(model_ref)
