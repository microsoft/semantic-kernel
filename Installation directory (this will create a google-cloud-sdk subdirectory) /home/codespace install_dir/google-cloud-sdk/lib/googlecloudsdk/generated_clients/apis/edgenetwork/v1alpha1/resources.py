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


BASE_URL = 'https://edgenetwork.googleapis.com/v1alpha1/'
DOCS_URL = 'https://cloud.google.com/distributed-cloud-edge/docs'


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
  PROJECTS_LOCATIONS_ZONES = (
      'projects.locations.zones',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/zones/{zonesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ZONES_INTERCONNECTATTACHMENTS = (
      'projects.locations.zones.interconnectAttachments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/zones/{zonesId}/'
              'interconnectAttachments/{interconnectAttachmentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ZONES_INTERCONNECTS = (
      'projects.locations.zones.interconnects',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/zones/{zonesId}/'
              'interconnects/{interconnectsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ZONES_NETWORKS = (
      'projects.locations.zones.networks',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/zones/{zonesId}/'
              'networks/{networksId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ZONES_ROUTERS = (
      'projects.locations.zones.routers',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/zones/{zonesId}/'
              'routers/{routersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ZONES_ROUTES = (
      'projects.locations.zones.routes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/zones/{zonesId}/'
              'routes/{routesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ZONES_SUBNETS = (
      'projects.locations.zones.subnets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/zones/{zonesId}/'
              'subnets/{subnetsId}',
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
