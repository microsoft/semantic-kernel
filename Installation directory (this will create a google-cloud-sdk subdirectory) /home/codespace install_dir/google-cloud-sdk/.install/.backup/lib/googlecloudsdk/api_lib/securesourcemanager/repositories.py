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
"""The Secure Source Manager repositories client module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

VERSION_MAP = {base.ReleaseTrack.ALPHA: 'v1'}


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance('securesourcemanager', api_version)


@contextlib.contextmanager
def OverrideApiEndpointOverrides(temp_endpoint):
  """Context manager to override securesourcemanager endpoint overrides temporarily.

  Args:
    temp_endpoint: new endpoint value

  Yields:
    None
  """
  endpoint_property = getattr(
      properties.VALUES.api_endpoint_overrides, 'securesourcemanager'
  )
  old_endpoint = endpoint_property.Get()

  try:
    endpoint_property.Set(temp_endpoint)
    yield
  finally:
    endpoint_property.Set(old_endpoint)


class RepositoriesClient(object):
  """Client for Secure Source Manager repositories."""

  def __init__(self):
    self.client = GetClientInstance(base.ReleaseTrack.ALPHA)
    self.messages = self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_repositories
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName('securesourcemanager', 'v1')

  def Create(
      self,
      repository_ref,
      description,
      default_branch,
      gitignores,
      license_name,
      readme,
  ):
    """Create a new Secure Source Manager repository.

    Args:
      repository_ref: a resource reference to
        securesourcemanager.projects.locations.repositories.
      description: description of the repository
      default_branch: default branch name of the repository
      gitignores: list of gitignore template names
      license_name: license template name
      readme: README template name

    Returns:
      Created repository.
    """
    initial_config = self.messages.InitialConfig(
        defaultBranch=default_branch,
        gitignores=gitignores,
        license=license_name,
        readme=readme,
    )
    repository = self.messages.Repository(
        description=description,
        initialConfig=initial_config,
    )
    create_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesCreateRequest(
        parent=repository_ref.Parent().RelativeName(),
        repository=repository,
        repositoryId=repository_ref.repositoriesId,
    )
    return self._service.Create(create_req)

  def Describe(self, repository_ref):
    """Get metadata for a Secure Source Manager repository.

    Args:
      repository_ref: a resource reference to
        securesourcemanager.projects.locations.repositories.

    Returns:
    Description of repository.
    """
    get_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesGetRequest(
        name=repository_ref.RelativeName()
    )
    return self._service.Get(get_req)

  def Delete(self, repository_ref, allow_missing):
    """Delete a Secure Source Manager repository.

    Args:
      repository_ref: a Resource reference to a
        securesourcemanager.projects.locations.repositories resource.
      allow_missing: Optional. If set to true, and the repository is not found,
        the request will succeed but no action will be taken on the server.

    Returns:
    Deleted Repository Resource.
    """

    delete_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesDeleteRequest(
        allowMissing=allow_missing, name=repository_ref.RelativeName()
    )
    return self._service.Delete(delete_req)

  def List(self, location_ref, page_size, page_token):
    """Lists repositories in a Secure Source Manager instance.

    Args:
      location_ref: a Resource reference to a
        securesourcemanager.projects.locations resource.
      page_size: Optional. Requested page size. Server may return fewer items
        than requested. If unspecified, server will pick an appropriate default.
      page_token: A token identifying a page of results the server should
        return.

    Returns:
    List of repositories.
    """
    list_req = self.messages.SecuresourcemanagerProjectsLocationsRepositoriesListRequest(
        pageSize=page_size,
        pageToken=page_token,
        parent=location_ref.RelativeName(),
    )

    return self._service.List(list_req)
