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
"""Command to cancel a hyperparameter tuning job in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.hp_tuning_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.hp_tuning_jobs import flags
from googlecloudsdk.command_lib.ai.hp_tuning_jobs import hp_tuning_jobs_util
from googlecloudsdk.core import log

_HPTUNING_JOB_CANCEL_DISPLAY_MESSAGE = """\
Request to cancel hyperparameter tuning job [{id}] has been sent.

You may view the status of your job with the command

  $ gcloud{command_version} ai hp-tuning-jobs describe {id} --region={region}
"""


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Cancel(base.SilentCommand):
  """Cancel a running hyperparameter tuning job.

  If the job is already finished, the command will not perform any operation.

  ## EXAMPLES

  To cancel a job ``123'' under project ``example'' in region
  ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddHptuningJobResourceArg(parser, 'to cancel')

  def Run(self, args):
    hptuning_job_ref = args.CONCEPTS.hptuning_job.Parse()
    region = hptuning_job_ref.AsDict()['locationsId']
    validation.ValidateRegion(
        region, available_regions=constants.SUPPORTED_TRAINING_REGIONS)

    version = constants.GA_VERSION if self.ReleaseTrack(
    ) == base.ReleaseTrack.GA else constants.BETA_VERSION
    with endpoint_util.AiplatformEndpointOverrides(
        version=version, region=region):
      response = client.HpTuningJobsClient(version=version).Cancel(
          hptuning_job_ref.RelativeName())

      log.status.Print(
          _HPTUNING_JOB_CANCEL_DISPLAY_MESSAGE.format(
              id=hptuning_job_ref.Name(),
              command_version=hp_tuning_jobs_util.OutputCommandVersion(
                  self.ReleaseTrack()),
              region=region))
      return response
