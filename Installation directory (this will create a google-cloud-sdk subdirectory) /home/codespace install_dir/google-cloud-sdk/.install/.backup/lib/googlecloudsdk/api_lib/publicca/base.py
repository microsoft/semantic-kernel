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
"""Shared utilities for accessing the Public CA API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

DEFAULT_API_VERSION = 'v1'


def GetClientClass(api_version=DEFAULT_API_VERSION):
  return apis.GetClientClass('publicca', api_version)


def GetClientInstance(api_version=DEFAULT_API_VERSION):
  return apis.GetClientInstance('publicca', api_version)


def GetMessagesModule(api_version=DEFAULT_API_VERSION):
  return apis.GetMessagesModule('publicca', api_version)


def GetVersion(release_track):
  if release_track is base.ReleaseTrack.GA:
    return 'v1'
  elif release_track is base.ReleaseTrack.BETA:
    return 'v1beta1'
  else:
    return 'v1alpha1'
