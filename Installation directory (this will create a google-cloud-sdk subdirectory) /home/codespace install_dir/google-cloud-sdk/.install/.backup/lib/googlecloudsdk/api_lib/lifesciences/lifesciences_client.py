# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Common stateful utilities for the gcloud Life Sciences tool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

OPERATION_TIMEOUT = 60 * 20 * 1000


class LifeSciencesClient(object):
  """Client for calling Cloud Life Sciences APIs."""

  def __init__(self):
    super(LifeSciencesClient, self).__init__()
    self._api_version = 'v2beta'
    self._client = None
    self._resources = None

  @property
  def client(self):
    if self._client is None:
      self._client = apis.GetClientInstance('lifesciences', self._api_version)
    return self._client

  @property
  def messages(self):
    return self.client.MESSAGES_MODULE
