# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Resource definitions for Cloud Platform Apis generated from apitools."""

import enum


BASE_URL = 'https://apigee.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/apigee-api-management/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  ORGANIZATIONS = (
      'organizations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ANALYTICS_DATASTORES = (
      'organizations.analytics.datastores',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/analytics/datastores/'
              '{datastoresId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIPRODUCTS = (
      'organizations.apiproducts',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apiproducts/{apiproductsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIPRODUCTS_ATTRIBUTES = (
      'organizations.apiproducts.attributes',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apiproducts/{apiproductsId}/'
              'attributes/{attributesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIPRODUCTS_RATEPLANS = (
      'organizations.apiproducts.rateplans',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apiproducts/{apiproductsId}/'
              'rateplans/{rateplansId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIS = (
      'organizations.apis',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apis/{apisId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIS_KEYVALUEMAPS = (
      'organizations.apis.keyvaluemaps',
      'organizations/{organizationsId}/apis/{apisId}/keyvaluemaps/'
      '{keyvaluemapsId}',
      {},
      ['organizationsId', 'apisId', 'keyvaluemapsId'],
      True
  )
  ORGANIZATIONS_APIS_KEYVALUEMAPS_ENTRIES = (
      'organizations.apis.keyvaluemaps.entries',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apis/{apisId}/keyvaluemaps/'
              '{keyvaluemapsId}/entries/{entriesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIS_REVISIONS = (
      'organizations.apis.revisions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apis/{apisId}/revisions/'
              '{revisionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APPGROUPS = (
      'organizations.appgroups',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/appgroups/{appgroupsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APPGROUPS_APPS = (
      'organizations.appgroups.apps',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/appgroups/{appgroupsId}/apps/'
              '{appsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APPGROUPS_APPS_KEYS = (
      'organizations.appgroups.apps.keys',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/appgroups/{appgroupsId}/apps/'
              '{appsId}/keys/{keysId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APPS = (
      'organizations.apps',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apps/{appsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DATACOLLECTORS = (
      'organizations.datacollectors',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/datacollectors/'
              '{datacollectorsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS = (
      'organizations.developers',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_APPS = (
      'organizations.developers.apps',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'apps/{appsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_APPS_ATTRIBUTES = (
      'organizations.developers.apps.attributes',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'apps/{appsId}/attributes/{attributesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_APPS_KEYS = (
      'organizations.developers.apps.keys',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'apps/{appsId}/keys/{keysId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_ATTRIBUTES = (
      'organizations.developers.attributes',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'attributes/{attributesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_SUBSCRIPTIONS = (
      'organizations.developers.subscriptions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'subscriptions/{subscriptionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENDPOINTATTACHMENTS = (
      'organizations.endpointAttachments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/endpointAttachments/'
              '{endpointAttachmentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVGROUPS = (
      'organizations.envgroups',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/envgroups/{envgroupsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVGROUPS_ATTACHMENTS = (
      'organizations.envgroups.attachments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/envgroups/{envgroupsId}/'
              'attachments/{attachmentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS = (
      'organizations.environments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_ANALYTICS_EXPORTS = (
      'organizations.environments.analytics.exports',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'analytics/exports/{exportsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS = (
      'organizations.environments.apis',
      'organizations/{organizationsId}/environments/{environmentsId}/apis/'
      '{apisId}',
      {},
      ['organizationsId', 'environmentsId', 'apisId'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS_REVISIONS = (
      'organizations.environments.apis.revisions',
      'organizations/{organizationsId}/environments/{environmentsId}/apis/'
      '{apisId}/revisions/{revisionsId}',
      {},
      ['organizationsId', 'environmentsId', 'apisId', 'revisionsId'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS_REVISIONS_DEBUGSESSIONS = (
      'organizations.environments.apis.revisions.debugsessions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'apis/{apisId}/revisions/{revisionsId}/debugsessions/'
              '{debugsessionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS_REVISIONS_DEBUGSESSIONS_DATA = (
      'organizations.environments.apis.revisions.debugsessions.data',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'apis/{apisId}/revisions/{revisionsId}/debugsessions/'
              '{debugsessionsId}/data/{dataId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_ARCHIVEDEPLOYMENTS = (
      'organizations.environments.archiveDeployments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'archiveDeployments/{archiveDeploymentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_DEPLOYMENTS = (
      'organizations.environments.deployments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'deployments/{deploymentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_FLOWHOOKS = (
      'organizations.environments.flowhooks',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'flowhooks/{flowhooksId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_KEYSTORES = (
      'organizations.environments.keystores',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'keystores/{keystoresId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_KEYSTORES_ALIASES = (
      'organizations.environments.keystores.aliases',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'keystores/{keystoresId}/aliases/{aliasesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_KEYVALUEMAPS = (
      'organizations.environments.keyvaluemaps',
      'organizations/{organizationsId}/environments/{environmentsId}/'
      'keyvaluemaps/{keyvaluemapsId}',
      {},
      ['organizationsId', 'environmentsId', 'keyvaluemapsId'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_KEYVALUEMAPS_ENTRIES = (
      'organizations.environments.keyvaluemaps.entries',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'keyvaluemaps/{keyvaluemapsId}/entries/{entriesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_OPTIMIZEDSTATS = (
      'organizations.environments.optimizedStats',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'optimizedStats/{optimizedStatsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_QUERIES = (
      'organizations.environments.queries',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'queries/{queriesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_REFERENCES = (
      'organizations.environments.references',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'references/{referencesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_RESOURCEFILES = (
      'organizations.environments.resourcefiles',
      '{+parent}/resourcefiles/{type}/{name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'resourcefiles/{type}/{name}',
      },
      ['parent', 'type', 'name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_SECURITYACTIONS = (
      'organizations.environments.securityActions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'securityActions/{securityActionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_SECURITYINCIDENTS = (
      'organizations.environments.securityIncidents',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'securityIncidents/{securityIncidentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_SECURITYREPORTS = (
      'organizations.environments.securityReports',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'securityReports/{securityReportsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_STATS = (
      'organizations.environments.stats',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'stats/{statsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_TARGETSERVERS = (
      'organizations.environments.targetservers',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'targetservers/{targetserversId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_TRACECONFIG_OVERRIDES = (
      'organizations.environments.traceConfig.overrides',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'traceConfig/overrides/{overridesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_HOSTQUERIES = (
      'organizations.hostQueries',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/hostQueries/{hostQueriesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_HOSTSECURITYREPORTS = (
      'organizations.hostSecurityReports',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/hostSecurityReports/'
              '{hostSecurityReportsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_HOSTSTATS = (
      'organizations.hostStats',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/hostStats/{hostStatsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_INSTANCES = (
      'organizations.instances',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/instances/{instancesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_INSTANCES_ATTACHMENTS = (
      'organizations.instances.attachments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/instances/{instancesId}/'
              'attachments/{attachmentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_INSTANCES_CANARYEVALUATIONS = (
      'organizations.instances.canaryevaluations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/instances/{instancesId}/'
              'canaryevaluations/{canaryevaluationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_INSTANCES_NATADDRESSES = (
      'organizations.instances.natAddresses',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/instances/{instancesId}/'
              'natAddresses/{natAddressesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_KEYVALUEMAPS = (
      'organizations.keyvaluemaps',
      'organizations/{organizationsId}/keyvaluemaps/{keyvaluemapsId}',
      {},
      ['organizationsId', 'keyvaluemapsId'],
      True
  )
  ORGANIZATIONS_KEYVALUEMAPS_ENTRIES = (
      'organizations.keyvaluemaps.entries',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/keyvaluemaps/{keyvaluemapsId}/'
              'entries/{entriesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_OPERATIONS = (
      'organizations.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_OPTIMIZEDHOSTSTATS = (
      'organizations.optimizedHostStats',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/optimizedHostStats/'
              '{optimizedHostStatsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_REPORTS = (
      'organizations.reports',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/reports/{reportsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SECURITYFEEDBACK = (
      'organizations.securityFeedback',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/securityFeedback/'
              '{securityFeedbackId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SECURITYPROFILES = (
      'organizations.securityProfiles',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/securityProfiles/'
              '{securityProfilesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SECURITYPROFILESV2 = (
      'organizations.securityProfilesV2',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/securityProfilesV2/'
              '{securityProfilesV2Id}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SHAREDFLOWS = (
      'organizations.sharedflows',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/sharedflows/{sharedflowsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SHAREDFLOWS_REVISIONS = (
      'organizations.sharedflows.revisions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/sharedflows/{sharedflowsId}/'
              'revisions/{revisionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SITES = (
      'organizations.sites',
      'organizations/{organizationsId}/sites/{sitesId}',
      {},
      ['organizationsId', 'sitesId'],
      True
  )
  ORGANIZATIONS_SITES_APICATEGORIES = (
      'organizations.sites.apicategories',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/sites/{sitesId}/apicategories/'
              '{apicategoriesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SITES_APIDOCS = (
      'organizations.sites.apidocs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/sites/{sitesId}/apidocs/'
              '{apidocsId}',
      },
      ['name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
