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
"""`gcloud tasks queues buffer` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Buffer(base.Command):
  """Buffers a task into a queue."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To buffer into a queue:

              $ {command} --queue=my-queue --location=us-central1
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceFlag(parser, required=True)
    flags.AddLocationFlag(
        parser, required=True, helptext='The location where the queue exists.'
    )
    flags.AddTaskIdFlag(parser)

  def Run(self, args):
    api = GetApiAdapter(self.ReleaseTrack())
    tasks_client = api.tasks
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_id = parsers.ParseTaskId(args)

    task_id = '' if task_id is None else task_id
    tasks_client.Buffer(queue_ref, task_id)
    log.status.Print(
        'Buffered task in queue [{}].'.format(
            parsers.GetConsolePromptString(queue_ref.RelativeName())
        )
    )
