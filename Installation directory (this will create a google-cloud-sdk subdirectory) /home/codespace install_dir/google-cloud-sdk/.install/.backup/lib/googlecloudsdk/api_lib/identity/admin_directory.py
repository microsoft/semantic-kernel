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
"""Useful commands for interacting with the Cloud Identity Groups API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

API_NAME = 'admin'
API_VERSION = 'v1'


def GetClient(version=API_VERSION):
  """Import and return the appropriate Cloud Identity Groups client.

  Args:
    version: str, the version of the API desired

  Returns:
    Cloud Identity Groups client for the appropriate release track
  """
  return apis.GetClientInstance(API_NAME, version)


def GetMessages(version=API_VERSION):
  """Import and return the appropriate Cloud Identity Groups messages module.

  Args:
    version: str, the version of the API desired

  Returns:
    Cloud Identity Groups messages for the appropriate release track
  """
  return apis.GetMessagesModule(API_NAME, version)


def Preview(directory_users_list_request):
  """Lists users satisfying the query.

  Args:
    directory_users_list_request: DirectoryUsersListRequest

  Returns:
    Users: Response message for List operation
    which is containing a list of user satisfying the query
  """
  client = GetClient()
  return client.users.List(directory_users_list_request)
