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
"""Command to list hyperparameter tuning jobs in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.hp_tuning_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.hp_tuning_jobs import hp_tuning_jobs_util

_DETAILED_HELP = {
    'EXAMPLES':
        """ \
        To list the jobs of project ``example'' in region
        ``us-central1'', run:

          $ {command} --project=example --region=us-central1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGA(base.ListCommand):
  """List existing hyperparameter tuning jobs."""
  detailed_help = _DETAILED_HELP
  _version = constants.GA_VERSION

  @classmethod
  def Args(cls, parser):
    """Method called by Calliope to set up arguments for this command.

    Args:
      parser: A argparse.Parser to register accepted arguments in command input.
    """
    flags.AddRegionResourceArg(
        parser,
        'to list hyperparameter tuning jobs',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_TRAINING_REGIONS))
    flags.AddUriFlags(parser, hp_tuning_jobs_util.HPTUNING_JOB_COLLECTION,
                      constants.AI_PLATFORM_API_VERSION[cls._version])

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
    validation.ValidateRegion(
        region, available_regions=constants.SUPPORTED_TRAINING_REGIONS)

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._version, region=region):
      return client.HpTuningJobsClient(version=self._version).List(
          region=region_ref.RelativeName())


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListPreGA(ListGA):
  """List existing hyperparameter tuning jobs."""
  _version = constants.BETA_VERSION
