# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to trigger one-time run of a Dataplex task."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.dataplex import task
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Run(base.Command):
  """Trigger one-time run of a Dataplex task."""

  detailed_help = {
      'EXAMPLES': """\
          To trigger a one-time run of a Dataplex task `test-task` within
          lake `test-lake` in location `us-central1`, run:

           $ {command} test-task --location=us-central1 --lake=test-lake
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddTaskResourceArg(parser, 'to run.')
    parser.add_argument(
        'ARGS',
        metavar='execution-spec-args',
        nargs=argparse.REMAINDER,
        default=[],
        help=(
            'Execution spec arguments to pass to the driver. Follows the format'
            ' argKey=argValue.'
        ),
        type=arg_parsers.ArgList(),
    )
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    task_ref = args.CONCEPTS.task.Parse()
    run_task_response = task.RunTask(task_ref, args)
    return run_task_response
