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
"""Utilities for dealing with Private CA Resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.core import resources


def MakeGetUriFunc(collection):
  """Returns a function which turns a resource into a uri."""

  def _GetUri(resource):
    registry = resources.REGISTRY.Clone()
    registry.RegisterApiByName('privateca', privateca_base.V1_API_VERSION)
    parsed = registry.Parse(resource.name, collection=collection)
    return parsed.SelfLink()

  return _GetUri
