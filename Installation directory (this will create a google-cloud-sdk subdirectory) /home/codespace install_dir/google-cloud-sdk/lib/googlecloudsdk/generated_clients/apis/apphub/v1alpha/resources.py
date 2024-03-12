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


BASE_URL = 'https://apphub.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/app-hub/docs/'


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
  PROJECTS_LOCATIONS_APPLICATIONS = (
      'projects.locations.applications',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/applications/'
              '{applicationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APPLICATIONS_SERVICES = (
      'projects.locations.applications.services',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/applications/'
              '{applicationsId}/services/{servicesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APPLICATIONS_WORKLOADS = (
      'projects.locations.applications.workloads',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/applications/'
              '{applicationsId}/workloads/{workloadsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DISCOVEREDSERVICES = (
      'projects.locations.discoveredServices',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'discoveredServices/{discoveredServicesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DISCOVEREDWORKLOADS = (
      'projects.locations.discoveredWorkloads',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'discoveredWorkloads/{discoveredWorkloadsId}',
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
  PROJECTS_LOCATIONS_SERVICEPROJECTATTACHMENTS = (
      'projects.locations.serviceProjectAttachments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'serviceProjectAttachments/{serviceProjectAttachmentsId}',
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
