# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Command to list tasks for a specified Batch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.batch import tasks
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.batch import resource_args


class List(base.ListCommand):
  """List tasks for a specified Batch job.

  Currently, since Batch only supports one taskGroup, group0, the command
  takes --job as the required argument and will list all tasks
  in group0 of the job.

  This command can fail for the following reasons:
  * The job specified does not exist.
  * The active account does not have permission to access the given job

  ## EXAMPLES

  To print all tasks in the group0 of job with name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar
  """

  @staticmethod
  def Args(parser):
    resource_args.AddJobFlagResourceArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat('table(name, status.state)')

  def Run(self, args):
    release_track = self.ReleaseTrack()

    client = tasks.TasksClient(release_track)
    job_ref = args.CONCEPTS.job.Parse()

    return list_pager.YieldFromList(
        client.service,
        client.messages.BatchProjectsLocationsJobsTaskGroupsTasksListRequest(
            parent=job_ref.RelativeName() + '/taskGroups/group0',
            pageSize=args.page_size,
            filter=args.filter),
        batch_size=args.page_size,
        field='tasks',
        limit=args.limit,
        batch_size_attribute='pageSize')
