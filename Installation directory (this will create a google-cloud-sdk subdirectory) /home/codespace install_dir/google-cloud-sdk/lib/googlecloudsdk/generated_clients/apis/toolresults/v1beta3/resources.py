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


BASE_URL = 'https://toolresults.googleapis.com/toolresults/v1beta3/'
DOCS_URL = 'https://firebase.google.com/docs/test-lab/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectId}',
      {},
      ['projectId'],
      True
  )
  PROJECTS_HISTORIES = (
      'projects.histories',
      'projects/{projectId}/histories/{historyId}',
      {},
      ['projectId', 'historyId'],
      True
  )
  PROJECTS_HISTORIES_EXECUTIONS = (
      'projects.histories.executions',
      'projects/{projectId}/histories/{historyId}/executions/{executionId}',
      {},
      ['projectId', 'historyId', 'executionId'],
      True
  )
  PROJECTS_HISTORIES_EXECUTIONS_CLUSTERS = (
      'projects.histories.executions.clusters',
      'projects/{projectId}/histories/{historyId}/executions/{executionId}/'
      'clusters/{clusterId}',
      {},
      ['projectId', 'historyId', 'executionId', 'clusterId'],
      True
  )
  PROJECTS_HISTORIES_EXECUTIONS_ENVIRONMENTS = (
      'projects.histories.executions.environments',
      'projects/{projectId}/histories/{historyId}/executions/{executionId}/'
      'environments/{environmentId}',
      {},
      ['projectId', 'historyId', 'executionId', 'environmentId'],
      True
  )
  PROJECTS_HISTORIES_EXECUTIONS_STEPS = (
      'projects.histories.executions.steps',
      'projects/{projectId}/histories/{historyId}/executions/{executionId}/'
      'steps/{stepId}',
      {},
      ['projectId', 'historyId', 'executionId', 'stepId'],
      True
  )
  PROJECTS_HISTORIES_EXECUTIONS_STEPS_PERFSAMPLESERIES = (
      'projects.histories.executions.steps.perfSampleSeries',
      'projects/{projectId}/histories/{historyId}/executions/{executionId}/'
      'steps/{stepId}/perfSampleSeries/{sampleSeriesId}',
      {},
      ['projectId', 'historyId', 'executionId', 'stepId', 'sampleSeriesId'],
      True
  )
  PROJECTS_HISTORIES_EXECUTIONS_STEPS_TESTCASES = (
      'projects.histories.executions.steps.testCases',
      'projects/{projectId}/histories/{historyId}/executions/{executionId}/'
      'steps/{stepId}/testCases/{testCaseId}',
      {},
      ['projectId', 'historyId', 'executionId', 'stepId', 'testCaseId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
