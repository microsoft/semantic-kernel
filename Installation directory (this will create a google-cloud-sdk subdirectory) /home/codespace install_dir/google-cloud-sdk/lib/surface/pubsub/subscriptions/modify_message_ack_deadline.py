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
"""Cloud Pub/Sub subscription modify command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _Run(args, ack_ids, legacy_output=False, capture_failures=False):
  """Modifies the ack deadline for one or more messages."""
  client = subscriptions.SubscriptionsClient()

  subscription_ref = args.CONCEPTS.subscription.Parse()
  if not capture_failures:
    result = client.ModifyAckDeadline(subscription_ref, ack_ids,
                                      args.ack_deadline)

    log.status.Print('Set ackDeadlineSeconds to [{0}] for messages with ackId '
                     '[{1}]] for subscription [{2}]'.format(
                         args.ack_deadline, ','.join(ack_ids),
                         subscription_ref.RelativeName()))

    if legacy_output:
      return {
          'subscriptionId': subscription_ref.RelativeName(),
          'ackId': ack_ids,
          'ackDeadlineSeconds': args.ack_deadline
      }, {}
    else:
      return result, {}

  result = None
  ack_ids_and_failure_reasons = {}
  try:
    result = client.ModifyAckDeadline(subscription_ref, ack_ids,
                                      args.ack_deadline)
  except api_ex.HttpError as error:
    ack_ids_and_failure_reasons = util.HandleExactlyOnceDeliveryError(error)

  failed_ack_ids, successfully_processed_ack_ids = util.ParseExactlyOnceAckIdsAndFailureReasons(
      ack_ids_and_failure_reasons, ack_ids)

  log.status.Print('Set ackDeadlineSeconds to [{0}] for messages with ackId '
                   '[{1}]] for subscription [{2}]'.format(
                       args.ack_deadline,
                       ','.join(successfully_processed_ack_ids),
                       subscription_ref.RelativeName()))
  if failed_ack_ids:
    log.status.Print('Set ackDeadlineSeconds to [{0}] for messages with ackId '
                     '[{1}]] failed for subscription [{2}]'.format(
                         args.ack_deadline, ','.join(failed_ack_ids),
                         subscription_ref.RelativeName()))
  if legacy_output:
    result = {
        'subscriptionId': subscription_ref.RelativeName(),
        'ackId': ack_ids,
        'ackDeadlineSeconds': args.ack_deadline
    }
  return result, ack_ids_and_failure_reasons


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ModifyMessageAckDeadline(base.Command):
  """Modifies the ACK deadline for a specific Cloud Pub/Sub message."""

  detailed_help = {
      'DESCRIPTION':
          """\
          This method is useful to indicate that more time is needed to process
          a message by the subscriber, or to make the message available for
          redelivery if the processing was interrupted."""
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSubscriptionResourceArg(parser, 'messages belong to.')
    flags.AddAckIdFlag(parser, 'modify the deadline for.')
    flags.AddAckDeadlineFlag(parser, required=True)

  def Run(self, args):
    result, ack_ids_and_failure_reasons = _Run(
        args, args.ack_ids, capture_failures=True)
    if ack_ids_and_failure_reasons:
      return ack_ids_and_failure_reasons
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ModifyMessageAckDeadlineBeta(ModifyMessageAckDeadline):
  """Modifies the ACK deadline for a specific Cloud Pub/Sub message."""

  @staticmethod
  def Args(parser):
    resource_args.AddSubscriptionResourceArg(parser, 'messages belong to.')
    flags.AddAckIdFlag(parser, 'modify the deadline for.', add_deprecated=True)
    flags.AddAckDeadlineFlag(parser, required=True)

  def Run(self, args):
    ack_ids = flags.ParseAckIdsArgs(args)
    legacy_output = properties.VALUES.pubsub.legacy_output.GetBool()
    result, ack_ids_and_failure_reasons = _Run(
        args, ack_ids, legacy_output=legacy_output, capture_failures=True)
    if ack_ids_and_failure_reasons:
      return ack_ids_and_failure_reasons
    return result
