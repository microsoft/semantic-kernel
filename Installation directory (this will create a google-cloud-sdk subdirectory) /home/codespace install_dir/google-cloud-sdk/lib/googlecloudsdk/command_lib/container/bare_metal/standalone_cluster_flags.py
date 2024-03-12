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
"""Helpers for flags in commands for Anthos standalone clusters on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.container.bare_metal import cluster_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def StandaloneClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='standalone_cluster',
      help_text='cluster of the {resource}.',
  )


def GetStandaloneClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.bareMetalStandaloneClusters',
      resource_name='standalone_cluster',
      bareMetalStandaloneClustersId=StandaloneClusterAttributeConfig(),
      locationsId=cluster_flags.LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddStandaloneClusterResourceArg(
    parser, verb, positional=True, required=True, flag_name_overrides=None
):
  """Adds a resource argument for an Anthos on bare metal standalone cluster.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
    flag_name_overrides: {str: str}, dict of attribute names to the desired flag
      name.
  """
  name = 'standalone_cluster' if positional else '--cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetStandaloneClusterResourceSpec(),
      'standalone cluster {}'.format(verb),
      required=required,
      flag_name_overrides=flag_name_overrides,
  ).AddToParser(parser)


def StandaloneClusterMembershipIdAttributeConfig():
  """Gets standalone cluster membership ID resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='membership',
      help_text=(
          ' membership of the {resource}, in the form of'
          ' projects/PROJECT/locations/LOCATION/memberships/MEMBERSHIP. '
      ),
  )


def StandaloneClusterMembershipLocationAttributeConfig():
  """Gets standalone cluster membership location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
  )


def StandaloneClusterMembershipProjectAttributeConfig():
  """Gets Google Cloud project resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text='Google Cloud project for the {resource}.',
  )


def GetStandaloneClusterMembershipResourceSpec():
  return concepts.ResourceSpec(
      'gkehub.projects.locations.memberships',
      resource_name='membership',
      membershipsId=StandaloneClusterMembershipIdAttributeConfig(),
      locationsId=StandaloneClusterMembershipLocationAttributeConfig(),
      projectsId=StandaloneClusterMembershipProjectAttributeConfig(),
  )


def AddStandaloneClusterMembershipResourceArg(parser, **kwargs):
  """Adds a resource argument for a bare metal standalone cluster membership.

  Args:
    parser: The argparse parser to add the resource arg to.
    **kwargs: Additional arguments like positional, required, etc.
  """
  positional = kwargs.get('positional')
  required = kwargs.get('required')
  name = 'membership' if positional else '--membership'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetStandaloneClusterMembershipResourceSpec(),
      (
          'membership of the standalone cluster. Membership can be the'
          ' membership ID or the full resource name.'
      ),
      required=required,
      flag_name_overrides={
          'project': '--membership-project',
          'location': '--membership-location',
      },
  ).AddToParser(parser)


def AddForceStandaloneCluster(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for force standalone cluster operation when there are existing node pools.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--force',
      action='store_true',
      help=(
          'If set, the operation will also apply to the child node pools. This'
          ' flag is required if the cluster has any associated node pools.'
      ),
  )


def AddAllowMissingStandaloneCluster(
    parser: parser_arguments.ArgumentInterceptor,
):
  """Adds a flag for the standalone cluster operation to return success and perform no action when there is no matching standalone cluster.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the Bare Metal standalone cluster is not found, the'
          ' request will succeed but no action will be taken.'
      ),
  )


def AddStandaloneConfigType(parser: parser_arguments.ArgumentInterceptor):
  """Adds flags to specify standalone cluster version config type.

  Args:
    parser: The argparse parser to add the flag to.
  """
  config_type_group = parser.add_group(
      'Use cases for querying versions.', mutex=True
  )
  upgrade_config = config_type_group.add_group(
      'Upgrade an Anthos on bare metal standalone cluster use case.'
  )
  arg_parser = concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              '--standalone-cluster',
              GetStandaloneClusterResourceSpec(),
              'Standalone cluster to query versions for upgrade.',
              flag_name_overrides={'location': ''},
              required=False,
              group=upgrade_config,
          ),
      ],
      command_level_fallthroughs={
          '--standalone-cluster.location': ['--location'],
      },
  )
  arg_parser.AddToParser(parser)


def AddAllowMissingUpdateStandaloneCluster(
    parser: parser_arguments.ArgumentInterceptor,
):
  """Adds a flag to enable allow missing in an update cluster request.

  If set to true, and the standalone cluster is not found, the request will
  create a new standalone cluster with the provided configuration. The user
  must have both create and update permission to call Update with
  allow_missing set to true.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the Anthos standalone cluster on bare metal is not'
          ' found, the update request will try to create a new standalone'
          ' cluster with the provided configuration.'
      ),
  )


def AddValidationOnly(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag to only validate the request without performing the operation.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--validate-only',
      action='store_true',
      help=(
          'If set, only validate the request, but do not actually perform the'
          ' operation.'
      ),
  )


def AddVersion(parser: parser_arguments.ArgumentInterceptor, is_update=False):
  """Adds a flag to specify the Anthos on bare metal standalone cluster version.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  parser.add_argument(
      '--version',
      required=required,
      help='Anthos on bare metal version for the standalone cluster resource.',
  )


def _AddControlPlaneNodeConfigs(bare_metal_node_config_group, is_update=False):
  """Adds flags to set the control plane node config.

  Args:
    bare_metal_node_config_group: The parent mutex group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  node_config_mutex_group = bare_metal_node_config_group.add_group(
      help='Populate control plane node config.', required=required, mutex=True
  )
  control_plane_node_configs_from_file_help_text = """
Path of the YAML/JSON file that contains the control plane node configs.

Examples:

  nodeConfigs:
  - nodeIP: 10.200.0.10
    labels:
      node1: label1
      node2: label2
  - nodeIP: 10.200.0.11
    labels:
      node3: label3
      node4: label4

List of supported fields in `nodeConfigs`

KEY           | VALUE                     | NOTE
--------------|---------------------------|---------------------------
nodeIP        | string                    | required, mutable
labels        | one or more key-val pairs | optional, mutable

"""
  node_config_mutex_group.add_argument(
      '--control-plane-node-configs-from-file',
      help=control_plane_node_configs_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )
  node_config_mutex_group.add_argument(
      '--control-plane-node-configs',
      help='Control plane node configuration.',
      action='append',
      type=arg_parsers.ArgDict(
          spec={
              'node-ip': str,
              'labels': str,
          },
          required_keys=['node-ip'],
      ),
  )


def _AddControlPlaneNodeLabels(bare_metal_node_config_group):
  """Adds a flag to assign labels to nodes in a node pool.

  Args:
    bare_metal_node_config_group: The parent group to add the flags to.
  """
  bare_metal_node_config_group.add_argument(
      '--control-plane-node-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Labels assigned to nodes of a node pool.',
  )


def _AddControlPlaneNodeTaints(bare_metal_node_config_group):
  """Adds a flag to specify the node taint in the node pool.

  Args:
    bare_metal_node_config_group: The parent group to add the flags to.
  """
  bare_metal_node_config_group.add_argument(
      '--control-plane-node-taints',
      metavar='KEY=VALUE:EFFECT',
      help='Node taint applied to every Kubernetes node in a node pool.',
      type=arg_parsers.ArgDict(),
  )


def _AddNodePoolConfig(
    bare_metal_control_plane_node_pool_config_group, is_update=False
):
  """Adds a command group to set the node pool config.

  Args:
    bare_metal_control_plane_node_pool_config_group: The argparse parser to add
      the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_node_pool_config_group = bare_metal_control_plane_node_pool_config_group.add_group(
      help=(
          'Anthos on bare metal node pool configuration for control plane'
          ' nodes.'
      ),
      required=required,
  )
  bare_metal_node_config_group = bare_metal_node_pool_config_group.add_group(
      help='Anthos on bare metal node configuration for control plane nodes.',
      required=required,
  )

  _AddControlPlaneNodeConfigs(bare_metal_node_config_group, is_update)
  _AddControlPlaneNodeLabels(bare_metal_node_config_group)
  _AddControlPlaneNodeTaints(bare_metal_node_config_group)


def _AddControlPlaneNodePoolConfig(
    bare_metal_control_plane_config_group, is_update=False
):
  """Adds a command group to set the control plane node pool config.

  Args:
    bare_metal_control_plane_config_group: The argparse parser to add the flag
      to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_control_plane_node_pool_config_group = bare_metal_control_plane_config_group.add_group(
      help=(
          'Anthos on bare metal standalone cluster control plane node pool'
          ' configuration.'
      ),
      required=required,
  )
  _AddNodePoolConfig(bare_metal_control_plane_node_pool_config_group, is_update)


def _AddControlPlaneAPIServerArgs(bare_metal_control_plane_config_group):
  """Adds a flag to specify the API server args.

  Args:
    bare_metal_control_plane_config_group: The parent group to add the flags to.
  """
  bare_metal_control_plane_config_group.add_argument(
      '--api-server-args',
      metavar='KEY=VALUE',
      help='API Server argument configuration.',
      type=arg_parsers.ArgDict(),
  )


def AddControlPlaneConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds a command group to set the control plane config.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_control_plane_config_group = parser.add_group(
      help=(
          'Anthos on bare metal standalone cluster control plane configuration.'
      ),
      required=required,
  )
  _AddControlPlaneNodePoolConfig(
      bare_metal_control_plane_config_group, is_update
  )
  _AddControlPlaneAPIServerArgs(bare_metal_control_plane_config_group)


def AddDescription(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag to specify the description of the resource.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--description', type=str, help='Description for the resource.'
  )


def AddClusterOperationsConfig(parser: parser_arguments.ArgumentInterceptor):
  """Adds a command group to set the cluster operations config.

  Args:
    parser: The argparse parser to add the flag to.
  """
  bare_metal_cluster_operations_config_group = parser.add_group(
      help='Anthos on bare metal standalone cluster operations configuration.',
  )

  bare_metal_cluster_operations_config_group.add_argument(
      '--enable-application-logs',
      action='store_true',
      help=(
          'Whether collection of application logs/metrics should be enabled (in'
          ' addition to system logs/metrics).'
      ),
  )


def AddMaintenanceConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds a command group to set the maintenance config.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_maintenance_config_group = parser.add_group(
      help='Anthos on bare metal standalone cluster maintenance configuration.',
  )

  bare_metal_maintenance_config_group.add_argument(
      '--maintenance-address-cidr-blocks',
      type=arg_parsers.ArgList(),
      metavar='MAINTENANCE_ADDRESS_CIDR_BLOCKS',
      help='IPv4 addresses to be placed into maintenance mode.',
      required=required,
  )


def _AddAuthorization(bare_metal_security_config_group, is_update=False):
  """Adds flags to specify applied and managed RBAC policy.

  Args:
    bare_metal_security_config_group: The parent group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  authorization_group = bare_metal_security_config_group.add_group(
      help=(
          'Cluster authorization configurations to bootstrap onto the'
          ' standalone cluster'
      )
  )
  authorization_group.add_argument(
      '--admin-users',
      help=(
          'Users that will be granted the cluster-admin role on the cluster,'
          ' providing full access to the cluster.'
      ),
      action='append',
      required=required,
  )


def AddSecurityConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds a command group to set the security config.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  bare_metal_security_config_group = parser.add_group(
      help='Anthos on bare metal standalone cluster security configuration.',
  )

  _AddAuthorization(bare_metal_security_config_group, is_update)


def AddNodeAccessConfig(parser: parser_arguments.ArgumentInterceptor):
  """Adds a command group to set the node access config.

  Args:
    parser: The argparse parser to add the flag to.
  """
  bare_metal_node_access_config_group = parser.add_group(
      help=(
          'Anthos on bare metal node access related settings for the standalone'
          ' cluster.'
      ),
  )

  bare_metal_node_access_config_group.add_argument(
      '--login-user',
      type=str,
      help='User name used to access node machines.',
  )


def _AddEnableSrIovConfig(sr_iov_config_group, is_update=False):
  """Adds a flag to specify the enablement of SR-IOV Config.

  Args:
    sr_iov_config_group: The parent group to add the flags to.
    is_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = not is_update
  sr_iov_config_mutex_group = sr_iov_config_group.add_group(
      mutex=True, required=required
  )

  sr_iov_config_mutex_group.add_argument(
      '--enable-sr-iov-config',
      action='store_true',
      help='If set, install the SR-IOV operator.',
  )

  sr_iov_config_mutex_group.add_argument(
      '--disable-sr-iov-config',
      action='store_true',
      help="If set, the SR-IOV operator won't be installed.",
  )


def _AddSrIovConfig(bare_metal_network_config_group, is_update=False):
  """Adds a flag to specify the SR-IOV Config.

  Args:
    bare_metal_network_config_group: The parent group to add the flags to.
    is_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = not is_update
  sr_iov_config_group = bare_metal_network_config_group.add_group(
      help='Anthos on bare metal standalone cluster SR-IOV configuration.',
      required=required,
  )

  _AddEnableSrIovConfig(sr_iov_config_group, is_update)


def _AddServiceAddressCIDRBlocks(
    bare_metal_island_mode_cidr_config_group, is_update=False
):
  """Adds a flag to specify the IPv4 address ranges used in the services in the cluster.

  Args:
    bare_metal_island_mode_cidr_config_group: The parent group to add the flag
      to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_island_mode_cidr_config_group.add_argument(
      '--island-mode-service-address-cidr-blocks',
      metavar='SERVICE_ADDRESS',
      required=required,
      type=arg_parsers.ArgList(
          min_length=1,
      ),
      help='IPv4 address range for all services in the cluster.',
  )


def _AddIslandModeCIDRConfig(bare_metal_network_config_group, is_update=False):
  """Adds island mode CIDR config related flags.

  Args:
    bare_metal_network_config_group: The parent group to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  bare_metal_island_mode_cidr_config_group = (
      bare_metal_network_config_group.add_group(
          help='Island mode CIDR network configuration.',
      )
  )
  _AddServiceAddressCIDRBlocks(
      bare_metal_island_mode_cidr_config_group, is_update
  )


def _AddNetworkModeConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds network mode config related flags.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  network_config_mutex_group = parser.add_group(
      mutex=True,
      required=required,
      help='Populate one of the network configs.',
  )

  _AddIslandModeCIDRConfig(network_config_mutex_group, is_update)


def AddNetworkConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds network config related flags.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_network_config_group = parser.add_group(
      help='Anthos on bare metal standalone cluster network configuration.',
      required=required,
  )

  _AddNetworkModeConfig(bare_metal_network_config_group, is_update)
  _AddSrIovConfig(bare_metal_network_config_group, is_update)


def _AddBGPLBAsn(bgp_lb_config_group, is_update=False):
  """Adds flags for ASN used by BGP LB load balancer of the cluster.

  Args:
   bgp_lb_config_group: The parent group to add the flags to.
   is_update: bool, whether the flag is for update command or not.
  """
  bgp_lb_config_group.add_argument(
      '--bgp-lb-asn',
      required=not is_update,
      help='BGP autonomous system number (ASN) of the cluster.',
      type=int,
  )


def _AddBGPLBPeerConfigs(bgp_lb_config_group, is_update=False):
  """Adds flags for peer configs used by BGP LB load balancer.

  Args:
    bgp_lb_config_group: The parent group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bgp_lb_peer_configs_mutex_group = bgp_lb_config_group.add_group(
      help='BGP LB peer configuration.',
      mutex=True,
      required=required,
  )
  bgp_lb_peer_configs_from_file_help_text = """
Path of the YAML/JSON file that contains the BGP LB peer configs.

Examples:

  bgpPeerConfigs:
  - asn: 1000
    controlPlaneNodes:
    - 10.200.0.14/32
    - 10.200.0.15/32
    ipAddress: 10.200.0.16/32
  - asn: 1001
    controlPlaneNodes:
    - 10.200.0.17/32
    - 10.200.0.18/32
    ipAddress: 10.200.0.19/32

List of supported fields in `bgpPeerConfigs`

KEY               | VALUE                 | NOTE
------------------|-----------------------|---------------------------
asn               | int                   | required, mutable
controlPlaneNodes | one or more IP ranges | optional, mutable
ipAddress         | valid IP address      | required, mutable

"""
  bgp_lb_peer_configs_mutex_group.add_argument(
      '--bgp-lb-peer-configs-from-file',
      help=bgp_lb_peer_configs_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )
  bgp_lb_peer_configs_mutex_group.add_argument(
      '--bgp-lb-peer-configs',
      help='BGP LB peer configuration.',
      action='append',
      type=arg_parsers.ArgDict(
          spec={
              'asn': int,
              'ip-address': str,
              'control-plane-nodes': arg_parsers.ArgList(custom_delim_char=';'),
          },
          required_keys=['asn', 'ip-address'],
      ),
  )


def _AddBGPLBNodeConfigs(bare_metal_bgp_lb_node_config):
  """Adds flags to set the BGP LB node config.

  Args:
    bare_metal_bgp_lb_node_config: The parent group to add the flag to.
  """
  node_config_mutex_group = bare_metal_bgp_lb_node_config.add_group(
      help='Populate BGP LB load balancer node config.', mutex=True
  )
  bgp_lb_node_configs_from_file_help_text = """
Path of the YAML/JSON file that contains the BGP LB node configs.

Examples:

  nodeConfigs:
  - nodeIP: 10.200.0.10
    labels:
      node1: label1
      node2: label2
  - nodeIP: 10.200.0.11
    labels:
      node3: label3
      node4: label4

List of supported fields in `nodeConfigs`

KEY           | VALUE                     | NOTE
--------------|---------------------------|---------------------------
nodeIP        | string                    | required, mutable
labels        | one or more key-val pairs | optional, mutable

"""
  node_config_mutex_group.add_argument(
      '--bgp-lb-load-balancer-node-configs-from-file',
      help=bgp_lb_node_configs_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )
  node_config_mutex_group.add_argument(
      '--bgp-lb-load-balancer-node-configs',
      help='BGP LB load balancer node configuration.',
      action='append',
      type=arg_parsers.ArgDict(
          spec={
              'node-ip': str,
              'labels': str,
          },
          required_keys=['node-ip'],
      ),
  )


def _AddBGPLBNodeLabels(bare_metal_bgp_lb_node_config):
  """Adds a flag to assign labels to nodes in a BGP LB node pool.

  Args:
    bare_metal_bgp_lb_node_config: The parent group to add the flags to.
  """
  bare_metal_bgp_lb_node_config.add_argument(
      '--bgp-lb-load-balancer-node-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Labels assigned to nodes of a BGP LB node pool.',
  )


def _AddBGPLBNodeTaints(bare_metal_bgp_lb_node_config):
  """Adds a flag to specify the node taint in the BGP LB node pool.

  Args:
   bare_metal_bgp_lb_node_config: The parent group to add the flags to.
  """
  bare_metal_bgp_lb_node_config.add_argument(
      '--bgp-lb-load-balancer-node-taints',
      metavar='KEY=VALUE:EFFECT',
      help='Node taint applied to every node in a BGP LB node pool.',
      type=arg_parsers.ArgDict(),
  )


def _AddBGPLBNodePoolConfig(bgp_lb_config_group):
  """Adds a command group to set the node pool config for BGP LB load balancer.

  Args:
   bgp_lb_config_group: The argparse parser to add the flag to.
  """
  bare_metal_bgp_lb_node_pool_config_group = bgp_lb_config_group.add_group(
      help=(
          'Anthos on bare metal node pool configuration for BGP LB load'
          ' balancer nodes.'
      ),
  )
  bare_metal_bgp_lb_node_config = (
      bare_metal_bgp_lb_node_pool_config_group.add_group(
          help='BGP LB Node Pool configuration.'
      )
  )

  _AddBGPLBNodeConfigs(bare_metal_bgp_lb_node_config)
  _AddBGPLBNodeLabels(bare_metal_bgp_lb_node_config)
  _AddBGPLBNodeTaints(bare_metal_bgp_lb_node_config)


def _AddBGPLBAddressPools(bgp_lb_config_group, is_update=False):
  """Adds flags for address pools used by BGP LB load balancer.

  Args:
    bgp_lb_config_group: The parent group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bgp_lb_address_pools_mutex_group = bgp_lb_config_group.add_group(
      help='BGP LB address pools configuration.',
      mutex=True,
      required=required,
  )
  bgp_lb_address_pools_from_file_help_text = """
Path of the YAML/JSON file that contains the BGP LB address pools.

Examples:

  addressPools:
  - pool: pool-1
    addresses:
    - 10.200.0.14/32
    - 10.200.0.15/32
    avoidBuggyIPs: True
    manualAssign: True
  - pool: pool-2
    addresses:
    - 10.200.0.16/32
    avoidBuggyIPs: False
    manualAssign: False

List of supported fields in `addressPools`

KEY           | VALUE                 | NOTE
--------------|-----------------------|---------------------------
pool          | string                | required, mutable
addresses     | one or more IP ranges | required, mutable
avoidBuggyIPs | bool                  | optional, mutable, defaults to False
manualAssign  | bool                  | optional, mutable, defaults to False

"""
  bgp_lb_address_pools_mutex_group.add_argument(
      '--bgp-lb-address-pools-from-file',
      help=bgp_lb_address_pools_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )
  bgp_lb_address_pools_mutex_group.add_argument(
      '--bgp-lb-address-pools',
      help='BGP LB address pools configuration.',
      action='append',
      type=arg_parsers.ArgDict(
          spec={
              'pool': str,
              'avoid-buggy-ips': arg_parsers.ArgBoolean(),
              'manual-assign': arg_parsers.ArgBoolean(),
              'addresses': arg_parsers.ArgList(custom_delim_char=';'),
          },
          required_keys=['pool', 'addresses'],
      ),
  )


def _AddBGPLBConfig(lb_config_mutex_group, is_update=False):
  """Adds flags for bgpLB load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  bgp_lb_config_group = lb_config_mutex_group.add_group(
      'BGP LB Configuration',
  )

  _AddBGPLBAsn(bgp_lb_config_group, is_update)
  _AddBGPLBPeerConfigs(bgp_lb_config_group, is_update)
  _AddBGPLBAddressPools(bgp_lb_config_group, is_update)
  _AddBGPLBNodePoolConfig(bgp_lb_config_group)


def _AddMetalLBNodeConfigs(bare_metal_metal_lb_node_config):
  """Adds flags to set the Metal LB node config.

  Args:
    bare_metal_metal_lb_node_config: The parent group to add the flag to.
  """
  node_config_mutex_group = bare_metal_metal_lb_node_config.add_group(
      help='Populate MetalLB load balancer node config.', mutex=True
  )
  metal_lb_node_configs_from_file_help_text = """
Path of the YAML/JSON file that contains the Metal LB node configs.

Examples:

  nodeConfigs:
  - nodeIP: 10.200.0.10
    labels:
      node1: label1
      node2: label2
  - nodeIP: 10.200.0.11
    labels:
      node3: label3
      node4: label4

List of supported fields in `nodeConfigs`

KEY           | VALUE                     | NOTE
--------------|---------------------------|---------------------------
nodeIP        | string                    | required, mutable
labels        | one or more key-val pairs | optional, mutable

"""
  node_config_mutex_group.add_argument(
      '--metal-lb-load-balancer-node-configs-from-file',
      help=metal_lb_node_configs_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )
  node_config_mutex_group.add_argument(
      '--metal-lb-load-balancer-node-configs',
      help='MetalLB load balancer node configuration.',
      action='append',
      type=arg_parsers.ArgDict(
          spec={
              'node-ip': str,
              'labels': str,
          },
          required_keys=['node-ip'],
      ),
  )


def _AddMetalLBNodeLabels(bare_metal_metal_lb_node_config):
  """Adds a flag to assign labels to nodes in a MetalLB node pool.

  Args:
    bare_metal_metal_lb_node_config: The parent group to add the flags to.
  """
  bare_metal_metal_lb_node_config.add_argument(
      '--metal-lb-load-balancer-node-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Labels assigned to nodes of a MetalLB node pool.',
  )


def _AddMetalLBNodeTaints(bare_metal_metal_lb_node_config):
  """Adds a flag to specify the node taint in the MetalLBnode pool.

  Args:
   bare_metal_metal_lb_node_config: The parent group to add the flags to.
  """
  bare_metal_metal_lb_node_config.add_argument(
      '--metal-lb-load-balancer-node-taints',
      metavar='KEY=VALUE:EFFECT',
      help='Node taint applied to every node in a MetalLB node pool.',
      type=arg_parsers.ArgDict(),
  )


def _AddMetalLBNodePoolConfig(metal_lb_config_group):
  """Adds a command group to set the node pool config for MetalLB load balancer.

  Args:
   metal_lb_config_group: The argparse parser to add the flag to.
  """
  bare_metal_metal_lb_node_pool_config_group = metal_lb_config_group.add_group(
      help=(
          'Anthos on bare metal node pool configuration for MetalLB load'
          ' balancer nodes.'
      ),
  )
  bare_metal_metal_lb_node_config = (
      bare_metal_metal_lb_node_pool_config_group.add_group(
          help='MetalLB Node Pool configuration.'
      )
  )

  _AddMetalLBNodeConfigs(bare_metal_metal_lb_node_config)
  _AddMetalLBNodeLabels(bare_metal_metal_lb_node_config)
  _AddMetalLBNodeTaints(bare_metal_metal_lb_node_config)


def _AddMetalLBAddressPools(metal_lb_config_group, is_update=False):
  """Adds flags for address pools used by Metal LB load balancer.

  Args:
    metal_lb_config_group: The parent group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  metal_lb_address_pools_mutex_group = metal_lb_config_group.add_group(
      help='MetalLB address pools configuration.',
      mutex=True,
      required=required,
  )
  metal_lb_address_pools_from_file_help_text = """
Path of the YAML/JSON file that contains the MetalLB address pools.

Examples:

  addressPools:
  - pool: pool-1
    addresses:
    - 10.200.0.14/32
    - 10.200.0.15/32
    avoidBuggyIPs: True
    manualAssign: True
  - pool: pool-2
    addresses:
    - 10.200.0.16/32
    avoidBuggyIPs: False
    manualAssign: False

List of supported fields in `addressPools`

KEY           | VALUE                 | NOTE
--------------|-----------------------|---------------------------
pool          | string                | required, mutable
addresses     | one or more IP ranges | required, mutable
avoidBuggyIPs | bool                  | optional, mutable, defaults to False
manualAssign  | bool                  | optional, mutable, defaults to False

"""
  metal_lb_address_pools_mutex_group.add_argument(
      '--metal-lb-address-pools-from-file',
      help=metal_lb_address_pools_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )
  metal_lb_address_pools_mutex_group.add_argument(
      '--metal-lb-address-pools',
      help='MetalLB address pools configuration.',
      action='append',
      type=arg_parsers.ArgDict(
          spec={
              'pool': str,
              'avoid-buggy-ips': arg_parsers.ArgBoolean(),
              'manual-assign': arg_parsers.ArgBoolean(),
              'addresses': arg_parsers.ArgList(custom_delim_char=';'),
          },
          required_keys=['pool', 'addresses'],
      ),
  )


def _AddMetalLBConfig(lb_config_mutex_group, is_update=False):
  """Adds flags for metalLB load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  metal_lb_config_group = lb_config_mutex_group.add_group(
      'MetalLB Configuration',
  )

  _AddMetalLBAddressPools(metal_lb_config_group, is_update)
  _AddMetalLBNodePoolConfig(metal_lb_config_group)


def AddLoadBalancerConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds a command group to set the load balancer config.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_load_balancer_config_group = parser.add_group(
      help=(
          'Anthos on bare metal standalone cluster load balancer configuration.'
      ),
      required=required,
  )

  lb_config_mutex_group = bare_metal_load_balancer_config_group.add_group(
      mutex=True,
      required=required,
      help='Populate one of the load balancers.',
  )

  _AddMetalLBConfig(lb_config_mutex_group, is_update)
  _AddBGPLBConfig(lb_config_mutex_group, is_update)


def AddUpdateAnnotations(parser: parser_arguments.ArgumentInterceptor):
  """Adds flags to update annotations.

  Args:
    parser: The argparse parser to add the flag to.
  """
  annotations_mutex_group = parser.add_group(mutex=True)
  annotations_mutex_group.add_argument(
      '--add-annotations',
      metavar='KEY1=VALUE1,KEY2=VALUE2',
      help=(
          'Add the given key-value pairs to the current annotations, or update'
          ' its value if the key already exists.'
      ),
      type=arg_parsers.ArgDict(),
  )
  annotations_mutex_group.add_argument(
      '--remove-annotations',
      metavar='KEY1,KEY2',
      help='Remove annotations of the given keys.',
      type=arg_parsers.ArgList(),
  )
  annotations_mutex_group.add_argument(
      '--clear-annotations',
      hidden=True,
      action='store_true',
      help='Clear all the current annotations',
  )
  annotations_mutex_group.add_argument(
      '--set-annotations',
      hidden=True,
      metavar='KEY1=VALUE1,KEY2=VALUE2',
      type=arg_parsers.ArgDict(),
      help='Replace all the current annotations',
  )


def AddIgnoreErrors(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for ignore_errors field.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--ignore-errors',
      help=(
          'If set, the unenrollment of a bare metal standalone cluster'
          ' resource will succeed even if errors occur during unenrollment.'
      ),
      action='store_true',
  )
