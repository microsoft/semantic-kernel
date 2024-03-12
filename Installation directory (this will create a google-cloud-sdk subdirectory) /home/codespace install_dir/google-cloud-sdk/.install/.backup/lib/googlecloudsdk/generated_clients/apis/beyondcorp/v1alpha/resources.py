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


BASE_URL = 'https://beyondcorp.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organizationsId}/locations/{locationsId}',
      {},
      ['organizationsId', 'locationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_GLOBAL = (
      'organizations.locations.global',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_GLOBAL_PARTNERTENANTS = (
      'organizations.locations.global.partnerTenants',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/global/'
              'partnerTenants/{partnerTenantsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_GLOBAL_PARTNERTENANTS_BROWSERDLPRULES = (
      'organizations.locations.global.partnerTenants.browserDlpRules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/global/'
              'partnerTenants/{partnerTenantsId}/browserDlpRules/'
              '{browserDlpRulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_GLOBAL_PARTNERTENANTS_PROXYCONFIGS = (
      'organizations.locations.global.partnerTenants.proxyConfigs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/global/'
              'partnerTenants/{partnerTenantsId}/proxyConfigs/'
              '{proxyConfigsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_INSIGHTS = (
      'organizations.locations.insights',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'insights/{insightsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_OPERATIONS = (
      'organizations.locations.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_SUBSCRIPTIONS = (
      'organizations.locations.subscriptions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'subscriptions/{subscriptionsId}',
      },
      ['name'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APPCONNECTIONS = (
      'projects.locations.appConnections',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/appConnections/'
              '{appConnectionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APPCONNECTORS = (
      'projects.locations.appConnectors',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/appConnectors/'
              '{appConnectorsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APPGATEWAYS = (
      'projects.locations.appGateways',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/appGateways/'
              '{appGatewaysId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONNECTIONS = (
      'projects.locations.connections',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/connections/'
              '{connectionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONNECTORS = (
      'projects.locations.connectors',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/connectors/'
              '{connectorsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_GLOBAL_SECURITYGATEWAYS = (
      'projects.locations.global.securityGateways',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/global/securityGateways/'
              '{securityGatewaysId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INSIGHTS = (
      'projects.locations.insights',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/insights/'
              '{insightsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONS = (
      'projects.locations.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
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
