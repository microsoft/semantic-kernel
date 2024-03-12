# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Utilities for dealing with ML jobs API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml


class NoFieldsSpecifiedError(exceptions.Error):
  """Error indicating that no updates were requested in a Patch operation."""


class NoPackagesSpecifiedError(exceptions.Error):
  """Error that no packages were specified for non-custom training."""


def GetMessagesModule(version='v1'):
  return apis.GetMessagesModule('ml', version)


def GetClientInstance(version='v1', no_http=False):
  return apis.GetClientInstance('ml', version, no_http=no_http)


class JobsClient(object):
  """Client for jobs service in the Cloud ML Engine API."""

  def __init__(self, client=None, messages=None,
               short_message_prefix='GoogleCloudMlV1', client_version='v1'):
    self.client = client or GetClientInstance(client_version)
    self.messages = messages or self.client.MESSAGES_MODULE
    self._short_message_prefix = short_message_prefix

  def GetShortMessage(self, short_message_name):
    return getattr(self.messages,
                   '{prefix}{name}'.format(prefix=self._short_message_prefix,
                                           name=short_message_name), None)

  @property
  def state_enum(self):
    return self.messages.GoogleCloudMlV1Job.StateValueValuesEnum

  def List(self, project_ref):
    req = self.messages.MlProjectsJobsListRequest(
        parent=project_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.projects_jobs, req, field='jobs',
        batch_size_attribute='pageSize')

  @property
  def job_class(self):
    return self.messages.GoogleCloudMlV1Job

  @property
  def training_input_class(self):
    return self.messages.GoogleCloudMlV1TrainingInput

  @property
  def prediction_input_class(self):
    return self.messages.GoogleCloudMlV1PredictionInput

  def _MakeCreateRequest(self, parent=None, job=None):
    return self.messages.MlProjectsJobsCreateRequest(
        parent=parent,
        googleCloudMlV1Job=job)

  def Create(self, project_ref, job):
    return self.client.projects_jobs.Create(
        self._MakeCreateRequest(
            parent=project_ref.RelativeName(),
            job=job))

  def Cancel(self, job_ref):
    """Cancels given job."""
    req = self.messages.MlProjectsJobsCancelRequest(name=job_ref.RelativeName())
    return self.client.projects_jobs.Cancel(req)

  def Get(self, job_ref):
    req = self.messages.MlProjectsJobsGetRequest(name=job_ref.RelativeName())
    return self.client.projects_jobs.Get(req)

  def Patch(self, job_ref, labels_update):
    """Update a job."""
    job = self.job_class()
    update_mask = []
    if labels_update.needs_update:
      job.labels = labels_update.labels
      update_mask.append('labels')
    if not update_mask:
      raise NoFieldsSpecifiedError('No updates requested.')
    req = self.messages.MlProjectsJobsPatchRequest(
        name=job_ref.RelativeName(),
        googleCloudMlV1Job=job,
        updateMask=','.join(update_mask)
    )
    return self.client.projects_jobs.Patch(req)

  def BuildTrainingJob(self,
                       path=None,
                       module_name=None,
                       job_name=None,
                       trainer_uri=None,
                       region=None,
                       job_dir=None,
                       scale_tier=None,
                       user_args=None,
                       runtime_version=None,
                       python_version=None,
                       network=None,
                       service_account=None,
                       labels=None,
                       kms_key=None,
                       custom_train_server_config=None,
                       enable_web_access=None):
    """Builds a Cloud ML Engine Job from a config file and/or flag values.

    Args:
        path: path to a yaml configuration file
        module_name: value to set for moduleName field (overrides yaml file)
        job_name: value to set for jobName field (overrides yaml file)
        trainer_uri: List of values to set for trainerUri field (overrides yaml
          file)
        region: compute region in which to run the job (overrides yaml file)
        job_dir: Cloud Storage working directory for the job (overrides yaml
          file)
        scale_tier: ScaleTierValueValuesEnum the scale tier for the job
          (overrides yaml file)
        user_args: [str]. A list of arguments to pass through to the job.
        (overrides yaml file)
        runtime_version: the runtime version in which to run the job (overrides
          yaml file)
        python_version: the Python version in which to run the job (overrides
          yaml file)
        network: user network to which the job should be peered with (overrides
          yaml file)
        service_account: A service account (email address string) to use for the
          job.
        labels: Job.LabelsValue, the Cloud labels for the job
        kms_key: A customer-managed encryption key to use for the job.
        custom_train_server_config: jobs_util.CustomTrainingInputServerConfig,
          configuration object for custom server parameters.
        enable_web_access: whether to enable the interactive shell for the job.
    Raises:
      NoPackagesSpecifiedError: if a non-custom job was specified without any
        trainer_uris.
    Returns:
        A constructed Job object.
    """
    job = self.job_class()

    # TODO(b/123467089): Remove yaml file loading here, only parse data objects
    if path:
      data = yaml.load_path(path)
      if data:
        job = encoding.DictToMessage(data, self.job_class)

    if job_name:
      job.jobId = job_name

    if labels is not None:
      job.labels = labels

    if not job.trainingInput:
      job.trainingInput = self.training_input_class()
    additional_fields = {
        'pythonModule': module_name,
        'args': user_args,
        'packageUris': trainer_uri,
        'region': region,
        'jobDir': job_dir,
        'scaleTier': scale_tier,
        'runtimeVersion': runtime_version,
        'pythonVersion': python_version,
        'network': network,
        'serviceAccount': service_account,
        'enableWebAccess': enable_web_access,
    }
    for field_name, value in additional_fields.items():
      if value is not None:
        setattr(job.trainingInput, field_name, value)

    if kms_key:
      arg_utils.SetFieldInMessage(job,
                                  'trainingInput.encryptionConfig.kmsKeyName',
                                  kms_key)

    if custom_train_server_config:
      for field_name, value in custom_train_server_config.GetFieldMap().items():
        if value is not None:
          if (field_name.endswith('Config') and
              not field_name.endswith('TfConfig')):
            if value['imageUri']:
              arg_utils.SetFieldInMessage(
                  job,
                  'trainingInput.{}.imageUri'.format(field_name),
                  value['imageUri'])
            if value['acceleratorConfig']['type']:
              arg_utils.SetFieldInMessage(
                  job,
                  'trainingInput.{}.acceleratorConfig.type'.format(field_name),
                  value['acceleratorConfig']['type'])
            if value['acceleratorConfig']['count']:
              arg_utils.SetFieldInMessage(
                  job,
                  'trainingInput.{}.acceleratorConfig.count'.format(field_name),
                  value['acceleratorConfig']['count'])
            if field_name == 'workerConfig' and value['tpuTfVersion']:
              arg_utils.SetFieldInMessage(
                  job,
                  'trainingInput.{}.tpuTfVersion'.format(field_name),
                  value['tpuTfVersion'])
          else:
            setattr(job.trainingInput, field_name, value)

    if not self.HasPackageURIs(job) and not self.IsCustomContainerTraining(job):
      raise NoPackagesSpecifiedError('Non-custom jobs must have packages.')

    return job

  def HasPackageURIs(self, job):
    return bool(job.trainingInput.packageUris)

  def IsCustomContainerTraining(self, job):
    return bool(job.trainingInput.masterConfig and
                job.trainingInput.masterConfig.imageUri)

  def BuildBatchPredictionJob(self,
                              job_name=None,
                              model_dir=None,
                              model_name=None,
                              version_name=None,
                              input_paths=None,
                              data_format=None,
                              output_path=None,
                              region=None,
                              runtime_version=None,
                              max_worker_count=None,
                              batch_size=None,
                              signature_name=None,
                              labels=None,
                              accelerator_count=None,
                              accelerator_type=None):
    """Builds a Cloud ML Engine Job for batch prediction from flag values.

    Args:
        job_name: value to set for jobName field
        model_dir: str, Google Cloud Storage location of the model files
        model_name: str, value to set for modelName field
        version_name: str, value to set for versionName field
        input_paths: list of input files
        data_format: format of the input files
        output_path: single value for the output location
        region: compute region in which to run the job
        runtime_version: the runtime version in which to run the job
        max_worker_count: int, the maximum number of workers to use
        batch_size: int, the number of records per batch sent to Tensorflow
        signature_name: str, name of input/output signature in the TF meta graph
        labels: Job.LabelsValue, the Cloud labels for the job
        accelerator_count: int, The number of accelerators to attach to the
           machines
       accelerator_type: AcceleratorsValueListEntryValuesEnum, The type of
           accelerator to add to machine.
    Returns:
        A constructed Job object.
    """
    project_id = properties.VALUES.core.project.GetOrFail()

    if accelerator_type:
      accelerator_config_msg = self.GetShortMessage('AcceleratorConfig')
      accelerator_config = accelerator_config_msg(count=accelerator_count,
                                                  type=accelerator_type)
    else:
      accelerator_config = None

    prediction_input = self.prediction_input_class(
        inputPaths=input_paths,
        outputPath=output_path,
        region=region,
        runtimeVersion=runtime_version,
        maxWorkerCount=max_worker_count,
        batchSize=batch_size,
        accelerator=accelerator_config
    )

    prediction_input.dataFormat = prediction_input.DataFormatValueValuesEnum(
        data_format)
    if model_dir:
      prediction_input.uri = model_dir
    elif version_name:
      version_ref = resources.REGISTRY.Parse(
          version_name, collection='ml.projects.models.versions',
          params={'modelsId': model_name, 'projectsId': project_id})
      prediction_input.versionName = version_ref.RelativeName()
    else:
      model_ref = resources.REGISTRY.Parse(
          model_name, collection='ml.projects.models',
          params={'projectsId': project_id})
      prediction_input.modelName = model_ref.RelativeName()

    if signature_name:
      prediction_input.signatureName = signature_name

    return self.job_class(
        jobId=job_name,
        predictionInput=prediction_input,
        labels=labels
    )
