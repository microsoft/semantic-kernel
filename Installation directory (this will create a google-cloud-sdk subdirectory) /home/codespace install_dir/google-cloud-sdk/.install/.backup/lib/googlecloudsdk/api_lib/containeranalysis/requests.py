# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utility for making containeranalysis API calls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources


def GetClient():
  return apis.GetClientInstance('containeranalysis', 'v1')


def GetMessages():
  return apis.GetMessagesModule('containeranalysis', 'v1')


def GetClientV1beta1():
  return apis.GetClientInstance('containeranalysis', 'v1beta1')


def GetMessagesV1beta1():
  return apis.GetMessagesModule('containeranalysis', 'v1beta1')


def ExportSbomV1beta1(project, uri):
  """Export SBOM for AR image resources."""
  client = GetClientV1beta1()
  messages = GetMessagesV1beta1()
  resource_ref = resources.REGISTRY.Create(
      'containeranalysis.projects.resources',
      projectsId=project,
      resourcesId=uri
  )
  name = resource_ref.RelativeName()
  req = messages.ContaineranalysisProjectsResourcesExportSBOMRequest(name=name)
  return client.projects_resources.ExportSBOM(req)


def ListOccurrencesV1beta1(project, res_filter, page_size=1000):
  """List occurrences for resources in a project."""
  client = GetClientV1beta1()
  messages = GetMessagesV1beta1()
  project_ref = resources.REGISTRY.Parse(
      project, collection='cloudresourcemanager.projects'
  )
  return list_pager.YieldFromList(
      client.projects_occurrences,
      request=messages.ContaineranalysisProjectsOccurrencesListRequest(
          parent=project_ref.RelativeName(), filter=res_filter
      ),
      field='occurrences',
      batch_size=page_size,
      batch_size_attribute='pageSize',
  )


def ListOccurrencesWithFiltersV1beta1(project, filters):
  """List occurrences for resources in a project with multiple filters."""
  results = [ListOccurrencesV1beta1(project, f) for f in filters]
  return itertools.chain(*results)


def ListOccurrences(project, res_filter, page_size=1000):
  """List occurrences for resources in a project."""
  client = GetClient()
  messages = GetMessages()
  project_ref = resources.REGISTRY.Parse(
      project, collection='cloudresourcemanager.projects')
  return list_pager.YieldFromList(
      client.projects_occurrences,
      request=messages.ContaineranalysisProjectsOccurrencesListRequest(
          parent=project_ref.RelativeName(), filter=res_filter),
      field='occurrences',
      batch_size=page_size,
      batch_size_attribute='pageSize')


def ListOccurrencesWithFilters(project, filters):
  """List occurrences for resources in a project with multiple filters."""
  results = [ListOccurrences(project, f) for f in filters]
  return itertools.chain(*results)


def GetVulnerabilitySummary(project, res_filter):
  """Get vulnerability summary for resources in a project."""
  client = GetClient()
  messages = GetMessages()
  project_ref = resources.REGISTRY.Parse(
      project, collection='cloudresourcemanager.projects')
  req = (
      messages
      .ContaineranalysisProjectsOccurrencesGetVulnerabilitySummaryRequest(
          parent=project_ref.RelativeName(), filter=res_filter))
  return client.projects_occurrences.GetVulnerabilitySummary(req)


def GetVulnerabilitySummaryWithFilters(project, filters):
  """Get vulnerability summary for resources in a project with multiple filters."""
  return [GetVulnerabilitySummary(project, f) for f in filters]
