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
"""Fallthrough hooks for edge-cloud commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def GetClusterFallthrough():
  """Python hook to get the value for the '-' cluster.

  See details at:

  https://cloud.google.com/apis/design/design_patterns#list_sub-collections

  This allows us to operate on node pools without needing to specify a specific
  parent cluster.

  Returns:
    The value of the wildcard cluster.
  """
  return '-'
