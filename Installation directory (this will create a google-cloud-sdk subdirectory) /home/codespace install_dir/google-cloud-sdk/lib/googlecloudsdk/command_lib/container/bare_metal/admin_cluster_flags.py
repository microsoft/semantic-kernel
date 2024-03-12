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
"""Helpers for flags in commands for Anthos clusters on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.container.gkeonprem import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties


def LocationAttributeConfig():
  """Gets Google Cloud location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
      fallthroughs=[
          deps.PropertyFallthrough(
              properties.VALUES.container_bare_metal.location,
          ),
      ],
  )


def GetLocationResourceSpec():
  """Constructs and returns the Resource specification for Location."""
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
  )


def AddLocationResourceArg(parser: parser_arguments.ArgumentInterceptor, verb):
  """Adds a resource argument for Google Cloud location.

  Args:
    parser: The argparse.parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'Google Cloud location {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      help_text='cluster of the {resource}.',
  )


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.bareMetalClusters',
      resource_name='cluster',
      bareMetalClustersId=ClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddClusterResourceArg(
    parser, verb, positional=True, required=True, flag_name_overrides=None
):
  """Adds a resource argument for an Anthos cluster on Bare Metal.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
    flag_name_overrides: {str: str}, dict of attribute names to the desired flag
      name.
  """
  name = 'cluster' if positional else '--cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetClusterResourceSpec(),
      'cluster {}'.format(verb),
      required=required,
      flag_name_overrides=flag_name_overrides,
  ).AddToParser(parser)


def AdminClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='admin_cluster',
      help_text='cluster of the {resource}.',
  )


def GetAdminClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.bareMetalAdminClusters',
      resource_name='admin_cluster',
      bareMetalAdminClustersId=AdminClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddAdminClusterResourceArg(
    parser, verb, positional=True, required=True, flag_name_overrides=None
):
  """Adds a resource argument for an Anthos on bare metal admin cluster.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
    flag_name_overrides: {str: str}, dict of attribute names to the desired flag
      name.
  """
  name = 'admin_cluster' if positional else '--admin-cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAdminClusterResourceSpec(),
      'admin cluster {}'.format(verb),
      required=required,
      flag_name_overrides=flag_name_overrides,
  ).AddToParser(parser)


def AddForceCluster(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for force cluster operation when there are existing node pools.

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


def AddAllowMissingCluster(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for the cluster operation to return success and perform no action when there is no matching cluster.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the Bare Metal cluster is not found, the request will'
          ' succeed but no action will be taken.'
      ),
  )


def AddAllowMissingUpdateCluster(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag to enable allow missing in an update cluster request.

  If set to true, and the cluster is not found, the request will
  create a new cluster with the provided configuration. The user
  must have both create and update permission to call Update with
  allow_missing set to true.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the Anthos cluster on bare metal is not found, the'
          ' update request will try to create a new cluster with the provided'
          ' configuration.'
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


def AddConfigType(parser: parser_arguments.ArgumentInterceptor):
  """Adds flags to specify version config type.

  Args:
    parser: The argparse parser to add the flag to.
  """
  config_type_group = parser.add_group(
      'Use cases for querying versions.', mutex=True
  )
  create_config = config_type_group.add_group(
      'Create an Anthos on bare metal admin cluster use case.'
  )
  upgrade_config = config_type_group.add_group(
      'Upgrade an Anthos on bare metal admin cluster use case.'
  )
  arg_parser = concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              '--admin-cluster-membership',
              flags.GetAdminClusterMembershipResourceSpec(),
              (
                  'Membership of the admin cluster to query versions for'
                  ' create. Membership can be the membership ID or the full'
                  ' resource name.'
              ),
              flag_name_overrides={
                  'project': '--admin-cluster-membership-project',
                  'location': '--admin-cluster-membership-location',
              },
              required=False,
              group=create_config,
          ),
          presentation_specs.ResourcePresentationSpec(
              '--cluster',
              GetClusterResourceSpec(),
              'Cluster to query versions for upgrade.',
              required=False,
              flag_name_overrides={'location': ''},
              group=upgrade_config,
          ),
      ],
      command_level_fallthroughs={
          '--cluster.location': ['--location'],
      },
  )
  arg_parser.AddToParser(parser)
  parser.set_defaults(admin_cluster_membership_location='global')


def AddAdminConfigType(parser: parser_arguments.ArgumentInterceptor):
  """Adds flags to specify admin cluster version config type.

  Args:
    parser: The argparse parser to add the flag to.
  """
  config_type_group = parser.add_group(
      'Use cases for querying versions.', mutex=True
  )
  upgrade_config = config_type_group.add_group(
      'Upgrade an Anthos on bare metal admin cluster use case.'
  )
  arg_parser = concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              '--admin-cluster',
              GetAdminClusterResourceSpec(),
              'Admin cluster to query versions for upgrade.',
              flag_name_overrides={'location': ''},
              required=False,
              group=upgrade_config,
          ),
      ],
      command_level_fallthroughs={
          '--admin-cluster.location': ['--location'],
      },
  )
  arg_parser.AddToParser(parser)


def AddVersion(parser: parser_arguments.ArgumentInterceptor, is_update=False):
  """Adds a flag to specify the Anthos cluster on bare metal version.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  parser.add_argument(
      '--version',
      required=required,
      help=(
          'Anthos cluster on bare metal version for the admin cluster resource.'
      ),
  )


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


def _AddPodAddressCIDRBlocks(bare_metal_island_mode_cidr_config_group):
  """Adds a flag to specify the IPv4 address ranges used in the pods in the cluster.

  Args:
    bare_metal_island_mode_cidr_config_group: The parent group to add the flag
      to.
  """
  bare_metal_island_mode_cidr_config_group.add_argument(
      '--island-mode-pod-address-cidr-blocks',
      metavar='POD_ADDRESS',
      required=True,
      type=arg_parsers.ArgList(
          min_length=1,
      ),
      help='IPv4 address range for all pods in the cluster.',
  )


def _AddIslandModeCIDRConfig(bare_metal_network_config_group, is_update=False):
  """Adds island mode CIDR config related flags.

  Args:
    bare_metal_network_config_group: The parent group to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_island_mode_cidr_config_group = (
      bare_metal_network_config_group.add_group(
          help='Island mode CIDR network configuration.',
      )
  )
  if required:
    _AddServiceAddressCIDRBlocks(
        bare_metal_island_mode_cidr_config_group, is_update
    )
    _AddPodAddressCIDRBlocks(bare_metal_island_mode_cidr_config_group)
  else:
    _AddServiceAddressCIDRBlocks(
        bare_metal_island_mode_cidr_config_group, is_update
    )


def AddNetworkConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds network config related flags.

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


def _AddManualLBConfig(lb_config_mutex_group):
  """Adds flags for manual load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
  """
  manual_lb_config_group = lb_config_mutex_group.add_group(
      help='Manual load balancer configuration.',
  )
  manual_lb_config_group.add_argument(
      '--enable-manual-lb',
      required=True,
      action='store_true',
      help='ManualLB typed load balancers configuration.',
  )


def _AddVIPConfig(bare_metal_load_balancer_config_group):
  """Adds flags to set VIPs used by the load balancer.

  Args:
    bare_metal_load_balancer_config_group: The parent group to add the flags to.
  """
  bare_metal_vip_config_group = bare_metal_load_balancer_config_group.add_group(
      help=' VIPs used by the load balancer.',
      required=True,
  )
  bare_metal_vip_config_group.add_argument(
      '--control-plane-vip',
      required=True,
      help='VIP for the Kubernetes API of this cluster.',
  )
  bare_metal_vip_config_group.add_argument(
      '--ingress-vip',
      required=True,
      help='VIP for ingress traffic into this cluster.',
  )


def _AddLoadBalancerPortConfig(bare_metal_load_balancer_config_group):
  """Adds flags to set port for load balancer.

  Args:
    bare_metal_load_balancer_config_group: The parent group to add the flags to.
  """
  control_plane_load_balancer_port_config_group = (
      bare_metal_load_balancer_config_group.add_group(
          help='Control plane load balancer port configuration.',
          required=True,
      )
  )
  control_plane_load_balancer_port_config_group.add_argument(
      '--control-plane-load-balancer-port',
      required=True,
      help='Control plane load balancer port configuration.',
      type=int,
  )


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
      help='Anthos on bare metal cluster load balancer configuration.',
      required=required,
  )

  lb_config_mutex_group = bare_metal_load_balancer_config_group.add_group(
      mutex=True,
      required=required,
      help='Populate one of the load balancers.',
  )

  if required:
    _AddVIPConfig(bare_metal_load_balancer_config_group)
    _AddLoadBalancerPortConfig(bare_metal_load_balancer_config_group)
    _AddMetalLBConfig(lb_config_mutex_group, is_update)
    _AddManualLBConfig(lb_config_mutex_group)
  else:
    _AddMetalLBConfig(lb_config_mutex_group, is_update)


def _AddStorageLVPShareConfig(bare_metal_lvp_share_config_group):
  """Adds flags to set LVP Share class and path used by the storage.

  Args:
    bare_metal_lvp_share_config_group: The parent group to add the flags to.
  """
  bare_metal_storage_lvp_share_config_group = (
      bare_metal_lvp_share_config_group.add_group(
          help=' LVP share class and path used by the storage.',
          required=True,
      )
  )
  bare_metal_storage_lvp_share_config_group.add_argument(
      '--lvp-share-path',
      required=True,
      help='Path for the LVP share class.',
  )
  bare_metal_storage_lvp_share_config_group.add_argument(
      '--lvp-share-storage-class',
      required=True,
      help='Storage class for LVP share.',
  )


def _AddLVPShareConfig(bare_metal_storage_config_group):
  """Adds flags to set LVP Share class and path used by the storage.

  Args:
    bare_metal_storage_config_group: The parent group to add the flags to.
  """
  bare_metal_lvp_share_config_group = bare_metal_storage_config_group.add_group(
      help=' LVP share configuration.',
      required=True,
  )

  bare_metal_lvp_share_config_group.add_argument(
      '--shared-path-pv-count',
      help='Number of subdirectories to create under path.',
  )

  _AddStorageLVPShareConfig(bare_metal_lvp_share_config_group)


def _AddLVPNodeMountsConfig(bare_metal_storage_config_group):
  """Adds flags to set LVP Node Mounts class and path used by the storage.

  Args:
    bare_metal_storage_config_group: The parent group to add the flags to.
  """
  bare_metal_lvp_node_config_group = bare_metal_storage_config_group.add_group(
      help=' LVP node mounts class and path used by the storage.',
      required=True,
  )
  bare_metal_lvp_node_config_group.add_argument(
      '--lvp-node-mounts-config-path',
      required=True,
      help='Path for the LVP node mounts class.',
  )
  bare_metal_lvp_node_config_group.add_argument(
      '--lvp-node-mounts-config-storage-class',
      required=True,
      help='Storage class for LVP node mounts.',
  )


def AddStorageConfig(parser: parser_arguments.ArgumentInterceptor):
  """Adds a command group to set the storage config.

  Args:
    parser: The argparse parser to add the flag to.
  """
  bare_metal_storage_config_group = parser.add_group(
      help='Anthos on bare metal cluster storage configuration.',
      required=True,
  )
  _AddLVPShareConfig(bare_metal_storage_config_group)
  _AddLVPNodeMountsConfig(bare_metal_storage_config_group)


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
  bare_metal_control_plane_node_pool_config_group = (
      bare_metal_control_plane_config_group.add_group(
          help=(
              'Anthos on bare metal cluster control plane node pool'
              ' configuration.'
          ),
          required=required,
      )
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
      help='Anthos on bare metal cluster control plane configuration.',
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


def AddAnnotations(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag to specify cluster annotations.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Annotations on the Anthos on bare metal resource.',
  )


def _AddURIConfig(bare_metal_proxy_config_group, is_update=False):
  """Adds a flag to specify the address of the proxy server.

  Args:
    bare_metal_proxy_config_group: The parent group to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_proxy_config_group.add_argument(
      '--uri',
      required=required,
      type=str,
      help='Address of the proxy server.',
  )


def _AddNoProxyConfig(bare_metal_proxy_config_group):
  """Adds a flag to specify the address of the proxy server.

  Args:
    bare_metal_proxy_config_group: The parent group to add the flag to.
  """
  bare_metal_proxy_config_group.add_argument(
      '--no-proxy',
      metavar='NO_PROXY',
      type=arg_parsers.ArgList(),
      help='List of IPs, hostnames, and domains that should skip the proxy.',
  )


def AddProxyConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds a command group to set the proxy config.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  bare_metal_proxy_config_group = parser.add_group(
      help='Anthos on bare metal cluster proxy configuration.',
  )
  _AddURIConfig(bare_metal_proxy_config_group, is_update)
  _AddNoProxyConfig(bare_metal_proxy_config_group)


def AddClusterOperationsConfig(parser: parser_arguments.ArgumentInterceptor):
  """Adds a command group to set the cluster operations config.

  Args:
    parser: The argparse parser to add the flag to.
  """
  bare_metal_cluster_operations_config_group = parser.add_group(
      help='Anthos on bare metal cluster operations configuration.',
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
      help='Anthos on bare metal cluster maintenance configuration.',
  )

  bare_metal_maintenance_config_group.add_argument(
      '--maintenance-address-cidr-blocks',
      type=arg_parsers.ArgList(),
      metavar='MAINTENANCE_ADDRESS_CIDR_BLOCKS',
      help='IPv4 addresses to be placed into maintenance mode.',
      required=required,
  )


def _AddMaxPodsPerNode(bare_metal_workload_node_config_group):
  """Adds flags to set maximum pods per node.

  Args:
    bare_metal_workload_node_config_group: The parent group to add the flags to.
  """
  bare_metal_workload_node_config_group.add_argument(
      '--max-pods-per-node',
      help='Maximum number of pods a node can run.',
      type=int,
  )


def _AddContainerRuntime(bare_metal_workload_node_config_group):
  """Adds flags to set runtime for containers.

  Args:
    bare_metal_workload_node_config_group: The parent group to add the flags to.
  """
  bare_metal_workload_node_config_group.add_argument(
      '--container-runtime',
      help=(
          'Container runtime which will be used in the bare metal admin'
          ' cluster.'
      ),
  )


def AddWorkloadNodeConfig(parser: parser_arguments.ArgumentInterceptor):
  """Adds a command group to set the workload node config.

  Args:
    parser: The argparse parser to add the flag to.
  """
  bare_metal_workload_node_config_group = parser.add_group(
      help='Anthos on bare metal cluster workload node configuration.',
  )

  _AddMaxPodsPerNode(bare_metal_workload_node_config_group)
  _AddContainerRuntime(bare_metal_workload_node_config_group)


def _AddAuthorization(bare_metal_security_config_group, is_update=False):
  """Adds flags to specify applied and managed RBAC policy.

  Args:
    bare_metal_security_config_group: The parent group to add the flags to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  authorization_group = bare_metal_security_config_group.add_group(
      help='Admin cluster authorization configurations'
  )
  authorization_group.add_argument(
      '--admin-users',
      help=(
          'Users that will be granted the view role on the admin cluster,'
          ' providing view only access to the cluster.'
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
      help='Anthos on bare metal admin cluster security configuration.',
  )

  _AddAuthorization(bare_metal_security_config_group, is_update)


def AddNodeAccessConfig(parser: parser_arguments.ArgumentInterceptor):
  """Adds a command group to set the node access config.

  Args:
    parser: The argparse parser to add the flag to.
  """
  bare_metal_node_access_config_group = parser.add_group(
      help=(
          'Anthos on bare metal node access related settings for the admin'
          ' cluster.'
      ),
  )

  bare_metal_node_access_config_group.add_argument(
      '--login-user',
      type=str,
      help='User name used to access node machines.',
  )


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.operations',
      resource_name='operation',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddOperationResourceArg(parser: parser_arguments.ArgumentInterceptor, verb):
  """Adds a resource argument for operation in bare metal.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'operation_id',
      GetOperationResourceSpec(),
      'operation {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AdminClusterMembershipIdAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='admin_cluster_membership',
      help_text=(
          'admin cluster membership of the {resource}, in the form of'
          ' projects/PROJECT/locations/LOCATION/memberships/MEMBERSHIP. '
      ),
  )


def AdminClusterMembershipLocationAttributeConfig():
  """Gets admin cluster membership location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
  )


def AdminClusterMembershipProjectAttributeConfig():
  """Gets Google Cloud project resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text='Google Cloud project for the {resource}.',
  )


def GetAdminClusterMembershipResourceSpec():
  return concepts.ResourceSpec(
      'gkehub.projects.locations.memberships',
      resource_name='admin_cluster_membership',
      membershipsId=AdminClusterMembershipIdAttributeConfig(),
      locationsId=AdminClusterMembershipLocationAttributeConfig(),
      projectsId=AdminClusterMembershipProjectAttributeConfig(),
  )


def AddAdminClusterMembershipResourceArg(
    parser, positional=True, required=True
):
  """Adds a resource argument for a bare metal admin cluster membership.

  Args:
    parser: The argparse parser to add the resource arg to.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
  """
  name = (
      'admin_cluster_membership' if positional else '--admin-cluster-membership'
  )
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAdminClusterMembershipResourceSpec(),
      (
          'membership of the admin cluster. Membership can be the membership ID'
          ' or the full resource name.'
      ),
      required=required,
      flag_name_overrides={
          'project': '--admin-cluster-membership-project',
          'location': '--admin-cluster-membership-location',
      },
  ).AddToParser(parser)


def AddAdminLoadBalancerConfig(
    parser: parser_arguments.ArgumentInterceptor, is_update=False
):
  """Adds a command group to set the load balancer config.

  Args:
    parser: The argparse parser to add the flag to.
    is_update: bool, whether the flag is for update command or not.
  """
  required = not is_update
  bare_metal_admin_load_balancer_config_group = parser.add_group(
      help='Anthos on bare metal admin cluster load balancer configuration.',
      required=required,
  )
  _AddAdminVIPConfig(bare_metal_admin_load_balancer_config_group)
  _AddAdminLoadBalancerPortConfig(bare_metal_admin_load_balancer_config_group)
  _AddAdminManualLBConfig(bare_metal_admin_load_balancer_config_group)


def _AddAdminVIPConfig(bare_metal_admin_load_balancer_config_group):
  """Adds flags to set VIPs used by the load balancer.

  Args:
    bare_metal_admin_load_balancer_config_group: The parent group to add the
      flags to.
  """
  bare_metal_vip_config_group = (
      bare_metal_admin_load_balancer_config_group.add_group(
          help='VIPs used by the load balancer.',
          required=True,
      )
  )
  bare_metal_vip_config_group.add_argument(
      '--control-plane-vip',
      required=True,
      help='VIP for the Kubernetes API of this cluster.',
  )


def _AddAdminLoadBalancerPortConfig(
    bare_metal_admin_load_balancer_config_group,
):
  """Adds flags to set port for load balancer.

  Args:
    bare_metal_admin_load_balancer_config_group: The parent group to add the
      flags to.
  """
  control_plane_load_balancer_port_config_group = (
      bare_metal_admin_load_balancer_config_group.add_group(
          help='Control plane load balancer port configuration.',
          required=True,
      )
  )
  control_plane_load_balancer_port_config_group.add_argument(
      '--control-plane-load-balancer-port',
      required=True,
      help='Control plane load balancer port configuration.',
      type=int,
  )


def _AddAdminManualLBConfig(bare_metal_admin_load_balancer_config_group):
  """Adds flags for manual load balancer.

  Args:
    bare_metal_admin_load_balancer_config_group: The parent group to add the
      flags to.
  """
  manual_lb_config_group = (
      bare_metal_admin_load_balancer_config_group.add_group(
          help='Manual load balancer configuration.',
      )
  )
  manual_lb_config_group.add_argument(
      '--enable-manual-lb',
      required=True,
      action='store_true',
      help='ManualLB typed load balancers configuration.',
  )


def AddAdminWorkloadNodeConfig(parser: parser_arguments.ArgumentInterceptor):
  """Adds a command group to set the workload node config.

  Args:
    parser: The argparse parser to add the flag to.
  """
  bare_metal_workload_node_config_group = parser.add_group(
      help='Anthos on bare metal admin cluster workload node configuration.',
  )

  _AddMaxPodsPerNode(bare_metal_workload_node_config_group)


def AddIgnoreErrors(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for ignore_errors field.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--ignore-errors',
      help=(
          'If set, the unenrollment of a bare metal admin cluster'
          ' resource will succeed even if errors occur during unenrollment.'
      ),
      action='store_true',
  )
