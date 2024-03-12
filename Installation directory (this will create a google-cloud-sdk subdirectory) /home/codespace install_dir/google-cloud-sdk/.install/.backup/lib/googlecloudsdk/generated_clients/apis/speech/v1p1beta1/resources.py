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


BASE_URL = 'https://speech.googleapis.com/v1p1beta1/'
DOCS_URL = 'https://cloud.google.com/speech-to-text/docs/quickstart-protocol'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  OPERATIONS = (
      'operations',
      'operations/{+name}',
      {
          '':
              'operations/{operationsId}',
      },
      ['name'],
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
  PROJECTS_LOCATIONS_CUSTOMCLASSES = (
      'projects.locations.customClasses',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/customClasses/'
              '{customClassesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PHRASESETS = (
      'projects.locations.phraseSets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/phraseSets/'
              '{phraseSetsId}',
      },
      ['name'],
      True
  )
  SPEECH = (
      'speech',
      'speech',
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
