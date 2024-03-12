# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utility for the CMEK and user-provided AR use cases."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.functions.v1 import exceptions
from googlecloudsdk.calliope import exceptions as base_exceptions
from six.moves import http_client

_KMS_KEY_RE = re.compile(
    r'^projects/[^/]+/locations/(?P<location>[^/]+)/keyRings/[a-zA-Z0-9_-]+'
    '/cryptoKeys/[a-zA-Z0-9_-]+$'
)
_DOCKER_REPOSITORY_RE = re.compile(
    r'^projects/(?P<project>[^/]+)/locations/(?P<location>[^/]+)'
    '/repositories/[a-z]([a-z0-9-]*[a-z0-9])?$'
)
_DOCKER_REPOSITORY_DOCKER_FORMAT_RE = re.compile(
    r'^(?P<location>.*)-docker.pkg.dev\/(?P<project>[^\/]+)\/(?P<repo>[^\/]+)'
)


def ValidateKMSKeyForFunction(kms_key, function_ref):
  """Checks that the KMS key is compatible with the function.

  Args:
    kms_key: Fully qualified KMS key name.
    function_ref: Function resource reference.

  Raises:
    InvalidArgumentException: If the specified KMS key is not compatible with
      the function.
  """
  kms_key_match = _KMS_KEY_RE.search(kms_key)
  if kms_key_match:
    kms_keyring_location = kms_key_match.group('location')
    if kms_keyring_location == 'global':
      raise base_exceptions.InvalidArgumentException(
          '--kms-key', 'Global KMS keyrings are not allowed.'
      )
    if function_ref.locationsId != kms_keyring_location:
      raise base_exceptions.InvalidArgumentException(
          '--kms-key',
          'KMS keyrings should be created in the same region as the function.',
      )


def ValidateDockerRepositoryForFunction(docker_repository, function_ref):
  """Checks that the Docker repository is compatible with the function.

  Args:
    docker_repository: Fully qualified Docker repository resource name.
    function_ref: Function resource reference.

  Raises:
    InvalidArgumentException: If the specified Docker repository is not
      compatible with the function.
  """
  if docker_repository is None:
    return

  function_project = function_ref.projectsId
  function_location = function_ref.locationsId

  repo_project, repo_location = None, None
  repo_match = _DOCKER_REPOSITORY_RE.search(docker_repository)
  if repo_match:
    repo_project = repo_match.group('project')
    repo_location = repo_match.group('location')
  else:
    repo_match_docker_format = _DOCKER_REPOSITORY_DOCKER_FORMAT_RE.search(
        docker_repository
    )
    if repo_match_docker_format:
      repo_project = repo_match_docker_format.group('project')
      repo_location = repo_match_docker_format.group('location')

  if repo_match or repo_match_docker_format:
    if (
        function_project != repo_project
        and function_project.isdigit() == repo_project.isdigit()
    ):
      raise base_exceptions.InvalidArgumentException(
          '--docker-repository', 'Cross-project repositories are not supported.'
      )
    if function_location != repo_location:
      raise base_exceptions.InvalidArgumentException(
          '--docker-repository',
          'Cross-location repositories are not supported.',
      )


def NormalizeDockerRepositoryFormat(docker_repository):
  """Normalizes the docker repository name to the standard resource format.

  Args:
    docker_repository: Fully qualified Docker repository name.

  Returns:
    The name in a standard format supported by the API.
  """
  if docker_repository is None:
    return docker_repository

  repo_match_docker_format = _DOCKER_REPOSITORY_DOCKER_FORMAT_RE.search(
      docker_repository
  )
  if repo_match_docker_format:
    project = repo_match_docker_format.group('project')
    location = repo_match_docker_format.group('location')
    name = repo_match_docker_format.group('repo')
    return 'projects/{}/locations/{}/repositories/{}'.format(
        project, location, name
    )

  return docker_repository


def ProcessException(http_exception, kms_key=None):
  if (
      kms_key
      and http_exception.status_code == http_client.INTERNAL_SERVER_ERROR
  ):
    # TODO(b/268523346): more specific user-friendly error messages for
    # CMEK-related error modes.
    raise exceptions.FunctionsError(
        'An error occurred. Ensure that the KMS key {kms_key} exists and the '
        'Cloud Functions service account has encrypter/decrypter permissions '
        '(roles/cloudkms.cryptoKeyEncrypterDecrypter) on the key. If you '
        'have recently made changes to the IAM config, wait a few minutes '
        'for the config to propagate and try again.'.format(kms_key=kms_key)
    )
