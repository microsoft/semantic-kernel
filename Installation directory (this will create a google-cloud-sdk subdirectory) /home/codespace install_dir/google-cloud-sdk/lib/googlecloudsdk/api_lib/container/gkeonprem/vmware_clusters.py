# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for gkeonprem API clients for VMware cluster resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Generator, Optional

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.api_lib.container.vmware import version_util
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


class ClustersClient(client.ClientBase):
  """Client for clusters in GKE On-Prem VMware API."""

  def __init__(self, **kwargs):
    super(ClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_vmwareClusters

  def List(
      self, args: parser_extensions.Namespace
  ) -> Generator[messages.VmwareCluster, None, None]:
    """Lists Clusters in the GKE On-Prem VMware API."""
    # Workaround for P4SA: Call query version config first, ignore the result.
    project = (
        args.project if args.project else properties.VALUES.core.project.Get()
    )
    # Hard code location to `us-west1`, because it cannot handle `--location=-`.
    parent = 'projects/{project}/locations/{location}'.format(
        project=project, location='us-west1'
    )
    dummy_request = messages.GkeonpremProjectsLocationsVmwareClustersQueryVersionConfigRequest(
        parent=parent,
    )
    _ = self._service.QueryVersionConfig(dummy_request)

    # If location is not specified, and container_vmware/location is not set,
    # list clusters of all locations within a project.
    if (
        'location' not in args.GetSpecifiedArgsDict()
        and not properties.VALUES.container_vmware.location.Get()
    ):
      args.location = '-'

    list_req = messages.GkeonpremProjectsLocationsVmwareClustersListRequest(
        parent=self._location_name(args)
    )

    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='vmwareClusters',
        batch_size=flags.Get(args, 'page_size'),
        limit=flags.Get(args, 'limit'),
        batch_size_attribute='pageSize',
    )

  def Enroll(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Enrolls a VMware cluster to Anthos."""
    kwargs = {
        'adminClusterMembership': self._admin_cluster_membership_name(args),
        'vmwareClusterId': self._user_cluster_id(args),
        'localName': flags.Get(args, 'local_name'),
        'validateOnly': flags.Get(args, 'validate_only'),
    }
    enroll_vmware_cluster_request = messages.EnrollVmwareClusterRequest(
        **kwargs
    )
    req = messages.GkeonpremProjectsLocationsVmwareClustersEnrollRequest(
        parent=self._user_cluster_parent(args),
        enrollVmwareClusterRequest=enroll_vmware_cluster_request,
    )
    return self._service.Enroll(req)

  def Unenroll(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Unenrolls an Anthos cluster on VMware."""
    kwargs = {
        'name': self._user_cluster_name(args),
        'force': flags.Get(args, 'force'),
        'allowMissing': flags.Get(args, 'allow_missing'),
        'validateOnly': flags.Get(args, 'validate_only'),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersUnenrollRequest(
        **kwargs
    )
    return self._service.Unenroll(req)

  def Delete(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Deletes an Anthos cluster on VMware."""
    kwargs = {
        'name': self._user_cluster_name(args),
        'allowMissing': flags.Get(args, 'allow_missing'),
        'validateOnly': flags.Get(args, 'validate_only'),
        'force': flags.Get(args, 'force'),
        'ignoreErrors': flags.Get(args, 'ignore_errors'),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersDeleteRequest(
        **kwargs
    )
    return self._service.Delete(req)

  def Create(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Creates an Anthos cluster on VMware."""
    kwargs = {
        'parent': self._user_cluster_parent(args),
        'validateOnly': flags.Get(args, 'validate_only'),
        'vmwareCluster': self._vmware_cluster(args),
        'vmwareClusterId': self._user_cluster_id(args),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersCreateRequest(
        **kwargs
    )
    return self._service.Create(req)

  def CreateFromImport(
      self,
      args: parser_extensions.Namespace,
      vmware_cluster,
      vmware_cluster_ref,
  ) -> messages.Operation:
    """Creates an Anthos cluster on VMware."""
    kwargs = {
        'parent': vmware_cluster_ref.Parent().RelativeName(),
        'validateOnly': flags.Get(args, 'validate_only'),
        'vmwareCluster': vmware_cluster,
        'vmwareClusterId': vmware_cluster_ref.Name(),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersCreateRequest(
        **kwargs
    )
    return self._service.Create(req)

  def Update(self, args: parser_extensions.Namespace) -> messages.Operation:
    kwargs = {
        'name': self._user_cluster_name(args),
        'allowMissing': flags.Get(args, 'allow_missing'),
        'updateMask': update_mask.get_update_mask(
            args, update_mask.VMWARE_CLUSTER_ARGS_TO_UPDATE_MASKS
        ),
        'validateOnly': flags.Get(args, 'validate_only'),
        'vmwareCluster': self._vmware_cluster(args),
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersPatchRequest(
        **kwargs
    )
    return self._service.Patch(req)

  def UpdateFromFile(
      self, args: parser_extensions.Namespace, vmware_cluster
  ) -> messages.Operation:
    # explicitly list supported mutable fields
    # etag is excluded from the mutable fields, because it is derived.
    top_level_mutable_fields = [
        'description',
        'on_prem_version',
        'annotations',
        'control_plane_node',
        'anti_affinity_groups',
        'storage',
        'network_config',
        'load_balancer',
        'dataplane_v2',
        'auto_repair_config',
        'authorization',
    ]
    kwargs = {
        'name': self._user_cluster_name(args),
        'allowMissing': flags.Get(args, 'allow_missing'),
        'updateMask': ','.join(top_level_mutable_fields),
        'validateOnly': flags.Get(args, 'validate_only'),
        'vmwareCluster': vmware_cluster,
    }
    req = messages.GkeonpremProjectsLocationsVmwareClustersPatchRequest(
        **kwargs
    )
    return self._service.Patch(req)

  def QueryVersionConfig(
      self, args: parser_extensions.Namespace
  ) -> messages.QueryVmwareVersionConfigResponse:
    kwargs = {
        'createConfig_adminClusterMembership': (
            self._admin_cluster_membership_name(args)
        ),
        'upgradeConfig_clusterName': self._user_cluster_name(args),
        'parent': self._location_ref(args).RelativeName(),
    }

    # This is a workaround for the limitation in apitools with nested messages.
    encoding.AddCustomJsonFieldMapping(
        messages.GkeonpremProjectsLocationsVmwareClustersQueryVersionConfigRequest,
        'createConfig_adminClusterMembership',
        'createConfig.adminClusterMembership',
    )
    encoding.AddCustomJsonFieldMapping(
        messages.GkeonpremProjectsLocationsVmwareClustersQueryVersionConfigRequest,
        'upgradeConfig_clusterName',
        'upgradeConfig.clusterName',
    )

    req = messages.GkeonpremProjectsLocationsVmwareClustersQueryVersionConfigRequest(
        **kwargs
    )
    return self._service.QueryVersionConfig(req)

  def _vmware_cluster(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareCluster."""
    kwargs = {
        'name': self._user_cluster_name(args),
        'adminClusterMembership': self._admin_cluster_membership_name(args),
        'description': flags.Get(args, 'description'),
        'onPremVersion': flags.Get(args, 'version'),
        'annotations': self._annotations(args),
        'controlPlaneNode': self._vmware_control_plane_node_config(args),
        'antiAffinityGroups': self._vmware_aag_config(args),
        'storage': self._vmware_storage_config(args),
        'networkConfig': self._vmware_network_config(args),
        'loadBalancer': self._vmware_load_balancer_config(args),
        'vcenter': self._vmware_vcenter_config(args),
        'dataplaneV2': self._vmware_dataplane_v2_config(args),
        'vmTrackingEnabled': self._vm_tracking_enabled(args),
        'autoRepairConfig': self._vmware_auto_repair_config(args),
        'authorization': self._authorization(args),
        'enableControlPlaneV2': self._enable_control_plane_v2(args),
        'upgradePolicy': self._upgrade_policy(args),
    }
    if any(kwargs.values()):
      return messages.VmwareCluster(**kwargs)
    return None

  def _vmware_vcenter_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareVCenterConfig."""
    kwargs = {
        'caCertData': flags.Get(args, 'vcenter_ca_cert_data'),
        'cluster': flags.Get(args, 'vcenter_cluster'),
        'datacenter': flags.Get(args, 'vcenter_datacenter'),
        'datastore': flags.Get(args, 'vcenter_datastore'),
        'folder': flags.Get(args, 'vcenter_folder'),
        'resourcePool': flags.Get(args, 'vcenter_resource_pool'),
        'storagePolicyName': flags.Get(args, 'vcenter_storage_policy_name'),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareVCenterConfig(**kwargs)
    return None

  def _upgrade_policy(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareClusterUpgradePolicy."""
    if '--upgrade-policy' not in args.GetSpecifiedArgNames():
      return None

    upgrade_policy = args.upgrade_policy
    return messages.VmwareClusterUpgradePolicy(
        controlPlaneOnly=upgrade_policy.get('control-plane-only', None),
    )

  def _enable_control_plane_v2(self, args: parser_extensions.Namespace):
    """While creating a 1.15+ user cluster, default enable_control_plane_v2 to True if not set."""
    if 'enable_control_plane_v2' in args.GetSpecifiedArgsDict():
      return True

    if 'disable_control_plane_v2' in args.GetSpecifiedArgsDict():
      return False

    default_enable_control_plane_v2 = '1.15.0-gke.0'
    if args.command_path[-1] == 'create' and version_util.Version(
        args.version
    ).feature_available(default_enable_control_plane_v2):
      return True

    return None

  def _vm_tracking_enabled(self, args: parser_extensions.Namespace):
    if flags.Get(args, 'enable_vm_tracking'):
      return True
    return None

  def auto_repair_enabled(self, args: parser_extensions.Namespace):
    if flags.Get(args, 'enable_auto_repair'):
      return True
    if flags.Get(args, 'disable_auto_repair'):
      return False
    return None

  def _vmware_auto_repair_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareAutoRepairConfig."""
    kwargs = {
        'enabled': self.auto_repair_enabled(args),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareAutoRepairConfig(**kwargs)
    return None

  def _cluster_users(self, args: parser_extensions.Namespace):
    """Constructs repeated proto message ClusterUser."""
    cluster_user_messages = []
    admin_users = flags.Get(args, 'admin_users')
    if admin_users:
      for admin_user in admin_users:
        cluster_user_message = messages.ClusterUser(username=admin_user)
        cluster_user_messages.append(cluster_user_message)
      return cluster_user_messages

    # On update, skip setting default value.
    if args.command_path[-1] == 'update':
      return None

    # On create, client side default admin user to the current gcloud user.
    gcloud_config_core_account = properties.VALUES.core.account.Get()
    if gcloud_config_core_account:
      default_admin_user_message = messages.ClusterUser(
          username=gcloud_config_core_account
      )
      cluster_user_messages.append(default_admin_user_message)
      return cluster_user_messages

    return None

  def _authorization(self, args: parser_extensions.Namespace):
    """Constructs proto message Authorization."""
    kwargs = {
        'adminUsers': self._cluster_users(args),
    }
    if flags.IsSet(kwargs):
      return messages.Authorization(**kwargs)
    return None

  def _dataplane_v2_enabled(self, args: parser_extensions.Namespace):
    """Constructs proto field dataplane_v2_enabled."""
    if flags.Get(args, 'enable_dataplane_v2'):
      return True
    if flags.Get(args, 'disable_dataplane_v2'):
      return False
    return None

  def _advanced_networking(self, args: parser_extensions.Namespace):
    """Constructs proto field advanced_networking."""
    if flags.Get(args, 'enable_advanced_networking'):
      return True
    if flags.Get(args, 'disable_advanced_networking'):
      return False
    return None

  def _vmware_dataplane_v2_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareDataplaneV2Config."""
    kwargs = {
        'dataplaneV2Enabled': flags.Get(args, 'enable_dataplane_v2'),
        'advancedNetworking': flags.Get(args, 'enable_advanced_networking'),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareDataplaneV2Config(**kwargs)
    return None

  def _vsphere_csi_disabled(self, args: parser_extensions.Namespace):
    """Constructs proto field vsphere_csi_disabled."""
    if flags.Get(args, 'disable_vsphere_csi'):
      return True
    if flags.Get(args, 'enable_vsphere_csi'):
      return False
    return None

  def _vmware_storage_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareStorageConfig."""
    kwargs = {
        'vsphereCsiDisabled': self._vsphere_csi_disabled(args),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareStorageConfig(**kwargs)
    return None

  def _aag_config_disabled(self, args: parser_extensions.Namespace):
    """Constructs proto field aag_config_disabled."""
    if flags.Get(args, 'disable_aag_config'):
      return True
    if flags.Get(args, 'enable_aag_config'):
      return False
    return None

  def _vmware_aag_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareAAGConfig."""
    kwargs = {
        'aagConfigDisabled': self._aag_config_disabled(args),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareAAGConfig(**kwargs)
    return None

  def _auto_resize_enabled(self, args: parser_extensions.Namespace):
    """Constructs proto field auto_resize_config.enabled."""
    if flags.Get(args, 'enable_auto_resize'):
      return True
    if flags.Get(args, 'disable_auto_resize'):
      return False
    return None

  def _vmware_auto_resize_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareAutoResizeConfig."""
    kwargs = {
        'enabled': self._auto_resize_enabled(args),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareAutoResizeConfig(**kwargs)
    return None

  def _vmware_control_plane_node_config(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message VmwareControlPlaneNodeConfig."""
    kwargs = {
        'autoResizeConfig': self._vmware_auto_resize_config(args),
        'cpus': flags.Get(args, 'cpus'),
        'memory': flags.Get(args, 'memory'),
        'replicas': flags.Get(args, 'replicas'),
        'vsphereConfig': self._vmware_control_plane_vsphere_config(args),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareControlPlaneNodeConfig(**kwargs)
    return None

  def _vmware_control_plane_vsphere_config(
      self, args: parser_extensions.Namespace
  ) -> Optional[messages.VmwareControlPlaneVsphereConfig]:
    """Constructs proto message VmwareControlPlaneVsphereConfig."""
    if 'control_plane_vsphere_config' not in args.GetSpecifiedArgsDict():
      return None

    kwargs = {
        'datastore': args.control_plane_vsphere_config.get('datastore', None),
        'storagePolicyName': args.control_plane_vsphere_config.get(
            'storage-policy-name', None
        ),
    }
    return messages.VmwareControlPlaneVsphereConfig(**kwargs)

  def _create_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for create command."""
    annotations = flags.Get(args, 'annotations')
    return self._dict_to_annotations_message(annotations)

  def _update_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for update command."""
    annotation_flags = [
        'add_annotations',
        'clear_annotations',
        'remove_annotations',
        'set_annotations',
    ]
    if all(
        flag not in args.GetSpecifiedArgsDict() for flag in annotation_flags
    ):
      return None

    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_response = self.Describe(cluster_ref)

    curr_annotations = {}
    if cluster_response.annotations:
      for annotation in cluster_response.annotations.additionalProperties:
        curr_annotations[annotation.key] = annotation.value

    if 'add_annotations' in args.GetSpecifiedArgsDict():
      for key, value in args.add_annotations.items():
        curr_annotations[key] = value
      return self._dict_to_annotations_message(curr_annotations)
    elif 'clear_annotations' in args.GetSpecifiedArgsDict():
      return messages.VmwareCluster.AnnotationsValue()
    elif 'remove_annotations' in args.GetSpecifiedArgsDict():
      updated_annotations = {
          key: value
          for key, value in curr_annotations.items()
          if key not in args.remove_annotations
      }
      return self._dict_to_annotations_message(updated_annotations)
    elif 'set_annotations' in args.GetSpecifiedArgsDict():
      return self._dict_to_annotations_message(args.set_annotations)

    return None

  def _dict_to_annotations_message(self, annotations):
    additional_property_messages = []
    if not annotations:
      return None

    for key, value in annotations.items():
      additional_property_messages.append(
          messages.VmwareCluster.AnnotationsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    annotation_value_message = messages.VmwareCluster.AnnotationsValue(
        additionalProperties=additional_property_messages
    )
    return annotation_value_message

  def _annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue."""
    if args.command_path[-1] == 'create':
      return self._create_annotations(args)
    elif args.command_path[-1] == 'update':
      return self._update_annotations(args)
    return None

  def _vmware_host_ip(self, host_ip) -> messages.VmwareHostIp:
    """Constructs proto message VmwareHostIp."""
    hostname = host_ip.get('hostname', None)
    if not hostname:
      raise InvalidConfigFile(
          'Missing field [hostname] in Static IP configuration file.'
      )

    ip = host_ip.get('ip', None)
    if not ip:
      raise InvalidConfigFile(
          'Missing field [ip] in Static IP configuration file.'
      )

    kwargs = {'hostname': hostname, 'ip': ip}
    return messages.VmwareHostIp(**kwargs)

  def _vmware_ip_block(self, ip_block):
    """Constructs proto message VmwareIpBlock."""
    gateway = ip_block.get('gateway', None)
    if not gateway:
      raise InvalidConfigFile(
          'Missing field [gateway] in Static IP configuration file.'
      )

    netmask = ip_block.get('netmask', None)
    if not netmask:
      raise InvalidConfigFile(
          'Missing field [netmask] in Static IP configuration file.'
      )

    host_ips = ip_block.get('ips', [])
    if not host_ips:
      raise InvalidConfigFile(
          'Missing field [ips] in Static IP configuration file.'
      )

    kwargs = {
        'gateway': gateway,
        'netmask': netmask,
        'ips': [self._vmware_host_ip(host_ip) for host_ip in host_ips],
    }
    if flags.IsSet(kwargs):
      return messages.VmwareIpBlock(**kwargs)
    return None

  def _vmware_static_ip_config_from_file(
      self, args: parser_extensions.Namespace
  ):
    file_content = args.static_ip_config_from_file
    static_ip_config = file_content.get('staticIPConfig', None)
    if not static_ip_config:
      raise InvalidConfigFile(
          'Missing field [staticIPConfig] in Static IP configuration file.'
      )

    ip_blocks = static_ip_config.get('ipBlocks', [])
    if not ip_blocks:
      raise InvalidConfigFile(
          'Missing field [ipBlocks] in Static IP configuration file.'
      )

    kwargs = {
        'ipBlocks': [self._vmware_ip_block(ip_block) for ip_block in ip_blocks],
    }
    if flags.IsSet(kwargs):
      return messages.VmwareStaticIpConfig(**kwargs)
    return None

  def _vmware_static_ip_config_ip_blocks(
      self, args: parser_extensions.Namespace
  ):
    vmware_static_ip_config_message = messages.VmwareStaticIpConfig()
    for ip_block in args.static_ip_config_ip_blocks:
      vmware_ip_block_message = messages.VmwareIpBlock(
          gateway=ip_block['gateway'],
          netmask=ip_block['netmask'],
          ips=[
              messages.VmwareHostIp(ip=ip[0], hostname=ip[1])
              for ip in ip_block['ips']
          ],
      )
      vmware_static_ip_config_message.ipBlocks.append(vmware_ip_block_message)
    return vmware_static_ip_config_message

  def _vmware_static_ip_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareStaticIpConfig."""
    if 'static_ip_config_from_file' in args.GetSpecifiedArgsDict():
      return self._vmware_static_ip_config_from_file(args)

    if 'static_ip_config_ip_blocks' in args.GetSpecifiedArgsDict():
      return self._vmware_static_ip_config_ip_blocks(args)

    return None

  def _vmware_dhcp_ip_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareDhcpIpConfig."""
    kwargs = {
        'enabled': flags.Get(args, 'enable_dhcp'),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareDhcpIpConfig(**kwargs)
    return None

  def _vmware_host_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareHostConfig."""
    kwargs = {
        'dnsServers': flags.Get(args, 'dns_servers', []),
        'ntpServers': flags.Get(args, 'ntp_servers', []),
        'dnsSearchDomains': flags.Get(args, 'dns_search_domains', []),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareHostConfig(**kwargs)
    return None

  def _control_plane_ip_block(self, args: parser_extensions.Namespace):
    """Constructs proto message ControlPlaneIpBlock."""
    if 'control_plane_ip_block' not in args.GetSpecifiedArgsDict():
      return None

    kwargs = {
        'gateway': args.control_plane_ip_block.get('gateway', None),
        'netmask': args.control_plane_ip_block.get('netmask', None),
        'ips': [
            messages.VmwareHostIp(ip=ip[0], hostname=ip[1])
            for ip in args.control_plane_ip_block.get('ips', [])
        ],
    }
    return messages.VmwareIpBlock(**kwargs)

  def _vmware_control_plane_v2_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareControlPlaneV2Config."""
    kwargs = {
        'controlPlaneIpBlock': self._control_plane_ip_block(args),
    }
    if any(kwargs.values()):
      return messages.VmwareControlPlaneV2Config(**kwargs)
    return None

  def _vmware_network_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareNetworkConfig."""
    kwargs = {
        'serviceAddressCidrBlocks': flags.Get(
            args, 'service_address_cidr_blocks', []
        ),
        'podAddressCidrBlocks': flags.Get(args, 'pod_address_cidr_blocks', []),
        'staticIpConfig': self._vmware_static_ip_config(args),
        'dhcpIpConfig': self._vmware_dhcp_ip_config(args),
        'hostConfig': self._vmware_host_config(args),
        'controlPlaneV2Config': self._vmware_control_plane_v2_config(args),
    }
    if any(kwargs.values()):
      return messages.VmwareNetworkConfig(**kwargs)
    return None

  def _vmware_load_balancer_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareLoadBalancerConfig."""
    kwargs = {
        'f5Config': self._vmware_f5_big_ip_config(args),
        'metalLbConfig': self._vmware_metal_lb_config(args),
        'manualLbConfig': self._vmware_manual_lb_config(args),
        'vipConfig': self._vmware_vip_config(args),
    }
    if any(kwargs.values()):
      return messages.VmwareLoadBalancerConfig(**kwargs)
    return None

  def _vmware_vip_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareVipConfig."""
    kwargs = {
        'controlPlaneVip': flags.Get(args, 'control_plane_vip'),
        'ingressVip': flags.Get(args, 'ingress_vip'),
    }
    if any(kwargs.values()):
      return messages.VmwareVipConfig(**kwargs)
    return None

  def _vmware_f5_big_ip_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareF5BigIpConfig."""
    kwargs = {
        'address': flags.Get(args, 'f5_config_address'),
        'partition': flags.Get(args, 'f5_config_partition'),
        'snatPool': flags.Get(args, 'f5_config_snat_pool'),
    }
    if any(kwargs.values()):
      return messages.VmwareF5BigIpConfig(**kwargs)
    return None

  def _vmware_metal_lb_config_from_file(
      self, args: parser_extensions.Namespace
  ) -> messages.VmwareMetalLbConfig:
    file_content = args.metal_lb_config_from_file
    metal_lb_config = file_content.get('metalLBConfig', None)
    if not metal_lb_config:
      raise InvalidConfigFile(
          'Missing field [metalLBConfig] in Metal LB configuration file.'
      )

    address_pools = metal_lb_config.get('addressPools', [])
    if not address_pools:
      raise InvalidConfigFile(
          'Missing field [addressPools] in Metal LB configuration file.'
      )

    kwargs = {
        'addressPools': self._address_pools(address_pools),
    }
    return messages.VmwareMetalLbConfig(**kwargs)

  def _vmware_metal_lb_config_from_flag(
      self, args: parser_extensions.Namespace
  ) -> messages.VmwareMetalLbConfig:
    vmware_metal_lb_config = messages.VmwareMetalLbConfig()
    for address_pool in args.metal_lb_config_address_pools:
      address_pool_message = messages.VmwareAddressPool(
          addresses=address_pool.get('addresses', []),
          avoidBuggyIps=address_pool.get('avoid-buggy-ips', None),
          manualAssign=address_pool.get('manual-assign', None),
          pool=address_pool.get('pool', None),
      )
      vmware_metal_lb_config.addressPools.append(address_pool_message)
    return vmware_metal_lb_config

  def _vmware_metal_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareMetalLbConfig."""
    if 'metal_lb_config_from_file' in args.GetSpecifiedArgsDict():
      return self._vmware_metal_lb_config_from_file(args)
    elif 'metal_lb_config_address_pools' in args.GetSpecifiedArgsDict():
      return self._vmware_metal_lb_config_from_flag(args)
    else:
      return None

  def _vmware_manual_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareManualLbConfig."""
    kwargs = {
        'controlPlaneNodePort': flags.Get(args, 'control_plane_node_port'),
        'ingressHttpNodePort': flags.Get(args, 'ingress_http_node_port'),
        'ingressHttpsNodePort': flags.Get(args, 'ingress_https_node_port'),
        'konnectivityServerNodePort': flags.Get(
            args, 'konnectivity_server_node_port'
        ),
    }
    if flags.IsSet(kwargs):
      return messages.VmwareManualLbConfig(**kwargs)
    return None

  def _address_pools(self, address_pools):
    """Constructs proto message field address_pools."""
    return [
        self._vmware_address_pool(address_pool)
        for address_pool in address_pools
    ]

  def _vmware_address_pool(self, address_pool) -> messages.VmwareAddressPool:
    """Constructs proto message VmwareAddressPool."""
    addresses = address_pool.get('addresses', [])
    if not addresses:
      raise InvalidConfigFile(
          'Missing field [addresses] in Metal LB configuration file.'
      )

    avoid_buggy_ips = address_pool.get('avoidBuggyIPs', None)
    manual_assign = address_pool.get('manualAssign', None)

    pool = address_pool.get('pool', None)
    if not pool:
      raise InvalidConfigFile(
          'Missing field [pool] in Metal LB configuration file.'
      )

    kwargs = {
        'addresses': addresses,
        'avoidBuggyIps': avoid_buggy_ips,
        'manualAssign': manual_assign,
        'pool': pool,
    }
    return messages.VmwareAddressPool(**kwargs)


class InvalidConfigFile(exceptions.Error):
  """Invalid Argument."""

  pass
