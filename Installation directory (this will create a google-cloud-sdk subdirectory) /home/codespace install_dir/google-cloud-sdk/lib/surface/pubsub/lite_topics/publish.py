# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Pub/Sub lite-topics publish command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import lite_util
from googlecloudsdk.command_lib.util.args import resource_args

_DESCRIPTION = """\
Publishes a message to the specified Pub/Sub Lite topic. This command requires
Python 3.6 or greater, and requires the grpcio Python package to be installed.

For MacOS, Linux, and Cloud Shell users, to install the gRPC client libraries,
run:

  $ sudo pip3 install grpcio
  $ export CLOUDSDK_PYTHON_SITEPACKAGES=1
"""

_EXAMPLES = """\
To publish a message to a Pub/Sub Lite topic, run:

$ {command} mytopic --location=us-central1-a --message="Hello World!"

To publish a message to a Pub/Sub Lite topic with an ordering key and
attributes, run:

  $ {command} mytopic --location=us-central1-a --message="Hello World!" --ordering-key="key" --attributes=KEY1=VAL1,KEY2=VAL2

To publish a message to a Pub/Sub Lite topic with an event time, run:

  $ {command} mytopic --location=us-central1-a --message="Hello World!" --event-time="2021-01-01T12:00:00Z"
"""


def _AddPublishFlags(parser):
  """Adds publish arguments to the parser."""
  resource_args.AddResourceArgToParser(
      parser,
      resource_path='pubsub.lite_topic',
      help_text='The pubsub lite topic to publish to.',
      required=True)
  parser.add_argument(
      '--message',
      help="""The body of the message to publish to the given topic name.""")
  parser.add_argument(
      '--attributes',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(key_type=str, value_type=str, max_length=100),
      help="""Comma-separated list of attributes. Each ATTRIBUTE has the form
          name="value". You can specify up to 100 attributes.""")
  parser.add_argument(
      '--ordering-key',
      help="""A string key, used for ordering delivery to subscribers. All
          messages with the same ordering key will be assigned to the same
          partition for ordered delivery.""")
  parser.add_argument(
      '--event-time',
      type=arg_parsers.Datetime.Parse,
      metavar='DATETIME',
      help="""A user-specified event time. Run `gcloud topic datetimes` for
          information on time formats.""")


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Publish(base.Command):
  """Publish Pub/Sub Lite messages."""

  detailed_help = {'DESCRIPTION': _DESCRIPTION, 'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    _AddPublishFlags(parser)

  def Run(self, args):
    lite_util.RequirePython36('gcloud pubsub lite-topics publish')
    try:
      # pylint: disable=g-import-not-at-top
      from googlecloudsdk.api_lib.pubsub import lite_topics
      # pylint: enable=g-import-not-at-top
    except ImportError:
      raise lite_util.NoGrpcInstalled()

    with lite_topics.PublisherClient() as publisher_client:
      return publisher_client.Publish(
          topic_resource=args.CONCEPTS.topic.Parse(),
          message=args.message,
          ordering_key=args.ordering_key,
          attributes=args.attributes,
          event_time=args.event_time if hasattr(args, 'event_time') else None)
