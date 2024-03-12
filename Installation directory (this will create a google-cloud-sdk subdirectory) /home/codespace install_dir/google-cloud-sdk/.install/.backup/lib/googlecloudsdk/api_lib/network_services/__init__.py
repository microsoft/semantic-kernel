# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""API utilities for `gcloud network-services` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

API_VERSION_FOR_TRACK = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
    base.ReleaseTrack.BETA: 'v1beta1',
    base.ReleaseTrack.GA: 'v1',
}
API_NAME = 'networkservices'


def GetMessagesModule(release_track=base.ReleaseTrack.BETA):
  api_version = API_VERSION_FOR_TRACK.get(release_track)
  return apis.GetMessagesModule(API_NAME, api_version)


def GetClientInstance(release_track=base.ReleaseTrack.BETA):
  api_version = API_VERSION_FOR_TRACK.get(release_track)
  return apis.GetClientInstance(API_NAME, api_version)


def GetApiBaseUrl(release_track=base.ReleaseTrack.ALPHA):
  api_version = API_VERSION_FOR_TRACK.get(release_track)
  return resources.GetApiBaseUrlOrThrow(API_NAME, api_version)
