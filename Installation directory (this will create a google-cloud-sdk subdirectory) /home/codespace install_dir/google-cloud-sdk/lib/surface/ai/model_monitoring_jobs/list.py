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
"""Vertex AI deployment monitoring jobs list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_monitoring_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util

DETAILED_HELP = {
    'EXAMPLES':
        """
    List the model deployment monitoring jobs of project `example` in region `us-central1`, run:

      $ {command} --project=example --region=us-central1
    """,
}


def _Run(args, version):
  """Run method for delete command."""
  region_ref = args.CONCEPTS.region.Parse()
  region = region_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    return client.ModelMonitoringJobsClient(version=version).List(
        region_ref=region_ref)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGa(base.ListCommand):
  """List the model deployment monitoring jobs of the given project and region."""

  @staticmethod
  def Args(parser):
    flags.AddRegionResourceArg(
        parser,
        'to list model deployment monitoring jobs',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_MODEL_MONITORING_JOBS_REGIONS))

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List the model deployment monitoring jobs of the given project and region."""

  @staticmethod
  def Args(parser):
    flags.AddRegionResourceArg(
        parser,
        'to list model deployment monitoring jobs',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_MODEL_MONITORING_JOBS_REGIONS))

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)


List.detailed_help = DETAILED_HELP
ListGa.detailed_help = DETAILED_HELP
