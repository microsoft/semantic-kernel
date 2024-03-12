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
"""Utilities for working with update mask."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

VMWARE_CLUSTER_ARGS_TO_UPDATE_MASKS = {
    'description': 'description',
    'version': 'on_prem_version',
    'add_annotations': 'annotations',
    'clear_annotations': 'annotations',
    'remove_annotations': 'annotations',
    'set_annotations': 'annotations',
    'cpus': 'control_plane_node.cpus',
    'memory': 'control_plane_node.memory',
    'enable_auto_resize': 'control_plane_node.auto_resize_config.enabled',
    'disable_auto_resize': 'control_plane_node.auto_resize_config.enabled',
    'enable_aag_config': 'anti_affinity_groups.aag_config_disabled',
    'disable_aag_config': 'anti_affinity_groups.aag_config_disabled',
    'enable_vsphere_csi': 'storage.vsphere_csi_disabled',
    'disable_vsphere_csi': 'storage.vsphere_csi_disabled',
    'static_ip_config_from_file': 'network_config.static_ip_config',
    'static_ip_config_ip_blocks': 'network_config.static_ip_config',
    'metal_lb_config_from_file': 'load_balancer.metal_lb_config',
    'metal_lb_config_address_pools': 'load_balancer.metal_lb_config',
    'enable_auto_repair': 'auto_repair_config.enabled',
    'disable_auto_repair': 'auto_repair_config.enabled',
    'admin_users': 'authorization.admin_users',
    'upgrade_control_plane': 'upgrade_policy',
}

VMWARE_NODE_POOL_ARGS_TO_UPDATE_MASKS = {
    'display_name': 'display_name',
    'version': 'on_prem_version',
    'min_replicas': 'node_pool_autoscaling.min_replicas',
    'max_replicas': 'node_pool_autoscaling.max_replicas',
    'cpus': 'config.cpus',
    'memory': 'config.memory_mb',
    'replicas': 'config.replicas',
    'image_type': 'config.image_type',
    'image': 'config.image',
    'boot_disk_size': 'config.boot_disk_size_gb',
    'node_taints': 'config.taints',
    'node_labels': 'config.labels',
    'enable_load_balancer': 'config.enable_load_balancer',
    'disable_load_balancer': 'config.enable_load_balancer',
}

VMWARE_ADMIN_CLUSTER_ARGS_TO_UPDATE_MASKS = {
    'required_platform_version': 'platform_config.required_platform_version',
}

BARE_METAL_CLUSTER_ARGS_TO_UPDATE_MASKS = {
    'metal_lb_address_pools_from_file': (
        'load_balancer.metal_lb_config.address_pools'
    ),
    'metal_lb_address_pools': 'load_balancer.metal_lb_config.address_pools',
    'metal_lb_load_balancer_node_configs_from_file': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.node_configs',
    'metal_lb_load_balancer_node_configs': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.node_configs',
    'metal_lb_load_balancer_node_labels': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.labels',
    'metal_lb_load_balancer_node_taints': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.taints',
    'metal_lb_load_balancer_registry_pull_qps': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.registry_pull_qps',
    'metal_lb_load_balancer_registry_burst': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.registry_burst',
    'disable_metal_lb_load_balancer_serialize_image_pulls': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.serialize_image_pulls_disabled',
    'enable_metal_lb_load_balancer_serialize_image_pulls': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.serialize_image_pulls_disabled',
    'control_plane_node_configs_from_file': 'control_plane.control_plane_node_pool_config.node_pool_config.node_configs',
    'control_plane_node_configs': 'control_plane.control_plane_node_pool_config.node_pool_config.node_configs',
    'control_plane_node_labels': (
        'control_plane.control_plane_node_pool_config.node_pool_config.labels'
    ),
    'control_plane_node_taints': (
        'control_plane.control_plane_node_pool_config.node_pool_config.taints'
    ),
    'control_plane_registry_pull_qps': 'control_plane.control_plane_node_pool_config.node_pool_config.kubelet_config.registry_pull_qps',
    'control_plane_registry_burst': 'control_plane.control_plane_node_pool_config.node_pool_config.kubelet_config.registry_burst',
    'disable_control_plane_serialize_image_pulls': 'control_plane.control_plane_node_pool_config.node_pool_config.kubelet_config.serialize_image_pulls_disabled',
    'enable_control_plane_serialize_image_pulls': 'control_plane.control_plane_node_pool_config.node_pool_config.kubelet_config.serialize_image_pulls_disabled',
    'api_server_args': 'control_plane.api_server_args',
    'description': 'description',
    'version': 'bare_metal_version',
    'enable_application_logs': 'cluster_operations.enable_application_logs',
    'maintenance_address_cidr_blocks': (
        'maintenance_config.maintenance_address_cidr_blocks'
    ),
    'admin_users': 'security_config.authorization.admin_users',
    'login_user': 'node_access_config.login_user',
    'island_mode_service_address_cidr_blocks': (
        'network_config.island_mode_cidr.service_address_cidr_blocks'
    ),
    'enable_sr_iov_config': 'network_config.sr_iov_config.enabled',
    'disable_sr_iov_config': 'network_config.sr_iov_config.enabled',
    'bgp_asn': 'load_balancer.bgp_lb_config.asn',
    'bgp_peer_configs': 'load_balancer.bgp_lb_config.bgp_peer_configs',
    'bgp_address_pools': 'load_balancer.bgp_lb_config.address_pools',
    'bgp_load_balancer_node_configs': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.node_configs',
    'bgp_load_balancer_node_taints': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.taints',
    'bgp_load_balancer_node_labels': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.labels',
    'bgp_load_balancer_registry_pull_qps': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.registry_pull_qps',
    'bgp_load_balancer_registry_burst': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.registry_burst',
    'disable_bgp_load_balancer_serialize_image_pulls': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.serialize_image_pulls_disabled',
    'enable_bgp_load_balancer_serialize_image_pulls': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.kubelet_config.serialize_image_pulls_disabled',
    'add_annotations': 'annotations',
    'clear_annotations': 'annotations',
    'remove_annotations': 'annotations',
    'set_annotations': 'annotations',
    'binauthz_evaluation_mode': 'binary_authorization.evaluation_mode',
    'upgrade_control_plane': 'upgrade_policy.control_plane_only',
}

BARE_METAL_NODE_POOL_ARGS_TO_UPDATE_MASKS = {
    'node_configs_from_file': 'node_pool_config.node_configs',
    'node_configs': 'node_pool_config.node_configs',
    'node_labels': 'node_pool_config.labels',
    'node_taints': 'node_pool_config.taints',
    'display_name': 'display_name',
    'registry_pull_qps': 'node_pool_config.kubelet_config.registry_pull_qps',
    'registry_burst': 'node_pool_config.kubelet_config.registry_burst',
    'disable_serialize_image_pulls': (
        'node_pool_config.kubelet_config.serialize_image_pulls_disabled'
    ),
    'enable_serialize_image_pulls': (
        'node_pool_config.kubelet_config.serialize_image_pulls_disabled'
    ),
    'version': 'bare_metal_version',
}

BARE_METAL_ADMIN_CLUSTER_ARGS_TO_UPDATE_MASKS = {
    'version': 'bare_metal_version',
    'description': 'description',
    'control_plane_node_configs': 'control_plane.control_plane_node_pool_config.node_pool_config.node_configs',
    'control_plane_node_configs_from_file': 'control_plane.control_plane_node_pool_config.node_pool_config.node_configs',
    'control_plane_node_labels': (
        'control_plane.control_plane_node_pool_config.node_pool_config.labels'
    ),
    'control_plane_node_taints': (
        'control_plane.control_plane_node_pool_config.node_pool_config.taints'
    ),
    'api_server_args': 'control_plane.api_server_args',
    'uri': 'proxy.uri',
    'no_proxy': 'proxy.no_proxy',
    'enable_application_logs': 'cluster_operations.enable_application_logs',
    'maintenance_address_cidr_blocks': (
        'maintenance_config.maintenance_address_cidr_blocks'
    ),
    'max_pods_per_node': 'node_config.max_pods_per_node',
    'login_user': 'node_access_config.login_user',
    'island_mode_service_address_cidr_blocks': (
        'network_config.island_mode_cidr.service_address_cidr_blocks'
    ),
    'binauthz_evaluation_mode': 'binary_authorization.evaluation_mode',
}

BARE_METAL_STANDALONE_CLUSTER_ARGS_TO_UPDATE_MASKS = {
    'control_plane_node_configs_from_file': 'control_plane.control_plane_node_pool_config.node_pool_config.node_configs',
    'control_plane_node_configs': 'control_plane.control_plane_node_pool_config.node_pool_config.node_configs',
    'control_plane_node_labels': (
        'control_plane.control_plane_node_pool_config.node_pool_config.labels'
    ),
    'control_plane_node_taints': (
        'control_plane.control_plane_node_pool_config.node_pool_config.taints'
    ),
    'api_server_args': 'control_plane.api_server_args',
    'description': 'description',
    'version': 'bare_metal_version',
    'enable_application_logs': 'cluster_operations.enable_application_logs',
    'maintenance_address_cidr_blocks': (
        'maintenance_config.maintenance_address_cidr_blocks'
    ),
    'admin_users': 'security_config.authorization.admin_users',
    'login_user': 'node_access_config.login_user',
    'island_mode_service_address_cidr_blocks': (
        'network_config.island_mode_cidr.service_address_cidr_blocks'
    ),
    'enable_sr_iov_config': 'network_config.sr_iov_config.enabled',
    'disable_sr_iov_config': 'network_config.sr_iov_config.enabled',
    'metal_lb_address_pools': 'load_balancer.metal_lb_config.address_pools',
    'metal_lb_address_pools_from_file': (
        'load_balancer.metal_lb_config.address_pools'
    ),
    'metal_lb_load_balancer_node_configs_from_file': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.node_configs',
    'metal_lb_load_balancer_node_configs': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.node_configs',
    'metal_lb_load_balancer_node_labels': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.labels',
    'metal_lb_load_balancer_node_taints': 'load_balancer.metal_lb_config.load_balancer_node_pool_config.node_pool_config.taints',
    'bgp_lb_address_pools': 'load_balancer.bgp_lb_config.address_pools',
    'bgp_lb_address_pools_from_file': (
        'load_balancer.bgp_lb_config.address_pools'
    ),
    'bgp_lb_load_balancer_node_configs_from_file': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.node_configs',
    'bgp_lb_load_balancer_node_configs': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.node_configs',
    'bgp_lb_load_balancer_node_labels': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.labels',
    'bgp_lb_load_balancer_node_taints': 'load_balancer.bgp_lb_config.load_balancer_node_pool_config.node_pool_config.taints',
    'bgp_lb_peer_configs': 'load_balancer.bgp_lb_config.bgp_peer_configs',
    'bgp_lb_peer_configs_from_file': (
        'load_balancer.bgp_lb_config.bgp_peer_configs'
    ),
    'bgp_lb_asn': 'load_balancer.bgp_lb_config.asn',
    'add_annotations': 'annotations',
    'clear_annotations': 'annotations',
    'remove_annotations': 'annotations',
    'set_annotations': 'annotations',
    'binauthz_evaluation_mode': 'binary_authorization.evaluation_mode',
}

BARE_METAL_STANDALONE_NODE_POOL_ARGS_TO_UPDATE_MASKS = {
    'node_configs_from_file': 'node_pool_config.node_configs',
    'node_configs': 'node_pool_config.node_configs',
    'node_labels': 'node_pool_config.labels',
    'node_taints': 'node_pool_config.taints',
    'display_name': 'display_name',
    'registry_pull_qps': 'node_pool_config.kubelet_config.registry_pull_qps',
    'registry_burst': 'node_pool_config.kubelet_config.registry_burst',
    'disable_serialize_image_pulls': (
        'node_pool_config.kubelet_config.serialize_image_pulls_disabled'
    ),
    'enable_serialize_image_pulls': (
        'node_pool_config.kubelet_config.serialize_image_pulls_disabled'
    ),
}


def get_update_mask(args, args_to_update_masks) -> str:
  """Maps user provided arguments to API supported mutable fields in format of yaml field paths.

  Args:
    args: All arguments passed from CLI.
    args_to_update_masks: Mapping for a specific resource, such as user cluster,
      or node pool.

  Returns:
    A string that contains yaml field paths to be used in the API update
    request.
  """
  update_mask_list = []
  for arg in args_to_update_masks:
    if hasattr(args, arg) and args.IsSpecified(arg):
      update_mask_list.append(args_to_update_masks[arg])
  return ','.join(sorted(set(update_mask_list)))
