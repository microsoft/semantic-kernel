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


BASE_URL = 'https://clouddeploy.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/deploy/'


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
  PROJECTS_LOCATIONS_CUSTOMTARGETTYPES = (
      'projects.locations.customTargetTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'customTargetTypes/{customTargetTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DELIVERYPIPELINES = (
      'projects.locations.deliveryPipelines',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'deliveryPipelines/{deliveryPipelinesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DELIVERYPIPELINES_AUTOMATIONRUNS = (
      'projects.locations.deliveryPipelines.automationRuns',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'deliveryPipelines/{deliveryPipelinesId}/automationRuns/'
              '{automationRunsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DELIVERYPIPELINES_AUTOMATIONS = (
      'projects.locations.deliveryPipelines.automations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'deliveryPipelines/{deliveryPipelinesId}/automations/'
              '{automationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DELIVERYPIPELINES_RELEASES = (
      'projects.locations.deliveryPipelines.releases',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'deliveryPipelines/{deliveryPipelinesId}/releases/{releasesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DELIVERYPIPELINES_RELEASES_ROLLOUTS = (
      'projects.locations.deliveryPipelines.releases.rollouts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'deliveryPipelines/{deliveryPipelinesId}/releases/{releasesId}/'
              'rollouts/{rolloutsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DELIVERYPIPELINES_RELEASES_ROLLOUTS_JOBRUNS = (
      'projects.locations.deliveryPipelines.releases.rollouts.jobRuns',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'deliveryPipelines/{deliveryPipelinesId}/releases/{releasesId}/'
              'rollouts/{rolloutsId}/jobRuns/{jobRunsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DEPLOYPOLICIES = (
      'projects.locations.deployPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/deployPolicies/'
              '{deployPoliciesId}',
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
  PROJECTS_LOCATIONS_TARGETS = (
      'projects.locations.targets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/targets/'
              '{targetsId}',
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
