# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Util for iap."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from apitools.base.py import encoding
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
import six

IAP_API = 'iap'

APPENGINE_APPS_COLLECTION = 'appengine.apps'
COMPUTE_BACKEND_SERVICES_COLLECTION = 'compute.backendServices'
PROJECTS_COLLECTION = 'iap.projects'
IAP_WEB_COLLECTION = 'iap.projects.iap_web'
IAP_WEB_SERVICES_COLLECTION = 'iap.projects.iap_web.services'
IAP_WEB_SERVICES_VERSIONS_COLLECTION = 'iap.projects.iap_web.services.versions'
IAP_TCP_DESTGROUP_COLLECTION = 'iap.projects.iap_tunnel.locations.destGroups'
IAP_TCP_LOCATIONS_COLLECTION = 'iap.projects.iap_tunnel.locations'


def _ApiVersion(release_track):
  del release_track
  return 'v1'


def _GetRegistry(api_version):
  # Override the default API map version so we can increment API versions on a
  # API interface basis.
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName(IAP_API, api_version)
  return registry


def _GetProject(project_id):
  return projects_api.Get(projects_util.ParseProject(project_id))


class IapIamResource(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for IAP IAM resources."""

  def __init__(self, release_track, project):
    """Base Constructor for an IAP IAM resource.

    Args:
      release_track: base.ReleaseTrack, release track of command.
      project: Project of the IAP IAM resource
    """
    self.release_track = release_track
    self.api_version = _ApiVersion(release_track)

    self.client = apis.GetClientInstance(IAP_API, self.api_version)
    self.registry = _GetRegistry(self.api_version)
    self.project = project

  @property
  def messages(self):
    return self.client.MESSAGES_MODULE

  @property
  def service(self):
    return getattr(self.client, self.api_version)

  @abc.abstractmethod
  def _Name(self):
    """Human-readable name of the resource."""
    pass

  @abc.abstractmethod
  def _Parse(self):
    """Parses the IAP IAM resource from the arguments."""
    pass

  def _GetIamPolicy(self, resource_ref):
    request = self.messages.IapGetIamPolicyRequest(
        resource=resource_ref.RelativeName(),
        getIamPolicyRequest=self.messages.GetIamPolicyRequest(
            options=self.messages.GetPolicyOptions(
                requestedPolicyVersion=
                iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)))
    return self.service.GetIamPolicy(request)

  def GetIamPolicy(self):
    """Get IAM policy for an IAP IAM resource."""
    resource_ref = self._Parse()
    return self._GetIamPolicy(resource_ref)

  def _SetIamPolicy(self, resource_ref, policy):
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
    request = self.messages.IapSetIamPolicyRequest(
        resource=resource_ref.RelativeName(),
        setIamPolicyRequest=self.messages.SetIamPolicyRequest(policy=policy)
    )
    response = self.service.SetIamPolicy(request)
    iam_util.LogSetIamPolicy(resource_ref.RelativeName(), self._Name())
    return response

  def SetIamPolicy(self, policy_file):
    """Set the IAM policy for an IAP IAM resource."""
    policy = iam_util.ParsePolicyFile(policy_file, self.messages.Policy)
    resource_ref = self._Parse()
    return self._SetIamPolicy(resource_ref, policy)

  def AddIamPolicyBinding(self, member, role, condition):
    """Add IAM policy binding to an IAP IAM resource."""
    resource_ref = self._Parse()

    policy = self._GetIamPolicy(resource_ref)
    iam_util.AddBindingToIamPolicyWithCondition(
        self.messages.Binding, self.messages.Expr, policy, member,
        role, condition)
    self._SetIamPolicy(resource_ref, policy)

  def RemoveIamPolicyBinding(self, member, role, condition, all_conditions):
    """Remove IAM policy binding from an IAP IAM resource."""
    resource_ref = self._Parse()

    policy = self._GetIamPolicy(resource_ref)
    iam_util.RemoveBindingFromIamPolicyWithCondition(
        policy, member, role, condition, all_conditions=all_conditions)
    self._SetIamPolicy(resource_ref, policy)


class IAPWeb(IapIamResource):
  """IAP IAM project resource.
  """

  def _Name(self):
    return 'project'

  def _Parse(self):
    project = _GetProject(self.project)
    return self.registry.Parse(
        None, params={
            'projectsId': '{}/iap_web'.format(project.projectNumber),
        }, collection=PROJECTS_COLLECTION)


def _AppEngineAppId(app_id):
  return 'appengine-{}'.format(app_id)


def _GetApplication(project):
  """Returns the application, given a project."""
  api_client = appengine_api_client.AppengineApiClient.GetApiClient()
  application = resources.REGISTRY.Parse(
      None,
      params={
          'appsId': project,
      },
      collection=APPENGINE_APPS_COLLECTION)

  request = api_client.messages.AppengineAppsGetRequest(
      name=application.RelativeName())
  return api_client.client.apps.Get(request)


class AppEngineApplication(IapIamResource):
  """IAP IAM App Engine application resource.
  """

  def _Name(self):
    return 'App Engine application'

  def _Parse(self):
    project = _GetProject(self.project)
    return self.registry.Parse(
        None,
        params={
            'project': project.projectNumber,
            'iapWebId': _AppEngineAppId(project.projectId),
        },
        collection=IAP_WEB_COLLECTION)

  def _SetAppEngineApplicationIap(self, enabled, oauth2_client_id=None,
                                  oauth2_client_secret=None):
    application = _GetApplication(self.project)

    api_client = appengine_api_client.AppengineApiClient.GetApiClient()

    iap_kwargs = _MakeIAPKwargs(False, application.iap, enabled,
                                oauth2_client_id, oauth2_client_secret)
    application_update = api_client.messages.Application(
        iap=api_client.messages.IdentityAwareProxy(**iap_kwargs))

    application = resources.REGISTRY.Parse(
        self.project, collection=APPENGINE_APPS_COLLECTION)

    update_request = api_client.messages.AppengineAppsPatchRequest(
        name=application.RelativeName(),
        application=application_update,
        updateMask='iap,')
    operation = api_client.client.apps.Patch(update_request)
    return operations_util.WaitForOperation(api_client.client.apps_operations,
                                            operation)

  def Enable(self, oauth2_client_id, oauth2_client_secret):
    """Enable IAP on an App Engine Application."""
    return self._SetAppEngineApplicationIap(True,
                                            oauth2_client_id,
                                            oauth2_client_secret)

  def Disable(self):
    """Disable IAP on an App Engine Application."""
    return self._SetAppEngineApplicationIap(False)


class AppEngineService(IapIamResource):
  """IAP IAM App Engine service resource.
  """

  def __init__(self, release_track, project, service_id):
    super(AppEngineService, self).__init__(release_track, project)
    self.service_id = service_id

  def _Name(self):
    return 'App Engine application service'

  def _Parse(self):
    project = _GetProject(self.project)
    return self.registry.Parse(
        None,
        params={
            'project': project.projectNumber,
            'iapWebId': _AppEngineAppId(project.projectId),
            'serviceId': self.service_id,
        },
        collection=IAP_WEB_SERVICES_COLLECTION)


class AppEngineServiceVersion(IapIamResource):
  """IAP IAM App Engine service version resource.
  """

  def __init__(self, release_track, project, service_id, version_id):
    super(AppEngineServiceVersion, self).__init__(release_track, project)
    self.service_id = service_id
    self.version_id = version_id

  def _Name(self):
    return 'App Engine application service version'

  def _Parse(self):
    project = _GetProject(self.project)
    return self.registry.Parse(
        None,
        params={
            'project': project.projectNumber,
            'iapWebId': _AppEngineAppId(project.projectId),
            'serviceId': self.service_id,
            'versionId': self.version_id,
        },
        collection=IAP_WEB_SERVICES_VERSIONS_COLLECTION)


BACKEND_SERVICES = 'compute'


class BackendServices(IapIamResource):
  """IAP IAM backend services resource.
  """

  def __init__(self, release_track, project, region_id):
    super(BackendServices, self).__init__(release_track, project)
    self.region_id = region_id

  def _Name(self):
    return 'backend services'

  def _IapWebId(self):
    if self.region_id:
      return '%s-%s' % (BACKEND_SERVICES, self.region_id)
    else:
      return BACKEND_SERVICES

  def _Parse(self):
    project = _GetProject(self.project)
    iap_web_id = self._IapWebId()
    return self.registry.Parse(
        None,
        params={
            'project': project.projectNumber,
            'iapWebId': iap_web_id,
        },
        collection=IAP_WEB_COLLECTION)


class BackendService(IapIamResource):
  """IAP IAM backend service resource.
  """

  def __init__(self, release_track, project, region_id, service_id):
    super(BackendService, self).__init__(release_track, project)
    self.region_id = region_id
    self.service_id = service_id

  def _Name(self):
    return 'backend service'

  def _IapWebId(self):
    if self.region_id:
      return '%s-%s' % (BACKEND_SERVICES, self.region_id)
    else:
      return BACKEND_SERVICES

  def _Parse(self):
    project = _GetProject(self.project)
    iap_web_id = self._IapWebId()
    return self.registry.Parse(
        None,
        params={
            'project': project.projectNumber,
            'iapWebId': iap_web_id,
            'serviceId': self.service_id,
        },
        collection=IAP_WEB_SERVICES_COLLECTION)

  def _SetBackendServiceIap(self, enabled, oauth2_client_id=None,
                            oauth2_client_secret=None):
    holder = base_classes.ComputeApiHolder(base.ReleaseTrack.GA)
    client = holder.client
    def MakeRequest(method, request):
      return holder.client.apitools_client.backendServices, method, request

    backend_service = holder.resources.Parse(
        self.service_id,
        params={
            'project': self.project,
        },
        collection=COMPUTE_BACKEND_SERVICES_COLLECTION)
    get_request = client.messages.ComputeBackendServicesGetRequest(
        project=backend_service.project,
        backendService=backend_service.Name())

    objects = client.MakeRequests([MakeRequest('Get', get_request)])
    if (enabled and objects[0].protocol is
        not client.messages.BackendService.ProtocolValueValuesEnum.HTTPS):
      log.warning('IAP has been enabled for a backend service that does not '
                  'use HTTPS. Data sent from the Load Balancer to your VM will '
                  'not be encrypted.')
    iap_kwargs = _MakeIAPKwargs(True, objects[0].iap, enabled,
                                oauth2_client_id, oauth2_client_secret)
    replacement = encoding.CopyProtoMessage(objects[0])
    replacement.iap = client.messages.BackendServiceIAP(**iap_kwargs)
    update_request = client.messages.ComputeBackendServicesPatchRequest(
        project=backend_service.project,
        backendService=backend_service.Name(),
        backendServiceResource=replacement)
    return client.MakeRequests([MakeRequest('Patch', update_request)])

  def Enable(self, oauth2_client_id, oauth2_client_secret):
    """Enable IAP on a backend service."""
    return self._SetBackendServiceIap(True,
                                      oauth2_client_id,
                                      oauth2_client_secret)

  def Disable(self):
    """Disable IAP on a backend service."""
    return self._SetBackendServiceIap(False)


def _MakeIAPKwargs(is_backend_service, existing_iap_settings, enabled,
                   oauth2_client_id, oauth2_client_secret):
  """Make IAP kwargs for IAP settings.

  Args:
    is_backend_service: boolean, True if we are applying IAP to a backend
        service.
    existing_iap_settings: appengine IdentityAwareProxy or compute
        BackendServiceIAP, IAP settings.
    enabled: boolean, True if IAP is enabled.
    oauth2_client_id: OAuth2 client ID to use.
    oauth2_client_secret: OAuth2 client secret to use.

  Returns:
    IAP kwargs for appengine IdentityAwareProxy or compute BackendServiceIAP
  """

  if (is_backend_service and enabled and
      not (existing_iap_settings and existing_iap_settings.enabled)):
    log.warning('IAP only protects requests that go through the Cloud Load '
                'Balancer. See the IAP documentation for important security '
                'best practices: https://cloud.google.com/iap/.')
  kwargs = {
      'enabled': enabled,
  }
  if oauth2_client_id:
    kwargs['oauth2ClientId'] = oauth2_client_id
  if oauth2_client_secret:
    kwargs['oauth2ClientSecret'] = oauth2_client_secret
  return kwargs


class IapSettingsResource(object):
  """Class for IAP settings resources."""

  def __init__(self, release_track, resource_name):
    """Constructor for IAP setting resource.

    Args:
      release_track: base.ReleaseTrack, release track of command.
      resource_name: resource name for the iap settings.
    """
    self.release_track = release_track
    self.resource_name = resource_name
    self.api_version = _ApiVersion(release_track)
    self.client = apis.GetClientInstance(IAP_API, self.api_version)
    self.registry = _GetRegistry(self.api_version)

  @property
  def messages(self):
    return self.client.MESSAGES_MODULE

  @property
  def service(self):
    return getattr(self.client, self.api_version)

  def _ParseIapSettingsFile(self, iap_settings_file_path,
                            iap_settings_message_type):
    """Create an iap settings message from a JSON formatted file.

    Args:
       iap_settings_file_path: Path to iap_setttings JSON file
       iap_settings_message_type: iap settings message type to convert JSON to

    Returns:
       the iap_settings message filled from JSON file
    Raises:
       BadFileException if JSON file is malformed.
    """
    iap_settings_to_parse = yaml.load_path(iap_settings_file_path)
    try:
      iap_settings_message = encoding.PyValueToMessage(
          iap_settings_message_type, iap_settings_to_parse)
    except (AttributeError) as e:
      raise calliope_exceptions.BadFileException(
          'Iap settings file {0} does not contain properly formatted JSON {1}'
          .format(iap_settings_file_path, six.text_type(e)))
    return iap_settings_message

  def GetIapSetting(self):
    """Get the setting for an IAP resource."""
    request = self.messages.IapGetIapSettingsRequest(name=self.resource_name)
    return self.service.GetIapSettings(request)

  def SetIapSetting(self, setting_file):
    """Set the setting for an IAP resource."""
    iap_settings = self._ParseIapSettingsFile(setting_file,
                                              self.messages.IapSettings)
    iap_settings.name = self.resource_name
    request = self.messages.IapUpdateIapSettingsRequest(
        iapSettings=iap_settings, name=self.resource_name)
    return self.service.UpdateIapSettings(request)


class IapTunnelDestGroupResource(IapIamResource):
  """IAP TCP tunnelDestGroup IAM resource."""

  def __init__(self, release_track, project, region='-', group_name=None):
    super(IapTunnelDestGroupResource, self).__init__(release_track, project)
    self.region = region
    self.group_name = group_name

  def ResourceService(self):
    return getattr(self.client, 'projects_iap_tunnel_locations_destGroups')

  def _Name(self):
    return 'iap_tunneldestgroups'

  def _Parse(self):
    if self.group_name is None:
      return self._ParseWithoutGroupId()
    return self._ParseWithGroupId()

  def _ParseWithGroupId(self):
    project_number = _GetProject(self.project).projectNumber
    return self.registry.Parse(
        None,
        params={
            'projectsId': project_number,
            'locationsId': self.region,
            'destGroupsId': self.group_name,
        },
        collection=IAP_TCP_DESTGROUP_COLLECTION)

  def _ParseWithoutGroupId(self):
    self.project_number = _GetProject(self.project).projectNumber
    return self.registry.Parse(
        None,
        params={
            'projectsId': self.project_number,
            'locationsId': self.region,
        },
        collection=IAP_TCP_LOCATIONS_COLLECTION)

  def _CreateTunnelDestGroupObject(self, cidr_list, fqdn_list):
    return {
        'name': self.group_name,
        'cidrs': cidr_list.split(',') if cidr_list else [],
        'fqdns': fqdn_list.split(',') if fqdn_list else [],
    }

  def Create(self, cidr_list, fqdn_list):
    """Creates a TunnelDestGroup."""

    tunnel_dest_group = self._CreateTunnelDestGroupObject(cidr_list, fqdn_list)
    request = self.messages.IapProjectsIapTunnelLocationsDestGroupsCreateRequest(
        parent=self._ParseWithoutGroupId().RelativeName(),
        tunnelDestGroup=tunnel_dest_group,
        tunnelDestGroupId=self.group_name)
    return self.ResourceService().Create(request)

  def Delete(self):
    """Deletes the TunnelDestGroup."""
    request = self.messages.IapProjectsIapTunnelLocationsDestGroupsDeleteRequest(
        name=self._Parse().RelativeName())
    return self.ResourceService().Delete(request)

  def List(self, page_size=None, limit=None, list_filter=None):
    """Yields TunnelDestGroups."""
    list_req = self.messages.IapProjectsIapTunnelLocationsDestGroupsListRequest(
        parent=self._ParseWithoutGroupId().RelativeName())
    return list_pager.YieldFromList(
        self.ResourceService(),
        list_req,
        batch_size=page_size,
        limit=limit,
        field='tunnelDestGroups',
        batch_size_attribute='pageSize')

  def Get(self):
    """Get TunnelDestGroup."""
    request = self.messages.IapProjectsIapTunnelLocationsDestGroupsGetRequest(
        name=self._Parse().RelativeName())
    return self.ResourceService().Get(request)

  def Update(self, cidr_list, fqdn_list, update_mask):
    """Update TunnelDestGroup."""

    tunnel_dest_group = self._CreateTunnelDestGroupObject(cidr_list, fqdn_list)

    request = self.messages.IapProjectsIapTunnelLocationsDestGroupsPatchRequest(
        name=self._Parse().RelativeName(),
        tunnelDestGroup=tunnel_dest_group,
        updateMask=update_mask)
    return self.ResourceService().Patch(request)
