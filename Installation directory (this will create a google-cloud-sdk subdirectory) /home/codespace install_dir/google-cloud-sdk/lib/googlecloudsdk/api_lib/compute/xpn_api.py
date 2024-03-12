# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Utilities for the API to configure cross-project networking (XPN)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.api_lib.compute import utils


_DEFAULT_API_VERSION = 'v1'


class XpnApiError(exceptions.Error):
  pass


class XpnClient(object):
  """A client for interacting with the cross-project networking (XPN) API.

  The XPN API is a subset of the Google Compute Engine API.
  """

  def __init__(self, compute_client):
    self.compute_client = compute_client
    self.client = compute_client.apitools_client
    self.messages = compute_client.messages

  def _MakeRequest(self, request, errors):
    return self.compute_client.MakeRequests(
        requests=[request],
        errors_to_collect=errors)

  def _MakeRequestSync(self, request_tuple, operation_msg=None):
    errors = []
    results = list(self._MakeRequest(request_tuple, errors))

    if errors:
      operation_msg = operation_msg or 'complete all requests'
      msg = 'Could not {0}:'.format(operation_msg)
      utils.RaiseException(errors, XpnApiError, msg)

    return results[0]  # if there were no errors, this will exist

  def EnableHost(self, project):
    """Enable the project with the given ID as an XPN host."""
    request_tuple = (
        self.client.projects,
        'EnableXpnHost',
        self.messages.ComputeProjectsEnableXpnHostRequest(project=project))
    msg = 'enable [{project}] as XPN host'.format(project=project)
    self._MakeRequestSync(request_tuple, msg)

  def DisableHost(self, project):
    """Disable the project with the given ID as an XPN host."""
    request_tuple = (
        self.client.projects,
        'DisableXpnHost',
        self.messages.ComputeProjectsDisableXpnHostRequest(project=project))
    msg = 'disable [{project}] as XPN host'.format(project=project)
    self._MakeRequestSync(request_tuple, msg)

  def GetHostProject(self, project):
    """Get the XPN host for the given project."""
    request_tuple = (
        self.client.projects,
        'GetXpnHost',
        self.messages.ComputeProjectsGetXpnHostRequest(project=project))
    msg = 'get XPN host for project [{project}]'.format(project=project)
    return self._MakeRequestSync(request_tuple, msg)

  def ListEnabledResources(self, project):
    request = self.messages.ComputeProjectsGetXpnResourcesRequest(
        project=project)
    return list_pager.YieldFromList(
        self.client.projects,
        request,
        method='GetXpnResources',
        batch_size_attribute='maxResults',
        batch_size=500,
        field='resources')

  def ListOrganizationHostProjects(self, project, organization_id):
    """List the projects in an organization that are enabled as XPN hosts.

    Args:
      project: str, project ID to make the request with.
      organization_id: str, the ID of the organization to list XPN hosts
          for. If None, the organization is inferred from the project.

    Returns:
      Generator for `Project`s corresponding to XPN hosts in the organization.
    """
    request = self.messages.ComputeProjectsListXpnHostsRequest(
        project=project,
        projectsListXpnHostsRequest=self.messages.ProjectsListXpnHostsRequest(
            organization=organization_id))
    return list_pager.YieldFromList(
        self.client.projects,
        request,
        method='ListXpnHosts',
        batch_size_attribute='maxResults',
        batch_size=500,
        field='items')

  def _EnableXpnAssociatedResource(self, host_project, associated_resource,
                                   xpn_resource_type):
    """Associate the given resource with the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_resource: ID of the resource to associate with host_project
      xpn_resource_type: XpnResourceId.TypeValueValuesEnum, the type of the
         resource
    """
    projects_enable_request = self.messages.ProjectsEnableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(
            id=associated_resource,
            type=xpn_resource_type)
    )
    request = self.messages.ComputeProjectsEnableXpnResourceRequest(
        project=host_project,
        projectsEnableXpnResourceRequest=projects_enable_request)
    request_tuple = (self.client.projects, 'EnableXpnResource', request)
    msg = ('enable resource [{0}] as an associated resource '
           'for project [{1}]').format(associated_resource, host_project)
    self._MakeRequestSync(request_tuple, msg)

  def EnableXpnAssociatedProject(self, host_project, associated_project):
    """Associate the given project with the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_project: ID of the project to associate
    """
    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    self._EnableXpnAssociatedResource(
        host_project, associated_project, xpn_resource_type=xpn_types.PROJECT)

  def _DisableXpnAssociatedResource(self, host_project, associated_resource,
                                    xpn_resource_type):
    """Disassociate the given resource from the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_resource: ID of the resource to disassociate from host_project
      xpn_resource_type: XpnResourceId.TypeValueValuesEnum, the type of the
         resource
    """
    projects_disable_request = self.messages.ProjectsDisableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(
            id=associated_resource,
            type=xpn_resource_type)
    )
    request = self.messages.ComputeProjectsDisableXpnResourceRequest(
        project=host_project,
        projectsDisableXpnResourceRequest=projects_disable_request)
    request_tuple = (self.client.projects, 'DisableXpnResource', request)
    msg = ('disable resource [{0}] as an associated resource '
           'for project [{1}]').format(associated_resource, host_project)
    self._MakeRequestSync(request_tuple, msg)

  def DisableXpnAssociatedProject(self, host_project, associated_project):
    """Disassociate the given project from the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_project: ID of the project to disassociate from host_project
    """
    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    self._DisableXpnAssociatedResource(
        host_project, associated_project, xpn_resource_type=xpn_types.PROJECT)


def GetXpnClient(release_track):
  holder = base_classes.ComputeApiHolder(release_track)
  return XpnClient(holder.client)
