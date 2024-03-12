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

BASE_URL = 'https://www.googleapis.com/admin/directory/v1/'
DOCS_URL = 'https://developers.google.com/admin-sdk/directory/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  CUSTOMER = ('customer', 'customer/{customerId}', {}, [u'customerId'], True)
  RESOURCES = ('resources', 'customer/{customer}', {}, [u'customer'], True)
  ASPS = ('asps', 'users/{userKey}/asps/{codeId}', {}, [u'userKey',
                                                        u'codeId'], True)
  CHROMEOSDEVICES = ('chromeosdevices',
                     'customer/{customerId}/devices/chromeos/{deviceId}', {},
                     [u'customerId', u'deviceId'], True)
  CUSTOMERS = ('customers', 'customers/{customerKey}', {}, [u'customerKey'],
               True)
  DOMAINALIASES = ('domainAliases',
                   'customer/{customer}/domainaliases/{domainAliasName}', {},
                   [u'customer', u'domainAliasName'], True)
  DOMAINS = ('domains', 'customer/{customer}/domains/{domainName}', {},
             [u'customer', u'domainName'], True)
  GROUPS = ('groups', 'groups/{groupKey}', {}, [u'groupKey'], True)
  MEMBERS = ('members', 'groups/{groupKey}/members/{memberKey}', {},
             [u'groupKey', u'memberKey'], True)
  MOBILEDEVICES = ('mobiledevices',
                   'customer/{customerId}/devices/mobile/{resourceId}', {},
                   [u'customerId', u'resourceId'], True)
  NOTIFICATIONS = ('notifications',
                   'customer/{customer}/notifications/{notificationId}', {},
                   [u'customer', u'notificationId'], True)
  ORGUNITS = ('orgunits', 'customer/{customerId}/orgunits{/orgUnitPath*}', {},
              [u'customerId'], True)
  RESOURCES_BUILDINGS = ('resources.buildings',
                         'customer/{customer}/resources/buildings/{buildingId}',
                         {}, [u'customer', u'buildingId'], True)
  RESOURCES_CALENDARS = (
      'resources.calendars',
      'customer/{customer}/resources/calendars/{calendarResourceId}', {},
      [u'customer', u'calendarResourceId'], True)
  RESOURCES_FEATURES = ('resources.features',
                        'customer/{customer}/resources/features/{featureKey}',
                        {}, [u'customer', u'featureKey'], True)
  ROLEASSIGNMENTS = ('roleAssignments',
                     'customer/{customer}/roleassignments/{roleAssignmentId}',
                     {}, [u'customer', u'roleAssignmentId'], True)
  ROLES = ('roles', 'customer/{customer}/roles/{roleId}', {},
           [u'customer', u'roleId'], True)
  SCHEMAS = ('schemas', 'customer/{customerId}/schemas/{schemaKey}', {},
             [u'customerId', u'schemaKey'], True)
  TOKENS = ('tokens', 'users/{userKey}/tokens/{clientId}', {},
            [u'userKey', u'clientId'], True)
  USERS = ('users', 'users/{userKey}', {}, [u'userKey'], True)
  USERS_PHOTOS = ('users.photos', 'users/{userKey}/photos/thumbnail', {},
                  [u'userKey'], True)

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
