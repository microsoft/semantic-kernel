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
"""Utilities for `gcloud redis zones` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py import encoding


RedisZone = collections.namedtuple('RedisZone', ['name', 'region'])


def ExtractZonesFromRegionsListResponse(response, args):
  for region in response:
    if args.IsSpecified('region') and region.locationId != args.region:
      continue

    if not region.metadata:
      continue

    metadata = encoding.MessageToDict(region.metadata)

    for zone in metadata.get('availableZones', []):
      zone = RedisZone(name=zone, region=region.locationId)
      yield zone
