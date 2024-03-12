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
"""`gcloud tasks describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Show details about a task."""
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To describe a task:

              $ {command} --queue=my-queue my-task
         """,
  }

  TASK_RESPONSE_VIEW_MAPPER = flags.GetTaskResponseViewMapper(
      base.ReleaseTrack.GA)

  @staticmethod
  def Args(parser):
    return Describe._Args(parser, Describe.TASK_RESPONSE_VIEW_MAPPER)

  @staticmethod
  def _Args(parser, task_response_view_mapper):
    flags.AddTaskResourceArgs(parser, 'to describe')
    flags.AddLocationFlag(parser)
    task_response_view_mapper.choice_arg.AddToParser(parser)

  def Run(self, args):
    tasks_client = GetApiAdapter(self.ReleaseTrack()).tasks
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    task_ref = parsers.ParseTask(args.task, queue_ref)
    return tasks_client.Get(
        task_ref,
        response_view=self.TASK_RESPONSE_VIEW_MAPPER.GetEnumForChoice(
            args.response_view))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaDescribe(Describe):
  """Show details about a task."""

  TASK_RESPONSE_VIEW_MAPPER = flags.GetTaskResponseViewMapper(
      base.ReleaseTrack.BETA)

  @staticmethod
  def Args(parser):
    return Describe._Args(parser, BetaDescribe.TASK_RESPONSE_VIEW_MAPPER)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDescribe(Describe):
  """Show details about a task."""

  TASK_RESPONSE_VIEW_MAPPER = flags.GetTaskResponseViewMapper(
      base.ReleaseTrack.ALPHA)

  @staticmethod
  def Args(parser):
    return Describe._Args(parser, AlphaDescribe.TASK_RESPONSE_VIEW_MAPPER)
