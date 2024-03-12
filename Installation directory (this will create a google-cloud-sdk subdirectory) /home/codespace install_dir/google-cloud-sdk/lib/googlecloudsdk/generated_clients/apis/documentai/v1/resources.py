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


BASE_URL = 'https://documentai.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/document-ai/docs/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

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
  PROJECTS_LOCATIONS_PROCESSORTYPES = (
      'projects.locations.processorTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/processorTypes/'
              '{processorTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PROCESSORS = (
      'projects.locations.processors',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/processors/'
              '{processorsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PROCESSORS_HUMANREVIEWCONFIG = (
      'projects.locations.processors.humanReviewConfig',
      'projects/{projectsId}/locations/{locationsId}/processors/'
      '{processorsId}/humanReviewConfig',
      {},
      ['projectsId', 'locationsId', 'processorsId'],
      True
  )
  PROJECTS_LOCATIONS_PROCESSORS_PROCESSORVERSIONS = (
      'projects.locations.processors.processorVersions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/processors/'
              '{processorsId}/processorVersions/{processorVersionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PROCESSORS_PROCESSORVERSIONS_EVALUATIONS = (
      'projects.locations.processors.processorVersions.evaluations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/processors/'
              '{processorsId}/processorVersions/{processorVersionsId}/'
              'evaluations/{evaluationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_OPERATIONS = (
      'projects.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/operations/{operationsId}',
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
