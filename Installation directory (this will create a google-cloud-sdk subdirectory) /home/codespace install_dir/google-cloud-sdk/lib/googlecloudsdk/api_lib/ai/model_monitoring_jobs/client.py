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
"""Utilities for dealing with AI Platform model monitoring jobs API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import encoding
from apitools.base.py import extra_types
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.ai import util as api_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import model_monitoring_jobs_util
from googlecloudsdk.command_lib.ai import validation as common_validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
import six


def _ParseEndpoint(endpoint_id, region_ref):
  """Parses a endpoint ID into a endpoint resource object."""
  region = region_ref.AsDict()['locationsId']
  return resources.REGISTRY.Parse(
      endpoint_id,
      params={
          'locationsId': region,
          'projectsId': properties.VALUES.core.project.GetOrFail
      },
      collection='aiplatform.projects.locations.endpoints')


def _ParseDataset(dataset_id, region_ref):
  """Parses a dataset ID into a dataset resource object."""
  region = region_ref.AsDict()['locationsId']
  return resources.REGISTRY.Parse(
      dataset_id,
      params={
          'locationsId': region,
          'projectsId': properties.VALUES.core.project.GetOrFail
      },
      collection='aiplatform.projects.locations.datasets')


class ModelMonitoringJobsClient(object):
  """High-level client for the AI Platform model deployment monitoring jobs surface."""

  def __init__(self, client=None, messages=None, version=None):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_modelDeploymentMonitoringJobs
    self._version = version

  def _ConstructDriftThresholds(self, feature_thresholds,
                                feature_attribution_thresholds):
    """Construct drift thresholds from user input.

    Args:
      feature_thresholds: Dict or None, key: feature_name, value: thresholds.
      feature_attribution_thresholds: Dict or None, key:feature_name, value:
        attribution score thresholds.

    Returns:
      PredictionDriftDetectionConfig
    """
    prediction_drift_detection = api_util.GetMessage(
        'ModelMonitoringObjectiveConfigPredictionDriftDetectionConfig',
        self._version)()
    additional_properties = []
    attribution_additional_properties = []
    if feature_thresholds:
      for key, value in feature_thresholds.items():
        threshold = 0.3 if not value else float(value)
        additional_properties.append(prediction_drift_detection
                                     .DriftThresholdsValue().AdditionalProperty(
                                         key=key,
                                         value=api_util.GetMessage(
                                             'ThresholdConfig',
                                             self._version)(value=threshold)))
      prediction_drift_detection.driftThresholds = prediction_drift_detection.DriftThresholdsValue(
          additionalProperties=additional_properties)
    if feature_attribution_thresholds:
      for key, value in feature_attribution_thresholds.items():
        threshold = 0.3 if not value else float(value)
        attribution_additional_properties.append(
            prediction_drift_detection.AttributionScoreDriftThresholdsValue(
            ).AdditionalProperty(
                key=key,
                value=api_util.GetMessage('ThresholdConfig',
                                          self._version)(value=threshold)))
      prediction_drift_detection.attributionScoreDriftThresholds = prediction_drift_detection.AttributionScoreDriftThresholdsValue(
          additionalProperties=attribution_additional_properties)

    return prediction_drift_detection

  def _ConstructSkewThresholds(self, feature_thresholds,
                               feature_attribution_thresholds):
    """Construct skew thresholds from user input.

    Args:
      feature_thresholds: Dict or None, key: feature_name, value: thresholds.
      feature_attribution_thresholds: Dict or None, key:feature_name, value:
        attribution score thresholds.

    Returns:
      TrainingPredictionSkewDetectionConfig
    """
    training_prediction_skew_detection = api_util.GetMessage(
        'ModelMonitoringObjectiveConfigTrainingPredictionSkewDetectionConfig',
        self._version)()
    additional_properties = []
    attribution_additional_properties = []
    if feature_thresholds:
      for key, value in feature_thresholds.items():
        threshold = 0.3 if not value else float(value)
        additional_properties.append(training_prediction_skew_detection
                                     .SkewThresholdsValue().AdditionalProperty(
                                         key=key,
                                         value=api_util.GetMessage(
                                             'ThresholdConfig',
                                             self._version)(value=threshold)))
      training_prediction_skew_detection.skewThresholds = training_prediction_skew_detection.SkewThresholdsValue(
          additionalProperties=additional_properties)
    if feature_attribution_thresholds:
      for key, value in feature_attribution_thresholds.items():
        threshold = 0.3 if not value else float(value)
        attribution_additional_properties.append(
            training_prediction_skew_detection
            .AttributionScoreSkewThresholdsValue().AdditionalProperty(
                key=key,
                value=api_util.GetMessage('ThresholdConfig',
                                          self._version)(value=threshold)))
      training_prediction_skew_detection.attributionScoreSkewThresholds = training_prediction_skew_detection.AttributionScoreSkewThresholdsValue(
          additionalProperties=attribution_additional_properties)

    return training_prediction_skew_detection

  def _ConstructObjectiveConfigForUpdate(self, existing_monitoring_job,
                                         feature_thresholds,
                                         feature_attribution_thresholds):
    """Construct monitoring objective config.

    Update the feature thresholds for skew/drift detection to all the existing
    deployed models under the job.
    Args:
      existing_monitoring_job: Existing monitoring job.
      feature_thresholds: Dict or None, key: feature_name, value: thresholds.
      feature_attribution_thresholds: Dict or None, key: feature_name, value:
        attribution score thresholds.

    Returns:
      A list of model monitoring objective config.
    """
    prediction_drift_detection = self._ConstructDriftThresholds(
        feature_thresholds, feature_attribution_thresholds)
    training_prediction_skew_detection = self._ConstructSkewThresholds(
        feature_thresholds, feature_attribution_thresholds)

    objective_configs = []
    for objective_config in existing_monitoring_job.modelDeploymentMonitoringObjectiveConfigs:
      if objective_config.objectiveConfig.trainingPredictionSkewDetectionConfig:
        if training_prediction_skew_detection.skewThresholds:
          objective_config.objectiveConfig.trainingPredictionSkewDetectionConfig.skewThresholds = training_prediction_skew_detection.skewThresholds
        if training_prediction_skew_detection.attributionScoreSkewThresholds:
          objective_config.objectiveConfig.trainingPredictionSkewDetectionConfig.attributionScoreSkewThresholds = training_prediction_skew_detection.attributionScoreSkewThresholds
      if objective_config.objectiveConfig.predictionDriftDetectionConfig:
        if prediction_drift_detection.driftThresholds:
          objective_config.objectiveConfig.predictionDriftDetectionConfig.driftThresholds = prediction_drift_detection.driftThresholds
        if prediction_drift_detection.attributionScoreDriftThresholds:
          objective_config.objectiveConfig.predictionDriftDetectionConfig.attributionScoreDriftThresholds = prediction_drift_detection.attributionScoreDriftThresholds
      if training_prediction_skew_detection.attributionScoreSkewThresholds or prediction_drift_detection.attributionScoreDriftThresholds:
        objective_config.objectiveConfig.explanationConfig = api_util.GetMessage(
            'ModelMonitoringObjectiveConfigExplanationConfig', self._version)(
                enableFeatureAttributes=True)
      objective_configs.append(objective_config)
    return objective_configs

  def _ConstructObjectiveConfigForCreate(self, location_ref, endpoint_name,
                                         feature_thresholds,
                                         feature_attribution_thresholds,
                                         dataset, bigquery_uri, data_format,
                                         gcs_uris, target_field,
                                         training_sampling_rate):
    """Construct monitoring objective config.

    Apply the feature thresholds for skew or drift detection to all the deployed
    models under the endpoint.
    Args:
      location_ref: Location reference.
      endpoint_name: Endpoint resource name.
      feature_thresholds: Dict or None, key: feature_name, value: thresholds.
      feature_attribution_thresholds: Dict or None, key: feature_name, value:
        attribution score thresholds.
      dataset: Vertex AI Dataset Id.
      bigquery_uri: The BigQuery table of the unmanaged Dataset used to train
        this Model.
      data_format: Google Cloud Storage format, supported format: csv,
        tf-record.
      gcs_uris: The Google Cloud Storage uri of the unmanaged Dataset used to
        train this Model.
      target_field: The target field name the model is to predict.
      training_sampling_rate: Training Dataset sampling rate.

    Returns:
      A list of model monitoring objective config.
    """
    objective_config_template = api_util.GetMessage(
        'ModelDeploymentMonitoringObjectiveConfig', self._version)()
    if feature_thresholds or feature_attribution_thresholds:
      if dataset or bigquery_uri or gcs_uris or data_format:
        training_dataset = api_util.GetMessage(
            'ModelMonitoringObjectiveConfigTrainingDataset', self._version)()
        if target_field is None:
          raise errors.ArgumentError(
              "Target field must be provided if you'd like to do training-prediction skew detection."
          )
        training_dataset.targetField = target_field
        training_dataset.loggingSamplingStrategy = api_util.GetMessage(
            'SamplingStrategy', self._version)(
                randomSampleConfig=api_util.GetMessage(
                    'SamplingStrategyRandomSampleConfig', self._version)(
                        sampleRate=training_sampling_rate))
        if dataset:
          training_dataset.dataset = _ParseDataset(dataset,
                                                   location_ref).RelativeName()
        elif bigquery_uri:
          training_dataset.bigquerySource = api_util.GetMessage(
              'BigQuerySource', self._version)(
                  inputUri=bigquery_uri)
        elif gcs_uris or data_format:
          if gcs_uris is None:
            raise errors.ArgumentError(
                'Data format is defined but no Google Cloud Storage uris are provided. Please use --gcs-uris to provide training datasets.'
            )
          if data_format is None:
            raise errors.ArgumentError(
                'No Data format is defined for Google Cloud Storage training dataset. Please use --data-format to define the Data format.'
            )
          training_dataset.dataFormat = data_format
          training_dataset.gcsSource = api_util.GetMessage(
              'GcsSource', self._version)(
                  uris=gcs_uris)
        training_prediction_skew_detection = self._ConstructSkewThresholds(
            feature_thresholds, feature_attribution_thresholds)
        objective_config_template.objectiveConfig = api_util.GetMessage(
            'ModelMonitoringObjectiveConfig', self._version
        )(trainingDataset=training_dataset,
          trainingPredictionSkewDetectionConfig=training_prediction_skew_detection
         )
      else:
        prediction_drift_detection = self._ConstructDriftThresholds(
            feature_thresholds, feature_attribution_thresholds)
        objective_config_template.objectiveConfig = api_util.GetMessage(
            'ModelMonitoringObjectiveConfig', self._version)(
                predictionDriftDetectionConfig=prediction_drift_detection)

      if feature_attribution_thresholds:
        objective_config_template.objectiveConfig.explanationConfig = api_util.GetMessage(
            'ModelMonitoringObjectiveConfigExplanationConfig', self._version)(
                enableFeatureAttributes=True)

    get_endpoint_req = self.messages.AiplatformProjectsLocationsEndpointsGetRequest(
        name=endpoint_name)
    endpoint = self.client.projects_locations_endpoints.Get(get_endpoint_req)
    objective_configs = []
    for deployed_model in endpoint.deployedModels:
      objective_config = copy.deepcopy(objective_config_template)
      objective_config.deployedModelId = deployed_model.id
      objective_configs.append(objective_config)
    return objective_configs

  def _ParseCreateLabels(self, args):
    """Parses create labels."""
    return labels_util.ParseCreateArgs(
        args,
        api_util.GetMessage('ModelDeploymentMonitoringJob',
                            self._version)().LabelsValue)

  def _ParseUpdateLabels(self, model_monitoring_job_ref, args):
    """Parses update labels."""
    def GetLabels():
      return self.Get(model_monitoring_job_ref).labels

    return labels_util.ProcessUpdateArgsLazy(
        args,
        api_util.GetMessage('ModelDeploymentMonitoringJob',
                            self._version)().LabelsValue, GetLabels)

  def Create(self, location_ref, args):
    """Creates a model deployment monitoring job."""
    endpoint_ref = _ParseEndpoint(args.endpoint, location_ref)
    job_spec = api_util.GetMessage('ModelDeploymentMonitoringJob',
                                   self._version)()
    kms_key_name = common_validation.GetAndValidateKmsKey(args)
    if kms_key_name is not None:
      job_spec.encryptionSpec = api_util.GetMessage('EncryptionSpec',
                                                    self._version)(
                                                        kmsKeyName=kms_key_name)

    if args.monitoring_config_from_file:
      data = yaml.load_path(args.monitoring_config_from_file)
      if data:
        job_spec = messages_util.DictToMessageWithErrorCheck(
            data,
            api_util.GetMessage('ModelDeploymentMonitoringJob', self._version))
    else:
      job_spec.modelDeploymentMonitoringObjectiveConfigs = self._ConstructObjectiveConfigForCreate(
          location_ref, endpoint_ref.RelativeName(), args.feature_thresholds,
          args.feature_attribution_thresholds, args.dataset, args.bigquery_uri,
          args.data_format, args.gcs_uris, args.target_field,
          args.training_sampling_rate)
    job_spec.endpoint = endpoint_ref.RelativeName()
    job_spec.displayName = args.display_name
    job_spec.labels = self._ParseCreateLabels(args)

    enable_anomaly_cloud_logging = False if args.anomaly_cloud_logging is None else args.anomaly_cloud_logging

    job_spec.modelMonitoringAlertConfig = api_util.GetMessage(
        'ModelMonitoringAlertConfig', self._version)(
            enableLogging=enable_anomaly_cloud_logging,
            emailAlertConfig=api_util.GetMessage(
                'ModelMonitoringAlertConfigEmailAlertConfig',
                self._version)(userEmails=args.emails),
            notificationChannels=args.notification_channels)

    job_spec.loggingSamplingStrategy = api_util.GetMessage(
        'SamplingStrategy', self._version)(
            randomSampleConfig=api_util.GetMessage(
                'SamplingStrategyRandomSampleConfig', self._version)(
                    sampleRate=args.prediction_sampling_rate))

    job_spec.modelDeploymentMonitoringScheduleConfig = api_util.GetMessage(
        'ModelDeploymentMonitoringScheduleConfig', self._version)(
            monitorInterval='{}s'.format(
                six.text_type(3600 * int(args.monitoring_frequency))))

    if args.predict_instance_schema:
      job_spec.predictInstanceSchemaUri = args.predict_instance_schema

    if args.analysis_instance_schema:
      job_spec.analysisInstanceSchemaUri = args.analysis_instance_schema

    if args.log_ttl:
      job_spec.logTtl = '{}s'.format(six.text_type(86400 * int(args.log_ttl)))

    if args.sample_predict_request:
      instance_json = model_monitoring_jobs_util.ReadInstanceFromArgs(
          args.sample_predict_request)
      job_spec.samplePredictInstance = encoding.PyValueToMessage(
          extra_types.JsonValue, instance_json)

    if self._version == constants.BETA_VERSION:
      return self._service.Create(
          self.messages.
          AiplatformProjectsLocationsModelDeploymentMonitoringJobsCreateRequest(
              parent=location_ref.RelativeName(),
              googleCloudAiplatformV1beta1ModelDeploymentMonitoringJob=job_spec
          ))
    else:
      return self._service.Create(
          self.messages.
          AiplatformProjectsLocationsModelDeploymentMonitoringJobsCreateRequest(
              parent=location_ref.RelativeName(),
              googleCloudAiplatformV1ModelDeploymentMonitoringJob=job_spec))

  def Patch(self, model_monitoring_job_ref, args):
    """Update a model deployment monitoring job."""
    model_monitoring_job_to_update = api_util.GetMessage(
        'ModelDeploymentMonitoringJob', self._version)()
    update_mask = []

    job_spec = api_util.GetMessage('ModelDeploymentMonitoringJob',
                                   self._version)()
    if args.monitoring_config_from_file:
      data = yaml.load_path(args.monitoring_config_from_file)
      if data:
        job_spec = messages_util.DictToMessageWithErrorCheck(
            data,
            api_util.GetMessage('ModelDeploymentMonitoringJob', self._version))
        model_monitoring_job_to_update.modelDeploymentMonitoringObjectiveConfigs = job_spec.modelDeploymentMonitoringObjectiveConfigs
        update_mask.append('model_deployment_monitoring_objective_configs')

    if args.feature_thresholds or args.feature_attribution_thresholds:
      get_monitoring_job_req = self.messages.AiplatformProjectsLocationsModelDeploymentMonitoringJobsGetRequest(
          name=model_monitoring_job_ref.RelativeName())
      model_monitoring_job = self._service.Get(get_monitoring_job_req)
      model_monitoring_job_to_update.modelDeploymentMonitoringObjectiveConfigs = self._ConstructObjectiveConfigForUpdate(
          model_monitoring_job, args.feature_thresholds,
          args.feature_attribution_thresholds)
      update_mask.append('model_deployment_monitoring_objective_configs')

    if args.display_name:
      model_monitoring_job_to_update.displayName = args.display_name
      update_mask.append('display_name')

    if args.emails:
      model_monitoring_job_to_update.modelMonitoringAlertConfig = (
          api_util.GetMessage('ModelMonitoringAlertConfig', self._version)(
              emailAlertConfig=api_util.GetMessage(
                  'ModelMonitoringAlertConfigEmailAlertConfig', self._version
              )(userEmails=args.emails)
          )
      )
      update_mask.append('model_monitoring_alert_config.email_alert_config')

    if args.anomaly_cloud_logging is not None:
      if args.emails:
        model_monitoring_job_to_update.modelMonitoringAlertConfig.enableLogging = (
            args.anomaly_cloud_logging
        )
      else:
        model_monitoring_job_to_update.modelMonitoringAlertConfig = (
            api_util.GetMessage('ModelMonitoringAlertConfig', self._version)(
                enableLogging=args.anomaly_cloud_logging
            )
        )
      update_mask.append('model_monitoring_alert_config.enable_logging')

    if args.notification_channels:
      if args.emails or args.anomaly_cloud_logging is not None:
        model_monitoring_job_to_update.modelMonitoringAlertConfig.notificationChannels = (
            args.notification_channels
        )
      else:
        model_monitoring_job_to_update.modelMonitoringAlertConfig = (
            api_util.GetMessage('ModelMonitoringAlertConfig', self._version)(
                notificationChannels=args.notification_channels
            )
        )
      update_mask.append('model_monitoring_alert_config.notification_channels')

    # sampling rate
    if args.prediction_sampling_rate:
      model_monitoring_job_to_update.loggingSamplingStrategy = api_util.GetMessage(
          'SamplingStrategy', self._version)(
              randomSampleConfig=api_util.GetMessage(
                  'SamplingStrategyRandomSampleConfig', self._version)(
                      sampleRate=args.prediction_sampling_rate))
      update_mask.append('logging_sampling_strategy')

    # schedule
    if args.monitoring_frequency:
      model_monitoring_job_to_update.modelDeploymentMonitoringScheduleConfig = api_util.GetMessage(
          'ModelDeploymentMonitoringScheduleConfig', self._version)(
              monitorInterval='{}s'.format(
                  six.text_type(3600 * int(args.monitoring_frequency))))
      update_mask.append('model_deployment_monitoring_schedule_config')

    if args.analysis_instance_schema:
      model_monitoring_job_to_update.analysisInstanceSchemaUri = args.analysis_instance_schema
      update_mask.append('analysis_instance_schema_uri')

    if args.log_ttl:
      model_monitoring_job_to_update.logTtl = '{}s'.format(
          six.text_type(86400 * int(args.log_ttl)))
      update_mask.append('log_ttl')

    labels_update = self._ParseUpdateLabels(model_monitoring_job_ref, args)
    if labels_update.needs_update:
      model_monitoring_job_to_update.labels = labels_update.labels
      update_mask.append('labels')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    if self._version == constants.BETA_VERSION:
      req = self.messages.AiplatformProjectsLocationsModelDeploymentMonitoringJobsPatchRequest(
          name=model_monitoring_job_ref.RelativeName(),
          googleCloudAiplatformV1beta1ModelDeploymentMonitoringJob=model_monitoring_job_to_update,
          updateMask=','.join(update_mask))
    else:
      req = self.messages.AiplatformProjectsLocationsModelDeploymentMonitoringJobsPatchRequest(
          name=model_monitoring_job_ref.RelativeName(),
          googleCloudAiplatformV1ModelDeploymentMonitoringJob=model_monitoring_job_to_update,
          updateMask=','.join(update_mask))

    return self._service.Patch(req)

  def Get(self, model_monitoring_job_ref):
    request = self.messages.AiplatformProjectsLocationsModelDeploymentMonitoringJobsGetRequest(
        name=model_monitoring_job_ref.RelativeName())
    return self._service.Get(request)

  def List(self, limit=None, region_ref=None):
    return list_pager.YieldFromList(
        self._service,
        self.messages
        .AiplatformProjectsLocationsModelDeploymentMonitoringJobsListRequest(
            parent=region_ref.RelativeName()),
        field='modelDeploymentMonitoringJobs',
        batch_size_attribute='pageSize',
        limit=limit)

  def Delete(self, model_monitoring_job_ref):
    request = self.messages.AiplatformProjectsLocationsModelDeploymentMonitoringJobsDeleteRequest(
        name=model_monitoring_job_ref.RelativeName())
    return self._service.Delete(request)

  def Pause(self, model_monitoring_job_ref):
    request = self.messages.AiplatformProjectsLocationsModelDeploymentMonitoringJobsPauseRequest(
        name=model_monitoring_job_ref.RelativeName())
    return self._service.Pause(request)

  def Resume(self, model_monitoring_job_ref):
    request = self.messages.AiplatformProjectsLocationsModelDeploymentMonitoringJobsResumeRequest(
        name=model_monitoring_job_ref.RelativeName())
    return self._service.Resume(request)
