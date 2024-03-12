# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""SourceRepo APIs layer.

Parse methods accepts strings from command-line arguments, and it can accept
more formats like "https://...". Get methods are strict about the arguments.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import six


class RepoResourceError(core_exceptions.Error):
  """Raised when a repo could not be parsed."""


def ParseRepo(repo):
  """Parse a string as a sourcerepo.projects.repos resource."""
  try:
    return resources.REGISTRY.Parse(
        repo,
        params={'projectsId': properties.VALUES.core.project.GetOrFail},
        collection='sourcerepo.projects.repos')
  except core_exceptions.Error as e:
    raise RepoResourceError(six.text_type(e))


def GetDefaultProject():
  """Create a sourcerepo.projects resource of the default project."""
  return resources.REGISTRY.Create(
      'sourcerepo.projects',
      projectsId=properties.VALUES.core.project.GetOrFail())


class Source(object):
  """Base class for sourcerepo api wrappers."""

  def __init__(self, client=None):
    if client is None:
      client = apis.GetClientInstance('sourcerepo', 'v1')
    self._client = client
    self.messages = apis.GetMessagesModule('sourcerepo', 'v1')

  def GetIamPolicy(self, repo_resource):
    """Gets IAM policy for a repo.

    Args:
      repo_resource:  The repo resource with collection type
        sourcerepo.projects.repos
    Returns:
      (messages.Policy) The IAM policy.
    """
    request = self.messages.SourcerepoProjectsReposGetIamPolicyRequest(
        resource=repo_resource.RelativeName())
    return self._client.projects_repos.GetIamPolicy(request)

  def SetIamPolicy(self, repo_resource, policy):
    """Sets the IAM policy from a policy string.

    Args:
      repo_resource: The repo as a resource with colleciton type
        sourcerepo.projects.repos
      policy: (string) The file containing the new IAM policy.
    Returns:
      (messages.Policy) The IAM policy.
    """
    req = self.messages.SetIamPolicyRequest(policy=policy)
    request = self.messages.SourcerepoProjectsReposSetIamPolicyRequest(
        resource=repo_resource.RelativeName(), setIamPolicyRequest=req)
    return self._client.projects_repos.SetIamPolicy(request)

  def ListRepos(self, project_resource, limit=None, page_size=None):
    """Returns list of repos."""
    return list_pager.YieldFromList(
        self._client.projects_repos,
        self.messages.SourcerepoProjectsReposListRequest(
            name=project_resource.RelativeName()),
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='repos')

  def GetRepo(self, repo_resource):
    """Finds details on the named repo, if it exists.

    Args:
      repo_resource: (Resource) A resource representing the repo to create.
    Returns:
      (messages.Repo) The full definition of the new repo, as reported by
        the server.
      Returns None if the repo does not exist.
    """
    request = self.messages.SourcerepoProjectsReposGetRequest(
        name=repo_resource.RelativeName())
    return self._client.projects_repos.Get(request)

  def CreateRepo(self, repo_resource):
    """Creates a repo.

    Args:
      repo_resource: (Resource) A resource representing the repo to create.
    Returns:
      (messages.Repo) The full definition of the new repo, as reported by
        the server.
    """
    parent = resources.REGISTRY.Create(
        'sourcerepo.projects', projectsId=repo_resource.projectsId)
    request = self.messages.SourcerepoProjectsReposCreateRequest(
        parent=parent.RelativeName(),
        repo=self.messages.Repo(name=repo_resource.RelativeName()))
    return self._client.projects_repos.Create(request)

  def DeleteRepo(self, repo_resource):
    """Deletes a repo.

    Args:
      repo_resource: (Resource) A resource representing the repo to create.
    """
    request = self.messages.SourcerepoProjectsReposDeleteRequest(
        name=repo_resource.RelativeName())
    self._client.projects_repos.Delete(request)

  def PatchRepo(self, repo, update_mask='pubsubConfigs'):
    """Updates a repo's configuration."""
    req = self.messages.SourcerepoProjectsReposPatchRequest(
        name=repo.name,
        updateRepoRequest=self.messages.UpdateRepoRequest(
            repo=repo, updateMask=update_mask))
    return self._client.projects_repos.Patch(req)
