# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Utilities for dealing with region resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Region(object):
  """Value class representing a region resource."""

  def __init__(self, region, standard, flexible, search_api):
    self.region = region
    self.standard = standard
    self.flexible = flexible
    self.search_api = search_api

  @classmethod
  def FromRegionResource(cls, region):
    """Create region from a google.cloud.location.Location message."""
    flex = False
    standard = False
    search_api = False
    region_id = region.labels.additionalProperties[0].value
    for p in region.metadata.additionalProperties:
      if p.key == 'flexibleEnvironmentAvailable' and p.value.boolean_value:
        flex = True
      elif p.key == 'standardEnvironmentAvailable' and p.value.boolean_value:
        standard = True
      elif p.key == 'searchApiAvailable' and p.value.boolean_value:
        search_api = True

    return cls(region_id, standard, flex, search_api)

  def __str__(self):
    envs = (
        x[1] for x in [(self.standard, 'standard'),
                       (self.flexible, 'flexible'),
                       (self.search_api, 'search_api')] if x[0])
    out = '{region: <13}'.format(region=self.region)
    return out + ' (supports {envs})'.format(envs=' and '.join(envs))
