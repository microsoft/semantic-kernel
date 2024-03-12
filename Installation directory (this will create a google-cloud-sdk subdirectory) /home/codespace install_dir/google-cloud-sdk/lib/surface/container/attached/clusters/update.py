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
"""Command to update an Attached cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import attached as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import flags as attached_flags
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To update a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1 --description=testcluster
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an Attached cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAttachedClusterResourceArg(parser, 'to update')
    flags.AddDescription(parser, required=False)
    flags.AddClearDescription(parser)
    flags.AddAnnotations(parser)
    flags.AddValidateOnly(parser, 'update of the cluster')
    flags.AddLogging(parser, True)
    flags.AddMonitoringConfig(parser)
    flags.AddBinauthzEvaluationMode(parser)
    flags.AddAdminGroupsForUpdate(parser)

    attached_flags.AddAdminUsersForUpdate(parser)
    attached_flags.AddPlatformVersion(parser, required=False)
    attached_flags.AddProxyConfig(parser)

    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(constants.ATTACHED_CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the update command."""
    location = resource_args.ParseAttachedClusterResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      cluster_ref = resource_args.ParseAttachedClusterResourceArg(args)
      cluster_client = api_util.ClustersClient()
      message = command_util.ClusterMessage(
          cluster_ref.attachedClustersId, action='Updating'
      )
      return command_util.Update(
          resource_ref=cluster_ref,
          resource_client=cluster_client,
          args=args,
          message=message,
          kind=constants.ATTACHED_CLUSTER_KIND,
      )
