# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Methods and constants for global access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.container import api_adapter as container_api_adapter
from googlecloudsdk.api_lib.container.fleet import client as hub_client
from googlecloudsdk.api_lib.container.fleet import util as hub_util
from googlecloudsdk.api_lib.resourcesettings import service as resourcesettings_service
from googlecloudsdk.api_lib.run import job
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.util import apis

from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

CONTAINER_API_VERSION = 'v1beta1'

SERVERLESS_API_NAME = 'run'
SERVERLESS_API_VERSION = 'v1'

_ALL_REGIONS = '-'

CLOUDRUN_FEATURE = 'appdevexperience'


def GetServerlessClientInstance(api_version=SERVERLESS_API_VERSION):
  return apis.GetClientInstance(SERVERLESS_API_NAME, api_version)


def ListRegions(client):
  """Get the list of all available regions from control plane.

  Args:
    client: (base_api.BaseApiClient), instance of a client to use for the list
      request.

  Returns:
    A list of str, which are regions.
  """
  return sorted([l.locationId for l in ListLocations(client)])


def ListLocations(client):
  """Get the list of all available regions from control plane.

  Args:
    client: (base_api.BaseApiClient), instance of a client to use for the list
      request.

  Returns:
    A list of location resources.
  """
  project_resource_relname = util.ProjectPath(
      properties.VALUES.core.project.Get(required=True))
  return client.projects_locations.List(
      client.MESSAGES_MODULE.RunProjectsLocationsListRequest(
          name=project_resource_relname, pageSize=100)).locations


def ListServices(client, region=_ALL_REGIONS):
  """Get the global services for a OnePlatform project.

  Args:
    client: (base_api.BaseApiClient), instance of a client to use for the list
      request.
    region: (str) optional name of location to search for services in. If not
      passed, this defaults to the global value for all locations.

  Returns:
    List of googlecloudsdk.api_lib.run import service.Service objects.
  """
  project = properties.VALUES.core.project.Get(required=True)
  locations = resources.REGISTRY.Parse(
      region,
      params={'projectsId': project},
      collection='run.projects.locations')
  request = client.MESSAGES_MODULE.RunProjectsLocationsServicesListRequest(
      parent=locations.RelativeName())
  response = client.projects_locations_services.List(request)

  # Log the regions that did not respond.
  if response.unreachable:
    log.warning('The following Cloud Run regions did not respond: {}. '
                'List results may be incomplete.'.format(', '.join(
                    sorted(response.unreachable))))

  return [
      service.Service(item, client.MESSAGES_MODULE) for item in response.items
  ]


def ListJobs(client, namespace):
  """Get the global services for a OnePlatform project.

  Args:
    client: (base_api.BaseApiClient), instance of a client to use for the list
      request.
    namespace: namespace/project to list jobs in

  Returns:
    List of googlecloudsdk.api_lib.run import job.Job objects.
  """
  request = client.MESSAGES_MODULE.RunNamespacesJobsListRequest(
      parent=namespace.RelativeName())
  response = client.namespaces_jobs.List(request)

  # Log the regions that did not respond.
  if response.unreachable:
    log.warning('The following Cloud Run regions did not respond: {}. '
                'List results may be incomplete.'.format(', '.join(
                    sorted(response.unreachable))))

  return [job.Job(item, client.MESSAGES_MODULE) for item in response.items]


def ListClusters(location=None, project=None):
  """Get all clusters with Cloud Run enabled.

  Args:
    location: str optional name of location to search for clusters in. Leaving
      this field blank will search in all locations.
    project: str optional name of project to search for clusters in. Leaving
      this field blank will use the project defined by the corresponding
      property.

  Returns:
    List of googlecloudsdk.generated_clients.apis.container.CONTAINER_API_VERSION
    import container_CONTAINER_API_VERSION_messages.Cluster objects
  """
  container_api = container_api_adapter.NewAPIAdapter(CONTAINER_API_VERSION)
  if not project:
    project = properties.VALUES.core.project.Get(required=True)

  response = container_api.ListClusters(project, location)
  if response.missingZones:
    log.warning('The following cluster locations did not respond: {}. '
                'List results may be incomplete.'.format(', '.join(
                    response.missingZones)))

  def _SortKey(cluster):
    return (cluster.zone, cluster.name)

  clusters = sorted(response.clusters, key=_SortKey)

  crfa_cluster_names = ListCloudRunForAnthosClusters(project)

  return [
      c for c in clusters if (c.name in crfa_cluster_names or
                              (c.addonsConfig.cloudRunConfig and
                               not c.addonsConfig.cloudRunConfig.disabled))
  ]


def ListVerifiedDomains(client):
  """Get all verified domains.

  Args:
    client: (base_api.BaseApiClient), instance of a client to use for the list
      request.

  Returns:
    List of client.MESSAGES_MODULE.AuthorizedDomain objects
  """
  project_resource_relname = util.ProjectPath(
      properties.VALUES.core.project.Get(required=True))
  request = client.MESSAGES_MODULE.RunProjectsAuthorizeddomainsListRequest(
      parent=project_resource_relname)
  response = client.projects_authorizeddomains.List(request)
  return response.domains


def GetClusterRef(cluster, project=None):
  """Returns a ref for the specified cluster.

  Args:
    cluster: container_CONTAINER_API_VERSION_messages.Cluster object
    project: str optional project which overrides the default

  Returns:
    A Resource object
  """
  if not project:
    project = properties.VALUES.core.project.Get(required=True)
  return resources.REGISTRY.Parse(
      cluster.name,
      params={
          'projectId': project,
          'zone': cluster.zone
      },
      collection='container.projects.zones.clusters')


def MultiTenantClustersForProject(project_id, cluster_location):
  """Returns a list of clusters accounting for multi-tenant projects.

  This function can also be used for non-multitenant projects and will
  operate on the single passed-in project_id.

  Args:
    project_id: The id of the project, which may or may not be multi-tenant
    cluster_location: The zone or region of the cluster

  Returns:
    A list of cluster refs
  """
  project_ids = _MultiTenantProjectsIfEnabled(project_id)
  project_ids.insert(0, project_id)
  return _ClustersForProjectIds(project_ids, cluster_location)


def _ClustersForProjectIds(project_ids, cluster_location):
  response = []
  for project_id in project_ids:
    clusters = ListClusters(cluster_location, project_id)
    for cluster in clusters:
      response.append(GetClusterRef(cluster, project_id))
  return response


def _MultiTenantProjectsIfEnabled(project):
  if not _IsResourceSettingsEnabled(project):
    return []
  return _MultiTenantProjectIds(project)


def _IsResourceSettingsEnabled(project):
  api_endpoint = apis.GetEffectiveApiEndpoint(
      resourcesettings_service.RESOURCE_SETTINGS_API_NAME,
      resourcesettings_service.RESOURCE_SETTINGS_API_VERSION)
  # removes initial https:// and trailing slash
  api_endpoint = re.sub(r'https://(.*)/', r'\1', api_endpoint)

  return enable_api.IsServiceEnabled(project, api_endpoint)


def _MultiTenantProjectIds(project):
  """Returns a list of Multitenant project ids."""
  setting_name = 'projects/{}/settings/cloudrun-multiTenancy'.format(project)

  messages = resourcesettings_service.ResourceSettingsMessages()

  get_request = messages.ResourcesettingsProjectsSettingsGetRequest(
      name=setting_name,
      view=messages.ResourcesettingsProjectsSettingsGetRequest
      .ViewValueValuesEnum.SETTING_VIEW_EFFECTIVE_VALUE)
  settings_service = resourcesettings_service.ProjectsSettingsService()
  service_value = settings_service.LookupEffectiveValue(get_request)
  return [
      _MulitTenantProjectId(project)
      for project in service_value.localValue.stringSetValue.values
  ]


# The setting value has the format of projects/PROJECT-ID.
# Returns only the PROJECT-ID.
def _MulitTenantProjectId(setting_value):
  return setting_value.split('/')[1]


def ListCloudRunForAnthosClusters(project):
  """Get all clusters with Cloud Run for Anthos enabled.

  Args:
   project: str optional of project to search for clusters in. Leaving this
     field blank will use the project defined by the corresponding property.

  Returns:
    List of Cluster string names
  """

  crfa_spec = 'projects/%s/locations/global/features/%s' % (project,
                                                            CLOUDRUN_FEATURE)
  try:
    f = hub_client.HubClient().GetFeature(crfa_spec)
  except api_exceptions.HttpError:
    return []

  cluster_state_obj = _ListAnthosClusterStates(f)
  return [name for name, state in cluster_state_obj.items() if state == 'OK']


def _ListAnthosClusterStates(f):
  try:
    cluster_state_obj = {
        hub_util.MembershipShortname(m): s.state.code.name
        for m, s in hub_client.HubClient.ToPyDict(f.membershipStates).items()
    }
  except AttributeError:
    return {}
  return cluster_state_obj
