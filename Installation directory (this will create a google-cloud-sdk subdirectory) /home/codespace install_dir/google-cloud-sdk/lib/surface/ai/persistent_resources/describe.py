# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to get a Persistent Resource in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.persistent_resources import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai.persistent_resources import flags
from googlecloudsdk.command_lib.ai.persistent_resources import validation


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribePreGA(base.DescribeCommand):
  """Get detailed information about a PersistentResource with a given id.

  ## EXAMPLES

  To get the persistent resource with the PersistentResource id ``123'' under
  project ``example'' in region ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
  """

  _api_version = constants.BETA_VERSION

  @staticmethod
  def Args(parser):
    flags.AddPersistentResourceResourceArg(parser, 'to describe')

  def Run(self, args):
    persistent_resource_ref = args.CONCEPTS.persistent_resource.Parse()
    region = persistent_resource_ref.AsDict()['locationsId']
    validation.ValidateRegion(region)

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._api_version, region=region
    ):
      response = client.PersistentResourcesClient(
          version=self._api_version
      ).Get(persistent_resource_ref.RelativeName())
      return response
