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
"""`gcloud tasks queues update-pull-queue` command."""

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
class UpdatePull(base.UpdateCommand):
  """Update a pull queue.

  The flags available to this command represent the fields of a pull queue
  that are mutable. Attempting to use this command on a different type of queue
  will result in an error.

  If you have early access to Cloud Tasks, refer to the following guide for
  more information about the different queue target types:
  https://cloud.google.com/cloud-tasks/docs/queue-types.
  For access, sign up here: https://goo.gl/Ya0AZd
  """

  @staticmethod
  def Args(parser):
    flags.AddQueueResourceArg(parser, 'to update')
    flags.AddLocationFlag(parser)
    flags.AddUpdatePullQueueFlags(parser)

  def Run(self, args):
    parsers.CheckUpdateArgsSpecified(args, constants.PULL_QUEUE,
                                     release_track=self.ReleaseTrack())
    api = GetApiAdapter(self.ReleaseTrack())
    queues_client = api.queues
    queue_ref = parsers.ParseQueue(args.queue, args.location)
    queue_config = parsers.ParseCreateOrUpdateQueueArgs(
        args,
        constants.PULL_QUEUE,
        api.messages,
        is_update=True,
        release_track=self.ReleaseTrack())
    updated_fields = parsers.GetSpecifiedFieldsMask(
        args, constants.PULL_QUEUE, release_track=self.ReleaseTrack())
    update_response = queues_client.Patch(
        queue_ref, updated_fields, retry_config=queue_config.retryConfig)
    log.status.Print('Updated queue [{}].'.format(
        parsers.GetConsolePromptString(queue_ref.RelativeName())))
    return update_response
