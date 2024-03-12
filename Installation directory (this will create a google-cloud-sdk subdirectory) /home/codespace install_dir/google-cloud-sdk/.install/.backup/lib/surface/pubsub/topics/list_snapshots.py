# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Cloud Pub/Sub topics list-snapshots command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListSnapshots(base.ListCommand):
  """Lists Cloud Pub/Sub snapshots from a given topic."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Lists all of the Cloud Pub/Sub snapshots attached to the given
          topic and that match the given filter.""",
      'EXAMPLES':
          """\
          To filter results by snapshot name
          (ie. only show snapshot 'mysnaps'), run:

            $ {command} mytopic --filter=snapshotId:mysnaps

          To combine multiple filters (with AND or OR), run:

            $ {command} mytopic --filter="snapshotId:mysnaps1 AND snapshotId:mysnaps2"

          To filter snapshots that match an expression:

            $ {command} mytopic --filter="snapshotId:snaps_*"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('yaml')
    parser.display_info.AddUriFunc(util.SnapshotUriFunc)
    resource_args.AddTopicResourceArg(parser, 'to list snapshots for.')

  def Run(self, args):
    client = topics.TopicsClient()

    topic_ref = args.CONCEPTS.topic.Parse()
    return client.ListSnapshots(topic_ref, page_size=args.page_size)
