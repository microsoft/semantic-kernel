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


BASE_URL = 'https://mediaasset.googleapis.com/v1alpha/'
DOCS_URL = 'go/cloud-media-asset'


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
  PROJECTS_LOCATIONS_ASSETTYPES = (
      'projects.locations.assetTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/assetTypes/'
              '{assetTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ASSETTYPES_ASSETS = (
      'projects.locations.assetTypes.assets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/assetTypes/'
              '{assetTypesId}/assets/{assetsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ASSETTYPES_ASSETS_ACTIONS = (
      'projects.locations.assetTypes.assets.actions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/assetTypes/'
              '{assetTypesId}/assets/{assetsId}/actions/{actionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ASSETTYPES_ASSETS_ANNOTATIONSETS = (
      'projects.locations.assetTypes.assets.annotationSets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/assetTypes/'
              '{assetTypesId}/assets/{assetsId}/annotationSets/'
              '{annotationSetsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ASSETTYPES_ASSETS_ANNOTATIONSETS_ANNOTATIONS = (
      'projects.locations.assetTypes.assets.annotationSets.annotations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/assetTypes/'
              '{assetTypesId}/assets/{assetsId}/annotationSets/'
              '{annotationSetsId}/annotations/{annotationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ASSETTYPES_RULES = (
      'projects.locations.assetTypes.rules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/assetTypes/'
              '{assetTypesId}/rules/{rulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CATALOGS = (
      'projects.locations.catalogs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/catalogs/'
              '{catalogsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_COMPLEXTYPES = (
      'projects.locations.complexTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/complexTypes/'
              '{complexTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_MODULES = (
      'projects.locations.modules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/modules/'
              '{modulesId}',
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
  PROJECTS_LOCATIONS_TRANSFORMERS = (
      'projects.locations.transformers',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/transformers/'
              '{transformersId}',
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
