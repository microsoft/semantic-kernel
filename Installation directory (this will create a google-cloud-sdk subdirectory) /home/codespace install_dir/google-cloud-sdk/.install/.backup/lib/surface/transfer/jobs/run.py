# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to run transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import operations_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import properties


class Run(base.Command):
  """Run a Transfer Service transfer job."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Run a Transfer Service transfer job.
      """,
      'EXAMPLES':
          """\
      To run job 'foo', run:

        $ {command} foo
      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='The name of the job you want to run.')
    parser.add_argument(
        '--no-async',
        action='store_true',
        help=(
            'Blocks other tasks in your terminal until the transfer operation'
            ' has completed. If not included, tasks will run asynchronously.'))

  def Run(self, args):
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    formatted_name = name_util.add_job_prefix(args.name)

    result = client.transferJobs.Run(
        messages.StoragetransferTransferJobsRunRequest(
            jobName=formatted_name,
            runTransferJobRequest=messages.RunTransferJobRequest(
                projectId=properties.VALUES.core.project.Get())))

    if args.no_async:
      operations_util.block_until_done(operation_name=result.name)

    return result
