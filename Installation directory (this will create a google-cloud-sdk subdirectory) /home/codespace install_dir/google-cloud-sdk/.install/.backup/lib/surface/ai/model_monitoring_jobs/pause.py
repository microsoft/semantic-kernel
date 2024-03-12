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
"""Vertex AI deployment monitoring jobs pause command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_monitoring_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'EXAMPLES':
        """
    To pause a model deployment monitoring job `123` of project `example` in region `us-central1`, run:

      $ {command} 123 --project=example --region=us-central1
    """,
}


def _Run(args, version, release_prefix):
  """Run method for pause command."""
  model_monitoring_job_ref = args.CONCEPTS.monitoring_job.Parse()
  region = model_monitoring_job_ref.AsDict()['locationsId']
  model_monitoring_job_id = model_monitoring_job_ref.AsDict(
  )['modelDeploymentMonitoringJobsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    console_io.PromptContinue(
        'This will pause model deployment monitoring job [{}]...'.format(
            model_monitoring_job_id),
        cancel_on_no=True)
    response = client.ModelMonitoringJobsClient(
        version=version).Pause(model_monitoring_job_ref)
    cmd_prefix = 'gcloud'
    if release_prefix:
      cmd_prefix += ' ' + release_prefix
    log.status.Print(
        constants.MODEL_MONITORING_JOB_PAUSE_DISPLAY_MESSAGE.format(
            id=model_monitoring_job_ref.Name(), cmd_prefix=cmd_prefix))
    return response


@base.ReleaseTracks(base.ReleaseTrack.GA)
class PauseGa(base.SilentCommand):
  """Pause a running Vertex AI model deployment monitoring job."""

  @staticmethod
  def Args(parser):
    flags.AddModelMonitoringJobResourceArg(parser, 'to pause')

  def Run(self, args):
    return _Run(args, constants.GA_VERSION, self.ReleaseTrack().prefix)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Pause(base.SilentCommand):
  """Pause a running Vertex AI model deployment monitoring job."""

  @staticmethod
  def Args(parser):
    flags.AddModelMonitoringJobResourceArg(parser, 'to pause')

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION, self.ReleaseTrack().prefix)


Pause.detailed_help = DETAILED_HELP
PauseGa.detailed_help = DETAILED_HELP
