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


BASE_URL = 'https://anthosevents.googleapis.com/apis/sources.knative.dev/v1beta1/'
DOCS_URL = ''


class Collections(enum.Enum):
  """Collections for all supported apis."""

  NAMESPACES = (
      'namespaces',
      'namespaces/{namespacesId}',
      {},
      ['namespacesId'],
      True
  )
  NAMESPACES_CUSTOMRESOURCEDEFINITIONS = (
      'namespaces.customresourcedefinitions',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/customresourcedefinitions/'
              '{customresourcedefinitionsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_BROKERS = (
      'namespaces.brokers',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/brokers/{brokersId}',
      },
      ['name'],
      True
  )
  NAMESPACES_TRIGGERS = (
      'namespaces.triggers',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/triggers/{triggersId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDAUDITLOGSSOURCES = (
      'namespaces.cloudauditlogssources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudauditlogssources/'
              '{cloudauditlogssourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDPUBSUBSOURCES = (
      'namespaces.cloudpubsubsources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudpubsubsources/'
              '{cloudpubsubsourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDSCHEDULERSOURCES = (
      'namespaces.cloudschedulersources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudschedulersources/'
              '{cloudschedulersourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDSTORAGESOURCES = (
      'namespaces.cloudstoragesources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudstoragesources/'
              '{cloudstoragesourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_APISERVERSOURCES = (
      'namespaces.apiserversources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/apiserversources/'
              '{apiserversourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_PINGSOURCES = (
      'namespaces.pingsources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/pingsources/{pingsourcesId}',
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
