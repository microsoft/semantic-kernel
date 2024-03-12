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
"""`gcloud tasks queues delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a queue."""
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To delete a queue:

              $ {command} my-queue
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to delete')
    flags.AddLocationFlag(parser)

  def Run(self, args):
    queues_client = GetApiAdapter(self.ReleaseTrack()).queues
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    queue_short = parsers.GetConsolePromptString(queue_ref.RelativeName())
    console_io.PromptContinue(
        cancel_on_no=True,
        prompt_string=(
            'Deleted queues can not be re-created for a duration of up to 7 '
            'days. Are you sure you want to delete: [{}]'.format(queue_short)))
    queues_client.Delete(queue_ref)
    log.DeletedResource(queue_short, 'queue')
