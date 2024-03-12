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
"""GKEHUB API client utils."""

# TODO(b/181243034): This file should be replaced with `util.py` once
# the Membership API is on version selector.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base

GKEHUB_API_NAME = 'gkehub'
GKEHUB_ALPHA_API_VERSION = 'v1alpha'
GKEHUB_BETA_API_VERSION = 'v1beta1'
GKEHUB_GA_API_VERSION = 'v1'


def GetApiVersionForTrack(release_track=None):
  if not release_track:
    return core_apis.ResolveVersion(GKEHUB_API_NAME)
  elif release_track == base.ReleaseTrack.ALPHA:
    return GKEHUB_ALPHA_API_VERSION
  elif release_track == base.ReleaseTrack.BETA:
    return GKEHUB_BETA_API_VERSION
  elif release_track == base.ReleaseTrack.GA:
    return GKEHUB_GA_API_VERSION
  return core_apis.ResolveVersion(GKEHUB_API_NAME)


def GetApiClientForApiVersion(api_version=None):
  if not api_version:
    api_version = core_apis.ResolveVersion(GKEHUB_API_NAME)
  return core_apis.GetClientInstance(GKEHUB_API_NAME, api_version)


def GetApiClientForTrack(release_track=base.ReleaseTrack.GA):
  return GetApiClientForApiVersion(
      GetApiVersionForTrack(release_track=release_track))
