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
"""Helpers for flags in commands working with Anthos clusters on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.container.gkeonprem import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def Get(args, flag_name, default=None):
  """Returns the value if it's set, otherwise returns None.

  Args:
    args: An argparser Namespace class instance.
    flag_name: A string type flag name.
    default: The default value to return if not found in the argparser
      namespace.

  Returns:
    The flag value if it is set by the user. If the flag is not added to the
    interface, or it is added by not specified by the user, returns the
    default value.
  """
  default_values = {
      'page_size': 100,
  }
  if hasattr(args, flag_name) and args.IsSpecified(flag_name):
    return getattr(args, flag_name)
  return default_values.get(flag_name, default)


def IsSet(kwargs):
  """Returns True if any of the kwargs is set to not None value.

  The added condition handles the case when user specified boolean False
  for the given args, and it should return True, which does not work with
  normal Python identity comparison.

  Args:
    kwargs: dict, a mapping from proto field to its respective constructor
      function.

  Returns:
    True if there exists a field that contains a user specified argument.
  """
  for value in kwargs.values():
    if isinstance(value, bool):
      return True
    elif value:
      return True
  return False


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.operations',
      resource_name='operation',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddOperationResourceArg(parser: parser_arguments.ArgumentInterceptor, verb):
  """Adds a resource argument for operation in VMware.

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


def LocationAttributeConfig():
  """Gets Google Cloud location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.container_vmware.location),
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
      'gkeonprem.projects.locations.vmwareClusters',
      resource_name='cluster',
      vmwareClustersId=ClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddClusterResourceArg(
    parser: parser_arguments.ArgumentInterceptor,
    verb,
    positional=True,
    required=True,
    flag_name_overrides=None,
):
  """Adds a resource argument for an Anthos cluster on VMware.

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


def GetAdminClusterResource(admin_cluster_name):
  relative_name = admin_cluster_name
  if admin_cluster_name.startswith('//'):
    # Remove '//gkeonprem.googleapis.com/' from the resource name.
    parts = admin_cluster_name.split('/')
    relative_name = '/'.join(parts[3:])
  return resources.REGISTRY.ParseRelativeName(
      relative_name,
      collection='gkeonprem.projects.locations.vmwareAdminClusters',
  )


def AdminClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='admin_cluster',
      help_text='cluster of the {resource}.',
  )


def GetAdminClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.vmwareAdminClusters',
      resource_name='admin_cluster',
      vmwareAdminClustersId=AdminClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddAdminClusterResourceArg(
    parser: parser_arguments.ArgumentInterceptor,
    verb,
    positional=True,
    required=True,
    flag_name_overrides=None,
):
  """Adds a resource argument for an Anthos on VMware admin cluster.

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


def GetAdminClusterMembershipResource(membership_name):
  return resources.REGISTRY.ParseRelativeName(
      membership_name, collection='gkehub.projects.locations.memberships'
  )


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
    parser: parser_arguments.ArgumentInterceptor, positional=True, required=True
):
  """Adds a resource argument for a VMware admin cluster membership.

  Args:
    parser: The argparse parser to add the resource arg to.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
  """
  name = (
      'admin_cluster_membership' if positional else '--admin-cluster-membership'
  )
  admin_cluster_membership_help_text = """membership of the admin cluster. Membership name is the same as the admin cluster name.

Examples:

  $ {command}
        --admin-cluster-membership=projects/example-project-12345/locations/us-west1/memberships/example-admin-cluster-name

or

  $ {command}
        --admin-cluster-membership-project=example-project-12345
        --admin-cluster-membership-location=us-west1
        --admin-cluster-membership=example-admin-cluster-name

  """
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAdminClusterMembershipResourceSpec(),
      admin_cluster_membership_help_text,
      required=required,
      flag_name_overrides={
          'project': '--admin-cluster-membership-project',
          'location': '--admin-cluster-membership-location',
      },
  ).AddToParser(parser)


def NodePoolAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='node_pool', help_text='node pool of the {resource}.'
  )


def GetNodePoolResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.vmwareClusters.vmwareNodePools',
      resource_name='node_pool',
      vmwareNodePoolsId=NodePoolAttributeConfig(),
      vmwareClustersId=ClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddNodePoolResourceArg(
    parser: parser_arguments.ArgumentInterceptor, verb, positional=True
):
  """Adds a resource argument for a VMware node pool.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'node_pool' if positional else '--node-pool'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetNodePoolResourceSpec(),
      'node pool {}'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddForceUnenrollCluster(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for force unenroll operation when there are existing node pools.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--force',
      action='store_true',
      help=(
          'If set, any child node pools will also be unenrolled. This flag is'
          ' required if the cluster has any associated node pools.'
      ),
  )


def AddForceDeleteCluster(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for force delete cluster operation when there are existing node pools.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--force',
      action='store_true',
      help=(
          'If set, any node pools from the cluster will also be deleted. This'
          ' flag is required if the cluster has any associated node pools.'
      ),
  )


def AddAllowMissingDeleteNodePool(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for delete node pool operation to return success and perform no action when there is no matching node pool.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the Vmware Node Pool is not found, the request will'
          ' succeed but no action will be taken.'
      ),
  )


def AddAllowMissingUnenrollNodePool(
    parser: parser_arguments.ArgumentInterceptor,
):
  """Adds a flag for unenroll node pool operation to return success and perform no action when there is no matching node pool.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the Vmware Node Pool is not found, the request will'
          ' succeed but no action will be taken.'
      ),
  )


def AddAllowMissingDeleteCluster(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for delete cluster operation to return success and perform no action when there is no matching cluster.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the Anthos cluster on VMware is not found, the request'
          ' will succeed but no action will be taken.'
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
      hidden=True,
      help=(
          'If set, and the Anthos cluster on VMware is not found, the update'
          ' request will try to create a new cluster with the provided'
          ' configuration.'
      ),
  )


def AddAllowMissingUnenrollCluster(
    parser: parser_arguments.ArgumentInterceptor,
):
  """Adds a flag to enable allow missing in an unenroll cluster request.

  If set, and the Anthos on VMware cluster is not found, the request will
  succeed but no action will be taken on the server and return a completed LRO.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If set, and the VMware Cluster is not found, the request will'
          ' succeed but no action will be taken on the server and return a'
          ' completed LRO.'
      ),
  )


def AddValidationOnly(
    parser: parser_arguments.ArgumentInterceptor, hidden=False
):
  """Adds a flag to only validate the request without performing the operation.

  Args:
    parser: The argparse parser to add the flag to.
    hidden: Set to False when validate-only flag is implemented in the API.
  """
  parser.add_argument(
      '--validate-only',
      action='store_true',
      help=(
          'If set, only validate the request, but do not actually perform the'
          ' operation.'
      ),
      hidden=hidden,
  )


def _AddImageType(vmware_node_config_group, for_update=False):
  """Adds a flag to specify the node pool image type.

  Args:
    vmware_node_config_group: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_node_config_group.add_argument(
      '--image-type',
      required=required,
      help='OS image type to use on node pool instances.',
  )


def _AddReplicas(vmware_node_config_group):
  """Adds a flag to specify the number of replicas in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--replicas',
      type=int,
      help='Number of replicas to use on node pool instances.',
  )


def _AddEnableLoadBalancer(vmware_node_config_group, for_update=False):
  """Adds a flag to enable load balancer in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    enable_lb_mutex_group = vmware_node_config_group.add_group(mutex=True)
    surface = enable_lb_mutex_group
  else:
    surface = vmware_node_config_group

  surface.add_argument(
      '--enable-load-balancer',
      action='store_const',
      const=True,
      help=(
          'If set, enable the use of load balancer on the node pool instances.'
      ),
  )

  if for_update:
    surface.add_argument(
        '--disable-load-balancer',
        action='store_const',
        const=True,
        help=(
            'If set, disable the use of load balancer on the node pool'
            ' instances.'
        ),
    )


def _AddCpus(vmware_node_config_group):
  """Adds a flag to specify the number of cpus in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--cpus',
      help='Number of CPUs for each node in the node pool.',
      type=int,
  )


def _AddMemoryMb(vmware_node_config_group):
  """Adds a flag to specify the memory in MB in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--memory',
      help='Size of memory for each node in the node pool in MB.',
      type=arg_parsers.BinarySize(default_unit='MB', type_abbr='MB'),
  )


def _AddImage(vmware_node_config_group):
  """Adds a flag to specify the image in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--image',
      help='OS image name in vCenter.',
      type=str,
  )


def _AddBootDiskSizeGb(vmware_node_config_group):
  """Adds a flag to specify the boot disk size in GB in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--boot-disk-size',
      help='Size of VMware disk to be used during creation in GB.',
      type=arg_parsers.BinarySize(default_unit='GB', type_abbr='GB'),
  )


def _AddNodeTaint(vmware_node_config_group, for_update=False):
  """Adds a flag to specify the node taint in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  node_pool_create_help_text = """\
Applies the given kubernetes taints on all nodes in the new node pool, which can
be used with tolerations for pod scheduling.

Taint effect must be one of the following: `NoSchedule`, `PreferNoSchedule`, or `NoExecute`.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-taints=key1=val1:NoSchedule,key2=val2:PreferNoSchedule
"""
  node_pool_update_help_text = """\
Replaces all the user specified Kubernetes taints on all nodes in an existing
node pool, which can be used with tolerations for pod scheduling.

Taint effect must be one of the following: `NoSchedule`, `PreferNoSchedule`, or `NoExecute`.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-taints=key1=val1:NoSchedule,key2=val2:PreferNoSchedule
"""

  help_text = (
      node_pool_update_help_text if for_update else node_pool_create_help_text
  )
  vmware_node_config_group.add_argument(
      '--node-taints',
      metavar='KEY=VALUE:EFFECT',
      help=help_text,
      type=arg_parsers.ArgDict(),
  )


def _AddNodeLabels(vmware_node_config_group):
  """Adds a flag to specify the labels in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--node-labels',
      metavar='KEY=VALUE',
      help='Kubernetes labels (key/value pairs) to be applied to each node.',
      type=arg_parsers.ArgDict(),
  )


def AddVmwareNodeConfig(
    parser: parser_arguments.ArgumentInterceptor,
    for_update: bool = False,
    release_track: base.ReleaseTrack = None,
):
  """Adds flags to specify the configuration of the node pool.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
    release_track: The release track of this command.
  """
  vmware_node_config_group = parser.add_group(
      help='Configuration of the node pool',
      required=False if for_update else True,
  )
  _AddCpus(vmware_node_config_group)
  _AddMemoryMb(vmware_node_config_group)
  _AddReplicas(vmware_node_config_group)
  _AddImageType(vmware_node_config_group, for_update=for_update)
  _AddImage(vmware_node_config_group)
  _AddBootDiskSizeGb(vmware_node_config_group)
  _AddNodeTaint(vmware_node_config_group)
  _AddNodeLabels(vmware_node_config_group)
  _AddVmwareVsphereConfig(
      vmware_node_config_group,
      release_track=release_track,
      for_update=for_update,
  )
  _AddEnableLoadBalancer(vmware_node_config_group, for_update=for_update)


def AddVmwareNodePoolAutoscalingConfig(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds a flag to specify the node pool autoscaling config.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  group = parser.add_group('Node pool autoscaling')
  group.add_argument(
      '--min-replicas',
      required=required,
      type=int,
      help='Minimum number of replicas in the node pool.',
  )
  group.add_argument(
      '--max-replicas',
      required=required,
      type=int,
      help='Maximum number of replicas in the node pool.',
  )


def AddVersion(parser: parser_arguments.ArgumentInterceptor, required=False):
  """Adds a flag to specify the Anthos cluster on VMware version.

  Args:
    parser: The argparse parser to add the flag to.
    required: bool, whether the argument is required or not.
  """
  parser.add_argument(
      '--version',
      required=required,
      help='Anthos Cluster on VMware version for the user cluster resource',
  )


def _AddF5Config(lb_config_mutex_group, for_update=False):
  """Adds flags for F5 Big IP load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  if for_update:
    return

  f5_config_group = lb_config_mutex_group.add_group(
      help='F5 Big IP Configuration',
  )
  f5_config_group.add_argument(
      '--f5-config-address',
      type=str,
      required=required,
      help='F5 Big IP load balancer address.',
  )
  f5_config_group.add_argument(
      '--f5-config-partition',
      type=str,
      required=required,
      help='F5 Big IP load balancer partition.',
  )
  f5_config_group.add_argument(
      '--f5-config-snat-pool',
      type=str,
      help='F5 Big IP load balancer pool name if using SNAT.',
  )


def _AddMetalLbConfig(lb_config_mutex_group):
  """Adds flags for MetalLB load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
  """
  metal_lb_config_mutex_group = lb_config_mutex_group.add_group(
      help='MetalLB Configuration',
      mutex=True,
  )

  metal_lb_config_from_file_help_text = """
Path of the YAML/JSON file that contains the MetalLB configurations.

Examples:

  metalLBConfig:
    addressPools:
    - pool: lb-test-ip
      addresses:
      - 10.251.133.79/32
      - 10.251.133.80/32
      avoidBuggyIPs: True
      manualAssign: False
    - pool: ingress-ip
      addresses:
      - 10.251.133.70/32
      avoidBuggyIPs: False
      manualAssign: True

List of supported fields in `metalLBConfig`

KEY           | VALUE                     | NOTE
--------------|---------------------------|------------------
addressPools  | one or more addressPools  | required, mutable

List of supported fields in `addressPools`

KEY           | VALUE                 | NOTE
--------------|-----------------------|---------------------------
pool          | string                | required, mutable
addresses     | one or more IP ranges | required, mutable
avoidBuggyIPs | bool                  | optional, mutable, defaults to False
manualAssign  | bool                  | optional, mutable, defaults to False

"""
  metal_lb_config_mutex_group.add_argument(
      '--metal-lb-config-from-file',
      help=metal_lb_config_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )

  metal_lb_config_address_pools_help_text = """
MetalLB load balancer configurations.

Examples:

To specify MetalLB load balancer configurations for two address pools `pool1` and `pool2`,

```
$ gcloud {command}
    --metal-lb-config-address-pools 'pool=pool1,avoid-buggy-ips=True,manual-assign=True,addresses=192.168.1.1/32;192.168.1.2-192.168.1.3'
    --metal-lb-config-address-pools 'pool=pool2,avoid-buggy-ips=False,manual-assign=False,addresses=192.168.2.1/32;192.168.2.2-192.168.2.3'
```

Use quote around the flag value to escape semicolon in the terminal.
"""
  metal_lb_config_mutex_group.add_argument(
      '--metal-lb-config-address-pools',
      help=metal_lb_config_address_pools_help_text,
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


def _AddManualLbConfig(lb_config_mutex_group, for_update=False):
  """Adds flags for Manual load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    return
  manual_lb_config_group = lb_config_mutex_group.add_group(
      help=textwrap.dedent("""\
        Manual load balancer configuration.

        With manual load balancing mode, DHCP is not supported. Specify static IP addresses for cluster nodes instead.
        For more details, see https://cloud.google.com/anthos/clusters/docs/on-prem/latest/how-to/manual-load-balance#setting_aside_node_ip_addresses.
        """),
  )
  manual_lb_config_group.add_argument(
      '--ingress-http-node-port',
      help="NodePort for ingress service's http.",
      type=int,
  )
  manual_lb_config_group.add_argument(
      '--ingress-https-node-port',
      help="NodePort for ingress service's https.",
      type=int,
  )
  manual_lb_config_group.add_argument(
      '--control-plane-node-port',
      help='NodePort for control plane service.',
      type=int,
  )
  manual_lb_config_group.add_argument(
      '--konnectivity-server-node-port',
      help=(
          'NodePort for konnectivity service running as a sidecar in each'
          ' kube-apiserver pod.'
      ),
      type=int,
  )


def _AddVmwareVipConfig(vmware_load_balancer_config_group, for_update=False):
  """Adds flags to set VIPs used by the load balancer..

  Args:
    vmware_load_balancer_config_group: The parent group to add the flags to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  if for_update:
    return

  vmware_vip_config_group = vmware_load_balancer_config_group.add_group(
      help=' VIPs used by the load balancer',
      required=required,
  )
  vmware_vip_config_group.add_argument(
      '--control-plane-vip',
      required=required,
      help='VIP for the Kubernetes API of this cluster.',
  )
  vmware_vip_config_group.add_argument(
      '--ingress-vip',
      required=required,
      help='VIP for ingress traffic into this cluster.',
  )


def AddVmwareLoadBalancerConfig(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds a command group to set the load balancer config.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_load_balancer_config_group = parser.add_group(
      help='Anthos on VMware cluster load balancer configurations',
      required=required,
  )
  _AddVmwareVipConfig(vmware_load_balancer_config_group, for_update=for_update)

  lb_config_mutex_group = vmware_load_balancer_config_group.add_group(
      mutex=True,
      help='Populate one of the load balancers.',
      required=required,
  )
  _AddMetalLbConfig(lb_config_mutex_group)
  _AddF5Config(lb_config_mutex_group, for_update=for_update)
  _AddManualLbConfig(lb_config_mutex_group, for_update=for_update)


def AddDescription(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag to specify the description of the resource.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--description', type=str, help='Description for the resource.'
  )


def AddNodePoolDisplayName(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag to specify the display name of the node pool.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--display-name', type=str, help='Display name for the resource.'
  )


def AddNodePoolAnnotations(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag to specify node pool annotations."""
  parser.add_argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Annotations on the node pool.',
  )


def _AddServiceAddressCidrBlocks(vmware_network_config_group, for_update=False):
  """Adds a flag to specify the IPv4 address ranges used in the services in the cluster.

  Args:
    vmware_network_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  if for_update:
    return
  vmware_network_config_group.add_argument(
      '--service-address-cidr-blocks',
      metavar='SERVICE_ADDRESS',
      type=arg_parsers.ArgList(
          min_length=1,
          max_length=1,
      ),
      required=required,
      help='IPv4 address range for all services in the cluster.',
  )


def _AddPodAddressCidrBlocks(vmware_network_config_group, for_update=False):
  """Adds a flag to specify the IPv4 address ranges used in the pods in the cluster.

  Args:
    vmware_network_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  if for_update:
    return
  vmware_network_config_group.add_argument(
      '--pod-address-cidr-blocks',
      metavar='POD_ADDRESS',
      type=arg_parsers.ArgList(
          min_length=1,
          max_length=1,
      ),
      required=required,
      help='IPv4 address range for all pods in the cluster.',
  )


def AddVmwareNetworkConfig(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds network config related flags.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_network_config_group = parser.add_group(
      help='VMware User Cluster network configurations',
      required=required,
  )
  _AddServiceAddressCidrBlocks(
      vmware_network_config_group, for_update=for_update
  )
  _AddPodAddressCidrBlocks(vmware_network_config_group, for_update=for_update)
  _AddIpConfiguration(vmware_network_config_group, for_update=for_update)
  _AddVmwareHostConfig(vmware_network_config_group, for_update=for_update)

  # add create only flags.
  if not for_update:
    _AddVmwareControlPlaneV2Config(vmware_network_config_group)


def AddConfigType(parser: parser_arguments.ArgumentInterceptor):
  """Adds flags to specify version config type.

  Args:
    parser: The argparse parser to add the flag to.
  """
  config_type_group = parser.add_group(
      'Use cases for querying versions.', mutex=True, required=False
  )
  create_config = config_type_group.add_group(
      'Create an Anthos on VMware user cluster use case.'
  )
  upgrade_config = config_type_group.add_group(
      'Upgrade an Anthos on VMware user cluster use case.'
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


def _AddVmwareDhcpIpConfig(ip_configuration_mutex_group, for_update=False):
  """Adds flags to specify DHCP configuration.

  Args:
    ip_configuration_mutex_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    return
  dhcp_config_group = ip_configuration_mutex_group.add_group(
      help='DHCP configuration group.'
  )
  dhcp_config_group.add_argument(
      '--enable-dhcp',
      help=textwrap.dedent("""\
        Enable DHCP IP allocation for VMware user clusters.

        While using DHCP, manual load balancing mode is not supported. For more details, see https://cloud.google.com/anthos/clusters/docs/on-prem/latest/how-to/manual-load-balance#setting_aside_node_ip_addresses.
        """),
      action='store_true',
  )


def _ParseControlPlaneIpBlock(value):
  """Parse the given value in IP block format.

  Args:
    value: str, supports format of either IP, or 'IP hostname'.

  Returns:
    tuple: of structure (IP, hostname).

  Raises:
    exceptions.InvalidArgumentException: raise parsing error.
  """

  parsing_error = """Malformed IP block [{}].
Expect an individual IP address, or an individual IP address with an optional hostname.
Examples: --control-plane-ip-block 'netmask=255.255.255.0,gateway=10.0.0.0,ips=192.168.1.1;0.0.0.0 localhost'
""".format(value)

  if ' ' not in value:
    return (value, None)
  else:
    ip_block = value.split(' ')
    if len(ip_block) != 2:
      raise exceptions.InvalidArgumentException(
          '--control-plane-ip-block', message=parsing_error
      )
    else:
      return (ip_block[0], ip_block[1])


def _ParseStaticIpConfigIpBlock(value):
  """Parse the given value in IP block format.

  Args:
    value: str, supports either IP, IP hostname, or a CIDR range.

  Returns:
    tuple: of structure (IP, hostname).

  Raises:
    exceptions.InvalidArgumentException: raise parsing error.
  """

  parsing_error = """Malformed IP block [{}].
Expect an individual IP address, an individual IP address with an optional hostname, or a CIDR block.
Examples: ips=192.168.1.1;0.0.0.0 localhost;192.168.1.2/16
""".format(value)

  if ' ' not in value:
    return (value, None)
  else:
    ip_block = value.split(' ')
    if len(ip_block) != 2:
      raise exceptions.InvalidArgumentException(
          '--static-ip-config-ip-blocks', message=parsing_error
      )
    else:
      return (ip_block[0], ip_block[1])


def _AddVmwareStaticIpConfig(ip_configuration_mutex_group):
  """Adds flags to specify Static IP configuration.

  Args:
    ip_configuration_mutex_group: The parent group to add the flag to.
  """
  static_ip_config_from_file_help_text = """
Path of the YAML/JSON file that contains the static IP configurations, used by Anthos on VMware user cluster node pools.

Examples:

    staticIPConfig:
      ipBlocks:
      - gateway: 10.251.31.254
        netmask: 255.255.252.0
        ips:
        - hostname: hostname-1
          ip: 1.1.1.1
        - hostname: hostname-2
          ip: 2.2.2.2
        - hostname: hostname-3
          ip: 3.3.3.3
        - hostname: hostname-4
          ip: 4.4.4.4

List of supported fields in `staticIPConfig`

KEY       | VALUE                 | NOTE
--------- | --------------------  | -----------------
ipBlocks  | one or more ipBlocks  | required, mutable

List of supported fields in `ipBlocks`

KEY     | VALUE           | NOTE
------- | --------------- | -------------------
gateway | IP address      | required, immutable
netmask | IP address      | required, immutable
ips     | one or more ips | required, mutable

List of supported fields in `ips`

KEY       | VALUE       | NOTE
--------- | ----------- | -------------------
hostname  | string      | optional, immutable
ip        | IP address  | required, immutable

New `ips` fields can be added, existing `ips` fields cannot be removed or updated.
"""
  static_ip_config_mutex_group = ip_configuration_mutex_group.add_group(
      help='Static IP configuration group',
      mutex=True,
  )
  static_ip_config_mutex_group.add_argument(
      '--static-ip-config-from-file',
      help=static_ip_config_from_file_help_text,
      type=arg_parsers.YAMLFileContents(),
      hidden=True,
  )

  static_ip_config_ip_blocks_help_text = """
Static IP configurations.

Expect an individual IP address, an individual IP address with an optional hostname, or a CIDR block.

Example:

To specify two Static IP blocks,

```
$ gcloud {command}
    --static-ip-config-ip-blocks 'gateway=192.168.0.1,netmask=255.255.255.0,ips=192.168.1.1;0.0.0.0 localhost;192.168.1.2/16'
    --static-ip-config-ip-blocks 'gateway=192.168.1.1,netmask=255.255.0.0,ips=8.8.8.8;4.4.4.4'
```

Use quote around the flag value to escape semicolon in the terminal.
  """

  static_ip_config_mutex_group.add_argument(
      '--static-ip-config-ip-blocks',
      help=static_ip_config_ip_blocks_help_text,
      action='append',
      type=arg_parsers.ArgDict(
          spec={
              'gateway': str,
              'netmask': str,
              'ips': arg_parsers.ArgList(
                  element_type=_ParseStaticIpConfigIpBlock,
                  custom_delim_char=';',
              ),
          }
      ),
  )


def _AddIpConfiguration(vmware_network_config_group, for_update=False):
  """Adds flags to specify IP configuration used by the VMware User Cluster.

  Args:
    vmware_network_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  ip_configuration_mutex_group = vmware_network_config_group.add_group(
      mutex=True,
      help='IP configuration used by the VMware User Cluster',
  )
  _AddVmwareDhcpIpConfig(ip_configuration_mutex_group, for_update=for_update)
  _AddVmwareStaticIpConfig(ip_configuration_mutex_group)


def _AddVmwareHostConfig(vmware_network_config_group, for_update=False):
  """Adds flags to specify common parameters for all hosts irrespective of their IP address.

  Args:
    vmware_network_config_group: The parent group to add the flags to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    return

  vmware_host_config_group = vmware_network_config_group.add_group(
      help='Common parameters for all hosts irrespective of their IP address'
  )

  vmware_host_config_group.add_argument(
      '--dns-servers',
      metavar='DNS_SERVERS',
      type=arg_parsers.ArgList(str),
      help='DNS server IP address.',
  )
  vmware_host_config_group.add_argument(
      '--ntp-servers',
      metavar='NTP_SERVERS',
      type=arg_parsers.ArgList(str),
      help='NTP server IP address.',
  )
  vmware_host_config_group.add_argument(
      '--dns-search-domains',
      type=arg_parsers.ArgList(str),
      metavar='DNS_SEARCH_DOMAINS',
      help='DNS search domains.',
  )


def AddRequiredPlatformVersion(parser: parser_arguments.ArgumentInterceptor):
  """Adds flags to specify required platform version.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--required-platform-version',
      type=str,
      help=(
          'Platform version required for upgrading a user cluster. '
          'If the current platform version is lower than the required '
          'version, the platform version will be updated to the required '
          'version. If it is not installed in the platform, '
          'download the required version bundle.'
      ),
  )


def AddClusterAnnotations(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds a flag to specify cluster annotations.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    annotation_mutex_group = parser.add_group(mutex=True)
    surface = annotation_mutex_group
  else:
    surface = parser

  surface.add_argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Annotations on the VMware user cluster.',
  )
  if for_update:
    surface.add_argument(
        '--clear-annotations',
        action='store_true',
        help='Clear annotations on the VMware user cluster.',
    )


def AddVmwareControlPlaneNodeConfig(
    parser: parser_arguments.ArgumentInterceptor,
    for_update=False,
    release_track: base.ReleaseTrack = None,
):
  """Adds flags to specify VMware user cluster control plane node configurations.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
    release_track: base.ReleaseTrack, determine the flag scope based on release
      tracks.
  """
  vmware_control_plane_node_config_group = parser.add_group(
      help='Control plane node configurations',
  )
  vmware_control_plane_node_config_group.add_argument(
      '--cpus',
      type=int,
      help=(
          'Number of CPUs for each admin cluster node that serve as control'
          ' planes for this VMware user cluster. (default: 4 CPUs)'
      ),
  )
  vmware_control_plane_node_config_group.add_argument(
      '--memory',
      type=arg_parsers.BinarySize(default_unit='MB', type_abbr='MB'),
      help=(
          'Megabytes of memory for each admin cluster node that serves as a'
          ' control plane for this VMware User Cluster (default: 8192 MB'
          ' memory).'
      ),
  )
  if not for_update:
    vmware_control_plane_node_config_group.add_argument(
        '--replicas',
        type=int,
        help=(
            'Number of control plane nodes for this VMware user cluster.'
            ' (default: 1 replica).'
        ),
    )
  _AddVmwareAutoResizeConfig(
      vmware_control_plane_node_config_group, for_update=for_update
  )
  _AddVmwareControlPlaneVsphereConfig(
      vmware_control_plane_node_config_group, release_track=release_track
  )


def _AddVmwareAutoResizeConfig(
    vmware_control_plane_node_config_group, for_update=False
):
  """Adds flags to specify control plane auto resizing configurations.

  Args:
    vmware_control_plane_node_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  vmware_auto_resize_config_group = (
      vmware_control_plane_node_config_group.add_group(
          help='Auto resize configurations'
      )
  )
  if for_update:
    enable_auto_resize_mutex_group = vmware_auto_resize_config_group.add_group(
        mutex=True
    )
    surface = enable_auto_resize_mutex_group
  else:
    surface = vmware_auto_resize_config_group

  surface.add_argument(
      '--enable-auto-resize',
      action='store_true',
      help='Enable controle plane node auto resize.',
  )

  if for_update:
    surface.add_argument(
        '--disable-auto-resize',
        action='store_true',
        help='Disable controle plane node auto resize.',
    )


def AddVmwareAAGConfig(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds flags to specify VMware user cluster node pool anti-affinity group configurations.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  vmware_aag_config_group = parser.add_group(
      help='Anti-affinity group configurations',
  )

  if for_update:
    enable_aag_config_mutex_group = vmware_aag_config_group.add_group(
        mutex=True
    )
    surface = enable_aag_config_mutex_group
  else:
    surface = vmware_aag_config_group

  surface.add_argument(
      '--disable-aag-config',
      action='store_true',
      help=(
          'If set, spread nodes across at least three physical hosts (requires'
          ' at least three hosts). Enabled by default.'
      ),
  )
  if for_update:
    surface.add_argument(
        '--enable-aag-config',
        action='store_true',
        help='If set, enable anti-affinity group config.',
    )


def AddVmwareStorageConfig(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds flags to specify VMware storage configurations.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  vmware_storage_group = parser.add_group(help='Storage configurations')

  if for_update:
    disable_vsphere_csi_mutex_group = vmware_storage_group.add_group(mutex=True)
    surface = disable_vsphere_csi_mutex_group
  else:
    surface = vmware_storage_group

  surface.add_argument(
      '--disable-vsphere-csi',
      action='store_true',
      help=(
          'If set, vSphere CSI components are not deployed in the VMware User'
          ' Cluster. Enabled by default.'
      ),
  )
  if for_update:
    surface.add_argument(
        '--enable-vsphere-csi',
        action='store_true',
        help=(
            'If set, vSphere CSI components are deployed in the VMware User'
            ' Cluster.'
        ),
    )


def _AddEnableDataplaneV2(vmware_dataplane_v2_config_group, for_update=False):
  """Adds flags to specify enable_dataplane_v2.

  Args:
    vmware_dataplane_v2_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    return

  vmware_dataplane_v2_config_group.add_argument(
      '--enable-dataplane-v2',
      action='store_true',
      help='If set, enables Dataplane V2.',
  )


def _AddAdvancedNetworking(vmware_dataplane_v2_config_group, for_update=False):
  """Adds flags to specify advanced networking.

  Args:
    vmware_dataplane_v2_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    return

  vmware_dataplane_v2_config_group.add_argument(
      '--enable-advanced-networking',
      action='store_true',
      help=(
          'If set, enable advanced networking. Requires dataplane_v2_enabled to'
          ' be set true.'
      ),
  )


def AddVmwareDataplaneV2Config(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds flags to specify configurations for Dataplane V2, which is optimized dataplane for Kubernetes networking.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    return
  vmware_dataplane_v2_config_group = parser.add_group(
      help='Dataplane V2 configurations'
  )
  _AddEnableDataplaneV2(vmware_dataplane_v2_config_group, for_update=for_update)
  _AddAdvancedNetworking(
      vmware_dataplane_v2_config_group, for_update=for_update
  )


def AddEnableVmwareTracking(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds flags to specify vmware tracking configurations.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    return

  parser.add_argument(
      '--enable-vm-tracking',
      action='store_true',
      help='If set, enable VM tracking.',
  )


def AddVmwareAutoRepairConfig(
    parser: parser_arguments.ArgumentInterceptor, for_update=False
):
  """Adds flags to specify auto-repair configurations.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  vmware_auto_repair_config_group = parser.add_group(
      help='Auto-repair configurations'
  )

  if for_update:
    enable_auto_repair_mutex_group = vmware_auto_repair_config_group.add_group(
        mutex=True
    )
    surface = enable_auto_repair_mutex_group
  else:
    surface = vmware_auto_repair_config_group

  surface.add_argument(
      '--enable-auto-repair',
      action='store_true',
      help='If set, deploy the cluster-health-controller.',
  )
  if for_update:
    surface.add_argument(
        '--disable-auto-repair',
        action='store_true',
        help='If set, disables auto repair.',
    )


def AddAuthorization(parser: parser_arguments.ArgumentInterceptor):
  """Adds flags to specify applied and managed RBAC policy.

  Args:
    parser: The argparse parser to add the flag to.
  """
  authorization_group = parser.add_group(
      help=(
          'User cluster authorization configurations to bootstrap onto the'
          ' admin cluster'
      )
  )

  flag_help_text = """\
Users that will be granted the cluster-admin role on the cluster, providing full access to the cluster.

To add multiple users, specify one in each flag. When updating, the update command overwrites the whole grant list. Specify all existing and new users that you want to be cluster administrators.

Examples:

  $ {command}
      --admin-users alice@example.com
      --admin-users bob@example.com
"""
  authorization_group.add_argument(
      '--admin-users',
      help=flag_help_text,
      action='append',
  )


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
          'If set, the deletion of a VMware user cluster resource will succeed'
          ' even if errors occur during deletion.'
      ),
      action='store_true',
  )


def _AddVmwareControlPlaneV2Config(
    vmware_network_config_group, for_update=False
):
  """Adds a flag for control_plane_v2_config message.

  Args:
    vmware_network_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  # control plane v2 config is immutable.
  if for_update:
    return

  vmware_control_plane_v2_config_group = vmware_network_config_group.add_group(
      help='Control plane v2 mode configurations.'
  )
  help_text = """
Static IP addresses for the control plane nodes. The number of IP addresses should match the number of replicas for the control plane nodes, specified by `--replicas`.

To specify the control plane IP block,

```
$ gcloud {command}
    --control-plane-ip-block 'gateway=192.168.0.1,netmask=255.255.255.0,ips=192.168.1.1;0.0.0.0 localhost;'
```

  """
  vmware_control_plane_v2_config_group.add_argument(
      '--control-plane-ip-block',
      help=help_text,
      type=arg_parsers.ArgDict(
          spec={
              'gateway': str,
              'netmask': str,
              'ips': arg_parsers.ArgList(
                  element_type=_ParseControlPlaneIpBlock,
                  custom_delim_char=';',
              ),
          }
      ),
  )


def AddNodePoolIgnoreErrors(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for ignore_errors field.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--ignore-errors',
      help=(
          'If set, the deletion of a VMware node pool resource will succeed'
          ' even if errors occur during deletion.'
      ),
      action='store_true',
  )


def AddEnableControlPlaneV2(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for enabling_control_plane_v2 field.

  Args:
    parser: The argparse parser to add the flag to.
  """
  control_plane_v2_mutex_group = parser.add_group(
      mutex=True,
  )
  control_plane_v2_mutex_group.add_argument(
      '--enable-control-plane-v2',
      help='If set, enable control plane v2.',
      action='store_true',
  )
  control_plane_v2_mutex_group.add_argument(
      '--disable-control-plane-v2',
      help='If set, disable control plane v2.',
      action='store_true',
  )


def AddNodePoolVersion(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for on_prem_version field.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--version',
      help=(
          'Anthos version for the node pool. Defaults to the user cluster'
          ' version.'
      ),
      hidden=True,
  )


def AddUserClusterLocalName(parser: parser_arguments.ArgumentInterceptor):
  """Adds a flag for local_name field.

  Args:
    parser: The argparse parser to add the flag to.
  """
  local_name_help_text = """\
The object name of the VMware OnPremUserCluster custom resource on the
associated admin cluster. This field is used to support conflicting
resource names when enrolling existing clusters to the API. When not
provided, this field will resolve to the vmware_cluster_id. Otherwise, it
must match the object name of the VMware OnPremUserCluster custom resource.
It is not modifiable outside / beyond the  enrollment operation.
"""

  parser.add_argument(
      '--local-name',
      help=local_name_help_text,
  )


def _AddVmwareControlPlaneVsphereConfig(
    vmware_control_plane_node_config_group: parser_arguments.ArgumentInterceptor,
    release_track: base.ReleaseTrack = None,
):
  """Adds a flag for VmwareControlPlaneVsphereConfig message."""
  if release_track and release_track == base.ReleaseTrack.ALPHA:
    vmware_control_plane_node_config_group.add_argument(
        '--control-plane-vsphere-config',
        help='Vsphere-specific configurations.',
        hidden=True,
        metavar='datastore=DATASTORE,storage-policy-name=STORAGE_POLICY_NAME',
        type=arg_parsers.ArgDict(
            spec={
                'datastore': str,
                'storage-policy-name': str,
            },
        ),
    )


def _AddVmwareVsphereConfig(
    vmware_node_config_group: parser_arguments.ArgumentInterceptor,
    release_track: base.ReleaseTrack = None,
    for_update: bool = False,
):
  """Adds a flag for VmwareVsphereConfig."""
  if for_update:
    return

  # Only add to alpha track, promote to beta later.
  # The __eq__ comparison checks release_track.id so it should exclude None.
  if release_track is None or release_track != base.ReleaseTrack.ALPHA:
    return

  vmware_vsphere_config_help_text = textwrap.dedent("""\
    vSphere configurations for the node pool.

    DATASTORE is the name of the vCenter datastore.

    STORAGE_POLICY_NAME is the name of the vCenter storage policy.
    """)
  vmware_node_config_group.add_argument(
      '--vsphere-config',
      help=vmware_vsphere_config_help_text,
      hidden=True,
      type=arg_parsers.ArgDict(
          spec={
              'datastore': str,
              'storage-policy-name': str,
          }
      ),
      metavar='datastore=DATASTORE,storage-policy-name=STORAGE_POLICY_NAME',
  )


def AddUpgradePolicy(parser: parser_arguments.ArgumentInterceptor):
  upgrade_policy_group = parser.add_group(
      help='Upgrade policy for the cluster.',
  )

  upgrade_policy_group.add_argument(
      '--upgrade-policy',
      type=arg_parsers.ArgDict(
          spec={
              'control-plane-only': arg_parsers.ArgBoolean(),
          },
      ),
      help=textwrap.dedent("""\
      If not specified, control-plane-only is set to False. In the next upgrade operation, all worker node pools will be upgraded together with the control plane.

      Example:

        To upgrade the control plane only and keep worker node pools version unchanged, first specify the policy:

          ```shell
          $ {command} CLUSTER --upgrade-policy control-plane-only=True
          ```

        Then to start the upgrade operation using the specified policy, run:

          ```shell
          $ {parent_command} upgrade CLUSTER --version=VERSION
          ```

        After upgrading only the cluster control plane, to upgrade an individual node pool, run:

          ```shell
          $ {grandparent_command} node-pools update NODE_POOL --version=VERSION
          ```

      Example:

        Alternatively, to upgrade both the control plane and all worker node pools, first specify the policy:

          ```shell
          $ {command} CLUSTER --upgrade-policy control-plane-only=False
          ```

        Then to start the upgrade operation using the specified policy, run:

          ```shell
          $ {parent_command} upgrade CLUSTER --version=VERSION
          ```
      """),
  )


def AddVCenterConfig(parser: parser_arguments.ArgumentInterceptor) -> None:
  """Adds vCenterConfig flags."""
  vcenter_config_group = parser.add_group(
      help=(
          'vCenter configurations for the cluster. If not specified, it is'
          ' inherited from the admin cluster.'
      ),
  )

  vcenter_config_group.add_argument(
      '--vcenter-resource-pool',
      type=str,
      help='Name of the vCenter resource pool for the user cluster.',
  )
  vcenter_config_group.add_argument(
      '--vcenter-datastore',
      type=str,
      help='Name of the vCenter datastore for the user cluster.',
  )
  vcenter_config_group.add_argument(
      '--vcenter-datacenter',
      type=str,
      help='Name of the vCenter datacenter for the user cluster.',
  )
  vcenter_config_group.add_argument(
      '--vcenter-cluster',
      type=str,
      help='Name of the vCenter cluster for the user cluster.',
  )
  vcenter_config_group.add_argument(
      '--vcenter-folder',
      type=str,
      help='Name of the vCenter folder for the user cluster.',
  )
  vcenter_config_group.add_argument(
      '--vcenter-ca-cert-data',
      type=str,
      help=(
          'Name of the vCenter CA certificate public key for SSL verification.'
      ),
  )
  vcenter_config_group.add_argument(
      '--vcenter-storage-policy-name',
      type=str,
      help='Name of the vCenter storage policy for the user cluster.',
  )
