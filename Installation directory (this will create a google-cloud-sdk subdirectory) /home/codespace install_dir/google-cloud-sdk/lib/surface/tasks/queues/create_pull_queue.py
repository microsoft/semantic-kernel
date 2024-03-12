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
"""`gcloud tasks queues create-pull-queue` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreatePull(base.CreateCommand):
  """Create a pull queue.

  The flags available to this command represent the fields of a pull queue
  that are mutable.

  If you have early access to Cloud Tasks, refer to the following guide for
  more information about the different queue target types:
  https://cloud.google.com/cloud-tasks/docs/queue-types.
  For access, sign up here: https://goo.gl/Ya0AZd
  """

  detailed_help = {
      'DESCRIPTION':
          """
          {description}
          """,
      'EXAMPLES':
          """
          To create a Cloud Tasks pull queue:

              $ {command} my-queue
              --max-attempts=10 --max-retry-duration=10s
         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to create')
    flags.AddLocationFlag(parser)
    flags.AddCreatePullQueueFlags(parser)

  def Run(self, args):
    api = GetApiAdapter(self.ReleaseTrack())
    queues_client = api.queues
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    location_ref = parsers.ExtractLocationRefFromQueueRef(queue_ref)
    queue_config = parsers.ParseCreateOrUpdateQueueArgs(
        args,
        constants.PULL_QUEUE,
        api.messages,
        release_track=self.ReleaseTrack())
    if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      create_response = queues_client.Create(
          location_ref,
          queue_ref,
          retry_config=queue_config.retryConfig,
          rate_limits=queue_config.rateLimits,
          pull_target=queue_config.pullTarget)
    else:
      create_response = queues_client.Create(
          location_ref,
          queue_ref,
          retry_config=queue_config.retryConfig,
          rate_limits=queue_config.rateLimits,
          queue_type=queue_config.type)
    log.CreatedResource(
        parsers.GetConsolePromptString(queue_ref.RelativeName()), 'queue')
    return create_response
