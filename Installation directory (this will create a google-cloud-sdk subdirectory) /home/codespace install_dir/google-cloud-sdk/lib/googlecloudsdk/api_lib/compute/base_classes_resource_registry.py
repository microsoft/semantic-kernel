# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""A list of resources and their canonical format. This is deprecated."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_info


RESOURCE_REGISTRY = {
    'compute.addresses':
        resource_info.ResourceInfo(
            cache_command='compute addresses list',
            list_format="""
          table(
            name,
            region.basename(),
            address,
            status
          )
        """,),
    'compute.autoscalers':
        resource_info.ResourceInfo(
            async_collection='compute.operations',
            cache_command='compute autoscaler list',
            list_format="""
          table(
            name,
            target.basename(),
            autoscalingPolicy.policy():label=POLICY
          )
        """,),
    'compute.backendBuckets':
        resource_info.ResourceInfo(
            list_format="""
          table(
            name,
            bucketName:label=GCS_BUCKET_NAME,
            enableCdn
          )
        """,),
    'compute.backendServiceGroupHealth':
        resource_info.ResourceInfo(
            list_format="""
          default
        """,),
    'compute.backendServices':
        resource_info.ResourceInfo(
            cache_command='compute backend-services list',
            list_format="""
          table(
            name,
            backends[].group.list():label=BACKENDS,
            protocol
          )
        """,),
    'compute.backendServices.alpha':
        resource_info.ResourceInfo(
            cache_command='compute backend-services list',
            list_format="""
          table(
            name,
            backends[].group.list():label=BACKENDS,
            protocol,
            loadBalancingScheme,
            healthChecks.map().basename().list()
          )
        """,),
    'compute.regionBackendServices':
        resource_info.ResourceInfo(
            cache_command='compute backend-services list',
            list_format="""
          table(
            name,
            backends[].group.list():label=BACKENDS,
            protocol,
            loadBalancingScheme,
            healthChecks.map().basename().list()
          )
        """,),
    'compute.commitments':
        resource_info.ResourceInfo(
            cache_command='compute commitments list',
            list_format="""
          table(name,
                region.basename(),
                endTimestamp,
                status)
                """,),
    'compute.disks':
        resource_info.ResourceInfo(
            cache_command='compute disks list',
            list_format="""
          table(
            name,
            zone.basename(),
            sizeGb,
            type.basename(),
            status
          )
        """,),
    'compute.diskTypes':
        resource_info.ResourceInfo(
            cache_command='compute disk-types list',
            list_format="""
          table(
            name,
            zone.basename(),
            validDiskSize:label=VALID_DISK_SIZES
          )
        """,),
    'compute.diskTypes.alpha':
        resource_info.ResourceInfo(
            cache_command='compute disk-types list',
            list_format="""
          table(
            name,
            location():label=LOCATION,
            location_scope():label=SCOPE,
            validDiskSize:label=VALID_DISK_SIZES
          )
        """,),
    'compute.firewalls':
        resource_info.ResourceInfo(
            cache_command='compute firewall-rules list',
            list_format="""
          table(
            name,
            network.basename(),
            direction,
            priority,
            allowed[].map().firewall_rule().list():label=ALLOW,
            denied[].map().firewall_rule().list():label=DENY
          )
        """,),
    'compute.forwardingRules':
        resource_info.ResourceInfo(
            cache_command='compute forwarding-rules list',
            list_format="""
          table(
            name,
            region.basename(),
            IPAddress,
            IPProtocol,
            firstof(
                target,
                backendService).scope():label=TARGET
          )
        """,),
    'compute.groups':
        resource_info.ResourceInfo(
            cache_command='compute groups list',
            list_format="""
          table(
            name,
            members.len():label=NUM_MEMBERS,
            description
          )
        """,),
    'compute.healthChecks':
        resource_info.ResourceInfo(
            cache_command='compute health-checks list',
            list_format="""
          table(
            name,
            type:label=PROTOCOL
          )
        """,),
    'compute.httpHealthChecks':
        resource_info.ResourceInfo(
            cache_command='compute http-health-checks list',
            list_format="""
          table(
            name,
            host,
            port,
            requestPath
          )
        """,),
    'compute.httpsHealthChecks':
        resource_info.ResourceInfo(
            cache_command='compute https-health-checks list',
            list_format="""
          table(
            name,
            host,
            port,
            requestPath
          )
        """,),
    'compute.images':
        resource_info.ResourceInfo(
            cache_command='compute images list',
            list_format="""
          table(
            name,
            selfLink.map().scope(projects).segment(0):label=PROJECT,
            family,
            deprecated.state:label=DEPRECATED,
            status
          )
        """,),
    'compute.instanceGroups':
        resource_info.ResourceInfo(
            cache_command='compute instance-groups list',
            list_format="""
          table(
            name,
            location():label=LOCATION,
            location_scope():label=SCOPE,
            network.basename(),
            isManaged:label=MANAGED,
            size:label=INSTANCES
          )
        """,),
    'compute.instanceGroupManagers':
        resource_info.ResourceInfo(
            cache_command='compute instance-groups managed list',
            list_format="""
          table(
            name,
            location():label=LOCATION,
            location_scope():label=SCOPE,
            baseInstanceName,
            size,
            targetSize,
            instanceTemplate.basename(),
            autoscaled
          )
        """,),
    'compute.instances':
        resource_info.ResourceInfo(
            async_collection='compute.operations',
            cache_command='compute instances list',
            list_format="""
          table(
            name,
            zone.basename(),
            machineType.machine_type().basename(),
            scheduling.preemptible.yesno(yes=true, no=''),
            networkInterfaces[].networkIP.notnull().list():label=INTERNAL_IP,
            networkInterfaces[].accessConfigs[0].natIP.notnull().list()\
            :label=EXTERNAL_IP,
            status
          )
        """,),
    'compute.instanceTemplates':
        resource_info.ResourceInfo(
            cache_command='compute instance-templates list',
            list_format="""
          table(
            name,
            properties.machineType.machine_type(),
            properties.scheduling.preemptible.yesno(yes=true, no=''),
            creationTimestamp
          )
        """,),
    'compute.invalidations':
        resource_info.ResourceInfo(
            cache_command='beta compute url-maps list-cdn-cache-invalidations',
            list_format="""
          table(
            description,
            operation_http_status():label=HTTP_STATUS,
            status,
            insertTime:label=TIMESTAMP
          )
        """,),
    'compute.machineTypes':
        resource_info.ResourceInfo(
            cache_command='compute machine-types list',
            list_format="""
          table(
            name,
            zone.basename(),
            guestCpus:label=CPUS,
            memoryMb.size(units_in=MiB, units_out=GiB, precision=2):label=MEMORY_GB,
            deprecated.state:label=DEPRECATED
          )
        """,),
    'compute.networks':
        resource_info.ResourceInfo(
            cache_command='compute networks list',
            list_format="""
          table(
            name,
            x_gcloud_mode:label=MODE,
            IPv4Range:label=IPV4_RANGE,
            gatewayIPv4
          )
        """,),
    'compute.operations':
        resource_info.ResourceInfo(
            list_format="""
          table(
            name,
            operationType:label=TYPE,
            targetLink.scope():label=TARGET,
            operation_http_status():label=HTTP_STATUS,
            status,
            insertTime:label=TIMESTAMP
          )
        """,),
    'compute.peerings':
        resource_info.ResourceInfo(
            cache_command='compute networks peerings list',
            list_format="""
          table(
            name,
            source_network.basename():label=NETWORK,
            network.map().scope(projects).segment(0):label=PEER_PROJECT,
            network.basename():label=PEER_NETWORK,
            autoCreateRoutes,
            state,
            stateDetails
          )
        """,),
    'compute.projects':
        resource_info.ResourceInfo(
            list_format="""
          value(
            format("There is no API support yet.")
          )
        """,),
    'compute.xpnProjects':
        resource_info.ResourceInfo(
            list_format="""
          table(
            name,
            creationTimestamp,
            xpnProjectStatus
          )
        """,),
    'compute.xpnResourceId':
        resource_info.ResourceInfo(
            list_format="""
          table(
            id:label=RESOURCE_ID,
            type:label=RESOURCE_TYPE)
        """,),
    'compute.regions':
        resource_info.ResourceInfo(
            cache_command='compute regions list',
            list_format="""
          table(
            name,
            quotas.metric.CPUS.quota():label=CPUS,
            quotas.metric.DISKS_TOTAL_GB.quota():label=DISKS_GB,
            quotas.metric.IN_USE_ADDRESSES.quota():label=ADDRESSES,
            quotas.metric.STATIC_ADDRESSES.quota():label=RESERVED_ADDRESSES,
            status():label=STATUS,
            deprecated.deleted:label=TURNDOWN_DATE
          )
        """,),
    'compute.routers':
        resource_info.ResourceInfo(
            cache_command='compute routers list',
            list_format="""
          table(
            name,
            region.basename(),
            network.basename()
          )
        """,),
    'compute.routes':
        resource_info.ResourceInfo(
            cache_command='compute routes list',
            list_format="""
          table(
            name,
            network.basename(),
            destRange,
            firstof(
                nextHopInstance,
                nextHopGateway,
                nextHopIp,
                nextHopVpnTunnel,
                nextHopPeering).scope()
              :label=NEXT_HOP,
            priority
          )
        """,),
    'compute.snapshots':
        resource_info.ResourceInfo(
            cache_command='compute snapshots list',
            list_format="""
          table(
            name,
            diskSizeGb,
            sourceDisk.scope():label=SRC_DISK,
            status
          )
        """,),
    'compute.sslCertificates':
        resource_info.ResourceInfo(
            cache_command='compute ssl-certificates list',
            list_format="""
          table(
            name,
            creationTimestamp
          )
        """,),
    'compute.subnetworks':
        resource_info.ResourceInfo(
            cache_command='compute networks subnets list',
            list_format="""
          table(
            name,
            region.basename(),
            network.basename(),
            ipCidrRange:label=RANGE
          )
        """,),
    'compute.targetHttpProxies':
        resource_info.ResourceInfo(
            cache_command='compute target-http-proxies list',
            list_format="""
          table(
            name,
            urlMap.basename()
          )
        """,),
    'compute.targetHttpsProxies':
        resource_info.ResourceInfo(
            cache_command='compute target-https-proxies list',
            list_format="""
          table(
            name,
            sslCertificates.map().basename().list():label=SSL_CERTIFICATES,
            urlMap.basename()
          )
        """,),
    'compute.targetInstances':
        resource_info.ResourceInfo(
            cache_command='compute target-instances list',
            list_format="""
          table(
            name,
            zone.basename(),
            instance.basename(),
            natPolicy
          )
        """,),
    'compute.targetPoolInstanceHealth':
        resource_info.ResourceInfo(
            list_format="""
          default
        """,),
    'compute.targetPools':
        resource_info.ResourceInfo(
            cache_command='compute target-pools list',
            list_format="""
          table(
            name,
            region.basename(),
            sessionAffinity,
            backupPool.basename():label=BACKUP,
            healthChecks[].map().basename().list():label=HEALTH_CHECKS
          )
        """,),
    'compute.targetSslProxies':
        resource_info.ResourceInfo(
            cache_command='compute target-ssl-proxies list',),
    'compute.targetTcpProxies':
        resource_info.ResourceInfo(
            cache_command='compute target-tcp-proxies list',),
    'compute.targetVpnGateways':
        resource_info.ResourceInfo(
            cache_command='compute target-vpn-gateways list',
            list_format="""
          table(
            name,
            network.basename(),
            region.basename()
          )
        """,),
    'compute.urlMaps':
        resource_info.ResourceInfo(
            cache_command='compute url-maps list',
            list_format="""
          table(
            name,
            defaultService
          )
        """,),
    'compute.users':
        resource_info.ResourceInfo(
            cache_command='compute users list',
            list_format="""
          table(
            name,
            owner,
            description
          )
        """,),
    'compute.vpnTunnels':
        resource_info.ResourceInfo(
            cache_command='compute vpn-tunnels list',
            list_format="""
          table(
            name,
            region.basename(),
            targetVpnGateway.basename():label=GATEWAY,
            peerIp:label=PEER_ADDRESS
          )
        """,),
    'compute.zones':
        resource_info.ResourceInfo(
            cache_command='compute zones list',
            list_format="""
          table(
            name,
            region.basename(),
            status():label=STATUS,
            maintenanceWindows.next_maintenance():label=NEXT_MAINTENANCE,
            deprecated.deleted:label=TURNDOWN_DATE
          )
        """,),
}
