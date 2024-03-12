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
"""Data Pipelines API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import six

_DEFAULT_API_VERSION = 'v1'


def GetMessagesModule(api_version=_DEFAULT_API_VERSION):
  return apis.GetMessagesModule('datapipelines', api_version)


def GetClientInstance(api_version=_DEFAULT_API_VERSION):
  return apis.GetClientInstance('datapipelines', api_version)


def GetPipelineURI(resource):
  pipeline = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='datapipelines.pipelines')
  return pipeline.SelfLink()


def GetJobURI(resource):
  job = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='datapipelines.pipelines.jobs')
  return job.SelfLink()


class PipelinesClient(object):
  """Client for Pipelines for the Data Pipelines API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule()
    self._service = self.client.projects_locations_pipelines

  def Describe(self, pipeline):
    """Describe a Pipeline in the given project and region.

    Args:
      pipeline: str, the name for the Pipeline being described.

    Returns:
      Described Pipeline Resource.
    """
    describe_req = self.messages.DatapipelinesProjectsLocationsPipelinesGetRequest(
        name=pipeline)
    return self._service.Get(describe_req)

  def Delete(self, pipeline):
    """Delete a Pipeline in the given project and region.

    Args:
      pipeline: str, the name for the Pipeline being described.

    Returns:
      Empty Response.
    """
    delete_req = self.messages.DatapipelinesProjectsLocationsPipelinesDeleteRequest(
        name=pipeline)
    return self._service.Delete(delete_req)

  def Stop(self, pipeline):
    """Stop a Pipeline in the given project and region.

    Args:
      pipeline: str, the name for the Pipeline being described.

    Returns:
      Pipeline resource.
    """
    stop_req = self.messages.DatapipelinesProjectsLocationsPipelinesStopRequest(
        name=pipeline)
    return self._service.Stop(stop_req)

  def Run(self, pipeline):
    """Run a Pipeline in the given project and region.

    Args:
      pipeline: str, the name for the Pipeline being described.

    Returns:
      Job resource which was created.
    """
    stop_req = self.messages.DatapipelinesProjectsLocationsPipelinesRunRequest(
        name=pipeline)
    return self._service.Run(stop_req)

  def List(self, limit=None, page_size=50, input_filter='', region=''):
    """List Pipelines for the given project and region.

    Args:
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).
      input_filter: string, optional filter to pass, eg:
        "type:BATCH,status:ALL", to filter out the pipelines based on staus or
        type.
      region: string, relative name to the region.

    Returns:
      Generator of matching devices.
    """
    list_req = self.messages.DatapipelinesProjectsLocationsPipelinesListRequest(
        filter=input_filter, parent=region)
    return list_pager.YieldFromList(
        self.client.projects_locations_pipelines,
        list_req,
        field='pipelines',
        method='List',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize')

  def CreateLegacyTemplateRequest(self, args):
    """Create a Legacy Template request for the Pipeline workload.

    Args:
      args: Any, list of args needed to create a Pipeline.

    Returns:
      Legacy Template request.
    """
    location = args.region
    project_id = properties.VALUES.core.project.Get(required=True)
    params_list = self.ConvertDictArguments(
        args.parameters, self.messages
        .GoogleCloudDatapipelinesV1LaunchTemplateParameters.ParametersValue)

    transform_mapping_list = self.ConvertDictArguments(
        args.transform_name_mappings,
        self.messages.GoogleCloudDatapipelinesV1LaunchTemplateParameters
        .TransformNameMappingValue)
    transform_name_mappings = None
    if transform_mapping_list:
      transform_name_mappings = self.messages.GoogleCloudDatapipelinesV1LaunchTemplateParameters.TransformNameMappingValue(
          additionalProperties=transform_mapping_list)

    ip_private = self.messages.GoogleCloudDatapipelinesV1RuntimeEnvironment.IpConfigurationValueValuesEnum.WORKER_IP_PRIVATE
    ip_configuration = ip_private if args.disable_public_ips else None

    user_labels_list = self.ConvertDictArguments(
        args.additional_user_labels, self.messages
        .GoogleCloudDatapipelinesV1RuntimeEnvironment.AdditionalUserLabelsValue)
    additional_user_labels = None
    if user_labels_list:
      additional_user_labels = self.messages.GoogleCloudDatapipelinesV1RuntimeEnvironment.AdditionalUserLabelsValue(
          additionalProperties=user_labels_list)

    launch_parameter = self.messages.GoogleCloudDatapipelinesV1LaunchTemplateParameters(
        environment=self.messages.GoogleCloudDatapipelinesV1RuntimeEnvironment(
            serviceAccountEmail=args.dataflow_service_account_email,
            maxWorkers=args.max_workers,
            numWorkers=args.num_workers,
            network=args.network,
            subnetwork=args.subnetwork,
            machineType=args.worker_machine_type,
            tempLocation=args.temp_location,
            kmsKeyName=args.dataflow_kms_key,
            ipConfiguration=ip_configuration,
            workerRegion=args.worker_region,
            workerZone=args.worker_zone,
            enableStreamingEngine=args.enable_streaming_engine,
            additionalExperiments=(args.additional_experiments
                                   if args.additional_experiments else []),
            additionalUserLabels=additional_user_labels),
        update=args.update,
        parameters=self.messages
        .GoogleCloudDatapipelinesV1LaunchTemplateParameters.ParametersValue(
            additionalProperties=params_list) if params_list else None,
        transformNameMapping=transform_name_mappings)
    return self.messages.GoogleCloudDatapipelinesV1LaunchTemplateRequest(
        gcsPath=args.template_file_gcs_location,
        location=location,
        projectId=project_id,
        launchParameters=launch_parameter)

  def CreateFlexTemplateRequest(self, args):
    """Create a Flex Template request for the Pipeline workload.

    Args:
      args: Any, list of args needed to create a Pipeline.

    Returns:
      Flex Template request.
    """
    location = args.region
    project_id = properties.VALUES.core.project.Get(required=True)
    params_list = self.ConvertDictArguments(
        args.parameters, self.messages
        .GoogleCloudDatapipelinesV1LaunchFlexTemplateParameter.ParametersValue)

    transform_mapping_list = self.ConvertDictArguments(
        args.transform_name_mappings,
        self.messages.GoogleCloudDatapipelinesV1LaunchFlexTemplateParameter
        .TransformNameMappingsValue)
    transform_name_mappings = None
    if transform_mapping_list:
      transform_name_mappings = self.messages.GoogleCloudDatapipelinesV1LaunchFlexTemplateParameter.TransformNameMappingsValue(
          additionalProperties=transform_mapping_list)

    ip_private = self.messages.GoogleCloudDatapipelinesV1FlexTemplateRuntimeEnvironment.IpConfigurationValueValuesEnum.WORKER_IP_PRIVATE
    ip_configuration = ip_private if args.disable_public_ips else None

    user_labels_list = self.ConvertDictArguments(
        args.additional_user_labels,
        self.messages.GoogleCloudDatapipelinesV1FlexTemplateRuntimeEnvironment
        .AdditionalUserLabelsValue)
    additional_user_labels = None
    if user_labels_list:
      additional_user_labels = self.messages.GoogleCloudDatapipelinesV1FlexTemplateRuntimeEnvironment.AdditionalUserLabelsValue(
          additionalProperties=user_labels_list)

    flexrs_goal = None
    if args.flexrs_goal:
      if args.flexrs_goal == 'SPEED_OPTIMIZED':
        flexrs_goal = self.messages.GoogleCloudDatapipelinesV1FlexTemplateRuntimeEnvironment.FlexrsGoalValueValuesEnum.FLEXRS_SPEED_OPTIMIZED
      elif args.flexrs_goal == 'COST_OPTIMIZED':
        flexrs_goal = self.messages.GoogleCloudDatapipelinesV1FlexTemplateRuntimeEnvironment.FlexrsGoalValueValuesEnum.FLEXRS_COST_OPTIMIZED

    launch_parameter = self.messages.GoogleCloudDatapipelinesV1LaunchFlexTemplateParameter(
        containerSpecGcsPath=args.template_file_gcs_location,
        environment=self.messages
        .GoogleCloudDatapipelinesV1FlexTemplateRuntimeEnvironment(
            serviceAccountEmail=args.dataflow_service_account_email,
            maxWorkers=args.max_workers,
            numWorkers=args.num_workers,
            network=args.network,
            subnetwork=args.subnetwork,
            machineType=args.worker_machine_type,
            tempLocation=args.temp_location,
            kmsKeyName=args.dataflow_kms_key,
            ipConfiguration=ip_configuration,
            workerRegion=args.worker_region,
            workerZone=args.worker_zone,
            enableStreamingEngine=args.enable_streaming_engine,
            flexrsGoal=flexrs_goal,
            additionalExperiments=(args.additional_experiments
                                   if args.additional_experiments else []),
            additionalUserLabels=additional_user_labels),
        update=args.update,
        parameters=self.messages
        .GoogleCloudDatapipelinesV1LaunchFlexTemplateParameter.ParametersValue(
            additionalProperties=params_list) if params_list else None,
        transformNameMappings=transform_name_mappings)
    return self.messages.GoogleCloudDatapipelinesV1LaunchFlexTemplateRequest(
        location=location,
        projectId=project_id,
        launchParameter=launch_parameter)

  def Create(self, pipeline, parent, args):
    """Create a Pipeline in the given project and region.

    Args:
      pipeline: str, the name for the Pipeline being created.
      parent: str, relative name to the region.
      args: Any, list of args needed to create a Pipeline.

    Returns:
      Pipeline resource.
    """
    if args.pipeline_type == 'streaming':
      pipeline_type = self.messages.GoogleCloudDatapipelinesV1Pipeline.TypeValueValuesEnum(
          self.messages.GoogleCloudDatapipelinesV1Pipeline.TypeValueValuesEnum
          .PIPELINE_TYPE_STREAMING)
    else:
      pipeline_type = self.messages.GoogleCloudDatapipelinesV1Pipeline.TypeValueValuesEnum(
          self.messages.GoogleCloudDatapipelinesV1Pipeline.TypeValueValuesEnum
          .PIPELINE_TYPE_BATCH)

    schedule_info = self.messages.GoogleCloudDatapipelinesV1ScheduleSpec(
        schedule=args.schedule, timeZone=args.time_zone)

    if args.template_type == 'classic':
      legacy_template_request = self.CreateLegacyTemplateRequest(args)
      workload = self.messages.GoogleCloudDatapipelinesV1Workload(
          dataflowLaunchTemplateRequest=legacy_template_request)
    else:
      flex_template_request = self.CreateFlexTemplateRequest(args)
      workload = self.messages.GoogleCloudDatapipelinesV1Workload(
          dataflowFlexTemplateRequest=flex_template_request)

    if args.display_name:
      display_name = args.display_name
    else:
      display_name = pipeline.rsplit('/', 1)[-1]
    pipeline_spec = self.messages.GoogleCloudDatapipelinesV1Pipeline(
        name=pipeline,
        displayName=display_name,
        type=pipeline_type,
        scheduleInfo=schedule_info,
        workload=workload)

    create_req = self.messages.DatapipelinesProjectsLocationsPipelinesCreateRequest(
        googleCloudDatapipelinesV1Pipeline=pipeline_spec, parent=parent)
    return self._service.Create(create_req)

  def WorkloadUpdateMask(self, template_type, args):
    """Given a set of args for the workload, create the required update mask.

    Args:
      template_type: str, the type of the pipeline.
      args: Any, object with args needed for updating a pipeline.

    Returns:
      Update mask.
    """
    update_mask = []
    if template_type == 'flex':
      prefix_string = 'workload.dataflow_flex_template_request.launch_parameter.'
    else:
      prefix_string = 'workload.dataflow_launch_template_request.launch_parameters.'

    if args.template_file_gcs_location:
      if template_type == 'flex':
        update_mask.append(prefix_string + 'container_spec_gcs_path')
      else:
        update_mask.append('workload.dataflow_launch_template_request.gcs_path')

    if args.parameters:
      update_mask.append(prefix_string + 'parameters')

    if args.update:
      update_mask.append(prefix_string + 'update')

    if args.transform_name_mappings:
      if template_type == 'flex':
        update_mask.append(prefix_string + 'transform_name_mappings')
      else:
        update_mask.append(prefix_string + 'transform_name_mapping')

    if args.max_workers:
      update_mask.append(prefix_string + 'environment.max_workers')

    if args.num_workers:
      update_mask.append(prefix_string + 'environment.num_workers')

    if args.dataflow_service_account_email:
      update_mask.append(prefix_string + 'environment.service_account_email')

    if args.temp_location:
      update_mask.append(prefix_string + 'environment.temp_location')

    if args.network:
      update_mask.append(prefix_string + 'environment.network')

    if args.subnetwork:
      update_mask.append(prefix_string + 'environment.subnetwork')

    if args.worker_machine_type:
      update_mask.append(prefix_string + 'environment.machine_type')

    if args.dataflow_kms_key:
      update_mask.append(prefix_string + 'environment.kms_key_name')

    if args.disable_public_ips:
      update_mask.append(prefix_string + 'environment.ip_configuration')

    if args.worker_region:
      update_mask.append(prefix_string + 'environment.worker_region')

    if args.worker_zone:
      update_mask.append(prefix_string + 'environment.worker_zone')

    if args.enable_streaming_engine:
      update_mask.append(prefix_string + 'environment.enable_streaming_engine')

    if args.flexrs_goal:
      if template_type == 'flex':
        update_mask.append(prefix_string + 'environment.flexrs_goal')

    if args.additional_user_labels:
      update_mask.append(prefix_string + 'environment.additional_user_labels')

    if args.additional_experiments:
      update_mask.append(prefix_string + 'environment.additional_experiments')

    return update_mask

  def Patch(self, pipeline, args):
    """Update a Pipeline in the given project and region.

    Args:
      pipeline: str, the name for the Pipeline being updated.
      args: Any, object with args needed to update a Pipeline.

    Returns:
      Pipeline resource.
    """

    update_mask = []
    schedule_info = None
    if args.schedule or args.time_zone:
      schedule, time_zone = None, None
      if args.schedule:
        schedule = args.schedule
        update_mask.append('schedule_info.schedule')
      if args.time_zone:
        time_zone = args.time_zone
        update_mask.append('schedule_info.time_zone')
      schedule_info = self.messages.GoogleCloudDatapipelinesV1ScheduleSpec(
          schedule=schedule, timeZone=time_zone)

    if args.display_name:
      update_mask.append('display_name')

    if args.template_type == 'classic':
      update_mask += self.WorkloadUpdateMask('classic', args)
      legacy_template_request = self.CreateLegacyTemplateRequest(args)
      workload = self.messages.GoogleCloudDatapipelinesV1Workload(
          dataflowLaunchTemplateRequest=legacy_template_request)
    else:
      update_mask += self.WorkloadUpdateMask('flex', args)
      flex_template_request = self.CreateFlexTemplateRequest(args)
      workload = self.messages.GoogleCloudDatapipelinesV1Workload(
          dataflowFlexTemplateRequest=flex_template_request)

    pipeline_spec = self.messages.GoogleCloudDatapipelinesV1Pipeline(
        name=pipeline,
        displayName=args.display_name,
        scheduleInfo=schedule_info,
        workload=workload)

    update_req = self.messages.DatapipelinesProjectsLocationsPipelinesPatchRequest(
        googleCloudDatapipelinesV1Pipeline=pipeline_spec,
        name=pipeline,
        updateMask=','.join(update_mask))
    return self._service.Patch(update_req)

  def ConvertDictArguments(self, arguments, value_message):
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


class JobsClient(object):
  """Client used for interacting with job related service from the Data Pipelines API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule()
    self._service = self.client.projects_locations_pipelines_jobs

  def List(self, limit=None, page_size=50, pipeline=''):
    """Make API calls to list jobs for pipelines.

    Args:
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).
      pipeline: string, the name of the pipeline to list jobs for.

    Returns:
      Generator that yields jobs.
    """
    list_req = self.messages.DatapipelinesProjectsLocationsPipelinesJobsListRequest(
        parent=pipeline)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='jobs',
        method='List',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize')
