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
"""'vmware clusters delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.clusters import ClustersClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete a cluster in a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To delete a cluster called `my-cluster` in private cloud `my-private-cloud` and zone `us-west2-a`, run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --private-cloud=my-private-cloud

            Or:

            $ {command} my-cluster --private-cloud=my-private-cloud

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Google Cloud VMware Engine cluster."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = ClustersClient()
    is_async = args.async_
    operation = client.Delete(cluster)
    if is_async:
      log.DeletedResource(operation.name, kind='cluster', is_async=True)
      return operation

    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for cluster [{}] to be deleted'.format(
            cluster.RelativeName()),
        has_result=False)
