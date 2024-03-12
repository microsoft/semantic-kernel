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
"""`gcloud tasks create-pull-task` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreatePull(base.CreateCommand):
  """Create and add a task to a pull queue."""

  @staticmethod
  def Args(parser):
    flags.AddCreatePullTaskFlags(parser)
    flags.AddLocationFlag(parser)

  def Run(self, args):
    api = GetApiAdapter(self.ReleaseTrack())
    tasks_client = api.tasks
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_ref = parsers.ParseTask(args.task,
                                 queue_ref) if args.task else None
    task_config = parsers.ParseCreateTaskArgs(
        args, constants.PULL_TASK, api.messages,
        release_track=self.ReleaseTrack())
    create_response = tasks_client.Create(
        queue_ref, task_ref,
        schedule_time=task_config.scheduleTime,
        pull_message=task_config.pullMessage)
    log.CreatedResource(create_response.name, 'task')
    return create_response
