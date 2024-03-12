# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Utilities for calling the Composer ImageVersions API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base

LIST_FIELD_NAME = 'imageVersions'
PAGE_SIZE = 1000


class ImageVersionService(object):
  """Provides supported images version from the Image Version API."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    self.client = None
    self.release_track = release_track
    self.messages = api_util.GetMessagesModule(release_track=self.release_track)

  def GetClient(self):
    if self.client is None:
      self.client = api_util.GetClientInstance(
          self.release_track).projects_locations_imageVersions

    return self.client

  def List(self, project_location_ref):
    """Retrieves list of supported images version from the Image Version API."""
    # TODO(b/122741565): Add support for paging
    request = self.messages.ComposerProjectsLocationsImageVersionsListRequest
    locations = [project_location_ref]

    return api_util.AggregateListResults(request, self.GetClient(), locations,
                                         LIST_FIELD_NAME, PAGE_SIZE)
