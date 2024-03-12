# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Command to delete a Cloud Dataflow snapshot.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import snapshot_utils


class Delete(base.Command):
  """Delete a Cloud Dataflow snapshot.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To delete an existing Cloud Dataflow snapshot, run:

            $ {command} SNAPSHOT_ID --region=SNAPSHOT_REGION
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    snapshot_utils.ArgsForSnapshotRef(parser)

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      A Snapshot message.
    """
    snapshot_ref = snapshot_utils.ExtractSnapshotRef(args)
    return apis.Snapshots.Delete(
        snapshot_id=snapshot_ref.snapshotId,
        project_id=snapshot_ref.projectId,
        region_id=snapshot_ref.location)
