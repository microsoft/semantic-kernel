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
"""Utilities for gkeonprem API clients for Bare Metal cluster resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Optional

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


class _BareMetalClusterClient(client.ClientBase):
  """Base class for GKE OnPrem Bare Metal API clients."""

  def _create_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for create command."""
    annotations = getattr(args, 'annotations', {})

    return self._dict_to_annotations_message(annotations)

  def _add_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for adding new annotations."""
    result = {**self._get_current_annotations(args), **args.add_annotations}

    return self._dict_to_annotations_message(result)

  def _clear_annotations(self):
    """Constructs proto message AnnotationsValue for clearing annotations."""
    return messages.BareMetalCluster.AnnotationsValue()

  def _remove_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for removing annotations."""
    curr_annotations = self._get_current_annotations(args)
    updated_annotations = {
        key: value
        for key, value in curr_annotations.items()
        if key not in args.remove_annotations
    }

    return self._dict_to_annotations_message(updated_annotations)

  def _set_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for setting annotations."""
    return self._dict_to_annotations_message(args.set_annotations)

  def _get_current_annotations(self, args: parser_extensions.Namespace):
    """Fetches the standalone cluster annotations."""
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_response = self.Describe(cluster_ref)

    curr_annotations = {}
    if cluster_response.annotations:
      for annotation in cluster_response.annotations.additionalProperties:
        curr_annotations[annotation.key] = annotation.value

    return curr_annotations

  def _update_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for update command."""
    specified_args = args.GetSpecifiedArgsDict()
    if 'add_annotations' in specified_args:
      return self._add_annotations(args)

    if 'clear_annotations' in specified_args:
      return self._clear_annotations()

    if 'remove_annotations' in specified_args:
      return self._remove_annotations(args)

    if 'set_annotations' in specified_args:
      return self._set_annotations(args)

  def _dict_to_annotations_message(self, annotations):
    """Converts key-val pairs to proto message AnnotationsValue."""
    additional_property_messages = []
    if not annotations:
      return None

    for key, value in annotations.items():
      additional_property_messages.append(
          messages.BareMetalCluster.AnnotationsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    annotation_value_message = messages.BareMetalCluster.AnnotationsValue(
        additionalProperties=additional_property_messages
    )
    return annotation_value_message

  def _annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue."""
    if args.command_path[-1] == 'update':
      return self._update_annotations(args)

    if args.command_path[-1] == 'create':
      return self._create_annotations(args)

    return None

  def _island_mode_cidr_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalIslandModeCidrConfig."""
    kwargs = {
        'serviceAddressCidrBlocks': getattr(
            args, 'island_mode_service_address_cidr_blocks', []
        ),
        'podAddressCidrBlocks': getattr(
            args, 'island_mode_pod_address_cidr_blocks', []
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalIslandModeCidrConfig(**kwargs)

    return None

  def _sr_iov_config(self, args: parser_extensions.Namespace):
    kwargs = {
        'enabled': self.sr_iov_config_enabled(args),
    }

    if self.IsSet(kwargs):
      return messages.BareMetalSrIovConfig(**kwargs)

    return None

  def sr_iov_config_enabled(self, args: parser_extensions.Namespace):
    if 'enable_sr_iov_config' in args.GetSpecifiedArgsDict():
      return True
    elif 'disable_sr_iov_config' in args.GetSpecifiedArgsDict():
      return False
    else:
      return None

  def _multiple_network_interfaces_config(
      self, args: parser_extensions.Namespace
  ):
    kwargs = {
        'enabled': self.GetFlag(args, 'enable_multi_nic_config'),
    }
    if self.IsSet(kwargs):
      return messages.BareMetalMultipleNetworkInterfacesConfig(**kwargs)
    return None

  def _network_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalNetworkConfig."""
    kwargs = {
        'islandModeCidr': self._island_mode_cidr_config(args),
        'advancedNetworking': self.GetFlag(args, 'enable_advanced_networking'),
        'multipleNetworkInterfacesConfig': (
            self._multiple_network_interfaces_config(args)
        ),
        'srIovConfig': self._sr_iov_config(args),
    }

    if self.IsSet(kwargs):
      return messages.BareMetalNetworkConfig(**kwargs)

    return None

  def _vip_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalVipConfig."""
    kwargs = {
        'controlPlaneVip': getattr(args, 'control_plane_vip', None),
        'ingressVip': getattr(args, 'ingress_vip', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalVipConfig(**kwargs)

    return None

  def _port_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalPortConfig."""
    kwargs = {
        'controlPlaneLoadBalancerPort': getattr(
            args, 'control_plane_load_balancer_port', None
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalPortConfig(**kwargs)

    return None

  def _address_pools_from_file(self, args: parser_extensions.Namespace):
    """Constructs proto message field address_pools."""
    if not args.metal_lb_address_pools_from_file:
      return []

    address_pools = args.metal_lb_address_pools_from_file.get(
        'addressPools', []
    )

    if not address_pools:
      raise exceptions.BadArgumentException(
          '--metal_lb_address_pools_from_file',
          'Missing field [addressPools] in Metal LB address pools file.',
      )

    address_pool_messages = []
    for address_pool in address_pools:
      address_pool_messages.append(self._address_pool(address_pool))

    return address_pool_messages

  def _address_pool(self, address_pool):
    """Constructs proto message BareMetalLoadBalancerAddressPool."""
    addresses = address_pool.get('addresses', [])
    if not addresses:
      raise exceptions.BadArgumentException(
          '--metal_lb_address_pools_from_file',
          'Missing field [addresses] in Metal LB address pools file.',
      )

    pool = address_pool.get('pool', None)
    if not pool:
      raise exceptions.BadArgumentException(
          '--metal_lb_address_pools_from_file',
          'Missing field [pool] in Metal LB address pools file.',
      )

    kwargs = {
        'addresses': addresses,
        'avoidBuggyIps': address_pool.get('avoidBuggyIPs', None),
        'manualAssign': address_pool.get('manualAssign', None),
        'pool': pool,
    }

    return messages.BareMetalLoadBalancerAddressPool(**kwargs)

  def _address_pools_from_flag(self, args: parser_extensions.Namespace):
    if not args.metal_lb_address_pools:
      return []

    address_pools = []
    for address_pool in args.metal_lb_address_pools:
      address_pools.append(
          messages.BareMetalLoadBalancerAddressPool(
              addresses=address_pool.get('addresses', []),
              avoidBuggyIps=address_pool.get('avoid-buggy-ips', None),
              manualAssign=address_pool.get('manual-assign', None),
              pool=address_pool.get('pool', None),
          )
      )

    return address_pools

  def _metal_lb_node_config(self, metal_lb_node_config):
    """Constructs proto message BareMetalNodeConfig."""
    node_ip = metal_lb_node_config.get('nodeIP', '')
    if not node_ip:
      raise exceptions.BadArgumentException(
          '--metal_lb_load_balancer_node_configs_from_file',
          'Missing field [nodeIP] in Metal LB Node configs file.',
      )

    kwargs = {
        'nodeIp': node_ip,
        'labels': self._node_labels(metal_lb_node_config.get('labels', {})),
    }

    return messages.BareMetalNodeConfig(**kwargs)

  def _metal_lb_node_configs_from_file(self, args: parser_extensions.Namespace):
    """Constructs proto message field node_configs."""
    if not args.metal_lb_load_balancer_node_configs_from_file:
      return []

    metal_lb_node_configs = (
        args.metal_lb_load_balancer_node_configs_from_file.get(
            'nodeConfigs', []
        )
    )

    if not metal_lb_node_configs:
      raise exceptions.BadArgumentException(
          '--metal_lb_load_balancer_node_configs_from_file',
          'Missing field [nodeConfigs] in Metal LB Node configs file.',
      )

    metal_lb_node_configs_messages = []
    for metal_lb_node_config in metal_lb_node_configs:
      metal_lb_node_configs_messages.append(
          self._metal_lb_node_config(metal_lb_node_config)
      )

    return metal_lb_node_configs_messages

  def parse_node_labels(self, node_labels):
    """Validates and parses a node label object.

    Args:
      node_labels: str of key-val pairs separated by ';' delimiter.

    Returns:
      If label is valid, returns a dict mapping message LabelsValue to its
      value, otherwise, raise ArgumentTypeError.
      For example,
      {
          'key': LABEL_KEY
          'value': LABEL_VALUE
      }
    """
    if not node_labels.get('labels'):
      return None

    input_node_labels = node_labels.get('labels', '').split(';')
    additional_property_messages = []

    for label in input_node_labels:
      key_val_pair = label.split('=')
      if len(key_val_pair) != 2:
        raise arg_parsers.ArgumentTypeError(
            'Node Label [{}] not in correct format, expect KEY=VALUE.'.format(
                input_node_labels
            )
        )
      additional_property_messages.append(
          messages.BareMetalNodeConfig.LabelsValue.AdditionalProperty(
              key=key_val_pair[0], value=key_val_pair[1]
          )
      )

    labels_value_message = messages.BareMetalNodeConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def node_config(self, node_config_args):
    """Constructs proto message BareMetalNodeConfig."""
    kwargs = {
        'nodeIp': node_config_args.get('node-ip', ''),
        'labels': self.parse_node_labels(node_config_args),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodeConfig(**kwargs)

    return None

  def _metal_lb_node_configs_from_flag(self, args: parser_extensions.Namespace):
    """Constructs proto message field node_configs."""
    node_config_flag_value = (
        getattr(args, 'metal_lb_load_balancer_node_configs', [])
        if args.metal_lb_load_balancer_node_configs
        else []
    )

    return [
        self.node_config(node_config) for node_config in node_config_flag_value
    ]

  def _metal_lb_node_taints(self, args: parser_extensions.Namespace):
    """Constructs proto message NodeTaint."""
    taint_messages = []
    node_taints = getattr(args, 'metal_lb_load_balancer_node_taints', {})
    if not node_taints:
      return []

    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages.NodeTaint(**taint_object))

    return taint_messages

  def _metal_lb_labels(self, args: parser_extensions.Namespace):
    """Constructs proto message LabelsValue."""
    node_labels = getattr(args, 'metal_lb_load_balancer_node_labels', {})
    additional_property_messages = []

    if not node_labels:
      return None

    for key, value in node_labels.items():
      additional_property_messages.append(
          messages.BareMetalNodePoolConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = messages.BareMetalNodePoolConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _metal_lb_load_balancer_node_pool_config(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message BareMetalNodePoolConfig."""
    if (
        'metal_lb_load_balancer_node_configs_from_file'
        in args.GetSpecifiedArgsDict()
    ):
      metal_lb_node_configs = self._metal_lb_node_configs_from_file(args)
    else:
      metal_lb_node_configs = self._metal_lb_node_configs_from_flag(args)

    kwargs = {
        'nodeConfigs': metal_lb_node_configs,
        'labels': self._metal_lb_labels(args),
        'taints': self._metal_lb_node_taints(args),
        'kubeletConfig': self._metal_lb_kubelet_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodePoolConfig(**kwargs)
    return None

  def _metal_lb_serialize_image_pulls_disabled(
      self, args: parser_extensions.Namespace
  ):
    if (
        'enable_metal_lb_load_balancer_serialize_image_pulls'
        in args.GetSpecifiedArgsDict()
    ):
      return False
    elif (
        'disable_metal_lb_load_balancer_serialize_image_pulls'
        in args.GetSpecifiedArgsDict()
    ):
      return True
    else:
      return None

  def _metal_lb_kubelet_config(self, args: parser_extensions.Namespace):
    kwargs = {
        'registryBurst': self.GetFlag(
            args, 'metal_lb_load_balancer_registry_burst'
        ),
        'registryPullQps': self.GetFlag(
            args, 'metal_lb_load_balancer_registry_pull_qps'
        ),
        'serializeImagePullsDisabled': (
            self._metal_lb_serialize_image_pulls_disabled(args)
        ),
    }
    if self.IsSet(kwargs):
      return messages.BareMetalKubeletConfig(**kwargs)
    return None

  def _metal_lb_node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLoadBalancerNodePoolConfig."""
    kwargs = {
        'nodePoolConfig': self._metal_lb_load_balancer_node_pool_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalLoadBalancerNodePoolConfig(**kwargs)

    return None

  def _metal_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalMetalLbConfig."""
    if 'metal_lb_address_pools_from_file' in args.GetSpecifiedArgsDict():
      address_pools = self._address_pools_from_file(args)
    else:
      address_pools = self._address_pools_from_flag(args)
    kwargs = {
        'addressPools': address_pools,
        'loadBalancerNodePoolConfig': self._metal_lb_node_pool_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalMetalLbConfig(**kwargs)

    return None

  def _manual_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalManualLbConfig."""
    kwargs = {
        'enabled': getattr(args, 'enable_manual_lb', False),
    }

    if any(kwargs.values()):
      return messages.BareMetalManualLbConfig(**kwargs)

    return None

  def _load_balancer_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLoadBalancerConfig."""
    kwargs = {
        'vipConfig': self._vip_config(args),
        'portConfig': self._port_config(args),
        'metalLbConfig': self._metal_lb_config(args),
        'manualLbConfig': self._manual_lb_config(args),
        'bgpLbConfig': self._bgp_lb_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalLoadBalancerConfig(**kwargs)

    return None

  def _bgp_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalBgpLbConfig."""
    kwargs = {
        'addressPools': self._bgp_address_pools(args),
        'asn': self.GetFlag(args, 'bgp_asn'),
        'bgpPeerConfigs': self._bgp_peer_configs(args),
        'loadBalancerNodePoolConfig': self._bgp_load_balancer_node_pool_config(
            args
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalBgpLbConfig(**kwargs)
    return None

  def _bgp_address_pools(self, args: parser_extensions.Namespace):
    """Constructs repeated proto message BareMetalBgpLbConfig.BareMetalLoadBalancerAddressPool."""
    if 'bgp_address_pools' not in args.GetSpecifiedArgsDict():
      return []

    address_pools = []
    for address_pool in args.bgp_address_pools:
      address_pools.append(
          messages.BareMetalLoadBalancerAddressPool(
              addresses=address_pool.get('addresses', []),
              avoidBuggyIps=address_pool.get('avoid-buggy-ips', None),
              manualAssign=address_pool.get('manual-assign', None),
              pool=address_pool.get('pool', None),
          )
      )

    return address_pools

  def _bgp_peer_configs(self, args: parser_extensions.Namespace):
    """Constructs repeated proto message BareMetalBgpPeerConfig."""
    if 'bgp_peer_configs' not in args.GetSpecifiedArgsDict():
      return []

    ret = []
    for peer_config in self.GetFlag(args, 'bgp_peer_configs'):
      msg = messages.BareMetalBgpPeerConfig(
          asn=peer_config.get('asn', None),
          controlPlaneNodes=peer_config.get('control-plane-nodes', []),
          ipAddress=peer_config.get('ip', None),
      )
      ret.append(msg)

    return ret

  def _bgp_load_balancer_node_pool_config(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message BareMetalBgpLbConfig.BareMetalLoadBalancerNodePoolConfig."""
    kwargs = {
        'nodePoolConfig': self._bgp_node_pool_config(args),
    }
    if any(kwargs.values()):
      return messages.BareMetalLoadBalancerNodePoolConfig(**kwargs)

    return None

  def _bgp_node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalBgpLbConfig.BareMetalLoadBalancerNodePoolConfig.BareMetalNodePoolConfig."""
    kwargs = {
        'labels': self._bgp_load_balancer_node_labels(args),
        'nodeConfigs': self._bgp_load_balancer_node_configs(args),
        'taints': self._bgp_load_balancer_node_taints(args),
        'kubeletConfig': self._bgp_load_balancer_kubelet_config(args),
    }
    if any(kwargs.values()):
      return messages.BareMetalNodePoolConfig(**kwargs)
    return None

  def _bgp_serialize_image_pulls_disabled(
      self, args: parser_extensions.Namespace
  ):
    if (
        'disable_bgp_load_balancer_serialize_image_pulls'
        in args.GetSpecifiedArgsDict()
    ):
      return True
    elif (
        'enable_bgp_load_balancer_serialize_image_pulls'
        in args.GetSpecifiedArgsDict()
    ):
      return False
    else:
      return None

  def _bgp_load_balancer_kubelet_config(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message BareMetalBgpLbConfig.BareMetalLoadBalancerNodePoolConfig.BareMetalNodePoolConfig.BareMetalKubeletConfig."""
    kwargs = {
        'registryBurst': self.GetFlag(args, 'bgp_load_balancer_registry_burst'),
        'registryPullQps': self.GetFlag(
            args, 'bgp_load_balancer_registry_pull_qps'
        ),
        'serializeImagePullsDisabled': self._bgp_serialize_image_pulls_disabled(
            args
        ),
    }
    if self.IsSet(kwargs):
      return messages.BareMetalKubeletConfig(**kwargs)
    return None

  def _bgp_load_balancer_node_configs(self, args: parser_extensions.Namespace):
    """Constructs repeated proto message BareMetalBgpLbConfig.BareMetalLoadBalancerNodePoolConfig.BareMetalNodePoolConfig.BareMetalNodeConfig."""
    if 'bgp_load_balancer_node_configs' not in args.GetSpecifiedArgsDict():
      return []

    node_configs = []
    for node_config in self.GetFlag(args, 'bgp_load_balancer_node_configs'):
      node_configs.append(self.node_config(node_config))

    return node_configs

  def _bgp_load_balancer_node_labels(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalBgpLbConfig.BareMetalLoadBalancerNodePoolConfig.BareMetalNodePoolConfig.LabelsValue."""
    if 'bgp_load_balancer_node_labels' not in args.GetSpecifiedArgsDict():
      return None

    additional_property_messages = []
    for key, value in args.bgp_load_balancer_node_labels.items():
      additional_property_messages.append(
          messages.BareMetalNodePoolConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = messages.BareMetalNodePoolConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _bgp_load_balancer_node_taints(self, args: parser_extensions.Namespace):
    """Constructs repeated proto message NodeTaint."""
    if 'bgp_load_balancer_node_taints' not in args.GetSpecifiedArgsDict():
      return []

    node_taints = self.GetFlag(args, 'bgp_load_balancer_node_taints', {})
    taint_messages = []
    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages.NodeTaint(**taint_object))

    return taint_messages

  def _lvp_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLvpConfig."""
    kwargs = {
        'path': getattr(args, 'lvp_share_path', None),
        'storageClass': getattr(args, 'lvp_share_storage_class', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalLvpConfig(**kwargs)

    return None

  def _lvp_share_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLvpShareConfig."""
    kwargs = {
        'lvpConfig': self._lvp_config(args),
        'sharedPathPvCount': getattr(args, 'lvp_share_path_pv_count', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalLvpShareConfig(**kwargs)

    return None

  def _lvp_node_mounts_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalLvpConfig."""
    kwargs = {
        'path': getattr(args, 'lvp_node_mounts_config_path', None),
        'storageClass': getattr(
            args, 'lvp_node_mounts_config_storage_class', None
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalLvpConfig(**kwargs)

    return None

  def _storage_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStorageConfig."""
    kwargs = {
        'lvpShareConfig': self._lvp_share_config(args),
        'lvpNodeMountsConfig': self._lvp_node_mounts_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalStorageConfig(**kwargs)

    return None

  def _node_labels(self, labels):
    """Constructs proto message LabelsValue."""
    additional_property_messages = []
    if not labels:
      return None

    for key, value in labels.items():
      additional_property_messages.append(
          messages.BareMetalNodeConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = messages.BareMetalNodeConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _control_plane_node_config(self, control_plane_node_config):
    """Constructs proto message BareMetalNodeConfig."""
    node_ip = control_plane_node_config.get('nodeIP', '')
    if not node_ip:
      raise exceptions.BadArgumentException(
          '--control_plane_node_configs_from_file',
          'Missing field [nodeIP] in Control Plane Node configs file.',
      )

    kwargs = {
        'nodeIp': node_ip,
        'labels': self._node_labels(
            control_plane_node_config.get('labels', {})
        ),
    }

    return messages.BareMetalNodeConfig(**kwargs)

  def _control_plane_node_configs_from_file(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message field node_configs."""
    if not args.control_plane_node_configs_from_file:
      return []

    control_plane_node_configs = args.control_plane_node_configs_from_file.get(
        'nodeConfigs', []
    )

    if not control_plane_node_configs:
      raise exceptions.BadArgumentException(
          '--control_plane_node_configs_from_file',
          'Missing field [nodeConfigs] in Control Plane Node configs file.',
      )

    control_plane_node_configs_messages = []
    for control_plane_node_config in control_plane_node_configs:
      control_plane_node_configs_messages.append(
          self._control_plane_node_config(control_plane_node_config)
      )

    return control_plane_node_configs_messages

  def _control_plane_node_configs_from_flag(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message field node_configs."""
    node_configs = []
    node_config_flag_value = getattr(args, 'control_plane_node_configs', None)
    if node_config_flag_value:
      for node_config in node_config_flag_value:
        node_configs.append(self.node_config(node_config))

    return node_configs

  def _control_plane_node_taints(self, args: parser_extensions.Namespace):
    """Constructs proto message NodeTaint."""
    taint_messages = []
    node_taints = getattr(args, 'control_plane_node_taints', {})
    if not node_taints:
      return []

    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages.NodeTaint(**taint_object))

    return taint_messages

  def _control_plane_node_labels(self, args: parser_extensions.Namespace):
    """Constructs proto message LabelsValue."""
    node_labels = getattr(args, 'control_plane_node_labels', {})
    additional_property_messages = []
    if not node_labels:
      return None

    for key, value in node_labels.items():
      additional_property_messages.append(
          messages.BareMetalNodePoolConfig.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )

    labels_value_message = messages.BareMetalNodePoolConfig.LabelsValue(
        additionalProperties=additional_property_messages
    )

    return labels_value_message

  def _node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalNodePoolConfig."""
    if 'control_plane_node_configs_from_file' in args.GetSpecifiedArgsDict():
      node_configs = self._control_plane_node_configs_from_file(args)
    else:
      node_configs = self._control_plane_node_configs_from_flag(args)

    kwargs = {
        'nodeConfigs': node_configs,
        'labels': self._control_plane_node_labels(args),
        'taints': self._control_plane_node_taints(args),
        'kubeletConfig': self._control_plane_kubelet_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodePoolConfig(**kwargs)

    return None

  def _control_plane_serialize_image_pulls_disabled(
      self, args: parser_extensions.Namespace
  ):
    if (
        'disable_control_plane_serialize_image_pulls'
        in args.GetSpecifiedArgsDict()
    ):
      return True
    elif (
        'enable_control_plane_serialize_image_pulls'
        in args.GetSpecifiedArgsDict()
    ):
      return False
    else:
      return None

  def _control_plane_kubelet_config(self, args: parser_extensions.Namespace):
    kwargs = {
        'registryPullQps': self.GetFlag(
            args, 'control_plane_registry_pull_qps'
        ),
        'registryBurst': self.GetFlag(args, 'control_plane_registry_burst'),
        'serializeImagePullsDisabled': (
            self._control_plane_serialize_image_pulls_disabled(args)
        ),
    }
    if self.IsSet(kwargs):
      return messages.BareMetalKubeletConfig(**kwargs)
    return None

  def _control_plane_node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalControlPlaneNodePoolConfig."""
    kwargs = {
        'nodePoolConfig': self._node_pool_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalControlPlaneNodePoolConfig(**kwargs)

    return None

  def _api_server_args(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalApiServerArgument."""
    api_server_args = []
    api_server_args_flag_value = getattr(args, 'api_server_args', None)
    if api_server_args_flag_value:
      for key, val in api_server_args_flag_value.items():
        api_server_args.append(
            messages.BareMetalApiServerArgument(argument=key, value=val)
        )

    return api_server_args

  def _control_plane_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalControlPlaneConfig."""
    kwargs = {
        'controlPlaneNodePoolConfig': self._control_plane_node_pool_config(
            args
        ),
        'apiServerArgs': self._api_server_args(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalControlPlaneConfig(**kwargs)

    return None

  def _proxy_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalProxyConfig."""
    kwargs = {
        'uri': getattr(args, 'uri', None),
        'noProxy': getattr(args, 'no_proxy', []),
    }

    if any(kwargs.values()):
      return messages.BareMetalProxyConfig(**kwargs)

    return None

  def _cluster_operations_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalClusterOperationsConfig."""
    kwargs = {
        'enableApplicationLogs': getattr(args, 'enable_application_logs', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalClusterOperationsConfig(**kwargs)

    return None

  def _maintenance_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalMaintenanceConfig."""
    kwargs = {
        'maintenanceAddressCidrBlocks': getattr(
            args, 'maintenance_address_cidr_blocks', []
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalMaintenanceConfig(**kwargs)

    return None

  def _container_runtime(self, container_runtime):
    """Constructs proto message BareMetalWorkloadNodeConfig.ContainerRuntimeValueValuesEnum."""
    if container_runtime is None:
      return None

    container_runtime_enum = (
        messages.BareMetalWorkloadNodeConfig.ContainerRuntimeValueValuesEnum
    )
    container_runtime_mapping = {
        'ContainerRuntimeUnspecified': (
            container_runtime_enum.CONTAINER_RUNTIME_UNSPECIFIED
        ),
        'Conatinerd': container_runtime_enum.CONTAINERD,
    }

    return container_runtime_mapping[container_runtime]

  def _workload_node_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalWorkloadNodeConfig."""
    container_runtime = getattr(args, 'container_runtime', None)
    kwargs = {
        'containerRuntime': self._container_runtime(container_runtime),
        'maxPodsPerNode': getattr(args, 'max_pods_per_node', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalWorkloadNodeConfig(**kwargs)

    return None

  # TODO(b/257292798): Move to common directory
  def _cluster_users(self, args: parser_extensions.Namespace):
    """Constructs repeated proto message ClusterUser."""
    cluster_user_messages = []
    admin_users = getattr(args, 'admin_users', None)
    if admin_users:
      return [
          messages.ClusterUser(username=admin_user)
          for admin_user in admin_users
      ]

    # On update, skip setting default value.
    if args.command_path[-1] == 'update':
      return None

    # On create, client side default admin user to the current gcloud user.
    gcloud_config_core_account = properties.VALUES.core.account.Get()
    if gcloud_config_core_account:
      default_admin_user_message = messages.ClusterUser(
          username=gcloud_config_core_account
      )
      return cluster_user_messages.append(default_admin_user_message)

    return None

  def _authorization(self, args: parser_extensions.Namespace):
    """Constructs proto message Authorization."""
    kwargs = {
        'adminUsers': self._cluster_users(args),
    }

    if any(kwargs.values()):
      return messages.Authorization(**kwargs)

    return None

  def _security_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalSecurityConfig."""
    kwargs = {
        'authorization': self._authorization(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalSecurityConfig(**kwargs)

    return None

  def _node_access_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalNodeAccessConfig."""
    kwargs = {
        'loginUser': getattr(args, 'login_user', 'root'),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodeAccessConfig(**kwargs)

    return None

  def _upgrade_policy(
      self, args: parser_extensions.Namespace
  ) -> Optional[messages.BareMetalClusterUpgradePolicy]:
    """Constructs proto message BareMetalClusterUpgradePolicy."""
    kwargs = {
        'controlPlaneOnly': getattr(args, 'upgrade_control_plane', None),
    }

    if any(kwargs.values()):
      return messages.BareMetalClusterUpgradePolicy(**kwargs)

    return None

  def _bare_metal_user_cluster(self, args: parser_extensions.Namespace):
    """Constructs proto message Bare Metal Cluster."""
    kwargs = {
        'name': self._user_cluster_name(args),
        'adminClusterMembership': self._admin_cluster_membership_name(args),
        'description': getattr(args, 'description', None),
        'annotations': self._annotations(args),
        'bareMetalVersion': getattr(args, 'version', None),
        'networkConfig': self._network_config(args),
        'controlPlane': self._control_plane_config(args),
        'loadBalancer': self._load_balancer_config(args),
        'storage': self._storage_config(args),
        'proxy': self._proxy_config(args),
        'clusterOperations': self._cluster_operations_config(args),
        'maintenanceConfig': self._maintenance_config(args),
        'nodeConfig': self._workload_node_config(args),
        'securityConfig': self._security_config(args),
        'nodeAccessConfig': self._node_access_config(args),
        'binaryAuthorization': self._binary_authorization(args),
        'upgradePolicy': self._upgrade_policy(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalCluster(**kwargs)

    return None


class ClustersClient(_BareMetalClusterClient):
  """Client for clusters in gkeonprem bare metal API."""

  def __init__(self, **kwargs):
    super(ClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_bareMetalClusters

  def List(self, args: parser_extensions.Namespace):
    """Lists Clusters in the GKE On-Prem Bare Metal API."""
    # Workaround for P4SA: Call query version config first, ignore the result.
    # Context: b/296435390#comment2
    project = (
        args.project if args.project else properties.VALUES.core.project.Get()
    )
    # Hard code location to `us-west1`, because it cannot handle `--location=-`.
    parent = 'projects/{project}/locations/{location}'.format(
        project=project, location='us-west1'
    )
    dummy_request = messages.GkeonpremProjectsLocationsBareMetalClustersQueryVersionConfigRequest(
        parent=parent,
    )
    _ = self._service.QueryVersionConfig(dummy_request)

    # If location is not specified, and container_bare_metal/location is not set
    # list clusters of all locations within a project.
    if (
        'location' not in args.GetSpecifiedArgsDict()
        and not properties.VALUES.container_bare_metal.location.Get()
    ):
      args.location = '-'

    list_req = messages.GkeonpremProjectsLocationsBareMetalClustersListRequest(
        parent=self._location_name(args)
    )

    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='bareMetalClusters',
        batch_size=getattr(args, 'page_size', 100),
        limit=getattr(args, 'limit', None),
        batch_size_attribute='pageSize',
    )

  def Describe(self, resource_ref):
    """Gets a GKE On-Prem Bare Metal API cluster resource."""
    req = messages.GkeonpremProjectsLocationsBareMetalClustersGetRequest(
        name=resource_ref.RelativeName()
    )

    return self._service.Get(req)

  def Enroll(self, args: parser_extensions.Namespace):
    """Enrolls a bare metal cluster to Anthos."""
    kwargs = {
        'adminClusterMembership': self._admin_cluster_membership_name(args),
        'bareMetalClusterId': self._user_cluster_id(args),
        'localName': getattr(args, 'local_name', None),
    }
    enroll_bare_metal_cluster_request = messages.EnrollBareMetalClusterRequest(
        **kwargs
    )
    req = messages.GkeonpremProjectsLocationsBareMetalClustersEnrollRequest(
        parent=self._user_cluster_parent(args),
        enrollBareMetalClusterRequest=enroll_bare_metal_cluster_request,
    )

    return self._service.Enroll(req)

  def QueryVersionConfig(self, args: parser_extensions.Namespace):
    """Query Anthos on bare metal version configuration."""
    kwargs = {
        'createConfig_adminClusterMembership': (
            self._admin_cluster_membership_name(args)
        ),
        'upgradeConfig_clusterName': self._user_cluster_name(args),
        'parent': self._location_ref(args).RelativeName(),
    }

    # This is a workaround for the limitation in apitools with nested messages.
    encoding.AddCustomJsonFieldMapping(
        messages.GkeonpremProjectsLocationsBareMetalClustersQueryVersionConfigRequest,
        'createConfig_adminClusterMembership',
        'createConfig.adminClusterMembership',
    )
    encoding.AddCustomJsonFieldMapping(
        messages.GkeonpremProjectsLocationsBareMetalClustersQueryVersionConfigRequest,
        'upgradeConfig_clusterName',
        'upgradeConfig.clusterName',
    )

    req = messages.GkeonpremProjectsLocationsBareMetalClustersQueryVersionConfigRequest(
        **kwargs
    )
    return self._service.QueryVersionConfig(req)

  def Unenroll(self, args: parser_extensions.Namespace):
    """Unenrolls an Anthos cluster on bare metal."""
    kwargs = {
        'name': self._user_cluster_name(args),
        'force': getattr(args, 'force', None),
        'allowMissing': getattr(args, 'allow_missing', None),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersUnenrollRequest(
        **kwargs
    )

    return self._service.Unenroll(req)

  def Delete(self, args: parser_extensions.Namespace):
    """Deletes an Anthos cluster on bare metal."""
    kwargs = {
        'name': self._user_cluster_name(args),
        'allowMissing': getattr(args, 'allow_missing', False),
        'validateOnly': getattr(args, 'validate_only', False),
        'force': getattr(args, 'force', False),
        'ignoreErrors': self.GetFlag(args, 'ignore_errors'),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersDeleteRequest(
        **kwargs
    )

    return self._service.Delete(req)

  def Create(self, args: parser_extensions.Namespace):
    """Creates an Anthos cluster on bare metal."""
    kwargs = {
        'parent': self._user_cluster_parent(args),
        'validateOnly': getattr(args, 'validate_only', False),
        'bareMetalCluster': self._bare_metal_user_cluster(args),
        'bareMetalClusterId': self._user_cluster_id(args),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersCreateRequest(
        **kwargs
    )

    return self._service.Create(req)

  def Update(self, args: parser_extensions.Namespace):
    """Updates an Anthos cluster on bare metal."""
    kwargs = {
        'name': self._user_cluster_name(args),
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'updateMask': update_mask.get_update_mask(
            args, update_mask.BARE_METAL_CLUSTER_ARGS_TO_UPDATE_MASKS
        ),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'bareMetalCluster': self._bare_metal_user_cluster(args),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersPatchRequest(
        **kwargs
    )

    return self._service.Patch(req)

  def CreateFromImport(
      self,
      args: parser_extensions.Namespace,
      bare_metal_cluster,
      bare_metal_cluster_ref,
  ):
    """Creates an Anthos cluster on bare metal."""
    kwargs = {
        'parent': bare_metal_cluster_ref.Parent().RelativeName(),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'bareMetalCluster': bare_metal_cluster,
        'bareMetalClusterId': bare_metal_cluster_ref.Name(),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersCreateRequest(
        **kwargs
    )
    return self._service.Create(req)

  def UpdateFromFile(
      self, args: parser_extensions.Namespace, bare_metal_cluster
  ):
    # explicitly list supported mutable fields
    # etag is excluded from the mutable fields, because it is derived.
    top_level_mutable_fields = [
        'description',
        'bare_metal_version',
        'annotations',
        'network_config',
        'control_plane',
        'load_balancer',
        'storage',
        'proxy',
        'cluster_operations',
        'maintenance_config',
        'node_config',
        'security_config',
        'node_access_config',
        'os_environment_config',
    ]
    kwargs = {
        'name': self._user_cluster_name(args),
        'allowMissing': self.GetFlag(args, 'allow_missing'),
        'updateMask': ','.join(top_level_mutable_fields),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'bareMetalCluster': bare_metal_cluster,
    }
    req = messages.GkeonpremProjectsLocationsBareMetalClustersPatchRequest(
        **kwargs
    )
    return self._service.Patch(req)
