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


BASE_URL = 'https://appengine.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/appengine/docs/admin-api/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  APPS = (
      'apps',
      '{+name}',
      {
          '':
              'apps/{appsId}',
      },
      ['name'],
      True
  )
  APPS_AUTHORIZEDCERTIFICATES = (
      'apps.authorizedCertificates',
      '{+name}',
      {
          '':
              'apps/{appsId}/authorizedCertificates/'
              '{authorizedCertificatesId}',
      },
      ['name'],
      True
  )
  APPS_DOMAINMAPPINGS = (
      'apps.domainMappings',
      '{+name}',
      {
          '':
              'apps/{appsId}/domainMappings/{domainMappingsId}',
      },
      ['name'],
      True
  )
  APPS_FIREWALL_INGRESSRULES = (
      'apps.firewall.ingressRules',
      '{+name}',
      {
          '':
              'apps/{appsId}/firewall/ingressRules/{ingressRulesId}',
      },
      ['name'],
      True
  )
  APPS_LOCATIONS = (
      'apps.locations',
      '{+name}',
      {
          '':
              'apps/{appsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  APPS_OPERATIONS = (
      'apps.operations',
      '{+name}',
      {
          '':
              'apps/{appsId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  APPS_SERVICES = (
      'apps.services',
      '{+name}',
      {
          '':
              'apps/{appsId}/services/{servicesId}',
      },
      ['name'],
      True
  )
  APPS_SERVICES_VERSIONS = (
      'apps.services.versions',
      '{+name}',
      {
          '':
              'apps/{appsId}/services/{servicesId}/versions/{versionsId}',
      },
      ['name'],
      True
  )
  APPS_SERVICES_VERSIONS_INSTANCES = (
      'apps.services.versions.instances',
      '{+name}',
      {
          '':
              'apps/{appsId}/services/{servicesId}/versions/{versionsId}/'
              'instances/{instancesId}',
      },
      ['name'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectId}',
      {},
      ['projectId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
