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
"""Utility for retrieving and parsing the Resource Map."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.util.resource_map.base import ResourceMapBase

_RESOURCE_MAP_PATH = os.path.join(
    os.path.dirname(__file__), ('declarative_map.yaml'))
_RESOURCE_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), ('declarative_map_schema.yaml'))


class DeclarativeMap(ResourceMapBase):
  """Resource map for declarative command generation metadata."""

  def _register_paths(self):
    self._map_file_path = _RESOURCE_MAP_PATH
    self._schema_file_path = _RESOURCE_SCHEMA_PATH
