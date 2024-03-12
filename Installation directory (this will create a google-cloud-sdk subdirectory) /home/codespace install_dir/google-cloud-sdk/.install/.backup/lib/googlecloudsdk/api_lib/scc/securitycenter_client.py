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
"""Useful commands for interacting with the Cloud SCC API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions

API_NAME = 'securitycenter'
BETA_API_VERSION = 'v1beta1'
V1_API_VERSION = 'v1'
V1P1BETA1_API_VERSION = 'v1p1beta1'
V2_API_VERSION = 'v2'


def GetClient(version=V1_API_VERSION):
  """Import and return the appropriate Cloud SCC client.

  Args:
    version: str, the version of the API desired.

  Returns:
    Cloud SCC client for the appropriate release track.
  """
  return apis.GetClientInstance(API_NAME, version)


def GetMessages(version=V1_API_VERSION):
  """Import and return the appropriate Cloud SCC messages module."""
  return apis.GetMessagesModule(API_NAME, version)


class AssetsClient(object):
  """Client for Security Center service in the for the Asset APIs."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClient()
    self.messages = messages or GetMessages()
    self._assetservice = self.client.organizations_assets

  def List(self, parent, request_filter=None):
    list_req_type = (self.messages.SecuritycenterOrganizationsAssetsListRequest)

    list_req = list_req_type(parent=parent, filter=request_filter)

    return self._assetservice.List(list_req)


class Error(exceptions.Error):
  """Base class for exceptions in this module."""
