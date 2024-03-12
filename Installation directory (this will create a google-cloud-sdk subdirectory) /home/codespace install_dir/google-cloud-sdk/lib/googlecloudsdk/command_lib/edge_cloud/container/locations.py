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
"""Utilities for edge-cloud container location commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from apitools.base.py import encoding
from googlecloudsdk.core import exceptions

_Zone = collections.namedtuple('EdgeContainerZone', ['name', 'region'])


def ReplaceResourceZoneWithRegion(ref, args, request):
  """Replaces the request.name 'locations/{zone}' with 'locations/{region}'."""
  del ref, args  # Unused.
  request.name = re.sub(
      r'(projects/[-a-z0-9]+/locations/[a-z]+-[a-z]+[0-9])[-a-z0-9]*((?:/.*)?)',
      r'\1\2', request.name)
  return request


def ExtractZonesFromLocations(response, _):
  """Returns the zones from a ListLocationResponse."""
  for region in response:
    if not region.metadata:
      continue

    metadata = encoding.MessageToDict(region.metadata)
    for zone in metadata.get('availableZones', []):
      yield _Zone(name=zone, region=region.locationId)


def ExtractZoneFromLocation(response, args):
  """Returns the argument-specified zone from a GetLocationResponse."""
  metadata = encoding.MessageToDict(response.metadata)

  want_zone = args.zone.split('/')[-1]
  for zone_name, zone in metadata.get('availableZones', {}).items():
    if zone_name == want_zone:
      if 'rackTypes' in zone:
        racks = zone.pop('rackTypes')
        populated_rack = []
        for rack, rack_type in racks.items():
          # Base racks are a pair of two modified Config-1 racks containing
          # aggregation switches.
          if rack_type == 'BASE':
            populated_rack.append(rack + ' (BASE)')
          # Expansion rack type, also known as standalone racks,
          # are added by customers on demand.
          elif rack_type == 'EXPANSION':
            populated_rack.append(rack + ' (EXPANSION)')
          # Only displaying the suffix for multi-rack rack types,
          # i.e. base/expansion, ignore the rest.
          else:
            populated_rack.append(rack)
        zone['racks'] = populated_rack
      return zone
  raise exceptions.Error('Zone not found: {}'.format(want_zone))
