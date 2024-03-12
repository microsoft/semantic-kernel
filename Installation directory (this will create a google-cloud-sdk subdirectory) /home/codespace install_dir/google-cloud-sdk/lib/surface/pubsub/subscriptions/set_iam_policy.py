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
"""Cloud Pub/Sub subscriptions set-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class SetIamPolicy(base.Command):
  """Set the IAM policy for a Cloud Pub/Sub Subscription."""

  detailed_help = iam_util.GetDetailedHelpForSetIamPolicy(
      'subscription', 'my-subscription')

  @staticmethod
  def Args(parser):
    resource_args.AddSubscriptionResourceArg(parser, 'to set an IAM policy on.')
    flags.AddIamPolicyFileFlag(parser)

  def Run(self, args):
    client = subscriptions.SubscriptionsClient()
    messages = client.messages

    subscription_ref = args.CONCEPTS.subscription.Parse()
    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)

    response = client.SetIamPolicy(subscription_ref, policy=policy)
    log.status.Print('Updated IAM policy for subscription [{}].'.format(
        subscription_ref.Name()))
    return response
