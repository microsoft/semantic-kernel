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
"""Utils for the compute in-place snapshots commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.api_lib.compute.regions import utils as region_utils


def WarnAboutScopeDeprecations(ips_refs, client):
  """Tests to check if the zone is deprecated."""
  zone_resource_fetcher = zone_utils.ZoneResourceFetcher(client)
  zone_resource_fetcher.WarnForZonalCreation(
      (
          ref
          for ref in ips_refs
          if ref.Collection() == 'compute.zoneInstantSnapshots'
      )
  )
  # Check if the region is deprecated.
  region_resource_fetcher = region_utils.RegionResourceFetcher(client)
  region_resource_fetcher.WarnForRegionalCreation(
      (
          ref
          for ref in ips_refs
          if ref.Collection() == 'compute.regionInstantSnapshots'
      )
  )
