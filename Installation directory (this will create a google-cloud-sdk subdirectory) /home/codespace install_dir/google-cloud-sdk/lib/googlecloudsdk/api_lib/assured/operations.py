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
"""Utilities Assured Workloads API, Operations Endpoints."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.assured import util
from googlecloudsdk.core import resources


def GetWorkloadURI(resource):
  workload = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='assuredworkloads.organizations.locations.operations')
  return workload.SelfLink()


class OperationsClient(object):
  """Client for operations in Assured Workloads API."""

  def __init__(self, release_track, no_http=False):
    self.client = util.GetClientInstance(release_track, no_http)
    self.messages = util.GetMessagesModule(release_track)
    self._service = self.client.organizations_locations_operations

  def List(self, parent, limit=None, page_size=100):
    """List all Assured Workloads operations that belong to the given parent organization.

    Args:
      parent: str, the parent organization of the Assured Workloads operations
        to be listed, in the form: organizations/{ORG_ID}/locations/{LOCATION}.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A list of all Assured Workloads operations that belong to the given parent
      organization.
    """
    list_req = self.messages.AssuredworkloadsOrganizationsLocationsOperationsListRequest(
        name=parent, pageSize=page_size)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='operations',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute=None)

  def Describe(self, name):
    """Describe an Assured Workloads operation.

    Args:
      name: str, the name for the Assured Operation being described.

    Returns:
      Described Assured Workloads operation resource.
    """
    describe_req = self.messages.AssuredworkloadsOrganizationsLocationsOperationsGetRequest(
        name=name)
    return self.client.organizations_locations_operations.Get(describe_req)
