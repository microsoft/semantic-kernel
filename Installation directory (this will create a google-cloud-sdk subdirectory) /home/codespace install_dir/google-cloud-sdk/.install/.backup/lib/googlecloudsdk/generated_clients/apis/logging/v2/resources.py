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


BASE_URL = 'https://logging.googleapis.com/v2/'
DOCS_URL = 'https://cloud.google.com/logging/docs/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  BILLINGACCOUNTS = (
      'billingAccounts',
      'billingAccounts/{billingAccountsId}',
      {},
      ['billingAccountsId'],
      True
  )
  BILLINGACCOUNTS_EXCLUSIONS = (
      'billingAccounts.exclusions',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/exclusions/{exclusionsId}',
      },
      ['name'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS = (
      'billingAccounts.locations',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_BUCKETS = (
      'billingAccounts.locations.buckets',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
              'buckets/{bucketsId}',
      },
      ['name'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_BUCKETS_LINKS = (
      'billingAccounts.locations.buckets.links',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
              'buckets/{bucketsId}/links/{linksId}',
      },
      ['name'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_BUCKETS_VIEWS = (
      'billingAccounts.locations.buckets.views',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
              'buckets/{bucketsId}/views/{viewsId}',
      },
      ['name'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_OPERATIONS = (
      'billingAccounts.locations.operations',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  BILLINGACCOUNTS_SINKS = (
      'billingAccounts.sinks',
      '{+sinkName}',
      {
          '':
              'billingAccounts/{billingAccountsId}/sinks/{sinksId}',
      },
      ['sinkName'],
      True
  )
  EXCLUSIONS = (
      'exclusions',
      '{+name}',
      {
          '':
              '{v2Id}/{v2Id1}/exclusions/{exclusionsId}',
      },
      ['name'],
      True
  )
  FOLDERS = (
      'folders',
      'folders/{foldersId}',
      {},
      ['foldersId'],
      True
  )
  FOLDERS_EXCLUSIONS = (
      'folders.exclusions',
      '{+name}',
      {
          '':
              'folders/{foldersId}/exclusions/{exclusionsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS = (
      'folders.locations',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_BUCKETS = (
      'folders.locations.buckets',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/buckets/'
              '{bucketsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_BUCKETS_LINKS = (
      'folders.locations.buckets.links',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/buckets/'
              '{bucketsId}/links/{linksId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_BUCKETS_VIEWS = (
      'folders.locations.buckets.views',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/buckets/'
              '{bucketsId}/views/{viewsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_OPERATIONS = (
      'folders.locations.operations',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  FOLDERS_SINKS = (
      'folders.sinks',
      '{+sinkName}',
      {
          '':
              'folders/{foldersId}/sinks/{sinksId}',
      },
      ['sinkName'],
      True
  )
  LOCATIONS = (
      'locations',
      '{+name}',
      {
          '':
              '{v2Id}/{v2Id1}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  LOCATIONS_BUCKETS = (
      'locations.buckets',
      '{+name}',
      {
          '':
              '{v2Id}/{v2Id1}/locations/{locationsId}/buckets/{bucketsId}',
      },
      ['name'],
      True
  )
  LOCATIONS_BUCKETS_LINKS = (
      'locations.buckets.links',
      '{+name}',
      {
          '':
              '{v2Id}/{v2Id1}/locations/{locationsId}/buckets/{bucketsId}/'
              'links/{linksId}',
      },
      ['name'],
      True
  )
  LOCATIONS_BUCKETS_VIEWS = (
      'locations.buckets.views',
      '{+name}',
      {
          '':
              '{v2Id}/{v2Id1}/locations/{locationsId}/buckets/{bucketsId}/'
              'views/{viewsId}',
      },
      ['name'],
      True
  )
  LOCATIONS_OPERATIONS = (
      'locations.operations',
      '{+name}',
      {
          '':
              '{v2Id}/{v2Id1}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_EXCLUSIONS = (
      'organizations.exclusions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/exclusions/{exclusionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_BUCKETS = (
      'organizations.locations.buckets',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'buckets/{bucketsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_BUCKETS_LINKS = (
      'organizations.locations.buckets.links',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'buckets/{bucketsId}/links/{linksId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_BUCKETS_VIEWS = (
      'organizations.locations.buckets.views',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'buckets/{bucketsId}/views/{viewsId}',
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
  ORGANIZATIONS_SINKS = (
      'organizations.sinks',
      '{+sinkName}',
      {
          '':
              'organizations/{organizationsId}/sinks/{sinksId}',
      },
      ['sinkName'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_EXCLUSIONS = (
      'projects.exclusions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/exclusions/{exclusionsId}',
      },
      ['name'],
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
  PROJECTS_LOCATIONS_BUCKETS = (
      'projects.locations.buckets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/buckets/'
              '{bucketsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BUCKETS_LINKS = (
      'projects.locations.buckets.links',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/buckets/'
              '{bucketsId}/links/{linksId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BUCKETS_VIEWS = (
      'projects.locations.buckets.views',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/buckets/'
              '{bucketsId}/views/{viewsId}',
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
  PROJECTS_METRICS = (
      'projects.metrics',
      '{+metricName}',
      {
          '':
              'projects/{projectsId}/metrics/{metricsId}',
      },
      ['metricName'],
      True
  )
  PROJECTS_SINKS = (
      'projects.sinks',
      '{+sinkName}',
      {
          '':
              'projects/{projectsId}/sinks/{sinksId}',
      },
      ['sinkName'],
      True
  )
  SINKS = (
      'sinks',
      '{+sinkName}',
      {
          '':
              '{v2Id}/{v2Id1}/sinks/{sinksId}',
      },
      ['sinkName'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
