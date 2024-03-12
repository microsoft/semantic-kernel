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
"""Cloud Datacatalog entries client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import util


def ParseResourceIntoLookupRequest(resource, request):
  if resource.startswith('//'):
    request.linkedResource = resource
  else:
    request.sqlResource = resource
  return request


class EntriesClient(object):
  """Cloud Datacatalog entries client."""

  def __init__(self):
    self.client = util.GetClientInstance()
    self.messages = util.GetMessagesModule()
    self.entry_lookup_service = self.client.entries
    self.entry_service = self.client.projects_locations_entryGroups_entries

  def Lookup(self, resource):
    request = ParseResourceIntoLookupRequest(
        resource, self.messages.DatacatalogEntriesLookupRequest())
    return self.entry_lookup_service.Lookup(request)

  def Get(self, resource):
    request = self.messages.DatacatalogProjectsLocationsEntryGroupsEntriesGetRequest(
        name=resource.RelativeName())
    return self.entry_service.Get(request)
