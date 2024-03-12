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
"""Utilities Assured Workloads API, Client Generation Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope.base import ReleaseTrack

VERSION_MAP = {
    ReleaseTrack.ALPHA: 'v1beta1',
    ReleaseTrack.BETA: 'v1beta1',
    ReleaseTrack.GA: 'v1'
}
API_NAME = 'assuredworkloads'


def GetMessagesModule(release_track=ReleaseTrack.GA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetMessagesModule(API_NAME, api_version)


def GetClientInstance(release_track=ReleaseTrack.GA, no_http=False):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance(API_NAME, api_version, no_http)


def GetApiVersion(release_track=ReleaseTrack.GA):
  return VERSION_MAP.get(release_track)
