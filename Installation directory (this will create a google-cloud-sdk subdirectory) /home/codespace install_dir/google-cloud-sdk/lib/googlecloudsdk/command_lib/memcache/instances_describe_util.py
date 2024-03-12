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
"""Utilities for describe Memorystore Memcache instances."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import six


def FormatResponse(response, _):
  """Hook to modify gcloud describe output for maintenance windows."""
  modified_response = {}
  if response.authorizedNetwork:
    modified_response['authorizedNetwork'] = response.authorizedNetwork
  if response.createTime:
    modified_response['createTime'] = response.createTime
  if response.discoveryEndpoint:
    modified_response['discoveryEndpoint'] = response.discoveryEndpoint
  if response.displayName:
    modified_response['displayName'] = response.displayName
  if response.maintenanceSchedule:
    modified_response['maintenanceSchedule'] = response.maintenanceSchedule
  if response.memcacheFullVersion:
    modified_response['memcacheFullVersion'] = response.memcacheFullVersion
  if response.memcacheNodes:
    modified_response['memcacheNodes'] = response.memcacheNodes
  if response.memcacheVersion:
    modified_response['memcacheVersion'] = response.memcacheVersion
  if response.name:
    modified_response['name'] = response.name
  if response.nodeConfig:
    modified_response['nodeConfig'] = response.nodeConfig
  if response.nodeCount:
    modified_response['nodeCount'] = response.nodeCount
  if response.parameters:
    modified_response['parameters'] = response.parameters
  if response.state:
    modified_response['state'] = response.state
  if response.updateTime:
    modified_response['updateTime'] = response.updateTime
  if response.zones:
    modified_response['zones'] = response.zones

  if response.maintenancePolicy:
    modified_mw_policy = {}
    modified_mw_policy['createTime'] = response.maintenancePolicy.createTime
    modified_mw_policy['updateTime'] = response.maintenancePolicy.updateTime

    mwlist = response.maintenancePolicy.weeklyMaintenanceWindow
    modified_mwlist = []
    for mw in mwlist:
      item = {}
      # convert seconds to minutes
      duration_secs = int(mw.duration[:-1])
      duration_mins = int(duration_secs / 60)
      item['day'] = mw.day
      item['hour'] = mw.startTime.hours
      item['duration'] = six.text_type(duration_mins) + ' minutes'
      modified_mwlist.append(item)

    modified_mw_policy['maintenanceWindow'] = modified_mwlist
    modified_response['maintenancePolicy'] = modified_mw_policy

  return modified_response
