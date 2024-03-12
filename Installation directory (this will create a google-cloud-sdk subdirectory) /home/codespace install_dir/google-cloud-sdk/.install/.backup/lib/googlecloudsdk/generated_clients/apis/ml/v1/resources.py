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


BASE_URL = 'https://ml.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/ml/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_JOBS = (
      'projects.jobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/jobs/{jobsId}',
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
  PROJECTS_LOCATIONS_STUDIES = (
      'projects.locations.studies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/studies/'
              '{studiesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_STUDIES_TRIALS = (
      'projects.locations.studies.trials',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/studies/'
              '{studiesId}/trials/{trialsId}',
      },
      ['name'],
      True
  )
  PROJECTS_MODELS = (
      'projects.models',
      '{+name}',
      {
          '':
              'projects/{projectsId}/models/{modelsId}',
      },
      ['name'],
      True
  )
  PROJECTS_MODELS_VERSIONS = (
      'projects.models.versions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/models/{modelsId}/versions/{versionsId}',
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
