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
"""Utilities for gkeonprem API clients for Bare Metal Standalone cluster resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


class _BareMetalStandaloneClusterClient(client.ClientBase):
  """Base class for GKE OnPrem Bare Metal Standalone API clients."""

  def _sr_iov_config_enabled(self, args: parser_extensions.Namespace):
    if 'enable_sr_iov_config' in args.GetSpecifiedArgsDict():
      return True
    elif 'disable_sr_iov_config' in args.GetSpecifiedArgsDict():
      return False
    else:
      return None

  def _sr_iov_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneSrIovConfig."""
    kwargs = {
        'enabled': self._sr_iov_config_enabled(args),
    }

    if self.IsSet(kwargs):
      return messages.BareMetalStandaloneSrIovConfig(**kwargs)

    return None

  def _island_mode_cidr_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneIslandModeCidrConfig."""
    kwargs = {
        'serviceAddressCidrBlocks': getattr(
            args, 'island_mode_service_address_cidr_blocks', []
        ),
    }

    if any(kwargs.values()):
      return messages.BareMetalStandaloneIslandModeCidrConfig(**kwargs)

    return None

  def _network_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneNetworkConfig."""
    kwargs = {
        'islandModeCidr': self._island_mode_cidr_config(args),
        'srIovConfig': self._sr_iov_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalStandaloneNetworkConfig(**kwargs)

    return None

  def _address_pools_from_file(self, args: parser_extensions.Namespace):
    """Constructs proto message field address_pools."""
    if not args.metal_lb_address_pools_from_file:
      return []

    address_pools = args.metal_lb_address_pools_from_file.get(
        'addressPools', []
    )

    if not address_pools:
      self._raise_bad_argument_exception_error(
          '--metal_lb_address_pools_from_file',
          'addressPools',
          'Metal LB address pools file',
      )

    address_pool_messages = [
        self._metal_lb_address_pool(address_pool)
        for address_pool in address_pools
    ]

    return address_pool_messages

  def _metal_lb_address_pool(self, address_pool):
    """Constructs proto message BareMetalStandaloneLoadBalancerAddressPool."""
    addresses = address_pool.get('addresses', [])
    if not addresses:
      self._raise_bad_argument_exception_error(
          '--metal_lb_address_pools_from_file',
          'addresses',
          'Metal LB address pools file',
      )

    pool = address_pool.get('pool', None)
    if not pool:
      self._raise_bad_argument_exception_error(
          '--metal_lb_address_pools_from_file',
          'pool',
          'Metal LB address pools file',
      )

    kwargs = {
        'addresses': addresses,
        'avoidBuggyIps': address_pool.get('avoidBuggyIPs', None),
        'manualAssign': address_pool.get('manualAssign', None),
        'pool': pool,
    }

    return messages.BareMetalStandaloneLoadBalancerAddressPool(**kwargs)

  def _address_pools_from_flag(self, args: parser_extensions.Namespace):
    if not args.metal_lb_address_pools:
      return []

    address_pools = []
    for address_pool in args.metal_lb_address_pools:
      address_pools.append(
          messages.BareMetalStandaloneLoadBalancerAddressPool(
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
      self._raise_bad_argument_exception_error(
          '--metal_lb_load_balancer_node_configs_from_file',
          'nodeIp',
          'Metal LB Node configs file',
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
      self._raise_bad_argument_exception_error(
          '--metal_lb_load_balancer_node_configs_from_file',
          'nodeConfigs',
          'Metal LB Node configs file',
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

    return self._set_config_if_exists(messages.BareMetalNodeConfig, kwargs)

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
    }

    if any(kwargs.values()):
      return messages.BareMetalNodePoolConfig(**kwargs)

    return None

  def _metal_lb_node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneLoadBalancerNodePoolConfig."""
    kwargs = {
        'nodePoolConfig': self._metal_lb_load_balancer_node_pool_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalStandaloneLoadBalancerNodePoolConfig(**kwargs)

    return None

  def _metal_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneMetalLbConfig."""
    if 'metal_lb_address_pools_from_file' in args.GetSpecifiedArgsDict():
      address_pools = self._address_pools_from_file(args)
    else:
      address_pools = self._address_pools_from_flag(args)
    kwargs = {
        'addressPools': address_pools,
        'loadBalancerNodePoolConfig': self._metal_lb_node_pool_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalStandaloneMetalLbConfig(**kwargs)

    return None

  def _bgp_address_pools_from_file(self, args: parser_extensions.Namespace):
    """Constructs proto message field address_pools."""
    if not args.bgp_lb_address_pools_from_file:
      return []

    address_pools = args.bgp_lb_address_pools_from_file.get(
        'addressPools', []
    )

    if not address_pools:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_address_pools_from_file',
          'addressPools',
          'BGP LB address pools file',
      )

    address_pool_messages = []
    for address_pool in address_pools:
      address_pool_messages.append(self._bgp_lb_address_pool(address_pool))

    return address_pool_messages

  def _bgp_lb_address_pool(self, address_pool):
    """Constructs proto message BareMetalStandaloneLoadBalancerAddressPool."""
    addresses = address_pool.get('addresses', [])
    if not addresses:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_address_pools_from_file',
          'addresses',
          'BGP LB address pools file',
      )

    pool = address_pool.get('pool', None)
    if not pool:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_address_pools_from_file',
          'pool',
          'BGP LB address pools file',
      )

    kwargs = {
        'addresses': addresses,
        'avoidBuggyIps': address_pool.get('avoidBuggyIPs', None),
        'manualAssign': address_pool.get('manualAssign', None),
        'pool': pool,
    }

    return messages.BareMetalStandaloneLoadBalancerAddressPool(**kwargs)

  def _bgp_address_pools_from_flag(self, args: parser_extensions.Namespace):
    if not args.bgp_lb_address_pools:
      return []

    address_pools = []
    for address_pool in args.bgp_lb_address_pools:
      address_pools.append(
          messages.BareMetalStandaloneLoadBalancerAddressPool(
              addresses=address_pool.get('addresses', []),
              avoidBuggyIps=address_pool.get('avoid-buggy-ips', None),
              manualAssign=address_pool.get('manual-assign', None),
              pool=address_pool.get('pool', None),
          )
      )

    return address_pools

  def _bgp_lb_node_config(self, bgp_lb_node_config):
    """Constructs proto message BareMetalNodeConfig."""
    node_ip = bgp_lb_node_config.get('nodeIP', '')
    if not node_ip:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_load_balancer_node_configs_from_file',
          'nodeIP',
          'BGP LB Node configs file',
      )

    kwargs = {
        'nodeIp': node_ip,
        'labels': self._node_labels(bgp_lb_node_config.get('labels', {})),
    }

    return messages.BareMetalNodeConfig(**kwargs)

  def _bgp_lb_node_configs_from_file(self, args: parser_extensions.Namespace):
    """Constructs proto message field node_configs."""
    if not args.bgp_lb_load_balancer_node_configs_from_file:
      return []

    bgp_lb_node_configs = (
        args.bgp_lb_load_balancer_node_configs_from_file.get(
            'nodeConfigs', []
        )
    )

    if not bgp_lb_node_configs:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_load_balancer_node_configs_from_file',
          'nodeConfigs',
          'BGP LB Node configs file',
      )

    bgp_lb_node_configs_messages = []
    for bgp_lb_node_config in bgp_lb_node_configs:
      bgp_lb_node_configs_messages.append(
          self._bgp_lb_node_config(bgp_lb_node_config)
      )

    return bgp_lb_node_configs_messages

  def _bgp_lb_node_configs_from_flag(self, args: parser_extensions.Namespace):
    """Constructs proto message field node_configs."""
    node_config_flag_value = (
        getattr(args, 'bgp_lb_load_balancer_node_configs', [])
        if args.bgp_lb_load_balancer_node_configs
        else []
    )

    return [
        self.node_config(node_config) for node_config in node_config_flag_value
    ]

  def _bgp_lb_node_taints(self, args: parser_extensions.Namespace):
    """Constructs proto message NodeTaint."""
    taint_messages = []
    node_taints = getattr(args, 'bgp_lb_load_balancer_node_taints', {})
    if not node_taints:
      return []

    for node_taint in node_taints.items():
      taint_object = self._parse_node_taint(node_taint)
      taint_messages.append(messages.NodeTaint(**taint_object))

    return taint_messages

  def _bgp_lb_labels(self, args: parser_extensions.Namespace):
    """Constructs proto message LabelsValue."""
    node_labels = getattr(args, 'bgp_lb_load_balancer_node_labels', {})
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

  def _bgp_lb_load_balancer_node_pool_config(
      self, args: parser_extensions.Namespace
  ):
    """Constructs proto message BareMetalNodePoolConfig."""
    if (
        'bgp_lb_load_balancer_node_configs_from_file'
        in args.GetSpecifiedArgsDict()
    ):
      bgp_lb_node_configs = self._bgp_lb_node_configs_from_file(args)
    else:
      bgp_lb_node_configs = self._bgp_lb_node_configs_from_flag(args)

    kwargs = {
        'nodeConfigs': bgp_lb_node_configs,
        'labels': self._bgp_lb_labels(args),
        'taints': self._bgp_lb_node_taints(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalNodePoolConfig(**kwargs)

    return None

  def _bgp_lb_node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneLoadBalancerNodePoolConfig."""
    kwargs = {
        'nodePoolConfig': self._bgp_lb_load_balancer_node_pool_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalStandaloneLoadBalancerNodePoolConfig(**kwargs)

    return None

  def _bgp_peer_configs_from_file(self, args: parser_extensions.Namespace):
    """Constructs proto message field address_pools."""
    if not args.bgp_lb_peer_configs_from_file:
      return []

    peer_configs = args.bgp_lb_peer_configs_from_file.get('bgpPeerConfigs', [])

    if not peer_configs:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_peer_configs_from_file',
          'bgpPeerConfigs',
          'BGP LB peer configs file',
      )

    peer_configs_messages = []
    for peer_config in peer_configs:
      peer_configs_messages.append(self._peer_configs(peer_config))

    return peer_configs_messages

  def _peer_configs(self, peer_config):
    """Constructs proto message BareMetalStandaloneBgpPeerConfig."""
    asn = peer_config.get('asn', None)
    if not asn:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_peer_configs_from_file',
          'asn',
          'BGP LB peer configs file',
      )

    ip_address = peer_config.get('ipAddress', None)
    if not ip_address:
      self._raise_bad_argument_exception_error(
          '--bgp_lb_peer_configs_from_file',
          'ipAddress',
          'BGP LB peer configs file',
      )

    kwargs = {
        'asn': asn,
        'ipAddress': ip_address,
        'controlPlaneNodes': peer_config.get('controlPlaneNodes', []),
    }

    return messages.BareMetalStandaloneBgpPeerConfig(**kwargs)

  def _bgp_peer_configs_from_flag(self, args: parser_extensions.Namespace):
    if not args.bgp_lb_peer_configs:
      return []

    peer_configs = []
    for peer_config in args.bgp_lb_peer_configs:
      peer_configs.append(
          messages.BareMetalStandaloneBgpPeerConfig(
              controlPlaneNodes=peer_config.get('control-plane-nodes', []),
              asn=peer_config.get('asn', None),
              ipAddress=peer_config.get('ip-address', None),
          )
      )

    return peer_configs

  def _bgp_lb_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneBgpLbConfig."""
    if 'bgp_lb_address_pools_from_file' in args.GetSpecifiedArgsDict():
      address_pools = self._bgp_address_pools_from_file(args)
    else:
      address_pools = self._bgp_address_pools_from_flag(args)

    if 'bgp_lb_peer_configs_from_file' in args.GetSpecifiedArgsDict():
      peer_configs = self._bgp_peer_configs_from_file(args)
    else:
      peer_configs = self._bgp_peer_configs_from_flag(args)

    kwargs = {
        'addressPools': address_pools,
        'asn': getattr(args, 'bgp_lb_asn', None),
        'loadBalancerNodePoolConfig': self._bgp_lb_node_pool_config(args),
        'bgpPeerConfigs': peer_configs,
    }

    if any(kwargs.values()):
      return messages.BareMetalStandaloneBgpLbConfig(**kwargs)

    return None

  def _load_balancer_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneLoadBalancerConfig."""
    kwargs = {
        'metalLbConfig': self._metal_lb_config(args),
        'bgpLbConfig': self._bgp_lb_config(args),
    }

    if any(kwargs.values()):
      return messages.BareMetalStandaloneLoadBalancerConfig(**kwargs)

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
      self._raise_bad_argument_exception_error(
          '--control_plane_node_configs_from_file',
          'nodeIP',
          'Control Plane Node configs file',
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
      self._raise_bad_argument_exception_error(
          '--control_plane_node_configs_from_file',
          'nodeConfigs',
          'Control Plane Node configs file',
      )

    control_plane_node_configs_messages = []
    for control_plane_node_config in control_plane_node_configs:
      control_plane_node_configs_messages.append(
          self._control_plane_node_config(control_plane_node_config)
      )

    return control_plane_node_configs_messages

  def _raise_bad_argument_exception_error(self, flag, field, file):
    raise exceptions.BadArgumentException(
        flag, 'Missing field [' + field + '] in ' + file
    )

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
    }

    return self._set_config_if_exists(messages.BareMetalNodePoolConfig, kwargs)

  def _control_plane_node_pool_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneControlPlaneNodePoolConfig."""
    kwargs = {
        'nodePoolConfig': self._node_pool_config(args),
    }

    return self._set_config_if_exists(
        messages.BareMetalStandaloneControlPlaneNodePoolConfig, kwargs
    )

  def _api_server_args(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneApiServerArgument."""
    api_server_args = []
    api_server_args_flag_value = getattr(args, 'api_server_args', None)
    if api_server_args_flag_value:
      for key, val in api_server_args_flag_value.items():
        api_server_args.append(
            messages.BareMetalStandaloneApiServerArgument(
                argument=key, value=val
            )
        )

    return api_server_args

  def _control_plane_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneControlPlaneConfig."""
    kwargs = {
        'controlPlaneNodePoolConfig': self._control_plane_node_pool_config(
            args
        ),
        'apiServerArgs': self._api_server_args(args),
    }

    return self._set_config_if_exists(
        messages.BareMetalStandaloneControlPlaneConfig, kwargs
    )

  def _cluster_operations_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneClusterOperationsConfig."""
    kwargs = {
        'enableApplicationLogs': getattr(args, 'enable_application_logs', None),
    }

    return self._set_config_if_exists(
        messages.BareMetalStandaloneClusterOperationsConfig, kwargs
    )

  def _maintenance_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneMaintenanceConfig."""
    kwargs = {
        'maintenanceAddressCidrBlocks': getattr(
            args, 'maintenance_address_cidr_blocks', []
        ),
    }

    return self._set_config_if_exists(
        messages.BareMetalStandaloneMaintenanceConfig, kwargs
    )

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

    return self._set_config_if_exists(messages.Authorization, kwargs)

  def _security_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneSecurityConfig."""
    kwargs = {
        'authorization': self._authorization(args),
    }

    return self._set_config_if_exists(
        messages.BareMetalStandaloneSecurityConfig, kwargs
    )

  def _node_access_config(self, args: parser_extensions.Namespace):
    """Constructs proto message BareMetalStandaloneNodeAccessConfig."""
    kwargs = {
        'loginUser': getattr(args, 'login_user', 'root'),
    }

    return self._set_config_if_exists(
        messages.BareMetalStandaloneNodeAccessConfig, kwargs
    )

  def _add_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for adding new annotations."""
    curr_annotations = self._get_current_annotations(args)
    for key, value in args.add_annotations.items():
      curr_annotations[key] = value

    return self._dict_to_annotations_message(curr_annotations)

  def _clear_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for clearing annotations."""
    return messages.BareMetalStandaloneCluster.AnnotationsValue()

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
    cluster_ref = args.CONCEPTS.standalone_cluster.Parse()
    cluster_response = self.Describe(cluster_ref)

    curr_annotations = {}
    if cluster_response.annotations:
      for annotation in cluster_response.annotations.additionalProperties:
        curr_annotations[annotation.key] = annotation.value

    return curr_annotations

  def _update_annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue for update command."""
    if 'add_annotations' in args.GetSpecifiedArgsDict():
      return self._add_annotations(args)

    if 'clear_annotations' in args.GetSpecifiedArgsDict():
      return self._clear_annotations(args)

    if 'remove_annotations' in args.GetSpecifiedArgsDict():
      return self._remove_annotations(args)

    if 'set_annotations' in args.GetSpecifiedArgsDict():
      return self._set_annotations(args)

    return None

  def _dict_to_annotations_message(self, annotations):
    """Converts key-val pairs to proto message AnnotationsValue."""
    additional_property_messages = []
    if not annotations:
      return None

    for key, value in annotations.items():
      additional_property_messages.append(
          (
              messages.BareMetalStandaloneCluster.AnnotationsValue.AdditionalProperty
          )(key=key, value=value)
      )

    annotation_value_message = (
        messages.BareMetalStandaloneCluster.AnnotationsValue(
            additionalProperties=additional_property_messages
        )
    )
    return annotation_value_message

  def _annotations(self, args: parser_extensions.Namespace):
    """Constructs proto message AnnotationsValue."""
    if args.command_path[-1] == 'update':
      return self._update_annotations(args)

    return None

  def _bare_metal_standalone_cluster(self, args: parser_extensions.Namespace):
    """Constructs proto message Bare Metal Standalone Cluster."""
    kwargs = {
        'name': self._standalone_cluster_name(args),
        'description': getattr(args, 'description', None),
        'bareMetalVersion': getattr(args, 'version', None),
        'networkConfig': self._network_config(args),
        'loadBalancer': self._load_balancer_config(args),
        'controlPlane': self._control_plane_config(args),
        'clusterOperations': self._cluster_operations_config(args),
        'maintenanceConfig': self._maintenance_config(args),
        'securityConfig': self._security_config(args),
        'nodeAccessConfig': self._node_access_config(args),
        'annotations': self._annotations(args),
        'binaryAuthorization': self._binary_authorization(args),
    }

    return self._set_config_if_exists(
        messages.BareMetalStandaloneCluster, kwargs
    )

  def _set_config_if_exists(self, config_type, kwargs):
    if any(kwargs.values()):
      return config_type(**kwargs)
    else:
      return None


class StandaloneClustersClient(_BareMetalStandaloneClusterClient):
  """Client for clusters in gkeonprem bare metal standalone API."""

  def __init__(self, **kwargs):
    super(StandaloneClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_bareMetalStandaloneClusters

  def List(self, location_ref, limit=None, page_size=None):
    """Lists Clusters in the GKE On-Prem Bare Metal Standalone API."""
    list_req = messages.GkeonpremProjectsLocationsBareMetalStandaloneClustersListRequest(
        parent=location_ref.RelativeName()
    )

    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='bareMetalStandaloneClusters',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize')

  def Describe(self, resource_ref):
    """Gets a GKE On-Prem Bare Metal Standalone API cluster resource."""
    req = messages.GkeonpremProjectsLocationsBareMetalStandaloneClustersGetRequest(
        name=resource_ref.RelativeName()
    )

    return self._service.Get(req)

  def Enroll(self, args: parser_extensions.Namespace):
    """Enrolls an existing bare metal standalone cluster to the GKE on-prem API within a given project and location."""
    kwargs = {
        'membership': self._standalone_cluster_membership_name(args),
        'bareMetalStandaloneClusterId': self._standalone_cluster_id(args),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalStandaloneClustersEnrollRequest(
        parent=self._standalone_cluster_parent(args),
        enrollBareMetalStandaloneClusterRequest=messages.EnrollBareMetalStandaloneClusterRequest(
            **kwargs
        ),
    )

    return self._service.Enroll(req)

  def Unenroll(self, args: parser_extensions.Namespace):
    """Unenrolls an Anthos on bare metal standalone cluster."""
    kwargs = {
        'name': self._standalone_cluster_name(args),
        'allowMissing': getattr(args, 'allow_missing', None),
        'ignoreErrors': getattr(args, 'ignore_errors', None),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalStandaloneClustersUnenrollRequest(
        **kwargs
    )

    return self._service.Unenroll(req)

  def QueryVersionConfig(self, args: parser_extensions.Namespace):
    """Query Anthos on bare metal standalone cluster version configuration."""
    kwargs = {
        'upgradeConfig_clusterName': self._standalone_cluster_name(args),
        'parent': self._location_ref(args).RelativeName(),
    }

    # This is a workaround for the limitation in apitools with nested messages.
    encoding.AddCustomJsonFieldMapping(
        messages.GkeonpremProjectsLocationsBareMetalStandaloneClustersQueryVersionConfigRequest,
        'upgradeConfig_clusterName',
        'upgradeConfig.clusterName',
    )

    req = messages.GkeonpremProjectsLocationsBareMetalStandaloneClustersQueryVersionConfigRequest(
        **kwargs
    )
    return self._service.QueryVersionConfig(req)

  def Update(self, args: parser_extensions.Namespace):
    """Updates an Anthos on bare metal standalone cluster."""
    kwargs = {
        'name': self._standalone_cluster_name(args),
        'allowMissing': getattr(args, 'allow_missing', None),
        'updateMask': update_mask.get_update_mask(
            args, update_mask.BARE_METAL_STANDALONE_CLUSTER_ARGS_TO_UPDATE_MASKS
        ),
        'validateOnly': getattr(args, 'validate_only', False),
        'bareMetalStandaloneCluster': self._bare_metal_standalone_cluster(args),
    }
    req = messages.GkeonpremProjectsLocationsBareMetalStandaloneClustersPatchRequest(
        **kwargs
    )

    return self._service.Patch(req)
