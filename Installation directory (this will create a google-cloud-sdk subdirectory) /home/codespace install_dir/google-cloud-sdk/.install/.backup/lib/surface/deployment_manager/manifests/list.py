# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""manifests list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.calliope import base


@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class List(base.ListCommand, dm_base.DmCommand):
  """List manifests in a deployment.

  Prints a table with summary information on all manifests in the deployment.
  """

  detailed_help = {
      'EXAMPLES': """
To print out a list of manifests in a deployment, run:

  $ {command} --deployment=my-deployment

To print only the name of each manifest, run:

  $ {command} --deployment=my-deployment --simple-list
""",
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('--deployment', help='Deployment name.', required=True)
    dm_api_util.SIMPLE_LIST_FLAG.AddToParser(parser)
    parser.display_info.AddFormat('table(name, id, insertTime)')

  def Run(self, args):
    """Run 'manifests list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of manifests for the specified deployment.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    request = self.messages.DeploymentmanagerManifestsListRequest(
        project=dm_base.GetProject(),
        deployment=args.deployment,
    )
    return dm_api_util.YieldWithHttpExceptions(list_pager.YieldFromList(
        self.client.manifests, request, field='manifests',
        limit=args.limit, batch_size=args.page_size))
