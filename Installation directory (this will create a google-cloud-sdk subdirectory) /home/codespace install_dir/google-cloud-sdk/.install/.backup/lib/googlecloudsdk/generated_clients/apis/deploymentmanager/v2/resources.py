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


BASE_URL = 'https://deploymentmanager.googleapis.com/deploymentmanager/v2/'
DOCS_URL = 'https://cloud.google.com/deployment-manager'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  DEPLOYMENTS = (
      'deployments',
      'projects/{project}/global/deployments/{deployment}',
      {},
      ['project', 'deployment'],
      True
  )
  MANIFESTS = (
      'manifests',
      'projects/{project}/global/deployments/{deployment}/manifests/'
      '{manifest}',
      {},
      ['project', 'deployment', 'manifest'],
      True
  )
  OPERATIONS = (
      'operations',
      'projects/{project}/global/operations/{operation}',
      {},
      ['project', 'operation'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{project}',
      {},
      ['project'],
      True
  )
  RESOURCES = (
      'resources',
      'projects/{project}/global/deployments/{deployment}/resources/'
      '{resource}',
      {},
      ['project', 'deployment', 'resource'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
