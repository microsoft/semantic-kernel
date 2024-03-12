# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


class Update(base.SilentCommand):
  """Update a quota override for a consumer.

  This command updates a quota override for a consumer. The supported consumers
  are projects, folders, and organizations. The override ID can be
  found from list command output.

  ## EXAMPLES

  To update a quota override for project with project number, run:

    $ {command} --service=example.googleapis.com --consumer=projects/12321
        --metric=example.googleapis.com/default_requests
        --unit=1/min/{project} --value=360

  To update a quota override for project with project ID, run:

    $ {command} --service=example.googleapis.com --consumer=projects/hello
        --metric=example.googleapis.com/default_requests
        --unit=1/min/{project} --value=360

  To update a quota override for an organization, run:

    $ {command} --service=example.googleapis.com --consumer=organizations/555
        --metric=example.googleapis.com/default_requests
        --unit=1/min/{project} --value=360

  To force the update of a quota override, run:

    $ {command} --service=example.googleapis.com --consumer=projects/12321
        --metric=example.googleapis.com/default_requests
        --unit=1/min/{project}
        --dimensions=regions=us-central1
        --dimensions=zones=us-central1-c --value=360 --force
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        '--service',
        required=True,
        help='The service to update a quota override for.')
    parser.add_argument(
        '--consumer',
        required=True,
        help='The consumer to update override for.')
    parser.add_argument(
        '--metric',
        required=True,
        help='The metric to update a quota override for.')
    parser.add_argument(
        '--unit',
        required=True,
        help='The unit of a metric to update a quota override for.')
    parser.add_argument(
        '--dimensions',
        type=arg_parsers.ArgDict(),
        metavar='KEY=VALUE',
        action=arg_parsers.UpdateAction,
        help='The dimensions of the override, e.g. for specific locations.')
    parser.add_argument(
        '--value', type=int, required=True, help='The value of the override.')
    parser.add_argument(
        '--force',
        action='store_true',
        default=False,
        help='Force override update even if the change results in a '
        'substantial decrease in available quota.')

  def Run(self, args):
    """Run 'endpoints quota update'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Nothing.
    """
    op = serviceusage.UpdateQuotaOverrideCall(args.consumer, args.service,
                                              args.metric, args.unit,
                                              args.dimensions, args.value,
                                              args.force)
    if op.done:
      return
    op = services_util.WaitOperation(op.name, serviceusage.GetOperation)
    services_util.PrintOperation(op)
