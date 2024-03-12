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


BASE_URL = 'https://vmwareengine.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/solutions/vmware-as-a-service'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NETWORKPEERINGS = (
      'projects.locations.networkPeerings',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/networkPeerings/'
              '{networkPeeringsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NETWORKPOLICIES = (
      'projects.locations.networkPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/networkPolicies/'
              '{networkPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NETWORKPOLICIES_EXTERNALACCESSRULES = (
      'projects.locations.networkPolicies.externalAccessRules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/networkPolicies/'
              '{networkPoliciesId}/externalAccessRules/'
              '{externalAccessRulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NODETYPES = (
      'projects.locations.nodeTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/nodeTypes/'
              '{nodeTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONS = (
      'projects.locations.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS = (
      'projects.locations.privateClouds',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_CLUSTERS = (
      'projects.locations.privateClouds.clusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/clusters/{clustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_CLUSTERS_NODES = (
      'projects.locations.privateClouds.clusters.nodes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/clusters/{clustersId}/nodes/{nodesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_DNSFORWARDING = (
      'projects.locations.privateClouds.dnsForwarding',
      'projects/{project}/locations/{location}/privateClouds/{private_cloud}/'
      'dnsForwarding',
      {},
      ['project', 'location', 'private_cloud'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_EXTERNALADDRESSES = (
      'projects.locations.privateClouds.externalAddresses',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/externalAddresses/{externalAddressesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_HCXACTIVATIONKEYS = (
      'projects.locations.privateClouds.hcxActivationKeys',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/hcxActivationKeys/{hcxActivationKeysId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_IDENTITYSOURCES = (
      'projects.locations.privateClouds.identitySources',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/identitySources/{identitySourcesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_LOGGINGSERVERS = (
      'projects.locations.privateClouds.loggingServers',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/loggingServers/{loggingServersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_MANAGEMENTDNSZONEBINDINGS = (
      'projects.locations.privateClouds.managementDnsZoneBindings',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/managementDnsZoneBindings/'
              '{managementDnsZoneBindingsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECLOUDS_SUBNETS = (
      'projects.locations.privateClouds.subnets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/privateClouds/'
              '{privateCloudsId}/subnets/{subnetsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PRIVATECONNECTIONS = (
      'projects.locations.privateConnections',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'privateConnections/{privateConnectionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VMWAREENGINENETWORKS = (
      'projects.locations.vmwareEngineNetworks',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'vmwareEngineNetworks/{vmwareEngineNetworksId}',
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
