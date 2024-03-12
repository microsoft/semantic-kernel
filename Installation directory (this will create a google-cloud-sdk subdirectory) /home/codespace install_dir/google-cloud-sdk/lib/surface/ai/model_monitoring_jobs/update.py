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
"""Vertex AI model deployment monitoring jobs update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_monitoring_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """
    To update display name of model deployment monitoring job `123` under project `example` in region `us-central1`, run:

      $ {command} 123 --display-name=new-name --project=example --region=us-central1
    """,
}


def _Args(parser):
  """Add flags for update command."""
  flags.AddModelMonitoringJobResourceArg(parser, 'to update')
  flags.GetDisplayNameArg(
      'model deployment monitoring job', required=False).AddToParser(parser)
  flags.GetEmailsArg(required=False).AddToParser(parser)
  flags.GetPredictionSamplingRateArg(
      required=False, default=None).AddToParser(parser)
  flags.GetMonitoringFrequencyArg(
      required=False, default=None).AddToParser(parser)
  flags.GetAnalysisInstanceSchemaArg(required=False).AddToParser(parser)
  flags.GetMonitoringLogTtlArg(required=False).AddToParser(parser)
  flags.AddObjectiveConfigGroupForUpdate(parser, required=False)
  flags.GetAnomalyCloudLoggingArg(required=False).AddToParser(parser)
  flags.GetNotificationChannelsArg(required=False).AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)


def _Run(args, version):
  """Run method for update command."""
  validation.ValidateDisplayName(args.display_name)
  model_monitoring_job_ref = args.CONCEPTS.monitoring_job.Parse()
  region = model_monitoring_job_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    try:
      result = client.ModelMonitoringJobsClient(version=version).Patch(
          model_monitoring_job_ref, args)
    except errors.NoFieldsSpecifiedError:
      available_update_args = [
          'display_name',
          'emails',
          'prediction_sampling_rate',
          'feature_thresholds',
          'monitoring_config_from_file',
          'monitoring_frequency',
          'analysis_instance_schema',
          'log_ttl',
          'update_labels',
          'clear_labels',
          'remove_labels',
          'anomaly_cloud_logging',
          'notification_channels',
      ]
      if not any(args.IsSpecified(arg) for arg in available_update_args):
        raise
      log.status.Print('No update to perform.')
      return None
    else:
      log.UpdatedResource(
          result.name, kind='Vertex AI model deployment monitoring job')
      return result


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGa(base.UpdateCommand):
  """Update an Vertex AI model deployment monitoring job."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update an Vertex AI model deployment monitoring job."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)


Update.detailed_help = DETAILED_HELP
UpdateGa.detailed_help = DETAILED_HELP
