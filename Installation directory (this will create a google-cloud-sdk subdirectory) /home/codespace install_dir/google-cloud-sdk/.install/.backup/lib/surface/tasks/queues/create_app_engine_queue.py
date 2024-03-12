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
"""`gcloud tasks queues create command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


@base.Deprecate(is_removed=False,
                warning='This command is deprecated. '
                        'Use `gcloud beta tasks queues create` instead')
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateAppEngine(base.CreateCommand):
  """Create a Cloud Tasks queue.

  The flags available to this command represent the fields of a queue that are
  mutable.
  """
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create a Cloud Tasks queue:

              $ {command} my-queue
                --max-attempts=10 --max-retry-duration=5s
                --max-doublings=4 --min-backoff=1s
                --max-backoff=10s
                --max-dispatches-per-second=100
                --max-concurrent-dispatches=10
                --routing-override=service:abc
         """,
  }

  def __init__(self, *args, **kwargs):
    super(CreateAppEngine, self).__init__(*args, **kwargs)
    self.is_alpha = False

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to create')
    flags.AddLocationFlag(parser)
    flags.AddCreatePushQueueFlags(
        parser,
        release_track=base.ReleaseTrack.BETA,
        app_engine_queue=True,
        http_queue=False,
    )

  def Run(self, args):
    api = GetApiAdapter(self.ReleaseTrack())
    queues_client = api.queues
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    location_ref = parsers.ExtractLocationRefFromQueueRef(queue_ref)
    queue_config = parsers.ParseCreateOrUpdateQueueArgs(
        args,
        constants.PUSH_QUEUE,
        api.messages,
        release_track=self.ReleaseTrack(),
        http_queue=False,
    )
    if not self.is_alpha:
      create_response = queues_client.Create(
          location_ref,
          queue_ref,
          retry_config=queue_config.retryConfig,
          rate_limits=queue_config.rateLimits,
          app_engine_http_queue=queue_config.appEngineHttpQueue,
          stackdriver_logging_config=queue_config.stackdriverLoggingConfig)
    else:
      create_response = queues_client.Create(
          location_ref,
          queue_ref,
          retry_config=queue_config.retryConfig,
          rate_limits=queue_config.rateLimits,
          app_engine_http_target=queue_config.appEngineHttpTarget)
    log.CreatedResource(
        parsers.GetConsolePromptString(queue_ref.RelativeName()), 'queue')
    return create_response


@base.Deprecate(is_removed=False,
                warning='This command group is deprecated. '
                        'Use `gcloud alpha tasks queues create` instead')
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaCreateAppEngine(CreateAppEngine):
  """Create a Cloud Tasks queue.

  The flags available to this command represent the fields of a queue that are
  mutable.
  """

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create a Cloud Tasks queue:

              $ {command} my-queue
                --max-attempts=10 --max-retry-duration=5s
                --max-doublings=4 --min-backoff=1s
                --max-backoff=10s
                --max-tasks-dispatched-per-second=100
                --max-concurrent-tasks=10
                --routing-override=service:abc
          """,
  }

  def __init__(self, *args, **kwargs):
    super(AlphaCreateAppEngine, self).__init__(*args, **kwargs)
    self.is_alpha = True

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to create')
    flags.AddLocationFlag(parser)
    flags.AddCreatePushQueueFlags(
        parser,
        release_track=base.ReleaseTrack.ALPHA,
        app_engine_queue=True,
        http_queue=False,
    )
