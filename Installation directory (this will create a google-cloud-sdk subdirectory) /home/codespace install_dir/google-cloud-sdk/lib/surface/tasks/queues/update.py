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
"""`gcloud tasks queues update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import GetApiAdapter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Cloud Tasks queue.

  The flags available to this command represent the fields of a queue that are
  mutable.
  """
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To update a Cloud Tasks queue:

              $ {command} my-queue
                --clear-max-attempts --clear-max-retry-duration
                --clear-max-doublings --clear-min-backoff
                --clear-max-backoff
                --clear-max-dispatches-per-second
                --clear-max-concurrent-dispatches
                --clear-routing-override
         """,
  }

  def __init__(self, *args, **kwargs):
    super(Update, self).__init__(*args, **kwargs)
    self.is_alpha = False

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to update')
    flags.AddLocationFlag(parser)
    flags.AddUpdatePushQueueFlags(parser)

  def Run(self, args):
    if self.ReleaseTrack() == base.ReleaseTrack.BETA:
      queue_type = args.type
    else:
      queue_type = constants.PUSH_QUEUE
    parsers.CheckUpdateArgsSpecified(args,
                                     queue_type,
                                     release_track=self.ReleaseTrack())
    api = GetApiAdapter(self.ReleaseTrack())
    queues_client = api.queues
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    queue_config = parsers.ParseCreateOrUpdateQueueArgs(
        args,
        queue_type,
        api.messages,
        is_update=True,
        release_track=self.ReleaseTrack())
    updated_fields = parsers.GetSpecifiedFieldsMask(
        args, queue_type, release_track=self.ReleaseTrack())

    if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      app_engine_routing_override = (
          queue_config.appEngineHttpTarget.appEngineRoutingOverride
          if queue_config.appEngineHttpTarget is not None else None)
      http_target_args = parsers.GetHttpTargetArgs(queue_config)

      update_response = queues_client.Patch(
          queue_ref,
          updated_fields,
          retry_config=queue_config.retryConfig,
          rate_limits=queue_config.rateLimits,
          app_engine_routing_override=app_engine_routing_override,
          http_uri_override=http_target_args['http_uri_override'],
          http_method_override=http_target_args['http_method_override'],
          http_header_override=http_target_args['http_header_override'],
          http_oauth_email_override=http_target_args[
              'http_oauth_email_override'
          ],
          http_oauth_scope_override=http_target_args[
              'http_oauth_scope_override'
          ],
          http_oidc_email_override=http_target_args['http_oidc_email_override'],
          http_oidc_audience_override=http_target_args[
              'http_oidc_audience_override'
          ],
      )
    elif self.ReleaseTrack() == base.ReleaseTrack.BETA:
      app_engine_routing_override = (
          queue_config.appEngineHttpQueue.appEngineRoutingOverride
          if queue_config.appEngineHttpQueue is not None else None)

      http_target_args = parsers.GetHttpTargetArgs(queue_config)

      update_response = queues_client.Patch(
          queue_ref,
          updated_fields,
          retry_config=queue_config.retryConfig,
          rate_limits=queue_config.rateLimits,
          app_engine_routing_override=app_engine_routing_override,
          stackdriver_logging_config=queue_config.stackdriverLoggingConfig,
          queue_type=queue_config.type,
          http_uri_override=http_target_args['http_uri_override'],
          http_method_override=http_target_args['http_method_override'],
          http_header_override=http_target_args['http_header_override'],
          http_oauth_email_override=http_target_args[
              'http_oauth_email_override'
          ],
          http_oauth_scope_override=http_target_args[
              'http_oauth_scope_override'
          ],
          http_oidc_email_override=http_target_args['http_oidc_email_override'],
          http_oidc_audience_override=http_target_args[
              'http_oidc_audience_override'
          ],
      )
    else:
      app_engine_routing_override = queue_config.appEngineRoutingOverride

      http_target_args = parsers.GetHttpTargetArgs(queue_config)
      update_response = queues_client.Patch(
          queue_ref,
          updated_fields,
          retry_config=queue_config.retryConfig,
          rate_limits=queue_config.rateLimits,
          app_engine_routing_override=app_engine_routing_override,
          stackdriver_logging_config=queue_config.stackdriverLoggingConfig,
          http_uri_override=http_target_args['http_uri_override'],
          http_method_override=http_target_args['http_method_override'],
          http_header_override=http_target_args['http_header_override'],
          http_oauth_email_override=http_target_args[
              'http_oauth_email_override'
          ],
          http_oauth_scope_override=http_target_args[
              'http_oauth_scope_override'
          ],
          http_oidc_email_override=http_target_args['http_oidc_email_override'],
          http_oidc_audience_override=http_target_args[
              'http_oidc_audience_override'
          ],
      )
    log.status.Print('Updated queue [{}].'.format(
        parsers.GetConsolePromptString(queue_ref.RelativeName())))
    return update_response


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaUpdate(Update):
  """Update a Cloud Tasks queue.

  The flags available to this command represent the fields of a queue that are
  mutable.
  """
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To update a Cloud Tasks queue:

              $ {command} my-queue
                --clear-max-attempts --clear-max-retry-duration
                --clear-max-doublings --clear-min-backoff
                --clear-max-backoff
                --clear-max-dispatches-per-second
                --clear-max-concurrent-dispatches
                --clear-routing-override
         """,
  }

  def __init__(self, *args, **kwargs):
    super(BetaUpdate, self).__init__(*args, **kwargs)
    self.is_alpha = False

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to update')
    flags.AddLocationFlag(parser)
    flags.AddUpdatePushQueueFlags(
        parser, release_track=base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaUpdate(Update):
  """Update a Cloud Tasks queue.

  The flags available to this command represent the fields of a queue that are
  mutable. Attempting to use this command on a different type of queue will
  result in an error.
  """
  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To update a Cloud Tasks queue:

              $ {command} my-queue
                --clear-max-attempts --clear-max-retry-duration
                --clear-max-doublings --clear-min-backoff
                --clear-max-backoff
                --clear-max-tasks-dispatched-per-second
                --clear-max-concurrent-tasks
                --clear-routing-override
         """,
  }

  def __init__(self, *args, **kwargs):
    super(AlphaUpdate, self).__init__(*args, **kwargs)
    self.is_alpha = True

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to update')
    flags.AddLocationFlag(parser)
    flags.AddUpdatePushQueueFlags(parser, release_track=base.ReleaseTrack.ALPHA)
