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
"""Command to list models in Vertex AI."""

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
            displayName
        )
    """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListV1(base.ListCommand):
  """List the models of the given project and region.

  ## EXAMPLES

  List the models of project ``example'' in region ``us-central1'', run:

    $ {command} --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_DEFAULT_FORMAT)
    flags.AddRegionResourceArg(
        parser, 'to list models', prompt_func=region_util.PromptForOpRegion)

  def _Run(self, args, region_ref, region):
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.GA_VERSION, region=region):
      client_instance = apis.GetClientInstance(
          constants.AI_PLATFORM_API_NAME,
          constants.AI_PLATFORM_API_VERSION[constants.GA_VERSION])
      return client.ModelsClient(
          client=client_instance,
          messages=client_instance.MESSAGES_MODULE).List(region_ref=region_ref)

  def Run(self, args):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    return self._Run(args, region_ref, region)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListV1Beta1(ListV1):
  """List the models of the given project and region.

  ## EXAMPLES

  List the models of project `example` in region `us-central1`, run:

    $ {command} --project=example --region=us-central1
  """

  def _Run(self, args, region_ref, region):
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.BETA_VERSION, region=region):
      return client.ModelsClient().List(region_ref=region_ref)
