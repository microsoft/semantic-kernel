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

"""Utility functions for the KMS Inventory CLI."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis

DEFAULT_API_NAME = 'kmsinventory'
DEFAULT_API_VERSION = 'v1'


# The messages module can also be accessed from client.MESSAGES_MODULE
def GetClientInstance():
  return apis.GetClientInstance(DEFAULT_API_NAME, DEFAULT_API_VERSION)


def GetMessagesModule():
  return apis.GetMessagesModule(DEFAULT_API_NAME, DEFAULT_API_VERSION)


def ListKeys(project, args):
  client = GetClientInstance()
  request = GetMessagesModule().KmsinventoryProjectsCryptoKeysListRequest(
      parent='projects/' + project)

  return list_pager.YieldFromList(
      client.projects_cryptoKeys,
      request,
      limit=args.limit,
      batch_size_attribute='pageSize',
      batch_size=args.page_size,
      field='cryptoKeys')


def GetProtectedResourcesSummary(name):
  client = GetClientInstance()
  request = GetMessagesModule(
  ).KmsinventoryProjectsLocationsKeyRingsCryptoKeysGetProtectedResourcesSummaryRequest(
      name=name)
  return client.projects_locations_keyRings_cryptoKeys.GetProtectedResourcesSummary(
      request)


def SearchProtectedResources(scope, key_name, resource_types, args):
  client = GetClientInstance()
  request = GetMessagesModule().KmsinventoryOrganizationsProtectedResourcesSearchRequest(
      scope=scope, cryptoKey=key_name, resourceTypes=resource_types
  )

  return list_pager.YieldFromList(
      client.organizations_protectedResources,
      request,
      method='Search',
      limit=args.limit,
      batch_size_attribute='pageSize',
      batch_size=args.page_size,
      field='protectedResources',
  )
