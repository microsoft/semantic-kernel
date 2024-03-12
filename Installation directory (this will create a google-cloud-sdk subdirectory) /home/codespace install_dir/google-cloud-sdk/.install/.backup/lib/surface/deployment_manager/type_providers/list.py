# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""type-providers list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class List(base.ListCommand, dm_base.DmCommand):
  """List type providers in a project.

  Prints a list of the configured type providers.
  """

  detailed_help = {
      'EXAMPLES': """\
          To print out a list of all type providers, run:

            $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(name, insertTime.date(format="%Y-%m-%d"):label=INSERT_DATE)')

  def Run(self, args):
    """Run 'type-providers list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of type providers for this project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    project = dm_base.GetProject()

    request = (self.messages.
               DeploymentmanagerTypeProvidersListRequest(project=project))
    return dm_api_util.YieldWithHttpExceptions(
        list_pager.YieldFromList(self.client.typeProviders,
                                 request,
                                 field='typeProviders',
                                 batch_size=args.page_size,
                                 limit=args.limit))
