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


BASE_URL = 'https://source.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/eap/cloud-repositories/cloud-source-api'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectId}',
      {},
      ['projectId'],
      True
  )
  PROJECTS_REPOS = (
      'projects.repos',
      'projects/{projectId}/repos/{repoName}',
      {},
      ['projectId', 'repoName'],
      True
  )
  PROJECTS_REPOS_ALIASES = (
      'projects.repos.aliases',
      'projects/{projectId}/repos/{repoName}/aliases/{kind}/{name}',
      {},
      ['projectId', 'repoName', 'kind', 'name'],
      True
  )
  PROJECTS_REPOS_ALIASES_FILES = (
      'projects.repos.aliases.files',
      'projects/{projectId}/repos/{repoName}/aliases/{kind}/{name}/files/'
      '{+path}',
      {
          '':
              'projects/{projectId}/repos/{repoName}/aliases/{kind}/{name}/'
              'files/{filesId}',
      },
      ['projectId', 'repoName', 'kind', 'name', 'path'],
      True
  )
  PROJECTS_REPOS_REVISIONS = (
      'projects.repos.revisions',
      'projects/{projectId}/repos/{repoName}/revisions/{revisionId}',
      {},
      ['projectId', 'repoName', 'revisionId'],
      True
  )
  PROJECTS_REPOS_REVISIONS_FILES = (
      'projects.repos.revisions.files',
      'projects/{projectId}/repos/{repoName}/revisions/{revisionId}/files/'
      '{+path}',
      {
          '':
              'projects/{projectId}/repos/{repoName}/revisions/{revisionId}/'
              'files/{filesId}',
      },
      ['projectId', 'repoName', 'revisionId', 'path'],
      True
  )
  PROJECTS_REPOS_WORKSPACES = (
      'projects.repos.workspaces',
      'projects/{projectId}/repos/{repoName}/workspaces/{name}',
      {},
      ['projectId', 'repoName', 'name'],
      True
  )
  PROJECTS_REPOS_WORKSPACES_FILES = (
      'projects.repos.workspaces.files',
      'projects/{projectId}/repos/{repoName}/workspaces/{name}/files/{+path}',
      {
          '':
              'projects/{projectId}/repos/{repoName}/workspaces/{name}/files/'
              '{filesId}',
      },
      ['projectId', 'repoName', 'name', 'path'],
      True
  )
  PROJECTS_REPOS_WORKSPACES_SNAPSHOTS = (
      'projects.repos.workspaces.snapshots',
      'projects/{projectId}/repos/{repoName}/workspaces/{name}/snapshots/'
      '{snapshotId}',
      {},
      ['projectId', 'repoName', 'name', 'snapshotId'],
      True
  )
  PROJECTS_REPOS_WORKSPACES_SNAPSHOTS_FILES = (
      'projects.repos.workspaces.snapshots.files',
      'projects/{projectId}/repos/{repoName}/workspaces/{name}/snapshots/'
      '{snapshotId}/files/{+path}',
      {
          '':
              'projects/{projectId}/repos/{repoName}/workspaces/{name}/'
              'snapshots/{snapshotId}/files/{filesId}',
      },
      ['projectId', 'repoName', 'name', 'snapshotId', 'path'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
