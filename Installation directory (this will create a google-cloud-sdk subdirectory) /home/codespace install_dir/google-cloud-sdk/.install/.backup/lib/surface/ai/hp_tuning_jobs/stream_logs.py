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
"""Command to check stream logs of a hyperparameter tuning job in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.hp_tuning_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags as common_flags
from googlecloudsdk.command_lib.ai import log_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.hp_tuning_jobs import flags as hp_tuning_job_flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class StreamLogs(base.Command):
  """Stream logs from a running Vertex AI hyperparameter tuning job.

     ## EXAMPLES

     To stream logs of a hyperparameter tuning job, run:

     $ {command} stream-logs HP_TUNING_JOB
  """

  @staticmethod
  def Args(parser):
    hp_tuning_job_flags.AddHptuningJobResourceArg(parser, 'to fetch stream log')
    common_flags.AddStreamLogsFlags(parser)
    parser.display_info.AddFormat(log_util.LOG_FORMAT)

  def Run(self, args):
    hptuning_job_ref = args.CONCEPTS.hptuning_job.Parse()
    region = hptuning_job_ref.AsDict()['locationsId']
    validation.ValidateRegion(
        region, available_regions=constants.SUPPORTED_TRAINING_REGIONS)

    version = constants.GA_VERSION if self.ReleaseTrack(
    ) == base.ReleaseTrack.GA else constants.BETA_VERSION
    with endpoint_util.AiplatformEndpointOverrides(
        version=version, region=region):
      relative_name = hptuning_job_ref.RelativeName()
      return log_util.StreamLogs(
          hptuning_job_ref.AsDict()['hyperparameterTuningJobsId'],
          continue_function=client.HpTuningJobsClient(
              version=version).CheckJobComplete(relative_name),
          polling_interval=args.polling_interval,
          task_name=args.task_name,
          allow_multiline=args.allow_multiline_logs)
