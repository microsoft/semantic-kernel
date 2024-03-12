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
"""API utilities for `gcloud active-directory` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

API_VERSION_FOR_TRACK = {
    base.ReleaseTrack.BETA: 'v1beta1',
    base.ReleaseTrack.ALPHA: 'v1alpha1'
}


def Client(api_version):
  """Creates a managedidentities client."""
  return apis.GetClientInstance('managedidentities', api_version)


def Messages(api_version):
  """Messages for the managedidentities API."""
  return apis.GetMessagesModule('managedidentities', api_version)
