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


BASE_URL = 'https://sasportal.googleapis.com/v1alpha1/'
DOCS_URL = 'https://developers.google.com/spectrum-access-system/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  CUSTOMERS = (
      'customers',
      '{+name}',
      {
          '':
              'customers/{customersId}',
      },
      ['name'],
      True
  )
  CUSTOMERS_DEPLOYMENTS = (
      'customers.deployments',
      '{+name}',
      {
          '':
              'customers/{customersId}/deployments/{deploymentsId}',
      },
      ['name'],
      True
  )
  CUSTOMERS_DEVICES = (
      'customers.devices',
      '{+name}',
      {
          '':
              'customers/{customersId}/devices/{devicesId}',
      },
      ['name'],
      True
  )
  CUSTOMERS_NODES = (
      'customers.nodes',
      '{+name}',
      {
          '':
              'customers/{customersId}/nodes/{nodesId}',
      },
      ['name'],
      True
  )
  DEPLOYMENTS = (
      'deployments',
      '{+name}',
      {
          '':
              'deployments/{deploymentsId}',
      },
      ['name'],
      True
  )
  DEPLOYMENTS_DEVICES = (
      'deployments.devices',
      '{+name}',
      {
          '':
              'deployments/{deploymentsId}/devices/{devicesId}',
      },
      ['name'],
      True
  )
  NODES = (
      'nodes',
      '{+name}',
      {
          '':
              'nodes/{nodesId}',
      },
      ['name'],
      True
  )
  NODES_DEPLOYMENTS = (
      'nodes.deployments',
      '{+name}',
      {
          '':
              'nodes/{nodesId}/deployments/{deploymentsId}',
      },
      ['name'],
      True
  )
  NODES_DEVICES = (
      'nodes.devices',
      '{+name}',
      {
          '':
              'nodes/{nodesId}/devices/{devicesId}',
      },
      ['name'],
      True
  )
  NODES_NODES = (
      'nodes.nodes',
      '{+name}',
      {
          '':
              'nodes/{nodesId}/nodes/{nodesId1}',
      },
      ['name'],
      True
  )
  POLICIES = (
      'policies',
      'policies:get',
      {},
      [],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
