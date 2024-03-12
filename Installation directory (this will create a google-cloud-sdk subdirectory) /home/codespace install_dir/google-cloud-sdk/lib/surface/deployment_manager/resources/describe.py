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

"""resources describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_api_util
from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


@dm_base.UseDmApi(dm_base.DmApiVersion.V2)
class Describe(base.DescribeCommand, dm_base.DmCommand):
  """Provide information about a resource.

  This command prints out all available details about a resource.
  """

  detailed_help = {
      'EXAMPLES': """
To display information about a resource, run:

  $ {command} --deployment=my-deployment my-resource-name
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
    parser.add_argument('resource', help='Resource name.')

  def Run(self, args):
    """Run 'resources describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested resource.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    try:
      return self.client.resources.Get(
          self.messages.DeploymentmanagerResourcesGetRequest(
              project=dm_base.GetProject(),
              deployment=args.deployment,
              resource=args.resource
          )
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, dm_api_util.HTTP_ERROR_FORMAT)
