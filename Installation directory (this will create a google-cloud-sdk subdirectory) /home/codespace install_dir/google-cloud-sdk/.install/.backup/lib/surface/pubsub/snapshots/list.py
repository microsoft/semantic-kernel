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
"""Cloud Pub/Sub snapshots list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import snapshots
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util


class List(base.ListCommand):
  """Lists all the snapshots in a given project."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table[box](
            projectId:label=PROJECT,
            snapshotId:label=SNAPSHOT,
            topicId:label=TOPIC,
            expireTime:label=EXPIRE_TIME
            )
        """)
    parser.display_info.AddUriFunc(util.SnapshotUriFunc)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Snapshot paths that match the regular expression in args.name_filter.

    Raises:
      sdk_ex.HttpException if there is an error with the regular
      expression syntax.
    """
    client = snapshots.SnapshotsClient()
    for snapshot in client.List(util.ParseProject(), page_size=args.page_size):
      yield util.ListSnapshotDisplayDict(snapshot)
