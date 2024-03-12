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


BASE_URL = 'https://datacatalog.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/data-catalog/docs/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  CATALOG = (
      'catalog',
      'catalog',
      {},
      [],
      True
  )
  ENTRIES = (
      'entries',
      'entries',
      {},
      [],
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
  PROJECTS_LOCATIONS_ENTRYGROUPS = (
      'projects.locations.entryGroups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/entryGroups/'
              '{entryGroupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ENTRYGROUPS_ENTRIES = (
      'projects.locations.entryGroups.entries',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/entryGroups/'
              '{entryGroupsId}/entries/{entriesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ENTRYGROUPS_ENTRIES_TAGS = (
      'projects.locations.entryGroups.entries.tags',
      'projects/{projectsId}/locations/{locationsId}/entryGroups/'
      '{entryGroupsId}/entries/{entriesId}/tags/{tagsId}',
      {},
      ['projectsId', 'locationsId', 'entryGroupsId', 'entriesId', 'tagsId'],
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
  PROJECTS_LOCATIONS_TAGTEMPLATES = (
      'projects.locations.tagTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/tagTemplates/'
              '{tagTemplatesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TAGTEMPLATES_FIELDS = (
      'projects.locations.tagTemplates.fields',
      'projects/{projectsId}/locations/{locationsId}/tagTemplates/'
      '{tagTemplatesId}/fields/{fieldsId}',
      {},
      ['projectsId', 'locationsId', 'tagTemplatesId', 'fieldsId'],
      True
  )
  PROJECTS_LOCATIONS_TAGTEMPLATES_FIELDS_ENUMVALUES = (
      'projects.locations.tagTemplates.fields.enumValues',
      'projects/{projectsId}/locations/{locationsId}/tagTemplates/'
      '{tagTemplatesId}/fields/{fieldsId}/enumValues/{enumValuesId}',
      {},
      ['projectsId', 'locationsId', 'tagTemplatesId', 'fieldsId', 'enumValuesId'],
      True
  )
  PROJECTS_LOCATIONS_TAXONOMIES = (
      'projects.locations.taxonomies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/taxonomies/'
              '{taxonomiesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TAXONOMIES_POLICYTAGS = (
      'projects.locations.taxonomies.policyTags',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/taxonomies/'
              '{taxonomiesId}/policyTags/{policyTagsId}',
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
