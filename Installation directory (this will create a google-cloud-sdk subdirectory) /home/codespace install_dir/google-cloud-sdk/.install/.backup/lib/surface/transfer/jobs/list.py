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
"""Command to list Transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import list_util
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_printer


class List(base.Command):
  """List Transfer Service transfer jobs."""

  detailed_help = {
      'DESCRIPTION':
          """\
      List Transfer Service transfer jobs in a given project to show their
      configurations and latest operations.
      """,
      'EXAMPLES':
          """\
      To list all jobs in your current project, run:

        $ {command}

      To list all disabled jobs in your project, run:

        $ {command} --job-statuses=disabled

      To list jobs 'foo' and 'bar', run:

        $ {command} --job-names=foo,bar

      To list all information about all jobs formatted as JSON, run:

        $ {command} --format=json

      To list all information about jobs 'foo' and 'bar' formatted as YAML, run:

        $ {command} --job-names=foo,bar --format=YAML
      """,
  }

  @staticmethod
  def Args(parser):
    parser.SetSortArgs(False)
    list_util.add_common_list_flags(parser)
    parser.add_argument(
        '--job-names',
        type=arg_parsers.ArgList(),
        metavar='JOB_NAMES',
        help='The names of the jobs you want to list. Separate multiple job'
        ' names with commas (e.g., --job-names=foo,bar). If not specified,'
        ' all jobs will be listed.')
    parser.add_argument(
        '--job-statuses',
        type=arg_parsers.ArgList(),
        metavar='JOB_STATUSES',
        help='List only jobs with the statuses you specify.'
        " Options include 'enabled', 'disabled', 'deleted' (case"
        ' insensitive). Separate multiple statuses with commas (e.g.,'
        ' --job-statuses=enabled,deleted). If not specified, all jobs will'
        ' be listed.')
    parser.add_argument(
        '--expand-table',
        action='store_true',
        help='Include additional table columns (job name, source, destination,'
        ' frequency, lastest operation name, job status) in command output.'
        ' Tip: increase the size of your terminal before running the command.')

  def Display(self, args, resources):
    """API response display logic."""
    if args.expand_table:
      # Removes unwanted "transferJobs/" and "transferOperations/" prefixes.
      format_string = """table(
          name.slice(13:).join(sep=''),
          transferSpec.firstof(
              gcsDataSource, awsS3DataSource, httpDataSource,
              azureBlobStorageDataSource, posixDataSource
            ).firstof(
              bucketName, listUrl, container, rootDirectory
            ).trailoff(45):label=SOURCE,
          transferSpec.firstof(
              gcsDataSink, posixDataSink
          ).firstof(
              bucketName, rootDirectory
          ).trailoff(45):label=DESTINATION,
          latestOperationName.slice(19:).join(sep=''),
          status)
      """
    else:
      format_string = """table(
          name.slice(13:).join(sep=''),
          latestOperationName.slice(19:).join(sep=''))
      """
    resource_printer.Print(resources, args.format or format_string)

  def Run(self, args):
    """Command execution logic."""
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    if args.job_names:
      formatted_job_names = name_util.add_job_prefix(args.job_names)
    else:
      formatted_job_names = None
    job_statuses = args.job_statuses or None

    filter_dictionary = {
        'jobNames': formatted_job_names,
        'jobStatuses': job_statuses,
        'projectId': properties.VALUES.core.project.Get(),
    }
    filter_string = json.dumps(filter_dictionary)

    resources_iterator = list_pager.YieldFromList(
        client.transferJobs,
        messages.StoragetransferTransferJobsListRequest(filter=filter_string),
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
        field='transferJobs',
        limit=args.limit,
    )
    list_util.print_transfer_resources_iterator(resources_iterator,
                                                self.Display, args)
