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

"""The configs waiters create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.runtime_config import flags
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Create waiter resources.

  This command creates a new waiter resource with the specified name and
  parameters.
  """

  detailed_help = {
      'EXAMPLES': """
          To create a waiter in "my-config" with success and failure paths
          nested under "/status", run:

            $ {command} my-waiter --config-name=my-config --timeout=15m --success-cardinality-path=/status/success --success-cardinality-number=5 --failure-cardinality-path=/status/failure --failure-cardinality-number=1

          This waiter will wait for at most 15 minutes for the first of two
          possible scenarios: 1) five or more variables are written to the
          /status/success/ path; or 2) one or more variables are written to the
          /status/failure/ path.

          To create a waiter without a failure path, run:

            $ {command} my-waiter --config-name=my-config --timeout=15m --success-cardinality-path=/status/success --success-cardinality-number=5

          This waiter will wait until 5 or more success variables are written,
          or the 15 minute timeout elapses.
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
    base.ASYNC_FLAG.AddToParser(parser)

    parser.add_argument(
        '--timeout',
        type=arg_parsers.Duration(lower_bound='1s',
                                  upper_bound='{0}s'.format(
                                      util.MAX_WAITER_TIMEOUT)),
        required=True,
        help="""\
        The amount of time to wait before failing with DEADLINE_EXCEEDED.
        See $ gcloud topic datetimes for information on duration formats.
        """)

    parser.add_argument(
        '--success-cardinality-path',
        help='The path where success variables are written.',
        required=True)
    parser.add_argument(
        '--success-cardinality-number',
        help='The minimum required number of success variables.',
        type=arg_parsers.BoundedInt(lower_bound=1),
        default=1)

    parser.add_argument(
        '--failure-cardinality-path',
        help='The path where failure variables are written.')
    parser.add_argument(
        '--failure-cardinality-number',
        help='The minimum required number of failure variables.',
        type=arg_parsers.BoundedInt(lower_bound=1),
        default=1)

    parser.add_argument('name', help='The waiter name.')

  def Run(self, args):
    """Run 'runtime-configs waiters create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The associated waiter operation.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    waiter_client = util.WaiterClient()
    messages = util.Messages()

    waiter_resource = util.ParseWaiterName(args.name, args)
    project = waiter_resource.projectsId
    config = waiter_resource.configsId

    success = messages.EndCondition(
        cardinality=messages.Cardinality(
            path=args.success_cardinality_path,
            number=args.success_cardinality_number,
        )
    )

    if args.failure_cardinality_path:
      failure = messages.EndCondition(
          cardinality=messages.Cardinality(
              path=args.failure_cardinality_path,
              number=args.failure_cardinality_number,
          )
      )
    else:
      failure = None

    result = waiter_client.Create(
        messages.RuntimeconfigProjectsConfigsWaitersCreateRequest(
            parent=util.ConfigPath(project, config),
            waiter=messages.Waiter(
                name=waiter_resource.RelativeName(),
                timeout='{0}s'.format(args.timeout),
                success=success,
                failure=failure,
            )
        )
    )

    log.CreatedResource(waiter_resource)

    if args.async_:
      # In async mode, we return the current waiter representation.
      # The waiter resource exists immediately after creation; the
      # operation resource returned from CreateWaiter only tracks the
      # waiting process.
      self._async_resource = waiter_resource
      request = (waiter_client.client.MESSAGES_MODULE
                 .RuntimeconfigProjectsConfigsWaitersGetRequest(
                     name=waiter_resource.RelativeName()))
      result = waiter_client.Get(request)
    else:
      self._async_resource = None
      result = util.WaitForWaiter(waiter_resource)
      if util.IsFailedWaiter(result):
        self.exit_code = 2  # exit with code 2 if the result waiter failed.

    return util.FormatWaiter(result)

  def Epilog(self, unused_resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      unused_resources_were_displayed: Unused.
    """
    if self._async_resource:
      log.status.Print()
      log.status.Print(
          ('The wait command can be used to monitor the progress '
           'of waiter [{0}].').format(self._async_resource.Name()))
