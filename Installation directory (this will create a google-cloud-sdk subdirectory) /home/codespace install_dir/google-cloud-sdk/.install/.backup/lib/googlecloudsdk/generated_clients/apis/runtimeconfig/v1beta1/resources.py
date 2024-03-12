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


BASE_URL = 'https://runtimeconfig.googleapis.com/v1beta1/'
DOCS_URL = 'https://cloud.google.com/deployment-manager/runtime-configurator/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_CONFIGS = (
      'projects.configs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/configs/{configsId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONFIGS_OPERATIONS = (
      'projects.configs.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/configs/{configsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONFIGS_VARIABLES = (
      'projects.configs.variables',
      '{+name}',
      {
          '':
              'projects/{projectsId}/configs/{configsId}/variables/'
              '{variablesId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONFIGS_WAITERS = (
      'projects.configs.waiters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/configs/{configsId}/waiters/{waitersId}',
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
