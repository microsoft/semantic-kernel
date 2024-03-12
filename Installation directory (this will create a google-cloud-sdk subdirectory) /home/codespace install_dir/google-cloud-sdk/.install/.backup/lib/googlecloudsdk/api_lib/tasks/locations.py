# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""API Library for `gcloud tasks locations`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager


class Locations(object):
  """Client for locations service in the Cloud Tasks API."""

  def __init__(self, messages, locations_service):
    self.messages = messages
    self.locations_service = locations_service

  def Get(self, location_ref):
    request = self.messages.CloudtasksProjectsLocationsGetRequest(
        name=location_ref.RelativeName())
    return self.locations_service.Get(request)

  def List(self, project_ref, limit=None, page_size=100):
    request = self.messages.CloudtasksProjectsLocationsListRequest(
        name=project_ref.RelativeName())
    return list_pager.YieldFromList(
        self.locations_service, request, batch_size=page_size, limit=limit,
        field='locations', batch_size_attribute='pageSize')
