# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for Eventarc Providers API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.eventarc import common
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources


def GetProvidersURI(resource):
  provider = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='eventarc.projects.locations.providers')
  return provider.SelfLink()


class ProvidersClient(object):
  """Client for event providers in Eventarc API."""

  def __init__(self, release_track):
    api_version = common.GetApiVersion(release_track)
    client = apis.GetClientInstance(common.API_NAME, api_version)
    self._messages = client.MESSAGES_MODULE
    self._service = client.projects_locations_providers

  def List(self, location, limit, page_size):
    """Lists event providers in a given location.

    Args:
      location: str, the relative name of the location to list event providers
        in.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of event providers in the location.
    """
    list_req = self._messages.EventarcProjectsLocationsProvidersListRequest(
        parent=location, pageSize=page_size)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='providers',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize')

  def Get(self, provider_ref):
    """Gets a Provider.

    Args:
      provider_ref: Resource, the Provider to get.

    Returns:
      The Provider message.
    """
    get_req = self._messages.EventarcProjectsLocationsProvidersGetRequest(
        name=provider_ref.RelativeName())
    return self._service.Get(get_req)
