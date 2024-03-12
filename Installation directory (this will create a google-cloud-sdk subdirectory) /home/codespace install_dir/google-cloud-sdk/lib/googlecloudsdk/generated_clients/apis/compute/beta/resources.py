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


BASE_URL = 'https://compute.googleapis.com/compute/beta/'
DOCS_URL = 'https://cloud.google.com/compute/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  ACCELERATORTYPES = (
      'acceleratorTypes',
      'projects/{project}/zones/{zone}/acceleratorTypes/{acceleratorType}',
      {},
      ['project', 'zone', 'acceleratorType'],
      True
  )
  ADDRESSES = (
      'addresses',
      'projects/{project}/regions/{region}/addresses/{address}',
      {},
      ['project', 'region', 'address'],
      True
  )
  AUTOSCALERS = (
      'autoscalers',
      'projects/{project}/zones/{zone}/autoscalers/{autoscaler}',
      {},
      ['project', 'zone', 'autoscaler'],
      True
  )
  BACKENDBUCKETS = (
      'backendBuckets',
      'projects/{project}/global/backendBuckets/{backendBucket}',
      {},
      ['project', 'backendBucket'],
      True
  )
  BACKENDSERVICES = (
      'backendServices',
      'projects/{project}/global/backendServices/{backendService}',
      {},
      ['project', 'backendService'],
      True
  )
  DISKTYPES = (
      'diskTypes',
      'projects/{project}/zones/{zone}/diskTypes/{diskType}',
      {},
      ['project', 'zone', 'diskType'],
      True
  )
  DISKS = (
      'disks',
      'projects/{project}/zones/{zone}/disks/{disk}',
      {},
      ['project', 'zone', 'disk'],
      True
  )
  EXTERNALVPNGATEWAYS = (
      'externalVpnGateways',
      'projects/{project}/global/externalVpnGateways/{externalVpnGateway}',
      {},
      ['project', 'externalVpnGateway'],
      True
  )
  FIREWALLPOLICIES = (
      'firewallPolicies',
      'locations/global/firewallPolicies/{firewallPolicy}',
      {},
      ['firewallPolicy'],
      True
  )
  FIREWALLS = (
      'firewalls',
      'projects/{project}/global/firewalls/{firewall}',
      {},
      ['project', 'firewall'],
      True
  )
  FORWARDINGRULES = (
      'forwardingRules',
      'projects/{project}/regions/{region}/forwardingRules/{forwardingRule}',
      {},
      ['project', 'region', 'forwardingRule'],
      True
  )
  FUTURERESERVATIONS = (
      'futureReservations',
      'projects/{project}/zones/{zone}/futureReservations/{futureReservation}',
      {},
      ['project', 'zone', 'futureReservation'],
      True
  )
  GLOBALADDRESSES = (
      'globalAddresses',
      'projects/{project}/global/addresses/{address}',
      {},
      ['project', 'address'],
      True
  )
  GLOBALFORWARDINGRULES = (
      'globalForwardingRules',
      'projects/{project}/global/forwardingRules/{forwardingRule}',
      {},
      ['project', 'forwardingRule'],
      True
  )
  GLOBALNETWORKENDPOINTGROUPS = (
      'globalNetworkEndpointGroups',
      'projects/{project}/global/networkEndpointGroups/{networkEndpointGroup}',
      {},
      ['project', 'networkEndpointGroup'],
      True
  )
  GLOBALOPERATIONS = (
      'globalOperations',
      'projects/{project}/global/operations/{operation}',
      {},
      ['project', 'operation'],
      True
  )
  GLOBALORGANIZATIONOPERATIONS = (
      'globalOrganizationOperations',
      'locations/global/operations/{operation}',
      {},
      ['operation'],
      True
  )
  GLOBALPUBLICDELEGATEDPREFIXES = (
      'globalPublicDelegatedPrefixes',
      'projects/{project}/global/publicDelegatedPrefixes/'
      '{publicDelegatedPrefix}',
      {},
      ['project', 'publicDelegatedPrefix'],
      True
  )
  HEALTHCHECKS = (
      'healthChecks',
      'projects/{project}/global/healthChecks/{healthCheck}',
      {},
      ['project', 'healthCheck'],
      True
  )
  HTTPHEALTHCHECKS = (
      'httpHealthChecks',
      'projects/{project}/global/httpHealthChecks/{httpHealthCheck}',
      {},
      ['project', 'httpHealthCheck'],
      True
  )
  HTTPSHEALTHCHECKS = (
      'httpsHealthChecks',
      'projects/{project}/global/httpsHealthChecks/{httpsHealthCheck}',
      {},
      ['project', 'httpsHealthCheck'],
      True
  )
  IMAGEFAMILYVIEWS = (
      'imageFamilyViews',
      'projects/{project}/zones/{zone}/imageFamilyViews/{family}',
      {},
      ['project', 'zone', 'family'],
      True
  )
  IMAGES = (
      'images',
      'projects/{project}/global/images/{image}',
      {},
      ['project', 'image'],
      True
  )
  INSTANCEGROUPMANAGERRESIZEREQUESTS = (
      'instanceGroupManagerResizeRequests',
      'projects/{project}/zones/{zone}/instanceGroupManagers/'
      '{instanceGroupManager}/resizeRequests/{resizeRequest}',
      {},
      ['project', 'zone', 'instanceGroupManager', 'resizeRequest'],
      True
  )
  INSTANCEGROUPMANAGERS = (
      'instanceGroupManagers',
      'projects/{project}/zones/{zone}/instanceGroupManagers/'
      '{instanceGroupManager}',
      {},
      ['project', 'zone', 'instanceGroupManager'],
      True
  )
  INSTANCEGROUPS = (
      'instanceGroups',
      'projects/{project}/zones/{zone}/instanceGroups/{instanceGroup}',
      {},
      ['project', 'zone', 'instanceGroup'],
      True
  )
  INSTANCESETTINGS = (
      'instanceSettings',
      'projects/{project}/zones/{zone}/instanceSettings',
      {},
      ['project', 'zone'],
      True
  )
  INSTANCETEMPLATES = (
      'instanceTemplates',
      'projects/{project}/global/instanceTemplates/{instanceTemplate}',
      {},
      ['project', 'instanceTemplate'],
      True
  )
  INSTANCES = (
      'instances',
      'projects/{project}/zones/{zone}/instances/{instance}',
      {},
      ['project', 'zone', 'instance'],
      True
  )
  INSTANTSNAPSHOTS = (
      'instantSnapshots',
      'projects/{project}/zones/{zone}/instantSnapshots/{instantSnapshot}',
      {},
      ['project', 'zone', 'instantSnapshot'],
      True
  )
  INTERCONNECTATTACHMENTS = (
      'interconnectAttachments',
      'projects/{project}/regions/{region}/interconnectAttachments/'
      '{interconnectAttachment}',
      {},
      ['project', 'region', 'interconnectAttachment'],
      True
  )
  INTERCONNECTLOCATIONS = (
      'interconnectLocations',
      'projects/{project}/global/interconnectLocations/{interconnectLocation}',
      {},
      ['project', 'interconnectLocation'],
      True
  )
  INTERCONNECTREMOTELOCATIONS = (
      'interconnectRemoteLocations',
      'projects/{project}/global/interconnectRemoteLocations/'
      '{interconnectRemoteLocation}',
      {},
      ['project', 'interconnectRemoteLocation'],
      True
  )
  INTERCONNECTS = (
      'interconnects',
      'projects/{project}/global/interconnects/{interconnect}',
      {},
      ['project', 'interconnect'],
      True
  )
  LICENSECODES = (
      'licenseCodes',
      'projects/{project}/global/licenseCodes/{licenseCode}',
      {},
      ['project', 'licenseCode'],
      True
  )
  LICENSES = (
      'licenses',
      'projects/{project}/global/licenses/{license}',
      {},
      ['project', 'license'],
      True
  )
  MACHINEIMAGES = (
      'machineImages',
      'projects/{project}/global/machineImages/{machineImage}',
      {},
      ['project', 'machineImage'],
      True
  )
  MACHINETYPES = (
      'machineTypes',
      'projects/{project}/zones/{zone}/machineTypes/{machineType}',
      {},
      ['project', 'zone', 'machineType'],
      True
  )
  NETWORKATTACHMENTS = (
      'networkAttachments',
      'projects/{project}/regions/{region}/networkAttachments/'
      '{networkAttachment}',
      {},
      ['project', 'region', 'networkAttachment'],
      True
  )
  NETWORKEDGESECURITYSERVICES = (
      'networkEdgeSecurityServices',
      'projects/{project}/regions/{region}/networkEdgeSecurityServices/'
      '{networkEdgeSecurityService}',
      {},
      ['project', 'region', 'networkEdgeSecurityService'],
      True
  )
  NETWORKENDPOINTGROUPS = (
      'networkEndpointGroups',
      'projects/{project}/zones/{zone}/networkEndpointGroups/'
      '{networkEndpointGroup}',
      {},
      ['project', 'zone', 'networkEndpointGroup'],
      True
  )
  NETWORKFIREWALLPOLICIES = (
      'networkFirewallPolicies',
      'projects/{project}/global/firewallPolicies/{firewallPolicy}',
      {},
      ['project', 'firewallPolicy'],
      True
  )
  NETWORKS = (
      'networks',
      'projects/{project}/global/networks/{network}',
      {},
      ['project', 'network'],
      True
  )
  NEXTHOPGATEWAYS = (
      'nextHopGateways',
      'projects/{project}/global/gateways/{nextHopGateway}',
      {},
      ['project', 'nextHopGateway'],
      True
  )
  NODEGROUPS = (
      'nodeGroups',
      'projects/{project}/zones/{zone}/nodeGroups/{nodeGroup}',
      {},
      ['project', 'zone', 'nodeGroup'],
      True
  )
  NODETEMPLATES = (
      'nodeTemplates',
      'projects/{project}/regions/{region}/nodeTemplates/{nodeTemplate}',
      {},
      ['project', 'region', 'nodeTemplate'],
      True
  )
  NODETYPES = (
      'nodeTypes',
      'projects/{project}/zones/{zone}/nodeTypes/{nodeType}',
      {},
      ['project', 'zone', 'nodeType'],
      True
  )
  ORGANIZATIONSECURITYPOLICIES = (
      'organizationSecurityPolicies',
      'locations/global/securityPolicies/{securityPolicy}',
      {},
      ['securityPolicy'],
      True
  )
  PACKETMIRRORINGS = (
      'packetMirrorings',
      'projects/{project}/regions/{region}/packetMirrorings/{packetMirroring}',
      {},
      ['project', 'region', 'packetMirroring'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{project}',
      {},
      ['project'],
      True
  )
  PUBLICADVERTISEDPREFIXES = (
      'publicAdvertisedPrefixes',
      'projects/{project}/global/publicAdvertisedPrefixes/'
      '{publicAdvertisedPrefix}',
      {},
      ['project', 'publicAdvertisedPrefix'],
      True
  )
  PUBLICDELEGATEDPREFIXES = (
      'publicDelegatedPrefixes',
      'projects/{project}/regions/{region}/publicDelegatedPrefixes/'
      '{publicDelegatedPrefix}',
      {},
      ['project', 'region', 'publicDelegatedPrefix'],
      True
  )
  REGIONACCELERATORTYPES = (
      'regionAcceleratorTypes',
      'projects/{project}/regions/{region}/acceleratorTypes/{acceleratorType}',
      {},
      ['project', 'region', 'acceleratorType'],
      True
  )
  REGIONAUTOSCALERS = (
      'regionAutoscalers',
      'projects/{project}/regions/{region}/autoscalers/{autoscaler}',
      {},
      ['project', 'region', 'autoscaler'],
      True
  )
  REGIONBACKENDSERVICES = (
      'regionBackendServices',
      'projects/{project}/regions/{region}/backendServices/{backendService}',
      {},
      ['project', 'region', 'backendService'],
      True
  )
  REGIONCOMMITMENTS = (
      'regionCommitments',
      'projects/{project}/regions/{region}/commitments/{commitment}',
      {},
      ['project', 'region', 'commitment'],
      True
  )
  REGIONDISKTYPES = (
      'regionDiskTypes',
      'projects/{project}/regions/{region}/diskTypes/{diskType}',
      {},
      ['project', 'region', 'diskType'],
      True
  )
  REGIONDISKS = (
      'regionDisks',
      'projects/{project}/regions/{region}/disks/{disk}',
      {},
      ['project', 'region', 'disk'],
      True
  )
  REGIONHEALTHCHECKSERVICES = (
      'regionHealthCheckServices',
      'projects/{project}/regions/{region}/healthCheckServices/'
      '{healthCheckService}',
      {},
      ['project', 'region', 'healthCheckService'],
      True
  )
  REGIONHEALTHCHECKS = (
      'regionHealthChecks',
      'projects/{project}/regions/{region}/healthChecks/{healthCheck}',
      {},
      ['project', 'region', 'healthCheck'],
      True
  )
  REGIONINSTANCEGROUPMANAGERS = (
      'regionInstanceGroupManagers',
      'projects/{project}/regions/{region}/instanceGroupManagers/'
      '{instanceGroupManager}',
      {},
      ['project', 'region', 'instanceGroupManager'],
      True
  )
  REGIONINSTANCEGROUPS = (
      'regionInstanceGroups',
      'projects/{project}/regions/{region}/instanceGroups/{instanceGroup}',
      {},
      ['project', 'region', 'instanceGroup'],
      True
  )
  REGIONINSTANCETEMPLATES = (
      'regionInstanceTemplates',
      'projects/{project}/regions/{region}/instanceTemplates/'
      '{instanceTemplate}',
      {},
      ['project', 'region', 'instanceTemplate'],
      True
  )
  REGIONINSTANTSNAPSHOTS = (
      'regionInstantSnapshots',
      'projects/{project}/regions/{region}/instantSnapshots/{instantSnapshot}',
      {},
      ['project', 'region', 'instantSnapshot'],
      True
  )
  REGIONNETWORKENDPOINTGROUPS = (
      'regionNetworkEndpointGroups',
      'projects/{project}/regions/{region}/networkEndpointGroups/'
      '{networkEndpointGroup}',
      {},
      ['project', 'region', 'networkEndpointGroup'],
      True
  )
  REGIONNETWORKFIREWALLPOLICIES = (
      'regionNetworkFirewallPolicies',
      'projects/{project}/regions/{region}/firewallPolicies/{firewallPolicy}',
      {},
      ['project', 'region', 'firewallPolicy'],
      True
  )
  REGIONNOTIFICATIONENDPOINTS = (
      'regionNotificationEndpoints',
      'projects/{project}/regions/{region}/notificationEndpoints/'
      '{notificationEndpoint}',
      {},
      ['project', 'region', 'notificationEndpoint'],
      True
  )
  REGIONOPERATIONS = (
      'regionOperations',
      'projects/{project}/regions/{region}/operations/{operation}',
      {},
      ['project', 'region', 'operation'],
      True
  )
  REGIONSECURITYPOLICIES = (
      'regionSecurityPolicies',
      'projects/{project}/regions/{region}/securityPolicies/{securityPolicy}',
      {},
      ['project', 'region', 'securityPolicy'],
      True
  )
  REGIONSECURITYPOLICYRULES = (
      'regionSecurityPolicyRules',
      'projects/{project}/regions/{region}/securityPolicies/{securityPolicy}/'
      'securityPolicyRules/{securityPolicyRule}',
      {},
      ['project', 'region', 'securityPolicy', 'securityPolicyRule'],
      True
  )
  REGIONSSLCERTIFICATES = (
      'regionSslCertificates',
      'projects/{project}/regions/{region}/sslCertificates/{sslCertificate}',
      {},
      ['project', 'region', 'sslCertificate'],
      True
  )
  REGIONSSLPOLICIES = (
      'regionSslPolicies',
      'projects/{project}/regions/{region}/sslPolicies/{sslPolicy}',
      {},
      ['project', 'region', 'sslPolicy'],
      True
  )
  REGIONTARGETHTTPPROXIES = (
      'regionTargetHttpProxies',
      'projects/{project}/regions/{region}/targetHttpProxies/'
      '{targetHttpProxy}',
      {},
      ['project', 'region', 'targetHttpProxy'],
      True
  )
  REGIONTARGETHTTPSPROXIES = (
      'regionTargetHttpsProxies',
      'projects/{project}/regions/{region}/targetHttpsProxies/'
      '{targetHttpsProxy}',
      {},
      ['project', 'region', 'targetHttpsProxy'],
      True
  )
  REGIONTARGETTCPPROXIES = (
      'regionTargetTcpProxies',
      'projects/{project}/regions/{region}/targetTcpProxies/{targetTcpProxy}',
      {},
      ['project', 'region', 'targetTcpProxy'],
      True
  )
  REGIONURLMAPS = (
      'regionUrlMaps',
      'projects/{project}/regions/{region}/urlMaps/{urlMap}',
      {},
      ['project', 'region', 'urlMap'],
      True
  )
  REGIONS = (
      'regions',
      'projects/{project}/regions/{region}',
      {},
      ['project', 'region'],
      True
  )
  RESERVATIONS = (
      'reservations',
      'projects/{project}/zones/{zone}/reservations/{reservation}',
      {},
      ['project', 'zone', 'reservation'],
      True
  )
  RESOURCEPOLICIES = (
      'resourcePolicies',
      'projects/{project}/regions/{region}/resourcePolicies/{resourcePolicy}',
      {},
      ['project', 'region', 'resourcePolicy'],
      True
  )
  ROUTERS = (
      'routers',
      'projects/{project}/regions/{region}/routers/{router}',
      {},
      ['project', 'region', 'router'],
      True
  )
  ROUTES = (
      'routes',
      'projects/{project}/global/routes/{route}',
      {},
      ['project', 'route'],
      True
  )
  SECURITYPOLICIES = (
      'securityPolicies',
      'projects/{project}/global/securityPolicies/{securityPolicy}',
      {},
      ['project', 'securityPolicy'],
      True
  )
  SECURITYPOLICYRULES = (
      'securityPolicyRules',
      'projects/{project}/global/securityPolicies/{securityPolicy}/'
      'securityPolicyRules/{securityPolicyRule}',
      {},
      ['project', 'securityPolicy', 'securityPolicyRule'],
      True
  )
  SERVICEATTACHMENTS = (
      'serviceAttachments',
      'projects/{project}/regions/{region}/serviceAttachments/'
      '{serviceAttachment}',
      {},
      ['project', 'region', 'serviceAttachment'],
      True
  )
  SNAPSHOTSETTINGS = (
      'snapshotSettings',
      'projects/{project}/global/snapshotSettings',
      {},
      ['project'],
      True
  )
  SNAPSHOTS = (
      'snapshots',
      'projects/{project}/global/snapshots/{snapshot}',
      {},
      ['project', 'snapshot'],
      True
  )
  SSLCERTIFICATES = (
      'sslCertificates',
      'projects/{project}/global/sslCertificates/{sslCertificate}',
      {},
      ['project', 'sslCertificate'],
      True
  )
  SSLPOLICIES = (
      'sslPolicies',
      'projects/{project}/global/sslPolicies/{sslPolicy}',
      {},
      ['project', 'sslPolicy'],
      True
  )
  STORAGEPOOLTYPES = (
      'storagePoolTypes',
      'projects/{project}/zones/{zone}/storagePoolTypes/{storagePoolType}',
      {},
      ['project', 'zone', 'storagePoolType'],
      True
  )
  STORAGEPOOLS = (
      'storagePools',
      'projects/{project}/zones/{zone}/storagePools/{storagePool}',
      {},
      ['project', 'zone', 'storagePool'],
      True
  )
  SUBNETWORKS = (
      'subnetworks',
      'projects/{project}/regions/{region}/subnetworks/{subnetwork}',
      {},
      ['project', 'region', 'subnetwork'],
      True
  )
  TARGETGRPCPROXIES = (
      'targetGrpcProxies',
      'projects/{project}/global/targetGrpcProxies/{targetGrpcProxy}',
      {},
      ['project', 'targetGrpcProxy'],
      True
  )
  TARGETHTTPPROXIES = (
      'targetHttpProxies',
      'projects/{project}/global/targetHttpProxies/{targetHttpProxy}',
      {},
      ['project', 'targetHttpProxy'],
      True
  )
  TARGETHTTPSPROXIES = (
      'targetHttpsProxies',
      'projects/{project}/global/targetHttpsProxies/{targetHttpsProxy}',
      {},
      ['project', 'targetHttpsProxy'],
      True
  )
  TARGETINSTANCES = (
      'targetInstances',
      'projects/{project}/zones/{zone}/targetInstances/{targetInstance}',
      {},
      ['project', 'zone', 'targetInstance'],
      True
  )
  TARGETPOOLS = (
      'targetPools',
      'projects/{project}/regions/{region}/targetPools/{targetPool}',
      {},
      ['project', 'region', 'targetPool'],
      True
  )
  TARGETSSLPROXIES = (
      'targetSslProxies',
      'projects/{project}/global/targetSslProxies/{targetSslProxy}',
      {},
      ['project', 'targetSslProxy'],
      True
  )
  TARGETTCPPROXIES = (
      'targetTcpProxies',
      'projects/{project}/global/targetTcpProxies/{targetTcpProxy}',
      {},
      ['project', 'targetTcpProxy'],
      True
  )
  TARGETVPNGATEWAYS = (
      'targetVpnGateways',
      'projects/{project}/regions/{region}/targetVpnGateways/'
      '{targetVpnGateway}',
      {},
      ['project', 'region', 'targetVpnGateway'],
      True
  )
  URLMAPS = (
      'urlMaps',
      'projects/{project}/global/urlMaps/{urlMap}',
      {},
      ['project', 'urlMap'],
      True
  )
  VPNGATEWAYS = (
      'vpnGateways',
      'projects/{project}/regions/{region}/vpnGateways/{vpnGateway}',
      {},
      ['project', 'region', 'vpnGateway'],
      True
  )
  VPNTUNNELS = (
      'vpnTunnels',
      'projects/{project}/regions/{region}/vpnTunnels/{vpnTunnel}',
      {},
      ['project', 'region', 'vpnTunnel'],
      True
  )
  ZONEOPERATIONS = (
      'zoneOperations',
      'projects/{project}/zones/{zone}/operations/{operation}',
      {},
      ['project', 'zone', 'operation'],
      True
  )
  ZONES = (
      'zones',
      'projects/{project}/zones/{zone}',
      {},
      ['project', 'zone'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
