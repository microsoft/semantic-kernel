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
"""API client library for Cloud DNS active peering zones."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


class Client(object):
  """API client for Cloud DNS active peering zones."""

  _API_NAME = 'dns'

  def __init__(self, version, client, messages=None):
    self.version = version
    self.client = client
    self._service = self.client.activePeeringZones
    self.messages = messages or self.client.MESSAGES_MODULE

  @classmethod
  def FromApiVersion(cls, version):
    return cls(version, apis.GetClientInstance(cls._API_NAME, version))
