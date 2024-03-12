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
"""API client library for Cloud DNS managed zones."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dns import util


class Client(object):
  """API client for Cloud DNS managed zones."""

  _API_NAME = 'dns'

  def __init__(self, version, client, messages=None):
    self.version = version
    self.client = client
    self._service = self.client.dnsKeys
    self.messages = messages or client.MESSAGES_MODULE

  @classmethod
  def FromApiVersion(cls, version):
    return cls(version, util.GetApiClient(version))

  def Get(self, key_ref):
    return self._service.Get(
        self.messages.DnsDnsKeysGetRequest(
            dnsKeyId=key_ref.Name(),
            managedZone=key_ref.managedZone,
            project=key_ref.project))

  def List(self, zone_ref):
    request = self.messages.DnsDnsKeysListRequest(
        project=zone_ref.project,
        managedZone=zone_ref.Name())
    return list_pager.YieldFromList(self._service, request, field='dnsKeys')
