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

"""The configs waiters describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.runtime_config import flags


class Describe(base.DescribeCommand):
  """Describe waiter resources.

  This command displays information about the waiter resource with the
  specified name.
  """

  detailed_help = {
      'EXAMPLES': """
          To describe a waiter named "my-waiter" within a configuration named
          "my-config", run:

            $ {command} my-waiter --config-name=my-config
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
    flags.AddRequiredConfigFlag(parser)
    parser.add_argument('name', help='The waiter name.')

  def Run(self, args):
    """Run 'runtime-configs waiters describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested waiter.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    waiter_client = util.WaiterClient()
    messages = util.Messages()

    waiter_resource = util.ParseWaiterName(args.name, args)

    result = waiter_client.Get(
        messages.RuntimeconfigProjectsConfigsWaitersGetRequest(
            name=waiter_resource.RelativeName(),
        )
    )

    return util.FormatWaiter(result)
