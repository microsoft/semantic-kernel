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


BASE_URL = 'https://networksecurity.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/networking'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organizationsId}/locations/{locationsId}',
      {},
      ['organizationsId', 'locationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_ADDRESSGROUPS = (
      'organizations.locations.addressGroups',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'addressGroups/{addressGroupsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_FIREWALLENDPOINTS = (
      'organizations.locations.firewallEndpoints',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'firewallEndpoints/{firewallEndpointsId}',
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
  ORGANIZATIONS_LOCATIONS_SECURITYPROFILEGROUPS = (
      'organizations.locations.securityProfileGroups',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'securityProfileGroups/{securityProfileGroupsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_SECURITYPROFILES = (
      'organizations.locations.securityProfiles',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'securityProfiles/{securityProfilesId}',
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
  PROJECTS_LOCATIONS_ADDRESSGROUPS = (
      'projects.locations.addressGroups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/addressGroups/'
              '{addressGroupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AUTHORIZATIONPOLICIES = (
      'projects.locations.authorizationPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'authorizationPolicies/{authorizationPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CLIENTTLSPOLICIES = (
      'projects.locations.clientTlsPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'clientTlsPolicies/{clientTlsPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_FIREWALLENDPOINTASSOCIATIONS = (
      'projects.locations.firewallEndpointAssociations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'firewallEndpointAssociations/{firewallEndpointAssociationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_GATEWAYSECURITYPOLICIES = (
      'projects.locations.gatewaySecurityPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'gatewaySecurityPolicies/{gatewaySecurityPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_GATEWAYSECURITYPOLICIES_RULES = (
      'projects.locations.gatewaySecurityPolicies.rules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'gatewaySecurityPolicies/{gatewaySecurityPoliciesId}/rules/'
              '{rulesId}',
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
  PROJECTS_LOCATIONS_SERVERTLSPOLICIES = (
      'projects.locations.serverTlsPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'serverTlsPolicies/{serverTlsPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TLSINSPECTIONPOLICIES = (
      'projects.locations.tlsInspectionPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'tlsInspectionPolicies/{tlsInspectionPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_URLLISTS = (
      'projects.locations.urlLists',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/urlLists/'
              '{urlListsId}',
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
