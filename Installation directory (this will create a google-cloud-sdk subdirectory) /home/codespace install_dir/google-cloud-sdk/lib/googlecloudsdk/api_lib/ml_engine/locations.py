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
"""Utilities for dealing with ML locations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class NoFieldsSpecifiedError(exceptions.Error):
  """Error indicating that no updates were requested in a Patch operation."""


def _ParseLocation(location):
  return resources.REGISTRY.Parse(
      location,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='ml.projects.locations')


class LocationsClient(object):
  """High-level client for the AI Platform locations surface."""

  def __init__(self, client=None, messages=None):
    self.client = client or apis.GetClientInstance('ml', 'v1')
    self.messages = messages or self.client.MESSAGES_MODULE

  def Get(self, location):
    """Get details about a location."""
    location_ref = _ParseLocation(location)
    req = self.messages.MlProjectsLocationsGetRequest(
        name=location_ref.RelativeName())
    return self.client.projects_locations.Get(req)

  def List(self, project_ref):
    """List available locations for the project."""
    req = self.messages.MlProjectsLocationsListRequest(
        parent=project_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.projects_locations,
        req,
        field='locations',
        batch_size_attribute='pageSize')
