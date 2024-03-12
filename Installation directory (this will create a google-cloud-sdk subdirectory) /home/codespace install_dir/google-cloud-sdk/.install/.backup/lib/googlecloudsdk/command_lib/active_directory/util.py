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
"""Utilities for `gcloud active-directory`."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import active_directory


def AppendLocationsGlobalToParent(unused_domain_ref, unused_args, request):
  """Add locations/global to parent path, since it isn't automatically populated by apitools."""
  request.parent += "/locations/global"
  return request


def UpdateOperationRequestNameVariable(unused_ref, unused_args, request):
  request.name = request.name + "/locations/global/operations"
  return request


def GetClientForResource(resource_ref):
  api_version = resource_ref.GetCollectionInfo().api_version
  client = active_directory.Client(api_version)
  return client


def GetMessagesForResource(resource_ref):
  api_version = resource_ref.GetCollectionInfo().api_version
  messages = active_directory.Messages(api_version)
  return messages
