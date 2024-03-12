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
"""API utilities for `gcloud network-management simulation` commands."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


def Client(api_version):
  """Creates a simulation client."""
  return apis.GetClientInstance('networkmanagement', api_version)


def Messages(api_version):
  """Messages for the simulation API."""
  return apis.GetMessagesModule('networkmanagement', api_version)
