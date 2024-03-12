# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Utilities for GCR."""

import dataclasses
from typing import Iterator
from apitools.base.py import list_pager
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.asset import client_util as asset_client_util
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_VALID_GCR_REGION_PREFIX = frozenset({'', 'us.', 'eu.', 'asia.'})


def ListGCRRepos(parent: str) -> Iterator[docker_name.Repository]:
  """Lists GCR repositories under the parent resource.

  Args:
    parent: A parent resource, e.g. projects/123, folders/123, orgnizations/123.

  Yields:
    Each docker repository that is a GCR repo under the parent resource.
  """

  gcr_buckets_search_request = (
      asset_client_util.GetMessages().CloudassetSearchAllResourcesRequest(
          scope=parent,
          query='name:artifacts appspot com',
          assetTypes=[
              f'storage.{properties.VALUES.core.universe_domain.Get()}/Bucket'
          ],
          readMask='name,parentFullResourceName',
      )
  )
  gcr_buckets = list_pager.YieldFromList(
      asset_client_util.GetClient().v1,
      gcr_buckets_search_request,
      method='SearchAllResources',
      field='results',
      batch_size_attribute='pageSize',
  )

  for bucket in gcr_buckets:
    repo = _BucketToRepo(bucket)
    if repo is not None:
      yield repo


@dataclasses.dataclass(frozen=True)
class GCRUsage:
  """GCRUsage represents usage for a GCR repo.

  Attributes:
    repository: A GCR repo name.
    usage: Usage for the repo.
  """

  repository: str
  usage: str


def CheckGCRUsage(repo: docker_name.Repository) -> GCRUsage:
  """Checks usage for a GCR repo.

  Args:
    repo: A docker repository.

  Returns:
    A GCRUsage object.
  """

  try:
    with docker_image.FromRegistry(
        basic_creds=util.CredentialProvider(),
        name=repo,
        transport=util.Http(),
    ) as r:
      return GCRUsage(str(repo), r.check_usage_only())
  except (
      docker_http.V2DiagnosticException,
      docker_http.TokenRefreshException,
  ) as e:
    return GCRUsage(str(repo), str(e))


def _BucketToRepo(
    bucket: asset_client_util.GetMessages().ResourceSearchResult,
) -> docker_name.Repository:
  """Converts a GCS bucket to a GCR repo.

  Args:
    bucket: A CAIS ResourceSearchResult for a GCS bucket.

  Returns:
    A docker repository.
  """

  project_prefix = f'//cloudresourcemanager.{properties.VALUES.core.universe_domain.Get()}/projects/'
  if not bucket.parentFullResourceName.startswith(project_prefix):
    log.warning(
        f'{bucket.parentFullResourceName} is not a Project name. Skipping...'
    )
    return None
  project_id = bucket.parentFullResourceName.removeprefix(project_prefix)

  bucket_prefix = f'//storage.{properties.VALUES.core.universe_domain.Get()}/'
  bucket_suffix = _BucketSuffix(project_id)
  if not bucket.name.startswith(bucket_prefix) or not bucket.name.endswith(
      bucket_suffix
  ):
    log.warning(
        f'{bucket.name} is not a Container Registry bucket. Skipping...',
    )
    return None
  gcr_region_prefix = bucket.name.removeprefix(bucket_prefix).removesuffix(
      bucket_suffix,
  )
  if gcr_region_prefix not in _VALID_GCR_REGION_PREFIX:
    log.warning(
        f'{bucket.name} is not a Container Registry bucket. Skipping...',
    )
    return None

  gcr_repo_path = '{region}gcr.io/{project}'.format(
      region=gcr_region_prefix, project=project_id.replace(':', '/', 1)
  )
  return util.ValidateRepositoryPath(gcr_repo_path)


def _BucketSuffix(project_id: str) -> str:
  """Converts a project ID to a GCR bucket suffix.

  Args:
    project_id: The project ID.

  Returns:
    A string representing the suffix of GCR buckets in the project. The suffix
    format is different for normal projects and domain-scoped projects. For
    example:

    my-proj           -> artifacts.my-proj.appspot.com
    my-domain:my-proj -> artifacts.my-proj.my-domain.a.appspot.com
  """

  chunks = project_id.split(':', 1)
  if len(chunks) == 2:
    # Domain-scoped project.
    return f'artifacts.{chunks[1]}.{chunks[0]}.a.appspot.com'
  return f'artifacts.{project_id}.appspot.com'
