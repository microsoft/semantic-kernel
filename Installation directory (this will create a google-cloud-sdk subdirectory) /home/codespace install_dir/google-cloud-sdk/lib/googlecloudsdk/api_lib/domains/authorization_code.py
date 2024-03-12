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
"""API client library for Cloud Domains operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


class Client(object):
  """API client for Cloud Domains authorization-code."""

  def __init__(self, client, messages=None):
    self.client = client
    self._get_service = self.client.projects_locations_registrations
    # pylint: disable=line-too-long
    self._reset_service = self.client.projects_locations_registrations_authorizationCode
    self.messages = messages or client.MESSAGES_MODULE

  @classmethod
  def FromApiVersion(cls, version):
    return cls(apis.GetClientInstance('domains', version))

  def Get(self, registration_ref):
    # pylint: disable=line-too-long
    request = self.messages.DomainsProjectsLocationsRegistrationsGetAuthorizationCodeRequest(
        name=registration_ref.RelativeName())
    return self._get_service.GetAuthorizationCode(request)

  def Reset(self, registration_ref):
    # pylint: disable=line-too-long
    request = self.messages.DomainsProjectsLocationsRegistrationsAuthorizationCodeResetRequest(
        name=registration_ref.RelativeName())
    return self._reset_service.Reset(request)
