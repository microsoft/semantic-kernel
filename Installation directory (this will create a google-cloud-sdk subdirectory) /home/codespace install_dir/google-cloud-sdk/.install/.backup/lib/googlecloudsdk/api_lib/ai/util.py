# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""General utilities for dealing with Vertex AI api messages."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants


def GetMessagesModule(version=constants.GA_VERSION):
  """Returns message module of the corresponding API version."""
  return apis.GetMessagesModule(constants.AI_PLATFORM_API_NAME,
                                constants.AI_PLATFORM_API_VERSION[version])


def GetMessage(message_name, version=constants.GA_VERSION):
  """Returns the Vertex AI api messages class by name."""
  return getattr(
      GetMessagesModule(version), '{prefix}{name}'.format(
          prefix=constants.AI_PLATFORM_MESSAGE_PREFIX[version],
          name=message_name), None)
