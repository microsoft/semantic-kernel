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


BASE_URL = 'https://anthospolicycontrollerstatus-pa.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/anthos-config-management/docs/concepts/policy-controller'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS_FLEETCONSTRAINTTEMPLATES = (
      'projects.fleetConstraintTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/fleetConstraintTemplates/'
              '{fleetConstraintTemplatesId}',
      },
      ['name'],
      True
  )
  PROJECTS_FLEETCONSTRAINTS = (
      'projects.fleetConstraints',
      '{+name}',
      {
          '':
              'projects/{projectsId}/fleetConstraints/{fleetConstraintsId}/'
              '{fleetConstraintsId1}',
      },
      ['name'],
      True
  )
  PROJECTS_MEMBERSHIPCONSTRAINTTEMPLATES = (
      'projects.membershipConstraintTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/membershipConstraintTemplates/'
              '{membershipConstraintTemplatesId}/'
              '{membershipConstraintTemplatesId1}',
      },
      ['name'],
      True
  )
  PROJECTS_MEMBERSHIPCONSTRAINTS = (
      'projects.membershipConstraints',
      '{+name}',
      {
          '':
              'projects/{projectsId}/membershipConstraints/'
              '{membershipConstraintsId}/{membershipConstraintsId1}/'
              '{membershipConstraintsId2}',
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

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
