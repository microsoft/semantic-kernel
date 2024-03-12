# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Provide Client and Message Instances to Overwatch."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def get_overwatch_client():
  return apis.GetClientInstance('securedlandingzone', 'v1beta', no_http=False)


# Get the slz-overwatch resquest/response messages
def get_overwatch_message():
  client = get_overwatch_client()
  return client.MESSAGES_MODULE


# Get the overwatch service object from the client.
def get_overwatch_service():
  client = get_overwatch_client()
  return client.organizations_locations_overwatches


# Get the organization service object from the client.
def get_organization_service():
  client = get_overwatch_client()
  return client.organizations_locations


# Get the operations service object fropm the client.
def get_operations_service():
  client = get_overwatch_client()
  return client.organizations_locations_operations
