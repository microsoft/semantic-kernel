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
"""Utilities for describe Memorystore Redis instances."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def FormatResponse(response, _):
  """Hook to convert seconds into minutes for duration field."""
  modified_response = {}
  if response.authorizedNetwork:
    modified_response['authorizedNetwork'] = response.authorizedNetwork
  if response.availableMaintenanceVersions:
    modified_response[
        'availableMaintenanceVersions'] = response.availableMaintenanceVersions
  if response.connectMode:
    modified_response['connectMode'] = response.connectMode
  if response.createTime:
    modified_response['createTime'] = response.createTime
  if response.currentLocationId:
    modified_response['currentLocationId'] = response.currentLocationId
  if response.host:
    modified_response['host'] = response.host
  if response.locationId:
    modified_response['locationId'] = response.locationId
  if response.maintenanceSchedule:
    modified_response['maintenanceSchedule'] = response.maintenanceSchedule
  if response.maintenanceVersion:
    modified_response['maintenanceVersion'] = response.maintenanceVersion
  if response.memorySizeGb:
    modified_response['memorySizeGb'] = response.memorySizeGb
  if response.name:
    modified_response['name'] = response.name
  if response.persistenceIamIdentity:
    modified_response[
        'persistenceIamIdentity'] = response.persistenceIamIdentity
  if response.port:
    modified_response['port'] = response.port
  if response.readEndpoint:
    modified_response['readEndpoint'] = response.readEndpoint
  if response.readEndpointPort:
    modified_response['readEndpointPort'] = response.readEndpointPort
  if response.readReplicasMode:
    modified_response['readReplicasMode'] = response.readReplicasMode
  if response.redisVersion:
    modified_response['redisVersion'] = response.redisVersion
  if response.replicaCount:
    modified_response['replicaCount'] = response.replicaCount
  if response.reservedIpRange:
    modified_response['reservedIpRange'] = response.reservedIpRange
  if response.secondaryIpRange:
    modified_response['secondaryIpRange'] = response.secondaryIpRange
  if response.state:
    modified_response['state'] = response.state
  if response.tier:
    modified_response['tier'] = response.tier
  if response.transitEncryptionMode:
    modified_response['transitEncryptionMode'] = response.transitEncryptionMode
  if response.persistenceConfig:
    modified_response['persistenceConfig'] = response.persistenceConfig

  if response.maintenancePolicy:
    modified_mw_policy = {}
    modified_mw_policy['createTime'] = response.maintenancePolicy.createTime
    modified_mw_policy['updateTime'] = response.maintenancePolicy.updateTime

    modified_mwlist = []
    for mw in response.maintenancePolicy.weeklyMaintenanceWindow:
      item = {}
      # convert seconds to minutes
      duration_secs = int(mw.duration[:-1])
      duration_mins = int(duration_secs/60)
      item['day'] = mw.day
      item['hour'] = mw.startTime.hours
      item['duration'] = str(duration_mins) + ' minutes'
      modified_mwlist.append(item)

    modified_mw_policy['maintenanceWindow'] = modified_mwlist
    modified_response['maintenancePolicy'] = modified_mw_policy

  if response.nodes:
    modified_node_list = []
    for node in response.nodes:
      item = {}
      item['id'] = node.id
      item['zone'] = node.zone
      modified_node_list.append(item)
    modified_response['nodes'] = modified_node_list

  return modified_response
