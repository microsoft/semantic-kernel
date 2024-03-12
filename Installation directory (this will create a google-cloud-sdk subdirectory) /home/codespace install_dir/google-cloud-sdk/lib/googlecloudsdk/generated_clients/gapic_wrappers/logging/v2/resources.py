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
"""Resource definitions for Cloud Platform APIs generated from gapic."""

import enum


BASE_URL = 'https://logging.googleapis.com/v2/'
DOCS_URL = 'https://cloud.google.com/logging/docs/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  BILLINGACCOUNTS = (
      'billingAccounts',
      'billingAccounts/{billing_account}',
      {},
      ['billing_account'],
      True
  )
  BILLINGACCOUNTS_CMEKSETTINGS = (
      'billingAccounts.cmekSettings',
      'billingAccounts/{billing_account}/cmekSettings',
      {},
      ['billing_account'],
      True
  )
  BILLINGACCOUNTS_EXCLUSIONS = (
      'billingAccounts.exclusions',
      'billingAccounts/{billing_account}/exclusions/{exclusion}',
      {},
      ['billing_account', 'exclusion'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS = (
      'billingAccounts.locations',
      'billingAccounts/{billing_account}/locations/{location}',
      {},
      ['billing_account', 'location'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_BUCKETS = (
      'billingAccounts.locations.buckets',
      'billingAccounts/{billing_account}/locations/{location}/buckets/'
      '{bucket}',
      {},
      ['billing_account', 'location', 'bucket'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_BUCKETS_LINKS = (
      'billingAccounts.locations.buckets.links',
      'billingAccounts/{billing_account}/locations/{location}/buckets/'
      '{bucket}/links/{link}',
      {},
      ['billing_account', 'location', 'bucket', 'link'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_BUCKETS_VIEWS = (
      'billingAccounts.locations.buckets.views',
      'billingAccounts/{billing_account}/locations/{location}/buckets/'
      '{bucket}/views/{view}',
      {},
      ['billing_account', 'location', 'bucket', 'view'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_RECENTQUERIES = (
      'billingAccounts.locations.recentQueries',
      'billingAccounts/{billing_account}/locations/{location}/recentQueries/'
      '{saved_query}',
      {},
      ['billing_account', 'location', 'saved_query'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_SAVEDQUERIES = (
      'billingAccounts.locations.savedQueries',
      'billingAccounts/{billing_account}/locations/{location}/savedQueries/'
      '{saved_query}',
      {},
      ['billing_account', 'location', 'saved_query'],
      True
  )
  BILLINGACCOUNTS_LOGS = (
      'billingAccounts.logs',
      'billingAccounts/{billing_account}/logs/{log}',
      {},
      ['billing_account', 'log'],
      True
  )
  BILLINGACCOUNTS_SETTINGS = (
      'billingAccounts.settings',
      'billingAccounts/{billing_account}/settings',
      {},
      ['billing_account'],
      True
  )
  BILLINGACCOUNTS_SINKS = (
      'billingAccounts.sinks',
      'billingAccounts/{billing_account}/sinks/{sink}',
      {},
      ['billing_account', 'sink'],
      True
  )
  FOLDERS = (
      'folders',
      'folders/{folder}',
      {},
      ['folder'],
      True
  )
  FOLDERS_CMEKSETTINGS = (
      'folders.cmekSettings',
      'folders/{folder}/cmekSettings',
      {},
      ['folder'],
      True
  )
  FOLDERS_EXCLUSIONS = (
      'folders.exclusions',
      'folders/{folder}/exclusions/{exclusion}',
      {},
      ['folder', 'exclusion'],
      True
  )
  FOLDERS_LOCATIONS = (
      'folders.locations',
      'folders/{folder}/locations/{location}',
      {},
      ['folder', 'location'],
      True
  )
  FOLDERS_LOCATIONS_BUCKETS = (
      'folders.locations.buckets',
      'folders/{folder}/locations/{location}/buckets/{bucket}',
      {},
      ['folder', 'location', 'bucket'],
      True
  )
  FOLDERS_LOCATIONS_BUCKETS_LINKS = (
      'folders.locations.buckets.links',
      'folders/{folder}/locations/{location}/buckets/{bucket}/links/{link}',
      {},
      ['folder', 'location', 'bucket', 'link'],
      True
  )
  FOLDERS_LOCATIONS_BUCKETS_VIEWS = (
      'folders.locations.buckets.views',
      'folders/{folder}/locations/{location}/buckets/{bucket}/views/{view}',
      {},
      ['folder', 'location', 'bucket', 'view'],
      True
  )
  FOLDERS_LOCATIONS_RECENTQUERIES = (
      'folders.locations.recentQueries',
      'folders/{folder}/locations/{location}/recentQueries/{saved_query}',
      {},
      ['folder', 'location', 'saved_query'],
      True
  )
  FOLDERS_LOCATIONS_SAVEDQUERIES = (
      'folders.locations.savedQueries',
      'folders/{folder}/locations/{location}/savedQueries/{saved_query}',
      {},
      ['folder', 'location', 'saved_query'],
      True
  )
  FOLDERS_LOGS = (
      'folders.logs',
      'folders/{folder}/logs/{log}',
      {},
      ['folder', 'log'],
      True
  )
  FOLDERS_SETTINGS = (
      'folders.settings',
      'folders/{folder}/settings',
      {},
      ['folder'],
      True
  )
  FOLDERS_SINKS = (
      'folders.sinks',
      'folders/{folder}/sinks/{sink}',
      {},
      ['folder', 'sink'],
      True
  )
  ORGANIZATIONS = (
      'organizations',
      'organizations/{organization}',
      {},
      ['organization'],
      True
  )
  ORGANIZATIONS_CMEKSETTINGS = (
      'organizations.cmekSettings',
      'organizations/{organization}/cmekSettings',
      {},
      ['organization'],
      True
  )
  ORGANIZATIONS_EXCLUSIONS = (
      'organizations.exclusions',
      'organizations/{organization}/exclusions/{exclusion}',
      {},
      ['organization', 'exclusion'],
      True
  )
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organization}/locations/{location}',
      {},
      ['organization', 'location'],
      True
  )
  ORGANIZATIONS_LOCATIONS_BUCKETS = (
      'organizations.locations.buckets',
      'organizations/{organization}/locations/{location}/buckets/{bucket}',
      {},
      ['organization', 'location', 'bucket'],
      True
  )
  ORGANIZATIONS_LOCATIONS_BUCKETS_LINKS = (
      'organizations.locations.buckets.links',
      'organizations/{organization}/locations/{location}/buckets/{bucket}/'
      'links/{link}',
      {},
      ['organization', 'location', 'bucket', 'link'],
      True
  )
  ORGANIZATIONS_LOCATIONS_BUCKETS_VIEWS = (
      'organizations.locations.buckets.views',
      'organizations/{organization}/locations/{location}/buckets/{bucket}/'
      'views/{view}',
      {},
      ['organization', 'location', 'bucket', 'view'],
      True
  )
  ORGANIZATIONS_LOCATIONS_RECENTQUERIES = (
      'organizations.locations.recentQueries',
      'organizations/{organization}/locations/{location}/recentQueries/'
      '{saved_query}',
      {},
      ['organization', 'location', 'saved_query'],
      True
  )
  ORGANIZATIONS_LOCATIONS_SAVEDQUERIES = (
      'organizations.locations.savedQueries',
      'organizations/{organization}/locations/{location}/savedQueries/'
      '{saved_query}',
      {},
      ['organization', 'location', 'saved_query'],
      True
  )
  ORGANIZATIONS_LOGS = (
      'organizations.logs',
      'organizations/{organization}/logs/{log}',
      {},
      ['organization', 'log'],
      True
  )
  ORGANIZATIONS_SETTINGS = (
      'organizations.settings',
      'organizations/{organization}/settings',
      {},
      ['organization'],
      True
  )
  ORGANIZATIONS_SINKS = (
      'organizations.sinks',
      'organizations/{organization}/sinks/{sink}',
      {},
      ['organization', 'sink'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{project}',
      {},
      ['project'],
      True
  )
  PROJECTS_CMEKSETTINGS = (
      'projects.cmekSettings',
      'projects/{project}/cmekSettings',
      {},
      ['project'],
      True
  )
  PROJECTS_EXCLUSIONS = (
      'projects.exclusions',
      'projects/{project}/exclusions/{exclusion}',
      {},
      ['project', 'exclusion'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{project}/locations/{location}',
      {},
      ['project', 'location'],
      True
  )
  PROJECTS_LOCATIONS_BUCKETS = (
      'projects.locations.buckets',
      'projects/{project}/locations/{location}/buckets/{bucket}',
      {},
      ['project', 'location', 'bucket'],
      True
  )
  PROJECTS_LOCATIONS_BUCKETS_LINKS = (
      'projects.locations.buckets.links',
      'projects/{project}/locations/{location}/buckets/{bucket}/links/{link}',
      {},
      ['project', 'location', 'bucket', 'link'],
      True
  )
  PROJECTS_LOCATIONS_BUCKETS_VIEWS = (
      'projects.locations.buckets.views',
      'projects/{project}/locations/{location}/buckets/{bucket}/views/{view}',
      {},
      ['project', 'location', 'bucket', 'view'],
      True
  )
  PROJECTS_LOCATIONS_RECENTQUERIES = (
      'projects.locations.recentQueries',
      'projects/{project}/locations/{location}/recentQueries/{recent_query}',
      {},
      ['project', 'location', 'recent_query'],
      True
  )
  PROJECTS_LOCATIONS_SAVEDQUERIES = (
      'projects.locations.savedQueries',
      'projects/{project}/locations/{location}/savedQueries/{saved_query}',
      {},
      ['project', 'location', 'saved_query'],
      True
  )
  PROJECTS_LOGS = (
      'projects.logs',
      'projects/{project}/logs/{log}',
      {},
      ['project', 'log'],
      True
  )
  PROJECTS_METRICS = (
      'projects.metrics',
      'projects/{project}/metrics/{metric}',
      {},
      ['project', 'metric'],
      True
  )
  PROJECTS_SETTINGS = (
      'projects.settings',
      'projects/{project}/settings',
      {},
      ['project'],
      True
  )
  PROJECTS_SINKS = (
      'projects.sinks',
      'projects/{project}/sinks/{sink}',
      {},
      ['project', 'sink'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
