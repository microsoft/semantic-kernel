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

"""API helpers for the interacting with binauthz."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

V1_ALPHA2 = 'v1alpha2'
V1_BETA1 = 'v1beta1'
V1 = 'v1'

# TODO(b/110493948): Change to the beta surface when making the default.
_DEFAULT_VERSION = V1_ALPHA2


def GetApiVersion(release_track):
  if release_track == base.ReleaseTrack.GA:
    return V1
  elif release_track == base.ReleaseTrack.BETA:
    return V1_BETA1
  elif release_track == base.ReleaseTrack.ALPHA:
    return V1_ALPHA2
  else:
    raise ValueError('Unsupported Release Track: {}'.format(release_track))


def GetClientInstance(version=None):
  if version is None:
    version = _DEFAULT_VERSION
  return apis.GetClientInstance('binaryauthorization', version)


def GetMessagesModule(version=None):
  if version is None:
    version = _DEFAULT_VERSION
  return apis.GetMessagesModule('binaryauthorization', version)
