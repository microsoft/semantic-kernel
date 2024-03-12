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
"""Shared utilities for accessing the Private CA API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

import six.moves.urllib.parse

DEFAULT_API_VERSION = 'v1'
V1_API_VERSION = 'v1'


def GetClientClass(api_version=DEFAULT_API_VERSION):
  return apis.GetClientClass('privateca', api_version)


def GetClientInstance(api_version=DEFAULT_API_VERSION):
  return apis.GetClientInstance('privateca', api_version)


def GetMessagesModule(api_version=DEFAULT_API_VERSION):
  return apis.GetMessagesModule('privateca', api_version)


def GetServiceName(api_version=DEFAULT_API_VERSION):
  """Gets the service name based on the configured API endpoint."""
  endpoint = apis.GetEffectiveApiEndpoint('privateca', api_version)
  return six.moves.urllib.parse.urlparse(endpoint).hostname
