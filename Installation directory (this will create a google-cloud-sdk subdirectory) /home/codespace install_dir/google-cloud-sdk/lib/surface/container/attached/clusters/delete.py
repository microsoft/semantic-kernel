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
"""Command to delete a registered AttachedCluster resource.."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import attached as api_util
from googlecloudsdk.api_lib.container.gkemulticloud import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import flags as attached_flags
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.core.console import console_io

_EXAMPLES = """
To delete an AttachedCluster resource named ``my-cluster'' managed in location
``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a registered AttachedCluster resource."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    resource_args.AddAttachedClusterResourceArg(parser, 'to delete')

    flags.AddValidateOnly(parser, 'cluster to delete')
    flags.AddAllowMissing(parser)

    attached_flags.AddIgnoreErrors(parser)

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs the delete command."""
    location = resource_args.ParseAttachedClusterResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      cluster_ref = resource_args.ParseAttachedClusterResourceArg(args)
      cluster_client = api_util.ClustersClient()
      message = command_util.ClusterMessage(
          cluster_ref.attachedClustersId, kind=constants.ATTACHED
      )
      if not args.ignore_errors:
        self._prompt_ignore_errors(args, cluster_client, cluster_ref)
      try:
        ret = command_util.Delete(
            resource_ref=cluster_ref,
            resource_client=cluster_client,
            args=args,
            message=message,
            kind=constants.ATTACHED_CLUSTER_KIND,
        )
      except waiter.OperationError as e:
        pretty_print.Info(
            'Delete cluster failed. Try re-running with `--ignore-errors`.'
        )
        raise e
      return ret

  def _prompt_ignore_errors(self, args, cluster_client, cluster_ref):
    resp = cluster_client.Get(cluster_ref)
    messages = util.GetMessagesModule()
    error_states = [
        messages.GoogleCloudGkemulticloudV1AttachedCluster.StateValueValuesEnum.ERROR,
        messages.GoogleCloudGkemulticloudV1AttachedCluster.StateValueValuesEnum.DEGRADED,
    ]
    if resp.state not in error_states:
      return
    args.ignore_errors = console_io.PromptContinue(
        message=(
            'Cluster is in ERROR or DEGRADED state. '
            'Setting --ignore-errors flag.'
        ),
        throw_if_unattended=True,
        cancel_on_no=False,
        default=False,
    )
