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


BASE_URL = 'https://bigquery.googleapis.com/bigquery/v2/'
DOCS_URL = 'https://cloud.google.com/bigquery/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  DATASETS = (
      'datasets',
      'projects/{+projectId}/datasets/{+datasetId}',
      {
          '':
              'projects/{projectId}/datasets/{datasetId}',
      },
      ['projectId', 'datasetId'],
      True
  )
  JOBS = (
      'jobs',
      'projects/{+projectId}/jobs/{+jobId}',
      {
          '':
              'projects/{projectId}/jobs/{jobId}',
      },
      ['projectId', 'jobId'],
      True
  )
  MODELS = (
      'models',
      'projects/{+projectId}/datasets/{+datasetId}/models/{+modelId}',
      {
          '':
              'projects/{projectsId}/datasets/{datasetsId}/models/{modelsId}',
      },
      ['projectId', 'datasetId', 'modelId'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectId}',
      {},
      ['projectId'],
      True
  )
  ROUTINES = (
      'routines',
      'projects/{+projectId}/datasets/{+datasetId}/routines/{+routineId}',
      {
          '':
              'projects/{projectsId}/datasets/{datasetsId}/routines/'
              '{routinesId}',
      },
      ['projectId', 'datasetId', 'routineId'],
      True
  )
  TABLEDATA = (
      'tabledata',
      'projects/{projectId}/datasets/{datasetId}/tables/{tableId}',
      {},
      ['projectId', 'datasetId', 'tableId'],
      False
  )
  TABLES = (
      'tables',
      'projects/{+projectId}/datasets/{+datasetId}/tables/{+tableId}',
      {
          '':
              'projects/{projectId}/datasets/{datasetId}/tables/{tableId}',
      },
      ['projectId', 'datasetId', 'tableId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
