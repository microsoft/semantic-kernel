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
"""Vertex AI model monitoring jobs create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_monitoring_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import model_monitoring_jobs_util
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """
    To create a model deployment monitoring job under project ``example'' in region ``us-central1'' for endpoint ``123'', run:

      $ {command} --project=example --region=us-central1 --display-name=my_monitoring_job --emails=a@gmail.com,b@gmail.com --endpoint=123 --prediction-sampling-rate=0.2

    To create a model deployment monitoring job with drift detection for all the deployed models under the endpoint ``123'', run:

      $ {command} --project=example --region=us-central1 --display-name=my_monitoring_job --emails=a@gmail.com,b@gmail.com --endpoint=123 --prediction-sampling-rate=0.2 --feature-thresholds=feat1=0.1,feat2=0.2,feat3=0.2,feat4=0.3

    To create a model deployment monitoring job with skew detection for all the deployed models under the endpoint ``123'', with training dataset from Google Cloud Storage, run:

      $ {command} --project=example --region=us-central1 --display-name=my_monitoring_job --emails=a@gmail.com,b@gmail.com --endpoint=123 --prediction-sampling-rate=0.2 --feature-thresholds=feat1=0.1,feat2=0.2,feat3=0.2,feat4=0.3 --target-field=price --data-format=csv --gcs-uris=gs://test-bucket/dataset.csv

    To create a model deployment monitoring job with skew detection for all the deployed models under the endpoint ``123'', with training dataset from Vertex AI dataset ``456'', run:

      $ {command} --project=example --region=us-central1 --display-name=my_monitoring_job --emails=a@gmail.com,b@gmail.com --endpoint=123 --prediction-sampling-rate=0.2 --feature-thresholds=feat1=0.1,feat2=0.2,feat3=0.2,feat4=0.3 --target-field=price --dataset=456

    To create a model deployment monitoring job with different drift detection or skew detection for different deployed models, run:

      $ {command} --project=example --region=us-central1 --display-name=my_monitoring_job --emails=a@gmail.com,b@gmail.com --endpoint=123 --prediction-sampling-rate=0.2 --monitoring-config-from-file=your_objective_config.yaml

    After creating the monitoring job, be sure to send some predict requests. It will be used to generate some metadata for analysis purpose, like predict and analysis instance schema.
    """,
}


def _Args(parser):
  """Add flags for create command."""
  flags.AddRegionResourceArg(
      parser,
      'to create model deployment monitoring job',
      prompt_func=region_util.GetPromptForRegionFunc(
          constants.SUPPORTED_MODEL_MONITORING_JOBS_REGIONS))
  flags.GetDisplayNameArg('model deployment monitoring job').AddToParser(parser)
  flags.GetEndpointIdArg(required=True).AddToParser(parser)
  flags.GetEmailsArg(required=True).AddToParser(parser)
  flags.GetPredictionSamplingRateArg(required=True).AddToParser(parser)
  flags.GetMonitoringFrequencyArg(required=False).AddToParser(parser)
  flags.GetPredictInstanceSchemaArg(required=False).AddToParser(parser)
  flags.GetAnalysisInstanceSchemaArg(required=False).AddToParser(parser)
  flags.GetSamplingPredictRequestArg(required=False).AddToParser(parser)
  flags.GetMonitoringLogTtlArg(required=False).AddToParser(parser)
  flags.AddObjectiveConfigGroupForCreate(parser, required=False)
  flags.AddKmsKeyResourceArg(parser, 'model deployment monitoring job')
  flags.GetAnomalyCloudLoggingArg(required=False).AddToParser(parser)
  flags.GetNotificationChannelsArg(required=False).AddToParser(parser)
  labels_util.AddCreateLabelsFlags(parser)


def _Run(args, version, release_prefix):
  """Run method for create command."""
  validation.ValidateDisplayName(args.display_name)
  region_ref = args.CONCEPTS.region.Parse()
  region = region_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(
      version=version, region=region):
    response = client.ModelMonitoringJobsClient(version=version).Create(
        region_ref, args)
    cmd_prefix = 'gcloud'
    if release_prefix:
      cmd_prefix += ' ' + release_prefix
    log.status.Print(
        constants.MODEL_MONITORING_JOB_CREATION_DISPLAY_MESSAGE.format(
            id=model_monitoring_jobs_util.ParseJobName(response.name),
            cmd_prefix=cmd_prefix,
            state=response.state))
    return response


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGa(base.CreateCommand):
  """Create a new Vertex AI model monitoring job."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION, self.ReleaseTrack().prefix)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a new Vertex AI model monitoring job."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION, self.ReleaseTrack().prefix)


Create.detailed_help = DETAILED_HELP
CreateGa.detailed_help = DETAILED_HELP
