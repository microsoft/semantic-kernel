# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""BQ copy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq import command_utils
from googlecloudsdk.command_lib.bq import hooks
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Copy(base.Command):
  """Bq Copy Command."""
  detailed_help = {
      'brief': 'Copy one BigQuery table to another.',
      'DESCRIPTION': """\
            *{command}* Copies one BigQuery table to another.
            """,
      'EXAMPLES': """\
          The following copies table `my-table`  to table `my-other-table`, in dataset `my-dataset`
          overwriting destination if it exists:

            $ {command} --source my-table --destination my-other-table --source-dataset my-dataset --overwrite
            """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    base.Argument(
        '--overwrite',
        action='store_true',
        default=False,
        required=False,
        help='Overwrite if the resource already exists.').AddToParser(parser)
    base.Argument(
        '--job-id',
        required=False,
        default='',
        help='A unique job ID to use for the request. '
             'If not specified a unique job id will '
             'be generated.').AddToParser(parser)
    concept_parser = hooks.GetTableCopyResourceArgs()[0]
    concept_parser.AddToParser(parser)

  def Run(self, args):
    job_id = hooks.JobIdProcessor(args.job_id)
    requests_type = hooks.GetApiMessage('BigqueryJobsInsertRequest')
    request = requests_type()
    project = args.project or properties.VALUES.core.project.Get(required=True)
    request.projectId = project
    request = hooks.ProcessTableCopyConfiguration(None, args, request)
    request = hooks.ProcessTableCopyOverwrite(None, args, request)
    arg_utils.SetFieldInMessage(request, 'job.jobReference.jobId', job_id)
    arg_utils.SetFieldInMessage(request, 'job.jobReference.projectId', project)

    client = hooks.GetApiClient()
    job_service = client.jobs
    job = client.jobs.Insert(request)

    source_ref = args.CONCEPTS.source.Parse()
    destination_ref = args.CONCEPTS.destination.Parse()
    copy_message = 'Copying {0}:{1} to {2}:{3}.'.format(
        source_ref.Parent().Name(), source_ref.Name(),
        destination_ref.Parent().Name(), destination_ref.Name())

    if not args.async_:
      log.CreatedResource(job.id, kind='Job', details=copy_message)
      return job

    result_service = client.tables
    poller = command_utils.BqJobPoller(job_service, result_service)
    job_ref = resources.REGISTRY.Parse(job.jobReference.jobId,
                                       params={'projectId': project},
                                       collection='bigquery.jobs')
    result = waiter.WaitFor(poller=poller, operation_ref=job_ref,
                            message=copy_message)

    log.status.Print('Copied {0}:{1} to {2}:{3}.'.format(
        source_ref.Parent().Name(), source_ref.Name(),
        destination_ref.Parent().Name(), destination_ref.Name()))
    return result
