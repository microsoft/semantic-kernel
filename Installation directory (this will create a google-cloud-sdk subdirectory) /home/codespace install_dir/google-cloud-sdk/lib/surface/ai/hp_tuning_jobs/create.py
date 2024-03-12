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
"""Command to create a hyperparameter tuning job in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import util as api_util
from googlecloudsdk.api_lib.ai.hp_tuning_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.hp_tuning_jobs import flags
from googlecloudsdk.command_lib.ai.hp_tuning_jobs import hp_tuning_jobs_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

_HPTUNING_JOB_CREATION_DISPLAY_MESSAGE = """\
Hyperparameter tuning job [{id}] submitted successfully.

Your job is still active. You may view the status of your job with the command

  $ gcloud{command_version} ai hp-tuning-jobs describe {id} --region={region}

Job State: {state}\
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGa(base.CreateCommand):
  """Create a hyperparameter tuning job."""

  _api_version = constants.GA_VERSION

  detailed_help = {
      'EXAMPLES':
          """\
          To create a job named ``test'' under project ``example'' in region
          ``us-central1'', run:

            $ {command} --region=us-central1 --project=example --config=config.yaml --display-name=test
          """
  }

  @classmethod
  def Args(cls, parser):
    flags.AddCreateHpTuningJobFlags(
        parser,
        api_util.GetMessage('StudySpec',
                            version=cls._api_version).AlgorithmValueValuesEnum)

  def Run(self, args):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    validation.ValidateRegion(
        region, available_regions=constants.SUPPORTED_TRAINING_REGIONS)

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._api_version, region=region):
      api_client = client.HpTuningJobsClient(version=self._api_version)
      algorithm = arg_utils.ChoiceToEnum(args.algorithm,
                                         api_client.AlgorithmEnum())
      labels = labels_util.ParseCreateArgs(
          args,
          api_client.HyperparameterTuningJobMessage().LabelsValue)

      response = api_client.Create(
          parent=region_ref.RelativeName(),
          config_path=args.config,
          display_name=args.display_name,
          max_trial_count=args.max_trial_count,
          parallel_trial_count=args.parallel_trial_count,
          algorithm=algorithm,
          kms_key_name=validation.GetAndValidateKmsKey(args),
          network=args.network,
          service_account=args.service_account,
          enable_web_access=args.enable_web_access,
          enable_dashboard_access=args.enable_dashboard_access,
          labels=labels)

      log.status.Print(
          _HPTUNING_JOB_CREATION_DISPLAY_MESSAGE.format(
              id=hp_tuning_jobs_util.ParseJobName(response.name),
              command_version=hp_tuning_jobs_util.OutputCommandVersion(
                  self.ReleaseTrack()),
              region=region,
              state=response.state))
      return response


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreatePreGa(CreateGa):
  """Create a hyperparameter tuning job."""

  _api_version = constants.BETA_VERSION
