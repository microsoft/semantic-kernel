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
"""Utilities for Locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.recommender import base
from googlecloudsdk.api_lib.recommender import flag_utils
from googlecloudsdk.command_lib.projects import util


def CreateClient(release_track):
  """Creates Client.

  Args:
    release_track: release_track value, can be ALPHA, BETA, GA

  Returns:
    The versioned client.
  """
  api_version = flag_utils.GetApiVersion(release_track)
  return Location(api_version)


class Location(base.ClientBase):
  """Base Location client for all versions."""

  def List(self, page_size, project=None, folder=None,
           organization=None, billing_account=None, limit=None):
    """List Locations.

    Args:
      page_size: int, The number of items to retrieve per request.
      project: string, The project name to retrieve locations for.
      folder: string, The folder name to retrieve locations for.
      organization: string, The organization name to retrieve locations for.
      billing_account: string, The billing project to retrieve locations for.
      limit: int, The maximum number of records to yield.

    Returns:
      The list of Locations.
    """
    # Using Project message is ok for all entities if the name is correct.
    folder_locations, organization_locations, project_locations = [], [], []
    billing_account_locations = []

    if folder:
      self._service = self._client.folders_locations
      request = self._messages.RecommenderFoldersLocationsListRequest(
          name='folders/' + folder
      )
      folder_locations = list_pager.YieldFromList(
          self._service,
          request,
          batch_size_attribute='pageSize',
          batch_size=page_size,
          limit=limit,
          field='locations',
      )
    if organization:
      self._service = self._client.organizations_locations
      request = self._messages.RecommenderOrganizationsLocationsListRequest(
          name='organizations/' + organization
      )
      organization_locations = list_pager.YieldFromList(
          self._service,
          request,
          batch_size_attribute='pageSize',
          batch_size=page_size,
          limit=limit,
          field='locations',
      )
    if project:
      self._service = self._client.projects_locations
      request = self._messages.RecommenderProjectsLocationsListRequest(
          name='projects/' + str(util.GetProjectNumber(project))
      )
      project_locations = list_pager.YieldFromList(
          self._service,
          request,
          batch_size_attribute='pageSize',
          batch_size=page_size,
          limit=limit,
          field='locations',
      )
    if billing_account:
      self._service = self._client.billingAccounts_locations
      request = self._messages.RecommenderBillingAccountsLocationsListRequest(
          name='billing-accounts/' + billing_account
      )
      billing_account_locations = list_pager.YieldFromList(
          self._service,
          request,
          batch_size_attribute='pageSize',
          batch_size=page_size,
          limit=limit,
          field='locations',
      )

    return itertools.chain(
        folder_locations,
        organization_locations,
        project_locations,
        billing_account_locations,
    )
