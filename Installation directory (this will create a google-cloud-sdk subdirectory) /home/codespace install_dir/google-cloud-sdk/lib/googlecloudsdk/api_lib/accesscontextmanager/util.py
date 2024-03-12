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
"""API utilities for access context manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter

_API_NAME = 'accesscontextmanager'


def _GetDefaultVersion():
  return apis.ResolveVersion(_API_NAME)


def GetMessages(version=None):
  version = version or _GetDefaultVersion()
  return apis.GetMessagesModule(_API_NAME, version)


def GetClient(version=None):
  version = version or _GetDefaultVersion()
  return apis.GetClientInstance(_API_NAME, version)


class OperationPoller(waiter.CloudOperationPoller):

  def __init__(self, result_service, operation_service, resource_ref):
    super(OperationPoller, self).__init__(result_service, operation_service)
    self.resource_ref = resource_ref

  def GetResult(self, operation):
    del operation  # Unused in GetResult
    request_type = self.result_service.GetRequestType('Get')
    return self.result_service.Get(request_type(
        name=self.resource_ref.RelativeName()))
