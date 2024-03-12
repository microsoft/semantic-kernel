# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Functions for creating a client to talk to the App Engine Admin API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json
import operator

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.app import build as app_cloud_build
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import exceptions
from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app import region_util
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app.api import appengine_api_client_base
from googlecloudsdk.api_lib.cloudbuild import logs as cloudbuild_logs
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.third_party.appengine.admin.tools.conversion import convert_yaml
import six
from six.moves import filter  # pylint: disable=redefined-builtin
from six.moves import map  # pylint: disable=redefined-builtin


APPENGINE_VERSIONS_MAP = {
    calliope_base.ReleaseTrack.GA: 'v1',
    calliope_base.ReleaseTrack.ALPHA: 'v1alpha',
    calliope_base.ReleaseTrack.BETA: 'v1beta'
}


def GetApiClientForTrack(release_track):
  api_version = APPENGINE_VERSIONS_MAP[release_track]
  return AppengineApiClient.GetApiClient(api_version)


class AppengineApiClient(appengine_api_client_base.AppengineApiClientBase):
  """Client used by gcloud to communicate with the App Engine API."""

  def GetApplication(self):
    """Retrieves the application resource.

    Returns:
      An app resource representing the project's app.

    Raises:
      apitools_exceptions.HttpNotFoundError if app doesn't exist
    """
    request = self.messages.AppengineAppsGetRequest(name=self._FormatApp())
    return self.client.apps.Get(request)

  def ListRuntimes(self, environment):
    """Lists the available runtimes for the given App Engine environment.

    Args:
      environment: The environment for the application, either Standard or
        Flexible.

    Returns:
      v1beta|v1.ListRuntimesResponse, the list of Runtimes.

    Raises:
      apitools_exceptions.HttpNotFoundError if app doesn't exist
    """
    request = self.messages.AppengineAppsListRuntimesRequest(
        parent=self._FormatApp(), environment=environment
    )
    return self.client.apps.ListRuntimes(request)

  def IsStopped(self, app):
    """Checks application resource to get serving status.

    Args:
      app: appengine_v1_messages.Application, the application to check.

    Returns:
      bool, whether the application is currently disabled. If serving or not
        set, returns False.
    """
    stopped = app.servingStatus in [
        self.messages.Application.ServingStatusValueValuesEnum.USER_DISABLED,
        self.messages.Application.ServingStatusValueValuesEnum.SYSTEM_DISABLED]
    return stopped

  def RepairApplication(self, progress_message=None):
    """Creates missing app resources.

    In particular, the Application.code_bucket GCS reference.

    Args:
      progress_message: str, the message to use while the operation is polled,
        if not the default.

    Returns:
      A long running operation.
    """
    request = self.messages.AppengineAppsRepairRequest(
        name=self._FormatApp(),
        repairApplicationRequest=self.messages.RepairApplicationRequest())

    operation = self.client.apps.Repair(request)

    log.debug('Received operation: [{operation}]'.format(
        operation=operation.name))

    return operations_util.WaitForOperation(
        self.client.apps_operations, operation, message=progress_message)

  def CreateApp(self, location, service_account=None):
    """Creates an App Engine app within the current cloud project.

    Creates a new singleton app within the currently selected Cloud Project.
    The action is one-time and irreversible.

    Args:
      location: str, The location (region) of the app, i.e. "us-central"
      service_account: str, The app level service account of the app, i.e.
        "123@test-app.iam.gserviceaccount.com"

    Raises:
      apitools_exceptions.HttpConflictError if app already exists

    Returns:
      A long running operation.
    """
    create_request = None
    if service_account:
      create_request = self.messages.Application(
          id=self.project, locationId=location, serviceAccount=service_account)
    else:
      create_request = self.messages.Application(
          id=self.project, locationId=location)

    operation = self.client.apps.Create(create_request)

    log.debug('Received operation: [{operation}]'.format(
        operation=operation.name))

    message = ('Creating App Engine application in project [{project}] and '
               'region [{region}].'.format(project=self.project,
                                           region=location))
    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation, message=message)

  def DeployService(self,
                    service_name,
                    version_id,
                    service_config,
                    manifest,
                    build,
                    extra_config_settings=None,
                    service_account_email=None):
    """Updates and deploys new app versions.

    Args:
      service_name: str, The service to deploy.
      version_id: str, The version of the service to deploy.
      service_config: AppInfoExternal, Service info parsed from a service yaml
        file.
      manifest: Dictionary mapping source files to Google Cloud Storage
        locations.
      build: BuildArtifact, a wrapper which contains either the build
        ID for an in-progress parallel build, the name of the container image
        for a serial build, or the options for creating a build elsewhere. Not
        present during standard deploys.
      extra_config_settings: dict, client config settings to pass to the server
        as beta settings.
      service_account_email: Identity of this deployed version. If not set, the
        Admin API will fall back to use the App Engine default appspot service
        account.

    Returns:
      The Admin API Operation, unfinished.

    Raises:
      apitools_exceptions.HttpNotFoundError if build ID doesn't exist
    """
    operation = self._CreateVersion(service_name, version_id, service_config,
                                    manifest, build, extra_config_settings,
                                    service_account_email)

    message = 'Updating service [{service}]'.format(service=service_name)
    if service_config.env in [env.FLEX, env.MANAGED_VMS]:
      message += ' (this may take several minutes)'

    operation_metadata_type = self._ResolveMetadataType()
    # This indicates that a server-side build should be created.
    if build and build.IsBuildOptions():
      if not operation_metadata_type:
        log.warning('Unable to determine build from Operation metadata. '
                    'Skipping log streaming')
      else:
        # Poll the operation until the build is present.
        poller = operations_util.AppEngineOperationBuildPoller(
            self.client.apps_operations, operation_metadata_type)
        operation = operations_util.WaitForOperation(
            self.client.apps_operations, operation, message=message,
            poller=poller)
        build_id = operations_util.GetBuildFromOperation(
            operation, operation_metadata_type)
        if build_id:
          build = app_cloud_build.BuildArtifact.MakeBuildIdArtifact(build_id)

    if build and build.IsBuildId():
      try:
        build_ref = resources.REGISTRY.Parse(
            build.identifier,
            params={'projectId': properties.VALUES.core.project.GetOrFail},
            collection='cloudbuild.projects.builds')
        cloudbuild_logs.CloudBuildClient().Stream(build_ref, out=log.status)
      except apitools_exceptions.HttpNotFoundError:
        region = util.ConvertToCloudRegion(self.GetApplication().locationId)
        build_ref = resources.REGISTRY.Create(
            collection='cloudbuild.projects.locations.builds',
            projectsId=properties.VALUES.core.project.GetOrFail,
            locationsId=region,
            buildsId=build.identifier)
        cloudbuild_logs.CloudBuildClient().Stream(build_ref, out=log.status)

    done_poller = operations_util.AppEngineOperationPoller(
        self.client.apps_operations, operation_metadata_type)
    return operations_util.WaitForOperation(
        self.client.apps_operations,
        operation,
        message=message,
        poller=done_poller)

  def _ResolveMetadataType(self):
    """Attempts to resolve the expected type for the operation metadata."""
    # pylint: disable=protected-access
    # TODO(b/74075874): Update ApiVersion method to accurately reflect client.
    metadata_type_name = 'OperationMetadata' + self.client._VERSION.title()
    # pylint: enable=protected-access
    return getattr(self.messages, metadata_type_name)

  def _CreateVersion(self,
                     service_name,
                     version_id,
                     service_config,
                     manifest,
                     build,
                     extra_config_settings=None,
                     service_account_email=None):
    """Begins the updates and deployment of new app versions.

    Args:
      service_name: str, The service to deploy.
      version_id: str, The version of the service to deploy.
      service_config: AppInfoExternal, Service info parsed from a service yaml
        file.
      manifest: Dictionary mapping source files to Google Cloud Storage
        locations.
      build: BuildArtifact, a wrapper which contains either the build ID for an
        in-progress parallel build, the name of the container image for a serial
        build, or the options to pass to Appengine for a server-side build.
      extra_config_settings: dict, client config settings to pass to the server
        as beta settings.
      service_account_email: Identity of this deployed version. If not set, the
        Admin API will fall back to use the App Engine default appspot service
        account.

    Returns:
      The Admin API Operation, unfinished.
    """
    version_resource = self._CreateVersionResource(service_config, manifest,
                                                   version_id, build,
                                                   extra_config_settings,
                                                   service_account_email)
    create_request = self.messages.AppengineAppsServicesVersionsCreateRequest(
        parent=self._GetServiceRelativeName(service_name=service_name),
        version=version_resource)

    return self.client.apps_services_versions.Create(create_request)

  def GetServiceResource(self, service):
    """Describe the given service.

    Args:
      service: str, the ID of the service

    Returns:
      Service resource object from the API
    """
    request = self.messages.AppengineAppsServicesGetRequest(
        name=self._GetServiceRelativeName(service))
    return self.client.apps_services.Get(request)

  def SetDefaultVersion(self, service_name, version_id):
    """Sets the default serving version of the given services.

    Args:
      service_name: str, The service name
      version_id: str, The version to set as default.
    Returns:
      Long running operation.
    """
    # Create a traffic split where 100% of traffic goes to the specified
    # version.
    allocations = {version_id: 1.0}
    return self.SetTrafficSplit(service_name, allocations)

  def SetTrafficSplit(self, service_name, allocations,
                      shard_by='UNSPECIFIED', migrate=False):
    """Sets the traffic split of the given services.

    Args:
      service_name: str, The service name
      allocations: A dict mapping version ID to traffic split.
      shard_by: A ShardByValuesEnum value specifying how to shard the traffic.
      migrate: Whether or not to migrate traffic.
    Returns:
      Long running operation.
    """
    # Create a traffic split where 100% of traffic goes to the specified
    # version.
    traffic_split = encoding.PyValueToMessage(self.messages.TrafficSplit,
                                              {'allocations': allocations,
                                               'shardBy': shard_by})
    update_service_request = self.messages.AppengineAppsServicesPatchRequest(
        name=self._GetServiceRelativeName(service_name=service_name),
        service=self.messages.Service(split=traffic_split),
        migrateTraffic=migrate,
        updateMask='split')

    message = 'Setting traffic split for service [{service}]'.format(
        service=service_name)
    operation = self.client.apps_services.Patch(update_service_request)
    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation,
                                            message=message)

  def SetIngressTrafficAllowed(self, service_name, ingress_traffic_allowed):
    """Sets the ingress traffic allowed for a service.

    Args:
      service_name: str, The service name
      ingress_traffic_allowed: An IngressTrafficAllowed enum.

    Returns:
      The completed Operation. The Operation will contain a Service resource.
    """
    network_settings = self.messages.NetworkSettings(
        ingressTrafficAllowed=ingress_traffic_allowed)
    update_service_request = self.messages.AppengineAppsServicesPatchRequest(
        name=self._GetServiceRelativeName(service_name=service_name),
        service=self.messages.Service(networkSettings=network_settings),
        updateMask='networkSettings')

    message = 'Setting ingress settings for service [{service}]'.format(
        service=service_name)
    operation = self.client.apps_services.Patch(update_service_request)
    return operations_util.WaitForOperation(
        self.client.apps_operations, operation, message=message)

  def DeleteVersion(self, service_name, version_id):
    """Deletes the specified version of the given service.

    Args:
      service_name: str, The service name
      version_id: str, The version to delete.

    Returns:
      The completed Operation.
    """
    delete_request = self.messages.AppengineAppsServicesVersionsDeleteRequest(
        name=self._FormatVersion(service_name=service_name,
                                 version_id=version_id))
    operation = self.client.apps_services_versions.Delete(delete_request)
    message = 'Deleting [{0}/{1}]'.format(service_name, version_id)
    return operations_util.WaitForOperation(
        self.client.apps_operations, operation, message=message)

  def SetServingStatus(self, service_name, version_id, serving_status,
                       block=True):
    """Sets the serving status of the specified version.

    Args:
      service_name: str, The service name
      version_id: str, The version to delete.
      serving_status: The serving status to set.
      block: bool, whether to block on the completion of the operation

    Returns:
      The completed Operation if block is True, or the Operation to wait on
      otherwise.
    """
    patch_request = self.messages.AppengineAppsServicesVersionsPatchRequest(
        name=self._FormatVersion(service_name=service_name,
                                 version_id=version_id),
        version=self.messages.Version(servingStatus=serving_status),
        updateMask='servingStatus')
    operation = self.client.apps_services_versions.Patch(patch_request)
    if block:
      return operations_util.WaitForOperation(self.client.apps_operations,
                                              operation)
    else:
      return operation

  def ListInstances(self, versions):
    """Produces a generator of all instances for the given versions.

    Args:
      versions: list of version_util.Version

    Returns:
      A list of instances_util.Instance objects for the given versions
    """
    instances = []
    for version in versions:
      request = self.messages.AppengineAppsServicesVersionsInstancesListRequest(
          parent=self._FormatVersion(version.service, version.id))
      try:
        for instance in list_pager.YieldFromList(
            self.client.apps_services_versions_instances,
            request,
            field='instances',
            batch_size=100,  # Set batch size so tests can expect it.
            batch_size_attribute='pageSize'):
          instances.append(
              instances_util.Instance.FromInstanceResource(instance))
      except apitools_exceptions.HttpNotFoundError:
        # Drop versions that were presumed deleted since initial enumeration.
        pass
    return instances

  def GetAllInstances(self, service=None, version=None, version_filter=None):
    """Generator of all instances, optionally filtering by service or version.

    Args:
      service: str, the ID of the service to filter by.
      version: str, the ID of the version to filter by.
      version_filter: filter function accepting version_util.Version

    Returns:
      generator of instance_util.Instance
    """
    services = self.ListServices()
    log.debug('All services: {0}'.format(services))
    services = service_util.GetMatchingServices(
        services, [service] if service else None)

    versions = self.ListVersions(services)
    log.debug('Versions: {0}'.format(list(map(str, versions))))
    versions = version_util.GetMatchingVersions(
        versions, [version] if version else None, service)
    versions = list(filter(version_filter, versions))

    return self.ListInstances(versions)

  def DebugInstance(self, res, ssh_key=None):
    """Enable debugging of a Flexible instance.

    Args:
      res: A googleclousdk.core.Resource object.
      ssh_key: str, Public SSH key to add to the instance. Examples:
        `[USERNAME]:ssh-rsa [KEY_VALUE] [USERNAME]` ,
        `[USERNAME]:ssh-rsa [KEY_VALUE] google-ssh {"userName":"[USERNAME]",`
        `"expireOn":"[EXPIRE_TIME]"}`
        For more information, see Adding and Removing SSH Keys
        (https://cloud.google.com/compute/docs/instances/adding-removing-ssh-
        keys).

    Returns:
      The completed Operation.
    """
    request = self.messages.AppengineAppsServicesVersionsInstancesDebugRequest(
        name=res.RelativeName(),
        debugInstanceRequest=self.messages.DebugInstanceRequest(sshKey=ssh_key))
    operation = self.client.apps_services_versions_instances.Debug(request)
    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation)

  def DeleteInstance(self, res):
    """Delete a Flexible instance.

    Args:
      res: A googlecloudsdk.core.Resource object.

    Returns:
      The completed Operation.
    """
    request = self.messages.AppengineAppsServicesVersionsInstancesDeleteRequest(
        name=res.RelativeName())
    operation = self.client.apps_services_versions_instances.Delete(request)
    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation)

  def GetInstanceResource(self, res):
    """Describe the given instance of the given version of the given service.

    Args:
      res: A googlecloudsdk.core.Resource object.

    Raises:
      apitools_exceptions.HttpNotFoundError: If instance does not
        exist.

    Returns:
      Version resource object from the API
    """
    request = self.messages.AppengineAppsServicesVersionsInstancesGetRequest(
        name=res.RelativeName())
    return self.client.apps_services_versions_instances.Get(request)

  def StopVersion(self, service_name, version_id, block=True):
    """Stops the specified version.

    Args:
      service_name: str, The service name
      version_id: str, The version to stop.
      block: bool, whether to block on the completion of the operation


    Returns:
      The completed Operation if block is True, or the Operation to wait on
      otherwise.
    """
    return self.SetServingStatus(
        service_name,
        version_id,
        self.messages.Version.ServingStatusValueValuesEnum.STOPPED,
        block)

  def StartVersion(self, service_name, version_id, block=True):
    """Starts the specified version.

    Args:
      service_name: str, The service name
      version_id: str, The version to start.
      block: bool, whether to block on the completion of the operation

    Returns:
      The completed Operation if block is True, or the Operation to wait on
      otherwise.
    """
    return self.SetServingStatus(
        service_name,
        version_id,
        self.messages.Version.ServingStatusValueValuesEnum.SERVING,
        block)

  def ListServices(self):
    """Lists all services for the given application.

    Returns:
      A list of service_util.Service objects.
    """
    request = self.messages.AppengineAppsServicesListRequest(
        parent=self._FormatApp())
    services = []
    for service in list_pager.YieldFromList(
        self.client.apps_services, request, field='services',
        batch_size=100, batch_size_attribute='pageSize'):
      traffic_split = {}
      if service.split:
        for split in service.split.allocations.additionalProperties:
          traffic_split[split.key] = split.value
      services.append(
          service_util.Service(self.project, service.id, traffic_split))
    return services

  def GetVersionResource(self, service, version):
    """Describe the given version of the given service.

    Args:
      service: str, the ID of the service for the version to describe.
      version: str, the ID of the version to describe.

    Returns:
      Version resource object from the API.
    """
    request = self.messages.AppengineAppsServicesVersionsGetRequest(
        name=self._FormatVersion(service, version),
        view=(self.messages.
              AppengineAppsServicesVersionsGetRequest.ViewValueValuesEnum.FULL))
    return self.client.apps_services_versions.Get(request)

  def ListVersions(self, services):
    """Lists all versions for the specified services.

    Args:
      services: A list of service_util.Service objects.
    Returns:
      A list of version_util.Version objects.
    """
    versions = []
    for service in services:
      # Get the versions.
      request = self.messages.AppengineAppsServicesVersionsListRequest(
          parent=self._GetServiceRelativeName(service.id))
      try:
        for version in list_pager.YieldFromList(
            self.client.apps_services_versions,
            request,
            field='versions',
            batch_size=100,
            batch_size_attribute='pageSize'):
          versions.append(
              version_util.Version.FromVersionResource(version, service))
      except apitools_exceptions.HttpNotFoundError:
        # Drop services that were presumed deleted since initial enumeration.
        pass

    return versions

  def ListRegions(self):
    """List all regions for the project, and support for standard and flexible.

    Returns:
      List of region_util.Region instances for the project.
    """
    request = self.messages.AppengineAppsLocationsListRequest(
        name='apps/{0}'.format(self.project))

    regions = list_pager.YieldFromList(
        self.client.apps_locations, request, field='locations',
        batch_size=100, batch_size_attribute='pageSize')
    return [region_util.Region.FromRegionResource(loc) for loc in regions]

  def DeleteService(self, service_name):
    """Deletes the specified service.

    Args:
      service_name: str, Name of the service to delete.

    Returns:
      The completed Operation.
    """
    delete_request = self.messages.AppengineAppsServicesDeleteRequest(
        name=self._GetServiceRelativeName(service_name=service_name))
    operation = self.client.apps_services.Delete(delete_request)
    message = 'Deleting [{}]'.format(service_name)
    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation,
                                            message=message)

  def GetOperation(self, op_id):
    """Grabs details about a particular gcloud operation.

    Args:
      op_id: str, ID of operation.

    Returns:
      Operation resource object from API call.
    """
    request = self.messages.AppengineAppsOperationsGetRequest(
        name=self._FormatOperation(op_id))

    return self.client.apps_operations.Get(request)

  def ListOperations(self, op_filter=None):
    """Lists all operations for the given application.

    Args:
      op_filter: String to filter which operations to grab.

    Returns:
      A list of opeartion_util.Operation objects.
    """
    request = self.messages.AppengineAppsOperationsListRequest(
        name=self._FormatApp(),
        filter=op_filter)

    operations = list_pager.YieldFromList(
        self.client.apps_operations, request, field='operations',
        batch_size=100, batch_size_attribute='pageSize')
    return [operations_util.Operation(op) for op in operations]

  def _CreateVersionResource(self,
                             service_config,
                             manifest,
                             version_id,
                             build,
                             extra_config_settings=None,
                             service_account_email=None):
    """Constructs a Version resource for deployment.

    Args:
      service_config: ServiceYamlInfo, Service info parsed from a service yaml
        file.
      manifest: Dictionary mapping source files to Google Cloud Storage
        locations.
      version_id: str, The version of the service.
      build: BuildArtifact, The build ID, image path, or build options.
      extra_config_settings: dict, client config settings to pass to the server
        as beta settings.
      service_account_email: identity of this deployed version. If not set,
        Admin API will fallback to use the App Engine default appspot SA.

    Returns:
      A Version resource whose Deployment includes either a container pointing
        to a completed image, or a build pointing to an in-progress build.
    """
    config_dict = copy.deepcopy(service_config.parsed.ToDict())

    # We always want to set a value for entrypoint when sending the request
    # to Zeus, even if one wasn't specified in the yaml file
    if 'entrypoint' not in config_dict:
      config_dict['entrypoint'] = ''

    try:
      # pylint: disable=protected-access
      schema_parser = convert_yaml.GetSchemaParser(self.client._VERSION)
      json_version_resource = schema_parser.ConvertValue(config_dict)
    except ValueError as e:
      raise exceptions.ConfigError(
          '[{f}] could not be converted to the App Engine configuration '
          'format for the following reason: {msg}'.format(
              f=service_config.file, msg=six.text_type(e)))
    log.debug('Converted YAML to JSON: "{0}"'.format(
        json.dumps(json_version_resource, indent=2, sort_keys=True)))

    # Override the 'service_account' in app.yaml if CLI provided this param.
    if service_account_email is not None:
      json_version_resource['serviceAccount'] = service_account_email

    json_version_resource['deployment'] = {}
    # Add the deployment manifest information.
    json_version_resource['deployment']['files'] = manifest
    if build:
      if build.IsImage():
        json_version_resource['deployment']['container'] = {
            'image': build.identifier
        }
      elif build.IsBuildId():
        json_version_resource['deployment']['build'] = {
            'cloudBuildId': build.identifier
        }
      elif build.IsBuildOptions():
        json_version_resource['deployment']['cloudBuildOptions'] = (
            build.identifier)
    version_resource = encoding.PyValueToMessage(self.messages.Version,
                                                 json_version_resource)
    # For consistency in the tests:
    if version_resource.envVariables:
      version_resource.envVariables.additionalProperties.sort(
          key=lambda x: x.key)

    # We need to pipe some settings to the server as beta settings.
    if extra_config_settings:
      if 'betaSettings' not in json_version_resource:
        json_version_resource['betaSettings'] = {}
      json_version_resource['betaSettings'].update(extra_config_settings)

    # In the JSON representation, BetaSettings are a dict of key-value pairs.
    # In the Message representation, BetaSettings are an ordered array of
    # key-value pairs. Sort the key-value pairs here, so that unit testing is
    # possible.
    if 'betaSettings' in json_version_resource:
      json_dict = json_version_resource.get('betaSettings')
      attributes = []
      for key, value in sorted(json_dict.items()):
        attributes.append(
            self.messages.Version.BetaSettingsValue.AdditionalProperty(
                key=key, value=value))
      version_resource.betaSettings = self.messages.Version.BetaSettingsValue(
          additionalProperties=attributes)

    # The files in the deployment manifest also need to be sorted for unit
    # testing purposes.
    try:
      version_resource.deployment.files.additionalProperties.sort(
          key=operator.attrgetter('key'))
    except AttributeError:  # manifest not present, or no files in manifest
      pass

    # Add an ID for the version which is to be created.
    version_resource.id = version_id
    return version_resource

  def UpdateDispatchRules(self, dispatch_rules):
    """Updates an application's dispatch rules.

    Args:
      dispatch_rules: [{'service': str, 'domain': str, 'path': str}], dispatch-
          rules to set-and-replace.

    Returns:
      Long running operation.
    """

    # Create a configuration update request.
    update_mask = 'dispatchRules,'

    application_update = self.messages.Application()
    application_update.dispatchRules = [self.messages.UrlDispatchRule(**r)
                                        for r in dispatch_rules]
    update_request = self.messages.AppengineAppsPatchRequest(
        name=self._FormatApp(),
        application=application_update,
        updateMask=update_mask)

    operation = self.client.apps.Patch(update_request)

    log.debug('Received operation: [{operation}] with mask [{mask}]'.format(
        operation=operation.name,
        mask=update_mask))

    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation)

  def UpdateDatabaseType(self, database_type):
    """Updates an application's database_type.

    Args:
      database_type: New database type to switch to

    Returns:
      Long running operation.
    """

    # Create a configuration update request.
    update_mask = 'databaseType'
    application_update = self.messages.Application()
    application_update.databaseType = database_type
    update_request = self.messages.AppengineAppsPatchRequest(
        name=self._FormatApp(),
        application=application_update,
        updateMask=update_mask)

    operation = self.client.apps.Patch(update_request)

    log.debug('Received operation: [{operation}] with mask [{mask}]'.format(
        operation=operation.name, mask=update_mask))

    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation)
