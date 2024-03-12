# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Cloud Pub/Sub topics detach-subscription command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_ex
from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log


def _Run(args):
  """Detaches one or more subscriptions."""
  client = topics.TopicsClient()

  failed = []
  for subscription_ref in args.CONCEPTS.subscription.Parse():
    try:
      result = client.DetachSubscription(subscription_ref)
    except api_ex.HttpError as error:
      exc = exceptions.HttpException(error)
      log.DetachedResource(
          subscription_ref.RelativeName(),
          kind='subscription',
          failed=util.CreateFailureErrorMessage(exc.payload.status_message),
      )
      failed.append(subscription_ref.subscriptionsId)
      continue

    subscription = client.messages.Subscription(
        name=subscription_ref.RelativeName())

    log.DetachedResource(subscription_ref.RelativeName(), kind='subscription')
    yield result

  if failed:
    raise util.RequestsFailedError(failed, 'detach')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class DetachSubscription(base.UpdateCommand):
  """Detaches one or more Cloud Pub/Sub subscriptions."""

  detailed_help = {
      'EXAMPLES':
          """\
          To detach a Cloud Pub/Sub subscription, run:

              $ {command} mysubscription"""
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSubscriptionResourceArg(parser, 'to detach.', plural=True)

  def Run(self, args):
    return _Run(args)
