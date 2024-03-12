# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Cloud Pub/Sub subscription modify-push-config command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _Run(args, legacy_output=False):
  """Modifies the push config for a subscription."""
  client = subscriptions.SubscriptionsClient()

  subscription_ref = args.CONCEPTS.subscription.Parse()
  push_config = util.ParsePushConfig(args)
  result = client.ModifyPushConfig(subscription_ref, push_config)

  log.UpdatedResource(subscription_ref.RelativeName(), kind='subscription')
  if legacy_output:
    return {
        'subscriptionId': subscription_ref.RelativeName(),
        'pushEndpoint': args.push_endpoint
    }
  else:
    return result


def _Args(parser):
  resource_args.AddSubscriptionResourceArg(parser, 'to modify.')
  flags.AddPushConfigFlags(parser, required=True)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ModifyPushConfig(base.Command):
  """Modifies the push configuration of a Cloud Pub/Sub subscription."""

  @classmethod
  def Args(cls, parser):
    _Args(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ModifyPushConfigBeta(ModifyPushConfig):
  """Modifies the push configuration of a Cloud Pub/Sub subscription."""

  @classmethod
  def Args(cls, parser):
    _Args(parser)

  def Run(self, args):
    legacy_output = properties.VALUES.pubsub.legacy_output.GetBool()
    return _Run(args, legacy_output=legacy_output)
