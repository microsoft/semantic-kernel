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
"""Vertex AI endpoints list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.core import resources

_DEFAULT_FORMAT = """
        table(
            name.basename():label=ENDPOINT_ID,
            displayName
        )
    """


def _GetUri(endpoint):
  ref = resources.REGISTRY.ParseRelativeName(endpoint.name,
                                             constants.ENDPOINTS_COLLECTION)
  return ref.SelfLink()


def _AddArgs(parser):
  parser.display_info.AddFormat(_DEFAULT_FORMAT)
  parser.display_info.AddUriFunc(_GetUri)
  flags.AddRegionResourceArg(
      parser, 'to list endpoints', prompt_func=region_util.PromptForOpRegion)


def _Run(args, version):
  region_ref = args.CONCEPTS.region.Parse()
  args.region = region_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    return client.EndpointsClient(version=version).List(region_ref)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGa(base.ListCommand):
  """List existing Vertex AI endpoints.

  ## EXAMPLES

  To list the endpoints under project ``example'' in region ``us-central1'',
  run:

    $ {command} --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(ListGa):
  """List existing Vertex AI endpoints.

  ## EXAMPLES

  To list the endpoints under project ``example'' in region ``us-central1'',
  run:

    $ {command} --project=example --region=us-central1
  """

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
