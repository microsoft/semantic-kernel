# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Helpers for flags in commands working with GKE Multi-cloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import util as api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties


def _ToCamelCase(name):
  """Converts hyphen-case name to CamelCase."""
  parts = name.split('-')
  return ''.join(x.title() for x in parts)


def _ToSnakeCaseUpper(name):
  """Converts hyphen-case name to SNAKE_CASE."""
  parts = name.split('-')
  return '_'.join(parts).upper()


def _ToHyphenCase(name):
  """Converts SNAKE_CASE to hyphen-case."""
  parts = name.split('_')
  return '-'.join(parts).lower()


def _InvalidValueError(value, flag, detail):
  return arg_parsers.ArgumentTypeError(
      'Invalid value [{}] for argument {}. {}'.format(value, flag, detail)
  )


_TAINT_EFFECT_ENUM_MAPPER = arg_utils.ChoiceEnumMapper(
    '--node-taints',
    api_util.GetMessagesModule().GoogleCloudGkemulticloudV1NodeTaint.EffectValueValuesEnum,
    include_filter=lambda effect: 'UNSPECIFIED' not in effect,
)

_TAINT_FORMAT_HELP = 'Node taint is of format key=value:effect.'

_TAINT_EFFECT_HELP = 'Effect must be one of: {}.'.format(
    ', '.join([_ToCamelCase(e) for e in _TAINT_EFFECT_ENUM_MAPPER.choices])
)

_REPLICAPLACEMENT_FORMAT_HELP = (
    'Replica placement is of format subnetid:zone, for example subnetid12345:1'
)

_LOGGING_CHOICES = [constants.SYSTEM, constants.WORKLOAD]

_ALLOW_DISABLE_LOGGING_CHOICES = [
    constants.NONE,
    constants.SYSTEM,
    constants.WORKLOAD,
]

_BINAUTHZ_EVAL_MODE_ENUM_MAPPER = arg_utils.ChoiceEnumMapper(
    '--binauthz-evaluation-mode',
    api_util.GetMessagesModule().GoogleCloudGkemulticloudV1BinaryAuthorization.EvaluationModeValueValuesEnum,
    include_filter=lambda mode: 'UNSPECIFIED' not in mode,
)


def AddPodAddressCidrBlocks(parser):
  """Adds the --pod-address-cidr-blocks flag."""
  parser.add_argument(
      '--pod-address-cidr-blocks',
      required=True,
      help=(
          'IP address range for the pods in this cluster in CIDR '
          'notation (e.g. 10.0.0.0/8).'
      ),
  )


def GetPodAddressCidrBlocks(args):
  """Gets the value of --pod-address-cidr-blocks flag."""
  cidr_blocks = getattr(args, 'pod_address_cidr_blocks', None)
  return [cidr_blocks] if cidr_blocks else []


def AddServiceAddressCidrBlocks(parser):
  """Add the --service-address-cidr-blocks flag."""
  parser.add_argument(
      '--service-address-cidr-blocks',
      required=True,
      help=(
          'IP address range for the services IPs in CIDR notation '
          '(e.g. 10.0.0.0/8).'
      ),
  )


def GetServiceAddressCidrBlocks(args):
  """Gets the value of --service-address-cidr-blocks flag."""
  cidr_blocks = getattr(args, 'service_address_cidr_blocks', None)
  return [cidr_blocks] if cidr_blocks else []


def AddSubnetID(parser, help_text, required=True):
  """Add the --subnet-id flag."""
  parser.add_argument(
      '--subnet-id',
      required=required,
      help='Subnet ID of an existing VNET to use for {}.'.format(help_text),
  )


def GetSubnetID(args):
  return getattr(args, 'subnet_id', None)


def AddOutputFile(parser, help_action):
  """Add an output file argument.

  Args:
    parser: The argparse.parser to add the output file argument to.
    help_action: str, describes the action of what will be stored.
  """
  parser.add_argument(
      '--output-file', help='Path to the output file {}.'.format(help_action)
  )


def AddValidateOnly(parser, help_action):
  """Add the --validate-only argument.

  Args:
    parser: The argparse.parser to add the argument to.
    help_action: str, describes the action that will be validated.
  """
  parser.add_argument(
      '--validate-only',
      action='store_true',
      help="Validate the {}, but don't actually perform it.".format(
          help_action
      ),
  )


def GetValidateOnly(args):
  return getattr(args, 'validate_only', None)


def AddEnableAutoRepair(parser, for_create=False):
  help_text = """\
Enable node autorepair feature for a node pool. Use --no-enable-autorepair to disable.

  $ {command} --enable-autorepair
"""
  if for_create:
    help_text += """
Node autorepair is disabled by default.
"""
  parser.add_argument(
      '--enable-autorepair', action='store_true', default=None, help=help_text
  )


def GetAutoRepair(args):
  return getattr(args, 'enable_autorepair', None)


def AddClusterVersion(parser, required=True):
  parser.add_argument(
      '--cluster-version',
      required=required,
      help='Kubernetes version to use for the cluster.',
  )


def GetClusterVersion(args):
  return getattr(args, 'cluster_version', None)


def AddDescription(parser, required=False):
  parser.add_argument(
      '--description', required=required, help='Description for the cluster.'
  )


def GetDescription(args):
  return getattr(args, 'description', None)


def AddClearDescription(parser):
  """Adds the --clear-description flag.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--clear-description',
      action='store_true',
      default=None,
      help='Clear the description for the cluster.',
  )


def AddDescriptionForUpdate(parser):
  """Adds description related flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  group = parser.add_group('Description', mutex=True)
  AddDescription(group)
  AddClearDescription(group)


def AddAnnotations(parser, noun='cluster'):
  parser.add_argument(
      '--annotations',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='ANNOTATION',
      help='Annotations for the {}.'.format(noun),
  )


def AddClearAnnotations(parser, noun):
  """Adds flag for clearing the annotations.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """
  parser.add_argument(
      '--clear-annotations',
      action='store_true',
      default=None,
      help='Clear the annotations for the {}.'.format(noun),
  )


def GetAnnotations(args):
  return getattr(args, 'annotations', None) or {}


def AddAnnotationsForUpdate(parser, noun):
  """Adds annotations related flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """
  group = parser.add_group('Annotations', mutex=True)
  AddAnnotations(group, noun)
  AddClearAnnotations(group, noun)


def AddNodeVersion(parser, required=True):
  parser.add_argument(
      '--node-version',
      required=required,
      help='Kubernetes version to use for the node pool.',
  )


def GetNodeVersion(args):
  return getattr(args, 'node_version', None)


def AddAutoscaling(parser, required=True):
  """Adds node pool autoscaling flags.

  Args:
    parser: The argparse.parser to add the arguments to.
    required: bool, whether autoscaling flags are required.
  """

  group = parser.add_argument_group('Node pool autoscaling', required=required)
  group.add_argument(
      '--min-nodes',
      required=required,
      type=int,
      help='Minimum number of nodes in the node pool.',
  )
  group.add_argument(
      '--max-nodes',
      required=required,
      type=int,
      help='Maximum number of nodes in the node pool.',
  )


def GetAutoscalingParams(args):
  min_nodes = 0
  max_nodes = 0
  min_nodes = args.min_nodes
  max_nodes = args.max_nodes

  return (min_nodes, max_nodes)


def GetMinNodes(args):
  return getattr(args, 'min_nodes', None)


def GetMaxNodes(args):
  return getattr(args, 'max_nodes', None)


def AddMaxPodsPerNode(parser):
  parser.add_argument(
      '--max-pods-per-node',
      type=int,
      help='Maximum number of pods per node.',
      required=True,
  )


def GetMaxPodsPerNode(args):
  return getattr(args, 'max_pods_per_node', None)


def AddAzureAvailabilityZone(parser):
  parser.add_argument(
      '--azure-availability-zone',
      help='Azure availability zone where the node pool will be created.',
  )


def GetAzureAvailabilityZone(args):
  return getattr(args, 'azure_availability_zone', None)


def AddVMSize(parser):
  parser.add_argument(
      '--vm-size', help='Azure Virtual Machine Size (e.g. Standard_DS1_v).'
  )


def GetVMSize(args):
  return getattr(args, 'vm_size', None)


def AddSSHPublicKey(parser, required=True):
  parser.add_argument(
      '--ssh-public-key',
      required=required,
      help='SSH public key to use for authentication.',
  )


def GetSSHPublicKey(args):
  return getattr(args, 'ssh_public_key', None)


def AddRootVolumeSize(parser):
  parser.add_argument(
      '--root-volume-size',
      type=arg_parsers.BinarySize(
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB'],
          default_unit='Gi',
      ),
      help=(
          'Size of the root volume. The value must be a whole number followed'
          ' by a size unit of `GB` for gigabyte, or `TB` for terabyte. If no'
          ' size unit is specified, GB is assumed.'
      ),
  )


def GetRootVolumeSize(args):
  size = getattr(args, 'root_volume_size', None)
  if not size:
    return None

  # Volume sizes are currently in GB, argument is in B.
  return int(size) >> 30


def AddMainVolumeSize(parser):
  parser.add_argument(
      '--main-volume-size',
      type=arg_parsers.BinarySize(
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB'],
          default_unit='Gi',
      ),
      help=(
          'Size of the main volume. The value must be a whole number followed'
          ' by a size unit of `GB` for gigabyte, or `TB` for terabyte. If no'
          ' size unit is specified, GB is assumed.'
      ),
  )


def GetMainVolumeSize(args):
  size = getattr(args, 'main_volume_size', None)
  if not size:
    return None

  # Volume sizes are currently in GB, argument is in B.
  return int(size) >> 30


def AddTags(parser, noun):
  help_text = """\
  Applies the given tags (comma separated) on the {0}. Example:

    $ {{command}} EXAMPLE_{1} --tags=tag1=one,tag2=two
  """.format(noun, noun.replace(' ', '_').upper())

  parser.add_argument(
      '--tags',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='TAG',
      help=help_text,
  )


def AddClearTags(parser, noun):
  """Adds flag for clearing the tags.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """

  parser.add_argument(
      '--clear-tags',
      action='store_true',
      default=None,
      help="Clear any tags associated with the {}'s nodes. ".format(noun),
  )


def AddTagsForUpdate(parser, noun):
  """Adds tags related flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flags are applicable.
  """
  group = parser.add_group('Tags', mutex=True)
  AddTags(group, noun)
  AddClearTags(group, noun)


def GetTags(args):
  return getattr(args, 'tags', None) or {}


def AddDatabaseEncryption(parser):
  """Adds database encryption flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--database-encryption-key-id',
      help=(
          'URL the of the Azure Key Vault key (with its version) '
          'to use to encrypt / decrypt cluster secrets.'
      ),
  )


def GetDatabaseEncryptionKeyId(args):
  return getattr(args, 'database_encryption_key_id', None)


def AddConfigEncryption(parser):
  """Adds config encryption flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--config-encryption-key-id',
      help=(
          'URL the of the Azure Key Vault key (with its version) '
          'to use to encrypt / decrypt config data.'
      ),
  )
  parser.add_argument(
      '--config-encryption-public-key',
      help=(
          'RSA key of the Azure Key Vault public key to use for encrypting '
          'config data.'
      ),
  )


def GetConfigEncryptionKeyId(args):
  return getattr(args, 'config_encryption_key_id', None)


def GetConfigEncryptionPublicKey(args):
  return getattr(args, 'config_encryption_public_key', None)


def AddNodeLabels(parser):
  """Adds the --node-labels flag."""
  parser.add_argument(
      '--node-labels',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='NODE_LABEL',
      help="Labels assigned to the node pool's nodes.",
  )


def GetNodeLabels(args):
  return getattr(args, 'node_labels', None) or {}


def AddClearNodeLabels(parser):
  """Adds the --clear-node-labels flag."""
  parser.add_argument(
      '--clear-node-labels',
      action='store_true',
      default=None,
      help="Clear the labels assigned to the node pool's nodes.",
  )


def AddNodeLabelsForUpdate(parser):
  """Adds node labels related flags for update."""
  group = parser.add_group('Node labels', mutex=True)
  AddNodeLabels(group)
  AddClearNodeLabels(group)


def _ValidateNodeTaintFormat(taint):
  """Validates the node taint format.

  Node taint is of format key=value:effect.

  Args:
    taint: Node taint.

  Returns:
    The node taint value and effect if the format is valid.

  Raises:
    ArgumentError: If the node taint format is invalid.
  """
  strs = taint.split(':')
  if len(strs) != 2:
    raise _InvalidValueError(taint, '--node-taints', _TAINT_FORMAT_HELP)
  value, effect = strs[0], strs[1]
  return value, effect


def _ValidateNodeTaint(taint):
  """Validates the node taint.

  Node taint is of format key=value:effect. Valid values for effect include
  NoExecute, NoSchedule, PreferNoSchedule.

  Args:
    taint: Node taint.

  Returns:
    The node taint if it is valid.

  Raises:
    ArgumentError: If the node taint is invalid.
  """
  unused_value, effect = _ValidateNodeTaintFormat(taint)
  effects = [_ToCamelCase(e) for e in _TAINT_EFFECT_ENUM_MAPPER.choices]
  if effect not in effects:
    raise _InvalidValueError(effect, '--node-taints', _TAINT_EFFECT_HELP)
  return taint


def AddNodeTaints(parser):
  parser.add_argument(
      '--node-taints',
      type=arg_parsers.ArgDict(min_length=1, value_type=_ValidateNodeTaint),
      metavar='NODE_TAINT',
      help=(
          'Taints assigned to nodes of the node pool. {} {}'.format(
              _TAINT_FORMAT_HELP, _TAINT_EFFECT_HELP
          )
      ),
  )


def GetNodeTaints(args):
  """Gets node taint objects from the arguments.

  Args:
    args: Arguments parsed from the command.

  Returns:
    The list of node taint objects.

  Raises:
    ArgumentError: If the node taint format is invalid.
  """
  taints = []
  taint_effect_map = {
      _ToCamelCase(e): e for e in _TAINT_EFFECT_ENUM_MAPPER.choices
  }
  node_taints = getattr(args, 'node_taints', None)
  if node_taints:
    for k, v in node_taints.items():
      value, effect = _ValidateNodeTaintFormat(v)
      effect = taint_effect_map[effect]
      effect = _TAINT_EFFECT_ENUM_MAPPER.GetEnumForChoice(effect)
      taint = api_util.GetMessagesModule().GoogleCloudGkemulticloudV1NodeTaint(
          key=k, value=value, effect=effect
      )
      taints.append(taint)
  return taints


def _ReplicaPlacementStrToObject(replicaplacement):
  """Converts a colon-delimited string to a GoogleCloudGkemulticloudV1ReplicaPlacement instance.

  Replica placement is of format subnetid:zone.

  Args:
    replicaplacement: Replica placement.

  Returns:
    A GoogleCloudGkemulticloudV1ReplicaPlacement instance.

  Raises:
    ArgumentError: If the Replica placement format is invalid.
  """
  strs = replicaplacement.split(':')
  if len(strs) != 2:
    raise _InvalidValueError(
        replicaplacement, '--replica-placements', _REPLICAPLACEMENT_FORMAT_HELP
    )
  subnetid, zone = strs[0], strs[1]
  return (
      api_util.GetMessagesModule().GoogleCloudGkemulticloudV1ReplicaPlacement(
          azureAvailabilityZone=zone, subnetId=subnetid
      )
  )


def AddReplicaPlacements(parser):
  parser.add_argument(
      '--replica-placements',
      type=arg_parsers.ArgList(element_type=_ReplicaPlacementStrToObject),
      metavar='REPLICA_PLACEMENT',
      help=(
          'Placement info for the control plane replicas. {}'.format(
              _REPLICAPLACEMENT_FORMAT_HELP
          )
      ),
  )


def GetReplicaPlacements(args):
  replica_placements = getattr(args, 'replica_placements', None)
  return replica_placements if replica_placements else []


def AddAuthProviderCmdPath(parser):
  parser.add_argument(
      '--auth-provider-cmd-path',
      hidden=True,
      help='Path to the executable for the auth provider field in kubeconfig.',
  )


def AddProxyConfig(parser):
  """Add proxy configuration flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """

  group = parser.add_argument_group('Proxy config')
  group.add_argument(
      '--proxy-resource-group-id',
      required=True,
      help='The ARM ID the of the resource group containing proxy keyvault.',
  )
  group.add_argument(
      '--proxy-secret-id',
      required=True,
      help='The URL the of the proxy setting secret with its version.',
  )


def GetProxyResourceGroupId(args):
  return getattr(args, 'proxy_resource_group_id', None)


def GetProxySecretId(args):
  return getattr(args, 'proxy_secret_id', None)


def AddFleetProject(parser):
  parser.add_argument(
      '--fleet-project',
      type=arg_parsers.CustomFunctionValidator(
          project_util.ValidateProjectIdentifier,
          '--fleet-project must be a valid project ID or project number.',
      ),
      required=True,
      help=(
          'ID or number of the Fleet host project where the cluster is'
          ' registered.'
      ),
  )


def GetFleetProject(args):
  """Gets and parses the fleet project argument.

  Project ID if specified is converted to project number. The parsed fleet
  project has format projects/<project-number>.

  Args:
    args: Arguments parsed from the command.

  Returns:
    The fleet project in format projects/<project-number>
    or None if the fleet projectnot is not specified.
  """
  p = getattr(args, 'fleet_project', None)
  if not p:
    return None
  if not p.isdigit():
    return 'projects/{}'.format(project_util.GetProjectNumber(p))
  return 'projects/{}'.format(p)


def AddPrivateEndpoint(parser):
  parser.add_argument(
      '--private-endpoint',
      default=False,
      action='store_true',
      help='If set, use private VPC for authentication.',
  )


def AddExecCredential(parser):
  parser.add_argument(
      '--exec-credential',
      default=False,
      action='store_true',
      help='If set, format access token as a Kubernetes execCredential object.',
  )


def AddAdminUsers(parser, create=True):
  help_txt = 'Users that can perform operations as a cluster administrator.'
  if create:
    help_txt += ' If not specified, the value of property core/account is used.'
  parser.add_argument(
      '--admin-users',
      type=arg_parsers.ArgList(min_length=1),
      metavar='USER',
      help=help_txt,
  )


def GetAdminUsers(args):
  if not hasattr(args, 'admin_users'):
    return None
  if args.admin_users:
    return args.admin_users
  # Default to core/account property if not specified.
  return [properties.VALUES.core.account.GetOrFail()]


def AddAdminGroupsForUpdate(parser):
  """Adds admin group configuration flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
  """

  group = parser.add_group('Admin groups', mutex=True)
  AddAdminGroups(group)
  AddClearAdminGroups(group)


def AddAdminGroups(parser):
  help_txt = """
Groups of users that can perform operations as a cluster administrator.
"""

  parser.add_argument(
      '--admin-groups',
      type=arg_parsers.ArgList(),
      metavar='GROUP',
      required=False,
      help=help_txt,
  )


def AddClearAdminGroups(parser):
  """Adds the --clear-admin-groups.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--clear-admin-groups',
      action='store_true',
      default=None,
      help='Clear the admin groups associated with the cluster',
  )


def GetAdminGroups(args):
  if not hasattr(args, 'admin_groups'):
    return None
  if args.admin_groups:
    return args.admin_groups
  return None


def AddLogging(parser, allow_disabled=False):
  """Adds the --logging flag."""
  help_text = """
Set the components that have logging enabled.

Examples:

  $ {command} --logging=SYSTEM
  $ {command} --logging=SYSTEM,WORKLOAD"""

  logging_choices = []
  if allow_disabled:
    logging_choices = _ALLOW_DISABLE_LOGGING_CHOICES
    help_text += """
  $ {command} --logging=NONE
"""
  else:
    logging_choices = _LOGGING_CHOICES

  parser.add_argument(
      '--logging',
      type=arg_parsers.ArgList(min_length=1, choices=logging_choices),
      metavar='COMPONENT',
      help=help_text,
  )


def GetLogging(args, allow_disabled=False):
  """Parses and validates the value of the --logging flag.

  Args:
    args: Arguments parsed from the command.
    allow_disabled: If disabling logging is allowed for this cluster.

  Returns:
    The logging config object as GoogleCloudGkemulticloudV1LoggingConfig.

  Raises:
    ArgumentError: If the value of the --logging flag is invalid.
  """
  logging = getattr(args, 'logging', None)
  if not logging:
    return None

  if constants.NONE in logging and (
      constants.SYSTEM in logging or constants.WORKLOAD in logging
  ):
    raise _InvalidValueError(
        ','.join(logging),
        '--logging',
        'Invalid logging config. NONE is not supported with SYSTEM or'
        ' WORKLOAD.',
    )

  messages = api_util.GetMessagesModule()
  config = messages.GoogleCloudGkemulticloudV1LoggingComponentConfig()
  enum = config.EnableComponentsValueListEntryValuesEnum

  if constants.NONE in logging:
    if allow_disabled:
      return messages.GoogleCloudGkemulticloudV1LoggingConfig(
          componentConfig=config
      )
    else:
      raise _InvalidValueError(
          ','.join(logging),
          '--logging',
          'Invalid logging config. NONE is not supported.',
      )

  if constants.SYSTEM not in logging:
    raise _InvalidValueError(
        ','.join(logging),
        '--logging',
        'Must include SYSTEM logging if any logging is enabled.',
    )
  if constants.SYSTEM in logging:
    config.enableComponents.append(enum.SYSTEM_COMPONENTS)
  if constants.WORKLOAD in logging:
    config.enableComponents.append(enum.WORKLOADS)
  return messages.GoogleCloudGkemulticloudV1LoggingConfig(
      componentConfig=config
  )


def AddImageType(parser):
  """Adds the --image-type flag."""
  help_text = """
Set the OS image type to use on node pool instances.

Examples:

  $ {command} --image-type=windows
  $ {command} --image-type=ubuntu
"""
  parser.add_argument('--image-type', help=help_text)


def GetImageType(args):
  return getattr(args, 'image_type', None)


def AddAzureRegion(parser):
  parser.add_argument(
      '--azure-region',
      required=True,
      help=(
          'Azure location to deploy the cluster. '
          'Refer to your Azure subscription for available locations.'
      ),
  )


def GetAzureRegion(args):
  return getattr(args, 'azure_region', None)


def AddResourceGroupId(parser):
  parser.add_argument(
      '--resource-group-id',
      required=True,
      help='ID of the Azure Resource Group to associate the cluster with.',
  )


def GetResourceGroupId(args):
  return getattr(args, 'resource_group_id', None)


def AddVnetId(parser):
  parser.add_argument(
      '--vnet-id',
      required=True,
      help='ID of the Azure Virtual Network to associate with the cluster.',
  )


def GetVnetId(args):
  return getattr(args, 'vnet_id', None)


def AddServiceLoadBalancerSubnetId(parser):
  parser.add_argument(
      '--service-load-balancer-subnet-id',
      help=(
          'ARM ID of the subnet where Kubernetes private service type '
          'load balancers are deployed, when the Service lacks a subnet '
          'annotation.'
      ),
  )


def GetServiceLoadBalancerSubnetId(args):
  return getattr(args, 'service_load_balancer_subnet_id', None)


def AddEndpointSubnetId(parser):
  parser.add_argument(
      '--endpoint-subnet-id',
      help=(
          'ARM ID of the subnet where the control plane load balancer '
          'is deployed. When unspecified, it defaults to the control '
          'plane subnet ID.'
      ),
  )


def GetEndpointSubnetId(args):
  return getattr(args, 'endpoint_subnet_id', None)


def AddAzureServicesAuthentication(auth_config_group, create=True):
  """Adds --azure-tenant-id and --azure-application-id flags."""
  group = auth_config_group.add_argument_group('Azure services authentication')
  group.add_argument(
      '--azure-tenant-id',
      required=create,
      help='ID of the Azure Tenant to manage Azure resources.',
  )
  group.add_argument(
      '--azure-application-id',
      required=create,
      help='ID of the Azure Application to manage Azure resources.',
  )
  if not create:
    AddClearClient(group)


def AddClearClient(parser):
  """Adds the --clear-client flag.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--clear-client',
      action='store_true',
      default=None,
      help=(
          'Clear the Azure client. This flag is required when updating to use '
          'Azure workload identity federation from Azure client to manage '
          ' Azure resources.'
      ),
  )


def GetAzureTenantID(args):
  return getattr(args, 'azure_tenant_id', None)


def GetAzureApplicationID(args):
  return getattr(args, 'azure_application_id', None)


def AddMonitoringConfig(parser, for_create=False):
  """Adds --enable-managed-prometheus and --disable-managed-prometheus flags to parser."""
  enable_help_text = """
  Enables managed collection for Managed Service for Prometheus in the cluster.

  See https://cloud.google.com/stackdriver/docs/managed-prometheus/setup-managed#enable-mgdcoll-gke
  for more info.

  Enabled by default for cluster versions 1.27 or greater,
  use --no-enable-managed-prometheus to disable.
  """
  if for_create:
    parser.add_argument(
        '--enable-managed-prometheus',
        action='store_true',
        default=None,
        help=enable_help_text,
    )
  else:
    group = parser.add_group('Monitoring Config', mutex=True)
    group.add_argument(
        '--disable-managed-prometheus',
        action='store_true',
        default=None,
        help='Disable managed collection for Managed Service for Prometheus.',
    )
    group.add_argument(
        '--enable-managed-prometheus',
        action='store_true',
        default=None,
        help='Enable managed collection for Managed Service for Prometheus.',
    )


def GetMonitoringConfig(args):
  """Parses and validates the value of the managed prometheus config flags.

  Args:
    args: Arguments parsed from the command.

  Returns:
    The monitoring config object as GoogleCloudGkemulticloudV1MonitoringConfig.
    None if enable_managed_prometheus is None.
  """
  enabled_prometheus = getattr(args, 'enable_managed_prometheus', None)
  disabled_prometheus = getattr(args, 'disable_managed_prometheus', None)

  messages = api_util.GetMessagesModule()
  config = messages.GoogleCloudGkemulticloudV1ManagedPrometheusConfig()
  if enabled_prometheus:
    config.enabled = True
  elif disabled_prometheus:
    config.enabled = False
  else:
    return None
  return messages.GoogleCloudGkemulticloudV1MonitoringConfig(
      managedPrometheusConfig=config
  )


def AddAllowMissing(parser):
  help_txt = """Allow idempotent deletion of cluster.
  The request will still succeed in case the cluster does not exist.
  """
  parser.add_argument('--allow-missing', action='store_true', help=help_txt)


def GetAllowMissing(args):
  return getattr(args, 'allow_missing', None)


def AddBinauthzEvaluationMode(parser):
  """Adds --binauthz-evaluation-mode flag to parser."""
  parser.add_argument(
      '--binauthz-evaluation-mode',
      choices=[
          _ToSnakeCaseUpper(c) for c in _BINAUTHZ_EVAL_MODE_ENUM_MAPPER.choices
      ],
      default=None,
      help='Set Binary Authorization evaluation mode for this cluster.',
  )


def GetBinauthzEvaluationMode(args):
  evaluation_mode = getattr(args, 'binauthz_evaluation_mode', None)
  if evaluation_mode is None:
    return None
  return _BINAUTHZ_EVAL_MODE_ENUM_MAPPER.GetEnumForChoice(
      _ToHyphenCase(evaluation_mode)
  )


def AddMaxSurgeUpdate(parser):
  """Adds --max-surge-update flag to parser."""
  help_text = """\
Maximum number of extra (surge) nodes to be created beyond the current size of
the node pool during its update process. Use --max-unavailable-update as well,
if needed, to control the overall surge settings.

To create an extra node each time the node pool is rolling updated, run:

  $ {command} --max-surge-update=1 --max-unavailable-update=0
"""
  parser.add_argument(
      '--max-surge-update', type=int, default=None, help=help_text
  )


def GetMaxSurgeUpdate(args):
  return getattr(args, 'max_surge_update', None)


def AddMaxUnavailableUpdate(parser, for_create=False):
  """Adds --max-unavailable-update flag to parser."""
  if for_create:
    help_text = """\
Maximum number of nodes that can be simultaneously unavailable during this node
pool's update process. Use --max-surge-update as well, if needed, to control the
overall surge settings.

To update 3 nodes in parallel (1 + 2), but keep at least 4 nodes (6 - 2)
available each time the node pool is rolling updated, run:

  $ {command} --min-nodes=6 --max-surge-update=1 --max-unavailable-update=2
"""
  else:
    help_text = """\
Maximum number of nodes that can be simultaneously unavailable during this node
pool's update process. Use --max-surge-update as well, if needed, to control the
overall surge settings.

To modify a node pool with 6 nodes such that, 3 nodes are updated in parallel
(1 + 2), but keep at least 4 nodes (6 - 2) available each time this
node pool is rolling updated, run:

  $ {command} --max-surge-update=1 --max-unavailable-update=2
"""
  parser.add_argument(
      '--max-unavailable-update', type=int, default=None, help=help_text
  )


def GetMaxUnavailableUpdate(args):
  return getattr(args, 'max_unavailable_update', None)


def AddRespectPodDisruptionBudget(parser):
  """Adds --respect-pdb flag to parser."""

  help_text = """\
Indicates whether the node pool rollback should respect pod disruption budget.
"""

  parser.add_argument(
      '--respect-pdb',
      default=False,
      action='store_true',
      help=help_text,
  )


def GetRespectPodDisruptionBudget(args):
  return getattr(args, 'respect_pdb', None)
