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


BASE_URL = 'https://cloudidentity.googleapis.com/v1beta1/'
DOCS_URL = 'https://cloud.google.com/identity/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  CUSTOMERS = (
      'customers',
      'customers/{customersId}',
      {},
      ['customersId'],
      True
  )
  CUSTOMERS_USERINVITATIONS = (
      'customers.userinvitations',
      '{+name}',
      {
          '':
              'customers/{customersId}/userinvitations/{userinvitationsId}',
      },
      ['name'],
      True
  )
  DEVICES = (
      'devices',
      '{+name}',
      {
          '':
              'devices/{devicesId}',
      },
      ['name'],
      True
  )
  DEVICES_DEVICEUSERS = (
      'devices.deviceUsers',
      '{+name}',
      {
          '':
              'devices/{devicesId}/deviceUsers/{deviceUsersId}',
      },
      ['name'],
      True
  )
  DEVICES_DEVICEUSERS_CLIENTSTATES = (
      'devices.deviceUsers.clientStates',
      '{+name}',
      {
          '':
              'devices/{devicesId}/deviceUsers/{deviceUsersId}/clientStates/'
              '{clientStatesId}',
      },
      ['name'],
      True
  )
  GROUPS = (
      'groups',
      '{+name}',
      {
          '':
              'groups/{groupId}',
      },
      ['name'],
      True
  )
  GROUPS_MEMBERSHIPS = (
      'groups.memberships',
      '{+name}',
      {
          '':
              'groups/{groupId}/memberships/{membershipId}',
      },
      ['name'],
      True
  )
  INBOUNDSAMLSSOPROFILES = (
      'inboundSamlSsoProfiles',
      '{+name}',
      {
          '':
              'inboundSamlSsoProfiles/{inboundSamlSsoProfilesId}',
      },
      ['name'],
      True
  )
  INBOUNDSAMLSSOPROFILES_IDPCREDENTIALS = (
      'inboundSamlSsoProfiles.idpCredentials',
      '{+name}',
      {
          '':
              'inboundSamlSsoProfiles/{inboundSamlSsoProfilesId}/'
              'idpCredentials/{idpCredentialsId}',
      },
      ['name'],
      True
  )
  INBOUNDSSOASSIGNMENTS = (
      'inboundSsoAssignments',
      '{+name}',
      {
          '':
              'inboundSsoAssignments/{inboundSsoAssignmentsId}',
      },
      ['name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
