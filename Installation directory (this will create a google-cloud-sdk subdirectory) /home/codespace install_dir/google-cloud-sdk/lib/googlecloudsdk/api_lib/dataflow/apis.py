# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Helpers for interacting with the Cloud Dataflow API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import shutil
import textwrap

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.command_lib.builds import submit_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
import six

DATAFLOW_API_NAME = 'dataflow'
DATAFLOW_API_VERSION = 'v1b3'
# TODO(b/139889563): Remove when dataflow args region is changed to required
DATAFLOW_API_DEFAULT_REGION = 'us-central1'


def GetMessagesModule():
  return apis.GetMessagesModule(DATAFLOW_API_NAME, DATAFLOW_API_VERSION)


def GetClientInstance():
  return apis.GetClientInstance(DATAFLOW_API_NAME, DATAFLOW_API_VERSION)


def GetProject():
  return properties.VALUES.core.project.Get(required=True)


class Jobs:
  """The Jobs set of Dataflow API functions."""

  GET_REQUEST = GetMessagesModule().DataflowProjectsLocationsJobsGetRequest
  LIST_REQUEST = GetMessagesModule().DataflowProjectsLocationsJobsListRequest
  AGGREGATED_LIST_REQUEST = GetMessagesModule(
  ).DataflowProjectsJobsAggregatedRequest
  UPDATE_REQUEST = GetMessagesModule(
  ).DataflowProjectsLocationsJobsUpdateRequest

  @staticmethod
  def GetService():
    return GetClientInstance().projects_locations_jobs

  @staticmethod
  def Get(job_id, project_id=None, region_id=None, view=None):
    """Calls the Dataflow Jobs.Get method.

    Args:
      job_id: Identifies a single job.
      project_id: The project which owns the job.
      region_id: The regional endpoint where the job lives.
      view: (DataflowProjectsJobsGetRequest.ViewValueValuesEnum) Level of
        information requested in response.

    Returns:
      (Job)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    request = GetMessagesModule().DataflowProjectsLocationsJobsGetRequest(
        jobId=job_id, location=region_id, projectId=project_id, view=view)
    try:
      return Jobs.GetService().Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def Cancel(job_id, force=False, project_id=None, region_id=None):
    """Cancels a job by calling the Jobs.Update method.

    Args:
      job_id: Identifies a single job.
      force: True to forcibly cancel the job.
      project_id: The project which owns the job.
      region_id: The regional endpoint where the job lives.

    Returns:
      (Job)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    labels = None
    if force:
      labels = GetMessagesModule().Job.LabelsValue(additionalProperties=[
          GetMessagesModule().Job.LabelsValue.AdditionalProperty(
              key='force_cancel_job', value='true')
      ])
    job = GetMessagesModule().Job(
        labels=labels,
        requestedState=(GetMessagesModule().Job.RequestedStateValueValuesEnum
                        .JOB_STATE_CANCELLED))
    request = GetMessagesModule().DataflowProjectsLocationsJobsUpdateRequest(
        jobId=job_id, location=region_id, projectId=project_id, job=job)
    try:
      return Jobs.GetService().Update(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def UpdateOptions(
      job_id,
      project_id=None,
      region_id=None,
      min_num_workers=None,
      max_num_workers=None,
      worker_utilization_hint=None,
      unset_worker_utilization_hint=None,
  ):
    """Update pipeline options on a running job.

    You should specify at-least one (or both) of min_num_workers and
    max_num_workers.

    Args:
      job_id: ID of job to update
      project_id: Project of the job
      region_id: Region the job is in
      min_num_workers: Lower-bound for worker autoscaling
      max_num_workers: Upper-bound for worker autoscaling
      worker_utilization_hint: Target CPU utilization for worker autoscaling
      unset_worker_utilization_hint: Unsets worker_utilization_hint value

    Returns:
      The updated Job
    """

    project_id = project_id or GetProject()
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    job = GetMessagesModule().Job(
        runtimeUpdatableParams=GetMessagesModule().RuntimeUpdatableParams(
            minNumWorkers=min_num_workers,
            maxNumWorkers=max_num_workers,
            workerUtilizationHint=(
                None
                if unset_worker_utilization_hint
                else worker_utilization_hint
            ),
        )
    )

    update_mask_pieces = []
    if min_num_workers is not None:
      update_mask_pieces.append('runtime_updatable_params.min_num_workers')
    if max_num_workers is not None:
      update_mask_pieces.append('runtime_updatable_params.max_num_workers')
    if (
        worker_utilization_hint is not None
        or unset_worker_utilization_hint
    ):
      update_mask_pieces.append(
          'runtime_updatable_params.worker_utilization_hint'
      )
    update_mask = ','.join(update_mask_pieces)

    request = GetMessagesModule().DataflowProjectsLocationsJobsUpdateRequest(
        jobId=job_id,
        location=region_id,
        projectId=project_id,
        job=job,
        updateMask=update_mask,
    )
    try:
      return Jobs.GetService().Update(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def Drain(job_id, project_id=None, region_id=None):
    """Drains a job by calling the Jobs.Update method.

    Args:
      job_id: Identifies a single job.
      project_id: The project which owns the job.
      region_id: The regional endpoint where the job lives.

    Returns:
      (Job)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    job = GetMessagesModule().Job(
        requestedState=(GetMessagesModule().Job.RequestedStateValueValuesEnum
                        .JOB_STATE_DRAINED))
    request = GetMessagesModule().DataflowProjectsLocationsJobsUpdateRequest(
        jobId=job_id, location=region_id, projectId=project_id, job=job)
    try:
      return Jobs.GetService().Update(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def ResumeUnsupportedSDK(job_id,
                           experiment_with_token,
                           project_id=None,
                           region_id=None):
    """Resumes a job by calling the Jobs.Update method.

    Args:
      job_id: Identifies a single job.
      experiment_with_token: The resume token unique to the job prefixed with
        the experiment key.
      project_id: The project which owns the job.
      region_id: The regional endpoint where the job lives.

    Returns:
      (Job)
    """
    project_id = project_id or GetProject()
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    environment = GetMessagesModule().Environment(
        experiments=[experiment_with_token])
    job = GetMessagesModule().Job(environment=environment)
    request = GetMessagesModule().DataflowProjectsLocationsJobsUpdateRequest(
        jobId=job_id, location=region_id, projectId=project_id, job=job)
    try:
      return Jobs.GetService().Update(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def Snapshot(job_id,
               project_id=None,
               region_id=None,
               ttl='604800s',
               snapshot_sources=False):
    """Takes a snapshot of a job via the Jobs.Snapshot method.

    Args:
      job_id: Identifies a single job.
      project_id: The project which owns the job.
      region_id: The regional endpoint where the job lives.
      ttl: The ttl for the snapshot.
      snapshot_sources: If true, the sources will be snapshotted.

    Returns:
      (Snapshot)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    request = GetMessagesModule().DataflowProjectsLocationsJobsSnapshotRequest(
        jobId=job_id,
        location=region_id,
        projectId=project_id,
        snapshotJobRequest=GetMessagesModule().SnapshotJobRequest(
            location=region_id, ttl=ttl, snapshotSources=snapshot_sources),
    )
    try:
      return Jobs.GetService().Snapshot(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class Metrics:
  """The Metrics set of Dataflow API functions."""

  GET_REQUEST = GetMessagesModule(
  ).DataflowProjectsLocationsJobsGetMetricsRequest

  @staticmethod
  def GetService():
    return GetClientInstance().projects_locations_jobs

  @staticmethod
  def Get(job_id, project_id=None, region_id=None, start_time=None):
    """Calls the Dataflow Metrics.Get method.

    Args:
      job_id: The job to get messages for.
      project_id: The project which owns the job.
      region_id: The regional endpoint of the job.
      start_time: Return only metric data that has changed since this time.
        Default is to return all information about all metrics for the job.

    Returns:
      (MetricUpdate)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    request = GetMessagesModule(
    ).DataflowProjectsLocationsJobsGetMetricsRequest(
        jobId=job_id,
        location=region_id,
        projectId=project_id,
        startTime=start_time)
    try:
      return Metrics.GetService().GetMetrics(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class TemplateArguments:
  """Wrapper class for template arguments."""

  project_id = None
  region_id = None
  gcs_location = None
  job_name = None
  zone = None
  max_workers = None
  num_workers = None
  network = None
  subnetwork = None
  worker_machine_type = None
  staging_location = None
  temp_location = None
  kms_key_name = None
  disable_public_ips = None
  parameters = None
  service_account_email = None
  worker_region = None
  worker_zone = None
  enable_streaming_engine = None
  additional_experiments = None
  additional_user_labels = None
  streaming_update = None
  transform_name_mappings = None
  flexrs_goal = None

  def __init__(self,
               project_id=None,
               region_id=None,
               job_name=None,
               gcs_location=None,
               zone=None,
               max_workers=None,
               num_workers=None,
               network=None,
               subnetwork=None,
               worker_machine_type=None,
               staging_location=None,
               temp_location=None,
               kms_key_name=None,
               disable_public_ips=None,
               parameters=None,
               service_account_email=None,
               worker_region=None,
               worker_zone=None,
               enable_streaming_engine=None,
               additional_experiments=None,
               additional_user_labels=None,
               streaming_update=None,
               transform_name_mappings=None,
               flexrs_goal=None):
    self.project_id = project_id
    self.region_id = region_id
    self.job_name = job_name
    self.gcs_location = gcs_location
    self.zone = zone
    self.max_workers = max_workers
    self.num_workers = num_workers
    self.network = network
    self.subnetwork = subnetwork
    self.worker_machine_type = worker_machine_type
    self.staging_location = staging_location
    self.temp_location = temp_location
    self.kms_key_name = kms_key_name
    self.disable_public_ips = disable_public_ips
    self.parameters = parameters
    self.service_account_email = service_account_email
    self.worker_region = worker_region
    self.worker_zone = worker_zone
    self.enable_streaming_engine = enable_streaming_engine
    self.additional_experiments = additional_experiments
    self.additional_user_labels = additional_user_labels
    self.streaming_update = streaming_update
    self.transform_name_mappings = transform_name_mappings
    self.flexrs_goal = flexrs_goal


class Templates:
  """The Templates set of Dataflow API functions."""

  CREATE_REQUEST = GetMessagesModule().CreateJobFromTemplateRequest
  LAUNCH_TEMPLATE_PARAMETERS = GetMessagesModule().LaunchTemplateParameters
  LAUNCH_TEMPLATE_PARAMETERS_VALUE = LAUNCH_TEMPLATE_PARAMETERS.ParametersValue
  LAUNCH_FLEX_TEMPLATE_REQUEST = GetMessagesModule().LaunchFlexTemplateRequest
  PARAMETERS_VALUE = CREATE_REQUEST.ParametersValue
  FLEX_TEMPLATE_ENVIRONMENT = GetMessagesModule().FlexTemplateRuntimeEnvironment
  FLEX_TEMPLATE_USER_LABELS_VALUE = (
      FLEX_TEMPLATE_ENVIRONMENT.AdditionalUserLabelsValue
  )
  FLEX_TEMPLATE_PARAMETER = GetMessagesModule().LaunchFlexTemplateParameter
  FLEX_TEMPLATE_PARAMETERS_VALUE = FLEX_TEMPLATE_PARAMETER.ParametersValue
  FLEX_TEMPLATE_TRANSFORM_NAME_MAPPING_VALUE = (
      FLEX_TEMPLATE_PARAMETER.TransformNameMappingsValue
  )
  IP_CONFIGURATION_ENUM_VALUE = GetMessagesModule(
  ).FlexTemplateRuntimeEnvironment.IpConfigurationValueValuesEnum
  FLEXRS_GOAL_ENUM_VALUE = GetMessagesModule(
  ).FlexTemplateRuntimeEnvironment.FlexrsGoalValueValuesEnum
  TEMPLATE_METADATA = GetMessagesModule().TemplateMetadata
  SDK_INFO = GetMessagesModule().SDKInfo
  SDK_LANGUAGE = GetMessagesModule().SDKInfo.LanguageValueValuesEnum
  CONTAINER_SPEC = GetMessagesModule().ContainerSpec
  FLEX_TEMPLATE_JAVA11_BASE_IMAGE = ('gcr.io/dataflow-templates-base/'
                                     'java11-template-launcher-base:latest')
  FLEX_TEMPLATE_JAVA17_BASE_IMAGE = ('gcr.io/dataflow-templates-base/'
                                     'java17-template-launcher-base:latest')
  FLEX_TEMPLATE_JAVA8_BASE_IMAGE = ('gcr.io/dataflow-templates-base/'
                                    'java8-template-launcher-base:latest')
  FLEX_TEMPLATE_PYTHON3_BASE_IMAGE = ('gcr.io/dataflow-templates-base/'
                                      'python3-template-launcher-base:latest')
  FLEX_TEMPLATE_GO_BASE_IMAGE = ('gcr.io/dataflow-templates-base/'
                                 'go-template-launcher-base:latest')
  # Mapping of apitools request message fields to their json parameters
  _CUSTOM_JSON_FIELD_MAPPINGS = {
      'dynamicTemplate_gcsPath': 'dynamicTemplate.gcsPath',
      'dynamicTemplate_stagingLocation': 'dynamicTemplate.stagingLocation'
  }

  # message fields.
  @staticmethod
  def ModifyDynamicTemplatesLaunchRequest(req):
    """Add Api field query string mappings to req."""
    updated_request_type = type(req)
    for req_field, mapped_param in Templates._CUSTOM_JSON_FIELD_MAPPINGS.items(
    ):
      encoding.AddCustomJsonFieldMapping(updated_request_type, req_field,
                                         mapped_param)
    return req

  @staticmethod
  def GetService():
    return GetClientInstance().projects_locations_templates

  @staticmethod
  def GetFlexTemplateService():
    return GetClientInstance().projects_locations_flexTemplates

  @staticmethod
  def Create(template_args=None):
    """Calls the Dataflow Templates.CreateFromJob method.

    Args:
      template_args: Arguments for create template.

    Returns:
      (Job)
    """
    params_list = []
    parameters = template_args.parameters
    for k, v in six.iteritems(parameters) if parameters else {}:
      params_list.append(
          Templates.PARAMETERS_VALUE.AdditionalProperty(key=k, value=v))

    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = template_args.region_id or DATAFLOW_API_DEFAULT_REGION

    ip_configuration_enum = GetMessagesModule(
    ).RuntimeEnvironment.IpConfigurationValueValuesEnum
    ip_private = ip_configuration_enum.WORKER_IP_PRIVATE
    ip_configuration = ip_private if template_args.disable_public_ips else None

    body = Templates.CREATE_REQUEST(
        gcsPath=template_args.gcs_location,
        jobName=template_args.job_name,
        location=region_id,
        environment=GetMessagesModule().RuntimeEnvironment(
            serviceAccountEmail=template_args.service_account_email,
            zone=template_args.zone,
            maxWorkers=template_args.max_workers,
            numWorkers=template_args.num_workers,
            network=template_args.network,
            subnetwork=template_args.subnetwork,
            machineType=template_args.worker_machine_type,
            tempLocation=template_args.staging_location,
            kmsKeyName=template_args.kms_key_name,
            ipConfiguration=ip_configuration,
            workerRegion=template_args.worker_region,
            workerZone=template_args.worker_zone,
            enableStreamingEngine=template_args.enable_streaming_engine,
            additionalExperiments=(template_args.additional_experiments
                                   if template_args.additional_experiments else
                                   [])),
        parameters=Templates.PARAMETERS_VALUE(
            additionalProperties=params_list) if parameters else None)
    request = GetMessagesModule(
    ).DataflowProjectsLocationsTemplatesCreateRequest(
        projectId=template_args.project_id or GetProject(),
        location=region_id,
        createJobFromTemplateRequest=body)

    try:
      return Templates.GetService().Create(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def LaunchDynamicTemplate(template_args=None):
    """Calls the Dataflow Templates.LaunchTemplate method on a dynamic template.

    Args:
      template_args: Arguments to create template. gcs_location must point to a
        Json serialized DynamicTemplateFileSpec.

    Returns:
      (LaunchTemplateResponse)
    """
    params_list = []
    parameters = template_args.parameters
    for k, v in six.iteritems(parameters) if parameters else {}:
      params_list.append(
          Templates.LAUNCH_TEMPLATE_PARAMETERS_VALUE.AdditionalProperty(
              key=k, value=v))

    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = template_args.region_id or DATAFLOW_API_DEFAULT_REGION

    ip_configuration_enum = GetMessagesModule(
    ).RuntimeEnvironment.IpConfigurationValueValuesEnum
    ip_private = ip_configuration_enum.WORKER_IP_PRIVATE
    ip_configuration = ip_private if template_args.disable_public_ips else None

    body = Templates.LAUNCH_TEMPLATE_PARAMETERS(
        environment=GetMessagesModule().RuntimeEnvironment(
            serviceAccountEmail=template_args.service_account_email,
            zone=template_args.zone,
            maxWorkers=template_args.max_workers,
            numWorkers=template_args.num_workers,
            network=template_args.network,
            subnetwork=template_args.subnetwork,
            machineType=template_args.worker_machine_type,
            tempLocation=template_args.staging_location,
            kmsKeyName=template_args.kms_key_name,
            ipConfiguration=ip_configuration,
            workerRegion=template_args.worker_region,
            workerZone=template_args.worker_zone),
        jobName=template_args.job_name,
        parameters=Templates.LAUNCH_TEMPLATE_PARAMETERS_VALUE(
            additionalProperties=params_list) if parameters else None,
        update=False)
    request = GetMessagesModule(
    ).DataflowProjectsLocationsTemplatesLaunchRequest(
        dynamicTemplate_gcsPath=template_args.gcs_location,
        dynamicTemplate_stagingLocation=template_args.staging_location,
        location=region_id,
        launchTemplateParameters=body,
        projectId=template_args.project_id or GetProject(),
        validateOnly=False)

    Templates.ModifyDynamicTemplatesLaunchRequest(request)

    try:
      return Templates.GetService().Launch(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def __ConvertDictArguments(arguments, value_message):
    """Convert dictionary arguments to parameter list .

    Args:
      arguments: Arguments for create job using template.
      value_message: the value message of the arguments

    Returns:
      List of value_message.AdditionalProperty
    """
    params_list = []
    if arguments:
      for k, v in six.iteritems(arguments):
        params_list.append(value_message.AdditionalProperty(key=k, value=v))

    return params_list

  @staticmethod
  def BuildJavaImageDockerfile(flex_template_base_image, pipeline_paths, env):
    """Builds Dockerfile contents for java flex template image.

    Args:
      flex_template_base_image: SDK version or base image to use.
      pipeline_paths: List of paths to pipelines and dependencies.
      env: Dictionary of env variables to set in the container image.

    Returns:
      Dockerfile contents as string.
    """
    dockerfile_template = """
    FROM {base_image}

    {env}

    {copy}

    {commands}
    """
    commands = ''
    env['FLEX_TEMPLATE_JAVA_CLASSPATH'] = '/template/*'
    envs = ['ENV {}={}'.format(k, v) for k, v in sorted(env.items())]
    env_list = '\n'.join(envs)
    paths = ' '.join(pipeline_paths)
    copy_command = 'COPY {} /template/'.format(paths)

    dockerfile_contents = textwrap.dedent(dockerfile_template).format(
        base_image=Templates._GetFlexTemplateBaseImage(
            flex_template_base_image),
        env=env_list,
        copy=copy_command,
        commands='\n'.join(commands))
    return dockerfile_contents

  @staticmethod
  def BuildPythonImageDockerfile(flex_template_base_image, pipeline_paths, env):
    """Builds Dockerfile contents for python flex template image.

    Args:
      flex_template_base_image: SDK version or base image to use.
      pipeline_paths: List of paths to pipelines and dependencies.
      env: Dictionary of env variables to set in the container image.

    Returns:
      Dockerfile contents as string.
    """
    dockerfile_template = """
    FROM {base_image}

    {env}

    {copy}

    {commands}
    """
    commands = [
        'apt-get update',
        'apt-get install -y libffi-dev git',
        'rm -rf /var/lib/apt/lists/*',
    ]

    env['FLEX_TEMPLATE_PYTHON_PY_FILE'] = '/template/{}'.format(
        (env['FLEX_TEMPLATE_PYTHON_PY_FILE']))
    if 'FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE' in env:
      env['FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE'] = '/template/{}'.format(
          env['FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE'])
      commands.append('pip install --no-cache-dir -U -r {}'.format(
          env['FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE']))
    if 'FLEX_TEMPLATE_PYTHON_SETUP_FILE' in env:
      env['FLEX_TEMPLATE_PYTHON_SETUP_FILE'] = '/template/{}'.format(
          env['FLEX_TEMPLATE_PYTHON_SETUP_FILE'])

    envs = ['ENV {}={}'.format(k, v) for k, v in sorted(env.items())]
    env_list = '\n'.join(envs)
    paths = ' '.join(pipeline_paths)
    copy_command = 'COPY {} /template/'.format(paths)

    dockerfile_contents = textwrap.dedent(dockerfile_template).format(
        base_image=Templates._GetFlexTemplateBaseImage(
            flex_template_base_image),
        env=env_list,
        copy=copy_command,
        commands='RUN ' + ' && '.join(commands))
    return dockerfile_contents

  # staticmethod enforced by prior code, this violates the style guide and
  # would benefit from a refactor in the future.
  # TODO(b/242564654): Add type annotations for arguments when presubmits allow
  # them.
  @staticmethod
  def BuildGoImageDockerfile(flex_template_base_image,
                             pipeline_paths,
                             env):
    """Builds Dockerfile contents for go flex template image.

    Args:
      flex_template_base_image: SDK version or base image to use.
      pipeline_paths: Path to pipeline binary.
      env: Dictionary of env variables to set in the container image.

    Returns:
      Dockerfile contents as string.
    """
    dockerfile_template = """
    FROM {base_image}

    {env}

    {copy}
    """
    env['FLEX_TEMPLATE_GO_BINARY'] = '/template/{}'.format(
        env['FLEX_TEMPLATE_GO_BINARY'])
    paths = ' '.join(pipeline_paths)
    copy_command = 'COPY {} /template/'.format(paths)

    envs = [
        'ENV {}={}'.format(var, val) for var, val in sorted(env.items())
    ]
    env_list = '\n'.join(envs)

    dockerfile_contents = textwrap.dedent(dockerfile_template).format(
        base_image=Templates._GetFlexTemplateBaseImage(
            flex_template_base_image),
        env=env_list,
        copy=copy_command)

    return dockerfile_contents

  @staticmethod
  def BuildDockerfile(flex_template_base_image, pipeline_paths, env,
                      sdk_language):
    """Builds Dockerfile contents for flex template image.

    Args:
      flex_template_base_image: SDK version or base image to use.
      pipeline_paths: List of paths to pipelines and dependencies.
      env: Dictionary of env variables to set in the container image.
      sdk_language: SDK language of the flex template.

    Returns:
      Dockerfile contents as string.
    """
    if sdk_language == 'JAVA':
      return Templates.BuildJavaImageDockerfile(flex_template_base_image,
                                                pipeline_paths, env)
    elif sdk_language == 'PYTHON':
      return Templates.BuildPythonImageDockerfile(flex_template_base_image,
                                                  pipeline_paths, env)
    elif sdk_language == 'GO':
      return Templates.BuildGoImageDockerfile(flex_template_base_image,
                                              pipeline_paths, env)

  @staticmethod
  def _ValidateTemplateParameters(parameters):
    """Validates ParameterMetadata objects in template metadata.

    Args:
      parameters: List of ParameterMetadata objects.

    Raises:
      ValueError: If is any of the required field is not set.
    """
    for parameter in parameters:
      if not parameter.name:
        raise ValueError(
            'Invalid template metadata. Parameter name field is empty.'
            ' Parameter: {}'.format(parameter))
      if not parameter.label:
        raise ValueError(
            'Invalid template metadata. Parameter label field is empty.'
            ' Parameter: {}'.format(parameter))
      if not parameter.helpText:
        raise ValueError(
            'Invalid template metadata. Parameter helpText field is empty.'
            ' Parameter: {}'.format(parameter))

  @staticmethod
  def __ValidateFlexTemplateEnv(env, sdk_language):
    """Builds and validates Flex template environment values.

    Args:
      env: Dictionary of env variables to set in the container image.
      sdk_language: SDK language of the flex template.

    Returns:
      True on valid env values.

    Raises:
      ValueError: If is any of parameter value is invalid.
    """
    if sdk_language == 'JAVA' and 'FLEX_TEMPLATE_JAVA_MAIN_CLASS' not in env:
      raise ValueError(('FLEX_TEMPLATE_JAVA_MAIN_CLASS environment variable '
                        'should be provided for all JAVA jobs.'))
    elif sdk_language == 'PYTHON' and 'FLEX_TEMPLATE_PYTHON_PY_FILE' not in env:
      raise ValueError(('FLEX_TEMPLATE_PYTHON_PY_FILE environment variable '
                        'should be provided for all PYTHON jobs.'))
    elif sdk_language == 'GO' and 'FLEX_TEMPLATE_GO_BINARY' not in env:
      raise ValueError(('FLEX_TEMPLATE_GO_BINARY environment variable '
                        'should be provided for all GO jobs.'))
    return True

  @staticmethod
  def _BuildTemplateMetadata(template_metadata_json):
    """Builds and validates TemplateMetadata object.

    Args:
      template_metadata_json: Template metadata in json format.

    Returns:
      TemplateMetadata object on success.

    Raises:
      ValueError: If is any of the required field is not set.
    """
    template_metadata = encoding.JsonToMessage(Templates.TEMPLATE_METADATA,
                                               template_metadata_json)
    template_metadata_obj = Templates.TEMPLATE_METADATA()

    if not template_metadata.name:
      raise ValueError('Invalid template metadata. Name field is empty.'
                       ' Template Metadata: {}'.format(template_metadata))
    template_metadata_obj.name = template_metadata.name

    if template_metadata.description:
      template_metadata_obj.description = template_metadata.description

    if template_metadata.parameters:
      Templates._ValidateTemplateParameters(template_metadata.parameters)
      template_metadata_obj.parameters = template_metadata.parameters

    return template_metadata_obj

  @staticmethod
  def _GetFlexTemplateBaseImage(flex_template_base_image):
    """Returns latest base image for given sdk version.

    Args:
        flex_template_base_image: SDK version or base image to use.

    Returns:
      If a custom base image value is given, returns the same value. Else,
      returns the latest base image for the given sdk version.
    """
    if flex_template_base_image == 'JAVA11':
      return Templates.FLEX_TEMPLATE_JAVA11_BASE_IMAGE
    elif flex_template_base_image == 'JAVA17':
      return Templates.FLEX_TEMPLATE_JAVA17_BASE_IMAGE
    elif flex_template_base_image == 'JAVA8':
      return Templates.FLEX_TEMPLATE_JAVA8_BASE_IMAGE
    elif flex_template_base_image == 'PYTHON3':
      return Templates.FLEX_TEMPLATE_PYTHON3_BASE_IMAGE
    elif flex_template_base_image == 'GO':
      return Templates.FLEX_TEMPLATE_GO_BASE_IMAGE
    return flex_template_base_image

  @staticmethod
  def _BuildSDKInfo(sdk_language):
    """Builds SDKInfo object.

    Args:
      sdk_language: SDK language of the flex template.

    Returns:
      SDKInfo object
    """
    if sdk_language == 'JAVA':
      return Templates.SDK_INFO(language=Templates.SDK_LANGUAGE.JAVA)
    elif sdk_language == 'PYTHON':
      return Templates.SDK_INFO(language=Templates.SDK_LANGUAGE.PYTHON)
    elif sdk_language == 'GO':
      return Templates.SDK_INFO(language=Templates.SDK_LANGUAGE.GO)

  @staticmethod
  def _StoreFlexTemplateFile(template_file_gcs_location, container_spec_json):
    """Stores flex template container spec file in GCS.

    Args:
      template_file_gcs_location: GCS location to store the template file.
      container_spec_json: Container spec in json format.

    Returns:
      Returns the stored flex template file gcs object on success.
      Propagates the error on failures.
    """
    with files.TemporaryDirectory() as temp_dir:
      local_path = os.path.join(temp_dir, 'template-file.json')
      # Use Unix style line-endings on all platforms (especially Windows)
      files.WriteFileContents(local_path, container_spec_json, newline='\n')
      storage_client = storage_api.StorageClient()
      obj_ref = storage_util.ObjectReference.FromUrl(template_file_gcs_location)
      return storage_client.CopyFileToGCS(local_path, obj_ref)

  @staticmethod
  def BuildAndStoreFlexTemplateFile(template_file_gcs_location,
                                    image,
                                    template_metadata_json,
                                    sdk_language,
                                    print_only,
                                    template_args=None,
                                    image_repository_username_secret_id=None,
                                    image_repository_password_secret_id=None,
                                    image_repository_cert_path=None):
    """Builds container spec and stores it in the flex template file in GCS.

    Args:
      template_file_gcs_location: GCS location to store the template file.
      image: Path to the container image.
      template_metadata_json: Template metadata in json format.
      sdk_language: SDK language of the flex template.
      print_only: Only prints the container spec and skips write to GCS.
      template_args: Default runtime parameters specified by template authors.
      image_repository_username_secret_id: Secret manager secret id for username
        to authenticate to private registry.
      image_repository_password_secret_id: Secret manager secret id for password
        to authenticate to private registry.
      image_repository_cert_path: The full URL to self-signed certificate of
        private registry in Cloud Storage.

    Returns:
      Container spec json if print_only is set. A success message with template
      file GCS path and container spec otherewise.
    """
    template_metadata = None
    if template_metadata_json:
      template_metadata = Templates._BuildTemplateMetadata(
          template_metadata_json)
    sdk_info = Templates._BuildSDKInfo(sdk_language)
    default_environment = None
    if template_args:
      user_labels_list = Templates.__ConvertDictArguments(
          template_args.additional_user_labels,
          Templates.FLEX_TEMPLATE_USER_LABELS_VALUE)
      ip_private = Templates.IP_CONFIGURATION_ENUM_VALUE.WORKER_IP_PRIVATE
      ip_configuration = (
          ip_private if template_args.disable_public_ips else None
      )
      enable_streaming_engine = (
          True if template_args.enable_streaming_engine else None
      )
      default_environment = Templates.FLEX_TEMPLATE_ENVIRONMENT(
          serviceAccountEmail=template_args.service_account_email,
          maxWorkers=template_args.max_workers,
          numWorkers=template_args.num_workers,
          network=template_args.network,
          subnetwork=template_args.subnetwork,
          machineType=template_args.worker_machine_type,
          tempLocation=template_args.temp_location
          if template_args.temp_location else template_args.staging_location,
          stagingLocation=template_args.staging_location,
          kmsKeyName=template_args.kms_key_name,
          ipConfiguration=ip_configuration,
          workerRegion=template_args.worker_region,
          workerZone=template_args.worker_zone,
          enableStreamingEngine=enable_streaming_engine,
          additionalExperiments=(template_args.additional_experiments if
                                 template_args.additional_experiments else []),
          additionalUserLabels=Templates.FLEX_TEMPLATE_USER_LABELS_VALUE(
              additionalProperties=user_labels_list)
          if user_labels_list else None)
    container_spec = Templates.CONTAINER_SPEC(
        image=image,
        metadata=template_metadata,
        sdkInfo=sdk_info,
        defaultEnvironment=default_environment,
        imageRepositoryUsernameSecretId=image_repository_username_secret_id,
        imageRepositoryPasswordSecretId=image_repository_password_secret_id,
        imageRepositoryCertPath=image_repository_cert_path)
    container_spec_json = encoding.MessageToJson(container_spec)
    container_spec_pretty_json = json.dumps(
        json.loads(container_spec_json),
        sort_keys=True,
        indent=4,
        separators=(',', ': '))
    if print_only:
      return container_spec_pretty_json
    try:
      Templates._StoreFlexTemplateFile(template_file_gcs_location,
                                       container_spec_pretty_json)
      log.status.Print(
          'Successfully saved container spec in flex template file.\n'
          'Template File GCS Location: {}\n'
          'Container Spec:\n\n'
          '{}'.format(template_file_gcs_location, container_spec_pretty_json))
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def BuildAndStoreFlexTemplateImage(image_gcr_path, flex_template_base_image,
                                     jar_paths, py_paths, go_binary_path, env,
                                     sdk_language, gcs_log_dir):
    """Builds the flex template docker container image and stores it in GCR.

    Args:
      image_gcr_path: GCR location to store the flex template container image.
      flex_template_base_image: SDK version or base image to use.
      jar_paths: List of jar paths to pipelines and dependencies.
      py_paths: List of python paths to pipelines and dependencies.
      go_binary_path: Path to compiled Go pipeline binary.
      env: Dictionary of env variables to set in the container image.
      sdk_language: SDK language of the flex template.
      gcs_log_dir: Path to Google Cloud Storage directory to store build logs.

    Returns:
      True if container is built and store successfully.

    Raises:
      ValueError: If the parameters values are invalid.
    """
    Templates.__ValidateFlexTemplateEnv(env, sdk_language)
    with files.TemporaryDirectory() as temp_dir:
      log.status.Print('Copying files to a temp directory {}'.format(temp_dir))

      pipeline_files = []
      paths = jar_paths
      if py_paths:
        paths = py_paths
      elif go_binary_path:
        paths = [go_binary_path]

      for path in paths:
        absl_path = os.path.abspath(path)
        if os.path.isfile(absl_path):
          shutil.copy2(absl_path, temp_dir)
        else:
          shutil.copytree(absl_path,
                          '{}/{}'.format(temp_dir, os.path.basename(absl_path)))
        pipeline_files.append(os.path.split(absl_path)[1])

      log.status.Print(
          'Generating dockerfile to build the flex template container image...')
      dockerfile_contents = Templates.BuildDockerfile(flex_template_base_image,
                                                      pipeline_files, env,
                                                      sdk_language)

      dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
      files.WriteFileContents(dockerfile_path, dockerfile_contents)
      log.status.Print(
          'Generated Dockerfile. Contents: {}'.format(dockerfile_contents))

      messages = cloudbuild_util.GetMessagesModule()
      build_config = submit_util.CreateBuildConfig(
          image_gcr_path,
          no_cache=False,
          messages=messages,
          substitutions=None,
          arg_config='cloudbuild.yaml',
          is_specified_source=True,
          no_source=False,
          source=temp_dir,
          gcs_source_staging_dir=None,
          ignore_file=None,
          arg_gcs_log_dir=gcs_log_dir,
          arg_machine_type=None,
          arg_disk_size=None,
          arg_worker_pool=None,
          arg_dir=None,
          arg_revision=None,
          arg_git_source_dir=None,
          arg_git_source_revision=None,
          buildpack=None,
      )
      log.status.Print('Pushing flex template container image to GCR...')

      submit_util.Build(messages, False, build_config)
      return True

  @staticmethod
  def CreateJobFromFlexTemplate(template_args=None):
    """Calls the create job from flex template APIs.

    Args:
      template_args: Arguments for create template.

    Returns:
      (Job)
    """

    params_list = Templates.__ConvertDictArguments(
        template_args.parameters, Templates.FLEX_TEMPLATE_PARAMETERS_VALUE)
    transform_mapping_list = Templates.__ConvertDictArguments(
        template_args.transform_name_mappings,
        Templates.FLEX_TEMPLATE_TRANSFORM_NAME_MAPPING_VALUE)
    transform_mappings = None
    streaming_update = None
    if template_args.streaming_update:
      streaming_update = template_args.streaming_update
      if transform_mapping_list:
        transform_mappings = (
            Templates.FLEX_TEMPLATE_TRANSFORM_NAME_MAPPING_VALUE(
                additionalProperties=transform_mapping_list
            )
        )

    user_labels_list = Templates.__ConvertDictArguments(
        template_args.additional_user_labels,
        Templates.FLEX_TEMPLATE_USER_LABELS_VALUE)

    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = template_args.region_id or DATAFLOW_API_DEFAULT_REGION

    ip_private = Templates.IP_CONFIGURATION_ENUM_VALUE.WORKER_IP_PRIVATE
    ip_configuration = ip_private if template_args.disable_public_ips else None

    flexrs_goal = None
    if template_args.flexrs_goal:
      if template_args.flexrs_goal == 'SPEED_OPTIMIZED':
        flexrs_goal = Templates.FLEXRS_GOAL_ENUM_VALUE.FLEXRS_SPEED_OPTIMIZED
      elif template_args.flexrs_goal == 'COST_OPTIMIZED':
        flexrs_goal = Templates.FLEXRS_GOAL_ENUM_VALUE.FLEXRS_COST_OPTIMIZED

    body = Templates.LAUNCH_FLEX_TEMPLATE_REQUEST(
        launchParameter=Templates.FLEX_TEMPLATE_PARAMETER(
            jobName=template_args.job_name,
            containerSpecGcsPath=template_args.gcs_location,
            environment=Templates.FLEX_TEMPLATE_ENVIRONMENT(
                serviceAccountEmail=template_args.service_account_email,
                maxWorkers=template_args.max_workers,
                numWorkers=template_args.num_workers,
                network=template_args.network,
                subnetwork=template_args.subnetwork,
                machineType=template_args.worker_machine_type,
                tempLocation=template_args.temp_location if template_args
                .temp_location else template_args.staging_location,
                stagingLocation=template_args.staging_location,
                kmsKeyName=template_args.kms_key_name,
                ipConfiguration=ip_configuration,
                workerRegion=template_args.worker_region,
                workerZone=template_args.worker_zone,
                enableStreamingEngine=template_args.enable_streaming_engine,
                flexrsGoal=flexrs_goal,
                additionalExperiments=(
                    template_args.additional_experiments if template_args
                    .additional_experiments else []),
                additionalUserLabels=Templates.FLEX_TEMPLATE_USER_LABELS_VALUE(
                    additionalProperties=user_labels_list
                ) if user_labels_list else None),
            update=streaming_update,
            transformNameMappings=transform_mappings,
            parameters=Templates.FLEX_TEMPLATE_PARAMETERS_VALUE(
                additionalProperties=params_list) if params_list else None))
    request = GetMessagesModule(
    ).DataflowProjectsLocationsFlexTemplatesLaunchRequest(
        projectId=template_args.project_id or GetProject(),
        location=region_id,
        launchFlexTemplateRequest=body)
    try:
      return Templates.GetFlexTemplateService().Launch(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class Messages:
  """The Messages set of Dataflow API functions."""

  LIST_REQUEST = GetMessagesModule(
  ).DataflowProjectsLocationsJobsMessagesListRequest

  @staticmethod
  def GetService():
    return GetClientInstance().projects_locations_jobs_messages

  @staticmethod
  def List(job_id,
           project_id=None,
           region_id=None,
           minimum_importance=None,
           start_time=None,
           end_time=None,
           page_size=None,
           page_token=None):
    """Calls the Dataflow Metrics.Get method.

    Args:
      job_id: The job to get messages about.
      project_id: The project which owns the job.
      region_id: The regional endpoint of the job.
      minimum_importance: Filter to only get messages with importance >= level
      start_time: If specified, return only messages with timestamps >=
        start_time. The default is the job creation time (i.e. beginning of
        messages).
      end_time: Return only messages with timestamps < end_time. The default is
        now (i.e. return up to the latest messages available).
      page_size: If specified, determines the maximum number of messages to
        return.  If unspecified, the service may choose an appropriate default,
        or may return an arbitrarily large number of results.
      page_token: If supplied, this should be the value of next_page_token
        returned by an earlier call. This will cause the next page of results to
        be returned.

    Returns:
      (ListJobMessagesResponse)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    request = GetMessagesModule(
    ).DataflowProjectsLocationsJobsMessagesListRequest(
        jobId=job_id,
        location=region_id,
        projectId=project_id,
        startTime=start_time,
        endTime=end_time,
        minimumImportance=minimum_importance,
        pageSize=page_size,
        pageToken=page_token)
    try:
      return Messages.GetService().List(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)


class Snapshots:
  """Cloud Dataflow snapshots api."""

  @staticmethod
  def GetService():
    return GetClientInstance().projects_locations_snapshots

  @staticmethod
  def Delete(snapshot_id=None, project_id=None, region_id=None):
    """Calls the Dataflow Snapshots.Delete method.

    Args:
      snapshot_id: The id of the snapshot to delete.
      project_id: The project that owns the snapshot.
      region_id: The regional endpoint of the snapshot.

    Returns:
      (DeleteSnapshotResponse)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    request = GetMessagesModule(
    ).DataflowProjectsLocationsSnapshotsDeleteRequest(
        snapshotId=snapshot_id, location=region_id, projectId=project_id)
    try:
      return Snapshots.GetService().Delete(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def Get(snapshot_id=None, project_id=None, region_id=None):
    """Calls the Dataflow Snapshots.Get method.

    Args:
      snapshot_id: The id of the snapshot to get.
      project_id: The project that owns the snapshot.
      region_id: The regional endpoint of the snapshot.

    Returns:
      (GetSnapshotResponse)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    request = GetMessagesModule().DataflowProjectsLocationsSnapshotsGetRequest(
        snapshotId=snapshot_id, location=region_id, projectId=project_id)
    try:
      return Snapshots.GetService().Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

  @staticmethod
  def List(job_id=None, project_id=None, region_id=None):
    """Calls the Dataflow Snapshots.List method.

    Args:
      job_id: If specified, only snapshots associated with the job will be
        returned.
      project_id: The project that owns the snapshot.
      region_id: The regional endpoint of the snapshot.

    Returns:
      (ListSnapshotsResponse)
    """
    project_id = project_id or GetProject()
    # TODO(b/139889563): Remove default when args region is changed to required
    region_id = region_id or DATAFLOW_API_DEFAULT_REGION
    request = GetMessagesModule().DataflowProjectsLocationsSnapshotsListRequest(
        jobId=job_id, location=region_id, projectId=project_id)
    try:
      return Snapshots.GetService().List(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)
