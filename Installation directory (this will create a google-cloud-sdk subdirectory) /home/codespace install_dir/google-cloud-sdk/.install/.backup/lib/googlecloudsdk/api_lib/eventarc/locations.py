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
"""Utilities for Eventarc Locations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.eventarc import common
from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def GetLocationsURI(resource):
  location = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='eventarc.projects.locations')
  return location.SelfLink()


class LocationsClient(object):
  """Client for locations in Eventarc API."""

  def __init__(self, release_track):
    api_version = common.GetApiVersion(release_track)
    client = apis.GetClientInstance(common.API_NAME, api_version)
    self.messages = client.MESSAGES_MODULE
    self._service = client.projects_locations

  def List(self, limit, page_size):
    """List locations in the Eventarc API.

    Args:
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      Generator of locations.
    """
    project_resource_relname = util.ProjectPath(
        properties.VALUES.core.project.Get(required=True))
    list_req = self.messages.EventarcProjectsLocationsListRequest(
        name=project_resource_relname)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='locations',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize')
