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
"""Functions for creating a client to talk to the App Engine Admin API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class AppengineApiClientBase(object):
  """Base class for App Engine API client."""

  def __init__(self, client):
    self.client = client
    self.project = properties.VALUES.core.project.Get(required=True)

  @property
  def messages(self):
    return self.client.MESSAGES_MODULE

  @classmethod
  def ApiVersion(cls):
    return 'v1'

  @classmethod
  def GetApiClient(cls, api_version=None):
    """Initializes an AppengineApiClient using the specified API version.

    Uses the api_client_overrides/appengine property to determine which client
    version to use if api_version is not set. Additionally uses the
    api_endpoint_overrides/appengine property to determine the server endpoint
    for the App Engine API.

    Args:
      api_version: The api version override.

    Returns:
      An AppengineApiClient used by gcloud to communicate with the App Engine
      API.

    Raises:
      ValueError: If default_version does not correspond to a supported version
      of the API.
    """
    if api_version is None:
      api_version = cls.ApiVersion()

    return cls(core_apis.GetClientInstance('appengine', api_version))

  def _FormatApp(self):
    res = resources.REGISTRY.Parse(
        self.project, params={}, collection='appengine.apps')
    return res.RelativeName()

  def _GetServiceRelativeName(self, service_name):
    res = resources.REGISTRY.Parse(
        service_name,
        params={'appsId': self.project},
        collection='appengine.apps.services')
    return res.RelativeName()

  def _FormatVersion(self, service_name, version_id):
    res = resources.REGISTRY.Parse(
        version_id,
        params={'appsId': self.project,
                'servicesId': service_name},
        collection='appengine.apps.services.versions')
    return res.RelativeName()

  def _FormatOperation(self, op_id):
    res = resources.REGISTRY.Parse(
        op_id,
        params={'appsId': self.project},
        collection='appengine.apps.operations')
    return res.RelativeName()
