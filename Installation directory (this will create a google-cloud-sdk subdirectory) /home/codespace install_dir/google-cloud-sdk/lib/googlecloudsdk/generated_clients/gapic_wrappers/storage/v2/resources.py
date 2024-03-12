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
"""Resource definitions for Cloud Platform APIs generated from gapic."""

import enum


BASE_URL = 'https://storage.googleapis.com/v2/'
DOCS_URL = 'https://cloud.google.com/storage/docs/apis'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{project}',
      {},
      ['project'],
      True
  )
  PROJECTS_BUCKETS = (
      'projects.buckets',
      'projects/{project}/buckets/{bucket}',
      {},
      ['project', 'bucket'],
      True
  )
  PROJECTS_BUCKETS_NOTIFICATIONCONFIGS = (
      'projects.buckets.notificationConfigs',
      'projects/{project}/buckets/{bucket}/notificationConfigs/'
      '{notification_config}',
      {},
      ['project', 'bucket', 'notification_config'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{project}/locations/{location}',
      {},
      ['project', 'location'],
      True
  )
  PROJECTS_LOCATIONS_KEYRINGS = (
      'projects.locations.keyRings',
      'projects/{project}/locations/{location}/keyRings/{key_ring}',
      {},
      ['project', 'location', 'key_ring'],
      True
  )
  PROJECTS_LOCATIONS_KEYRINGS_CRYPTOKEYS = (
      'projects.locations.keyRings.cryptoKeys',
      'projects/{project}/locations/{location}/keyRings/{key_ring}/'
      'cryptoKeys/{crypto_key}',
      {},
      ['project', 'location', 'key_ring', 'crypto_key'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
