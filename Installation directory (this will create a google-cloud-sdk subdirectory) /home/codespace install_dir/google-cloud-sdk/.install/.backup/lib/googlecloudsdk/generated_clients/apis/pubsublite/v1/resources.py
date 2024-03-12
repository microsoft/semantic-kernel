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


BASE_URL = 'https://pubsublite.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/pubsub/lite/docs'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  ADMIN_PROJECTS = (
      'admin.projects',
      'admin/projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  ADMIN_PROJECTS_LOCATIONS = (
      'admin.projects.locations',
      'admin/projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  ADMIN_PROJECTS_LOCATIONS_OPERATIONS = (
      'admin.projects.locations.operations',
      'admin/{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  ADMIN_PROJECTS_LOCATIONS_RESERVATIONS = (
      'admin.projects.locations.reservations',
      'admin/{+name}',
      {
          '':
              'admin/projects/{projectsId}/locations/{locationsId}/'
              'reservations/{reservationsId}',
      },
      ['name'],
      True
  )
  ADMIN_PROJECTS_LOCATIONS_RESERVATIONS_TOPICS = (
      'admin.projects.locations.reservations.topics',
      'admin/projects/{projectsId}/locations/{locationsId}/reservations/'
      '{reservationsId}/topics',
      {},
      ['projectsId', 'locationsId', 'reservationsId'],
      True
  )
  ADMIN_PROJECTS_LOCATIONS_SUBSCRIPTIONS = (
      'admin.projects.locations.subscriptions',
      'admin/{+name}',
      {
          '':
              'admin/projects/{projectsId}/locations/{locationsId}/'
              'subscriptions/{subscriptionsId}',
      },
      ['name'],
      True
  )
  ADMIN_PROJECTS_LOCATIONS_TOPICS = (
      'admin.projects.locations.topics',
      'admin/{+name}',
      {
          '':
              'admin/projects/{projectsId}/locations/{locationsId}/topics/'
              '{topicsId}',
      },
      ['name'],
      True
  )
  ADMIN_PROJECTS_LOCATIONS_TOPICS_SUBSCRIPTIONS = (
      'admin.projects.locations.topics.subscriptions',
      'admin/projects/{projectsId}/locations/{locationsId}/topics/{topicsId}/'
      'subscriptions',
      {},
      ['projectsId', 'locationsId', 'topicsId'],
      True
  )
  CURSOR_PROJECTS_LOCATIONS_SUBSCRIPTIONS = (
      'cursor.projects.locations.subscriptions',
      'cursor/projects/{projectsId}/locations/{locationsId}/subscriptions/'
      '{subscriptionsId}',
      {},
      ['projectsId', 'locationsId', 'subscriptionsId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
