# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Cloud Datacatalog search client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.data_catalog import util
from googlecloudsdk.command_lib.util.apis import arg_utils


class SearchClient(object):
  """Cloud Datacatalog search client."""

  def __init__(self, version_label):
    self.version_label = version_label
    self.client = util.GetClientInstance(version_label)
    self.messages = util.GetMessagesModule(version_label)
    self.service = self.client.catalog

  def Search(self, query,
             include_gcp_public_datasets,
             include_organization_ids,
             restricted_locations,
             include_project_ids,
             order_by, page_size, limit):
    """Parses search args into the request."""
    if self.version_label == 'v1':
      request = self.messages.GoogleCloudDatacatalogV1SearchCatalogRequest(
          query=query,
          orderBy=order_by,
      )
    else:
      request = self.messages.GoogleCloudDatacatalogV1beta1SearchCatalogRequest(
          query=query,
          orderBy=order_by,
      )
    if include_gcp_public_datasets:
      arg_utils.SetFieldInMessage(
          request, 'scope.includeGcpPublicDatasets',
          include_gcp_public_datasets)
    if include_organization_ids:
      arg_utils.SetFieldInMessage(
          request, 'scope.includeOrgIds',
          include_organization_ids)
    if include_project_ids:
      arg_utils.SetFieldInMessage(
          request, 'scope.includeProjectIds',
          include_project_ids)
    if restricted_locations:
      arg_utils.SetFieldInMessage(
          request, 'scope.restrictedLocations',
          restricted_locations)

    return list_pager.YieldFromList(
        self.service, request,
        batch_size=page_size,
        limit=limit,
        method='Search',
        field='results',
        batch_size_attribute='pageSize',
    )
