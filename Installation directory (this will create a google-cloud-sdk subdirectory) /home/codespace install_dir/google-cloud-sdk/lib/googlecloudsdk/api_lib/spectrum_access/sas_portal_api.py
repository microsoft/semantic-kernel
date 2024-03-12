# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Spectrum Access System Portal API client utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import frozendict

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

VERSION_MAP = frozendict.frozendict({base.ReleaseTrack.ALPHA: 'v1alpha1'})


# The messages module can also be accessed from client.MESSAGES_MODULE
def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetMessagesModule('sasportal', api_version)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance('sasportal', api_version)
