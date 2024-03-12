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


BASE_URL = 'https://batch.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/batch/'


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
  PROJECTS_LOCATIONS_JOBS = (
      'projects.locations.jobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/jobs/{jobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_JOBS_TASKGROUPS = (
      'projects.locations.jobs.taskGroups',
      'projects/{projectsId}/locations/{locationsId}/jobs/{jobsId}/'
      'taskGroups/{taskGroupsId}',
      {},
      ['projectsId', 'locationsId', 'jobsId', 'taskGroupsId'],
      True
  )
  PROJECTS_LOCATIONS_JOBS_TASKGROUPS_TASKS = (
      'projects.locations.jobs.taskGroups.tasks',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/jobs/{jobsId}/'
              'taskGroups/{taskGroupsId}/tasks/{tasksId}',
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

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
