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
"""Command to create an Anthos cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import aws as api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import flags as aws_flags
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To create a cluster named ``my-cluster'' managed in location ``us-west1'',
run:

$ {command} my-cluster --location=us-west1 --aws-region=AWS_REGION --cluster-version=CLUSTER_VERSION --database-encryption-kms-key-arn=KMS_KEY_ARN --iam-instance-profile=IAM_INSTANCE_PROFILE --pod-address-cidr-blocks=POD_ADDRESS_CIDR_BLOCKS --role-arn=ROLE_ARN --service-address-cidr-blocks=SERVICE_ADDRESS_CIDR_BLOCKS --subnet-ids=SUBNET_ID --vpc-id=VPC_ID
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Anthos cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddAwsClusterResourceArg(parser, 'to create')

    parser.add_argument(
        '--subnet-ids',
        required=True,
        type=arg_parsers.ArgList(),
        metavar='SUBNET_ID',
        help=(
            'Subnet ID of an existing VNET to use for the cluster control'
            ' plane.'
        ),
    )

    flags.AddPodAddressCidrBlocks(parser)
    flags.AddServiceAddressCidrBlocks(parser)
    flags.AddClusterVersion(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddMainVolumeSize(parser)
    flags.AddValidateOnly(parser, 'cluster to create')
    flags.AddFleetProject(parser)
    flags.AddTags(parser, 'cluster')
    flags.AddAdminUsers(parser)
    flags.AddAdminGroups(parser)
    flags.AddDescription(parser)
    flags.AddAnnotations(parser)
    flags.AddLogging(parser)
    flags.AddMonitoringConfig(parser, True)
    flags.AddBinauthzEvaluationMode(parser)

    aws_flags.AddAwsRegion(parser)
    aws_flags.AddIamInstanceProfile(parser)
    aws_flags.AddInstanceType(parser)
    aws_flags.AddSshEC2KeyPair(parser)
    aws_flags.AddConfigEncryptionKmsKeyArn(parser)
    aws_flags.AddDatabaseEncryptionKmsKeyArn(parser)
    aws_flags.AddRoleArn(parser)
    aws_flags.AddRoleSessionName(parser)
    aws_flags.AddVpcId(parser)
    aws_flags.AddSecurityGroupIds(parser, kind='control plane')
    aws_flags.AddPerNodePoolSGRules(parser)
    aws_flags.AddRootVolumeType(parser)
    aws_flags.AddRootVolumeIops(parser)
    aws_flags.AddRootVolumeThroughput(parser)
    aws_flags.AddRootVolumeKmsKeyArn(parser)
    aws_flags.AddMainVolumeType(parser)
    aws_flags.AddMainVolumeIops(parser)
    aws_flags.AddMainVolumeThroughput(parser)
    aws_flags.AddMainVolumeKmsKeyArn(parser)
    aws_flags.AddProxyConfig(parser)

    base.ASYNC_FLAG.AddToParser(parser)

    parser.display_info.AddFormat(constants.AWS_CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the create command."""
    location = resource_args.ParseAwsClusterResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      cluster_ref = resource_args.ParseAwsClusterResourceArg(args)
      cluster_client = api_util.ClustersClient()
      message = command_util.ClusterMessage(
          cluster_ref.awsClustersId,
          action='Creating',
          kind=constants.AWS,
          region=args.aws_region,
      )
      return command_util.Create(
          resource_ref=cluster_ref,
          resource_client=cluster_client,
          args=args,
          message=message,
          kind=constants.AWS_CLUSTER_KIND,
      )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create an Anthos cluster on AWS."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    """Registers alpha track flags for this command."""
    Create.Args(parser)
    aws_flags.AddInstancePlacement(parser)
