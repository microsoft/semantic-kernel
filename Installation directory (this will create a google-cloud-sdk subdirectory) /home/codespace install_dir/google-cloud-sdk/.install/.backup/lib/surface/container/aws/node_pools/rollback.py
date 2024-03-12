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
"""Command to rollback a node pool in an Anthos cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import aws as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags

_EXAMPLES = """
To roll back a canceled or failed update in node pool named ``my-node-pool''
in a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Rollback(base.Command):
  """Rollback a node pool in an Anthos cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAwsNodePoolResourceArg(parser, 'to rollback')
    flags.AddRespectPodDisruptionBudget(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs the rollback command."""
    location = resource_args.ParseAwsNodePoolResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      node_pool_ref = resource_args.ParseAwsNodePoolResourceArg(args)
      node_pool_client = api_util.NodePoolsClient()
      message = command_util.NodePoolMessage(
          node_pool_ref.awsNodePoolsId, cluster=node_pool_ref.awsClustersId
      )
      return command_util.Rollback(
          resource_ref=node_pool_ref,
          resource_client=node_pool_client,
          message=message,
          args=args,
          kind=constants.AWS_NODEPOOL_KIND,
      )
