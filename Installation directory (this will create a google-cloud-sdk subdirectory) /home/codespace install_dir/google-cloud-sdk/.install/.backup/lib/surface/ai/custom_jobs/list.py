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
"""Command to list custom jobs in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.custom_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai.custom_jobs import custom_jobs_util
from googlecloudsdk.command_lib.ai.custom_jobs import validation


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGA(base.ListCommand):
  """Lists the existing custom jobs.

  ## EXAMPLES

  To list the jobs of project ``example'' in region
  ``us-central1'', run:

    $ {command} --project=example --region=us-central1
  """
  _api_version = constants.GA_VERSION

  @classmethod
  def Args(cls, parser):
    """Method called by Calliope to set up arguments for this command.

    Args:
      parser: A argparse.Parser to register accepted arguments in command input.
    """
    flags.AddRegionResourceArg(
        parser,
        'to list custom jobs',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_TRAINING_REGIONS))
    flags.AddUriFlags(
        parser,
        collection=custom_jobs_util.CUSTOM_JOB_COLLECTION,
        api_version=constants.AI_PLATFORM_API_VERSION[cls._api_version])

  def Run(self, args):
    """Executes the list command.

    Args:
      args: an argparse.Namespace, it contains all arguments that this command
        was invoked with.

    Returns:
      The list of resources
    """
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    validation.ValidateRegion(region)

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._api_version, region=region):
      return client.CustomJobsClient(version=self._api_version).List(
          region=region_ref.RelativeName())


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListPreGA(ListGA):
  """Lists the existing custom jobs.

  ## EXAMPLES

  To list the jobs of project ``example'' in region
  ``us-central1'', run:

    $ {command} --project=example --region=us-central1
  """

  _api_version = constants.BETA_VERSION
