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
"""Command to create a node pool in an Anthos cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import aws as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import flags as aws_flags
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To create a node pool named ``my-node-pool'' in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1 --iam-instance-profile=IAM_INSTANCE_PROFILE --node-version=NODE_VERSION --subnet-id=SUBNET_ID
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a node pool in an Anthos cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.GA):
    resource_args.AddAwsNodePoolResourceArg(parser, 'to create')
    flags.AddNodeVersion(parser)
    flags.AddSubnetID(parser, 'the node pool')
    flags.AddAutoscaling(parser)
    flags.AddMaxPodsPerNode(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddValidateOnly(parser, 'node pool to create')
    flags.AddTags(parser, 'node pool')
    flags.AddNodeLabels(parser)
    flags.AddNodeTaints(parser)
    flags.AddAnnotations(parser, 'node pool')
    flags.AddEnableAutoRepair(parser, True)
    flags.AddMaxSurgeUpdate(parser)
    flags.AddMaxUnavailableUpdate(parser, for_create=True)

    aws_flags.AddOnDemandOrSpotInstanceType(parser, kind='node pool')
    aws_flags.AddSshEC2KeyPair(parser, kind='node pool')
    aws_flags.AddIamInstanceProfile(parser, kind='node pool')
    aws_flags.AddSecurityGroupIds(parser, kind='node pool')
    aws_flags.AddRootVolumeType(parser)
    aws_flags.AddRootVolumeIops(parser)
    aws_flags.AddRootVolumeThroughput(parser)
    aws_flags.AddRootVolumeKmsKeyArn(parser)
    aws_flags.AddProxyConfig(parser)
    aws_flags.AddConfigEncryptionKmsKeyArn(parser)
    aws_flags.AddAutoScalingMetricsCollection(parser)

    base.ASYNC_FLAG.AddToParser(parser)

    parser.display_info.AddFormat(constants.AWS_NODEPOOLS_FORMAT)

  def Run(self, args):
    """Runs the create command."""
    location = resource_args.ParseAwsNodePoolResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      node_pool_ref = resource_args.ParseAwsNodePoolResourceArg(args)
      node_pool_client = api_util.NodePoolsClient()
      message = command_util.NodePoolMessage(
          node_pool_ref.awsNodePoolsId,
          action='Creating',
          cluster=node_pool_ref.awsClustersId,
      )
      return command_util.Create(
          resource_ref=node_pool_ref,
          resource_client=node_pool_client,
          args=args,
          message=message,
          kind=constants.AWS_NODEPOOL_KIND,
      )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a node pool in an Anthos cluster on AWS."""

  @staticmethod
  def Args(parser):
    """Registers alpha track flags for this command."""
    Create.Args(parser, base.ReleaseTrack.ALPHA)
    aws_flags.AddInstancePlacement(parser)
    flags.AddImageType(parser)
