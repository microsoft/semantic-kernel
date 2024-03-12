# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Flag definitions specifically for gcloud ai hp-tuning-jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai.hp_tuning_jobs import hp_tuning_jobs_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

_HPTUNING_JOB_DISPLAY_NAME = base.Argument(
    '--display-name',
    required=True,
    help=('Display name of the hyperparameter tuning job to create.'))
# The parameter max-trial-count and parallel-trial-count can be set through
# command line or config.yaml file. Setting the values to be None to indicate
# the value is not set through command line by the customers. If both command
# line and config.yaml file don't set the field, we set it to be 1.
_HPTUNING_MAX_TRIAL_COUNT = base.Argument(
    '--max-trial-count',
    type=int,
    default=None,
    help='Desired total number of trials. The default value is 1.')
_HPTUNING_PARALLEL_TRIAL_COUNT = base.Argument(
    '--parallel-trial-count',
    type=int,
    default=None,
    help='Desired number of Trials to run in parallel. The default value is 1.')
_HPTUNING_JOB_CONFIG = base.Argument(
    '--config',
    required=True,
    help="""
Path to the job configuration file. This file should be a YAML document containing a HyperparameterTuningSpec.
If an option is specified both in the configuration file **and** via command line arguments, the command line arguments
override the configuration file.

Example(YAML):

  displayName: TestHpTuningJob
  maxTrialCount: 1
  parallelTrialCount: 1
  studySpec:
    metrics:
    - metricId: x
      goal: MINIMIZE
    parameters:
    - parameterId: z
      integerValueSpec:
        minValue: 1
        maxValue: 100
    algorithm: RANDOM_SEARCH
  trialJobSpec:
    workerPoolSpecs:
    - machineSpec:
        machineType: n1-standard-4
      replicaCount: 1
      containerSpec:
        imageUri: gcr.io/ucaip-test/ucaip-training-test
""")


def AddCreateHpTuningJobFlags(parser, algorithm_enum):
  """Adds arguments for creating hp tuning job."""
  _HPTUNING_JOB_DISPLAY_NAME.AddToParser(parser)
  _HPTUNING_JOB_CONFIG.AddToParser(parser)
  _HPTUNING_MAX_TRIAL_COUNT.AddToParser(parser)
  _HPTUNING_PARALLEL_TRIAL_COUNT.AddToParser(parser)

  labels_util.AddCreateLabelsFlags(parser)

  flags.AddRegionResourceArg(
      parser,
      'to create a hyperparameter tuning job',
      prompt_func=region_util.GetPromptForRegionFunc(
          constants.SUPPORTED_TRAINING_REGIONS))
  flags.TRAINING_SERVICE_ACCOUNT.AddToParser(parser)
  flags.NETWORK.AddToParser(parser)
  flags.ENABLE_WEB_ACCESS.AddToParser(parser)
  flags.ENABLE_DASHBOARD_ACCESS.AddToParser(parser)
  flags.AddKmsKeyResourceArg(parser, 'hyperparameter tuning job')

  arg_utils.ChoiceEnumMapper(
      '--algorithm',
      algorithm_enum,
      help_str='Search algorithm specified for the given study. '
  ).choice_arg.AddToParser(parser)


def AddHptuningJobResourceArg(parser,
                              verb,
                              regions=constants.SUPPORTED_TRAINING_REGIONS):
  """Adds a resource argument for a Vertex AI hyperparameter tuning job.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    regions: list[str], the list of supported regions.
  """
  job_resource_spec = concepts.ResourceSpec(
      resource_collection=hp_tuning_jobs_util.HPTUNING_JOB_COLLECTION,
      resource_name='hyperparameter tuning job',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=flags.RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(regions)),
      disable_auto_completers=False)

  concept_parsers.ConceptParser.ForResource(
      'hptuning_job',
      job_resource_spec,
      'The hyperparameter tuning job {}.'.format(verb),
      required=True).AddToParser(parser)
