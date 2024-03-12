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
"""Cloud Pub/Sub snapshot describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import snapshots
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util


class Describe(base.DescribeCommand):
  """Describes a Cloud Pub/Sub snapshot."""

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    parser.add_argument('snapshot', help='snapshot to describe.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A serialized object (dict) describing the results of the operation.
      This description fits the Resource described in the ResourceRegistry under
      'pubsub.projects.snapshots'.
    """
    client = snapshots.SnapshotsClient()
    snapshot_ref = util.ParseSnapshot(args.snapshot)
    return client.Get(snapshot_ref)
