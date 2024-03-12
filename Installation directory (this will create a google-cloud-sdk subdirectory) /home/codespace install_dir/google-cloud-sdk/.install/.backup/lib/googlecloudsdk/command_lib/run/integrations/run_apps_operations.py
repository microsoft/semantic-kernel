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
"""Allows you to write surfaces in terms of logical RunApps operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import datetime
import json
from typing import List, MutableSequence, Optional

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.run.integrations import api_utils
from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.api_lib.run.integrations import validator
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as run_flags
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import integration_list_printer
from googlecloudsdk.command_lib.run.integrations import messages_util
from googlecloudsdk.command_lib.run.integrations import stages
from googlecloudsdk.command_lib.run.integrations import typekits_util
from googlecloudsdk.command_lib.run.integrations.typekits import base
from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages
import six


types_utils.SERVICE_TYPE = 'service'

_DEFAULT_APP_NAME = 'default'

ALL_REGIONS = '-'

_RUN_APPS_API_NAME = 'runapps'
_RUN_APPS_API_VERSION = 'v1alpha1'


@contextlib.contextmanager
def Connect(args, release_track):
  """Provide a RunAppsOperations instance to use.

  Arguments:
    args: Namespace, the args namespace.
    release_track: the release track of the command.

  Yields:
    A RunAppsOperations instance.
  """
  # pylint: disable=protected-access
  client = apis.GetClientInstance(_RUN_APPS_API_NAME, _RUN_APPS_API_VERSION)

  region = run_flags.GetRegion(args, prompt=True)
  service_account = flags.GetServiceAccount(args)
  if not region:
    raise exceptions.ArgumentError(
        'You must specify a region. Either use the `--region` flag '
        'or set the run/region property.'
    )
  yield RunAppsOperations(
      client,
      _RUN_APPS_API_VERSION,
      region,
      release_track,
      service_account,
  )


def _HandleQueueingException(err):
  """Reraises the error if with better message if it's a queueing error.

  Args:
    err: the exception to be handled.

  Raises:
    exceptions.IntegrationsOperationError: this is a queueing error.
  """
  content = json.loads(err.content)
  msg = content['error']['message']
  code = content['error']['code']
  if msg == 'unable to queue the operation' and code == 409:
    raise exceptions.IntegrationsOperationError(
        'An integration is currently being configured.  Please wait '
        + 'until the current process is complete and try again'
    )
  raise err


class RunAppsOperations(object):
  """Client used by Cloud Run Integrations to communicate with the API."""

  def __init__(
      self, client, api_version, region, release_track, service_account
  ):
    """Inits RunAppsOperations with given API clients.

    Args:
      client: The API client for interacting with RunApps APIs.
      api_version: Version of resources & clients (v1alpha1, v1beta1)
      region: str, The region of the control plane.
      release_track: the release track of the command.
      service_account: the service account to use for any deployments.
    """

    self._client = client
    self._api_version = api_version
    self._region = region
    self._release_track = release_track
    self._service_account = service_account

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._client.MESSAGES_MODULE

  @property
  def region(self):
    return self._region

  def ApplyYaml(self, yaml_content: str):
    """Applies the application config from yaml file.

    Args:
      yaml_content: content of the yaml file.
    """
    app_dict = dict(yaml_content)
    name = _DEFAULT_APP_NAME
    if 'name' in app_dict:
      name = app_dict.pop('name')
    appconfig = runapps_v1alpha1_messages.Config(
        config=yaml.dump(yaml_content).encode('utf-8')
    )
    match_type_names = []
    vpc = False

    # try the canonical manifest
    for r in app_dict.get('resources', {}):
      res_id = r.get('id', '')
      parts = res_id.split('/')
      if len(parts) != 2:
        continue
      match_type_names.append({'type': parts[0], 'name': parts[1]})
      if parts[0] == 'redis':
        vpc = True

    if vpc:
      match_type_names.append({'type': 'vpc', 'name': '*'})
    match_type_names.sort(key=lambda x: x['type'])

    all_types = map(lambda x: x['type'], match_type_names)
    validator.CheckApiEnablements(all_types)

    resource_stages = base.GetComponentTypesFromSelectors(
        selectors=match_type_names
    )
    stages_map = stages.ApplyStages(resource_stages)

    def StatusUpdate(tracker, operation, unused_status):
      self._UpdateDeploymentTracker(tracker, operation, stages_map)
      return

    with progress_tracker.StagedProgressTracker(
        'Applying Configuration...',
        stages_map.values(),
        failure_message='Failed to apply configuration.',
    ) as tracker:
      self.ApplyAppConfig(
          tracker=tracker,
          tracker_update_func=StatusUpdate,
          appname=name,
          appconfig=appconfig,
          match_type_names=match_type_names,
      )

  def ApplyAppConfig(
      self,
      tracker,
      appname: str,
      appconfig: runapps_v1alpha1_messages.Config,
      integration_name=None,
      deploy_message=None,
      match_type_names=None,
      intermediate_step=False,
      etag=None,
      tracker_update_func=None,
  ):
    """Applies the application config.

    Args:
      tracker: StagedProgressTracker, to report on the progress.
      appname:  name of the application.
      appconfig: config of the application.
      integration_name: name of the integration that's being updated.
      deploy_message: message to display when deployment in progress.
      match_type_names: array of type/name pairs used for create selector.
      intermediate_step: bool of whether this is an intermediate step.
      etag: the etag of the application if it's an incremental patch.
      tracker_update_func: optional custom fn to update the tracker.
    """
    tracker.StartStage(stages.UPDATE_APPLICATION)
    if integration_name:
      tracker.UpdateStage(
          stages.UPDATE_APPLICATION,
          messages_util.CheckStatusMessage(
              self._release_track, integration_name
          ),
      )
    try:
      self._UpdateApplication(appname, appconfig, etag)
    except api_exceptions.HttpConflictError as err:
      _HandleQueueingException(err)
    except exceptions.IntegrationsOperationError as err:
      tracker.FailStage(stages.UPDATE_APPLICATION, err)
    else:
      tracker.CompleteStage(stages.UPDATE_APPLICATION)

    if match_type_names is None:
      match_type_names = [{'type': '*', 'name': '*'}]
    create_selector = {'matchTypeNames': match_type_names}

    if not intermediate_step:
      tracker.UpdateHeaderMessage(
          'Deployment started. This process will continue even if '
          'your terminal session is interrupted.'
      )
    tracker.StartStage(stages.CREATE_DEPLOYMENT)
    if deploy_message:
      tracker.UpdateStage(stages.CREATE_DEPLOYMENT, deploy_message)
    try:
      self._CreateDeployment(
          appname,
          tracker,
          tracker_update_func=tracker_update_func,
          create_selector=create_selector,
      )
    except api_exceptions.HttpConflictError as err:
      _HandleQueueingException(err)
    except exceptions.IntegrationsOperationError as err:
      tracker.FailStage(stages.CREATE_DEPLOYMENT, err)
    else:
      tracker.UpdateStage(stages.CREATE_DEPLOYMENT, '')
      tracker.CompleteStage(stages.CREATE_DEPLOYMENT)

    tracker.UpdateHeaderMessage('Done.')

  def _UpdateApplication(
      self, appname: str, appconfig: runapps_v1alpha1_messages.Config, etag: str
  ):
    """Update Application config, waits for operation to finish.

    Args:
      appname:  name of the application.
      appconfig: config of the application.
      etag: the etag of the application if it's an incremental patch.
    """
    app_ref = self.GetAppRef(appname)
    application = self.messages.Application(
        name=appname, config=appconfig, etag=etag
    )
    is_patch = etag or api_utils.GetApplication(self._client, app_ref)
    if is_patch:
      operation = api_utils.PatchApplication(self._client, app_ref, application)
    else:
      operation = api_utils.CreateApplication(
          self._client, app_ref, application
      )
    api_utils.WaitForApplicationOperation(self._client, operation)

  def _CreateDeployment(
      self,
      appname,
      tracker,
      tracker_update_func=None,
      create_selector=None,
      delete_selector=None,
  ):
    """Create a deployment, waits for operation to finish.

    Args:
      appname:  name of the application.
      tracker: The ProgressTracker to track the deployment operation.
      tracker_update_func: optional custom fn to update the tracker.
      create_selector: create selector for the deployment.
      delete_selector: delete selector for the deployment.
    """
    app_ref = self.GetAppRef(appname)
    deployment_name = self._GetDeploymentName(app_ref.Name())
    # TODO(b/217573594): remove this when oneof constraint is removed.
    if create_selector and delete_selector:
      raise exceptions.ArgumentError(
          'create_selector and delete_selector '
          'cannot be specified at the same time.'
      )
    deployment = self.messages.Deployment(
        name=deployment_name,
        createSelector=create_selector,
        deleteSelector=delete_selector,
        serviceAccount=self._service_account,
    )
    deployment_ops = api_utils.CreateDeployment(
        self._client, app_ref, deployment
    )

    dep_response = api_utils.WaitForDeploymentOperation(
        self._client,
        deployment_ops,
        tracker,
        tracker_update_func=tracker_update_func,
    )
    self.CheckDeploymentState(dep_response)

  def _GetDeploymentName(self, appname):
    return '{}-{}'.format(
        appname, datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    )

  @staticmethod
  def _UpdateDeploymentTracker(tracker, operation, tracker_stages):
    """Updates deployment tracker with the current status of operation.

    Args:
      tracker: The ProgressTracker to track the deployment operation.
      operation: run_apps.v1alpha1.operation object for the deployment.
      tracker_stages: map of stages with key as stage key (string) and value is
        the progress_tracker.Stage.
    """

    messages = api_utils.GetMessages()
    metadata = api_utils.GetDeploymentOperationMetadata(messages, operation)
    resources_in_progress = []
    resources_completed = []
    resource_state = messages.ResourceDeploymentStatus.StateValueValuesEnum

    if metadata.resourceStatus is not None:
      for resource in metadata.resourceStatus:
        stage_name = stages.StageKeyForResourceDeployment(resource.name.type)
        if resource.state == resource_state.RUNNING:
          resources_in_progress.append(stage_name)
        if resource.state == resource_state.FINISHED:
          resources_completed.append(stage_name)

    for resource in resources_in_progress:
      if resource in tracker_stages and tracker.IsWaiting(resource):
        tracker.StartStage(resource)

    for resource in resources_completed:
      if resource in tracker_stages and tracker.IsRunning(resource):
        tracker.CompleteStage(resource)
    tracker.Tick()

  def GetIntegrationGeneric(
      self,
      name: str,
      res_type: Optional[str] = None,
  ) -> Optional[runapps_v1alpha1_messages.Resource]:
    """Get an integration.

    Args:
      name: the name of the resource.
      res_type: type of the resource. If empty, will match any type.

    Raises:
      IntegrationNotFoundError: If the integration is not found.

    Returns:
      The integration config.
    """
    appconfig = self.GetDefaultApp().config
    res = self._FindResource(appconfig, name, res_type)
    if res:
      return res
    raise exceptions.IntegrationNotFoundError(
        'Integration [{}] cannot be found'.format(name)
    )

  def _FindResource(
      self,
      appconfig: runapps_v1alpha1_messages.Config,
      name: str,
      res_type: Optional[str] = None,
  ) -> Optional[runapps_v1alpha1_messages.Resource]:
    for res in appconfig.resourceList:
      if res.id.name == name and (not res_type or res.id.type == res_type):
        return res
    return None

  def GetIntegrationStatus(
      self, res_id: runapps_v1alpha1_messages.ResourceID
  ) -> Optional[runapps_v1alpha1_messages.ResourceStatus]:
    """Get status of an integration.

    Args:
      res_id: ResourceID of the resource.

    Returns:
      The ResourceStatus of the integration, or None if not found
    """
    try:
      app_status = api_utils.GetApplicationStatus(
          self._client, self.GetAppRef(_DEFAULT_APP_NAME), [res_id]
      )
      if app_status:
        for s in app_status.resourceStatuses:
          if s.id == res_id:
            return s
      return None
    except api_exceptions.HttpError:
      return None

  def GetLatestDeployment(
      self, resource: runapps_v1alpha1_messages.Resource
  ) -> Optional[runapps_v1alpha1_messages.Deployment]:
    """Fetches the deployment object given a resource config.

    Args:
      resource: the resource object.

    Returns:
      run_apps.v1alpha1.Deployment, the Deployment object.  This is None if
        the latest deployment name does not exist.  If the deployment itself
        cannot be found via the name or any http errors occur, then None will
        be returned.
    """
    if not resource.latestDeployment:
      return None

    try:
      return api_utils.GetDeployment(self._client, resource.latestDeployment)
    except api_exceptions.HttpError:
      return None

  def CreateIntegration(self, integration_type, parameters, service, name=None):
    """Create an integration.

    Args:
      integration_type:  type of the integration.
      parameters: parameter dictionary from args.
      service: the service to attach to the new integration.
      name: name of the integration, if empty, a defalt one will be generated.

    Returns:
      The name of the integration.
    """
    app = self.GetDefaultApp()
    typekit = typekits_util.GetTypeKit(integration_type)
    if name and typekit.is_singleton:
      raise exceptions.ArgumentError(
          '--name is not allowed for integration type [{}].'.format(
              integration_type
          )
      )
    if not name:
      name = typekit.NewIntegrationName(app.config)

    resource_type = typekit.resource_type

    if self._FindResource(app.config, name, resource_type):
      raise exceptions.ArgumentError(
          messages_util.IntegrationAlreadyExists(name)
      )

    resource = runapps_v1alpha1_messages.Resource(
        id=runapps_v1alpha1_messages.ResourceID(name=name, type=resource_type)
    )
    services_in_params = typekit.UpdateResourceConfig(parameters, resource)

    app.config.resourceList.append(resource)

    match_type_names = typekit.GetCreateSelectors(name)
    services = [service] if service else []
    services.extend(services_in_params)
    for svc in services:
      match_type_names.append({
          'type': types_utils.SERVICE_TYPE,
          'name': svc,
          'ignoreResourceConfig': True,
      })

    for svc in services:
      self.EnsureWorkloadResources(app.config, svc, types_utils.SERVICE_TYPE)
    self.CheckCloudRunServicesExistence(services)

    if service:
      workload = self._FindResource(
          app.config, service, types_utils.SERVICE_TYPE
      )
      typekit.BindServiceToIntegration(
          integration=resource,
          workload=workload,
      )

    resource_stages = typekit.GetCreateComponentTypes(
        selectors=match_type_names
    )

    deploy_message = typekit.GetDeployMessage(create=True)
    stages_map = stages.IntegrationStages(
        create=True, resource_types=resource_stages
    )

    def StatusUpdate(tracker, operation, unused_status):
      self._UpdateDeploymentTracker(tracker, operation, stages_map)
      return

    with progress_tracker.StagedProgressTracker(
        'Creating new Integration...',
        stages_map.values(),
        failure_message='Failed to create new integration.',
    ) as tracker:
      try:
        self.ApplyAppConfig(
            tracker=tracker,
            tracker_update_func=StatusUpdate,
            appname=_DEFAULT_APP_NAME,
            appconfig=app.config,
            integration_name=name,
            deploy_message=deploy_message,
            match_type_names=match_type_names,
            etag=app.etag,
        )
      except exceptions.IntegrationsOperationError as err:
        tracker.AddWarning(
            messages_util.RetryDeploymentMessage(self._release_track, name)
        )
        raise err

    return name

  def UpdateIntegration(
      self, name, parameters, add_service=None, remove_service=None
  ):
    """Update an integration.

    Args:
      name:  str, the name of the resource to update.
      parameters: dict, the parameters from args.
      add_service: the service to attach to the integration.
      remove_service: the service to remove from the integration.

    Raises:
      IntegrationNotFoundError: If the integration is not found.

    Returns:
      The name of the integration.
    """
    app = self.GetDefaultApp()
    existing_resource = self._FindResource(app.config, name)
    if existing_resource is None:
      raise exceptions.IntegrationNotFoundError(
          messages_util.IntegrationNotFound(name)
      )

    typekit = typekits_util.GetTypeKitByResource(existing_resource)

    flags.ValidateUpdateParameters(typekit.integration_type, parameters)

    specified_services = []
    services_in_params = typekit.UpdateResourceConfig(
        parameters, existing_resource
    )
    if services_in_params:
      specified_services.extend(services_in_params)
    if add_service:
      specified_services.append(add_service)

    match_type_names = typekit.GetCreateSelectors(name)

    for service in specified_services:
      self.EnsureWorkloadResources(
          app.config, service, types_utils.SERVICE_TYPE
      )
      # Specified services are always added to selector.
      self._AppendTypeMatcher(
          match_type_names,
          types_utils.SERVICE_TYPE,
          service,
          True,
      )

    if add_service:
      workload = self._FindResource(
          app.config, add_service, types_utils.SERVICE_TYPE
      )
      typekit.BindServiceToIntegration(
          integration=existing_resource,
          workload=workload,
      )

    if remove_service:
      workload_res = self._FindResource(
          app.config, remove_service, types_utils.SERVICE_TYPE
      )
      if workload_res:
        typekit.UnbindServiceFromIntegration(
            integration=existing_resource,
            workload=workload_res,
        )
        if self.GetCloudRunService(remove_service):
          # remove_service missing will not lead to failure.
          # only add it to selector if it exists.
          self._AppendTypeMatcher(
              match_type_names, types_utils.SERVICE_TYPE, remove_service
          )
      else:
        raise exceptions.ServiceNotFoundError(
            'Service [{}] is not found among integrations'.format(
                remove_service
            )
        )

    if specified_services:
      self.CheckCloudRunServicesExistence(specified_services)

    if typekit.is_ingress_service or (
        typekit.is_backing_service
        and add_service is None
        and remove_service is None
    ):
      ref_svcs = typekit.GetBindedWorkloads(
          existing_resource, app.config.resourceList, types_utils.SERVICE_TYPE
      )
      for service in ref_svcs:
        if service not in specified_services and self.GetCloudRunService(
            service
        ):
          # Non-specified services are only added to selector if it exists.
          self._AppendTypeMatcher(
              match_type_names, types_utils.SERVICE_TYPE, service, True
          )

    deploy_message = typekit.GetDeployMessage()

    resource_stages = typekit.GetCreateComponentTypes(
        selectors=match_type_names
    )
    stages_map = stages.IntegrationStages(
        create=False, resource_types=resource_stages
    )

    def StatusUpdate(tracker, operation, unused_status):
      self._UpdateDeploymentTracker(tracker, operation, stages_map)
      return

    with progress_tracker.StagedProgressTracker(
        'Updating Integration...',
        stages_map.values(),
        failure_message='Failed to update integration.',
    ) as tracker:
      return self.ApplyAppConfig(
          tracker=tracker,
          tracker_update_func=StatusUpdate,
          appname=_DEFAULT_APP_NAME,
          appconfig=app.config,
          integration_name=name,
          deploy_message=deploy_message,
          match_type_names=match_type_names,
          etag=app.etag,
      )

  def DeleteIntegration(self, name):
    """Delete an integration.

    Args:
      name:  str, the name of the resource to update.

    Raises:
      IntegrationNotFoundError: If the integration is not found.

    Returns:
      str, the type of the integration that is deleted.
    """
    app = self.GetDefaultApp()
    resource = self._FindResource(app.config, name)
    if resource is None:
      raise exceptions.IntegrationNotFoundError(
          'Integration [{}] cannot be found'.format(name)
      )
    try:
      typekit = typekits_util.GetTypeKitByResource(resource)
    except exceptions.ArgumentError:
      typekit = None

    bindings = base.BindingFinder(app.config.resourceList)
    binded_from_resources = bindings.GetIDsBindedTo(resource.id)
    unbind_match_type_names = []
    for rid in binded_from_resources:
      if rid.type == types_utils.SERVICE_TYPE:
        if self.GetCloudRunService(rid.name):
          # Only configure service to unbind if it exists
          unbind_match_type_names.append({
              'type': types_utils.SERVICE_TYPE,
              'name': rid.name,
              'ignoreResourceConfig': True,
          })
    if typekit:
      delete_match_type_names = typekit.GetDeleteSelectors(name)
      resource_stages = typekit.GetDeleteComponentTypes(
          selectors=delete_match_type_names
      )
    else:
      delete_match_type_names = [{
          'type': resource.id.type,
          'name': resource.id.name,
      }]
      resource_stages = [resource.id.type]

    stages_map = stages.IntegrationDeleteStages(
        destroy_resource_types=resource_stages,
        should_configure_service=bool(unbind_match_type_names),
    )

    def StatusUpdate(tracker, operation, unused_status):
      self._UpdateDeploymentTracker(tracker, operation, stages_map)
      return

    with progress_tracker.StagedProgressTracker(
        'Deleting Integration...',
        stages_map.values(),
        failure_message='Failed to delete integration.',
    ) as tracker:
      if binded_from_resources:
        for rid in binded_from_resources:
          binded_res = self._FindResource(
              app.config, rid.name, rid.type
          )
          base.RemoveBinding(resource, binded_res)
        # TODO(b/222748706): refine message on failure.
        if unbind_match_type_names:
          self.ApplyAppConfig(
              tracker=tracker,
              tracker_update_func=StatusUpdate,
              appname=_DEFAULT_APP_NAME,
              appconfig=app.config,
              match_type_names=unbind_match_type_names,
              intermediate_step=True,
              etag=app.etag,
          )
        else:
          self._UpdateApplication(
              appname=_DEFAULT_APP_NAME,
              appconfig=app.config,
              etag=app.etag,
          )
      # Undeploy integration resource
      delete_selector = {'matchTypeNames': delete_match_type_names}
      self._UndeployResource(name, delete_selector, tracker, StatusUpdate)

    if typekit:
      return typekit.integration_type
    else:
      return resource.id.type

  def _UndeployResource(
      self, name, delete_selector, tracker, tracker_update_func=None
  ):
    """Undeploy a resource.

    Args:
      name: name of the resource
      delete_selector: The selector for the undeploy operation.
      tracker: StagedProgressTracker, to report on the progress.
      tracker_update_func: optional custom fn to update the tracker.
    """
    tracker.StartStage(stages.UNDEPLOY_RESOURCE)
    self._CreateDeployment(
        appname=_DEFAULT_APP_NAME,
        tracker=tracker,
        tracker_update_func=tracker_update_func,
        delete_selector=delete_selector,
    )
    tracker.CompleteStage(stages.UNDEPLOY_RESOURCE)

    # Get application again to refresh etag before update
    app = self.GetDefaultApp()
    resource = self._FindResource(app.config, name)
    if resource:
      app.config.resourceList.remove(resource)
    tracker.StartStage(stages.CLEANUP_CONFIGURATION)
    self._UpdateApplication(
        appname=_DEFAULT_APP_NAME,
        appconfig=app.config,
        etag=app.etag,
    )
    tracker.CompleteStage(stages.CLEANUP_CONFIGURATION)

  def ListIntegrationTypes(self, include_workload: bool = False):
    """Returns the list of integration type definitions.

    Args:
      include_workload: whether to include workload types

    Returns:
      An array of integration type definitions.
    """
    return [
        integration
        for integration in types_utils.IntegrationTypes(self._client)
        if include_workload
        or (integration.service_type != types_utils.ServiceType.WORKLOAD)
    ]

  def GetIntegrationTypeDefinition(
      self, type_name, include_workload: bool = False
  ):
    """Returns the integration type definition of the given name.

    Args:
      type_name: name of the integration type
      include_workload: whether to include workload types

    Returns:
      An integration type definition. None if no matching type.
    """
    type_metadata = types_utils.GetTypeMetadata(type_name)
    if include_workload or (
        type_metadata is not None and
        type_metadata.service_type != types_utils.ServiceType.WORKLOAD
    ):
      return type_metadata
    return None

  def ListIntegrations(
      self,
      integration_type_filter: str,
      service_name_filter: str,
      region: str = None,
      filter_for_type: Optional[str] = None,
  ):
    """Returns the list of integrations from the default applications.

    If a '-' is provided for the region, then list applications will be called.
    This is for the global integrations list call.  Any other time
    the default region (either from --region or from gcloud config) will be
    used to fetch the default application.  If the global call is not needed,
    then fetching from a single region will reduce latency and remove the need
    of filtering out non default applications.

    Args:
      integration_type_filter: if populated integration type to filter by.
      service_name_filter: if populated service name to filter by.
      region: GCP region. If not provided, then the region will be pulled from
        the flag or from the config.  Only '-', which is the global region has
        any effect here.
      filter_for_type: the type to filter the list on. if given, the resources
        of that type will not be included in the list, and will only show
        binding to or from that type. if not given, all resources and bindings
        will be shown. for example, for `run integrations list`, it would filter
        for `service`.

    Returns:
      List of Dicts containing name, type, and services.
    """
    # Instant ccfe does not work well for global APIs, so for local development
    # with instant ccfe we will default back to fetching the region via
    # config.
    endpoint = properties.VALUES.api_endpoint_overrides.runapps.Get()
    if region == ALL_REGIONS and not _IsLocalHost(endpoint):
      list_apps = api_utils.ListApplications(
          self._client, self.ListAppsRequest()
      )
      apps = list_apps.applications if list_apps else []
      apps = _FilterForDefaultApps(apps)
    else:
      app = api_utils.GetApplication(
          self._client, self.GetAppRef(_DEFAULT_APP_NAME)
      )
      apps = [app] if app else []
    if not apps:
      return []

    output = []
    for app in apps:
      output.extend(
          self._ParseResourcesForList(
              app,
              integration_type_filter,
              service_name_filter,
              filter_for_type,
          )
      )
    return output

  def _ParseResourcesForList(
      self,
      app: runapps_v1alpha1_messages.Application,
      integration_type_filter: str,
      service_name_filter: str,
      focus_workload: Optional[str] = None,
  ):
    """Helper function for ListIntegrations to parse relevant fields."""
    if app.config is None:
      return []
    app_resources = app.config.resourceList
    if not app_resources:
      return []

    bindings = base.BindingFinder(app_resources)
    # cache deployment so we don't pull the same one multiple times.
    deployment_cache = {}

    # Filter by type and/or service.
    output = []
    # the dict is sorted by the resource name to guarantee the output
    # is the same every time.  This is useful for scenario tests.
    for resource in sorted(app_resources, key=lambda x: x.id.name):
      try:
        typekit = typekits_util.GetTypeKitByResource(resource)
      except exceptions.ArgumentError:
        typekit = None

      integration_type = (
          typekit.integration_type if typekit else resource.id.type
      )

      # this will need to filter out other workload if we start supporting
      # more than service
      if integration_type == focus_workload:
        continue

      # TODO(b/217744072): Support Cloud SDK topic filtering.
      # Optionally filter by type.
      if (
          integration_type_filter
          and integration_type != integration_type_filter
      ):
        continue

      if focus_workload:
        services = [
            res_id.name
            for res_id in bindings.GetBindingIDs(resource.id)
            if res_id.type == types_utils.SERVICE_TYPE
        ]
      else:
        services = [
            '{}/{}'.format(res_id.type, res_id.name)
            for res_id in bindings.GetBindingIDs(resource.id)
        ]

      # Optionally filter by service.
      if service_name_filter and service_name_filter not in services:
        continue

      status = self._GetStatusFromLatestDeployment(
          resource.latestDeployment, deployment_cache
      )

      # region is parsed from the name, which has the following form:
      # projects/<proj-name>/locations/<location>/applications/default'
      region = app.name.split('/')[3]

      output.append(
          integration_list_printer.Row(
              integration_name=resource.id.name,
              region=region,
              integration_type=integration_type,
              # sorting is done here to guarantee output for scenario tests
              services=','.join(sorted(services)),
              latest_deployment_status=six.text_type(status),
          )
      )

    return output

  def GetBindingData(
      self,
  ) -> List[base.BindingData]:
    """Return a list of bindings from the default application.

    Returns:
      The list of BindingData.
    """
    app = api_utils.GetApplication(
        self._client, self.GetAppRef(_DEFAULT_APP_NAME)
    )
    if app is None or app.config is None or app.config.resourceList is None:
      return []
    app_resources = app.config.resourceList

    bindings = base.BindingFinder(app_resources)
    return bindings.GetAllBindings()

  def _GetStatusFromLatestDeployment(
      self,
      deployment: str,
      deployment_cache: {str, runapps_v1alpha1_messages.Deployment},
  ) -> runapps_v1alpha1_messages.DeploymentStatus.StateValueValuesEnum:
    """Get status from latest deployment.

    Args:
      deployment: the name of the latest deployment
      deployment_cache: a map of cached deployments

    Returns:
      status of the latest deployment.
    """
    status = (
        runapps_v1alpha1_messages.DeploymentStatus.StateValueValuesEnum.STATE_UNSPECIFIED
    )
    if not deployment:
      return status
    if deployment_cache.get(deployment):
      status = deployment_cache[deployment].status.state
    else:
      dep = api_utils.GetDeployment(self._client, deployment)
      if dep:
        status = dep.status.state
        deployment_cache[deployment] = dep
    return status

  def GetDefaultApp(self) -> runapps_v1alpha1_messages.Application:
    """Returns the default application.

    Returns:
      the application config.
    """
    app = api_utils.GetApplication(
        self._client, self.GetAppRef(_DEFAULT_APP_NAME)
    )
    if not app:
      app = self.messages.Application(
          name=_DEFAULT_APP_NAME,
          config=runapps_v1alpha1_messages.Config(
              resourceList=[],
          ),
      )
    if not app.config:
      app.config = runapps_v1alpha1_messages.Config(
          resourceList=[],
      )
    app.config.resources = None
    return app

  def GetAppRef(self, name):
    """Returns the application resource object.

    Args:
      name:  name of the application.

    Returns:
      The application resource object
    """
    project = properties.VALUES.core.project.Get(required=True)
    location = self._region
    app_ref = resources.REGISTRY.Parse(
        name,
        params={'projectsId': project, 'locationsId': location},
        collection='runapps.projects.locations.applications',
    )
    return app_ref

  def ListAppsRequest(self) -> resources:
    """Creates request object for calling ListApplications for all regions."""
    project = properties.VALUES.core.project.Get(required=True)
    app_ref = resources.REGISTRY.Parse(
        ALL_REGIONS,
        params={
            'projectsId': project,
        },
        collection='runapps.projects.locations',
    )
    return app_ref

  def GetServiceRef(self, name):
    """Returns the Cloud Run service reference.

    Args:
      name:  name of the Cloud Run service.

    Returns:
      Cloud Run service reference
    """
    project = properties.VALUES.core.project.Get(required=True)
    service_ref = resources.REGISTRY.Parse(
        name,
        params={
            'namespacesId': project,
            'servicesId': name,
        },
        collection='run.namespaces.services',
    )
    return service_ref

  def EnsureWorkloadResources(
      self,
      appconfig: runapps_v1alpha1_messages.Config,
      res_name: str,
      res_type: str,
  ):
    """Make sure resources block for the Cloud Run services exists.

    Args:
      appconfig: the application config
      res_name: name of the resource,
      res_type: type of the resource,
    """
    if not self._FindResource(appconfig, res_name, res_type):
      appconfig.resourceList.append(
          runapps_v1alpha1_messages.Resource(
              id=runapps_v1alpha1_messages.ResourceID(
                  name=res_name, type=res_type
              )
          )
      )

  def GetCloudRunService(self, service_name):
    """Check for existence of Cloud Run services.

    Args:
      service_name: str, name of the service

    Returns:
      the Cloud Run service object
    """
    conn_context = connection_context.RegionalConnectionContext(
        self._region,
        global_methods.SERVERLESS_API_NAME,
        global_methods.SERVERLESS_API_VERSION,
    )
    with serverless_operations.Connect(conn_context) as client:
      service_ref = self.GetServiceRef(service_name)
      return client.GetService(service_ref)

  def CheckCloudRunServicesExistence(self, service_names):
    """Check for existence of Cloud Run services.

    Args:
      service_names: array, list of service to check.

    Raises:
      exceptions.ServiceNotFoundError: when a Cloud Run service doesn't exist.
    """
    for name in service_names:
      service = self.GetCloudRunService(name)
      if not service:
        raise exceptions.ServiceNotFoundError(
            'Service [{}] could not be found.'.format(name)
        )

  def CheckDeploymentState(self, response):
    """Throws any unexpected states contained within deployment reponse.

    Args:
      response: run_apps.v1alpha1.deployment, response to check
    """
    # Short hand refference of deployment/job state
    dep_state = self.messages.DeploymentStatus.StateValueValuesEnum
    job_state = self.messages.JobDetails.StateValueValuesEnum

    if response.status.state == dep_state.SUCCEEDED:
      return

    if response.status.state == dep_state.FAILED:
      if not response.status.errorMessage:
        raise exceptions.IntegrationsOperationError('Configuration failed.')

      # Look for job that failed. It should always be last job, but this is not
      # guaranteed behavior.
      url = ''
      for job in response.status.jobDetails[::-1]:
        if job.state == job_state.FAILED:
          url = job.jobUri
          break

      error_msg = 'Configuration failed with error:\n  {}'.format(
          '\n  '.join(response.status.errorMessage.split('; '))
      )
      if url:
        error_msg += '\nLogs are available at {}'.format(url)

      raise exceptions.IntegrationsOperationError(error_msg)

    else:
      raise exceptions.IntegrationsOperationError(
          'Configuration returned in unexpected state "{}".'.format(
              response.status.state.name
          )
      )

  def _AppendTypeMatcher(
      self,
      type_matchers: MutableSequence[base.Selector],
      res_type: str,
      res_name: str,
      ignore_resource_config: Optional[bool] = None,
  ):
    for matcher in type_matchers:
      if matcher['type'] == res_type and matcher['name'] == res_name:
        return
    type_matchers.append({
        'type': res_type,
        'name': res_name,
        'ignoreResourceConfig': ignore_resource_config,
    })

  def VerifyLocation(self):
    app_ref = self.GetAppRef(_DEFAULT_APP_NAME)

    # Fail open in case of global endpoint outage.
    try:
      response = api_utils.ListLocations(self._client, app_ref.projectsId)
    except api_exceptions.HttpError:
      return

    if not any(l.locationId == self._region for l in response.locations):
      raise exceptions.UnsupportedIntegrationsLocationError(
          'Currently this feature is only available in regions {0}.'.format(
              ', '.join([l.locationId for l in response.locations])
          )
      )


def _FilterForDefaultApps(
    apps: List[runapps_v1alpha1_messages.Application],
) -> List[runapps_v1alpha1_messages.Application]:
  """Returns a dict with only default applications.

  Args:
    apps: the list of applications to filter.

  Returns:
    A list of default applications.
  """
  # app.name is the fully qualified name.
  return [app for app in apps if app.name.endswith('/' + _DEFAULT_APP_NAME)]


def _IsLocalHost(endpoint: str) -> bool:
  return endpoint == 'http://localhost:8088/'
