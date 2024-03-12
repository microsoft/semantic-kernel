# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Utilities Service Directory locations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import base as sd_base
from googlecloudsdk.calliope import base


class LocationsClient(sd_base.ServiceDirectoryApiLibBase):
  """Client for locations in the Service Directory API."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(LocationsClient, self).__init__(release_track)
    self.service = self.client.projects_locations

  def List(self, project_ref):
    """Locations list request."""
    list_req = self.msgs.ServicedirectoryProjectsLocationsListRequest(
        name=project_ref.RelativeName())
    return self.service.List(list_req)

  def Describe(self, location_ref):
    """Locations describe request."""
    describe_req = self.msgs.ServicedirectoryProjectsLocationsGetRequest(
        name=location_ref.RelativeName())
    return self.service.Get(describe_req)
