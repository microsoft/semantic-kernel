# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud dataflow jobs list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.dataflow import job_display
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.util import times


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists all jobs in a particular project, optionally filtered by region.

  By default, 100 jobs in the current project are listed; this can be overridden
  with the gcloud --project flag, and the --limit flag.

  Using the --region flag will only list jobs from the given regional endpoint.

  ## EXAMPLES

  Filter jobs with the given name:

    $ {command} --filter="name=my-wordcount"

  List jobs with from a given region:

    $ {command} --region="europe-west1"

  List jobs created this year:

    $ {command} --created-after=2018-01-01

  List jobs created more than a week ago:

    $ {command} --created-before=-P1W
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""

    base.ASYNC_FLAG.RemoveFromParser(parser)
    # Set manageable limits on number of jobs that are listed.
    base.LIMIT_FLAG.SetDefault(parser, 100)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 20)

    # Flags for filtering jobs.
    parser.add_argument(
        '--status',
        choices={
            'all':
                ('Returns running jobs first, ordered on creation timestamp, '
                 'then, returns all terminated jobs ordered on the termination '
                 'timestamp.'),
            'terminated':
                ('Filters the jobs that have a terminated state, ordered on '
                 'the termination timestamp. Example terminated states: Done, '
                 'Updated, Cancelled, etc.'),
            'active':
                ('Filters the jobs that are running ordered on the creation '
                 'timestamp.'),
        },
        help='Filter the jobs to those with the selected status.')
    parser.add_argument(
        '--created-after',
        type=arg_parsers.Datetime.Parse,
        help=('Filter the jobs to those created after the given time. '
              'See $ gcloud topic datetimes for information on time formats. '
              'For example, `2018-01-01` is the first day of the year, and '
              '`-P2W` is 2 weeks ago.'))
    parser.add_argument(
        '--created-before',
        type=arg_parsers.Datetime.Parse,
        help=('Filter the jobs to those created before the given time. '
              'See $ gcloud topic datetimes for information on time formats.'))
    parser.add_argument(
        '--region',
        metavar='REGION',
        help=(
            'Only resources from the given region are queried. '
            'If not provided, an attempt will be made to query from all '
            'available regions. In the event of an outage, jobs from certain '
            'regions may not be available.'))

    parser.display_info.AddFormat("""
          table(
            id:label=JOB_ID,
            name:label=NAME,
            type:label=TYPE,
            creationTime.yesno(no="-"),
            state,
            location:label=REGION
          )
     """)
    parser.display_info.AddUriFunc(dataflow_util.JobsUriFunc)

  def Run(self, args):
    """Runs the command.

    Args:
      args: All the arguments that were provided to this command invocation.

    Returns:
      An iterator over Job messages.
    """
    if args.filter:
      filter_expr = resource_filter.Compile(args.filter)

      def EvalFilter(x):
        return (filter_expr.Evaluate(job_display.DisplayInfo(x)) and
                _JobFilter(args)(x))

      filter_pred = EvalFilter
    else:
      filter_pred = _JobFilter(args)

    project_id = properties.VALUES.core.project.Get(required=True)
    jobs = self._JobSummariesForProject(project_id, args, filter_pred)

    return [job_display.DisplayInfo(job) for job in jobs]

  def _JobSummariesForProject(self, project_id, args, filter_predicate):
    """Get the list of job summaries that match the predicate.

    Args:
      project_id: The project ID to retrieve
      args: parsed command line arguments
      filter_predicate: The filter predicate to apply

    Returns:
      An iterator over all the matching jobs.
    """
    request = None
    service = None
    status_filter = self._StatusArgToFilter(args.status, args.region)
    if args.region:
      request = apis.Jobs.LIST_REQUEST(
          projectId=project_id, location=args.region, filter=status_filter)
      service = apis.Jobs.GetService()
    else:
      log.status.Print(
          '`--region` not set; getting jobs from all available regions. ' +
          'Some jobs may be missing in the event of an outage. ' +
          'https://cloud.google.com/dataflow/docs/concepts/regional-endpoints')
      request = apis.Jobs.AGGREGATED_LIST_REQUEST(
          projectId=project_id, filter=status_filter)
      service = apis.GetClientInstance().projects_jobs

    return dataflow_util.YieldFromList(
        project_id=project_id,
        region_id=args.region,
        service=service,
        request=request,
        limit=args.limit,
        batch_size=args.page_size,
        field='jobs',
        batch_size_attribute='pageSize',
        predicate=filter_predicate)

  def _StatusArgToFilter(self, status, region=None):
    """Return a string describing the job status.

    Args:
      status: The job status enum
      region: The region argument, to select the correct wrapper message.

    Returns:
      string describing the job status
    """

    filter_value_enum = None
    if region:
      filter_value_enum = (
          apis.GetMessagesModule().DataflowProjectsLocationsJobsListRequest
          .FilterValueValuesEnum)
    else:
      filter_value_enum = (
          apis.GetMessagesModule().DataflowProjectsJobsAggregatedRequest
          .FilterValueValuesEnum)

    value_map = {
        'all': filter_value_enum.ALL,
        'terminated': filter_value_enum.TERMINATED,
        'active': filter_value_enum.ACTIVE,
    }
    return value_map.get(status, filter_value_enum.ALL)


class _JobFilter(object):
  """Predicate for filtering jobs."""

  def __init__(self, args):
    """Create a _JobFilter from the given args.

    Args:
      args: The argparse.Namespace containing the parsed arguments.
    """
    self.preds = []
    if args.created_after or args.created_before:
      self._ParseTimePredicate(args.created_after, args.created_before)

  def __call__(self, job):
    return all([pred(job) for pred in self.preds])

  def _ParseTimePredicate(self, after, before):
    """Return a predicate for filtering jobs by their creation time.

    Args:
      after: Only return true if the job was created after this time.
      before: Only return true if the job was created before this time.
    """
    if after and (not before):
      self.preds.append(lambda x: times.ParseDateTime(x.createTime) > after)
    elif (not after) and before:
      self.preds.append(lambda x: times.ParseDateTime(x.createTime) <= before)
    elif after and before:

      def _Predicate(x):
        create_time = times.ParseDateTime(x.createTime)
        return after < create_time and create_time <= before

      self.preds.append(_Predicate)
