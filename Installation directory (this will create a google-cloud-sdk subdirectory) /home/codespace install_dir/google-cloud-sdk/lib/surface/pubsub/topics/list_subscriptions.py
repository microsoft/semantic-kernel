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
"""Cloud Pub/Sub topics list_subscriptions command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties


def _Run(args, legacy_output=False):
  client = topics.TopicsClient()

  topic_ref = args.CONCEPTS.topic.Parse()
  for topic_sub in client.ListSubscriptions(
      topic_ref, page_size=args.page_size):
    if legacy_output:
      topic_sub = util.ListTopicSubscriptionDisplayDict(topic_sub)
    yield topic_sub


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListSubscriptions(base.ListCommand):
  """Lists Cloud Pub/Sub subscriptions from a given topic."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Lists all of the Cloud Pub/Sub subscriptions attached to the given
          topic and that match the given filter.""",
      'EXAMPLES':
          """\
          To filter results by subscription name
          (ie. only show subscription 'mysubs'), run:

            $ {command} mytopic --filter=mysubs

          To combine multiple filters (with AND or OR), run:

            $ {command} mytopic --filter="mysubs1 OR mysubs2"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('yaml')
    parser.display_info.AddUriFunc(util.SubscriptionUriFunc)

    resource_args.AddTopicResourceArg(parser, 'to list subscriptions for.')

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListSubscriptionsBeta(ListSubscriptions):
  """Lists Cloud Pub/Sub subscriptions from a given topic."""

  def Run(self, args):
    legacy_output = properties.VALUES.pubsub.legacy_output.GetBool()
    return _Run(args, legacy_output=legacy_output)
