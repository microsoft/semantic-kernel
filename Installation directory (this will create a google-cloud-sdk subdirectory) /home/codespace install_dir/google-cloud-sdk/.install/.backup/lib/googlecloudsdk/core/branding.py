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
"""Convenience utilities for manipulating collection and resource names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Branding(object):
  """Convenience class for mapping service names to official branding titles."""

  _branding_map = {
      'Access Context Manager': {'accesscontextmanager'},
      'Artifact Registry': {'artifactregistry'},
      'Google BigQuery': {'bigquery'},
      'Cloud Bigtable': {'bigtableadmin'},
      'Google Cloud Build': {'cloudbuild'},
      'Cloud Identity': {'cloudidentity'},
      'Cloud KMS': {'cloudkms'},
      'Cloud Resource Manager': {'cloudresourcemanager'},
      'Compute Engine': {'compute'},
      'Pub/Sub': {'pubsub'},
      'Cloud Source': {'sourcerepo'}
  }

  def __init__(self):
    self.branding_map = {}
    for brand_name, services in self._branding_map.items():
      for service in services:
        self.branding_map[service] = brand_name

  def get(self, service, backup=None):
    return self.branding_map.get(service, backup or service)
