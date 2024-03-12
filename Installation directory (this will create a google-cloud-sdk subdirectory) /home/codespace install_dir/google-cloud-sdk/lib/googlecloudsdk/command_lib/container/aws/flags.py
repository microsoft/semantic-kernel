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
"""Helpers for flags in commands working with Anthos Multi-Cloud on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import util as api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.util.apis import arg_utils


def AddAwsRegion(parser):
  parser.add_argument(
      '--aws-region', required=True, help='AWS region to deploy the cluster.'
  )


def GetAwsRegion(args):
  return getattr(args, 'aws_region', None)


def AddVpcId(parser):
  parser.add_argument(
      '--vpc-id', required=True, help='VPC associated with the cluster.'
  )


def GetVpcId(args):
  return getattr(args, 'vpc_id', None)


def AddIamInstanceProfile(parser, kind='cluster', required=True):
  """Adds the --iam-instance-profile flag."""
  parser.add_argument(
      '--iam-instance-profile',
      required=required,
      help=(
          'Name or ARN of the IAM instance profile associated with the {}.'
          .format(kind)
      ),
  )


def GetIamInstanceProfile(args):
  return getattr(args, 'iam_instance_profile', None)


def AddInstanceType(parser, kind='control plane'):
  """Adds the --instance-type flag."""
  parser.add_argument(
      '--instance-type',
      help="AWS EC2 instance type for the {}'s nodes.".format(kind),
  )


def GetInstanceType(args):
  return getattr(args, 'instance_type', None)


def AddSpotInstanceTypes(parser, kind='node pool'):
  """Adds the --spot-instance-types flag."""
  parser.add_argument(
      '--spot-instance-types',
      type=arg_parsers.ArgList(),
      metavar='INSTANCE_TYPE',
      help=(
          "List of AWS EC2 instance types for creating a spot {}'s nodes. The"
          ' specified instance types must have the same CPU architecture, the'
          ' same number of CPUs and memory. You can use the Amazon EC2 Instance'
          ' Selector tool (https://github.com/aws/amazon-ec2-instance-selector)'
          ' to choose instance types with matching CPU and memory'
          ' configurations.'.format(kind)
      ),
  )


def AddOnDemandOrSpotInstanceType(parser, kind='node pool'):
  """Adds instance configurtion for creating node pool."""
  group = parser.add_group('Node pool instance configuration', mutex=True)
  AddInstanceType(group, kind)
  AddSpotInstanceTypes(group, kind)


def GetSpotInstanceTypes(args):
  return getattr(args, 'spot_instance_types', None)


def AddSshEC2KeyPair(parser, kind='control plane'):
  """Adds the --ssh-ec2-key-pair flag."""
  parser.add_argument(
      '--ssh-ec2-key-pair',
      help=(
          "Name of the EC2 key pair authorized to login to the {}'s nodes."
          .format(kind)
      ),
  )


def GetSshEC2KeyPair(args):
  return getattr(args, 'ssh_ec2_key_pair', None)


def AddClearSshEc2KeyPair(parser, kind):
  """Adds the --clear-ssh-ec2-key-pair flag."""
  parser.add_argument(
      '--clear-ssh-ec2-key-pair',
      action='store_true',
      default=None,
      help=(
          "Clear the EC2 key pair authorized to login to the {}'s nodes."
          .format(kind)
      ),
  )


def AddSshEC2KeyPairForUpdate(parser, kind='control plane'):
  """Adds SSH config EC2 key pair related flags for update."""
  group = parser.add_group('SSH config', mutex=True)
  AddSshEC2KeyPair(group, kind)
  AddClearSshEc2KeyPair(group, kind)


def AddRoleArn(parser, required=True):
  parser.add_argument(
      '--role-arn',
      required=required,
      help=(
          'Amazon Resource Name (ARN) of the IAM role to assume when '
          'managing AWS resources.'
      ),
  )


def GetRoleArn(args):
  return getattr(args, 'role_arn', None)


def AddRoleSessionName(parser):
  parser.add_argument(
      '--role-session-name', help='Identifier for the assumed role session.'
  )


def GetRoleSessionName(args):
  return getattr(args, 'role_session_name', None)


def AddSecurityGroupIds(parser, kind='control plane'):
  """Adds the --security-group-ids flag."""
  parser.add_argument(
      '--security-group-ids',
      type=arg_parsers.ArgList(),
      metavar='SECURITY_GROUP_ID',
      help=(
          "IDs of additional security groups to add to the {}'s nodes.".format(
              kind
          )
      ),
  )


def GetSecurityGroupIds(args):
  return getattr(args, 'security_group_ids', None) or []


def AddClearSecurityGroupIds(parser, noun):
  """Adds flag for clearing the security groups.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """

  parser.add_argument(
      '--clear-security-group-ids',
      action='store_true',
      default=None,
      help=(
          'Clear any additional security groups associated with the '
          "{}'s nodes. This does not remove the default security groups."
          .format(noun)
      ),
  )


def AddSecurityGroupFlagsForUpdate(parser, noun):
  """Adds security group related flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flags are applicable.
  """

  group = parser.add_group('Security groups', mutex=True)
  AddSecurityGroupIds(group, noun)
  AddClearSecurityGroupIds(group, noun)


def AddPerNodePoolSGRules(parser):
  """Adds --disable-per-node-pool-sg-rules flag to parser."""

  parser.add_argument(
      '--disable-per-node-pool-sg-rules',
      action='store_true',
      default=None,
      dest='per_node_pool_sg_rules_disabled',
      help=(
          'Disable the default per node pool subnet security group rules on '
          'the control plane security group. When disabled, at least one '
          'security group that allows node pools to send traffic to '
          'the control plane on ports TCP/443 and TCP/8132 must be provided.'
      ),
  )


def GetPerNodePoolSGRulesDisabled(parser):
  return getattr(parser, 'per_node_pool_sg_rules_disabled', None)


def AddPerNodePoolSGRulesForUpdate(parser):
  """Adds --disable-per-node-pool-sg-rules and --enable-per-node-pool-sg-rules flags to parser."""

  group = parser.add_group(
      'Default per node pool security group rules', mutex=True
  )
  AddPerNodePoolSGRules(group)
  group.add_argument(
      '--enable-per-node-pool-sg-rules',
      action='store_false',
      default=None,
      dest='per_node_pool_sg_rules_disabled',
      help=(
          'Enable the default per node pool subnet security group rules on '
          'the control plane security group.'
      ),
  )


def _VolumeTypeEnumMapper(prefix):
  return arg_utils.ChoiceEnumMapper(
      '--{}-volume-type'.format(prefix),
      api_util.GetMessagesModule().GoogleCloudGkemulticloudV1AwsVolumeTemplate.VolumeTypeValueValuesEnum,
      include_filter=lambda volume_type: 'UNSPECIFIED' not in volume_type,
      help_str='Type of the {} volume.'.format(prefix),
  )


def AddRootVolumeType(parser):
  _VolumeTypeEnumMapper('root').choice_arg.AddToParser(parser)


def AddMainVolumeType(parser):
  _VolumeTypeEnumMapper('main').choice_arg.AddToParser(parser)


def GetRootVolumeType(args):
  if getattr(args, 'root_volume_type', None):
    return _VolumeTypeEnumMapper('root').GetEnumForChoice(args.root_volume_type)


def GetMainVolumeType(args):
  if getattr(args, 'main_volume_type', None):
    return _VolumeTypeEnumMapper('main').GetEnumForChoice(args.main_volume_type)


def _AddVolumeIops(parser, prefix):
  parser.add_argument(
      '--{}-volume-iops'.format(prefix),
      type=int,
      help=(
          'Number of I/O operations per second (IOPS) to provision '
          'for the {} volume.'.format(prefix)
      ),
  )


def AddRootVolumeIops(parser):
  _AddVolumeIops(parser, 'root')


def GetRootVolumeIops(args):
  return getattr(args, 'root_volume_iops', None)


def AddMainVolumeIops(parser):
  _AddVolumeIops(parser, 'main')


def GetMainVolumeIops(args):
  return getattr(args, 'main_volume_iops', None)


def _AddVolumeThroughput(parser, prefix):
  parser.add_argument(
      '--{}-volume-throughput'.format(prefix),
      type=int,
      help=(
          'Throughput to provision for the {} volume, in MiB/s. Only valid '
          'if the volume type is GP3. If volume type is GP3 and throughput '
          'is not provided, it defaults to 125.'.format(prefix)
      ),
  )


def AddRootVolumeThroughput(parser):
  _AddVolumeThroughput(parser, 'root')


def GetRootVolumeThroughput(args):
  return getattr(args, 'root_volume_throughput', None)


def AddMainVolumeThroughput(parser):
  _AddVolumeThroughput(parser, 'main')


def GetMainVolumeThroughput(args):
  return getattr(args, 'main_volume_throughput', None)


def _AddKmsKeyArn(parser, prefix, target, required=False):
  parser.add_argument(
      '--{}-kms-key-arn'.format(prefix),
      required=required,
      help=(
          'Amazon Resource Name (ARN) of the AWS KMS key to encrypt the {}.'
          .format(target)
      ),
  )


def AddRootVolumeKmsKeyArn(parser):
  _AddKmsKeyArn(parser, 'root-volume', 'root volume')


def GetRootVolumeKmsKeyArn(args):
  return getattr(args, 'root_volume_kms_key_arn', None)


def AddMainVolumeKmsKeyArn(parser):
  _AddKmsKeyArn(parser, 'main-volume', 'main volume')


def GetMainVolumeKmsKeyArn(args):
  return getattr(args, 'main_volume_kms_key_arn', None)


def AddDatabaseEncryptionKmsKeyArn(parser):
  _AddKmsKeyArn(parser, 'database-encryption', 'cluster secrets', required=True)


def GetDatabaseEncryptionKmsKeyArn(args):
  return getattr(args, 'database_encryption_kms_key_arn', None)


def AddConfigEncryptionKmsKeyArn(parser, required=True):
  _AddKmsKeyArn(parser, 'config-encryption', 'user data', required=required)


def GetConfigEncryptionKmsKeyArn(args):
  return getattr(args, 'config_encryption_kms_key_arn', None)


def _TenancyEnumMapper():
  return arg_utils.ChoiceEnumMapper(
      '--instance-placement',
      api_util.GetMessagesModule().GoogleCloudGkemulticloudV1AwsInstancePlacement.TenancyValueValuesEnum,
      include_filter=lambda tenancy: 'UNSPECIFIED' not in tenancy,
      help_str='Type of the tenancy.',
  )


def AddInstancePlacement(parser):
  return _TenancyEnumMapper().choice_arg.AddToParser(parser)


def GetInstancePlacement(args):
  instance_placement = getattr(args, 'instance_placement', None)
  return (
      _TenancyEnumMapper().GetEnumForChoice(instance_placement)
      if instance_placement
      else None
  )


def AddClearProxyConfig(parser, noun):
  """Adds flag for clearing the proxy configuration.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """

  parser.add_argument(
      '--clear-proxy-config',
      action='store_true',
      default=None,
      help='Clear the proxy configuration associated with the {}.'.format(noun),
  )


def AddProxySecretArn(parser, required=False):
  parser.add_argument(
      '--proxy-secret-arn',
      required=required,
      help=(
          'ARN of the AWS Secrets Manager secret that contains a proxy '
          'configuration.'
      ),
  )


def GetProxySecretArn(args):
  return getattr(args, 'proxy_secret_arn', None)


def AddProxySecretVersionId(parser, required=False):
  parser.add_argument(
      '--proxy-secret-version-id',
      required=required,
      help=(
          'Version ID string of the AWS Secrets Manager secret that contains '
          'a proxy configuration.'
      ),
  )


def GetProxySecretVersionId(args):
  return getattr(args, 'proxy_secret_version_id', None)


def AddProxyConfig(parser):
  """Adds proxy configuration flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """

  group = parser.add_argument_group('Proxy config')
  AddProxySecretArn(group, required=True)
  AddProxySecretVersionId(group, required=True)


def AddProxyConfigForUpdate(parser, noun):
  """Adds proxy configuration flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flags are applicable.
  """

  group = parser.add_group('Proxy config', mutex=True)
  update_proxy_group = group.add_group(
      'Update existing proxy config parameters'
  )
  AddProxySecretArn(update_proxy_group)
  AddProxySecretVersionId(update_proxy_group)
  AddClearProxyConfig(group, noun)


def GetSubnetIds(args):
  return getattr(args, 'subnet_ids', None) or []


def AddAutoScalingMetricsCollection(parser):
  """Adds autoscaling metrics collection flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """

  group = parser.add_argument_group('Node pool autoscaling metrics collection')
  AddAutoscalingMetricsGranularity(group, required=True)
  AddAutoscalingMetrics(group)


def AddAutoscalingMetricsGranularity(parser, required=False):
  parser.add_argument(
      '--autoscaling-metrics-granularity',
      required=required,
      help=(
          'Frequency at which EC2 Auto Scaling sends aggregated data to '
          'AWS CloudWatch. The only valid value is "1Minute".'
      ),
  )


def GetAutoscalingMetricsGranularity(args):
  return getattr(args, 'autoscaling_metrics_granularity', None)


def AddAutoscalingMetrics(parser):
  parser.add_argument(
      '--autoscaling-metrics',
      type=arg_parsers.ArgList(),
      metavar='AUTOSCALING_METRIC',
      required=False,
      help=(
          'Autoscaling metrics to enable. For a list of valid metrics, '
          'refer to https://docs.aws.amazon.com/autoscaling/ec2/APIReference/'
          'API_EnableMetricsCollection.html. If granularity is specified '
          'but not any metrics, all metrics are enabled.'
      ),
  )


def GetAutoscalingMetrics(args):
  return getattr(args, 'autoscaling_metrics', None)


def AddAutoScalingMetricsCollectionForUpdate(parser):
  """Adds autoscaling metrics collection flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
  """

  group = parser.add_group(
      'Node pool autoscaling metrics collection', mutex=True
  )
  update_metrics_group = group.add_group(
      'Update existing cloudwatch autoscaling metrics collection parameters'
  )
  AddAutoscalingMetricsGranularity(update_metrics_group)
  AddAutoscalingMetrics(update_metrics_group)
  AddClearAutoscalingMetrics(group)


def AddClearAutoscalingMetrics(parser):
  """Adds flag for clearing the cloudwatch autoscaling metrics collection.

  Args:
    parser: The argparse.parser to add the arguments to.
  """

  parser.add_argument(
      '--clear-autoscaling-metrics',
      action='store_true',
      default=None,
      help=(
          'Clear the cloudwatch autoscaling metrics collection '
          'associated with the nodepool.'
      ),
  )
