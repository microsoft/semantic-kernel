# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Resource definitions for Cloud Platform Apis generated from apitools."""

import enum


BASE_URL = 'https://dns.googleapis.com/dns/v1/'
DOCS_URL = 'https://cloud.google.com/dns/docs'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  CHANGES = (
      'changes',
      'projects/{project}/managedZones/{managedZone}/changes/{changeId}',
      {},
      ['project', 'managedZone', 'changeId'],
      True
  )
  DNSKEYS = (
      'dnsKeys',
      'projects/{project}/managedZones/{managedZone}/dnsKeys/{dnsKeyId}',
      {},
      ['project', 'managedZone', 'dnsKeyId'],
      True
  )
  MANAGEDZONEOPERATIONS = (
      'managedZoneOperations',
      'projects/{project}/managedZones/{managedZone}/operations/{operation}',
      {},
      ['project', 'managedZone', 'operation'],
      True
  )
  MANAGEDZONES = (
      'managedZones',
      'projects/{project}/managedZones/{managedZone}',
      {},
      ['project', 'managedZone'],
      True
  )
  POLICIES = (
      'policies',
      'projects/{project}/policies/{policy}',
      {},
      ['project', 'policy'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{project}',
      {},
      ['project'],
      True
  )
  RESOURCERECORDSETS = (
      'resourceRecordSets',
      'projects/{project}/managedZones/{managedZone}/rrsets/{name}/{type}',
      {},
      ['project', 'managedZone', 'name', 'type'],
      True
  )
  RESPONSEPOLICIES = (
      'responsePolicies',
      'projects/{project}/responsePolicies/{responsePolicy}',
      {},
      ['project', 'responsePolicy'],
      True
  )
  RESPONSEPOLICYRULES = (
      'responsePolicyRules',
      'projects/{project}/responsePolicies/{responsePolicy}/rules/'
      '{responsePolicyRule}',
      {},
      ['project', 'responsePolicy', 'responsePolicyRule'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
