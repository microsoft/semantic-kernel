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

"""resources list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import alpha_flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class List(base.ListCommand, dm_base.DmCommand):
  """List resources in a deployment.

  Prints a table with summary information on all resources in the deployment.
  """

  detailed_help = {
      'EXAMPLES': """
To print out a list of resources in the deployment with some summary information about each, run:

  $ {command} --deployment=my-deployment

To print only the name of each resource, run:

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
    dm_api_util.SIMPLE_LIST_FLAG.AddToParser(parser)
    parser.display_info.AddFormat("""
          table(
            name,
            type:wrap,
            update.state.yesno(no="COMPLETED"),
            update.error.errors.group(code),
            update.intent
          )
    """)

  def Run(self, args):
    """Run 'resources list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of resources for the specified deployment.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    request = self.messages.DeploymentmanagerResourcesListRequest(
        project=dm_base.GetProject(),
        deployment=args.deployment,
    )
    return dm_api_util.YieldWithHttpExceptions(
        list_pager.YieldFromList(self.client.resources,
                                 request,
                                 field='resources',
                                 limit=args.limit,
                                 batch_size=args.page_size))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.ALPHA)
class ListAlpha(List):
  """List resources in a deployment.

  Prints a table with summary information on all resources in the deployment.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    dm_api_util.SIMPLE_LIST_FLAG.AddToParser(parser)

  def _YieldPrintableResourcesOnErrors(self, args):
    request = self.messages.DeploymentmanagerResourcesListRequest(
        project=dm_base.GetProject(),
        deployment=args.deployment,
    )

    paginated_resources = dm_api_util.YieldWithHttpExceptions(
        list_pager.YieldFromList(
            self.client.resources,
            request,
            field='resources',
            limit=args.limit,
            batch_size=args.page_size))
    for resource in paginated_resources:
      yield resource

  def _isDeploymentInPreview(self, args):
    deployment = dm_api_util.FetchDeployment(self.client, self.messages,
                                             dm_base.GetProject(),
                                             args.deployment)
    if deployment.update:
      return True
    return False

  def Run(self, args):
    """Run 'resources list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of resources for the specified deployment.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """

    if args.IsSpecified('format'):
      super(ListAlpha, self).Run(args)
    elif self._isDeploymentInPreview(args):
      args.format = alpha_flags.LIST_PREVIEWED_RESOURCES_FORMAT
    else:
      args.format = alpha_flags.LIST_RESOURCES_FORMAT
    return dm_api_util.YieldWithHttpExceptions(
        self._YieldPrintableResourcesOnErrors(args))
