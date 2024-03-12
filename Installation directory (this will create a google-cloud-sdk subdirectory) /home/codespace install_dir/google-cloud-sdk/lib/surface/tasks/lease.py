# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""`gcloud tasks lease` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import list_formats
from googlecloudsdk.command_lib.tasks import parsers


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Lease(base.ListCommand):
  """Leases a list of tasks and displays them.

  Each task returned from this command will have its schedule time changed
  based on the lease duration specified. A task that has been returned by
  calling this command will not be returned in a different call before its
  schedule time. After the work associated with a task is finished, the lease
  holder should call `gcloud tasks acknowledge` on the task.
  """

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.LIMIT_FLAG.RemoveFromParser(parser)  # have our own --limit flag

    flags.AddQueueResourceFlag(parser, required=True, plural_tasks=True)
    flags.AddLocationFlag(parser)
    flags.AddTaskLeaseDurationFlag(parser, helptext="""\
        The number of seconds for the desired new lease duration for all tasks
        leased, starting from now. The maximum lease duration is 1 week.
        """)
    flags.AddFilterLeasedTasksFlag(parser)
    flags.AddMaxTasksToLeaseFlag(parser)

    list_formats.AddListTasksFormats(parser, is_alpha=True)

  def Run(self, args):
    tasks_client = GetApiAdapter(self.ReleaseTrack()).tasks
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    duration = parsers.FormatLeaseDuration(args.lease_duration)
    filter_string = parsers.ParseTasksLeaseFilterFlags(args)
    return tasks_client.Lease(queue_ref, duration, filter_string=filter_string,
                              max_tasks=args.limit).tasks
