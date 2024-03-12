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
"""Useful commands for interacting with the Immersive Stream for XR API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

_API_NAME = 'stream'
_VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
    base.ReleaseTrack.GA: 'v1'
}


def GetApiVersion(release_track):
  return _VERSION_MAP.get(release_track)


def GetClient(release_track):
  """Import and return the appropriate projects client.

  Args:
    release_track: the release track of the command, either ALPHA or GA

  Returns:
    Immersive Stream for XR client for the appropriate release track.
  """
  return apis.GetClientInstance(_API_NAME, GetApiVersion(release_track))


def GetMessages(release_track):
  """Import and return the appropriate projects messages module.

  Args:
    release_track: the release track of the command, either ALPHA or GA

  Returns:
    Immersive Stream for XR message.
  """
  return apis.GetMessagesModule(_API_NAME, GetApiVersion(release_track))
