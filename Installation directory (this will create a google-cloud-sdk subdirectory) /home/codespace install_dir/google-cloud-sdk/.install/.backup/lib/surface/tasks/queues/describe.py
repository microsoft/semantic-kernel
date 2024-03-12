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
"""`gcloud tasks queues describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers


class Describe(base.DescribeCommand):
  """Show details about a queue."""
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To describe queue:

              $ {command} my-queue
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to describe')
    flags.AddLocationFlag(parser)

  def Run(self, args):
    queues_client = GetApiAdapter(self.ReleaseTrack()).queues
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    return queues_client.Get(queue_ref)
