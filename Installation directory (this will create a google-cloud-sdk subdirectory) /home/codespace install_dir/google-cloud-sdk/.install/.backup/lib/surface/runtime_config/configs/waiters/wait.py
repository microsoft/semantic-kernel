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

"""The configs waiters wait command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.runtime_config import flags


class Wait(base.Command):
  """Wait for a waiter to end in success or failure.

  This command waits for a waiter to end in success or failure.
  """

  detailed_help = {
      'EXAMPLES': """
          To wait for a waiter named "my-waiter" within a configuration named
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

    parser.add_argument(
        '--max-wait',
        type=arg_parsers.Duration(lower_bound='1s',
                                  upper_bound='{0}s'.format(
                                      util.MAX_WAITER_TIMEOUT)),
        help="""\
        The maximum amount of time to wait for a waiter to finish.
        See $ gcloud topic datetimes for information on duration formats.
        """)

    parser.add_argument('name', help='The waiter name.')

  def Run(self, args):
    """Run 'runtime-configs waiters wait'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested waiter, after waiting for it to succeed or fail.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      OperationTimeoutError: If the waiter doesn't complete in time.
    """
    waiter_resource = util.ParseWaiterName(args.name, args)
    result = util.WaitForWaiter(waiter_resource, max_wait=args.max_wait)
    if util.IsFailedWaiter(result):
      self.exit_code = 2  # exit with code 2 if the result waiter failed.
    return util.FormatWaiter(result)
