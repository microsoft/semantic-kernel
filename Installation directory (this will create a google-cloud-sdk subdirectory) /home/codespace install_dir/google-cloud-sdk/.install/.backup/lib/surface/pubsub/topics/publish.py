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
"""Cloud Pub/Sub topics publish command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.util import http_encoding


def _Run(args, message_body, legacy_output=False):
  """Publishes a message to a topic."""
  client = topics.TopicsClient()

  attributes = util.ParseAttributes(args.attribute, messages=client.messages)
  ordering_key = getattr(args, 'ordering_key', None)
  topic_ref = args.CONCEPTS.topic.Parse()

  result = client.Publish(topic_ref, http_encoding.Encode(message_body),
                          attributes, ordering_key)

  if legacy_output:
    # We only allow to publish one message at a time, so do not return a
    # list of messageId.
    result = resource_projector.MakeSerializable(result)
    result['messageIds'] = result['messageIds'][0]
  return result


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Publish(base.Command):
  """Publishes a message to the specified topic."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Publishes a message to the specified topic name for testing and
          troubleshooting. Use with caution: all associated subscribers must
          be able to consume and acknowledge any message you publish,
          otherwise the system will continuously re-attempt delivery of the
          bad message for 7 days.""",
      'EXAMPLES':
          """\
          To publish messages in a batch to a specific Cloud Pub/Sub topic,
          run:

            $ {command} mytopic --message="Hello World!" --attribute=KEY1=VAL1,KEY2=VAL2
      """
  }

  @classmethod
  def Args(cls, parser):
    resource_args.AddTopicResourceArg(parser, 'to publish messages to.')
    flags.AddPublishMessageFlags(parser)

  def Run(self, args):
    return _Run(args, args.message)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class PublishBeta(Publish):
  """Publishes a message to the specified topic."""

  @classmethod
  def Args(cls, parser):
    resource_args.AddTopicResourceArg(parser, 'to publish messages to.')
    flags.AddPublishMessageFlags(parser, add_deprecated=True)

  def Run(self, args):
    message_body = flags.ParseMessageBody(args)
    legacy_output = properties.VALUES.pubsub.legacy_output.GetBool()
    return _Run(args, message_body, legacy_output=legacy_output)
