# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for Data Catalog entries commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.network_security import GetClientInstance
from googlecloudsdk.api_lib.network_security import GetMessagesModule
from googlecloudsdk.core import log


def LogRemoveItemsSuccess(response, args):
  log.status.Print(
      'Items were removed from address group [{}].'.format(args.address_group)
  )
  return response


def LogAddItemsSuccess(response, args):
  log.status.Print(
      'Items were added to address group [{}].'.format(args.address_group)
  )
  return response


def SetGlobalLocation():
  """Set default location to global."""
  return 'global'


def FormatSourceAddressGroup(_, arg, request):
  source_name = arg.source
  if os.path.basename(source_name) == source_name:
    location = os.path.dirname(request.addressGroup)
    request.cloneAddressGroupItemsRequest.sourceAddressGroup = '%s/%s' % (
        location,
        source_name,
    )
  return request


def LogCloneItemsSuccess(response, args):
  log.status.Print(
      'Items were cloned to address group [{}] from [{}].'.format(
          args.address_group, args.source
      )
  )
  return response


def ListProjectAddressGroupReferences(release_track, args):
  service = GetClientInstance(release_track).projects_locations_addressGroups
  messages = GetMessagesModule(release_track)
  request_type = (
      messages.NetworksecurityProjectsLocationsAddressGroupsListReferencesRequest
  )
  return ListAddressGroupReferences(service, request_type, args)


def ListOrganizationAddressGroupReferences(release_track, args):
  service = GetClientInstance(
      release_track
  ).organizations_locations_addressGroups
  messages = GetMessagesModule(release_track)
  request_type = (
      messages.NetworksecurityOrganizationsLocationsAddressGroupsListReferencesRequest
  )
  return ListAddressGroupReferences(service, request_type, args)


def ListAddressGroupReferences(service, request_type, args):
  address_group = args.CONCEPTS.address_group.Parse()
  request = request_type(addressGroup=address_group.RelativeName())
  return list_pager.YieldFromList(
      service,
      request,
      limit=args.limit,
      batch_size=args.page_size,
      method='ListReferences',
      field='addressGroupReferences',
      current_token_attribute='pageToken',
      next_token_attribute='nextPageToken',
      batch_size_attribute='pageSize',
  )
