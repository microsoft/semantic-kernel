# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""`gcloud tasks create-app-engine-task` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class CreateHttp(base.CreateCommand):
  """Create and add a task that targets a HTTP endpoint."""
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create a task:

              $ {command} --queue=my-queue
                --url=http://example.com/handler-path my-task
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddCreateHttpTaskFlags(parser)
    flags.AddLocationFlag(parser)

  def Run(self, args):
    if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      # This functionality doesn't exist in the alpha API so use beta.
      api_release_track = base.ReleaseTrack.BETA
    else:
      api_release_track = self.ReleaseTrack()

    api = GetApiAdapter(api_release_track)
    tasks_client = api.tasks
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_ref = parsers.ParseTask(args.task,
                                 queue_ref) if args.task else None
    task_config = parsers.ParseCreateTaskArgs(
        args, constants.HTTP_TASK, api.messages,
        release_track=api_release_track)
    create_response = tasks_client.Create(
        queue_ref, task_ref,
        schedule_time=task_config.scheduleTime,
        http_request=task_config.httpRequest)
    log.CreatedResource(create_response.name, 'task')
    return create_response
