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
"""Utilities for querying hptuning-jobs in AI platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.core import yaml


def GetAlgorithmEnum(version=constants.BETA_VERSION):
  messages = apis.GetMessagesModule(constants.AI_PLATFORM_API_NAME,
                                    constants.AI_PLATFORM_API_VERSION[version])
  if version == constants.GA_VERSION:
    return messages.GoogleCloudAiplatformV1StudySpec.AlgorithmValueValuesEnum
  else:
    return messages.GoogleCloudAiplatformV1beta1StudySpec.AlgorithmValueValuesEnum


class HpTuningJobsClient(object):
  """Client used for interacting with HyperparameterTuningJob endpoint."""

  def __init__(self, version):
    client = apis.GetClientInstance(constants.AI_PLATFORM_API_NAME,
                                    constants.AI_PLATFORM_API_VERSION[version])
    self._messages = client.MESSAGES_MODULE
    self._service = client.projects_locations_hyperparameterTuningJobs
    self.version = version
    self._message_prefix = constants.AI_PLATFORM_MESSAGE_PREFIX[version]

  def _GetMessage(self, message_name):
    """Returns the API messsages class by name."""

    return getattr(
        self._messages,
        '{prefix}{name}'.format(prefix=self._message_prefix,
                                name=message_name), None)

  def HyperparameterTuningJobMessage(self):
    """Returns the HyperparameterTuningJob resource message."""

    return self._GetMessage('HyperparameterTuningJob')

  def AlgorithmEnum(self):
    """Returns enum message representing Algorithm."""

    return self._GetMessage('StudySpec').AlgorithmValueValuesEnum

  def Create(
      self,
      config_path,
      display_name,
      parent=None,
      max_trial_count=None,
      parallel_trial_count=None,
      algorithm=None,
      kms_key_name=None,
      network=None,
      service_account=None,
      enable_web_access=False,
      enable_dashboard_access=False,
      labels=None):
    """Creates a hyperparameter tuning job with given parameters.

    Args:
      config_path: str, the file path of the hyperparameter tuning job
        configuration.
      display_name: str, the display name of the created hyperparameter tuning
        job.
      parent: str, parent of the created hyperparameter tuning job. e.g.
        /projects/xxx/locations/xxx/
      max_trial_count: int, the desired total number of Trials. The default
        value is 1.
      parallel_trial_count: int, the desired number of Trials to run in
        parallel. The default value is 1.
      algorithm: AlgorithmValueValuesEnum, the search algorithm specified for
        the Study.
      kms_key_name: str, A customer-managed encryption key to use for the
        hyperparameter tuning job.
      network: str, user network to which the job should be peered with
        (overrides yaml file)
      service_account: str, A service account (email address string) to use for
        the job.
      enable_web_access: bool, Whether to enable the interactive shell for the
        job.
      enable_dashboard_access: bool, Whether to enable the dashboard defined for
        the job.
      labels: LabelsValues, map-like user-defined metadata to organize the
        hp-tuning jobs.

    Returns:
      Created hyperparameter tuning job.
    """
    job_spec = self.HyperparameterTuningJobMessage()

    if config_path:
      data = yaml.load_path(config_path)
      if data:
        job_spec = messages_util.DictToMessageWithErrorCheck(
            data, self.HyperparameterTuningJobMessage())

    if not job_spec.maxTrialCount and not max_trial_count:
      job_spec.maxTrialCount = 1
    elif max_trial_count:
      job_spec.maxTrialCount = max_trial_count

    if not job_spec.parallelTrialCount and not parallel_trial_count:
      job_spec.parallelTrialCount = 1
    elif parallel_trial_count:
      job_spec.parallelTrialCount = parallel_trial_count

    if network:
      job_spec.trialJobSpec.network = network

    if service_account:
      job_spec.trialJobSpec.serviceAccount = service_account

    if enable_web_access:
      job_spec.trialJobSpec.enableWebAccess = enable_web_access
    if enable_dashboard_access:
      job_spec.trialJobSpec.enableDashboardAccess = enable_dashboard_access

    if display_name:
      job_spec.displayName = display_name

    if algorithm and job_spec.studySpec:
      job_spec.studySpec.algorithm = algorithm

    if kms_key_name is not None:
      job_spec.encryptionSpec = self._GetMessage('EncryptionSpec')(
          kmsKeyName=kms_key_name)

    if labels:
      job_spec.labels = labels

    if self.version == constants.GA_VERSION:
      request = self._messages.AiplatformProjectsLocationsHyperparameterTuningJobsCreateRequest(
          parent=parent,
          googleCloudAiplatformV1HyperparameterTuningJob=job_spec)
    else:
      request = self._messages.AiplatformProjectsLocationsHyperparameterTuningJobsCreateRequest(
          parent=parent,
          googleCloudAiplatformV1beta1HyperparameterTuningJob=job_spec)
    return self._service.Create(request)

  def Get(self, name=None):
    request = self._messages.AiplatformProjectsLocationsHyperparameterTuningJobsGetRequest(
        name=name)
    return self._service.Get(request)

  def Cancel(self, name=None):
    request = self._messages.AiplatformProjectsLocationsHyperparameterTuningJobsCancelRequest(
        name=name)
    return self._service.Cancel(request)

  def List(self, limit=None, region=None):
    return list_pager.YieldFromList(
        self._service,
        self._messages
        .AiplatformProjectsLocationsHyperparameterTuningJobsListRequest(
            parent=region),
        field='hyperparameterTuningJobs',
        batch_size_attribute='pageSize',
        limit=limit)

  def CheckJobComplete(self, name):
    """Returns a function to decide if log fetcher should continue polling.

    Args:
      name: String id of job.

    Returns:
      A one-argument function decides if log fetcher should continue.
    """
    request = self._messages.AiplatformProjectsLocationsHyperparameterTuningJobsGetRequest(
        name=name)
    response = self._service.Get(request)

    def ShouldContinue(periods_without_logs):
      if periods_without_logs <= 1:
        return True
      return response.endTime is None

    return ShouldContinue
