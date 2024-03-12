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
"""Cloud Pub/Sub topics list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties


def _Run(args, legacy_output=False):
  client = topics.TopicsClient()
  for topic in client.List(util.ParseProject(), page_size=args.page_size):
    if legacy_output:
      topic = util.ListTopicDisplayDict(topic)
    yield topic


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists Cloud Pub/Sub topics within a project."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Lists all of the Cloud Pub/Sub topics that exist in a given project that
          match the given topic name filter.""",
      'EXAMPLES':
          """\
          To filter results by topic name (ie. only show topic 'my-topic'), run:

            $ {command} --filter="name.scope(topic):'my-topic'"

          To combine multiple filters (with AND or OR), run:

            $ {command} --filter="name.scope(topic):'my-topic' OR name.scope(topic):'my-other-topic'"

          To filter topics that match an expression:

            $ {command} --filter="name.scope(topic):'my-topic_*'"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('yaml')
    parser.display_info.AddUriFunc(util.TopicUriFunc)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(List):
  """Lists Cloud Pub/Sub topics within a project."""

  def Run(self, args):
    legacy_output = properties.VALUES.pubsub.legacy_output.GetBool()
    return _Run(args, legacy_output=legacy_output)
