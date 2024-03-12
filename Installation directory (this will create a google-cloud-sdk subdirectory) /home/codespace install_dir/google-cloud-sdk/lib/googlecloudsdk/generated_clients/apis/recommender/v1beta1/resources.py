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


BASE_URL = 'https://recommender.googleapis.com/v1beta1/'
DOCS_URL = 'https://cloud.google.com/recommender/docs/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  BILLINGACCOUNTS = (
      'billingAccounts',
      'billingAccounts/{billingAccountsId}',
      {},
      ['billingAccountsId'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS = (
      'billingAccounts.locations',
      'billingAccounts/{billingAccountsId}/locations/{locationsId}',
      {},
      ['billingAccountsId', 'locationsId'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_INSIGHTTYPES = (
      'billingAccounts.locations.insightTypes',
      'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
      'insightTypes/{insightTypesId}',
      {},
      ['billingAccountsId', 'locationsId', 'insightTypesId'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_INSIGHTTYPES_INSIGHTS = (
      'billingAccounts.locations.insightTypes.insights',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
              'insightTypes/{insightTypesId}/insights/{insightsId}',
      },
      ['name'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_RECOMMENDERS = (
      'billingAccounts.locations.recommenders',
      'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
      'recommenders/{recommendersId}',
      {},
      ['billingAccountsId', 'locationsId', 'recommendersId'],
      True
  )
  BILLINGACCOUNTS_LOCATIONS_RECOMMENDERS_RECOMMENDATIONS = (
      'billingAccounts.locations.recommenders.recommendations',
      '{+name}',
      {
          '':
              'billingAccounts/{billingAccountsId}/locations/{locationsId}/'
              'recommenders/{recommendersId}/recommendations/'
              '{recommendationsId}',
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
  FOLDERS_LOCATIONS = (
      'folders.locations',
      'folders/{foldersId}/locations/{locationsId}',
      {},
      ['foldersId', 'locationsId'],
      True
  )
  FOLDERS_LOCATIONS_INSIGHTTYPES = (
      'folders.locations.insightTypes',
      'folders/{foldersId}/locations/{locationsId}/insightTypes/'
      '{insightTypesId}',
      {},
      ['foldersId', 'locationsId', 'insightTypesId'],
      True
  )
  FOLDERS_LOCATIONS_INSIGHTTYPES_INSIGHTS = (
      'folders.locations.insightTypes.insights',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/insightTypes/'
              '{insightTypesId}/insights/{insightsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_RECOMMENDERS = (
      'folders.locations.recommenders',
      'folders/{foldersId}/locations/{locationsId}/recommenders/'
      '{recommendersId}',
      {},
      ['foldersId', 'locationsId', 'recommendersId'],
      True
  )
  FOLDERS_LOCATIONS_RECOMMENDERS_RECOMMENDATIONS = (
      'folders.locations.recommenders.recommendations',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/recommenders/'
              '{recommendersId}/recommendations/{recommendationsId}',
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
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organizationsId}/locations/{locationsId}',
      {},
      ['organizationsId', 'locationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_INSIGHTTYPES = (
      'organizations.locations.insightTypes',
      'organizations/{organizationsId}/locations/{locationsId}/insightTypes/'
      '{insightTypesId}',
      {},
      ['organizationsId', 'locationsId', 'insightTypesId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_INSIGHTTYPES_INSIGHTS = (
      'organizations.locations.insightTypes.insights',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'insightTypes/{insightTypesId}/insights/{insightsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_RECOMMENDERS = (
      'organizations.locations.recommenders',
      'organizations/{organizationsId}/locations/{locationsId}/recommenders/'
      '{recommendersId}',
      {},
      ['organizationsId', 'locationsId', 'recommendersId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_RECOMMENDERS_RECOMMENDATIONS = (
      'organizations.locations.recommenders.recommendations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'recommenders/{recommendersId}/recommendations/'
              '{recommendationsId}',
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
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_INSIGHTTYPES = (
      'projects.locations.insightTypes',
      'projects/{projectsId}/locations/{locationsId}/insightTypes/'
      '{insightTypesId}',
      {},
      ['projectsId', 'locationsId', 'insightTypesId'],
      True
  )
  PROJECTS_LOCATIONS_INSIGHTTYPES_INSIGHTS = (
      'projects.locations.insightTypes.insights',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/insightTypes/'
              '{insightTypesId}/insights/{insightsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_RECOMMENDERS = (
      'projects.locations.recommenders',
      'projects/{projectsId}/locations/{locationsId}/recommenders/'
      '{recommendersId}',
      {},
      ['projectsId', 'locationsId', 'recommendersId'],
      True
  )
  PROJECTS_LOCATIONS_RECOMMENDERS_RECOMMENDATIONS = (
      'projects.locations.recommenders.recommendations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/recommenders/'
              '{recommendersId}/recommendations/{recommendationsId}',
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
