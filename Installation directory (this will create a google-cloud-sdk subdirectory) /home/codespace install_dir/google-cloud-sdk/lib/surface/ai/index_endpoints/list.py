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
"""Vertex AI index endpoints list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.index_endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListV1(base.ListCommand):
  """Lists the index endpoints of the given project and region.

  ## EXAMPLES

  Lists the index endpoints of project `example` in region `us-central1`, run:

    $ {command} --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddRegionResourceArg(
        parser,
        'to list index endpoints',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_OP_REGIONS
        ),
    )

  def _Run(self, args, version):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      return client.IndexEndpointsClient(version=version).List(
          region_ref=region_ref)

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListV1Beta1(ListV1):
  """Lists the index endpoints of the given project and region.

  ## EXAMPLES

  Lists the index endpoints of project `example` in region `us-central1`, run:

    $ {command} --project=example --region=us-central1
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
