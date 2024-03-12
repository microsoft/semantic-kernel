# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Utilities for `gcloud filestore zones` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def IsZonal(location):
  """Returns True if the location string is a GCP zone."""
  return len(location.split('-')) == 3


def IsRegional(location):
  """Returns True if the location string is a GCP region."""
  return len(location.split('-')) == 2


def GetRegionFromZone(zone):
  """Returns the GCP region that the input zone is in."""
  return '-'.join(zone.split('-')[:-1])


def ExtractRegionsFromLocationsListResponse(response, args):
  """Extract the regions from a list of GCP locations."""
  del args  # args is not used but passed by modify_responses_hook.
  for location in response:
    if IsRegional(location.locationId):
      yield location


def ExtractZonesFromLocationsListResponse(response, args):
  """Extract the zones from a list of GCP locations."""
  del args  # args is not used but passed by modify_responses_hook.
  for location in response:
    if IsZonal(location.locationId):
      yield location
